#include "UI/IBCharacterSelectScreen.h"
#include "UI/IBCharacterCreateScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBSheetDismissProcessor.h"
#include "Player/IBCharacterSubsystem.h"
#include "Player/IBOperativePreviewStage.h"
#include "IronBreach.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Framework/Application/SlateApplication.h"

namespace
{
	constexpr float ColumnWidth = 460.f;
	constexpr float CardHeight = 112.f;
	constexpr float PreviewPixels = 1024.f; // native render-target size; ScaleBox fits it to the screen height

	FText LastDeployedText(const FDateTime& Utc)
	{
		if (Utc.GetTicks() == 0)
		{
			return NSLOCTEXT("IBCharSelect", "NeverDeployed", "NEVER DEPLOYED");
		}
		const int32 Days = (FDateTime::UtcNow() - Utc).GetDays();
		if (Days <= 0) { return NSLOCTEXT("IBCharSelect", "DeployedToday", "LAST DEPLOYED — TODAY"); }
		if (Days == 1) { return NSLOCTEXT("IBCharSelect", "DeployedYesterday", "LAST DEPLOYED — YESTERDAY"); }
		return FText::FromString(FString::Printf(TEXT("LAST DEPLOYED — %d DAYS AGO"), Days));
	}

	void StyleCard(UButton* Card, bool bSelected, const FLinearColor& Accent)
	{
		if (!Card) { return; }
		FButtonStyle Style = Card->GetStyle();
		Style.Normal = bSelected
			? IBStyle::RoundedBrush(IBStyle::ChipHot(), 8.f, IBStyle::Amber(), 2.f)
			: IBStyle::RoundedBrush(IBStyle::Panel(), 8.f, IBStyle::Line(), 1.f);
		Style.Hovered = IBStyle::RoundedBrush(IBStyle::ChipHot(), 8.f, bSelected ? IBStyle::Amber() : Accent, 1.5f);
		Style.Pressed = IBStyle::RoundedBrush(IBStyle::Ink(), 8.f, IBStyle::Amber(), 1.5f);
		Style.NormalPadding = FMargin(0.f);
		Style.PressedPadding = FMargin(0.f);
		Card->SetStyle(Style);
	}
}

// ---------------------------------------------------------------- lifecycle

void UIBCharacterSelectScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	SetIsFocusable(true);
	BuildLayout();

	if (UIBCharacterSubsystem* Characters = GetCharacters())
	{
		Characters->OnRosterChanged.AddDynamic(this, &UIBCharacterSelectScreen::HandleRosterChanged);
	}
}

void UIBCharacterSelectScreen::NativeConstruct()
{
	Super::NativeConstruct();

	// Dismiss key ahead of focus routing — whatever holds focus, Escape reaches us.
	TWeakObjectPtr<UIBCharacterSelectScreen> WeakThis(this);
	DismissProcessor = FIBSheetDismissProcessor::Register([WeakThis]()
	{
		UIBCharacterSelectScreen* Self = WeakThis.Get();
		return Self ? Self->HandleDismissKey() : false;
	});

	// InitSelect runs after construction: BACK only exists for a switch, not the gate.
	if (Btn_Back)
	{
		Btn_Back->SetVisibility(bDismissible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}

	EnsureStage();
	RefreshCards();

	// First contact with an empty roster: straight into the intake form.
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (Characters && Characters->GetRoster().Num() == 0)
	{
		OpenCreate();
	}
	else
	{
		SetKeyboardFocus();
	}
}

void UIBCharacterSelectScreen::NativeDestruct()
{
	FIBSheetDismissProcessor::Unregister(DismissProcessor);

	if (UIBCharacterSubsystem* Characters = GetCharacters())
	{
		Characters->OnRosterChanged.RemoveDynamic(this, &UIBCharacterSelectScreen::HandleRosterChanged);
	}

	if (Stage)
	{
		Stage->Destroy();
		Stage = nullptr;
	}

	Super::NativeDestruct();
}

void UIBCharacterSelectScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// The unkillable-keys rule (see IBMenuScreen): reassert focus while we're
	// the top sheet; the intake form owns it when open.
	if (!CreateScreen && IsVisible() && !HasKeyboardFocus() && !HasFocusedDescendants())
	{
		SetKeyboardFocus();

		if (!bLoggedFocusSteal && FSlateApplication::IsInitialized())
		{
			bLoggedFocusSteal = true;
			TSharedPtr<SWidget> Focused = FSlateApplication::Get().GetUserFocusedWidget(0);
			UE_LOG(LogIronBreach, Log, TEXT("CharacterSelect: reclaimed keyboard focus (was on %s)"),
				Focused.IsValid() ? *Focused->GetTypeAsString() : TEXT("nothing"));
		}
	}
}

