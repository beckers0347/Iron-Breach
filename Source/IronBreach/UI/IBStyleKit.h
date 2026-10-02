#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Styling/CoreStyle.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

/**
 * The Iron Breach UI house style, one header. Every C++-built screen pulls
	 * from here: dark glass panels, service-steel text and cyan navigation.
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
	inline FLinearColor Line()    { return FLinearColor(0.120f, 0.290f, 0.350f, 0.65f); } // hairlines / strokes
	inline FLinearColor TextHi()  { return FLinearColor(0.850f, 0.900f, 1.000f); } // primary text
	inline FLinearColor TextLo()  { return FLinearColor(0.550f, 0.620f, 0.750f); } // secondary text
	inline FLinearColor Amber()   { return FLinearColor(0.850f, 0.620f, 0.180f); } // the Relic accent
	inline FLinearColor Cyan()    { return FLinearColor(0.280f, 0.780f, 0.900f); } // navigation / online
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

	/** Optional condensed display face, reusing the engine font already shipped with the game. */
	inline void UseDisplayFace(UTextBlock* Label)
	{
		if (!Label) { return; }
		const FSlateFontInfo Current = Label->GetFont();
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(TEXT("BoldCondensed"), Current.Size);
		Font.LetterSpacing = Current.LetterSpacing;
		Label->SetFont(Font);
	}

	/** Screen title: big, tracked-out, service-steel. */
	inline UTextBlock* MakeTitle(UWidgetTree* Tree, const FText& Text)
	{
		UTextBlock* Title = MakeText(Tree, Text, 36, TextHi(), 60);
		UseDisplayFace(Title);
		Title->SetShadowOffset(FVector2D::ZeroVector);
		return Title;
	}

	/** Small tracked-out section label ("WEAPONS", "BACKPACK"). */
	inline UTextBlock* MakeSection(UWidgetTree* Tree, const FText& Text)
	{
		return MakeText(Tree, Text, 12, Cyan(), 100);
	}

	/** Shared menu control. Radius remains optional for specialized widgets. */
	inline void StyleButton(UButton* Button, bool bAccent = false, float Radius = 0.0f)
	{
		if (!Button) { return; }
		const FLinearColor Rest = bAccent ? FLinearColor(.025f,.12f,.16f,.88f) : FLinearColor(.006f,.017f,.025f,.55f);
		FButtonStyle Style = Button->GetStyle();
		Style.Normal  = RoundedBrush(Rest, Radius, bAccent ? Cyan() : Line(), 1.0f);
		Style.Hovered = RoundedBrush(FLinearColor(.04f,.16f,.20f,.95f), Radius, Cyan(), 1.0f);
		Style.Pressed = RoundedBrush(FLinearColor(.08f,.23f,.28f), Radius, Cyan(), 1.0f);
		Style.Disabled = RoundedBrush(FLinearColor(.006f,.017f,.025f,.45f), Radius, Line(), 1.0f);
		Style.NormalPadding  = FMargin(16.f, 12.f);
		Style.PressedPadding = Style.NormalPadding;
		Button->SetStyle(Style);
	}

	/** Chip button + label in one call. */
	inline UButton* MakeButton(UWidgetTree* Tree, const FText& Label, int32 FontSize = 15,
		bool bAccent = false, UTextBlock** OutLabel = nullptr)
	{
		UButton* Button = Tree->ConstructWidget<UButton>(UButton::StaticClass());
		StyleButton(Button, bAccent);
		UTextBlock* Text = MakeText(Tree, Label, FontSize, TextHi(), 80);
		Text->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), FontSize));
		Text->SetShadowOffset(FVector2D::ZeroVector);
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
