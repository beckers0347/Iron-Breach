#include "UI/IBLobbyStripWidget.h"
#include "UI/IBStyleKit.h"
#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBFriendRowWidget.h"
#include "Online/IBFriendsSubsystem.h"
#include "Online/IBSessionSubsystem.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/SizeBox.h"

namespace
{
	constexpr int32 LobbySlots = 4; // mirrors UIBSessionSubsystem::MaxPlayers default
}

void UIBLobbyStripWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
	RefreshBanners(/*bForce=*/true);
}

void UIBLobbyStripWidget::BuildLayout()
{
	if (!WidgetTree || BannerRow) { return; }

	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	WidgetTree->RootWidget = Root;

	// ---- Bottom-center: header + the banner row ----
	UVerticalBox* StripColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	LobbyTitleText = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBLobby", "Title", "SQUAD"), 13, IBStyle::TextLo(), 600);
	CountText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::Amber(), 300);
	UTextBlock* FriendsLabel = nullptr;
	FriendsButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBLobby", "Friends", "FRIENDS"), 11, false, &FriendsLabel);
	FriendsButton->OnClicked.AddDynamic(this, &UIBLobbyStripWidget::HandleFriendsToggle);

	if (UHorizontalBoxSlot* TitleSlot = Header->AddChildToHorizontalBox(LobbyTitleText))
	{
		TitleSlot->SetVerticalAlignment(VAlign_Center);
		TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* CountSlot = Header->AddChildToHorizontalBox(CountText))
	{
		CountSlot->SetVerticalAlignment(VAlign_Center);
		CountSlot->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));
	}
	if (UHorizontalBoxSlot* FriendsSlot = Header->AddChildToHorizontalBox(FriendsButton))
	{
		FriendsSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* HeaderSlot = StripColumn->AddChildToVerticalBox(Header))
	{
		HeaderSlot->SetPadding(FMargin(4.f, 0.f, 4.f, 8.f));
	}

	BannerRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	StripColumn->AddChildToVerticalBox(BannerRow);

	if (UOverlaySlot* StripSlot = Root->AddChildToOverlay(StripColumn))
	{
		StripSlot->SetHorizontalAlignment(HAlign_Center);
		StripSlot->SetVerticalAlignment(VAlign_Bottom);
		StripSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 42.f));
	}

	// ---- Right flyout: the friends panel (hidden until toggled) ----
	FriendsPanel = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.97f), 12.f);
	FriendsPanel->SetPadding(FMargin(16.f));

	UVerticalBox* PanelColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	FriendsPanel->SetContent(PanelColumn);

	UHorizontalBox* PanelHeader = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* PanelTitle = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBLobby", "FriendsTitle", "FRIENDS"), 18, IBStyle::TextHi(), 500);
	UButton* RefreshButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBLobby", "Refresh", "REFRESH"), 10);
	RefreshButton->OnClicked.AddDynamic(this, &UIBLobbyStripWidget::HandleFriendsRefresh);
	if (UHorizontalBoxSlot* PTitleSlot = PanelHeader->AddChildToHorizontalBox(PanelTitle))
	{
		PTitleSlot->SetVerticalAlignment(VAlign_Center);
		PTitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* RefSlot = PanelHeader->AddChildToHorizontalBox(RefreshButton))
	{
		RefSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* PanelHeaderSlot = PanelColumn->AddChildToVerticalBox(PanelHeader))
	{
		PanelHeaderSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
	}

	FriendsEmptyText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 200);
	FriendsEmptyText->SetAutoWrapText(true);
	PanelColumn->AddChildToVerticalBox(FriendsEmptyText);

	FriendsList = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
	if (UVerticalBoxSlot* ListSlot = PanelColumn->AddChildToVerticalBox(FriendsList))
	{
		ListSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	USizeBox* PanelFrame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	PanelFrame->SetWidthOverride(340.f);
	PanelFrame->SetHeightOverride(520.f);
	PanelFrame->AddChild(FriendsPanel);
	if (UOverlaySlot* PanelSlot = Root->AddChildToOverlay(PanelFrame))
	{
		PanelSlot->SetHorizontalAlignment(HAlign_Right);
		PanelSlot->SetVerticalAlignment(VAlign_Center);
		PanelSlot->SetPadding(FMargin(0.f, 0.f, 36.f, 0.f));
	}
	PanelFrame->SetVisibility(ESlateVisibility::Collapsed);
	FriendsPanelFrame = PanelFrame; // the SizeBox is the show/hide target

	// Banner pool: MaxPlayers cards, filled/emptied in place.
	for (int32 i = 0; i < LobbySlots; ++i)
	{
		UIBPlayerBannerWidget* Banner = CreateWidget<UIBPlayerBannerWidget>(GetOwningPlayer(), UIBPlayerBannerWidget::StaticClass());
		if (!Banner) { continue; }
		if (UHorizontalBoxSlot* BannerSlot = BannerRow->AddChildToHorizontalBox(Banner))
		{
			BannerSlot->SetPadding(FMargin(7.f, 0.f));
		}
		Banners.Add(Banner);
	}
}

void UIBLobbyStripWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	RefreshAccumulator += InDeltaTime;
	if (RefreshAccumulator >= 0.5f)
	{
		RefreshAccumulator = 0.0f;
		RefreshBanners();
	}
}

void UIBLobbyStripWidget::RefreshBanners(bool bForce)
{
	const UWorld* World = GetWorld();
	const AGameStateBase* GameState = World ? World->GetGameState() : nullptr;
	if (!GameState || Banners.Num() == 0) { return; }

	// Fingerprint the roster; rebuilding identical banners twice a second
	// would flicker hover states for nothing.
	TArray<int32> Roster;
	for (const APlayerState* PS : GameState->PlayerArray)
	{
		if (PS) { Roster.Add(PS->GetPlayerId()); }
	}
	if (!bForce && Roster == LastRoster) { return; }
	LastRoster = Roster;

	const int32 PlayerCount = GameState->PlayerArray.Num();
	for (int32 i = 0; i < Banners.Num(); ++i)
	{
		if (!Banners[i]) { continue; }
		if (GameState->PlayerArray.IsValidIndex(i) && GameState->PlayerArray[i])
		{
			// Listen-server convention: first login is the host.
			Banners[i]->SetFromPlayerState(GameState->PlayerArray[i], /*bIsHost=*/i == 0);
		}
		else
		{
			Banners[i]->SetEmptySlot(i);
		}
	}

	if (CountText)
	{
		CountText->SetText(FText::FromString(FString::Printf(TEXT("%d / %d"), PlayerCount, Banners.Num())));
	}
}

UIBFriendsSubsystem* UIBLobbyStripWidget::GetFriendsSubsystem() const
{
	const UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBFriendsSubsystem>() : nullptr;
}

void UIBLobbyStripWidget::HandleFriendsToggle()
{
	bFriendsOpen = !bFriendsOpen;
	if (FriendsPanelFrame)
	{
		FriendsPanelFrame->SetVisibility(bFriendsOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
	if (bFriendsOpen)
	{
		if (UIBFriendsSubsystem* Friends = GetFriendsSubsystem())
		{
			if (!bFriendsBound)
			{
				Friends->OnFriendsUpdated.AddDynamic(this, &UIBLobbyStripWidget::HandleFriendsUpdated);
				bFriendsBound = true;
			}
			if (FriendsEmptyText)
			{
				FriendsEmptyText->SetText(NSLOCTEXT("IBLobby", "FriendsLoading", "READING FRIENDS LIST..."));
			}
			Friends->RefreshFriends();
		}
	}
}

void UIBLobbyStripWidget::HandleFriendsRefresh()
{
	if (UIBFriendsSubsystem* Friends = GetFriendsSubsystem())
	{
		Friends->RefreshFriends();
	}
}

void UIBLobbyStripWidget::HandleFriendsUpdated()
{
	RebuildFriendRows();
}

void UIBLobbyStripWidget::RebuildFriendRows()
{
	if (!FriendsList) { return; }
	FriendsList->ClearChildren();

	UIBFriendsSubsystem* Friends = GetFriendsSubsystem();
	if (!Friends) { return; }

	if (!Friends->HasFriendsService())
	{
		FriendsEmptyText->SetText(NSLOCTEXT("IBLobby", "NoService",
			"STEAM OFFLINE — FRIENDS UNAVAILABLE IN LAN MODE."));
		return;
	}

	const UGameInstance* GI = GetGameInstance();
	const UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
	const bool bCanInvite = Sessions && Sessions->IsInSession();

	const TArray<FIBFriendInfo> List = Friends->GetFriends();
	if (List.Num() == 0)
	{
		FriendsEmptyText->SetText(NSLOCTEXT("IBLobby", "NoFriends", "NO FRIENDS RETURNED BY STEAM."));
		return;
	}

	FriendsEmptyText->SetText(bCanInvite
		? FText::GetEmpty()
		: NSLOCTEXT("IBLobby", "HostHint", "HOST A LOBBY TO SEND INVITES."));

	for (const FIBFriendInfo& Info : List)
	{
		UIBFriendRowWidget* Row = CreateWidget<UIBFriendRowWidget>(GetOwningPlayer(), UIBFriendRowWidget::StaticClass());
		if (!Row) { continue; }
		Row->InitRow(Info, bCanInvite);
		Row->OnAction.AddDynamic(this, &UIBLobbyStripWidget::HandleRowAction);
		if (UScrollBoxSlot* RowSlot = Cast<UScrollBoxSlot>(FriendsList->AddChild(Row)))
		{
			RowSlot->SetPadding(FMargin(0.f, 2.f));
		}
	}
}

void UIBLobbyStripWidget::HandleRowAction(const FString& NetIdStr, bool bJoin)
{
	UIBFriendsSubsystem* Friends = GetFriendsSubsystem();
	if (!Friends) { return; }
	if (bJoin)
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Lobby] Joining friend %s"), *NetIdStr);
		Friends->JoinFriend(NetIdStr);
	}
	else
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Lobby] Inviting friend %s"), *NetIdStr);
		Friends->InviteFriend(NetIdStr);
	}
}