// ---------------------------------------------------------------- layout

void UIBCharacterSelectScreen::BuildLayout()
{
	if (!WidgetTree || RootOverlay) { return; }

	RootOverlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	WidgetTree->RootWidget = RootOverlay;

	// Opaque stage-black sheet: the title art stays behind the door. Black (not
	// Ink) so the preview capture's empty background is seamless with the sheet.
	UBorder* Sheet = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Sheet->SetBrush(IBStyle::RoundedBrush(FLinearColor::Black, 0.f));
	if (UOverlaySlot* SheetSlot = RootOverlay->AddChildToOverlay(Sheet))
	{
		SheetSlot->SetHorizontalAlignment(HAlign_Fill);
		SheetSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- The body: render target, left, full height, square ----
	PreviewImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
	PreviewImage->SetVisibility(ESlateVisibility::HitTestInvisible);
	{
		FSlateBrush Brush = PreviewImage->GetBrush();
		Brush.DrawAs = ESlateBrushDrawType::Image;
		Brush.ImageSize = FVector2D(PreviewPixels, PreviewPixels);
		Brush.TintColor = FSlateColor(FLinearColor::White);
		PreviewImage->SetBrush(Brush);
	}
	USizeBox* PreviewSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	PreviewSize->SetWidthOverride(PreviewPixels);
	PreviewSize->SetHeightOverride(PreviewPixels);
	PreviewSize->SetContent(PreviewImage);
	UScaleBox* PreviewScale = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());
	PreviewScale->SetStretch(EStretch::ScaleToFit);
	PreviewScale->SetContent(PreviewSize);
	if (UOverlaySlot* PreviewSlot = RootOverlay->AddChildToOverlay(PreviewScale))
	{
		PreviewSlot->SetHorizontalAlignment(HAlign_Left);
		PreviewSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- Title, top-left over the stage ----
	UVerticalBox* TitleBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	TitleBox->AddChildToVerticalBox(IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBCharSelect", "Title", "SELECT OPERATIVE")));
	UTextBlock* Sub = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBCharSelect", "Sub", "BREAKWATER SERVICE RECORD — THREE BILLETS TO A HOUSEHOLD"),
		12, IBStyle::TextLo(), 500);
	if (UVerticalBoxSlot* SubSlot = TitleBox->AddChildToVerticalBox(Sub))
	{
		SubSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	if (UOverlaySlot* TitleSlot = RootOverlay->AddChildToOverlay(TitleBox))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetVerticalAlignment(VAlign_Top);
		TitleSlot->SetPadding(FMargin(56.f, 44.f, 0.f, 0.f));
	}

	// ---- Nameplate, bottom-left at the operative's feet ----
	Nameplate = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	NameplateName = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 30, IBStyle::TextHi(), 350);
	NameplateRole = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 12, IBStyle::Amber(), 450);
	NameplateMeta = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 250);
	Nameplate->AddChildToVerticalBox(NameplateName);
	if (UVerticalBoxSlot* RoleSlot = Nameplate->AddChildToVerticalBox(NameplateRole))
	{
		RoleSlot->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f));
	}
	if (UVerticalBoxSlot* MetaSlot = Nameplate->AddChildToVerticalBox(NameplateMeta))
	{
		MetaSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	if (UOverlaySlot* PlateSlot = RootOverlay->AddChildToOverlay(Nameplate))
	{
		PlateSlot->SetHorizontalAlignment(HAlign_Left);
		PlateSlot->SetVerticalAlignment(VAlign_Bottom);
		PlateSlot->SetPadding(FMargin(56.f, 0.f, 0.f, 96.f));
	}

	// ---- Right column: billets + actions ----
	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	Column->AddChildToVerticalBox(IBStyle::MakeSection(WidgetTree, NSLOCTEXT("IBCharSelect", "SecRoster", "OPERATIVES ON FILE")));

	CardsColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	if (UVerticalBoxSlot* CardsSlot = Column->AddChildToVerticalBox(CardsColumn))
	{
		CardsSlot->SetPadding(FMargin(0.f, 10.f, 0.f, 0.f));
	}

	ActionPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Btn_Deploy = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharSelect", "Deploy", "DEPLOY"), 17, /*bAccent=*/true);
	Btn_Deploy->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleDeploy);
	USizeBox* DeploySize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	DeploySize->SetHeightOverride(54.f);
	DeploySize->SetContent(Btn_Deploy);
	if (UVerticalBoxSlot* DeploySlot = ActionPanel->AddChildToVerticalBox(DeploySize))
	{
		DeploySlot->SetPadding(FMargin(0.f, 18.f, 0.f, 8.f));
		DeploySlot->SetHorizontalAlignment(HAlign_Fill);
	}

	UTextBlock* DecomText = nullptr;
	Btn_Decom = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharSelect", "Decom", "DECOMMISSION"), 11, false, &DecomText);
	DecomLabel = DecomText;
	if (DecomLabel) { DecomLabel->SetColorAndOpacity(FSlateColor(IBStyle::TextLo())); }
	Btn_Decom->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleDecommission);
	USizeBox* DecomSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	DecomSize->SetHeightOverride(34.f);
	DecomSize->SetContent(Btn_Decom);
	if (UVerticalBoxSlot* DecomSlot = ActionPanel->AddChildToVerticalBox(DecomSize))
	{
		DecomSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	Column->AddChildToVerticalBox(ActionPanel);

	Txt_Status = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 12, IBStyle::TextLo(), 300);
	Txt_Status->SetAutoWrapText(true);
	USizeBox* StatusSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	StatusSize->SetMinDesiredHeight(48.f); // two lines: the column doesn't jump when the line wraps
	StatusSize->SetContent(Txt_Status);
	if (UVerticalBoxSlot* StatusSlot = Column->AddChildToVerticalBox(StatusSize))
	{
		StatusSlot->SetPadding(FMargin(0.f, 16.f, 0.f, 0.f));
	}

	USizeBox* ColumnSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ColumnSize->SetWidthOverride(ColumnWidth);
	ColumnSize->SetContent(Column);
	if (UOverlaySlot* ColumnSlot = RootOverlay->AddChildToOverlay(ColumnSize))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Right);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
		ColumnSlot->SetPadding(FMargin(0.f, 0.f, 72.f, 0.f));
	}

	// ---- Corners: BACK (switch only), QUIT TO DESKTOP ----
	Btn_Back = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharSelect", "Back", "BACK"), 13);
	Btn_Back->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleBack);
	Btn_Back->SetVisibility(ESlateVisibility::Collapsed);
	if (UOverlaySlot* BackSlot = RootOverlay->AddChildToOverlay(Btn_Back))
	{
		BackSlot->SetHorizontalAlignment(HAlign_Left);
		BackSlot->SetVerticalAlignment(VAlign_Bottom);
		BackSlot->SetPadding(FMargin(56.f, 0.f, 0.f, 28.f));
	}

	UButton* Btn_Quit = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharSelect", "Quit", "QUIT TO DESKTOP"), 13);
	Btn_Quit->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleQuit);
	if (UOverlaySlot* QuitSlot = RootOverlay->AddChildToOverlay(Btn_Quit))
	{
		QuitSlot->SetHorizontalAlignment(HAlign_Right);
		QuitSlot->SetVerticalAlignment(VAlign_Bottom);
		QuitSlot->SetPadding(FMargin(0.f, 0.f, 72.f, 28.f));
	}
}

