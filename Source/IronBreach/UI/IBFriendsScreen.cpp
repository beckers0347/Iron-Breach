#include "UI/IBFriendsScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBStyleKit.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBFriendRowWidget.h"
#include "Online/IBFriendsSubsystem.h"
#include "Online/IBSessionSubsystem.h"
#include "Online/IBWatchTypes.h"
#include "World/IBMapSubsystem.h"
#include "World/IBMapTypes.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/PlayerController.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

namespace IBSquadLayout
{
	/** Banner seats: the fireteam size the session advertises (six). */
	int32 SquadSlots() { return UIBSessionSubsystem::FireteamSize(); }

	/** Subtle V: the row dips toward the middle so six cards read as a formation, not a shelf. */
	float SeatDrop(int32 Index, int32 Count)
	{
		const float Center = (Count - 1) * 0.5f;
		return (Center - FMath::Abs(Index - Center)) * 18.f;
	}

	/** Width of the social flyout's frame, in the 1600 x 900 design space. */
	constexpr float FlyoutWidth = 340.f;
	/** Gap the flyout keeps from the right edge of the sheet. */
	constexpr float FlyoutInset = 8.f;
	/** Clear air between the seat row and the flyout. */
	constexpr float FlyoutGutter = 24.f;
	/** What the seat row gives up on its right while the flyout is open. The row
	 *  does not move by this amount — it is scaled to fit what is left, which is
	 *  why the number only has to be right, not lucky. */
	constexpr float SeatReserve = FlyoutWidth + FlyoutInset + FlyoutGutter;
}

void UIBFriendsScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBFriendsScreen::BuildLayout()
{
	if (!WidgetTree || BannerRow) { return; }

	const auto Page = BuildHangarSection(
        NSLOCTEXT("IBSquad", "PageTitle", "SQUAD"),
        NSLOCTEXT("IBSquad", "PageSub", "BREAKWATER / FIRETEAM"),
        NSLOCTEXT("IBSquad", "PageHint", "SELECT AN OPEN SEAT / INVITE     Q E / SWITCH MENU     ESC / RETURN"));
    UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>();
    Page.Body->AddChildToVerticalBox(Root)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	// ---- SOCIAL chip top-right (online count; toggles the flyout) ----
	UTextBlock* RawSocialText = nullptr;
	UButton* SocialButton = IBStyle::MakeButton(WidgetTree, FText::GetEmpty(), 12, false, &RawSocialText);
	SocialCountText = RawSocialText;
	SocialCountText->SetText(NSLOCTEXT("IBSquad", "Social", "SOCIAL"));
	SocialButton->OnClicked.AddDynamic(this, &UIBFriendsScreen::HandleSocialToggle);
	Page.HeaderRight->AddChildToVerticalBox(SocialButton);

	// ---- Center: the banner row (hero card at LocalSlotIndex) ----
	BannerRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	const int32 Seats = IBSquadLayout::SquadSlots();
	for (int32 i = 0; i < Seats; ++i)
	{
		UIBPlayerBannerWidget* Banner = CreateWidget<UIBPlayerBannerWidget>(GetOwningPlayer(), UIBPlayerBannerWidget::StaticClass());
		if (!Banner) { continue; }
		Banner->SetFeatured(i == LocalSlotIndex);
		Banner->OnInviteClicked.AddDynamic(this, &UIBFriendsScreen::HandleInviteSlotClicked);
		if (UHorizontalBoxSlot* CardSlot = BannerRow->AddChildToHorizontalBox(Banner))
		{
			CardSlot->SetPadding(FMargin(8.f, IBSquadLayout::SeatDrop(i, Seats), 8.f, 0.f));
			CardSlot->SetVerticalAlignment(VAlign_Top);
		}
		Banners.Add(Banner);
	}
	// The row is a fixed 1202 design units of card and cannot simply be shoved
	// sideways to make room for the flyout: an overlay slot that centres a child
	// wider than its allotted space does not keep the left edge on screen, and
	// the first seat went off the left of the sheet at both target sizes. Fit it
	// instead. HAlign_Fill on the slot means there is no centring arithmetic to
	// get wrong — the box is handed exactly what the padding leaves, and
	// ScaleToFit guarantees all six cards land inside it whatever that is.
	SeatFit = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());
	SeatFit->SetStretch(EStretch::ScaleToFit);
	SeatFit->SetStretchDirection(EStretchDirection::DownOnly); // never larger than authored
	if (UScaleBoxSlot* SeatSlot = Cast<UScaleBoxSlot>(SeatFit->AddChild(BannerRow)))
	{
		SeatSlot->SetHorizontalAlignment(HAlign_Center);
		SeatSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UOverlaySlot* RowSlot = Root->AddChildToOverlay(SeatFit))
	{
		RowSlot->SetHorizontalAlignment(HAlign_Fill);
		RowSlot->SetVerticalAlignment(VAlign_Center);
		RowSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 70.f));
	}

	// ---- Right flyout: the friends list ----
	// Near-opaque on purpose. At 0.95 the seat behind it read straight through
	// the panel — a bright cyan + on near-black shows at five percent — and the
	// flyout looked like a rendering fault rather than a panel on top.
	UBorder* FlyoutCard = IBHangar::Glass(WidgetTree, nullptr, FMargin(18.f), FIBGlassStyle::Dossier(), FLinearColor(0.006f, 0.015f, 0.026f, 0.995f));
	UVerticalBox* FlyoutColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	FlyoutCard->SetContent(FlyoutColumn);

	UHorizontalBox* FlyoutHeader = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* FlyoutTitle = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBSquad", "Friends", "FRIENDS"), 16, IBStyle::TextHi(), 500);
	UButton* RefreshButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBSquad", "Refresh", "REFRESH"), 10);
	RefreshButton->OnClicked.AddDynamic(this, &UIBFriendsScreen::HandleRefreshClicked);
	if (UHorizontalBoxSlot* FTitleSlot = FlyoutHeader->AddChildToHorizontalBox(FlyoutTitle))
	{
		FTitleSlot->SetVerticalAlignment(VAlign_Center);
		FTitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* RefSlot = FlyoutHeader->AddChildToHorizontalBox(RefreshButton))
	{
		RefSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* FlyoutHeaderSlot = FlyoutColumn->AddChildToVerticalBox(FlyoutHeader))
	{
		FlyoutHeaderSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	}

	FriendsEmptyText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 200);
	FriendsEmptyText->SetAutoWrapText(true);
	FlyoutColumn->AddChildToVerticalBox(FriendsEmptyText);

	FriendsList = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
	if (UVerticalBoxSlot* ListSlot = FlyoutColumn->AddChildToVerticalBox(FriendsList))
	{
		ListSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	FlyoutFrame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	// Same constant the seat row reserves against, so the two cannot drift apart.
	FlyoutFrame->SetWidthOverride(IBSquadLayout::FlyoutWidth);
	FlyoutFrame->SetHeightOverride(500.f);
	FlyoutFrame->AddChild(FlyoutCard);
	if (UOverlaySlot* FlyoutSlot = Root->AddChildToOverlay(FlyoutFrame))
	{
		FlyoutSlot->SetHorizontalAlignment(HAlign_Right);
		FlyoutSlot->SetVerticalAlignment(VAlign_Center);
		FlyoutSlot->SetPadding(FMargin(0.f, 0.f, IBSquadLayout::FlyoutInset, 70.f));
	}
	FlyoutFrame->SetVisibility(ESlateVisibility::Collapsed);

	// ---- Bottom-left: CURRENT LOCATION card ----
	UBorder* LocationCard = IBHangar::Glass(WidgetTree, nullptr, FMargin(16.f, 10.f), FIBGlassStyle::Chip(), FLinearColor(0.008f, 0.018f, 0.03f, 0.9f));
	UVerticalBox* LocationColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	LocationCard->SetContent(LocationColumn);
	LocationColumn->AddChildToVerticalBox(IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBSquad", "Location", "CURRENT LOCATION"), 9, IBStyle::TextLo(), 600));
	LocationMapText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 15, IBStyle::TextHi(), 300);
	LocationColumn->AddChildToVerticalBox(LocationMapText);
	LocationZoneText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 10, IBStyle::Cyan(), 300);
	LocationColumn->AddChildToVerticalBox(LocationZoneText);
	if (UOverlaySlot* LocationSlot = Root->AddChildToOverlay(LocationCard))
	{
		LocationSlot->SetHorizontalAlignment(HAlign_Left);
		LocationSlot->SetVerticalAlignment(VAlign_Bottom);
		LocationSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 0.f));
	}

	// ---- Bottom bar: LEAVE FIRETEAM + privacy line ----
	UHorizontalBox* BottomBar = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* LeaveLabel = nullptr;
	LeaveButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBSquad", "Leave", "LEAVE FIRETEAM"), 11, false, &LeaveLabel);
	LeaveButton->OnClicked.AddDynamic(this, &UIBFriendsScreen::HandleLeaveClicked);
	if (UHorizontalBoxSlot* LeaveSlot = BottomBar->AddChildToHorizontalBox(LeaveButton))
	{
		LeaveSlot->SetVerticalAlignment(VAlign_Center);
		LeaveSlot->SetPadding(FMargin(0.f, 0.f, 22.f, 0.f));
	}
	UTextBlock* Privacy = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBSquad", "Privacy", "FIRETEAM PRIVACY  ·  FRIENDS ONLY"), 10, IBStyle::TextLo(), 400);
	if (UHorizontalBoxSlot* PrivacySlot = BottomBar->AddChildToHorizontalBox(Privacy))
	{
		PrivacySlot->SetVerticalAlignment(VAlign_Center);
	}
	// On the same chip surface the CURRENT LOCATION card uses, for the same
	// reason: the hangar floor is the brightest thing on this screen and the
	// privacy line was sitting straight on top of its reflections.
	UBorder* BottomChip = IBHangar::Glass(WidgetTree, BottomBar, FMargin(14.f, 8.f),
		FIBGlassStyle::Chip(), FLinearColor(0.008f, 0.018f, 0.03f, 0.9f));
	if (UOverlaySlot* BottomSlot = Root->AddChildToOverlay(BottomChip))
	{
		BottomSlot->SetHorizontalAlignment(HAlign_Right);
		BottomSlot->SetVerticalAlignment(VAlign_Bottom);
		BottomSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));
	}
}

