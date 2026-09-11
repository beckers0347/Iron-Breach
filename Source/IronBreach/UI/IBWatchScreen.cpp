#include "UI/IBWatchScreen.h"
#include "UI/IBPlanetWidget.h"
#include "UI/IBSectorBoardWidget.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBStyleKit.h"
#include "UI/IBPaintKit.h"
#include "Online/IBWatchBoard.h"
#include "Online/IBWatchTypes.h"
#include "Online/IBSessionSubsystem.h"
#include "Items/IBPlayerState.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/GameStateBase.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Widgets/Layout/SBorder.h"
#include "Components/Image.h"
#include "Components/Spacer.h"
#include "Blueprint/WidgetTree.h"
#include "Misc/PackageName.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "TimerManager.h"

namespace IBWatchPresentation
{
	class SCardBorder final : public SBorder
	{
	public:
		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
			FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const FVector2D Size = Geo.GetLocalSize();
			const float W = static_cast<float>(Size.X), H = static_cast<float>(Size.Y);
			const float C = FMath::Min(12.f, FMath::Min(W, H) * 0.1f);
			const TArray<FVector2f> Shape = { FVector2f(0,0), FVector2f(W-C,0), FVector2f(W,C),
				FVector2f(W,H), FVector2f(C,H), FVector2f(0,H-C) };
			const FLinearColor Tint = Style.GetColorAndOpacityTint();
			IBPaint::Fill(Out, LayerId, Geo, Shape, FVector2f(W*0.5f,H*0.5f), FLinearColor(0.008f,0.013f,0.022f,0.92f)*Tint);
			TArray<FVector2f> Edge = Shape;
			Edge.Add(Shape[0]);
			IBPaint::Line(Out, LayerId+1, Geo, Edge, FLinearColor(0.09f,0.19f,0.26f,0.8f)*Tint, 1.f);
			IBPaint::Seg(Out, LayerId+1, Geo, FVector2f(0,0), FVector2f(58,0), IBStyle::Cyan()*Tint, 2.f);
			return SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId+2, Style, bParentEnabled);
		}
	};
}

TSharedRef<SWidget> UIBWatchCardBorder::RebuildWidget()
{
	MyBorder = SNew(IBWatchPresentation::SCardBorder);
	if (GetChildrenCount() > 0)
	{
		CastChecked<UBorderSlot>(GetContentSlot())->BuildSlot(MyBorder.ToSharedRef());
	}
	return MyBorder.ToSharedRef();
}

namespace IBWatchUI
{
	constexpr float CardW = 400.f;   // == IBPlanetLayout::CardW
	constexpr float DiveSeconds = 1.3f;

	inline FLinearColor Dust() { return FLinearColor(0.31f, 0.36f, 0.41f); }
	inline FLinearColor Glass() { return FLinearColor(0.012f, 0.018f, 0.030f, 0.80f); }

	inline float EaseInOut(float T)
	{
		return T < 0.5f ? 4.f * T * T * T : 1.f - FMath::Pow(-2.f * T + 2.f, 3.f) / 2.f;
	}

	enum class EPrimary : uint8 { Cyan, Amber, Outline, Off };

	/** The DEPLOY button: filled cyan (host), amber when it overrides a proposal, outlined for a client's PROPOSE. */
	inline void StylePrimary(UButton* Button, UTextBlock* Label, UTextBlock* Chevron, EPrimary Style)
	{
		if (!Button) { return; }
		FLinearColor Fill = IBStyle::Cyan(), Hot = FLinearColor(0.34f, 0.85f, 0.95f), Text = FLinearColor(0.016f, 0.13f, 0.17f);
		FLinearColor Outline = FLinearColor::Transparent; float OutlineW = 0.f;
		switch (Style)
		{
		case EPrimary::Amber:   Fill = IBStyle::Amber(); Hot = FLinearColor(1.0f, 0.76f, 0.36f); Text = FLinearColor(0.10f, 0.07f, 0.02f); break;
		case EPrimary::Outline: Fill = FLinearColor(0.f, 0.f, 0.f, 0.f); Hot = FLinearColor(0.25f, 0.75f, 0.85f, 0.14f); Text = IBStyle::Cyan(); Outline = IBStyle::Cyan(); OutlineW = 1.5f; break;
		case EPrimary::Off:     Fill = FLinearColor(0.f, 0.f, 0.f, 0.f); Hot = Fill; Text = Dust(); Outline = IBStyle::Line(); OutlineW = 1.f; break;
		default: break;
		}
		FButtonStyle St = Button->GetStyle();
		St.Normal   = IBStyle::RoundedBrush(Fill, 3.f, Outline, OutlineW);
		St.Hovered  = IBStyle::RoundedBrush(Hot, 3.f, Outline, OutlineW);
		St.Pressed  = IBStyle::RoundedBrush(Fill * FLinearColor(0.8f, 0.8f, 0.8f, 1.f), 3.f, Outline, OutlineW);
		St.Disabled = IBStyle::RoundedBrush(FLinearColor(0.f, 0.f, 0.f, 0.f), 3.f, IBStyle::Line(), 1.f);
		St.NormalPadding  = FMargin(22.f, 14.f);
		St.PressedPadding = FMargin(22.f, 15.f, 22.f, 13.f);
		Button->SetStyle(St);
		if (Label) { Label->SetColorAndOpacity(FSlateColor(Text)); }
		if (Chevron) { Chevron->SetColorAndOpacity(FSlateColor(Text * FLinearColor(1.f, 1.f, 1.f, 0.8f))); }
	}

	/** Text-only "link" button (VIEW MISSION, WITHDRAW). */
	inline void StyleLink(UButton* Button)
	{
		if (!Button) { return; }
		FButtonStyle St = Button->GetStyle();
		const FLinearColor None(0.f, 0.f, 0.f, 0.f);
		St.Normal  = IBStyle::RoundedBrush(None, 2.f);
		St.Hovered = IBStyle::RoundedBrush(FLinearColor(1.f, 1.f, 1.f, 0.05f), 2.f);
		St.Pressed = IBStyle::RoundedBrush(FLinearColor(1.f, 1.f, 1.f, 0.02f), 2.f);
		St.NormalPadding  = FMargin(6.f, 8.f);
		St.PressedPadding = FMargin(6.f, 9.f, 6.f, 7.f);
		Button->SetStyle(St);
	}

	/** Small square chip (site selector, roster). */
	inline void StyleChip(UButton* Button, bool bOn, const FLinearColor& OnColor)
	{
		if (!Button) { return; }
		FButtonStyle St = Button->GetStyle();
		const FLinearColor Rest(1.f, 1.f, 1.f, 0.02f);
		St.Normal  = IBStyle::RoundedBrush(Rest, 2.f, bOn ? OnColor : IBStyle::Line(), 1.f);
		St.Hovered = IBStyle::RoundedBrush(FLinearColor(1.f, 1.f, 1.f, 0.06f), 2.f, bOn ? OnColor : IBStyle::TextLo(), 1.f);
		St.Pressed = IBStyle::RoundedBrush(IBStyle::Ink(), 2.f, OnColor, 1.f);
		St.NormalPadding  = FMargin(8.f, 5.f);
		St.PressedPadding = FMargin(8.f, 6.f, 8.f, 4.f);
		Button->SetStyle(St);
	}

	inline UTextBlock* Mono(UWidgetTree* Tree, const FText& Text, int32 Size, const FLinearColor& Color, int32 Tracking = 500)
	{
		return IBStyle::MakeText(Tree, Text, Size, Color, Tracking);
	}

	inline UBorder* Hairline(UWidgetTree* Tree)
	{
		UBorder* B = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		B->SetBrush(IBStyle::RoundedBrush(IBStyle::Line(), 0.f));
		B->SetPadding(FMargin(0.f, 0.5f));
		return B;
	}
}

// ============================================================================ lifecycle

void UIBWatchScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
	SelectedSector = IBWatch::HomeSectorId();
	SelectedId = DefaultSelection();
	EnsureBoard();
	RefreshAll();
	StartVisualTour();
}