void UIBCharacterSelectScreen::EnsureStage()
{
	if (Stage) { return; }

	Stage = AIBOperativePreviewStage::Spawn(GetWorld());
	if (!Stage)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("CharacterSelect: preview stage failed to spawn"));
		return;
	}

	if (PreviewImage)
	{
		if (UTextureRenderTarget2D* RT = Stage->GetRenderTarget())
		{
			FSlateBrush Brush = PreviewImage->GetBrush();
			Brush.SetResourceObject(RT);
			Brush.ImageSize = FVector2D(PreviewPixels, PreviewPixels);
			PreviewImage->SetBrush(Brush);
		}
	}
}

// ---------------------------------------------------------------- roster

void UIBCharacterSelectScreen::RefreshCards()
{
	if (!CardsColumn) { return; }

	CardsColumn->ClearChildren();
	CardButtons.Reset();
	PendingDeleteId.Invalidate();
	if (DecomLabel)
	{
		DecomLabel->SetText(NSLOCTEXT("IBCharSelect", "Decom", "DECOMMISSION"));
		DecomLabel->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	}
	if (Btn_Decom)
	{
		IBStyle::StyleButton(Btn_Decom);
	}

	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters) { return; }

	const TArray<FIBCharacterRecord>& Roster = Characters->GetRoster();
	const FGuid LastActive = Characters->GetLastActiveId();

	for (int32 i = 0; i < Roster.Num(); ++i)
	{
		CardButtons.Add(BuildRosterCard(i, Roster[i], Roster[i].CharacterId == LastActive));
	}
	for (int32 i = Roster.Num(); i < Characters->GetMaxCharacters(); ++i)
	{
		BuildEmptyCard();
	}

	// Keep the selection if it survived; else the last operative on station; else the first.
	bool bSelectedValid = false;
	for (const FIBCharacterRecord& R : Roster)
	{
		if (R.CharacterId == SelectedId) { bSelectedValid = true; break; }
	}
	if (!bSelectedValid)
	{
		SelectedId.Invalidate();
		for (const FIBCharacterRecord& R : Roster)
		{
			if (R.CharacterId == LastActive) { SelectedId = R.CharacterId; break; }
		}
		if (!SelectedId.IsValid() && Roster.Num() > 0)
		{
			SelectedId = Roster[0].CharacterId;
		}
	}

	RefreshSelection();
}