void UIBFriendsScreen::NativeScreenOpened()
{
	RefreshBanners(/*bForce=*/true);
	RefreshLocationCard();

	if (UIBFriendsSubsystem* Friends = GetFriendsSubsystem())
	{
		if (!bFriendsBound)
		{
			Friends->OnFriendsUpdated.AddDynamic(this, &UIBFriendsScreen::HandleFriendsUpdated);
			bFriendsBound = true;
		}
		if (FriendsEmptyText)
		{
			FriendsEmptyText->SetText(NSLOCTEXT("IBSquad", "Loading", "READING FRIENDS LIST..."));
		}
		Friends->RefreshFriends();
	}

	// LEAVE only means something with a live session under you.
	const UGameInstance* GI = GetGameInstance();
	const UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
	if (LeaveButton)
	{
		LeaveButton->SetVisibility((Sessions && Sessions->IsInSession())
			? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
}

void UIBFriendsScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime); // keeps the base focus reassertion

	RefreshAccumulator += InDeltaTime;
	if (RefreshAccumulator >= 0.5f && IsVisible())
	{
		RefreshAccumulator = 0.0f;
		RefreshBanners();
	}
}

void UIBFriendsScreen::RefreshBanners(bool bForce)
{
	const UWorld* World = GetWorld();
	const AGameStateBase* GameState = World ? World->GetGameState() : nullptr;
	if (!GameState || Banners.Num() == 0) { return; }

	TArray<int32> Roster;
	for (const APlayerState* PS : GameState->PlayerArray)
	{
		if (PS) { Roster.Add(PS->GetPlayerId()); }
	}
	if (!bForce && Roster == LastRoster) { return; }
	LastRoster = Roster;

	// Display order: the LOCAL player always takes the hero slot; everyone
	// else fills around them in join order. Host = first login (chip only).
	const APlayerController* PC = GetOwningPlayer();
	const APlayerState* LocalPS = PC ? PC->PlayerState : nullptr;

	TArray<const APlayerState*> Others;
	const APlayerState* HostPS = GameState->PlayerArray.Num() > 0 ? GameState->PlayerArray[0].Get() : nullptr;
	for (const APlayerState* PS : GameState->PlayerArray)
	{
		if (PS && PS != LocalPS) { Others.Add(PS); }
	}

	TArray<const APlayerState*> Display;
	Display.SetNum(Banners.Num());
	int32 OtherIndex = 0;
	for (int32 i = 0; i < Banners.Num(); ++i)
	{
		if (i == LocalSlotIndex)
		{
			Display[i] = LocalPS;
		}
		else if (OtherIndex < Others.Num())
		{
			Display[i] = Others[OtherIndex++];
		}
	}

	for (int32 i = 0; i < Banners.Num(); ++i)
	{
		if (!Banners[i]) { continue; }
		if (Display.IsValidIndex(i) && Display[i])
		{
			Banners[i]->SetFromPlayerState(Display[i], /*bIsHost=*/Display[i] == HostPS);
			// Somebody took the seat the open flyout was raised from. It is not
			// an open seat any more, so the mark goes with it.
			if (i == SelectedSeatIndex) { SetSelectedSeat(INDEX_NONE); }
		}
		else
		{
			Banners[i]->SetEmptySlot(i);
		}
	}
}