void UIBWatchScreen::StartVisualTour()
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	// Explicit visual QA only. Use with -IBWatch, without the original -IBWatchShots.
	if (!FParse::Param(FCommandLine::Get(), TEXT("IBWatchVisualShots")) ||
		FParse::Param(FCommandLine::Get(), TEXT("IBWatchShots")) || !GetWorld() ||
		GetWorld()->GetNetMode() != NM_Standalone) { return; }
	const FString Dir = FPaths::ProjectSavedDir() / TEXT("Screenshots/WatchPolish");
	auto Step = [this](float At, TFunction<void()> Action)
	{
		FTimerHandle Handle;
		GetWorld()->GetTimerManager().SetTimer(Handle,
			FTimerDelegate::CreateWeakLambda(this, [Action]() { Action(); }), At, false);
	};
	auto Shot = [Dir](const TCHAR* Name) { FScreenshotRequest::RequestScreenshot(Dir / Name, true, false); };
	const FName InitialPick = SelectedId;
	Step(8.f, [Shot]() { Shot(TEXT("watch_orbit.png")); });
	Step(9.f, [this]() {
		for (const FIBSector& S : IBWatch::Sectors())
			if (!S.bLive) { HandleSectorPicked(S.Id); break; }
	});
	Step(11.f, [Shot]() { Shot(TEXT("watch_locked.png")); });
	Step(12.f, [this, InitialPick]() { HandlePicked(InitialPick); });
	Step(13.f, [this]() {
		for (const FIBDestination& D : IBWatch::Destinations())
			if (D.Kind == EIBDestinationKind::Range && D.CanDeploy()) { HandlePicked(D.Id); break; }
	});
	Step(15.f, [Shot]() { Shot(TEXT("watch_range.png")); });
	Step(16.f, [this]() {
		for (const FIBDestination& D : IBWatch::Destinations())
			if (D.Kind == EIBDestinationKind::Sector && D.CanDeploy()) { HandlePicked(D.Id); break; }
	});
	Step(18.f, [Shot]() { Shot(TEXT("watch_plains.png")); });
	Step(19.f, [this, InitialPick]() { HandlePicked(InitialPick); GoBoard(); });
	Step(22.f, [Shot]() { Shot(TEXT("watch_board_open.png")); });
	Step(23.f, [this]() { GoOrbit(); });
	Step(25.f, [Shot]() { Shot(TEXT("watch_orbit_back.png")); });
	Step(26.f, [this]() { HandlePrimary(); });
	Step(26.2f, [Shot]() { Shot(TEXT("watch_drop_start.png")); });
	Step(26.9f, [Shot]() { Shot(TEXT("watch_drop_mid.png")); });
	Step(27.7f, [Shot]() { Shot(TEXT("watch_drop_late.png")); });
	// GameInstance's timer survives the map travel, unlike the screen/world timers above.
	if (UGameInstance* GI = GetGameInstance())
	{
		FTimerHandle Handle;
		GI->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([Shot]() {
			Shot(TEXT("watch_arrival.png"));
		}), 36.f, false);
	}
#endif
}

void UIBWatchScreen::NativeDestruct()
{
	if (BoardState && IsValid(BoardState))
	{
		BoardState->OnChanged.RemoveDynamic(this, &UIBWatchScreen::HandleBoardChanged);
	}
	BoardState = nullptr;
	Super::NativeDestruct();
}

void UIBWatchScreen::NativeScreenOpened()
{
	Super::NativeScreenOpened();
	EnsureBoard();
	if (SelectedSector.IsNone()) { SelectedSector = IBWatch::HomeSectorId(); }
	if (SelectedId.IsNone()) { SelectedId = DefaultSelection(); }
	RefreshAll();
}

FReply UIBWatchScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape && bBoardView)
	{
		GoOrbit();
		return FReply::Handled();
	}
	if (InKeyEvent.GetKey() == EKeys::Enter && !InKeyEvent.IsRepeat())
	{
		HandlePrimary();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

// ============================================================================ layout

void UIBWatchScreen::BuildLayout()
{
	if (!WidgetTree || Planet) { return; }

	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!WidgetTree->RootWidget)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	if (!Root) { return; }

	// ---- the glass: the planet, full-bleed ----
	Planet = CreateWidget<UIBPlanetWidget>(GetOwningPlayer(), UIBPlanetWidget::StaticClass());
	if (Planet)
	{
		Planet->OnSectorPicked.AddDynamic(this, &UIBWatchScreen::HandleSectorPicked);
		Planet->OnSectorOpened.AddDynamic(this, &UIBWatchScreen::HandleSectorOpened);
		if (UOverlaySlot* S = Root->AddChildToOverlay(Planet))
		{
			S->SetHorizontalAlignment(HAlign_Fill);
			S->SetVerticalAlignment(VAlign_Fill);
		}
	}

	// ---- the breach board (sector view), positioned by BoardRect every tick ----
	Shade = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Shade->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
	Shade->SetVisibility(ESlateVisibility::Collapsed);
	if (UOverlaySlot* S = Root->AddChildToOverlay(Shade))
	{
		S->SetHorizontalAlignment(HAlign_Fill);
		S->SetVerticalAlignment(VAlign_Fill);
	}

	BoardCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
	BoardCanvas->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	Board = CreateWidget<UIBSectorBoardWidget>(GetOwningPlayer(), UIBSectorBoardWidget::StaticClass());
	if (Board)
	{
		Board->OnDestinationPicked.AddDynamic(this, &UIBWatchScreen::HandlePicked);
		BoardFrame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		BoardFrame->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.004f, 0.008f, 0.014f, 0.86f), 3.f, IBStyle::Cyan() * FLinearColor(1.f, 1.f, 1.f, 0.35f), 1.f));
		BoardFrame->SetPadding(FMargin(0.f));
		BoardFrame->SetContent(Board);
		BoardFrame->SetRenderOpacity(0.f);
		BoardFrame->SetVisibility(ESlateVisibility::Collapsed);
		BoardSlot = BoardCanvas->AddChildToCanvas(BoardFrame);
		if (BoardSlot)
		{
			BoardSlot->SetAutoSize(false);
			BoardSlot->SetPosition(FVector2D(92.0, 150.0));
			BoardSlot->SetSize(FVector2D(900.0, 600.0));
		}
	}
	if (UOverlaySlot* S = Root->AddChildToOverlay(BoardCanvas))
	{
		S->SetHorizontalAlignment(HAlign_Fill);
		S->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- HUD (fades during the drop) ----
	Hud = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	Hud->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	BuildHeader(Hud);
	BuildRoster(Hud);
	BuildCard(Hud);
	BuildFooter(Hud);
	if (UOverlaySlot* S = Root->AddChildToOverlay(Hud))
	{
		S->SetHorizontalAlignment(HAlign_Fill);
		S->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- the white-out ----
	Flash = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Flash->SetBrushColor(FLinearColor(1.f, 1.f, 1.f, 0.f));
	Flash->SetVisibility(ESlateVisibility::Collapsed);
	if (UOverlaySlot* S = Root->AddChildToOverlay(Flash))
	{
		S->SetHorizontalAlignment(HAlign_Fill);
		S->SetVerticalAlignment(VAlign_Fill);
	}
}

void UIBWatchScreen::BuildHeader(UOverlay* Root)
{
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Box->AddChildToVerticalBox(IBWatchUI::Mono(WidgetTree, NSLOCTEXT("IBWatch", "Eyebrow", "IRON BREACH  ·  DEFENSE FORCE  ·  CARROW COMMAND"), 9, IBStyle::TextLo(), 600));

	UHorizontalBox* Title = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Title->AddChildToHorizontalBox(IBStyle::MakeText(WidgetTree, FText::FromString(TEXT("//")), 24, IBStyle::Cyan(), 300));
	if (UHorizontalBoxSlot* S = Title->AddChildToHorizontalBox(IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBWatch", "Title", "THE WATCH"), 24, IBStyle::TextHi(), 300)))
	{
		S->SetPadding(FMargin(14.f, 0.f, 0.f, 0.f));
	}
	if (UVerticalBoxSlot* S = Box->AddChildToVerticalBox(Title)) { S->SetPadding(FMargin(0.f, 4.f, 0.f, 4.f)); }

	UHorizontalBox* Sub = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	HeaderSubText = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 450);
	HeaderSubHi = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 9, IBStyle::Cyan(), 450);
	Sub->AddChildToHorizontalBox(HeaderSubText);
	Sub->AddChildToHorizontalBox(HeaderSubHi);
	Box->AddChildToVerticalBox(Sub);

	Crumbs = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* OrbitLabel = nullptr;
	UButton* OrbitButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWatch", "CrumbOrbit", "<  ORBIT"), 9, false, &OrbitLabel);
	IBWatchUI::StyleChip(OrbitButton, false, IBStyle::Cyan());
	OrbitButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleView);
	Crumbs->AddChildToHorizontalBox(OrbitButton);
	if (UHorizontalBoxSlot* S = Crumbs->AddChildToHorizontalBox(IBWatchUI::Mono(WidgetTree, NSLOCTEXT("IBWatch", "CrumbBoard", "›   CARROW SECTOR  ·  BREACH BOARD"), 9, IBStyle::TextHi(), 450)))
	{
		S->SetPadding(FMargin(12.f, 0.f, 0.f, 0.f));
		S->SetVerticalAlignment(VAlign_Center);
	}
	Crumbs->SetVisibility(ESlateVisibility::Collapsed);
	if (UVerticalBoxSlot* S = Box->AddChildToVerticalBox(Crumbs)) { S->SetPadding(FMargin(0.f, 14.f, 0.f, 0.f)); }

	if (UOverlaySlot* S = Root->AddChildToOverlay(Box))
	{
		S->SetHorizontalAlignment(HAlign_Left);
		S->SetVerticalAlignment(VAlign_Top);
		S->SetPadding(FMargin(92.f, 26.f, 0.f, 0.f));
	}
}

