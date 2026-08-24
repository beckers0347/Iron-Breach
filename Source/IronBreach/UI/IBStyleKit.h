#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

/**
 * The Iron Breach UI house style, one header. Every C++-built screen pulls
 * from here so the whole game reads as ONE service console: ink-dark rounded
 * panels, service-steel text, Relic-amber accents, uplink-cyan for friendlies.
 *
 * Shane: WBP children override freely — this only styles what C++ builds.
 */
namespace IBStyle
{
	// ---- Palette ----
	inline FLinearColor Ink()     { return FLinearColor(0.008f, 0.012f, 0.022f); } // screen dim base
	inline FLinearColor Panel()   { return FLinearColor(0.030f, 0.040f, 0.065f); } // cards / sheets
	inline FLinearColor Chip()    { return FLinearColor(0.050f, 0.070f, 0.110f); } // buttons at rest
	inline FLinearColor ChipHot() { return FLinearColor(0.100f, 0.130f, 0.190f); } // buttons hovered
	inline FLinearColor Line()    { return FLinearColor(0.120f, 0.160f, 0.240f); } // hairlines / strokes
	inline FLinearColor TextHi()  { return FLinearColor(0.850f, 0.900f, 1.000f); } // primary text
	inline FLinearColor TextLo()  { return FLinearColor(0.550f, 0.620f, 0.750f); } // secondary text
	inline FLinearColor Amber()   { return FLinearColor(0.850f, 0.620f, 0.180f); } // the Relic accent
	inline FLinearColor Cyan()    { return FLinearColor(0.250f, 0.750f, 0.850f); } // friendly / online
	inline FLinearColor Danger()  { return FLinearColor(0.800f, 0.250f, 0.200f); } // destructive

	/** Rounded solid-color brush — the base of every panel and chip. */
	inline FSlateBrush RoundedBrush(const FLinearColor& Color, float Radius = 8.0f,
		const FLinearColor& Outline = FLinearColor::Transparent, float OutlineWidth = 0.0f)
	{
		FSlateBrush Brush;
		Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
		Brush.TintColor = Color;
		Brush.OutlineSettings = FSlateBrushOutlineSettings(FVector4(Radius, Radius, Radius, Radius), Outline, OutlineWidth);
		return Brush;
	}

	/** Panel border: rounded, hairline-stroked card. */
	inline UBorder* MakePanel(UWidgetTree* Tree, const FLinearColor& Fill, float Radius = 10.0f)
	{
		UBorder* Border = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Border->SetBrush(RoundedBrush(Fill, Radius, Line(), 1.0f));
		return Border;
	}

	/** Text with the house treatment. Tracking is 1/1000 em — headers breathe. */
	inline UTextBlock* MakeText(UWidgetTree* Tree, const FText& Text, int32 Size,
		const FLinearColor& Color, int32 Tracking = 0)
	{
		UTextBlock* Label = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Label->SetText(Text);
		FSlateFontInfo Font = Label->GetFont();
		Font.Size = Size;
		Font.LetterSpacing = Tracking;
		Label->SetFont(Font);
		Label->SetColorAndOpacity(FSlateColor(Color));
		Label->SetShadowOffset(FVector2D(1.f, 1.f));
		Label->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.7f));
		return Label;
	}

	/** Screen title: big, tracked-out, service-steel. */
	inline UTextBlock* MakeTitle(UWidgetTree* Tree, const FText& Text)
	{
		return MakeText(Tree, Text, 26, TextHi(), 400);
	}

	/** Small tracked-out section label ("WEAPONS", "BACKPACK"). */
	inline UTextBlock* MakeSection(UWidgetTree* Tree, const FText& Text)
	{
		return MakeText(Tree, Text, 12, TextLo(), 500);
	}

	/** The house button: rounded chip, lighter on hover with an amber stroke,
	 *  pressed sinks. Works on ANY UButton (fallback-built or WBP-bound). */
	inline void StyleButton(UButton* Button, bool bAccent = false, float Radius = 6.0f)
	{
		if (!Button) { return; }
		const FLinearColor Rest = bAccent ? FLinearColor(0.32f, 0.235f, 0.075f) : Chip();
		FButtonStyle Style = Button->GetStyle();
		Style.Normal  = RoundedBrush(Rest, Radius, Line(), 1.0f);
		Style.Hovered = RoundedBrush(ChipHot(), Radius, Amber(), 1.5f);
		Style.Pressed = RoundedBrush(Ink(), Radius, Amber(), 1.5f);
		Style.NormalPadding  = FMargin(14.f, 7.f);
		Style.PressedPadding = FMargin(14.f, 8.f, 14.f, 6.f);
		Button->SetStyle(Style);
	}

	/** Chip button + label in one call. */
	inline UButton* MakeButton(UWidgetTree* Tree, const FText& Label, int32 FontSize = 15,
		bool bAccent = false, UTextBlock** OutLabel = nullptr)
	{
		UButton* Button = Tree->ConstructWidget<UButton>(UButton::StaticClass());
		StyleButton(Button, bAccent);
		UTextBlock* Text = MakeText(Tree, Label, FontSize, TextHi(), 250);
		Button->AddChild(Text);
		if (OutLabel) { *OutLabel = Text; }
		return Button;
	}

	/** Thin accent bar (the Apex-banner top stripe, section underlines). */
	inline UBorder* MakeAccentBar(UWidgetTree* Tree, const FLinearColor& Color)
	{
		UBorder* Bar = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Bar->SetBrush(RoundedBrush(Color, 2.0f));
		return Bar;
	}
}
