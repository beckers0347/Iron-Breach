#pragma once

#include "UI/IBMenuLayout.h"
#include "UI/IBGlassBorder.h"
#include "UI/IBMenuGlyph.h"
#include "Components/ProgressBar.h"
#include "Components/Image.h"
#include "Engine/Texture2D.h"

// Shared presentation for the reference-led character, backpack and mission sheets.
namespace IBHangar
{
inline FLinearColor Cyan() { return IBStyle::Cyan(); }
inline FLinearColor Ink() { return FLinearColor(.008f, .019f, .028f, .83f); }
/** Edge hairline of every glass panel. */
inline FLinearColor Edge() { return FLinearColor(.12f, .29f, .35f, .65f); }
/** Fill of a selected / active surface (rail rows, filter chips). */
inline FLinearColor Lit() { return FLinearColor(.025f, .12f, .16f, .88f); }
inline FLinearColor Fade(const FLinearColor& Color, float Alpha) { return FLinearColor(Color.R, Color.G, Color.B, Color.A * Alpha); }
inline UTextBlock* Label(UWidgetTree* Tree, const FString& Value, int32 Size = 14, FLinearColor Color = IBStyle::TextHi())
{
    return IBMenuLayout::Text(Tree, FText::FromString(Value), Size, Color, 80);
}
/** Chamfered glass frame with an explicit paint recipe (IBGlassBorder.h has the presets). */
inline UIBGlassBorder* Glass(UWidgetTree* Tree, UWidget* Child, FMargin Padding, const FIBGlassStyle& Style,
    FLinearColor Fill = FLinearColor(.008f, .019f, .028f, .83f))
{
    UIBGlassBorder* Result = Tree->ConstructWidget<UIBGlassBorder>();
    Result->SetBrush(IBStyle::RoundedBrush(Fill, 0, Edge(), 1));
    Result->SetPadding(Padding);
    Result->SetGlassStyle(Style);
    if (Child) { Result->SetContent(Child); }
    return Result;
}
/** The standard content panel. Signature is stable; the frame is now chamfered glass. */
inline UBorder* Panel(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(20))
{
    return Glass(Tree, Child, Padding, FIBGlassStyle::Panel(), Ink());
}
/** Nested well / list surface inside a panel: quieter cuts, no accent. */
inline UBorder* Inset(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(12))
{
    return Glass(Tree, Child, Padding, FIBGlassStyle::Inset(), FLinearColor(.004f, .012f, .02f, .55f));
}
/** Small label chip (header identity, counters). */
inline UBorder* Chip(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(10, 5))
{
    return Glass(Tree, Child, Padding, FIBGlassStyle::Chip(), FLinearColor(.006f, .02f, .03f, .78f));
}
/** Inspector / dossier frame: one wide top-right cut. */
inline UBorder* Dossier(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(22))
{
    return Glass(Tree, Child, Padding, FIBGlassStyle::Dossier(), Ink());
}
/** Stat plinth under the operative. */
inline UBorder* Plinth(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(44, 10, 44, 14))
{
    return Glass(Tree, Child, Padding, FIBGlassStyle::Plinth(), FLinearColor(.006f, .016f, .024f, .90f));
}
/** Painted line-art mark in a fixed box. */
inline UIBMenuGlyph* Glyph(UWidgetTree* Tree, EIBMenuGlyph Kind, FLinearColor Tint = IBStyle::Cyan(), float Size = 20.f)
{
    UIBMenuGlyph* Result = Tree->ConstructWidget<UIBMenuGlyph>();
    Result->SetGlyph(Kind); Result->SetTint(Tint); Result->SetGlyphSize(FVector2D(Size, Size));
    return Result;
}
inline void StyleButton(UButton* Button, bool bActive = false)
{
    IBStyle::StyleButton(Button, bActive);
}
/** Rail / list row: flat at rest, lit when active, no outline box around every entry. */
inline void StyleRail(UButton* Button, bool bActive = false)
{
    if (!Button) { return; }
    FButtonStyle Style = Button->GetStyle();
    Style.Normal  = IBStyle::RoundedBrush(bActive ? Lit() : FLinearColor::Transparent, 0, bActive ? Fade(Cyan(), .45f) : FLinearColor::Transparent, bActive ? 1.f : 0.f);
    Style.Hovered = IBStyle::RoundedBrush(bActive ? FLinearColor(.04f,.16f,.20f,.95f) : FLinearColor(.2f,.65f,.75f,.10f), 0, Fade(Cyan(), bActive ? .6f : .3f), 1.f);
    Style.Pressed = IBStyle::RoundedBrush(FLinearColor(.06f,.2f,.25f,.95f), 0, Cyan(), 1.f);
    Style.Disabled = IBStyle::RoundedBrush(FLinearColor::Transparent, 0);
    Style.NormalPadding = FMargin(12, 9); Style.PressedPadding = Style.NormalPadding;
    Button->SetStyle(Style);
}
/** Filter tab: text chip with a lit fill when active, hairline otherwise. */
inline void StyleTab(UButton* Button, bool bActive = false)
{
    if (!Button) { return; }
    FButtonStyle Style = Button->GetStyle();
    Style.Normal  = IBStyle::RoundedBrush(bActive ? Lit() : FLinearColor(.004f,.012f,.02f,.5f), 0, bActive ? Cyan() : Edge(), 1.f);
    Style.Hovered = IBStyle::RoundedBrush(FLinearColor(.04f,.16f,.20f,.95f), 0, Cyan(), 1.f);
    Style.Pressed = IBStyle::RoundedBrush(FLinearColor(.08f,.23f,.28f), 0, Cyan(), 1.f);
    Style.Disabled = IBStyle::RoundedBrush(FLinearColor(.004f,.012f,.02f,.4f), 0, Edge(), 1.f);
    Style.NormalPadding = FMargin(14, 9); Style.PressedPadding = Style.NormalPadding;
    Button->SetStyle(Style);
}
/** Full-bleed scene behind a separately scaled foreground. */
inline void Background(UWidgetTree* Tree, UOverlay* Root)
{
    UImage* Scene = Tree->ConstructWidget<UImage>();
    Scene->SetBrushFromTexture(LoadObject<UTexture2D>(nullptr, TEXT("/Game/IronBreach/UI/Hangar/T_MenuHangar.T_MenuHangar")));
    Scene->SetVisibility(ESlateVisibility::HitTestInvisible);
    UOverlaySlot* ImageSlot = Root->AddChildToOverlay(Scene);
    ImageSlot->SetHorizontalAlignment(HAlign_Fill); ImageSlot->SetVerticalAlignment(VAlign_Fill);
    UBorder* Shade = Tree->ConstructWidget<UBorder>();
    Shade->SetBrushColor(FLinearColor(.002f,.009f,.018f,.28f));
    Shade->SetVisibility(ESlateVisibility::HitTestInvisible);
    UOverlaySlot* ShadeSlot = Root->AddChildToOverlay(Shade);
    ShadeSlot->SetHorizontalAlignment(HAlign_Fill); ShadeSlot->SetVerticalAlignment(VAlign_Fill);
}
/** Front-end overlay in the same 1600 x 900 coordinate space as field menus. */
inline UOverlay* Frontend(UWidgetTree* Tree)
{
    UOverlay* Root = Tree->ConstructWidget<UOverlay>(); Tree->RootWidget = Root;
    Background(Tree, Root);
    UOverlay* Sheet = Tree->ConstructWidget<UOverlay>();
    USizeBox* Design = IBMenuLayout::Width(Tree, Sheet, 1600); Design->SetHeightOverride(900);
    UScaleBox* Fit = Tree->ConstructWidget<UScaleBox>(); Fit->SetStretch(EStretch::ScaleToFit); Fit->SetContent(Design);
    UOverlaySlot* FitSlot = Root->AddChildToOverlay(Fit);
    FitSlot->SetHorizontalAlignment(HAlign_Fill); FitSlot->SetVerticalAlignment(VAlign_Fill);
    return Sheet;
}
inline UButton* Button(UWidgetTree* Tree, const FString& Value, UTextBlock** OutLabel = nullptr)
{
    UButton* Result = Tree->ConstructWidget<UButton>();
    UTextBlock* Text = Label(Tree, Value, 14);
    Result->SetContent(Text); StyleButton(Result);
    if (OutLabel) { *OutLabel = Text; }
    return Result;
}
inline void Rule(UWidgetTree* Tree, UVerticalBox* Box, float Bottom = 16)
{
    UBorder* Line = IBStyle::MakeAccentBar(Tree, FLinearColor(.13f,.33f,.40f,.7f));
    Line->SetPadding(FMargin(0,.5f));
    Box->AddChildToVerticalBox(Line)->SetPadding(FMargin(0,12,0,Bottom));
}
/** Small tracked section title with its hairline, the dossier "OBJECTIVES" / "INTEL" treatment. */
inline void SectionTitle(UWidgetTree* Tree, UVerticalBox* Box, const FString& Value, float Top = 22, float Bottom = 12)
{
    Box->AddChildToVerticalBox(Label(Tree, Value, 13, Cyan()))->SetPadding(FMargin(0, Top, 0, 0));
    Rule(Tree, Box, Bottom);
}
inline void Stat(UWidgetTree* Tree, UVerticalBox* Box, const FText& Name, float Value)
{
    UHorizontalBox* Row = Tree->ConstructWidget<UHorizontalBox>();
    Row->AddChildToHorizontalBox(IBMenuLayout::Text(Tree, Name, 13))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Row->AddChildToHorizontalBox(Label(Tree, FString::Printf(TEXT("%.0f"),Value),13));
    Box->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,0,0,6));
    UProgressBar* Bar = Tree->ConstructWidget<UProgressBar>();
    FProgressBarStyle Style;
    Style.SetBackgroundImage(IBStyle::RoundedBrush(FLinearColor(.08f,.13f,.16f),0));
    Style.SetFillImage(IBStyle::RoundedBrush(FLinearColor::White,0));
    Bar->SetWidgetStyle(Style); Bar->SetFillColorAndOpacity(Cyan());
    Bar->SetPercent(FMath::Clamp(Value / 100.f,0.f,1.f));
    USizeBox* Size = Tree->ConstructWidget<USizeBox>(); Size->SetHeightOverride(4); Size->SetContent(Bar);
    Box->AddChildToVerticalBox(Size)->SetPadding(FMargin(0,0,0,16));
}
}