void UIBWatchScreen::BuildRoster(UOverlay* Root)
{
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	NetText = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 600);
	if (UVerticalBoxSlot* S = Box->AddChildToVerticalBox(NetText)) { S->SetHorizontalAlignment(HAlign_Right); }

	RosterRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UVerticalBoxSlot* S = Box->AddChildToVerticalBox(RosterRow))
	{
		S->SetHorizontalAlignment(HAlign_Right);
		S->SetPadding(FMargin(0.f, 10.f, 0.f, 0.f));
	}
	if (UOverlaySlot* S = Root->AddChildToOverlay(Box))
	{
		S->SetHorizontalAlignment(HAlign_Right);
		S->SetVerticalAlignment(VAlign_Top);
		S->SetPadding(FMargin(0.f, 28.f, IBWatchUI::CardW + 48.f, 0.f));
	}
}

void UIBWatchScreen::BuildCard(UOverlay* Root)
{
	UVerticalBox* Card = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	NameText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 22, IBStyle::TextHi(), 200);
	NameText->SetAutoWrapText(true);
	IBStyle::UseDisplayFace(NameText);
	Card->AddChildToVerticalBox(NameText);
	SubText = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 500);
	if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(SubText)) { S->SetPadding(FMargin(0.f, 3.f, 0.f, 0.f)); }

	// site selector: the sector's destinations as chips
	SitesRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	for (int32 i = 0; i < 6; ++i)
	{
		UTextBlock* Lbl = nullptr;
		UButton* B = IBStyle::MakeButton(WidgetTree, FText::GetEmpty(), 8, false, &Lbl);
		IBWatchUI::StyleChip(B, false, IBStyle::Cyan());
		switch (i)
		{
		case 0: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite0); break;
		case 1: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite1); break;
		case 2: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite2); break;
		case 3: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite3); break;
		case 4: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite4); break;
		default: B->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSite5); break;
		}
		B->SetVisibility(ESlateVisibility::Collapsed);
		if (UHorizontalBoxSlot* S = SitesRow->AddChildToHorizontalBox(B)) { S->SetPadding(FMargin(0.f, 0.f, 6.f, 0.f)); }
		SiteButtons.Add(B);
		SiteLabels.Add(Lbl);
	}
	if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(SitesRow)) { S->SetPadding(FMargin(0.f, 10.f, 0.f, 0.f)); }

	// recon still
	{
		UOverlay* Thumb = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		ThumbFallback = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		ThumbFallback->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.025f, 0.035f, 0.055f), 2.f, IBStyle::Line(), 1.f));
		ThumbFallback->SetHorizontalAlignment(HAlign_Center);
		ThumbFallback->SetVerticalAlignment(VAlign_Center);
		ThumbFallbackText = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 8, IBStyle::TextLo(), 500);
		ThumbFallback->SetContent(ThumbFallbackText);
		if (UOverlaySlot* S = Thumb->AddChildToOverlay(ThumbFallback)) { S->SetHorizontalAlignment(HAlign_Fill); S->SetVerticalAlignment(VAlign_Fill); }

		ThumbImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		ThumbImage->SetVisibility(ESlateVisibility::Collapsed);
		if (UOverlaySlot* S = Thumb->AddChildToOverlay(ThumbImage)) { S->SetHorizontalAlignment(HAlign_Fill); S->SetVerticalAlignment(VAlign_Fill); }

		ThumbTagFrame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		ThumbTagFrame->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.008f, 0.012f, 0.022f, 0.7f), 2.f, IBStyle::Amber(), 1.f));
		ThumbTagFrame->SetPadding(FMargin(6.f, 3.f));
		ThumbTag = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 8, IBStyle::Amber(), 600);
		ThumbTagFrame->SetContent(ThumbTag);
		if (UOverlaySlot* S = Thumb->AddChildToOverlay(ThumbTagFrame)) { S->SetHorizontalAlignment(HAlign_Right); S->SetVerticalAlignment(VAlign_Top); S->SetPadding(FMargin(0.f, 8.f, 10.f, 0.f)); }

		UBorder* CaptionShade = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		CaptionShade->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.003f, 0.005f, 0.009f, 0.72f), 0.f));
		CaptionShade->SetPadding(FMargin(0.f, 17.f));
		CaptionShade->SetVisibility(ESlateVisibility::HitTestInvisible);
		if (UOverlaySlot* S = Thumb->AddChildToOverlay(CaptionShade)) { S->SetHorizontalAlignment(HAlign_Fill); S->SetVerticalAlignment(VAlign_Bottom); }

		ThumbCaption = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 8, IBStyle::TextHi() * FLinearColor(1.f, 1.f, 1.f, 0.75f), 600);
		if (UOverlaySlot* S = Thumb->AddChildToOverlay(ThumbCaption)) { S->SetHorizontalAlignment(HAlign_Left); S->SetVerticalAlignment(VAlign_Bottom); S->SetPadding(FMargin(10.f, 0.f, 0.f, 8.f)); }

		USizeBox* ThumbSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		ThumbSize->SetHeightOverride((IBWatchUI::CardW - 48.f) * 9.f / 16.f);
		ThumbSize->AddChild(Thumb);
		if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(ThumbSize)) { S->SetPadding(FMargin(0.f, 12.f, 0.f, 0.f)); }
	}

	// threat class + meter
	{
		UBorder* Block = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Block->SetBrush(IBStyle::RoundedBrush(FLinearColor(1.f, 1.f, 1.f, 0.03f), 2.f, IBStyle::Line(), 1.f));
		Block->SetPadding(FMargin(14.f, 10.f));
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UVerticalBox* Left = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		ThreatLabel = IBWatchUI::Mono(WidgetTree, NSLOCTEXT("IBWatch", "ThreatLabel", "THREAT CLASS"), 8, IBStyle::Amber(), 700);
		ThreatValue = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 18, IBStyle::Amber(), 300);
		IBStyle::UseDisplayFace(ThreatValue);
		Left->AddChildToVerticalBox(ThreatLabel);
		if (UVerticalBoxSlot* S = Left->AddChildToVerticalBox(ThreatValue)) { S->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f)); }
		if (UHorizontalBoxSlot* S = Row->AddChildToHorizontalBox(Left)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetVerticalAlignment(VAlign_Center); }
		UHorizontalBox* Meter = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		for (int32 i = 0; i < 5; ++i)
		{
			UBorder* Bar = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
			Bar->SetBrush(IBStyle::RoundedBrush(IBStyle::Line(), 1.f));
			USizeBox* BarSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
			BarSize->SetWidthOverride(9.f);
			BarSize->SetHeightOverride(16.f);
			BarSize->AddChild(Bar);
			if (UHorizontalBoxSlot* S = Meter->AddChildToHorizontalBox(BarSize)) { S->SetPadding(FMargin(0.f, 0.f, 4.f, 0.f)); S->SetVerticalAlignment(VAlign_Center); }
			MeterBars.Add(Bar);
		}
		if (UHorizontalBoxSlot* S = Row->AddChildToHorizontalBox(Meter)) { S->SetVerticalAlignment(VAlign_Center); }
		Block->SetContent(Row);
		if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(Block)) { S->SetPadding(FMargin(0.f, 12.f, 0.f, 0.f)); }
	}

	// mission type / objective
	auto MakeRow = [this, Card](const FText& Label, UBorder*& OutBullet, UTextBlock*& OutValue, bool bWrap)
	{
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		OutBullet = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		OutBullet->SetBrush(IBStyle::RoundedBrush(IBStyle::TextLo(), 1.f));
		USizeBox* BulletSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		BulletSize->SetWidthOverride(7.f);
		BulletSize->SetHeightOverride(7.f);
		BulletSize->AddChild(OutBullet);
		if (UHorizontalBoxSlot* S = Row->AddChildToHorizontalBox(BulletSize)) { S->SetPadding(FMargin(0.f, 5.f, 12.f, 0.f)); S->SetVerticalAlignment(VAlign_Top); }
		UVerticalBox* Col = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Col->AddChildToVerticalBox(IBWatchUI::Mono(WidgetTree, Label, 8, IBStyle::TextLo(), 700));
		OutValue = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 12, IBStyle::TextHi() * FLinearColor(1.f, 1.f, 1.f, 0.9f), 0);
		OutValue->SetAutoWrapText(bWrap);
		if (bWrap) { OutValue->SetLineHeightPercentage(1.2f); }
		if (UVerticalBoxSlot* S = Col->AddChildToVerticalBox(OutValue)) { S->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f)); }
		if (UHorizontalBoxSlot* S = Row->AddChildToHorizontalBox(Col)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); }
		if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(Row)) { S->SetPadding(FMargin(0.f, 12.f, 0.f, 0.f)); }
	};
	UBorder* B0 = nullptr; UTextBlock* V0 = nullptr;
	MakeRow(NSLOCTEXT("IBWatch", "MissionType", "MISSION TYPE"), B0, V0, false);
	TypeBullet = B0; TypeValue = V0;
	UBorder* B1 = nullptr; UTextBlock* V1 = nullptr;
	MakeRow(NSLOCTEXT("IBWatch", "Objective", "OBJECTIVE"), B1, V1, true);
	ObjBullet = B1; ObjValue = V1;

	// fireteam | mech deployment
	{
		UVerticalBox* Wrap = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Wrap->AddChildToVerticalBox(IBWatchUI::Hairline(WidgetTree));
		UHorizontalBox* Two = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		auto MakeCol = [this](const FText& Label, UTextBlock*& OutValue) -> UVerticalBox*
		{
			UVerticalBox* Col = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
			Col->AddChildToVerticalBox(IBWatchUI::Mono(WidgetTree, Label, 8, IBStyle::TextLo(), 700));
			OutValue = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 12, IBStyle::TextHi() * FLinearColor(1.f, 1.f, 1.f, 0.9f), 0);
			OutValue->SetAutoWrapText(true);
			if (UVerticalBoxSlot* S = Col->AddChildToVerticalBox(OutValue)) { S->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f)); }
			return Col;
		};
		UTextBlock* T = nullptr; UTextBlock* M = nullptr;
		if (UHorizontalBoxSlot* S = Two->AddChildToHorizontalBox(MakeCol(NSLOCTEXT("IBWatch", "Fireteam", "FIRETEAM"), T))) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetPadding(FMargin(0.f, 10.f, 12.f, 10.f)); }
		UBorder* Sep = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Sep->SetBrush(IBStyle::RoundedBrush(IBStyle::Line(), 0.f));
		Sep->SetPadding(FMargin(0.5f, 0.f));
		if (UHorizontalBoxSlot* S = Two->AddChildToHorizontalBox(Sep)) { S->SetPadding(FMargin(0.f, 8.f, 0.f, 8.f)); }
		if (UHorizontalBoxSlot* S = Two->AddChildToHorizontalBox(MakeCol(NSLOCTEXT("IBWatch", "Mech", "MECH DEPLOYMENT"), M))) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetPadding(FMargin(14.f, 10.f, 0.f, 10.f)); }
		TeamValue = T; MechValue = M;
		Wrap->AddChildToVerticalBox(Two);
		Wrap->AddChildToVerticalBox(IBWatchUI::Hairline(WidgetTree));
		if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(Wrap)) { S->SetPadding(FMargin(0.f, 12.f, 0.f, 0.f)); }
	}

	NarratorText = IBWatchUI::Mono(WidgetTree, FText::GetEmpty(), 9, IBStyle::Cyan(), 250);
	NarratorText->SetAutoWrapText(true);
	if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(NarratorText)) { S->SetPadding(FMargin(0.f, 10.f, 0.f, 8.f)); }

	// DEPLOY
	PrimaryButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	{
		UHorizontalBox* Inner = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		PrimaryLabel = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBWatch", "Deploy", "DEPLOY"), 17, FLinearColor::Black, 500);
		PrimaryLabel->SetShadowColorAndOpacity(FLinearColor::Transparent);
		if (UHorizontalBoxSlot* S = Inner->AddChildToHorizontalBox(PrimaryLabel)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetVerticalAlignment(VAlign_Center); }
		PrimaryChevron = IBStyle::MakeText(WidgetTree, FText::FromString(TEXT("››")), 18, FLinearColor::Black, 0);
		PrimaryChevron->SetShadowColorAndOpacity(FLinearColor::Transparent);
		if (UHorizontalBoxSlot* S = Inner->AddChildToHorizontalBox(PrimaryChevron)) { S->SetVerticalAlignment(VAlign_Center); }
		PrimaryButton->AddChild(Inner);
	}
	IBWatchUI::StylePrimary(PrimaryButton, PrimaryLabel, PrimaryChevron, IBWatchUI::EPrimary::Cyan);
	PrimaryButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandlePrimary);
	Card->AddChildToVerticalBox(PrimaryButton);

	// WITHDRAW / STAND DOWN
	UTextBlock* RawSecondary = nullptr;
	SecondaryButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWatch", "Withdraw", "WITHDRAW"), 9, false, &RawSecondary);
	SecondaryLabel = RawSecondary;
	SecondaryLabel->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	IBWatchUI::StyleLink(SecondaryButton);
	SecondaryButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleSecondary);
	SecondaryButton->SetVisibility(ESlateVisibility::Collapsed);
	if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(SecondaryButton)) { S->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f)); }

	// VIEW MISSION
	ViewButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	{
		UHorizontalBox* Inner = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		ViewLabel = IBWatchUI::Mono(WidgetTree, NSLOCTEXT("IBWatch", "ViewMission", "VIEW MISSION  ·  BREACH BOARD"), 9, IBStyle::TextLo(), 600);
		if (UHorizontalBoxSlot* S = Inner->AddChildToHorizontalBox(ViewLabel)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetVerticalAlignment(VAlign_Center); }
		if (UHorizontalBoxSlot* S = Inner->AddChildToHorizontalBox(IBStyle::MakeText(WidgetTree, FText::FromString(TEXT("››")), 14, IBStyle::TextLo(), 0))) { S->SetVerticalAlignment(VAlign_Center); }
		ViewButton->AddChild(Inner);
	}
	IBWatchUI::StyleLink(ViewButton);
	ViewButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleView);
	if (UVerticalBoxSlot* S = Card->AddChildToVerticalBox(ViewButton)) { S->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f)); }

	CardPanel = WidgetTree->ConstructWidget<UIBWatchCardBorder>(UIBWatchCardBorder::StaticClass());
	CardPanel->SetBrush(IBStyle::RoundedBrush(IBWatchUI::Glass(), 0.f));
	CardPanel->SetPadding(FMargin(24.f, 22.f, 24.f, 16.f));
	CardPanel->SetContent(Card);
	USizeBox* CardSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardSize->SetWidthOverride(IBWatchUI::CardW);
	CardSize->AddChild(CardPanel);
	if (UOverlaySlot* S = Root->AddChildToOverlay(CardSize))
	{
		S->SetHorizontalAlignment(HAlign_Right);
		S->SetVerticalAlignment(VAlign_Center);
		S->SetPadding(FMargin(0.f, 0.f, 24.f, 0.f));
	}
}

