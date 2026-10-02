#include "UI/IBSettingsScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBHangarStyle.h"
#include "Components/ScrollBox.h"
#include "IronBreach.h"
#include "Player/IBUserSettings.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

namespace
{
	const TCHAR* QualityNames[] = { TEXT("LOW"), TEXT("MEDIUM"), TEXT("HIGH"), TEXT("EPIC") };

	FText WindowModeName(EWindowMode::Type Mode)
	{
		switch (Mode)
		{
		case EWindowMode::Fullscreen:         return NSLOCTEXT("IBSettings", "Fullscreen", "FULLSCREEN");
		case EWindowMode::WindowedFullscreen: return NSLOCTEXT("IBSettings", "Borderless", "BORDERLESS");
		default:                              return NSLOCTEXT("IBSettings", "Windowed", "WINDOWED");
		}
	}

	FText OnOff(bool bValue)
	{
		return bValue ? NSLOCTEXT("IBSettings", "On", "ON") : NSLOCTEXT("IBSettings", "Off", "OFF");
	}

	FText Percent(float Normalized)
	{
		return FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Normalized * 100.f)));
	}
}

void UIBSettingsScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	ResolutionOptions = {
		{1280, 720}, {1600, 900}, {1920, 1080}, {2560, 1440}, {3440, 1440}, {3840, 2160}
	};
	if (const UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		const FIntPoint Current = Settings->GetScreenResolution();
		if (!ResolutionOptions.Contains(Current))
		{
			ResolutionOptions.Add(Current);
			ResolutionOptions.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X * A.Y < B.X * B.Y; });
		}
	}

	FpsCapOptions = { 0, 60, 120, 144, 240 };

	BuildFallbackLayout();
}

void UIBSettingsScreen::NativeScreenOpened()
{
	RefreshValues();
}

UWidget* UIBSettingsScreen::AddSection(UVerticalBox* Column, const FText& Label)
{
	// The dossier heading the character and mission sheets already wear: a lit
	// mark, tracked cyan caps, then the hairline. Smaller than the old 18 pt
	// display heading on purpose — a category label is a signpost, not a title,
	// and at 18 pt it was competing with SETTINGS itself.
	UHorizontalBox* Head = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UHorizontalBoxSlot* MarkSlot = Head->AddChildToHorizontalBox(
		IBHangar::Glyph(WidgetTree, EIBMenuGlyph::Diamond, IBStyle::Cyan(), 11.f)))
	{
		MarkSlot->SetVerticalAlignment(VAlign_Center);
		MarkSlot->SetPadding(FMargin(0.f, 0.f, 9.f, 0.f));
	}
	if (UHorizontalBoxSlot* TextSlot = Head->AddChildToHorizontalBox(
		IBMenuLayout::Text(WidgetTree, Label, 13, IBStyle::Cyan(), 180)))
	{
		TextSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* SectionSlot = Column->AddChildToVerticalBox(Head))
	{
		// Space above a heading is what separates one category from the rows of
		// the last one; space below it only pushes the heading off its own list.
		SectionSlot->SetPadding(FMargin(0.f, 22.f, 0.f, 8.f));
	}
	UBorder* Line = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Line());
	Line->SetPadding(FMargin(0.f, 0.5f));
	if (UVerticalBoxSlot* LineSlot = Column->AddChildToVerticalBox(Line))
	{
		LineSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
	}
	return Head;
}

void UIBSettingsScreen::ShowCategory(int32 Index)
{
	if (!CategoryAnchors.IsValidIndex(Index)) { return; }
	ActiveCategory = Index;
	for (int32 i = 0; i < CategoryChips.Num(); ++i)
	{
		IBHangar::StyleTab(CategoryChips[i], i == ActiveCategory);
	}
	// VIDEO owns the left column; AUDIO and CONTROLS share the right one. The
	// chip scrolls that column to the heading and stops there: no row is
	// hidden, no value is touched, and both columns stay fully scrollable by
	// hand — this is a shortcut, not a filter.
	UScrollBox* ColumnScroll = (Index == 0) ? LeftScroll.Get() : RightScroll.Get();
	if (ColumnScroll && CategoryAnchors[Index])
	{
		ColumnScroll->ScrollWidgetIntoView(CategoryAnchors[Index].Get());
	}
}

