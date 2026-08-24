#include "Online/IBFriendsSubsystem.h"
#include "Online/IBSessionSubsystem.h"
#include "IronBreach.h"
#include "OnlineSubsystem.h"
#include "OnlineSubsystemUtils.h"
#include "OnlineSessionSettings.h" // FOnlineSessionSearchResult definition
#include "Interfaces/OnlineFriendsInterface.h"
#include "Interfaces/OnlinePresenceInterface.h"
#include "Engine/GameInstance.h"

namespace
{
	IOnlineFriendsPtr GetFriendsInterface(const UWorld* World)
	{
		IOnlineSubsystem* OSS = Online::GetSubsystem(World);
		return OSS ? OSS->GetFriendsInterface() : nullptr;
	}

	IOnlineSessionPtr GetSessionsInterface(const UWorld* World)
	{
		IOnlineSubsystem* OSS = Online::GetSubsystem(World);
		return OSS ? OSS->GetSessionInterface() : nullptr;
	}
}

bool UIBFriendsSubsystem::HasFriendsService() const
{
	return GetFriendsInterface(GetWorld()).IsValid();
}

void UIBFriendsSubsystem::RefreshFriends()
{
	IOnlineFriendsPtr Friends = GetFriendsInterface(GetWorld());
	if (!Friends.IsValid())
	{
		// NULL subsystem (PIE without Steam): no friends service. Broadcast so
		// the panel can show its "STEAM OFFLINE" line instead of a spinner.
		UE_LOG(LogIronBreach, Log, TEXT("[Friends] No friends interface on this OSS"));
		CachedFriends.Reset();
		NetIdLookup.Reset();
		OnFriendsUpdated.Broadcast();
		return;
	}

	Friends->ReadFriendsList(0, EFriendsLists::ToString(EFriendsLists::Default),
		FOnReadFriendsListComplete::CreateUObject(this, &UIBFriendsSubsystem::HandleReadComplete));
}

void UIBFriendsSubsystem::HandleReadComplete(int32 LocalUserNum, bool bWasSuccessful,
	const FString& ListName, const FString& ErrorStr)
{
	CachedFriends.Reset();
	NetIdLookup.Reset();

	IOnlineFriendsPtr Friends = GetFriendsInterface(GetWorld());
	if (!bWasSuccessful || !Friends.IsValid())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] Read failed: %s"), *ErrorStr);
		OnFriendsUpdated.Broadcast();
		return;
	}

	TArray<TSharedRef<FOnlineFriend>> List;
	Friends->GetFriendsList(LocalUserNum, ListName, List);

	for (const TSharedRef<FOnlineFriend>& Friend : List)
	{
		const FOnlineUserPresence& Presence = Friend->GetPresence();

		FIBFriendInfo Info;
		Info.DisplayName = Friend->GetDisplayName();
		Info.NetIdStr = Friend->GetUserId()->ToString();
		Info.bOnline = Presence.bIsOnline;
		Info.bPlayingThisGame = Presence.bIsPlayingThisGame;

		NetIdLookup.Add(Info.NetIdStr, Friend->GetUserId());
		CachedFriends.Add(MoveTemp(Info));
	}

	// Reading order: squadmates-to-be first.
	CachedFriends.Sort([](const FIBFriendInfo& A, const FIBFriendInfo& B)
	{
		if (A.bPlayingThisGame != B.bPlayingThisGame) { return A.bPlayingThisGame; }
		if (A.bOnline != B.bOnline) { return A.bOnline; }
		return A.DisplayName < B.DisplayName;
	});

	UE_LOG(LogIronBreach, Log, TEXT("[Friends] %d friends (%d in-game)"), CachedFriends.Num(),
		CachedFriends.FilterByPredicate([](const FIBFriendInfo& F) { return F.bPlayingThisGame; }).Num());
	OnFriendsUpdated.Broadcast();
}

FUniqueNetIdPtr UIBFriendsSubsystem::ResolveNetId(const FString& NetIdStr) const
{
	const FUniqueNetIdPtr* Found = NetIdLookup.Find(NetIdStr);
	return Found ? *Found : nullptr;
}

void UIBFriendsSubsystem::InviteFriend(const FString& NetIdStr)
{
	IOnlineSessionPtr Sessions = GetSessionsInterface(GetWorld());
	const FUniqueNetIdPtr Id = ResolveNetId(NetIdStr);
	if (!Sessions.IsValid() || !Id.IsValid())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] Invite failed — unknown friend or no session interface"));
		return;
	}

	// No live session yet? A lobby invite needs a lobby — the UI should have
	// hosted first, but don't silently eat the click.
	if (!Sessions->GetNamedSession(NAME_GameSession))
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] Invite pressed with no live session — host a lobby first"));
		return;
	}

	Sessions->SendSessionInviteToFriend(0, NAME_GameSession, *Id);
	UE_LOG(LogIronBreach, Log, TEXT("[Friends] Invite sent to %s"), *NetIdStr);
}

void UIBFriendsSubsystem::JoinFriend(const FString& NetIdStr)
{
	IOnlineSessionPtr Sessions = GetSessionsInterface(GetWorld());
	const FUniqueNetIdPtr Id = ResolveNetId(NetIdStr);
	if (!Sessions.IsValid() || !Id.IsValid())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] Join failed — unknown friend or no session interface"));
		return;
	}

	FindFriendSessionHandle = Sessions->AddOnFindFriendSessionCompleteDelegate_Handle(0,
		FOnFindFriendSessionCompleteDelegate::CreateUObject(this, &UIBFriendsSubsystem::HandleFindFriendSessionComplete));

	UE_LOG(LogIronBreach, Log, TEXT("[Friends] Chasing %s's session..."), *NetIdStr);
	if (!Sessions->FindFriendSession(0, *Id))
	{
		Sessions->ClearOnFindFriendSessionCompleteDelegate_Handle(0, FindFriendSessionHandle);
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] FindFriendSession call failed immediately"));
	}
}

void UIBFriendsSubsystem::HandleFindFriendSessionComplete(int32 /*LocalUserNum*/, bool bWasSuccessful,
	const TArray<FOnlineSessionSearchResult>& Results)
{
	if (IOnlineSessionPtr Sessions = GetSessionsInterface(GetWorld()))
	{
		Sessions->ClearOnFindFriendSessionCompleteDelegate_Handle(0, FindFriendSessionHandle);
	}

	if (!bWasSuccessful || Results.Num() == 0 || !Results[0].IsValid())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Friends] Friend has no joinable session"));
		return;
	}

	UGameInstance* GI = GetGameInstance();
	if (UIBSessionSubsystem* SessionSub = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr)
	{
		SessionSub->JoinSearchResult(Results[0]); // session subsystem owns the travel
	}
}
