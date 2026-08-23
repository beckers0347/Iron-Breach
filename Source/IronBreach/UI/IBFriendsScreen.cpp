#include "UI/IBFriendsScreen.h"
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
	Dim->SetBrushColor(FLinearColor(0.01f, 0.015f, 0.03f, 0.78f));
	if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
	{
		DimSlot->SetHorizontalAlignment(HAlign_Fill);
		DimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// Title, house grammar (top-left like CHARACTER / THE LEDGER).
	UVerticalBox* TitleBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	TitleBox->AddChildToVerticalBox(IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBSquad", "Title", "SQUAD")));
	UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Amber());
	Accent->SetPadding(FMargin(0.f, 1.5f));
	if (UVerticalBoxSlot* AccentSlot = TitleBox->AddChildToVerticalBox(Accent))
	{
		AccentSlot->SetPadding(FMargin(0.f, 6.f, 60.f, 0.f));
	}
	if (UOverlaySlot* TitleSlot = Root->AddChildToOverlay(TitleBox))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetVerticalAlignment(VAlign_Top);
		TitleSlot->SetPadding(FMargin(90.f, 50.f, 0.f, 0.f));
	}

	// Center column: banner row up top, friends card under it.
	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	UHorizontalBox* SquadHeader = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* SquadLabel = IBStyle::MakeSection(WidgetTree, NSLOCTEXT("IBSquad", "Roster", "ACTIVE ROSTER"));
	CountText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::Amber(), 300);
	if (UHorizontalBoxSlot* LabelSlot = SquadHeader->AddChildToHorizontalBox(SquadLabel))
	{
		LabelSlot->SetVerticalAlignment(VAlign_Center);
		LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* CountSlot = SquadHeader->AddChildToHorizontalBox(CountText))
	{
		CountSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* SquadHeaderSlot = Column->AddChildToVerticalBox(SquadHeader))
	{
		SquadHeaderSlot->SetPadding(FMargin(4.f, 0.f, 4.f, 8.f));
	}

	BannerRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UVerticalBoxSlot* BannerSlot = Column->AddChildToVerticalBox(BannerRow))
	{
		BannerSlot->SetHorizontalAlignment(HAlign_Center);
		BannerSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 18.f));
	}

	for (int32 i = 0; i < SquadSlots; ++i)
	{
		UIBPlayerBannerWidget* Banner = CreateWidget<UIBPlayerBannerWidget>(GetOwningPlayer(), UIBPlayerBannerWidget::StaticClass());
		if (!Banner) { continue; }
		if (UHorizontalBoxSlot* CardSlot = BannerRow->AddChildToHorizontalBox(Banner))
		{
			CardSlot->SetPadding(FMargin(7.f, 0.f));
		}
		Banners.Add(Banner);
	}

	// Friends card.
	UBorder* Card = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.96f), 12.f);
	Card->SetPadding(FMargin(18.f, 14.f));
	UVerticalBox* CardColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Card->SetContent(CardColumn);

	UHorizontalBox* CardHeader = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* CardTitle = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBSquad", "Friends", "FRIENDS"), 16, IBStyle::TextHi(), 500);
	UButton* RefreshButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBSquad", "Refresh", "REFRESH"), 10);
	RefreshButton->OnClicked.AddDynamic(this, &UIBFriendsScreen::HandleRefreshClicked);
	if (UHorizontalBoxSlot* CardTitleSlot = CardHeader->AddChildToHorizontalBox(CardTitle))
	{
		CardTitleSlot->SetVerticalAlignment(VAlign_Center);
		CardTitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* RefreshSlot = CardHeader->AddChildToHorizontalBox(RefreshButton))
	{
		RefreshSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* CardHeaderSlot = CardColumn->AddChildToVerticalBox(CardHeader))
	{
		CardHeaderSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	}

	FriendsEmptyText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 200);
	FriendsEmptyText->SetAutoWrapText(true);
	CardColumn->AddChildToVerticalBox(FriendsEmptyText);

	FriendsList = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
	if (UVerticalBoxSlot* ListSlot = CardColumn->AddChildToVerticalBox(FriendsList))
	{
		ListSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	USizeBox* CardFrame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardFrame->SetWidthOverride(560.f);
	CardFrame->SetHeightOverride(300.f);
	CardFrame->AddChild(Card);
	if (UVerticalBoxSlot* CardFrameSlot = Column->AddChildToVerticalBox(CardFrame))
	{
		CardFrameSlot->SetHorizontalAlignment(HAlign_Center);
	}

	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Column))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Center);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
		ColumnSlot->SetPadding(FMargin(0.f, 40.f, 0.f, 0.f)); // clear the tab rail
	}
}

void UIBFriendsScreen::NativeScreenOpened()
{
	RefreshBanners(/*bForce=*/true);

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
		CountText->SetText(FText::FromString(FString::Printf(TEXT("%d / %d"),
			GameState->PlayerArray.Num(), Banners.Num())));
	}
}

UIBFriendsSubsystem* UIBFriendsScreen::GetFriendsSubsystem() const
{
	const UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBFriendsSubsystem>() : nullptr;
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

	if (!Friends->HasFriendsService())
	{
		FriendsEmptyText->SetText(NSLOCTEXT("IBSquad", "NoService",
			"STEAM OFFLINE — FRIENDS UNAVAILABLE IN LAN MODE."));
		return;
	}

	const UGameInstance* GI = GetGameInstance();
	const UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
	const bool bCanInvite = Sessions && Sessions->IsInSession();

	const TArray<FIBFriendInfo> List = Friends->GetFriends();
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
		UE_LOG(LogIronBreach, Log, TEXT("[Squad] Joining friend %s"), *NetIdStr);
		Friends->JoinFriend(NetIdStr);
	}
	else
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Squad] Inviting friend %s"), *NetIdStr);
		Friends->InviteFriend(NetIdStr);
	}
}
