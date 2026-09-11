#pragma once

#include "UI/IBStyleKit.h"
#include "UI/IBMenuBackdrop.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/ScrollBox.h"

/** Opt-in presentation helpers. Authored WBP trees and the Watch keep their layout. */
namespace IBMenuLayout
{
	inline UTextBlock* Text(UWidgetTree* Tree, const FText& Value, int32 Size = 13,
		FLinearColor Color = IBStyle::TextLo(), int32 Tracking = 0)
	{
		UTextBlock* Result = IBStyle::MakeText(Tree, Value, Size, Color, Tracking);
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), Size);
		Font.LetterSpacing = Tracking;
		Result->SetFont(Font);
		Result->SetShadowOffset(FVector2D::ZeroVector);
		return Result;
	}
	inline UTextBlock* Heading(UWidgetTree* Tree, const FText& Value, int32 Size = 34)
	{
		UTextBlock* Result = Text(Tree, Value, Size, IBStyle::TextHi(), 60);
		IBStyle::UseDisplayFace(Result);
		return Result;
	}
	inline UBorder* Card(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(20.f))
	{
		UBorder* Result = IBStyle::MakePanel(Tree, FLinearColor(.012f, .025f, .031f, .96f), 2.f);
		Result->SetPadding(Padding);
		Result->SetContent(Child);
		return Result;
	}
	inline USizeBox* Width(UWidgetTree* Tree, UWidget* Child, float Value)
	{
		USizeBox* Result = Tree->ConstructWidget<USizeBox>();
		Result->SetWidthOverride(Value);
		Result->SetContent(Child);
		return Result;
	}
	inline void Section(UWidgetTree* Tree, UVerticalBox* Column, const FText& Value)
	{
		Column->AddChildToVerticalBox(Heading(Tree, Value, 18))->SetPadding(FMargin(0, 0, 0, 14));
	}
	inline UScrollBox* Scroll(UWidgetTree* Tree, UVerticalBox* Column, UWidget* Child)
	{
		UScrollBox* Result = Tree->ConstructWidget<UScrollBox>();
		Result->SetAllowOverscroll(false);
		Result->SetScrollbarThickness(FVector2D(4, 4));
		Result->AddChild(Child);
		Column->AddChildToVerticalBox(Result)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		return Result;
	}
	inline void StyleButton(UButton* Button, bool bAccent = false)
	{
		IBStyle::StyleButton(Button, bAccent, 2.f);
		FButtonStyle Style = Button->GetStyle();
		Style.Normal = IBStyle::RoundedBrush(bAccent ? FLinearColor(.31f, .21f, .065f) : FLinearColor(.025f, .045f, .052f),
			2.f, bAccent ? IBStyle::Amber() : FLinearColor(.11f, .20f, .23f), 1.f);
		Style.NormalPadding = FMargin(16, 10);
		Style.PressedPadding = FMargin(16, 11, 16, 9);
		Button->SetStyle(Style);
	}
	inline UButton* Button(UWidgetTree* Tree, const FText& Value, UTextBlock** OutLabel = nullptr, bool bAccent = false)
	{
		UButton* Result = Tree->ConstructWidget<UButton>();
		StyleButton(Result, bAccent);
		UTextBlock* Label = Heading(Tree, Value, 16);
		Result->SetContent(Label);
		if (OutLabel) { *OutLabel = Label; }
		return Result;
	}
	struct FPage
	{
		UOverlay* Root = nullptr;
		UVerticalBox* Body = nullptr;
		UVerticalBox* HeaderRight = nullptr;
	};
	inline FPage Begin(UWidgetTree* Tree, const FText& Title, const FText& Subtitle, const FText& Hint, float SurfaceHeight = 760)
	{
		FPage Page;
		if (!Tree) { return Page; }
		Page.Root = Cast<UOverlay>(Tree->RootWidget);
		if (!Tree->RootWidget)
		{
			Page.Root = Tree->ConstructWidget<UOverlay>();
			Tree->RootWidget = Page.Root;
		}
		if (!Page.Root) { return Page; }
		UIBMenuBackdrop* Backdrop = Tree->ConstructWidget<UIBMenuBackdrop>();
		Backdrop->SetVisibility(ESlateVisibility::HitTestInvisible);
		UOverlaySlot* BackdropSlot = Page.Root->AddChildToOverlay(Backdrop);
		BackdropSlot->SetHorizontalAlignment(HAlign_Fill);
		BackdropSlot->SetVerticalAlignment(VAlign_Fill);

		UVerticalBox* Sheet = Tree->ConstructWidget<UVerticalBox>();
		UHorizontalBox* Header = Tree->ConstructWidget<UHorizontalBox>();
		UVerticalBox* HeadingBox = Tree->ConstructWidget<UVerticalBox>();
		HeadingBox->AddChildToVerticalBox(Text(Tree, Subtitle, 11, IBStyle::Cyan(), 160));
		HeadingBox->AddChildToVerticalBox(Heading(Tree, Title, 42))->SetPadding(FMargin(0, 4, 0, 12));
		Header->AddChildToHorizontalBox(HeadingBox)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		Page.HeaderRight = Tree->ConstructWidget<UVerticalBox>();
		Header->AddChildToHorizontalBox(Page.HeaderRight)->SetVerticalAlignment(VAlign_Center);
		Sheet->AddChildToVerticalBox(Header);
		UBorder* Rule = IBStyle::MakeAccentBar(Tree, FLinearColor(.16f, .28f, .30f));
		Rule->SetPadding(FMargin(0, .5f));
		Sheet->AddChildToVerticalBox(Rule)->SetPadding(FMargin(0, 0, 0, 22));
		Page.Body = Tree->ConstructWidget<UVerticalBox>();
		Sheet->AddChildToVerticalBox(Page.Body)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		Sheet->AddChildToVerticalBox(Text(Tree, Hint, 11, IBStyle::TextLo(), 60))->SetPadding(FMargin(0, 20, 0, 0));

		// A single design surface scales down to fit, including narrow windows.
		USizeBox* Surface = Width(Tree, Sheet, 1440);
		Surface->SetHeightOverride(SurfaceHeight);
		UScaleBox* Fit = Tree->ConstructWidget<UScaleBox>();
		Fit->SetStretch(EStretch::ScaleToFit);
		Fit->SetStretchDirection(EStretchDirection::DownOnly);
		UScaleBoxSlot* FitSlot = Cast<UScaleBoxSlot>(Fit->AddChild(Surface));
		FitSlot->SetHorizontalAlignment(HAlign_Center);
		FitSlot->SetVerticalAlignment(VAlign_Center);
		UOverlaySlot* PageSlot = Page.Root->AddChildToOverlay(Fit);
		PageSlot->SetHorizontalAlignment(HAlign_Fill);
		PageSlot->SetVerticalAlignment(VAlign_Fill);
		PageSlot->SetPadding(FMargin(64, 112, 64, 56));
		return Page;
	}
}
