#include "UI/IBSettingsScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
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

void UIBSettingsScreen::AddSection(UVerticalBox* Column, const FText& Label)
{
	UTextBlock* Section = IBMenuLayout::Heading(WidgetTree, Label, 18);
	if (UVerticalBoxSlot* SectionSlot = Column->AddChildToVerticalBox(Section))
	{
		SectionSlot->SetPadding(FMargin(0.f, 12.f, 0.f, 2.f));
	}
	UBorder* Line = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Line());
	Line->SetPadding(FMargin(0.f, 0.5f));
	if (UVerticalBoxSlot* LineSlot = Column->AddChildToVerticalBox(Line))
	{
		LineSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 4.f));
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

	auto MakeArrow = [this](const FText& Glyph)
	{
		UButton* Button = IBMenuLayout::Button(WidgetTree, Glyph);
		FButtonStyle Style = Button->GetStyle();
		Style.NormalPadding = FMargin(12, 5);
		Style.PressedPadding = FMargin(12, 6, 12, 4);
		Button->SetStyle(Style);
		return Button;
	};

	OutPrev = MakeArrow(NSLOCTEXT("IBSettings", "Prev", "<"));
	if (UHorizontalBoxSlot* PrevSlot = Row->AddChildToHorizontalBox(OutPrev))
	{
		PrevSlot->SetVerticalAlignment(VAlign_Center);
	}

	UTextBlock* Value = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::Amber(), 150);
	Value->SetJustification(ETextJustify::Center);
	USizeBox* ValueSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ValueSize->SetWidthOverride(190.f);
	ValueSize->AddChild(Value);
	if (UHorizontalBoxSlot* ValueSlot = Row->AddChildToHorizontalBox(ValueSize))
	{
		ValueSlot->SetVerticalAlignment(VAlign_Center);
	}

	OutNext = MakeArrow(NSLOCTEXT("IBSettings", "Next", ">"));
	if (UHorizontalBoxSlot* NextSlot = Row->AddChildToHorizontalBox(OutNext))
	{
		NextSlot->SetVerticalAlignment(VAlign_Center);
	}

	if (UVerticalBoxSlot* RowSlot = Column->AddChildToVerticalBox(Row))
	{
		RowSlot->SetPadding(FMargin(0.f, 4.f));
	}
	return Value;
}

void UIBSettingsScreen::BuildFallbackLayout()
{
	const auto Page = IBMenuLayout::Begin(WidgetTree,
		NSLOCTEXT("IBSettings", "Title", "SETTINGS"),
		NSLOCTEXT("IBSettings", "Kicker", "OPERATIVE / TERMINAL PREFERENCES"),
		NSLOCTEXT("IBSettings", "ControlsHint", "CHANGES APPLY AND SAVE IMMEDIATELY     ESC / RETURN TO GAME"));
	if (!Page.Body) { return; }
	UVerticalBox* Outer = Page.Body;
	// Two columns: VIDEO left; AUDIO + CONTROLS right.
	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UVerticalBox* Left = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UVerticalBox* Right = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UVerticalBox* LeftPanel = WidgetTree->ConstructWidget<UVerticalBox>();
	UVerticalBox* RightPanel = WidgetTree->ConstructWidget<UVerticalBox>();
	IBMenuLayout::Scroll(WidgetTree, LeftPanel, Left);
	IBMenuLayout::Scroll(WidgetTree, RightPanel, Right);
	UHorizontalBoxSlot* LeftSlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, LeftPanel));
	LeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	LeftSlot->SetPadding(FMargin(0, 0, 20, 0));
	Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, RightPanel))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	Outer->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	UButton *Prev = nullptr, *Next = nullptr;

	// ---- VIDEO (left) ----
	AddSection(Left, NSLOCTEXT("IBSettings", "Video", "VIDEO"));

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
	AddSection(Right, NSLOCTEXT("IBSettings", "Audio", "AUDIO"));

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
	AddSection(Right, NSLOCTEXT("IBSettings", "Controls", "CONTROLS"));

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
		FooterSlot->SetPadding(FMargin(0.f, 16.f, 0.f, 0.f));
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