void UIBWatchScreen::BuildFooter(UOverlay* Root)
{
	UTextBlock* Hints = IBWatchUI::Mono(WidgetTree,
		NSLOCTEXT("IBWatch", "Hints", "DRAG  ROTATE        SCROLL  ZOOM        SELECT  ·  DOUBLE-CLICK OPENS THE BOARD        ESC  BACK"), 8, IBStyle::TextLo(), 500);
	if (UOverlaySlot* S = Root->AddChildToOverlay(Hints))
	{
		S->SetHorizontalAlignment(HAlign_Left);
		S->SetVerticalAlignment(VAlign_Bottom);
		S->SetPadding(FMargin(92.f, 0.f, 0.f, 30.f));
	}

	UTextBlock* RawLeave = nullptr;
	LeaveButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWatch", "Leave", "LEAVE THE WATCH"), 8, false, &RawLeave);
	LeaveLabel = RawLeave;
	LeaveLabel->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	IBWatchUI::StyleChip(LeaveButton, false, IBStyle::Cyan());
	LeaveButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleLeave);
	if (UOverlaySlot* S = Root->AddChildToOverlay(LeaveButton))
	{
		S->SetHorizontalAlignment(HAlign_Right);
		S->SetVerticalAlignment(VAlign_Bottom);
		S->SetPadding(FMargin(0.f, 0.f, 24.f, 26.f));
	}
}

// ============================================================================ state plumbing