UButton* UIBCharacterSelectScreen::BuildRosterCard(int32 Index, const FIBCharacterRecord& Record, bool bLastOnStation)
{
	const FLinearColor Accent = IBCharacter::ClassColor(Record.Class);

	UButton* Card = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	StyleCard(Card, false, Accent);

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	// Trade color bar down the left edge.
	UBorder* Bar = IBStyle::MakeAccentBar(WidgetTree, Accent);
	USizeBox* BarSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	BarSize->SetWidthOverride(4.f);
	BarSize->SetContent(Bar);
	if (UHorizontalBoxSlot* BarSlot = Row->AddChildToHorizontalBox(BarSize))
	{
		BarSlot->SetPadding(FMargin(12.f, 14.f, 14.f, 14.f));
		BarSlot->SetVerticalAlignment(VAlign_Fill);
	}

	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	if (bLastOnStation)
	{
		UTextBlock* Tag = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBCharSelect", "LastTag", "LAST ON STATION"), 9, IBStyle::Amber(), 500);
		if (UVerticalBoxSlot* TagSlot = Body->AddChildToVerticalBox(Tag))
		{
			TagSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 3.f));
		}
	}
	Body->AddChildToVerticalBox(IBStyle::MakeText(WidgetTree, FText::FromString(Record.Callsign), 18, IBStyle::TextHi(), 300));
	UTextBlock* ClassLine = IBStyle::MakeText(WidgetTree, IBCharacter::ClassName(Record.Class), 11, Accent, 450);
	if (UVerticalBoxSlot* ClassSlot = Body->AddChildToVerticalBox(ClassLine))
	{
		ClassSlot->SetPadding(FMargin(0.f, 3.f, 0.f, 0.f));
	}
	const FString Meta = FString::Printf(TEXT("LV %d  ·  %s  ·  %s"), Record.Level,
		*IBCharacter::GenderName(Record.Gender).ToString(), *LastDeployedText(Record.LastPlayedUtc).ToString());
	UTextBlock* MetaLine = IBStyle::MakeText(WidgetTree, FText::FromString(Meta), 10, IBStyle::TextLo(), 200);
	if (UVerticalBoxSlot* MetaSlot = Body->AddChildToVerticalBox(MetaLine))
	{
		MetaSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	if (UHorizontalBoxSlot* BodySlot = Row->AddChildToHorizontalBox(Body))
	{
		BodySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		BodySlot->SetVerticalAlignment(VAlign_Center);
		BodySlot->SetPadding(FMargin(0.f, 12.f, 12.f, 12.f));
	}

	Card->AddChild(Row);

	switch (Index)
	{
	case 0:  Card->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleSelect0); break;
	case 1:  Card->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleSelect1); break;
	default: Card->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleSelect2); break;
	}

	USizeBox* CardSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardSize->SetHeightOverride(CardHeight);
	CardSize->SetContent(Card);
	if (UVerticalBoxSlot* CardSlot = CardsColumn->AddChildToVerticalBox(CardSize))
	{
		CardSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
		CardSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	return Card;
}

