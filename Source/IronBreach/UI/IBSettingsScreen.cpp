#include "UI/IBSettingsScreen.h"
#include "UI/IBStyleKit.h"
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

	BuildFallbackLayout();
}

void UIBSettingsScreen::NativeScreenOpened()
{
	RefreshValues();
}

UTextBlock* UIBSettingsScreen::MakeRow(UVerticalBox* Column, const FText& Label, UButton*& OutPrev, UButton*& OutNext)
{
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	UTextBlock* RowLabel = IBStyle::MakeText(WidgetTree, Label, 13, IBStyle::TextLo(), 400);
	USizeBox* LabelSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	LabelSize->SetWidthOverride(240.f);
	LabelSize->AddChild(RowLabel);
	if (UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(LabelSize))
	{
		LabelSlot->SetVerticalAlignment(VAlign_Center);
	}

	auto MakeArrow = [this](const FText& Glyph)
	{
		return IBStyle::MakeButton(WidgetTree, Glyph, 13);
	};

	OutPrev = MakeArrow(NSLOCTEXT("IBSettings", "Prev", "<"));
	if (UHorizontalBoxSlot* PrevSlot = Row->AddChildToHorizontalBox(OutPrev))
	{
		PrevSlot->SetVerticalAlignment(VAlign_Center);
	}

	UTextBlock* Value = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 15, IBStyle::Amber(), 150);
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
		RowSlot->SetPadding(FMargin(0.f, 7.f));
	}
	return Value;
}

void UIBSettingsScreen::BuildFallbackLayout()
{
	if (!WidgetTree) { return; }

	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!WidgetTree->RootWidget)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	if (!Root) { return; }

	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Dim->SetBrushColor(FLinearColor(0.01f, 0.015f, 0.03f, 0.82f));
	if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
	{
		DimSlot->SetHorizontalAlignment(HAlign_Fill);
		DimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	UTextBlock* Title = IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBSettings", "Title", "SETTINGS"));
	Column->AddChildToVerticalBox(Title);

	UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Amber());
	Accent->SetPadding(FMargin(0.f, 1.5f));
	if (UVerticalBoxSlot* AccentSlot = Column->AddChildToVerticalBox(Accent))
	{
		AccentSlot->SetPadding(FMargin(0.f, 6.f, 380.f, 12.f));
	}

	UButton *Prev = nullptr, *Next = nullptr;

	QualityValue = MakeRow(Column, NSLOCTEXT("IBSettings", "Quality", "QUALITY"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleQualityPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleQualityNext);

	WindowValue = MakeRow(Column, NSLOCTEXT("IBSettings", "Window", "WINDOW"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleWindowPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleWindowNext);

	ResolutionValue = MakeRow(Column, NSLOCTEXT("IBSettings", "Resolution", "RESOLUTION"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleResPrev);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleResNext);

	VolumeValue = MakeRow(Column, NSLOCTEXT("IBSettings", "Volume", "MASTER VOLUME"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleVolumeDown);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleVolumeUp);

	SensitivityValue = MakeRow(Column, NSLOCTEXT("IBSettings", "Sensitivity", "MOUSE SENSITIVITY"), Prev, Next);
	Prev->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSensDown);
	Next->OnClicked.AddDynamic(this, &UIBSettingsScreen::HandleSensUp);

	UTextBlock* Hint = IBStyle::MakeText(WidgetTree,
		NSLOCTEXT("IBSettings", "Hint", "CHANGES APPLY AND SAVE IMMEDIATELY  ·  ESC TO CLOSE"),
		10, IBStyle::TextLo(), 300);
	Hint->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* HintSlot = Column->AddChildToVerticalBox(Hint))
	{
		HintSlot->SetPadding(FMargin(0.f, 18.f, 0.f, 0.f));
	}

	// Card chrome, same sheet as the System screen.
	UBorder* Card = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.96f), 14.f);
	Card->SetPadding(FMargin(34.f, 28.f));
	Card->SetContent(Column);
	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Card))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Center);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
	}
}

void UIBSettingsScreen::RefreshValues()
{
	UIBUserSettings* Settings = UIBUserSettings::Get();
	if (!Settings) { return; }

	if (QualityValue)
	{
		const int32 Quality = FMath::Clamp(Settings->GetOverallScalabilityLevel(), 0, 3);
		// -1 = custom per-category levels; show as CUSTOM rather than lying.
		QualityValue->SetText(Settings->GetOverallScalabilityLevel() < 0
			? NSLOCTEXT("IBSettings", "Custom", "CUSTOM")
			: FText::FromString(QualityNames[Quality]));
	}
	if (WindowValue)
	{
		WindowValue->SetText(WindowModeName(Settings->GetFullscreenMode()));
	}
	if (ResolutionValue)
	{
		const FIntPoint Res = Settings->GetScreenResolution();
		ResolutionValue->SetText(FText::FromString(FString::Printf(TEXT("%d × %d"), Res.X, Res.Y)));
	}
	if (VolumeValue)
	{
		VolumeValue->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Settings->GetMasterVolume() * 100.f))));
	}
	if (SensitivityValue)
	{
		SensitivityValue->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), Settings->GetMouseSensitivity())));
	}
}

void UIBSettingsScreen::ApplyAndSave()
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->ApplySettings(false); // pushes video changes live
		Settings->ApplyIBSettings();
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
		// Cycle order: Fullscreen -> Borderless -> Windowed.
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

void UIBSettingsScreen::StepVolume(float Delta)
{
	if (UIBUserSettings* Settings = UIBUserSettings::Get())
	{
		Settings->SetMasterVolume(Settings->GetMasterVolume() + Delta);
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
