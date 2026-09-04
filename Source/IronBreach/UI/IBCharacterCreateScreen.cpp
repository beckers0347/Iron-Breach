#include "UI/IBCharacterCreateScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBSheetDismissProcessor.h"
#include "Player/IBCharacterSubsystem.h"
#include "Player/IBOperativePreviewStage.h"
#include "IronBreach.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/EditableText.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/TextureRenderTarget2D.h"

namespace
{
	constexpr int32 MaxCallsignLen = 16;
	constexpr float CreateColumnWidth = 460.f;
	constexpr float CreatePreviewPixels = 1024.f;

	const EIBOperativeClass AllClasses[] =
	{
		EIBOperativeClass::Breaker,
		EIBOperativeClass::Picket,
		EIBOperativeClass::Bellringer,
		EIBOperativeClass::Corpsman,
	};

	/** Rim color before a trade is chosen: the fireteam ice-blue, dimmed. */
	FLinearColor NeutralAccent() { return FLinearColor(0.45f, 0.55f, 0.70f); }
}

void UIBCharacterCreateScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	SetIsFocusable(true);
	BuildLayout();
}

void UIBCharacterCreateScreen::NativeConstruct()
{
	Super::NativeConstruct();

	TWeakObjectPtr<UIBCharacterCreateScreen> WeakThis(this);
	DismissProcessor = FIBSheetDismissProcessor::Register([WeakThis]()
	{
		UIBCharacterCreateScreen* Self = WeakThis.Get();
		return Self ? Self->HandleDismissKey() : false;
	});

	// InitCreate runs after construction — apply the cancel policy and the stage here.
	if (BackSize)
	{
		BackSize->SetVisibility(bAllowCancel ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
	if (PreviewImage && Stage)
	{
		if (UTextureRenderTarget2D* RT = Stage->GetRenderTarget())
		{
			FSlateBrush Brush = PreviewImage->GetBrush();
			Brush.SetResourceObject(RT);
			Brush.ImageSize = FVector2D(CreatePreviewPixels, CreatePreviewPixels);
			PreviewImage->SetBrush(Brush);
		}
	}
	RefreshPreview();

	// Let the player type a callsign immediately.
	if (Ed_Callsign)
	{
		Ed_Callsign->SetFocus();
	}
}

void UIBCharacterCreateScreen::NativeDestruct()
{
	FIBSheetDismissProcessor::Unregister(DismissProcessor);
	Super::NativeDestruct();
}

bool UIBCharacterCreateScreen::HandleDismissKey()
{
	if (bAllowCancel)
	{
		UE_LOG(LogIronBreach, Log, TEXT("CharacterCreate: dismiss key -> cancel"));
		OnCreateCancelled.Broadcast();
	}
	return true; // with an empty roster Escape does nothing — and nothing else gets it
}

void UIBCharacterCreateScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Keep keyboard focus inside the form (the callsign field counts) so Enter
	// always reaches us — the unkillable-keys rule from the menu screens.
	if (IsVisible() && !HasKeyboardFocus() && !HasFocusedDescendants())
	{
		SetKeyboardFocus();
	}
}

// ---------------------------------------------------------------- layout

void UIBCharacterCreateScreen::BuildLayout()
{
	if (!WidgetTree || Btn_Enlist) { return; }

	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	WidgetTree->RootWidget = Root;

	// Foreground for descendants that inherit it (the callsign field).
	SetForegroundColor(FSlateColor(IBStyle::TextHi()));

	// Opaque stage-black sheet (this sits over the select screen).
	UBorder* Sheet = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Sheet->SetBrush(IBStyle::RoundedBrush(FLinearColor::Black, 0.f));
	if (UOverlaySlot* SheetSlot = Root->AddChildToOverlay(Sheet))
	{
		SheetSlot->SetHorizontalAlignment(HAlign_Fill);
		SheetSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- The body being built: left, full height ----
	PreviewImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
	PreviewImage->SetVisibility(ESlateVisibility::HitTestInvisible);
	{
		FSlateBrush Brush = PreviewImage->GetBrush();
		Brush.DrawAs = ESlateBrushDrawType::Image;
		Brush.ImageSize = FVector2D(CreatePreviewPixels, CreatePreviewPixels);
		Brush.TintColor = FSlateColor(FLinearColor::White);
		PreviewImage->SetBrush(Brush);
	}
	USizeBox* PreviewSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	PreviewSize->SetWidthOverride(CreatePreviewPixels);
	PreviewSize->SetHeightOverride(CreatePreviewPixels);
	PreviewSize->SetContent(PreviewImage);
	UScaleBox* PreviewScale = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());
	PreviewScale->SetStretch(EStretch::ScaleToFit);
	PreviewScale->SetContent(PreviewSize);
	if (UOverlaySlot* PreviewSlot = Root->AddChildToOverlay(PreviewScale))
	{
		PreviewSlot->SetHorizontalAlignment(HAlign_Left);
		PreviewSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// ---- Title, top-left over the stage ----
	UVerticalBox* TitleBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	TitleBox->AddChildToVerticalBox(IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBCharCreate", "Title", "NEW OPERATIVE")));
	UTextBlock* Sub = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBCharCreate", "Sub", "GRAFT PROGRAM INTAKE — THE BREAKWATER TAKES ITS OWN"),
		12, IBStyle::TextLo(), 500);
	if (UVerticalBoxSlot* SubSlot = TitleBox->AddChildToVerticalBox(Sub))
	{
		SubSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	if (UOverlaySlot* TitleSlot = Root->AddChildToOverlay(TitleBox))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetVerticalAlignment(VAlign_Top);
		TitleSlot->SetPadding(FMargin(56.f, 44.f, 0.f, 0.f));
	}

	// ---- Nameplate at the feet: what the record will read ----
	UVerticalBox* Plate = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	PlateName = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBCharCreate", "PlateUnnamed", "UNNAMED OPERATIVE"), 30, IBStyle::TextHi(), 350);
	PlateRole = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBCharCreate", "PlateNoTrade", "NO TRADE ASSIGNED"), 12, IBStyle::TextLo(), 450);
	Plate->AddChildToVerticalBox(PlateName);
	if (UVerticalBoxSlot* RoleSlot = Plate->AddChildToVerticalBox(PlateRole))
	{
		RoleSlot->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f));
	}
	if (UOverlaySlot* PlateSlot = Root->AddChildToOverlay(Plate))
	{
		PlateSlot->SetHorizontalAlignment(HAlign_Left);
		PlateSlot->SetVerticalAlignment(VAlign_Bottom);
		PlateSlot->SetPadding(FMargin(56.f, 0.f, 0.f, 96.f));
	}

	// ---- Right column: the form ----
	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	auto AddGap = [this, Column](float Height)
	{
		USpacer* Gap = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
		Gap->SetSize(FVector2D(1.f, Height));
		Column->AddChildToVerticalBox(Gap);
	};

	// Callsign
	Column->AddChildToVerticalBox(IBStyle::MakeSection(WidgetTree, NSLOCTEXT("IBCharCreate", "SecCallsign", "CALLSIGN")));
	UBorder* CallsignChip = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	CallsignChip->SetBrush(IBStyle::RoundedBrush(IBStyle::Chip(), 6.0f, IBStyle::Line(), 1.0f));
	CallsignChip->SetPadding(FMargin(14.f, 10.f));
	Ed_Callsign = WidgetTree->ConstructWidget<UEditableText>(UEditableText::StaticClass());
	Ed_Callsign->SetHintText(NSLOCTEXT("IBCharCreate", "CallsignHint", "ENTER CALLSIGN"));
	FSlateFontInfo CallsignFont = Ed_Callsign->GetFont();
	CallsignFont.Size = 18;
	CallsignFont.LetterSpacing = 250;
	Ed_Callsign->SetFont(CallsignFont);
	Ed_Callsign->OnTextChanged.AddDynamic(this, &UIBCharacterCreateScreen::HandleCallsignChanged);
	Ed_Callsign->OnTextCommitted.AddDynamic(this, &UIBCharacterCreateScreen::HandleCallsignCommitted);
	CallsignChip->SetContent(Ed_Callsign);
	if (UVerticalBoxSlot* CsSlot = Column->AddChildToVerticalBox(CallsignChip))
	{
		CsSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
		CsSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	AddGap(22.f);

	// Combat trade: 2x2
	Column->AddChildToVerticalBox(IBStyle::MakeSection(WidgetTree, NSLOCTEXT("IBCharCreate", "SecClass", "COMBAT TRADE")));
	UUniformGridPanel* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass());
	Grid->SetSlotPadding(FMargin(5.f));
	ClassButtons.SetNum(UE_ARRAY_COUNT(AllClasses));
	for (int32 i = 0; i < UE_ARRAY_COUNT(AllClasses); ++i)
	{
		const EIBOperativeClass Class = AllClasses[i];
		UButton* Card = BuildClassCard(Class);
		ClassButtons[static_cast<int32>(Class)] = Card;
		if (UUniformGridSlot* CardSlot = Grid->AddChildToUniformGrid(Card, i / 2, i % 2))
		{
			CardSlot->SetHorizontalAlignment(HAlign_Fill);
			CardSlot->SetVerticalAlignment(VAlign_Fill);
		}
	}
	if (UButton* B = ClassButtons[static_cast<int32>(EIBOperativeClass::Breaker)])    { B->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleClassBreaker); }
	if (UButton* B = ClassButtons[static_cast<int32>(EIBOperativeClass::Picket)])     { B->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleClassPicket); }
	if (UButton* B = ClassButtons[static_cast<int32>(EIBOperativeClass::Bellringer)]) { B->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleClassBellringer); }
	if (UVerticalBoxSlot* GridSlot = Column->AddChildToVerticalBox(Grid))
	{
		GridSlot->SetPadding(FMargin(-5.f, 4.f, -5.f, 0.f)); // eat the outer slot padding
		GridSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	AddGap(22.f);

	// Gender
	Column->AddChildToVerticalBox(IBStyle::MakeSection(WidgetTree, NSLOCTEXT("IBCharCreate", "SecGender", "GENDER")));
	UHorizontalBox* GenderRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	auto MakeGenderChip = [this, GenderRow](const FText& Label) -> UButton*
	{
		UButton* Chip = IBStyle::MakeButton(WidgetTree, Label, 15);
		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetHeightOverride(50.f);
		Size->SetContent(Chip);
		if (UHorizontalBoxSlot* ChipSlot = GenderRow->AddChildToHorizontalBox(Size))
		{
			ChipSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
			ChipSlot->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
		}
		return Chip;
	};
	Btn_Male = MakeGenderChip(IBCharacter::GenderName(EIBOperativeGender::Male));
	Btn_Female = MakeGenderChip(IBCharacter::GenderName(EIBOperativeGender::Female));
	Btn_Male->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleGenderMale);
	Btn_Female->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleGenderFemale);
	if (UVerticalBoxSlot* GenderSlot = Column->AddChildToVerticalBox(GenderRow))
	{
		GenderSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
		GenderSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	AddGap(22.f);

	// Status line
	Txt_Status = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBCharCreate", "StatusIdle", "PICK A TRADE AND A GENDER, THEN ENLIST. A BLANK CALLSIGN GETS A SERVICE-ISSUED ONE."),
		12, IBStyle::TextLo(), 300);
	Txt_Status->SetAutoWrapText(true);
	USizeBox* StatusSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	StatusSize->SetMinDesiredHeight(64.f); // three lines: the form doesn't jump when the line wraps
	StatusSize->SetContent(Txt_Status);
	Column->AddChildToVerticalBox(StatusSize);
	AddGap(12.f);

	// Actions
	UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Btn_Enlist = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharCreate", "Enlist", "ENLIST"), 17, /*bAccent=*/true);
	Btn_Enlist->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleEnlist);
	USizeBox* EnlistSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	EnlistSize->SetHeightOverride(54.f);
	EnlistSize->SetContent(Btn_Enlist);
	if (UHorizontalBoxSlot* EnlistSlot = Actions->AddChildToHorizontalBox(EnlistSize))
	{
		EnlistSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		EnlistSlot->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
	}
	Btn_Back = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBCharCreate", "Back", "BACK"), 15);
	Btn_Back->OnClicked.AddDynamic(this, &UIBCharacterCreateScreen::HandleBack);
	BackSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	BackSize->SetWidthOverride(140.f);
	BackSize->SetHeightOverride(54.f);
	BackSize->SetContent(Btn_Back);
	Actions->AddChildToHorizontalBox(BackSize);
	BackSize->SetVisibility(bAllowCancel ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	if (UVerticalBoxSlot* ActionsSlot = Column->AddChildToVerticalBox(Actions))
	{
		ActionsSlot->SetHorizontalAlignment(HAlign_Fill);
	}

	USizeBox* ColumnSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ColumnSize->SetWidthOverride(CreateColumnWidth);
	ColumnSize->SetContent(Column);
	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(ColumnSize))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Right);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
		ColumnSlot->SetPadding(FMargin(0.f, 0.f, 72.f, 0.f));
	}

	RefreshSelectionStyles();
}