void UIBCharacterSelectScreen::BuildEmptyCard()
{
	UButton* Card = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	FButtonStyle Style = Card->GetStyle();
	FLinearColor EmptyFill = IBStyle::Panel();
	EmptyFill.A = 0.5f;
	Style.Normal  = IBStyle::RoundedBrush(EmptyFill, 8.f, IBStyle::Line(), 1.f);
	Style.Hovered = IBStyle::RoundedBrush(IBStyle::Panel(), 8.f, IBStyle::Amber(), 1.5f);
	Style.Pressed = IBStyle::RoundedBrush(IBStyle::Ink(), 8.f, IBStyle::Amber(), 1.5f);
	Style.NormalPadding = FMargin(0.f);
	Style.PressedPadding = FMargin(0.f);
	Card->SetStyle(Style);
	Card->OnClicked.AddDynamic(this, &UIBCharacterSelectScreen::HandleNewOperative);

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UTextBlock* Plus = IBStyle::MakeText(WidgetTree, FText::FromString(TEXT("+")), 28, IBStyle::TextLo(), 0);
	if (UHorizontalBoxSlot* PlusSlot = Row->AddChildToHorizontalBox(Plus))
	{
		PlusSlot->SetVerticalAlignment(VAlign_Center);
		PlusSlot->SetPadding(FMargin(0.f, 0.f, 16.f, 0.f));
	}
	UTextBlock* Label = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBCharSelect", "NewOp", "NEW OPERATIVE"), 13, IBStyle::TextLo(), 500);
	if (UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(Label))
	{
		LabelSlot->SetVerticalAlignment(VAlign_Center);
	}

	UOverlay* Center = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	if (UOverlaySlot* RowSlot = Center->AddChildToOverlay(Row))
	{
		RowSlot->SetHorizontalAlignment(HAlign_Center);
		RowSlot->SetVerticalAlignment(VAlign_Center);
	}
	Card->AddChild(Center);

	USizeBox* CardSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardSize->SetHeightOverride(CardHeight);
	CardSize->SetContent(Card);
	if (UVerticalBoxSlot* CardSlot = CardsColumn->AddChildToVerticalBox(CardSize))
	{
		CardSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
		CardSlot->SetHorizontalAlignment(HAlign_Fill);
	}
}

const FIBCharacterRecord* UIBCharacterSelectScreen::FindSelected() const
{
	const UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters || !SelectedId.IsValid()) { return nullptr; }
	for (const FIBCharacterRecord& R : Characters->GetRoster())
	{
		if (R.CharacterId == SelectedId) { return &R; }
	}
	return nullptr;
}

void UIBCharacterSelectScreen::SetDeploying(const FText& Status)
{
	bDeploying = true;
	if (CardsColumn) { CardsColumn->SetIsEnabled(false); }
	if (ActionPanel) { ActionPanel->SetIsEnabled(false); }
	if (Btn_Back) { Btn_Back->SetVisibility(ESlateVisibility::Collapsed); }
	CloseCreate();
	RefreshSelection(); // the operative who's deploying stands on the stage
	if (Txt_Status)
	{
		Txt_Status->SetText(Status);
		Txt_Status->SetColorAndOpacity(FSlateColor(IBStyle::Amber()));
	}
}

void UIBCharacterSelectScreen::SelectByIndex(int32 Index)
{
	if (bDeploying) { return; }
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters || !Characters->GetRoster().IsValidIndex(Index)) { return; }

	const FIBCharacterRecord& Record = Characters->GetRoster()[Index];
	if (PendingDeleteId.IsValid() && PendingDeleteId != Record.CharacterId)
	{
		RefreshCards(); // picking someone else disarms a pending decommission
	}
	SelectedId = Record.CharacterId;
	RefreshSelection();
}