void UIBFriendsScreen::RefreshLocationCard()
{
	const UWorld* World = GetWorld();
	if (!World || !LocationMapText) { return; }

	const FIBDestination* Destination = IBWatch::Find(IBWatch::DestinationForMap(World->GetMapName()));
	LocationMapText->SetText(Destination ? Destination->Name.ToUpper() : NSLOCTEXT("IBSquad", "Field", "FIELD OPERATIONS"));

	FText Zone = FText::GetEmpty();
	if (const UIBMapSubsystem* MapSub = World->GetSubsystem<UIBMapSubsystem>())
	{
		if (const UIBMapZoneData* ZoneData = MapSub->GetZoneData())
		{
			Zone = ZoneData->ZoneName;
		}
	}
	LocationZoneText->SetText(Zone);
	LocationZoneText->SetVisibility(Zone.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

UIBFriendsSubsystem* UIBFriendsScreen::GetFriendsSubsystem() const
{
	const UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBFriendsSubsystem>() : nullptr;
}

void UIBFriendsScreen::SetSelectedSeat(int32 Index)
{
	if (SelectedSeatIndex == Index) { return; }
	if (Banners.IsValidIndex(SelectedSeatIndex) && Banners[SelectedSeatIndex])
	{
		Banners[SelectedSeatIndex]->SetSeatSelected(false);
	}
	SelectedSeatIndex = Banners.IsValidIndex(Index) ? Index : INDEX_NONE;
	if (Banners.IsValidIndex(SelectedSeatIndex) && Banners[SelectedSeatIndex])
	{
		Banners[SelectedSeatIndex]->SetSeatSelected(true);
	}
}

void UIBFriendsScreen::SetFlyoutOpen(bool bOpen)
{
	bFlyoutOpen = bOpen;
	if (FlyoutFrame)
	{
		FlyoutFrame->SetVisibility(bFlyoutOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
	// The seat row and the right-hand flyout share one overlay. Reserve the
	// flyout's width on the row's right while it is open; the scale box then
	// fits all six cards into what is left instead of the row running off the
	// left of the sheet. Closed, the reserve is zero, the scale returns to 1 and
	// the arrangement is the authored one again.
	//
	// Fitting rather than translating, deliberately: a translation has to be
	// exactly right at every resolution and it was not, whereas ScaleToFit is
	// correct by construction. The cards shrink about five percent with the
	// flyout open, which keeps the order, the V and every hover, focus and
	// selection mark — those are painted in each card's own local space, so they
	// scale with it and stay on screen.
	if (UOverlaySlot* RowSlot = Cast<UOverlaySlot>(SeatFit ? SeatFit->Slot.Get() : nullptr))
	{
		RowSlot->SetPadding(FMargin(0.f, 0.f, bFlyoutOpen ? IBSquadLayout::SeatReserve : 0.f, 70.f));
	}
	// The seat mark exists to say where an open flyout came from, so it never
	// outlives the flyout.
	if (!bFlyoutOpen) { SetSelectedSeat(INDEX_NONE); }
}

void UIBFriendsScreen::HandleSocialToggle()
{
	SetFlyoutOpen(!bFlyoutOpen);
	if (bFlyoutOpen)
	{
		// Raised from the header chip, not from a seat: nothing to mark.
		SetSelectedSeat(INDEX_NONE);
		HandleRefreshClicked();
	}
}

void UIBFriendsScreen::HandleInviteSlotClicked(UIBPlayerBannerWidget* Banner)
{
	// The concept's +: an empty seat IS the invite affordance. The seat that
	// raised the list gets marked so it is obvious where you came from — it is
	// a visual origin only. Invites go to the session, not to a seat, and
	// nothing below this line reads the mark.
	SetFlyoutOpen(true);
	SetSelectedSeat(Banners.IndexOfByPredicate(
		[Banner](const TObjectPtr<UIBPlayerBannerWidget>& Seat) { return Seat.Get() == Banner; }));
	HandleRefreshClicked();
}

void UIBFriendsScreen::HandleLeaveClicked()
{
	UGameInstance* GI = GetGameInstance();
	if (UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr)
	{
		if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
		{
			Menu->CloseMenu(); // input-mode restore must run against THIS world
		}
		Sessions->IBLeave();
	}
}

void UIBFriendsScreen::HandleRefreshClicked()
{
	if (UIBFriendsSubsystem* Friends = GetFriendsSubsystem())
	{
		Friends->RefreshFriends();
	}
}

void UIBFriendsScreen::HandleFriendsUpdated()
{
	RebuildFriendRows();
}

void UIBFriendsScreen::RebuildFriendRows()
{
	if (!FriendsList) { return; }
	FriendsList->ClearChildren();

	UIBFriendsSubsystem* Friends = GetFriendsSubsystem();
	if (!Friends) { return; }

	// SOCIAL chip count: friends online right now.
	const TArray<FIBFriendInfo> List = Friends->GetFriends();
	if (SocialCountText)
	{
		const int32 Online = List.FilterByPredicate([](const FIBFriendInfo& F) { return F.bOnline; }).Num();
		SocialCountText->SetText(FText::FromString(FString::Printf(TEXT("SOCIAL  ·  %d"), Online)));
	}

	if (!Friends->HasFriendsService())
	{
		FriendsEmptyText->SetText(NSLOCTEXT("IBSquad", "NoService",
			"STEAM OFFLINE — FRIENDS UNAVAILABLE IN LAN MODE."));
		return;
	}

	const UGameInstance* GI = GetGameInstance();
	const UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
	const bool bCanInvite = Sessions && Sessions->IsInSession();

	if (List.Num() == 0)
	{
		FriendsEmptyText->SetText(NSLOCTEXT("IBSquad", "NoFriends", "NO FRIENDS RETURNED BY STEAM."));
		return;
	}

	FriendsEmptyText->SetText(bCanInvite
		? FText::GetEmpty()
		: NSLOCTEXT("IBSquad", "HostHint", "OFF THE NET — THIS WORLD ISN'T HOSTED, SO INVITES ARE UNAVAILABLE."));

	for (const FIBFriendInfo& Info : List)
	{
		UIBFriendRowWidget* Row = CreateWidget<UIBFriendRowWidget>(GetOwningPlayer(), UIBFriendRowWidget::StaticClass());
		if (!Row) { continue; }
		Row->InitRow(Info, bCanInvite);
		Row->OnAction.AddDynamic(this, &UIBFriendsScreen::HandleRowAction);
		if (UScrollBoxSlot* RowSlot = Cast<UScrollBoxSlot>(FriendsList->AddChild(Row)))
		{
			RowSlot->SetPadding(FMargin(0.f, 2.f));
		}
	}
}

void UIBFriendsScreen::HandleRowAction(const FString& NetIdStr, bool bJoin)
{
	UIBFriendsSubsystem* Friends = GetFriendsSubsystem();
	if (!Friends) { return; }
	if (bJoin)
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Fireteam] Joining friend %s"), *NetIdStr);
		Friends->JoinFriend(NetIdStr);
	}
	else
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Fireteam] Inviting friend %s"), *NetIdStr);
		Friends->InviteFriend(NetIdStr);
	}
}