void UIBWatchScreen::EnsureBoard()
{
	// Cached menu screens outlive a world: a board from the last map is a corpse.
	if (BoardState && !IsValid(BoardState))
	{
		BoardState = nullptr;
	}
	if (BoardState) { return; }
	AIBWatchBoard* Found = AIBWatchBoard::Get(GetWorld());
	if (!Found) { return; }
	BoardState = Found;
	BoardState->OnChanged.AddDynamic(this, &UIBWatchScreen::HandleBoardChanged);
	// Someone already put something forward: look at it.
	if (SelectedId.IsNone() || SelectedId == DefaultSelection())
	{
		if (!BoardState->GetArmedId().IsNone()) { SelectedId = BoardState->GetArmedId(); }
		else if (!BoardState->GetProposedId().IsNone()) { SelectedId = BoardState->GetProposedId(); }
	}
	RefreshAll();
}

void UIBWatchScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (!BoardState || !IsValid(BoardState)) { EnsureBoard(); }

	const FVector2D Size = MyGeometry.GetLocalSize();
	if (Size.X > 8.0 && Size.Y > 8.0) { LastScreenSize = Size; }
	TickViews(LastScreenSize, InDeltaTime);

	RefreshAccumulator += InDeltaTime;
	if (RefreshAccumulator >= 0.2f)
	{
		RefreshAccumulator = 0.f;
		RefreshNarrator();
		RefreshButtons();
	}
	RosterAccumulator += InDeltaTime;
	if (RosterAccumulator >= 1.0f)
	{
		RosterAccumulator = 0.f;
		RefreshRoster();
	}

	if (Board && BoardState)
	{
		Board->SetMarks(SelectedId, BoardState->GetProposedId(), BoardState->GetArmedId(), BoardState->GetCurrentId());
	}
	else if (Board)
	{
		Board->SetMarks(SelectedId, NAME_None, NAME_None, IBWatch::DestinationForMap(GetWorld() ? GetWorld()->GetMapName() : FString()));
	}
}

void UIBWatchScreen::TickViews(const FVector2D& ScreenSize, float DeltaTime)
{
	// orbit <-> board
	const float Target = bBoardView ? 1.f : 0.f;
	if (DiveT != Target)
	{
		DiveT = FMath::FInterpConstantTo(DiveT, Target, DeltaTime, 1.f / IBWatchUI::DiveSeconds);
	}
	const float Eased = IBWatchUI::EaseInOut(DiveT);
	if (Planet) { Planet->SetDive(Eased); }

	const float BoardAlpha = FMath::Clamp((Eased - 0.5f) / 0.45f, 0.f, 1.f);
	float BoardScale = 0.72f + 0.28f * BoardAlpha;
	FVector2D Pivot(0.5, 0.5);

	// the drop
	float K = -1.f;
	if (BoardState && IsValid(BoardState) && BoardState->IsArmed())
	{
		const float Secs = BoardState->GetSecondsToDeploy();
		K = 1.f - FMath::Clamp(Secs / IBWatch::DeployDropSeconds, 0.f, 1.f);
	}
	if (K >= 0.f)
	{
		const FName ArmedId = BoardState->GetArmedId();
		if (!bDropping)
		{
			bDropping = true;
			RefreshCallout();
		}
		if (Planet) { Planet->SetDrop(K, SectorOf(ArmedId)); }
		if (Hud)
		{
			// Slide the HUD out before the cut. RoundedBox outlines cannot reliably inherit opacity.
			const float Exit = IBWatchUI::EaseInOut(FMath::Clamp(K / 0.2f, 0.f, 1.f));
			Hud->SetRenderTranslation(FVector2D(0, -10.f * Exit));
			const ESlateVisibility Want = K > 0.2f ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible;
			if (Hud->GetVisibility() != Want) { Hud->SetVisibility(Want); }
		}
		if (const FIBDestination* Armed = IBWatch::Find(ArmedId))
		{
			Pivot = Armed->BoardPosition;
			BoardScale *= 1.f + 2.6f * IBWatchUI::EaseInOut(FMath::Clamp((K - 0.25f) / 0.6f, 0.f, 1.f));
		}
		if (Flash)
		{
			const float White = FMath::Clamp((K - 0.8f) / 0.1f, 0.f, 1.f);
			const float Black = FMath::Clamp((K - 0.9f) / 0.1f, 0.f, 1.f);
			Flash->SetBrushColor(FLinearColor(1.f - Black, 1.f - Black, 1.f - Black, FMath::Max(White, Black)));
			Flash->SetVisibility(White > 0.001f ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
	}
	else if (bDropping)
	{
		bDropping = false;
		if (Planet) { Planet->SetDrop(-1.f, NAME_None); }
		if (Hud) { Hud->SetVisibility(ESlateVisibility::SelfHitTestInvisible); Hud->SetRenderTranslation(FVector2D::ZeroVector); }
		if (Flash) { Flash->SetVisibility(ESlateVisibility::Collapsed); }
		RefreshCallout();
	}

	if (BoardFrame)
	{
		FVector2D BPos, BSize;
		UIBPlanetWidget::BoardRect(ScreenSize, BPos, BSize);
		if (BoardSlot)
		{
			BoardSlot->SetPosition(BPos);
			BoardSlot->SetSize(BSize);
		}
		BoardFrame->SetRenderOpacity(BoardAlpha);
		BoardFrame->SetRenderTransformPivot(Pivot);
		BoardFrame->SetRenderScale(FVector2D(BoardScale, BoardScale));
		const ESlateVisibility Want = BoardAlpha > 0.01f ? (K >= 0.f ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Visible) : ESlateVisibility::Collapsed;
		if (BoardFrame->GetVisibility() != Want) { BoardFrame->SetVisibility(Want); }
	}
	if (Shade)
	{
		const float ShadeA = 0.84f * Eased * (K >= 0.f ? 1.f - FMath::Clamp((K - 0.25f) / 0.4f, 0.f, 1.f) : 1.f);
		Shade->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, ShadeA));
		const ESlateVisibility Want = ShadeA > 0.005f ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
		if (Shade->GetVisibility() != Want) { Shade->SetVisibility(Want); }
	}
	if (Crumbs)
	{
		const ESlateVisibility Want = bBoardView ? ESlateVisibility::Visible : ESlateVisibility::Collapsed;
		if (Crumbs->GetVisibility() != Want) { Crumbs->SetVisibility(Want); }
	}
}

void UIBWatchScreen::GoBoard()
{
	const FIBSector* S = IBWatch::FindSector(SelectedSector);
	if (!S || !S->bLive) { return; }
	bBoardView = true;
	RefreshAll();
}

void UIBWatchScreen::GoOrbit()
{
	bBoardView = false;
	RefreshAll();
}

void UIBWatchScreen::HandleBoardChanged()
{
	// A fresh proposal or arm pulls everyone's eyes to it.
	if (BoardState)
	{
		FName Pull;
		if (!BoardState->GetArmedId().IsNone()) { Pull = BoardState->GetArmedId(); }
		else if (!BoardState->GetProposedId().IsNone()) { Pull = BoardState->GetProposedId(); }
		if (!Pull.IsNone())
		{
			SelectedId = Pull;
			SelectedSector = SectorOf(Pull);
		}
	}
	RefreshAll();
}

void UIBWatchScreen::HandlePicked(FName DestinationId)
{
	SelectedId = DestinationId;
	SelectedSector = SectorOf(DestinationId);
	RefreshAll();
}

void UIBWatchScreen::FocusDestination(FName DestinationId)
{
	if (!IBWatch::Find(DestinationId)) { return; }
	HandlePicked(DestinationId);
	GoBoard();
}

void UIBWatchScreen::HandleSectorPicked(FName SectorId)
{
	SelectedSector = SectorId;
	const FIBSector* S = IBWatch::FindSector(SectorId);
	if (S && S->bLive && SectorOf(SelectedId) != SectorId)
	{
		for (const FIBDestination& D : IBWatch::Destinations())
		{
			if (D.SectorId == SectorId && D.CanDeploy() && D.Kind != EIBDestinationKind::Bastion) { SelectedId = D.Id; break; }
		}
	}
	RefreshAll();
}

void UIBWatchScreen::HandleSectorOpened(FName SectorId)
{
	HandleSectorPicked(SectorId);
	GoBoard();
}

void UIBWatchScreen::PickSite(int32 Index)
{
	if (Index < 0 || Index >= SiteIds.Num()) { return; }
	SelectedId = SiteIds[Index];
	RefreshAll();
}
void UIBWatchScreen::HandleSite0() { PickSite(0); }
void UIBWatchScreen::HandleSite1() { PickSite(1); }
void UIBWatchScreen::HandleSite2() { PickSite(2); }
void UIBWatchScreen::HandleSite3() { PickSite(3); }
void UIBWatchScreen::HandleSite4() { PickSite(4); }
void UIBWatchScreen::HandleSite5() { PickSite(5); }