UTextBlock* UIBSettingsScreen::MakeRow(UVerticalBox* Column, const FText& Label, UButton*& OutPrev, UButton*& OutNext)
{
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	UTextBlock* RowLabel = IBMenuLayout::Text(WidgetTree, Label, 13, IBStyle::TextLo(), 30);
	USizeBox* LabelSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	LabelSize->SetWidthOverride(250.f);
	LabelSize->AddChild(RowLabel);
	if (UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(LabelSize))
	{
		LabelSlot->SetVerticalAlignment(VAlign_Center);
	}

	auto MakeArrow = [this](EIBMenuGlyph Mark)
	{
		// The chevron is the affordance; the box only shows up under the
		// pointer. Sixteen rows times two arrows is thirty-two outlined boxes
		// otherwise, and the sheet stops reading as one surface.
		UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		Button->SetContent(IBHangar::Glyph(WidgetTree, Mark, IBStyle::Cyan(), 13.f));
		FButtonStyle Style = Button->GetStyle();
		Style.Normal   = IBStyle::RoundedBrush(FLinearColor::Transparent, 0.f);
		Style.Hovered  = IBStyle::RoundedBrush(FLinearColor(.04f, .16f, .20f, .95f), 0.f, IBStyle::Cyan(), 1.f);
		Style.Pressed  = IBStyle::RoundedBrush(FLinearColor(.08f, .23f, .28f, .95f), 0.f, IBStyle::Cyan(), 1.f);
		// Disabled keeps a box deliberately: an unavailable control still has to
		// look like a control rather than like empty space.
		Style.Disabled = IBStyle::RoundedBrush(FLinearColor(.006f, .017f, .025f, .45f), 0.f, IBStyle::Line(), 1.f);
		Style.NormalPadding = FMargin(14.f, 7.f);
		Style.PressedPadding = Style.NormalPadding;
		Button->SetStyle(Style);
		return Button;
	};

	OutPrev = MakeArrow(EIBMenuGlyph::ChevronLeft);
	if (UHorizontalBoxSlot* PrevSlot = Row->AddChildToHorizontalBox(OutPrev))
	{
		PrevSlot->SetVerticalAlignment(VAlign_Center);
	}

	// White, one step larger than its label. The approved sheets put cyan on
	// section titles and controls and keep values in service steel; this screen
	// had it the other way round, so cyan was carrying both the headings' job
	// and the data's and separating neither. The chevrons stay cyan, which
	// leaves one honest rule on the page: cyan is what you can act on.
	UTextBlock* Value = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 14, IBStyle::TextHi(), 80);
	Value->SetJustification(ETextJustify::Center);
	USizeBox* ValueSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ValueSize->SetWidthOverride(190.f);
	ValueSize->AddChild(Value);
	if (UHorizontalBoxSlot* ValueSlot = Row->AddChildToHorizontalBox(ValueSize))
	{
		ValueSlot->SetVerticalAlignment(VAlign_Center);
	}

	OutNext = MakeArrow(EIBMenuGlyph::Chevron);
	if (UHorizontalBoxSlot* NextSlot = Row->AddChildToHorizontalBox(OutNext))
	{
		NextSlot->SetVerticalAlignment(VAlign_Center);
	}

	if (UVerticalBoxSlot* RowSlot = Column->AddChildToVerticalBox(Row))
	{
		RowSlot->SetPadding(FMargin(0.f, 5.f));
	}
	return Value;
}

