#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/OnlineSessionInterface.h" // FOnlineSessionSearchResult in the friend-session callback
#include "IBFriendsSubsystem.generated.h"

/** One row of the friends panel — flattened for BP/UI consumption. */
USTRUCT(BlueprintType)
struct FIBFriendInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Friends")
	FString DisplayName;

	/** Stable key back into the subsystem (invite/join take this). */
	UPROPERTY(BlueprintReadOnly, Category = "Friends")
	FString NetIdStr;

	UPROPERTY(BlueprintReadOnly, Category = "Friends")
	bool bOnline = false;

	/** In Iron Breach right now — the invite/join sweet spot. */
	UPROPERTY(BlueprintReadOnly, Category = "Friends")
	bool bPlayingThisGame = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBFriendsUpdated);

/**
 * Steam friends for the lobby flow: read the list, invite a friend into the
 * session, or chase a friend's session and join it. Presence-backed — works
 * wherever the platform OSS does (Steam in packaged/dev builds; the NULL
 * subsystem has no friends, and the panel says so instead of sitting empty).
 *
 * Join/invite ACCEPTANCE lands in UIBSessionSubsystem (it owns all session
 * mutation); this subsystem never travels anyone itself.
 */
UCLASS()
class IRONBREACH_API UIBFriendsSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Kick off an async friends-list read; OnFriendsUpdated fires when done. */
	UFUNCTION(BlueprintCallable, Category = "IronBreach|Friends")
	void RefreshFriends();

	/** Last read, sorted: in-game first, then online, then offline. */
	UFUNCTION(BlueprintPure, Category = "IronBreach|Friends")
	TArray<FIBFriendInfo> GetFriends() const { return CachedFriends; }

	/** True when the active OSS actually has a friends service (Steam yes, NULL no). */
	UFUNCTION(BlueprintPure, Category = "IronBreach|Friends")
	bool HasFriendsService() const;

	/** Steam invite → their overlay pops "join game". */
	UFUNCTION(BlueprintCallable, Category = "IronBreach|Friends")
	void InviteFriend(const FString& NetIdStr);

	/** Find the friend's current session and join it (presence join). */
	UFUNCTION(BlueprintCallable, Category = "IronBreach|Friends")
	void JoinFriend(const FString& NetIdStr);

	UPROPERTY(BlueprintAssignable, Category = "IronBreach|Friends")
	FOnIBFriendsUpdated OnFriendsUpdated;

private:
	void HandleReadComplete(int32 LocalUserNum, bool bWasSuccessful, const FString& ListName, const FString& ErrorStr);
	void HandleFindFriendSessionComplete(int32 LocalUserNum, bool bWasSuccessful, const TArray<FOnlineSessionSearchResult>& Results);

	FUniqueNetIdPtr ResolveNetId(const FString& NetIdStr) const;

	UPROPERTY()
	TArray<FIBFriendInfo> CachedFriends;

	/** NetIdStr -> real id, rebuilt on every read (ids aren't BP types). */
	TMap<FString, FUniqueNetIdPtr> NetIdLookup;

	FDelegateHandle FindFriendSessionHandle;
};