UButton* UIBCharacterCreateScreen::BuildClassCard(EIBOperativeClass Class)
{
	const bool bAvailable = IBCharacter::ClassAvailable(Class);
	const FLinearColor Accent = IBCharacter::ClassColor(Class);

	UButton* Card = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	IBStyle::StyleButton(Card, /*bAccent=*/false, 8.0f);
	{
		FButtonStyle Style = Card->GetStyle();
		Style.NormalPadding = FMargin(0.f);
		Style.PressedPadding = FMargin(0.f);
		Card->SetStyle(Style);
	}

	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	UBorder* Bar = IBStyle::MakeAccentBar(WidgetTree, bAvailable ? Accent : IBStyle::Line());
	USizeBox* BarSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	BarSize->SetHeightOverride(3.f);
	BarSize->SetContent(Bar);
	if (UVerticalBoxSlot* BarSlot = Body->AddChildToVerticalBox(BarSize))
	{
		BarSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	}

	Body->AddChildToVerticalBox(IBStyle::MakeText(WidgetTree, IBCharacter::ClassName(Class), 15,
		bAvailable ? IBStyle::TextHi() : IBStyle::TextLo(), 350));

	UTextBlock* Role = IBStyle::MakeText(WidgetTree, IBCharacter::ClassRoleLine(Class), 9,
		bAvailable ? Accent : IBStyle::TextLo(), 200);
	if (UVerticalBoxSlot* RoleSlot = Body->AddChildToVerticalBox(Role))
	{
		RoleSlot->SetPadding(FMargin(0.f, 3.f, 0.f, 6.f));
	}

	UTextBlock* Desc = IBStyle::MakeText(WidgetTree, IBCharacter::ClassDescription(Class), 9, IBStyle::TextLo(), 0);
	Desc->SetAutoWrapText(true);
	if (UVerticalBoxSlot* DescSlot = Body->AddChildToVerticalBox(Desc))
	{
		DescSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	if (!bAvailable)
	{
		UTextBlock* Locked = IBStyle::MakeText(WidgetTree, IBCharacter::ClassLockedLine(Class), 9, IBStyle::Amber(), 400);
		if (UVerticalBoxSlot* LockSlot = Body->AddChildToVerticalBox(Locked))
		{
			LockSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
		}
	}

	UBorder* Pad = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Pad->SetBrush(IBStyle::RoundedBrush(FLinearColor::Transparent, 0.f));
	Pad->SetPadding(FMargin(12.f, 10.f));
	Pad->SetContent(Body);

	USizeBox* CardSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardSize->SetHeightOverride(150.f);
	CardSize->SetContent(Pad);
	Card->AddChild(CardSize);

	Card->SetIsEnabled(bAvailable);
	return Card;
}

void UIBCharacterCreateScreen::RefreshSelectionStyles()
{
	for (int32 i = 0; i < ClassButtons.Num(); ++i)
	{
		UButton* Card = ClassButtons[i];
		if (!Card) { continue; }

		const EIBOperativeClass Class = static_cast<EIBOperativeClass>(i);
		const bool bSelected = bClassChosen && Class == SelectedClass;

		FButtonStyle Style = Card->GetStyle();
		Style.Normal = bSelected
			? IBStyle::RoundedBrush(IBStyle::ChipHot(), 8.0f, IBCharacter::ClassColor(Class), 2.0f)
			: IBStyle::RoundedBrush(IBStyle::Chip(), 8.0f, IBStyle::Line(), 1.0f);
		Card->SetStyle(Style);
	}

	auto StyleGender = [this](UButton* Chip, EIBOperativeGender Gender)
	{
		if (!Chip) { return; }
		const bool bSelected = bGenderChosen && Gender == SelectedGender;
		FButtonStyle Style = Chip->GetStyle();
		Style.Normal = bSelected
			? IBStyle::RoundedBrush(IBStyle::ChipHot(), 6.0f, IBStyle::Amber(), 2.0f)
			: IBStyle::RoundedBrush(IBStyle::Chip(), 6.0f, IBStyle::Line(), 1.0f);
		Chip->SetStyle(Style);
	};
	StyleGender(Btn_Male, EIBOperativeGender::Male);
	StyleGender(Btn_Female, EIBOperativeGender::Female);
}

void UIBCharacterCreateScreen::RefreshPreview()
{
	// The body on the stage tracks the form: gender picks the mannequin, the
	// trade lights the rim. Before any pick, a neutral Manny stands in.
	if (Stage)
	{
		Stage->ShowOperative(bGenderChosen ? SelectedGender : EIBOperativeGender::Male,
			bClassChosen ? IBCharacter::ClassColor(SelectedClass) : NeutralAccent());
	}

	if (PlateName)
	{
		const FString Typed = Ed_Callsign ? UIBCharacterSubsystem::SanitizeCallsign(Ed_Callsign->GetText().ToString()) : FString();
		PlateName->SetText(Typed.IsEmpty()
			? NSLOCTEXT("IBCharCreate", "PlateUnnamed", "UNNAMED OPERATIVE")
			: FText::FromString(Typed));
	}
	if (PlateRole)
	{
		if (bClassChosen)
		{
			PlateRole->SetText(FText::Format(NSLOCTEXT("IBCharCreate", "PlateRole", "{0}  —  {1}"),
				IBCharacter::ClassName(SelectedClass), IBCharacter::ClassRoleLine(SelectedClass)));
			PlateRole->SetColorAndOpacity(FSlateColor(IBCharacter::ClassColor(SelectedClass)));
		}
		else
		{
			PlateRole->SetText(NSLOCTEXT("IBCharCreate", "PlateNoTrade", "NO TRADE ASSIGNED"));
			PlateRole->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
		}
	}
}

// ---------------------------------------------------------------- input

void UIBCharacterCreateScreen::PickClass(EIBOperativeClass Class)
{
	bClassChosen = true;
	SelectedClass = Class;
	RefreshSelectionStyles();
	RefreshPreview();
	SetStatus(IBCharacter::ClassDescription(Class), /*bError=*/false);
}

void UIBCharacterCreateScreen::PickGender(EIBOperativeGender Gender)
{
	bGenderChosen = true;
	SelectedGender = Gender;
	RefreshSelectionStyles();
	RefreshPreview();
}

void UIBCharacterCreateScreen::HandleClassBreaker()    { PickClass(EIBOperativeClass::Breaker); }
void UIBCharacterCreateScreen::HandleClassPicket()     { PickClass(EIBOperativeClass::Picket); }
void UIBCharacterCreateScreen::HandleClassBellringer() { PickClass(EIBOperativeClass::Bellringer); }
void UIBCharacterCreateScreen::HandleGenderMale()      { PickGender(EIBOperativeGender::Male); }
void UIBCharacterCreateScreen::HandleGenderFemale()    { PickGender(EIBOperativeGender::Female); }

void UIBCharacterCreateScreen::HandleCallsignChanged(const FText& Text)
{
	// Hard cap the length live; full sanitize happens at enlist.
	const FString Raw = Text.ToString();
	if (Raw.Len() > MaxCallsignLen && Ed_Callsign)
	{
		Ed_Callsign->SetText(FText::FromString(Raw.Left(MaxCallsignLen)));
	}
	RefreshPreview(); // the nameplate reads what the record will say
}

void UIBCharacterCreateScreen::HandleCallsignCommitted(const FText& Text, ETextCommit::Type CommitMethod)
{
	if (CommitMethod == ETextCommit::OnEnter)
	{
		HandleEnlist();
	}
}

void UIBCharacterCreateScreen::HandleEnlist()
{
	if (!bClassChosen)
	{
		SetStatus(NSLOCTEXT("IBCharCreate", "ErrNoClass", "CHOOSE A COMBAT TRADE"), true);
		return;
	}
	if (!bGenderChosen)
	{
		SetStatus(NSLOCTEXT("IBCharCreate", "ErrNoGender", "CHOOSE A GENDER"), true);
		return;
	}

	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters)
	{
		SetStatus(NSLOCTEXT("IBCharCreate", "ErrNoSubsystem", "ROSTER SERVICE UNAVAILABLE"), true);
		return;
	}

	const FString Callsign = Ed_Callsign ? Ed_Callsign->GetText().ToString() : FString();

	FIBCharacterRecord Created;
	FText Error;
	if (!Characters->CreateCharacter(Callsign, SelectedClass, SelectedGender, Created, Error))
	{
		SetStatus(Error, true);
		return;
	}

	OnOperativeCreated.Broadcast(Created);
}

void UIBCharacterCreateScreen::HandleBack()
{
	if (bAllowCancel)
	{
		OnCreateCancelled.Broadcast();
	}
}

FReply UIBCharacterCreateScreen::NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if ((InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right) && bAllowCancel)
	{
		OnCreateCancelled.Broadcast();
		return FReply::Handled();
	}
	return Super::NativeOnPreviewKeyDown(InGeometry, InKeyEvent);
}

FReply UIBCharacterCreateScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if ((InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right) && bAllowCancel)
	{
		OnCreateCancelled.Broadcast();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UIBCharacterCreateScreen::SetStatus(const FText& Message, bool bError)
{
	if (Txt_Status)
	{
		Txt_Status->SetText(Message);
		Txt_Status->SetColorAndOpacity(FSlateColor(bError ? IBStyle::Danger() : IBStyle::TextLo()));
	}
	UE_LOG(LogIronBreach, Log, TEXT("CharacterCreate: %s"), *Message.ToString());
}

UIBCharacterSubsystem* UIBCharacterCreateScreen::GetCharacters() const
{
	UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBCharacterSubsystem>() : nullptr;
}