void UIBSettingsScreen::BuildFallbackLayout()
{
	const auto Page = BuildHangarSection(
		NSLOCTEXT("IBSettings", "Title", "SETTINGS"),
		NSLOCTEXT("IBSettings", "Kicker", "OPERATIVE / TERMINAL PREFERENCES"),
		NSLOCTEXT("IBSettings", "ControlsHint", "CHANGES APPLY AND SAVE IMMEDIATELY     ESC / RETURN TO GAME"));
	if (!Page.Body) { return; }
	UVerticalBox* Outer = Page.Body;

	// ---- Category strip ----
	// Sixteen rows across two scrolling columns had no way to get to a heading
	// except by dragging. These chips jump to one. They filter nothing.
	UHorizontalBox* Strip = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	auto AddChip = [this, Strip](const FText& Label) -> UButton*
	{
		UButton* Chip = IBStyle::MakeButton(WidgetTree, Label, 11);
		IBHangar::StyleTab(Chip, /*bActive=*/CategoryChips.Num() == 0);
		if (UHorizontalBoxSlot* ChipSlot = Strip->AddChildToHorizontalBox(Chip))
		{
			ChipSlot->SetVerticalAlignment(VAlign_Center);
			ChipSlot->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		}
		CategoryChips.Add(Chip);
		return Chip;
	};
	AddChip(NSLOCTEXT("IBSettings", "Video", "VIDEO"))
		->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleCategoryVideo);
	AddChip(NSLOCTEXT("IBSettings", "Audio", "AUDIO"))
		->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleCategoryAudio);
	AddChip(NSLOCTEXT("IBSettings", "Controls", "CONTROLS"))
		->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleCategoryControls);
	if (UVerticalBoxSlot* StripSlot = Outer->AddChildToVerticalBox(Strip))
	{
		StripSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 16.f));
	}

	// Two columns: VIDEO left; AUDIO + CONTROLS right.
	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UVerticalBox* Left = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UVerticalBox* Right = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UVerticalBox* LeftPanel = WidgetTree->ConstructWidget<UVerticalBox>();
	UVerticalBox* RightPanel = WidgetTree->ConstructWidget<UVerticalBox>();
	LeftScroll = IBMenuLayout::Scroll(WidgetTree, LeftPanel, Left);
	RightScroll = IBMenuLayout::Scroll(WidgetTree, RightPanel, Right);
	// Roomier gutter inside each card and a wider trough between them: the rows
	// are long and low-contrast, and they were running into the frame.
	const FMargin CardPad(26.f, 18.f, 22.f, 18.f);
	UHorizontalBoxSlot* LeftSlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, LeftPanel, CardPad));
	LeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	LeftSlot->SetPadding(FMargin(0, 0, 24, 0));
	Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, RightPanel, CardPad))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	Outer->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	UButton *Prev = nullptr, *Next = nullptr;

	// ---- VIDEO (left) ----
	CategoryAnchors.Add(AddSection(Left, NSLOCTEXT("IBSettings", "Video", "VIDEO")));

	QualityValue = MakeRow(Left, NSLOCTEXT("IBSettings", "Quality", "QUALITY"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleQualityPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleQualityNext);

	WindowValue = MakeRow(Left, NSLOCTEXT("IBSettings", "Window", "WINDOW"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleWindowPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleWindowNext);

	ResolutionValue = MakeRow(Left, NSLOCTEXT("IBSettings", "Resolution", "RESOLUTION"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleResPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleResNext);

	ScaleValue = MakeRow(Left, NSLOCTEXT("IBSettings", "RenderScale", "RENDER SCALE"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleScalePrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleScaleNext);

	VSyncValue = MakeRow(Left, NSLOCTEXT("IBSettings", "VSync", "VSYNC"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleVSyncToggle);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleVSyncToggle);

	FpsCapValue = MakeRow(Left, NSLOCTEXT("IBSettings", "FpsCap", "FRAME RATE CAP"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleFpsCapPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleFpsCapNext);

	FovValue = MakeRow(Left, NSLOCTEXT("IBSettings", "Fov", "FIELD OF VIEW"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleFovPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleFovNext);

	GammaValue = MakeRow(Left, NSLOCTEXT("IBSettings", "Gamma", "BRIGHTNESS"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleGammaPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleGammaNext);

	ShowFpsValue = MakeRow(Left, NSLOCTEXT("IBSettings", "ShowFps", "FPS COUNTER"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleShowFpsToggle);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleShowFpsToggle);

	// ---- AUDIO (right) ----
	CategoryAnchors.Add(AddSection(Right, NSLOCTEXT("IBSettings", "Audio", "AUDIO")));

	MasterValue = MakeRow(Right, NSLOCTEXT("IBSettings", "Master", "MASTER VOLUME"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleMasterPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleMasterNext);

	MusicValue = MakeRow(Right, NSLOCTEXT("IBSettings", "Music", "MUSIC"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleMusicPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleMusicNext);

	SfxValue = MakeRow(Right, NSLOCTEXT("IBSettings", "Sfx", "EFFECTS"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSfxPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSfxNext);

	// ---- CONTROLS (right) ----
	CategoryAnchors.Add(AddSection(Right, NSLOCTEXT("IBSettings", "Controls", "CONTROLS")));

	SensitivityValue = MakeRow(Right, NSLOCTEXT("IBSettings", "Sensitivity", "MOUSE SENSITIVITY"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSensPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSensNext);

	AdsSensitivityValue = MakeRow(Right, NSLOCTEXT("IBSettings", "AdsSens", "ADS SENSITIVITY"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleAdsSensPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleAdsSensNext);

	InvertValue = MakeRow(Right, NSLOCTEXT("IBSettings", "InvertY", "INVERT Y"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleInvertToggle);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleInvertToggle);

	AdsModeValue = MakeRow(Right, NSLOCTEXT("IBSettings", "AdsMode", "AIM MODE"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleAdsModeToggle);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleAdsModeToggle);

	// ---- Footer: reset + hint ----
	// A hairline first: the footer acts on everything above it, so it should
	// read as a different band rather than as one more row of the right column.
	UBorder* FooterRule = IBStyle::MakeAccentBar(WidgetTree, FLinearColor(.13f, .33f, .40f, .55f));
	FooterRule->SetPadding(FMargin(0.f, 0.5f));
	if (UVerticalBoxSlot* RuleSlot = Outer->AddChildToVerticalBox(FooterRule))
	{
		RuleSlot->SetPadding(FMargin(0.f, 18.f, 0.f, 0.f));
	}
	UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UButton* Reset = IBMenuLayout::Button(WidgetTree, NSLOCTEXT("IBSettings", "Reset", "RESET TO DEFAULTS"));
	Reset->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleResetClicked);
	if (UHorizontalBoxSlot* ResetSlot = Footer->AddChildToHorizontalBox(Reset))
	{
		ResetSlot->SetVerticalAlignment(VAlign_Center);
		ResetSlot->SetPadding(FMargin(0.f, 0.f, 18.f, 0.f));
	}
	UTextBlock* Hint = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBSettings", "ResetHint", "RESTORES VIDEO, AUDIO AND CONTROL PREFERENCES"),
		10, IBStyle::TextLo(), 300);
	if (UHorizontalBoxSlot* HintSlot = Footer->AddChildToHorizontalBox(Hint))
	{
		HintSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* FooterSlot = Outer->AddChildToVerticalBox(Footer))
	{
		FooterSlot->SetPadding(FMargin(0.f, 14.f, 0.f, 0.f));
		FooterSlot->SetHorizontalAlignment(HAlign_Center);
	}

}

void UIBSettingsScreen::RefreshValues()
{
	UIBUserSettings* Settings = UIBUserSettings::Get();
	if (!Settings) { return; }

	if (QualityValue)
	{
		const int32 Quality = FMath::Clamp(Settings->GetOverallScalabilityLevel(), 0, 3);
		QualityValue->SetText(Settings->GetOverallScalabilityLevel() < 0
			? NSLOCTEXT("IBSettings", "Custom", "CUSTOM")
			: FText::FromString(QualityNames[Quality]));
	}
	if (WindowValue)     { WindowValue->SetText(WindowModeName(Settings->GetFullscreenMode())); }
	if (ResolutionValue)
	{
		const FIntPoint Res = Settings->GetScreenResolution();
		ResolutionValue->SetText(FText::FromString(FString::Printf(TEXT("%d × %d"), Res.X, Res.Y)));
	}
	if (ScaleValue)      { ScaleValue->SetText(Percent(Settings->GetResolutionScaleNormalized())); }
	if (VSyncValue)      { VSyncValue->SetText(OnOff(Settings->IsVSyncEnabled())); }
	if (FpsCapValue)
	{
		const int32 Cap = FMath::RoundToInt(Settings->GetFrameRateLimit());
		FpsCapValue->SetText(Cap <= 0
			? NSLOCTEXT("IBSettings", "Uncapped", "UNCAPPED")
			: FText::FromString(FString::Printf(TEXT("%d"), Cap)));
	}
	if (FovValue)        { FovValue->SetText(FText::FromString(FString::Printf(TEXT("%d°"), FMath::RoundToInt(Settings->GetFieldOfView())))); }
	if (GammaValue)      { GammaValue->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), Settings->GetGamma()))); }
	if (ShowFpsValue)    { ShowFpsValue->SetText(OnOff(Settings->GetShowFPS())); }
	if (MasterValue)     { MasterValue->SetText(Percent(Settings->GetMasterVolume())); }
	if (MusicValue)      { MusicValue->SetText(Percent(Settings->GetMusicVolume())); }
	if (SfxValue)        { SfxValue->SetText(Percent(Settings->GetSFXVolume())); }
	if (SensitivityValue)    { SensitivityValue->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), Settings->GetMouseSensitivity()))); }
	if (AdsSensitivityValue) { AdsSensitivityValue->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), Settings->GetADSSensitivity()))); }
	if (InvertValue)     { InvertValue->SetText(OnOff(Settings->GetInvertY())); }
	if (AdsModeValue)
	{
		AdsModeValue->SetText(Settings->GetToggleADS()
			? NSLOCTEXT("IBSettings", "AdsToggle", "TOGGLE")
			: NSLOCTEXT("IBSettings", "AdsHold", "HOLD"));
	}
}