void UIBCharacterSelectScreen::RefreshSelection()
{
	UIBCharacterSubsystem* Characters = GetCharacters();
	const FIBCharacterRecord* Selected = FindSelected();

	// Card styling.
	if (Characters)
	{
		const TArray<FIBCharacterRecord>& Roster = Characters->GetRoster();
		for (int32 i = 0; i < CardButtons.Num() && i < Roster.Num(); ++i)
		{
			StyleCard(CardButtons[i], Roster[i].CharacterId == SelectedId, IBCharacter::ClassColor(Roster[i].Class));
		}
	}

	if (Selected)
	{
		const FLinearColor Accent = IBCharacter::ClassColor(Selected->Class);
		if (Stage) { Stage->ShowOperative(Selected->Gender, Accent); }

		if (Nameplate) { Nameplate->SetVisibility(ESlateVisibility::HitTestInvisible); }
		if (NameplateName) { NameplateName->SetText(FText::FromString(Selected->Callsign)); }
		if (NameplateRole)
		{
			NameplateRole->SetText(FText::Format(NSLOCTEXT("IBCharSelect", "PlateRole", "{0}  —  {1}"),
				IBCharacter::ClassName(Selected->Class), IBCharacter::ClassRoleLine(Selected->Class)));
			NameplateRole->SetColorAndOpacity(FSlateColor(Accent));
		}
		if (NameplateMeta)
		{
			NameplateMeta->SetText(FText::FromString(FString::Printf(TEXT("LV %d  ·  %s  ·  %s"), Selected->Level,
				*IBCharacter::GenderName(Selected->Gender).ToString(), *LastDeployedText(Selected->LastPlayedUtc).ToString())));
		}
		if (ActionPanel) { ActionPanel->SetVisibility(ESlateVisibility::Visible); }
		if (!bDeploying)
		{
			SetStatus(NSLOCTEXT("IBCharSelect", "StatusPick", "CHOOSE WHO ANSWERS THE NINE"), false);
		}
	}
	else
	{
		if (Stage) { Stage->ShowNothing(); }
		if (Nameplate) { Nameplate->SetVisibility(ESlateVisibility::Collapsed); }
		if (ActionPanel) { ActionPanel->SetVisibility(ESlateVisibility::Collapsed); }
		SetStatus(NSLOCTEXT("IBCharSelect", "StatusEmpty", "NO OPERATIVES ON FILE — THE GRAFT PROGRAM IS WAITING"), false);
	}
}

// ---------------------------------------------------------------- actions

void UIBCharacterSelectScreen::HandleSelect0() { SelectByIndex(0); }
void UIBCharacterSelectScreen::HandleSelect1() { SelectByIndex(1); }
void UIBCharacterSelectScreen::HandleSelect2() { SelectByIndex(2); }

void UIBCharacterSelectScreen::HandleDeploy()
{
	if (bDeploying) { return; }
	UIBCharacterSubsystem* Characters = GetCharacters();
	const FIBCharacterRecord* Selected = FindSelected();
	if (Characters && Selected && Characters->SelectCharacter(Selected->CharacterId))
	{
		OnFlowFinished.Broadcast();
	}
}

void UIBCharacterSelectScreen::HandleDecommission()
{
	if (bDeploying) { return; }
	UIBCharacterSubsystem* Characters = GetCharacters();
	const FIBCharacterRecord* Selected = FindSelected();
	if (!Characters || !Selected) { return; }

	const FIBCharacterRecord Record = *Selected;

	if (PendingDeleteId != Record.CharacterId)
	{
		// Arm. Second press makes it real.
		PendingDeleteId = Record.CharacterId;
		if (DecomLabel)
		{
			DecomLabel->SetText(NSLOCTEXT("IBCharSelect", "DecomConfirm", "CONFIRM — FOR GOOD?"));
			DecomLabel->SetColorAndOpacity(FSlateColor(IBStyle::Danger()));
		}
		if (Btn_Decom)
		{
			FButtonStyle Style = Btn_Decom->GetStyle();
			Style.Normal = IBStyle::RoundedBrush(FLinearColor(0.25f, 0.06f, 0.05f), 6.f, IBStyle::Danger(), 1.5f);
			Btn_Decom->SetStyle(Style);
		}
		SetStatus(FText::FromString(FString::Printf(TEXT("DECOMMISSION %s? THE RECORD DOES NOT COME BACK"), *Record.Callsign)), true);
		return;
	}

	Characters->DeleteCharacter(Record.CharacterId); // RosterChanged rebuilds the cards
}