bool UIBWatchScreen::IsHost() const
{
	const APlayerController* PC = GetOwningPlayer();
	return PC && PC->HasAuthority(); // listen-server host or standalone
}

bool UIBWatchScreen::IsOffline() const
{
	const UWorld* World = GetWorld();
	const UIBSessionSubsystem* Sessions = GetSessions();
	return World && World->GetNetMode() == NM_Standalone && (!Sessions || !Sessions->IsInSession());
}

int32 UIBWatchScreen::LocalPlayerId() const
{
	const APlayerState* PS = GetOwningPlayerState();
	return PS ? PS->GetPlayerId() : -1;
}

AIBPlayerState* UIBWatchScreen::LocalPlayerState() const
{
	APlayerController* PC = GetOwningPlayer();
	return PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
}

UIBSessionSubsystem* UIBWatchScreen::GetSessions() const
{
	UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
}

FName UIBWatchScreen::DefaultSelection() const
{
	const FName Here = BoardState ? BoardState->GetCurrentId()
		: IBWatch::DestinationForMap(GetWorld() ? GetWorld()->GetMapName() : FString());
	for (const FIBDestination& D : IBWatch::Destinations())
	{
		if (D.CanDeploy() && D.Id != Here && D.Kind != EIBDestinationKind::Bastion) { return D.Id; }
	}
	for (const FIBDestination& D : IBWatch::Destinations())
	{
		if (D.CanDeploy() && D.Id != Here) { return D.Id; }
	}
	return NAME_None;
}

FName UIBWatchScreen::SectorOf(FName DestinationId) const
{
	const FIBDestination* D = IBWatch::Find(DestinationId);
	return D && !D->SectorId.IsNone() ? D->SectorId : IBWatch::HomeSectorId();
}

const FIBSector* UIBWatchScreen::CurrentSector() const
{
	const FIBSector* S = IBWatch::FindSector(SelectedSector);
	return S ? S : IBWatch::FindSector(IBWatch::HomeSectorId());
}

// ============================================================================ refresh

void UIBWatchScreen::RefreshAll()
{
	RefreshHeader();
	RefreshRoster();
	RefreshCard();
	RefreshNarrator();
	RefreshButtons();
	RefreshCallout();
}

void UIBWatchScreen::RefreshHeader()
{
	if (HeaderSubText)
	{
		const FName Here = BoardState ? BoardState->GetCurrentId() : NAME_None;
		const FIBDestination* HereDest = IBWatch::Find(Here);
		const FString Where = HereDest ? HereDest->Name.ToString() : TEXT("IN TRANSIT");
		HeaderSubText->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  ORBITAL RELAY  ·  "), *Where)));
	}
	if (HeaderSubHi)
	{
		HeaderSubHi->SetText(FText::FromString(IsHost() ? TEXT("YOU HOLD THE TRIGGER") : TEXT("THE HOST HOLDS THE TRIGGER")));
	}
	if (NetText)
	{
		if (IsOffline())
		{
			NetText->SetText(NSLOCTEXT("IBWatch", "NetOffline", "OFF THE NET  —  SOLO"));
			NetText->SetColorAndOpacity(FSlateColor(IBStyle::Amber()));
		}
		else
		{
			NetText->SetText(NSLOCTEXT("IBWatch", "NetLive", "●  BREAKWATER NET  ·  LIVE"));
			NetText->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
		}
	}
	if (Board)
	{
		Board->SetNetLine(IsOffline() ? NSLOCTEXT("IBWatch", "BoardNetOff", "OFF THE NET") : NSLOCTEXT("IBWatch", "BoardNetLive", "BREAKWATER NET · LIVE"),
			IsOffline() ? IBStyle::Amber() : IBStyle::Cyan());
	}
}

void UIBWatchScreen::RefreshRoster()
{
	if (!RosterRow || !WidgetTree) { return; }
	RosterRow->ClearChildren();
	InviteButton = nullptr;

	struct FEntry { FString Name; int32 PlayerId; bool bLocal; };
	TArray<FEntry> Entries;
	if (const UWorld* World = GetWorld())
	{
		if (const AGameStateBase* GS = World->GetGameState())
		{
			for (const APlayerState* PS : GS->PlayerArray)
			{
				if (!PS) { continue; }
				const AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS);
				FEntry E;
				E.Name = IBPS ? IBPS->GetDisplayCallsign() : PS->GetPlayerName();
				E.PlayerId = PS->GetPlayerId();
				E.bLocal = (PS->GetPlayerId() == LocalPlayerId());
				Entries.Add(E);
			}
		}
	}
	// the host's PlayerState is made first: lowest id
	int32 HostId = MAX_int32;
	for (const FEntry& E : Entries) { HostId = FMath::Min(HostId, E.PlayerId); }
	if (IsHost() && Entries.Num() > 0) { HostId = LocalPlayerId(); }

	for (const FEntry& E : Entries)
	{
		const bool bHostEntry = (E.PlayerId == HostId);
		UBorder* Chip = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Chip->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.008f, 0.012f, 0.022f, 0.72f), 2.f, IBStyle::Line(), 1.f));
		Chip->SetPadding(FMargin(8.f, 5.f, 10.f, 5.f));
		UHorizontalBox* Inner = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UBorder* Dot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Dot->SetBrush(IBStyle::RoundedBrush(bHostEntry ? IBStyle::Amber() : IBStyle::Cyan(), 1.f));
		USizeBox* DotSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		DotSize->SetWidthOverride(5.f); DotSize->SetHeightOverride(5.f); DotSize->AddChild(Dot);
		if (UHorizontalBoxSlot* S = Inner->AddChildToHorizontalBox(DotSize)) { S->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f)); S->SetVerticalAlignment(VAlign_Center); }
		Inner->AddChildToHorizontalBox(IBWatchUI::Mono(WidgetTree, FText::FromString(E.Name.ToUpper()), 9, IBStyle::TextHi(), 400));
		Inner->AddChildToHorizontalBox(IBWatchUI::Mono(WidgetTree, FText::FromString(bHostEntry ? TEXT("  ·  HOST") : TEXT("  ·  LINKED")), 9, IBStyle::TextLo(), 400));
		Chip->SetContent(Inner);
		if (UHorizontalBoxSlot* S = RosterRow->AddChildToHorizontalBox(Chip)) { S->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f)); }
	}

	if (!IsOffline())
	{
		UTextBlock* Lbl = nullptr;
		InviteButton = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWatch", "Invite", "+  INVITE SQUAD"), 9, false, &Lbl);
		if (Lbl) { Lbl->SetColorAndOpacity(FSlateColor(IBStyle::Cyan())); }
		IBWatchUI::StyleChip(InviteButton, true, IBStyle::Cyan() * FLinearColor(1.f, 1.f, 1.f, 0.6f));
		InviteButton->OnClicked.AddDynamic(this, &UIBWatchScreen::HandleInvite);
		RosterRow->AddChildToHorizontalBox(InviteButton);
	}
}