void UIBSettingsScreen::ApplyAndSave()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->ApplySettings(false); // video + custom (ApplyNonResolutionSettings chains ApplyIBSettings)
		Settings->SaveSettings();
	}
	RefreshValues();
}

void UIBSettingsScreen::StepQuality(int32 Direction)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		const int32 Current = FMath::Clamp(Settings->GetOverallScalabilityLevel(), 0, 3);
		Settings->SetOverallScalabilityLevel(FMath::Clamp(Current + Direction, 0, 3));
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepWindowMode(int32 Direction)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		static const EWindowMode::Type Order[] = { EWindowMode::Fullscreen, EWindowMode::WindowedFullscreen, EWindowMode::Windowed };
		int32 Index = 0;
		for (int32 i = 0; i < 3; ++i) { if (Order[i] == Settings->GetFullscreenMode()) { Index = i; break; } }
		Settings->SetFullscreenMode(Order[(Index + Direction + 3) % 3]);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepResolution(int32 Direction)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		if (ResolutionOptions.Num() > 0)
		{
			int32 Index = ResolutionOptions.IndexOfByKey(Settings->GetScreenResolution());
			if (Index == INDEX_NONE) { Index = 0; }
			const int32 Count = ResolutionOptions.Num();
			Settings->SetScreenResolution(ResolutionOptions[(Index + Direction + Count) % Count]);
		}
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepRenderScale(int32 Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		const float Current = Settings->GetResolutionScaleNormalized() * 100.f;
		Settings->SetResolutionScaleNormalized(FMath::Clamp(Current + Delta, 50.f, 100.f) / 100.f);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::ToggleVSync()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetVSyncEnabled(!Settings->IsVSyncEnabled());
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepFpsCap(int32 Direction)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		const int32 Cap = FMath::RoundToInt(Settings->GetFrameRateLimit());
		int32 Index = FpsCapOptions.IndexOfByKey(Cap);
		if (Index == INDEX_NONE) { Index = 0; }
		const int32 Count = FpsCapOptions.Num();
		Settings->SetFrameRateLimit(static_cast<float>(FpsCapOptions[(Index + Direction + Count) % Count]));
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepFov(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetFieldOfView(Settings->GetFieldOfView() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepGamma(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetGamma(Settings->GetGamma() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::ToggleShowFps()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetShowFPS(!Settings->GetShowFPS());
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepMaster(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetMasterVolume(Settings->GetMasterVolume() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepMusic(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetMusicVolume(Settings->GetMusicVolume() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepSfx(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetSFXVolume(Settings->GetSFXVolume() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepSensitivity(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetMouseSensitivity(Settings->GetMouseSensitivity() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::StepAdsSensitivity(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetADSSensitivity(Settings->GetADSSensitivity() + Delta);
	}
	ApplyAndSave();
}

void UIBSettingsScreen::ToggleInvertY()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetInvertY(!Settings->GetInvertY());
	}
	ApplyAndSave();
}

void UIBSettingsScreen::ToggleAdsMode()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetToggleADS(!Settings->GetToggleADS());
	}
	ApplyAndSave();
}

void UIBSettingsScreen::HandleResetClicked()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetToDefaults();
	}
	ApplyAndSave();
}