void UIBCharacterSelectScreen::HandleRosterChanged()
{
	RefreshCards();

	// The last operative was just decommissioned: back to intake, no exit.
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (Characters && Characters->GetRoster().Num() == 0 && !CreateScreen)
	{
		OpenCreate();
	}
}

void UIBCharacterSelectScreen::HandleNewOperative()
{
	if (bDeploying) { return; }
	OpenCreate();
}

void UIBCharacterSelectScreen::OpenCreate()
{
	if (CreateScreen || !RootOverlay) { return; }

	UIBCharacterSubsystem* Characters = GetCharacters();
	const bool bCanCancel = Characters && Characters->GetRoster().Num() > 0;

	CreateScreen = CreateWidget<UIBCharacterCreateScreen>(GetOwningPlayer(), UIBCharacterCreateScreen::StaticClass());
	if (!CreateScreen) { return; }

	CreateScreen->InitCreate(bCanCancel, Stage);
	CreateScreen->OnOperativeCreated.AddDynamic(this, &UIBCharacterSelectScreen::HandleOperativeCreated);
	CreateScreen->OnCreateCancelled.AddDynamic(this, &UIBCharacterSelectScreen::HandleCreateCancelled);

	if (UOverlaySlot* CreateSlot = RootOverlay->AddChildToOverlay(CreateScreen))
	{
		CreateSlot->SetHorizontalAlignment(HAlign_Fill);
		CreateSlot->SetVerticalAlignment(VAlign_Fill);
	}
}

void UIBCharacterSelectScreen::CloseCreate()
{
	if (CreateScreen)
	{
		CreateScreen->RemoveFromParent();
		CreateScreen = nullptr;
	}
}

void UIBCharacterSelectScreen::HandleOperativeCreated(const FIBCharacterRecord& Character)
{
	// Creation already put them on station — the flow is done.
	CloseCreate();
	OnFlowFinished.Broadcast();
}

void UIBCharacterSelectScreen::HandleCreateCancelled()
{
	CloseCreate();
	RefreshCards(); // also puts the selected operative back on the stage
	SetKeyboardFocus();
}

void UIBCharacterSelectScreen::HandleBack()
{
	if (bDismissible)
	{
		OnFlowFinished.Broadcast();
	}
}

void UIBCharacterSelectScreen::HandleQuit()
{
	UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
}

bool UIBCharacterSelectScreen::HandleDismissKey()
{
	if (CreateScreen)
	{
		return false; // the intake form's own processor owns Escape while it's up
	}
	if (bDismissible && !bDeploying)
	{
		UE_LOG(LogIronBreach, Log, TEXT("CharacterSelect: dismiss key -> back to menu"));
		OnFlowFinished.Broadcast();
	}
	return true; // the gate swallows Escape: no operative, no menu
}

FReply UIBCharacterSelectScreen::NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if ((InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right) && bDismissible && !CreateScreen)
	{
		OnFlowFinished.Broadcast();
		return FReply::Handled();
	}
	return Super::NativeOnPreviewKeyDown(InGeometry, InKeyEvent);
}

FReply UIBCharacterSelectScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if ((InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right) && bDismissible && !CreateScreen)
	{
		OnFlowFinished.Broadcast();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UIBCharacterSelectScreen::SetStatus(const FText& Message, bool bError)
{
	if (Txt_Status)
	{
		Txt_Status->SetText(Message);
		Txt_Status->SetColorAndOpacity(FSlateColor(bError ? IBStyle::Danger() : IBStyle::TextLo()));
	}
}

UIBCharacterSubsystem* UIBCharacterSelectScreen::GetCharacters() const
{
	UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBCharacterSubsystem>() : nullptr;
}
