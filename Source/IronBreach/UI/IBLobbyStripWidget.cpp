#include "UI/IBLobbyStripWidget.h"
#include "UI/IBStyleKit.h"
#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBMenuSubsystem.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "Items/IBPlayerState.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"

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

	// Bottom-center: header + the banner row.
	UVerticalBox* StripColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	LobbyTitleText = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBLobby", "Title", "SQUAD"), 13, IBStyle::TextLo(), 600);
	CountText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::Amber(), 300);
	FriendsButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBLobby", "Friends", "FRIENDS"), 11);
	FriendsButton->OnClicked.AddDynamic(this, &UIBLobbyStripWidget::HandleFriendsClicked);

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
		if (!PS) { continue; }
		Roster.Add(PS->GetPlayerId());
		// Operative identity replicates a beat after the PlayerState itself;
		// fold it into the fingerprint so callsigns land without a roster change.
		if (const AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS))
		{
			Roster.Add(IBPS->HasOperative() ? static_cast<int32>(GetTypeHash(IBPS->GetOperativeCallsign())) : 0);
		}
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

void UIBLobbyStripWidget::HandleFriendsClicked()
{
	// One friends surface everywhere: the SQUAD menu tab.
	if (const ULocalPlayer* LP = GetOwningLocalPlayer())
	{
		if (UIBMenuSubsystem* Menu = LP->GetSubsystem<UIBMenuSubsystem>())
		{
			Menu->ToggleScreen(FName(TEXT("Squad")));
		}
	}
}