void UIBWatchScreen::RefreshCard()
{
	const FIBSector* S = CurrentSector();
	if (!S)
	{
		if (NameText) { NameText->SetText(NSLOCTEXT("IBWatch", "PickPin", "PICK A PIN")); }
		return;
	}

	auto SetMeter = [this](int32 Level, const FLinearColor& Colr)
	{
		for (int32 i = 0; i < MeterBars.Num(); ++i)
		{
			if (MeterBars[i]) { MeterBars[i]->SetBrush(IBStyle::RoundedBrush(i < Level ? Colr : IBStyle::Line(), 1.f)); }
		}
	};

	if (!S->bLive)
	{
		const FLinearColor Colr = S->Color;
		if (NameText) { NameText->SetText(S->Name); }
		if (SubText) { SubText->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  LAT %.1f° %s"), *S->Region.ToString(), FMath::Abs(S->Latitude), S->Latitude < 0.f ? TEXT("S") : TEXT("N")))); }
		SiteIds.Reset();
		RefreshSites();
		RefreshThumb(nullptr, S);
		if (ThreatLabel) { ThreatLabel->SetColorAndOpacity(FSlateColor(Colr)); }
		if (ThreatValue) { ThreatValue->SetText(IBWatch::ThreatLevelLabel(S->ThreatLevel)); ThreatValue->SetColorAndOpacity(FSlateColor(Colr)); }
		SetMeter(S->ThreatLevel, Colr);
		if (TypeValue) { TypeValue->SetText(FText::FromString(TEXT("—"))); }
		if (ObjValue) { ObjValue->SetText(S->Brief); }
		if (TeamValue) { TeamValue->SetText(FText::FromString(TEXT("—"))); }
		if (MechValue) { MechValue->SetText(FText::FromString(TEXT("—"))); }
		if (TypeBullet) { TypeBullet->SetBrush(IBStyle::RoundedBrush(IBStyle::TextLo(), 1.f)); }
		if (ObjBullet) { ObjBullet->SetBrush(IBStyle::RoundedBrush(IBStyle::TextLo(), 1.f)); }
		return;
	}

	const FIBDestination* D = IBWatch::Find(SelectedId);
	if (!D || D->SectorId != S->Id)
	{
		for (const FIBDestination& X : IBWatch::Destinations())
		{
			if (X.SectorId == S->Id && X.CanDeploy() && X.Kind != EIBDestinationKind::Bastion) { SelectedId = X.Id; D = &X; break; }
		}
	}
	// the sector's sites (everything but the Bastion itself)
	SiteIds.Reset();
	for (const FIBDestination& X : IBWatch::Destinations())
	{
		if (X.SectorId == S->Id && X.Kind != EIBDestinationKind::Bastion && X.Kind != EIBDestinationKind::Locked) { SiteIds.Add(X.Id); }
	}
	RefreshSites();
	if (!D)
	{
		if (NameText) { NameText->SetText(S->Name); }
		return;
	}

	const FLinearColor Kind = IBWatch::KindColor(D->Kind);
	const FLinearColor Colr = D->Kind == EIBDestinationKind::Locked ? IBStyle::TextLo() : Kind;
	if (NameText) { NameText->SetText(D->Name); }
	if (SubText)
	{
		SubText->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s"), *S->Name.ToString(), *D->Codename.ToString())));
	}
	RefreshThumb(D, S);
	if (ThreatLabel) { ThreatLabel->SetColorAndOpacity(FSlateColor(Colr)); }
	if (ThreatValue)
	{
		ThreatValue->SetText(D->ThreatLevel > 0 ? IBWatch::ThreatLevelLabel(D->ThreatLevel)
			: (D->Kind == EIBDestinationKind::Range ? NSLOCTEXT("IBWatch", "LiveFire", "LIVE FIRE") : NSLOCTEXT("IBWatch", "NoThreat", "NO THREAT")));
		ThreatValue->SetColorAndOpacity(FSlateColor(Colr));
	}
	SetMeter(D->ThreatLevel, Colr);
	if (TypeValue) { TypeValue->SetText(D->MissionType); }
	if (ObjValue) { ObjValue->SetText(D->Brief); }
	if (TeamValue) { TeamValue->SetText(D->Fireteam.IsEmpty() ? FText::FromString(FString::Printf(TEXT("%d–%d OPERATORS"), D->SquadMin, D->SquadMax)) : D->Fireteam); }
	if (MechValue) { MechValue->SetText(D->MechDeployment.IsEmpty() ? FText::FromString(TEXT("—")) : D->MechDeployment); }
	if (TypeBullet) { TypeBullet->SetBrush(IBStyle::RoundedBrush(Colr, 1.f)); }
	if (ObjBullet) { ObjBullet->SetBrush(IBStyle::RoundedBrush(Colr, 1.f)); }
}

void UIBWatchScreen::RefreshSites()
{
	for (int32 i = 0; i < SiteButtons.Num(); ++i)
	{
		UButton* B = SiteButtons[i];
		UTextBlock* L = SiteLabels[i];
		if (!B) { continue; }
		if (i >= SiteIds.Num())
		{
			B->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const FIBDestination* D = IBWatch::Find(SiteIds[i]);
		if (!D) { B->SetVisibility(ESlateVisibility::Collapsed); continue; }
		const bool bOn = (D->Id == SelectedId);
		const FLinearColor Kind = D->Kind == EIBDestinationKind::Locked ? IBStyle::TextLo() : IBWatch::KindColor(D->Kind);
		B->SetVisibility(ESlateVisibility::Visible);
		IBWatchUI::StyleChip(B, bOn, Kind);
		if (L)
		{
			L->SetText(D->ShortName.IsEmpty() ? D->Name : D->ShortName);
			L->SetColorAndOpacity(FSlateColor(bOn ? Kind : (D->Kind == EIBDestinationKind::Locked ? IBWatchUI::Dust() : IBStyle::TextLo())));
		}
	}
	if (SitesRow) { SitesRow->SetVisibility(SiteIds.Num() > 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed); }
}

void UIBWatchScreen::RefreshThumb(const FIBDestination* D, const FIBSector* S)
{
	UTexture2D* Still = nullptr;
	if (D && !D->ReconStill.IsNull()) { Still = D->ReconStill.LoadSynchronous(); }
	if (ThumbImage)
	{
		if (Still)
		{
			ThumbImage->SetBrushFromTexture(Still, false);
			ThumbImage->SetVisibility(ESlateVisibility::HitTestInvisible);
		}
		else
		{
			ThumbImage->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
	if (ThumbFallbackText)
	{
		ThumbFallbackText->SetText(D ? NSLOCTEXT("IBWatch", "StillPending", "RECON STILL  ·  CAPTURE PENDING")
		                             : NSLOCTEXT("IBWatch", "StillNone", "NO RECON IMAGERY  ·  RELAY DARK"));
	}
	const FLinearColor Tag = D ? (D->Kind == EIBDestinationKind::Locked ? IBStyle::TextLo() : IBWatch::KindColor(D->Kind)) : (S ? S->Color : IBStyle::TextLo());
	if (ThumbTag)
	{
		FString TagText;
		if (D)
		{
			const bool bHere = BoardState && D->Id == BoardState->GetCurrentId();
			TagText = bHere ? TEXT("YOU ARE HERE") : IBWatch::KindLabel(D->Kind).ToString();
		}
		else if (S)
		{
			FString Left, Right;
			TagText = S->Status.ToString().Split(TEXT(" · "), &Left, &Right) ? Left : S->Status.ToString();
		}
		ThumbTag->SetText(FText::FromString(TagText));
		ThumbTag->SetColorAndOpacity(FSlateColor(Tag));
	}
	if (ThumbTagFrame) { ThumbTagFrame->SetBrush(IBStyle::RoundedBrush(FLinearColor(0.008f, 0.012f, 0.022f, 0.7f), 2.f, Tag, 1.f)); }
	if (ThumbCaption)
	{
		ThumbCaption->SetText(D ? (BoardState && D->Id == BoardState->GetCurrentId() ? NSLOCTEXT("IBWatch", "CapLive", "LIVE FEED  ·  THE WATCH FLOOR") : NSLOCTEXT("IBWatch", "CapStill", "RECON STILL  ·  DAY 219"))
		                        : NSLOCTEXT("IBWatch", "CapNone", "NO RECON STILL"));
	}
}

void UIBWatchScreen::RefreshNarrator()
{
	if (!NarratorText) { return; }

	const FIBSector* S = CurrentSector();
	const FIBDestination* Sel = IBWatch::Find(SelectedId);
	const bool bHost = IsHost();
	FString Line;
	FLinearColor Colr = IBStyle::Cyan();

	if (S && !S->bLive)
	{
		Line = S->LockReason.ToString();
		Colr = IBStyle::Amber();
	}
	else if (BoardState && BoardState->IsArmed())
	{
		const FIBDestination* Armed = IBWatch::Find(BoardState->GetArmedId());
		Line = FString::Printf(TEXT("DROP AUTHORIZED — %s"), Armed ? *Armed->Name.ToString() : TEXT("—"));
		if (!BoardState->GetProposedByName().IsEmpty() && BoardState->GetProposedByPlayerId() != LocalPlayerId())
		{
			Line += FString::Printf(TEXT("  ·  %s CALLED IT"), *BoardState->GetProposedByName());
		}
		Colr = IBStyle::Amber();
	}
	else if (BoardState && !BoardState->GetProposedId().IsNone())
	{
		const FIBDestination* Prop = IBWatch::Find(BoardState->GetProposedId());
		const bool bMine = BoardState->GetProposedByPlayerId() == LocalPlayerId();
		if (bHost)
		{
			Line = FString::Printf(TEXT("%s PROPOSES %s — CONFIRM?"), *BoardState->GetProposedByName(), Prop ? *Prop->Name.ToString() : TEXT("—"));
		}
		else if (bMine)
		{
			Line = TEXT("PROPOSED — THE HOST HOLDS THE TRIGGER");
		}
		else
		{
			Line = FString::Printf(TEXT("%s PROPOSED %s"), *BoardState->GetProposedByName(), Prop ? *Prop->Name.ToString() : TEXT("—"));
		}
	}
	else if (Sel && BoardState && Sel->Id == BoardState->GetCurrentId())
	{
		Line = TEXT("YOU ARE HERE — PICK A BREACH");
	}
	else if (Sel && !Sel->CanDeploy())
	{
		Line = TEXT("NOT CLEARED FOR DEPLOYMENT — SEALED DISTRICT");
		Colr = IBStyle::Amber();
	}
	else if (IsOffline())
	{
		Line = TEXT("OFF THE NET — DEPLOY TAKES YOU ALONE");
		Colr = IBStyle::Amber();
	}
	else
	{
		Line = bHost ? TEXT("THE SQUAD TRAVELS TOGETHER  ·  DEPLOY DROPS EVERYONE")
		             : TEXT("PROPOSE A BREACH  ·  THE HOST CONFIRMS");
	}

	NarratorText->SetText(FText::FromString(Line));
	NarratorText->SetColorAndOpacity(FSlateColor(Colr));
}

void UIBWatchScreen::RefreshButtons()
{
	const FIBSector* S = CurrentSector();
	const FIBDestination* Sel = IBWatch::Find(SelectedId);
	const bool bHost = IsHost();
	const bool bArmed = BoardState && BoardState->IsArmed();
	const FName Proposed = BoardState ? BoardState->GetProposedId() : NAME_None;
	const FName Here = BoardState ? BoardState->GetCurrentId() : NAME_None;
	const bool bMine = BoardState && BoardState->GetProposedByPlayerId() == LocalPlayerId();
	const bool bLiveSector = S && S->bLive;
	const bool bSelDeployable = bLiveSector && Sel && Sel->CanDeploy() && Sel->Id != Here;

	FText PrimaryText;
	bool bPrimaryEnabled = false;
	IBWatchUI::EPrimary Style = IBWatchUI::EPrimary::Cyan;

	if (!bLiveSector)
	{
		PrimaryText = NSLOCTEXT("IBWatch", "NoDeployment", "NO DEPLOYMENT");
	}
	else if (bArmed)
	{
		PrimaryText = NSLOCTEXT("IBWatch", "Deploying", "DEPLOYING");
	}
	else if (Sel && Sel->Id == Here)
	{
		PrimaryText = NSLOCTEXT("IBWatch", "YouAreHere", "YOU ARE HERE");
	}
	else if (Sel && !Sel->CanDeploy())
	{
		PrimaryText = NSLOCTEXT("IBWatch", "NotCleared", "NOT CLEARED");
	}
	else if (bHost)
	{
		if (!Proposed.IsNone() && Proposed == SelectedId)
		{
			PrimaryText = NSLOCTEXT("IBWatch", "Confirm", "CONFIRM & DEPLOY");
			bPrimaryEnabled = true;
		}
		else if (!Proposed.IsNone())
		{
			PrimaryText = NSLOCTEXT("IBWatch", "DeployInstead", "DEPLOY HERE INSTEAD");
			bPrimaryEnabled = bSelDeployable;
			Style = IBWatchUI::EPrimary::Amber;
		}
		else
		{
			PrimaryText = NSLOCTEXT("IBWatch", "Deploy", "DEPLOY");
			bPrimaryEnabled = bSelDeployable;
		}
	}
	else
	{
		Style = IBWatchUI::EPrimary::Outline;
		if (!Proposed.IsNone() && Proposed == SelectedId)
		{
			PrimaryText = bMine ? NSLOCTEXT("IBWatch", "Proposed", "PROPOSED — WAITING ON HOST") : NSLOCTEXT("IBWatch", "Second", "SECOND THIS");
			bPrimaryEnabled = !bMine; // seconding re-proposes under your name
		}
		else if (!Proposed.IsNone() && bMine)
		{
			PrimaryText = NSLOCTEXT("IBWatch", "ProposeInstead", "PROPOSE THIS INSTEAD");
			bPrimaryEnabled = bSelDeployable;
		}
		else
		{
			PrimaryText = NSLOCTEXT("IBWatch", "Propose", "PROPOSE");
			bPrimaryEnabled = bSelDeployable;
		}
	}
	if (!bPrimaryEnabled) { Style = IBWatchUI::EPrimary::Off; }
	if (PrimaryLabel) { PrimaryLabel->SetText(PrimaryText); }
	if (PrimaryButton)
	{
		PrimaryButton->SetIsEnabled(bPrimaryEnabled);
		IBWatchUI::StylePrimary(PrimaryButton, PrimaryLabel, PrimaryChevron, Style);
	}

	// Secondary: host stands a proposal down; a proposer withdraws. Nothing once the drop is running.
	bool bSecondary = false;
	FText SecondaryText;
	if (!bArmed && bHost && !Proposed.IsNone())
	{
		bSecondary = true;
		SecondaryText = NSLOCTEXT("IBWatch", "StandDown", "STAND DOWN");
	}
	else if (!bArmed && !bHost && bMine)
	{
		bSecondary = true;
		SecondaryText = NSLOCTEXT("IBWatch", "Withdraw", "WITHDRAW");
	}
	if (SecondaryButton) { SecondaryButton->SetVisibility(bSecondary ? ESlateVisibility::Visible : ESlateVisibility::Collapsed); }
	if (SecondaryLabel) { SecondaryLabel->SetText(SecondaryText); }

	if (ViewButton)
	{
		ViewButton->SetVisibility(bLiveSector && !bArmed ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
	if (ViewLabel)
	{
		ViewLabel->SetText(bBoardView ? NSLOCTEXT("IBWatch", "BackToOrbit", "BACK TO ORBIT") : NSLOCTEXT("IBWatch", "ViewMission", "VIEW MISSION  ·  BREACH BOARD"));
	}

	if (LeaveButton && LeaveLabel)
	{
		if (GetMenuSubsystem())
		{
			LeaveLabel->SetText(NSLOCTEXT("IBWatch", "Close", "CLOSE"));
		}
		else
		{
			LeaveLabel->SetText(bHost ? NSLOCTEXT("IBWatch", "LeaveHost", "CLOSE THE WATCH") : NSLOCTEXT("IBWatch", "LeaveClient", "LEAVE THE WATCH"));
		}
	}
}

void UIBWatchScreen::RefreshCallout()
{
	if (!Planet) { return; }
	const FIBSector* S = CurrentSector();
	if (!S) { return; }
	FName CalloutSector = S->Id;
	FText Name = S->Name, Sub = S->Status;
	const FIBDestination* Armed = (BoardState && BoardState->IsArmed()) ? IBWatch::Find(BoardState->GetArmedId()) : nullptr;
	const FIBDestination* D = Armed ? Armed : (S->bLive ? IBWatch::Find(SelectedId) : nullptr);
	if (D)
	{
		if (Armed) { CalloutSector = SectorOf(Armed->Id); }
		Name = D->Name;
		Sub = Armed ? FText::FromString(FString::Printf(TEXT("%s  ·  %s"), *D->Codename.ToString(), *D->ThreatClass.ToString()))
		            : (D->Kind == EIBDestinationKind::Range ? NSLOCTEXT("IBWatch", "RangeSub", "RANGE  ·  LIVE FIRE") : D->ThreatClass);
	}
	Planet->SetSelection(CalloutSector, Name, Sub);
}

// ============================================================================ actions

void UIBWatchScreen::HandlePrimary()
{
	const FIBSector* S = CurrentSector();
	if (!S || !S->bLive) { return; }
	AIBPlayerState* PS = LocalPlayerState();
	if (!PS)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Watch] no IBPlayerState on this controller — cannot act"));
		return;
	}
	if (BoardState && BoardState->IsArmed()) { return; }
	const bool bHost = IsHost();
	const FName Proposed = BoardState ? BoardState->GetProposedId() : NAME_None;
	if (bHost && !Proposed.IsNone() && Proposed == SelectedId)
	{
		PS->WatchConfirm();
	}
	else
	{
		PS->WatchPropose(SelectedId);
	}
}

void UIBWatchScreen::HandleSecondary()
{
	if (AIBPlayerState* PS = LocalPlayerState())
	{
		PS->WatchCancel();
	}
}

void UIBWatchScreen::HandleView()
{
	if (bBoardView) { GoOrbit(); }
	else { GoBoard(); }
}

void UIBWatchScreen::HandleInvite()
{
	if (const ULocalPlayer* LP = GetOwningLocalPlayer())
	{
		if (UIBMenuSubsystem* Menu = LP->GetSubsystem<UIBMenuSubsystem>())
		{
			Menu->ToggleScreen(FName(TEXT("Squad")));
		}
	}
}

void UIBWatchScreen::HandleLeave()
{
	if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
	{
		Menu->CloseMenu();
		return;
	}
	if (UIBSessionSubsystem* Sessions = GetSessions())
	{
		Sessions->IBLeave(); // back to the operative sheet; host leaving ends it for the squad (ADR-002)
	}
}
