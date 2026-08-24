#include "UI/IBFriendsScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBStyleKit.h"
#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBFriendRowWidget.h"
#include "Online/IBFriendsSubsystem.h"
#include "Online/IBSessionSubsystem.h"
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
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

namespace
{
	constexpr int32 SquadSlots = 4; // mirrors UIBSessionSubsystem::MaxPlayers default
}

void UIBFriendsScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBFriendsScreen::BuildLayout()
{
	if (!WidgetTree || BannerRow) { return; }

	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!WidgetTree->RootWidget)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	if (!Root) { return; }

	// Menu-standard dim sheet.
	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Dim->SetBrushColor(FLinearColor(0.008f, 0.012f, 0.025f, 0.84f));
	if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
	{
		DimSlot->SetHorizontalAlignment(HAlign_Fill);
		DimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- Title block, concept grammar: IRON BREACH // FIRETEAM ----
	UVerticalBox* TitleBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	TitleBox->AddChildToVerticalBox(IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBSquad", "TitleTop", "IRON BREACH"), 24, IBStyle::TextHi(), 500));
	TitleBox->AddChildToVerticalBox(IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBSquad", "TitleSub", "// FIRETEAM"), 15, IBStyle::Cyan(), 500));
	if (UOverlaySlot* TitleSlot = Root->AddChildToOverlay(TitleBox))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetVerticalAlignment(VAlign_Top);
		TitleSlot->SetPadding(FMargin(90.f, 46.f, 0.f, 0.f));
	}

	// ---- SOCIAL chip top-right (online count; toggles the flyout) ----
	UTextBlock* RawSocialText = nullptr;
	UButton* SocialButton = IBStyle::MakeButton(WidgetTree, FText::GetEmpty(), 12, false, &RawSocialText);
	SocialCountText = RawSocialText;
	SocialCountText->SetText(NSLOCTEXT("IBSquad", "Social", "SOCIAL"));
	SocialButton->OnClicked.AddDynamic(this, &UIBFriendsScreen::HandleSocialToggle);
	if (UOverlaySlot* SocialSlot = Root->AddChildToOverlay(SocialButton))
	{
		SocialSlot->SetHorizontalAlignment(HAlign_Right);
		SocialSlot->SetVerticalAlignment(VAlign_Top);
		SocialSlot->SetPadding(FMargin(0.f, 96.f, 90.f, 0.f));
	}

	// ---- Center: the banner row (hero card at LocalSlotIndex) ----
	BannerRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	for (int32 i = 0; i < SquadSlots; ++i)
	{
		UIBPlayerBannerWidget* Banner = CreateWidget<UIBPlayerBannerWidget>(GetOwningPlayer(), UIBPlayerBannerWidget::StaticClass());
		if (!Banner) { continue; }
		Banner->SetFeatured(i == LocalSlotIndex);
		Banner->OnInviteClicked.AddDynamic(this, &UIBFriendsScreen::HandleInviteSlotClicked);
		if (UHorizontalBoxSlot* CardSlot = BannerRow->AddChildToHorizontalBox(Banner))
		{
			CardSlot->SetPadding(FMargin(9.f, 0.f));
			CardSlot->SetVerticalAlignment(VAlign_Center);
		}
		Banners.Add(Banner);
	}
	if (UOverlaySlot* RowSlot = Root->AddChildToOverlay(BannerRow))
	{
		RowSlot->SetHorizontalAlignment(HAlign_Center);
		RowSlot->SetVerticalAlignment(VAlign_Center);
		RowSlot->SetPadding(FMargin(0.f, 30.f, 0.f, 0.f));
	}

	// ---- Right flyout: the friends list ----
	UBorder* FlyoutCard = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.97f), 12.f);
	FlyoutCard->SetPadding(FMargin(16.f));
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
	FlyoutFrame->SetWidthOverride(340.f);
	FlyoutFrame->SetHeightOverride(500.f);
	FlyoutFrame->AddChild(FlyoutCard);
	if (UOverlaySlot* FlyoutSlot = Root->AddChildToOverlay(FlyoutFrame))
	{
		FlyoutSlot->SetHorizontalAlignment(HAlign_Right);
		FlyoutSlot->SetVerticalAlignment(VAlign_Center);
		FlyoutSlot->SetPadding(FMargin(0.f, 0.f, 42.f, 0.f));
	}
	FlyoutFrame->SetVisibility(ESlateVisibility::Collapsed);

	// ---- Bottom-left: CURRENT LOCATION card ----
	UBorder* LocationCard = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.94f), 10.f);
	LocationCard->SetPadding(FMargin(14.f, 10.f));
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
		LocationSlot->SetPadding(FMargin(90.f, 0.f, 0.f, 46.f));
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
	if (UOverlaySlot* BottomSlot = Root->AddChildToOverlay(BottomBar))
	{
		BottomSlot->SetHorizontalAlignment(HAlign_Center);
		BottomSlot->SetVerticalAlignment(VAlign_Bottom);
		BottomSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 46.f));
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
	Display.SetNum(SquadSlots);
	int32 OtherIndex = 0;
	for (int32 i = 0; i < SquadSlots; ++i)
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

	LocationMapText->SetText(FText::FromString(
		World->GetMapName().Replace(TEXT("UEDPIE_0_"), TEXT("")).Replace(TEXT("Lvl_"), TEXT("")).ToUpper()));

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

void UIBFriendsScreen::SetFlyoutOpen(bool bOpen)
{
	bFlyoutOpen = bOpen;
	if (FlyoutFrame)
	{
		FlyoutFrame->SetVisibility(bFlyoutOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
}

void UIBFriendsScreen::HandleSocialToggle()
{
	SetFlyoutOpen(!bFlyoutOpen);
	if (bFlyoutOpen)
	{
		HandleRefreshClicked();
	}
}

void UIBFriendsScreen::HandleInviteSlotClicked(UIBPlayerBannerWidget* /*Banner*/)
{
	// The concept's +: an empty seat IS the invite affordance.
	SetFlyoutOpen(true);
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
		: NSLOCTEXT("IBSquad", "HostHint", "HOST A LOBBY TO SEND INVITES."));

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
