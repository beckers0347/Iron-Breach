#pragma once

#include "UI/IBMenuLayout.h"
#include "Components/ProgressBar.h"

// Shared presentation for the reference-led character, backpack and mission sheets.
namespace IBHangar
{
inline FLinearColor Cyan() { return FLinearColor(.28f, .78f, .9f); }
inline FLinearColor Ink() { return FLinearColor(.008f, .019f, .028f, .83f); }
inline UTextBlock* Label(UWidgetTree* Tree, const FString& Value, int32 Size = 14, FLinearColor Color = IBStyle::TextHi())
{
    return IBMenuLayout::Text(Tree, FText::FromString(Value), Size, Color, 80);
}
inline UBorder* Panel(UWidgetTree* Tree, UWidget* Child, FMargin Padding = FMargin(20))
{
    UBorder* Result = IBMenuLayout::Card(Tree, Child, Padding);
    Result->SetBrush(IBStyle::RoundedBrush(Ink(), 0, FLinearColor(.12f, .29f, .35f, .65f), 1));
    return Result;
}
inline void StyleButton(UButton* Button, bool bActive = false)
{
    if (!Button) { return; }
    FButtonStyle Style;
    Style.SetNormal(IBStyle::RoundedBrush(bActive ? FLinearColor(.025f,.12f,.16f,.88f) : FLinearColor(.006f,.017f,.025f,.55f), 0,
        bActive ? Cyan() : FLinearColor(.12f,.27f,.32f,.6f), 1));
    Style.SetHovered(IBStyle::RoundedBrush(FLinearColor(.04f,.16f,.20f,.95f), 0, Cyan(), 1));
    Style.SetPressed(IBStyle::RoundedBrush(FLinearColor(.08f,.23f,.28f), 0, Cyan(), 1));
    Style.SetNormalPadding(FMargin(16,12)); Style.SetPressedPadding(FMargin(16,12));
    Button->SetStyle(Style);
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
