#include "UI/IBKitHudWidget.h"
#include "UI/IBStyleKit.h"
#include "Classes/IBOperativeKitComponent.h"
#include "Player/IBCharacterTypes.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ProgressBar.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UIBKitHudWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBKitHudWidget::InitFor(UIBOperativeKitComponent* InKit)
{
	Kit = InKit;
	RefreshLabels();
}

void UIBKitHudWidget::BuildLayout()
{
	if (!WidgetTree || Column) { return; }

	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	WidgetTree->RootWidget = Root;
	SetVisibility(ESlateVisibility::HitTestInvisible);

	Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	for (int32 I=0; I<4; ++I) { Chips.Add(BuildChip(Column)); }

	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Column))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Right);
		ColumnSlot->SetVerticalAlignment(VAlign_Bottom);
		ColumnSlot->SetPadding(FMargin(0.f, 0.f, 28.f, 28.f));
	}
}

UIBKitHudWidget::FChip UIBKitHudWidget::BuildChip(UVerticalBox* InColumn)
{
	FChip Chip;

	Chip.Frame = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.92f), 0.f);
	Chip.Frame->SetPadding(FMargin(10.f, 8.f));

	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	// Key badge.
	UBorder* Badge = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Badge->SetBrush(IBStyle::RoundedBrush(IBStyle::Chip(), 0.f, IBStyle::Line(), 1.f));
	Badge->SetPadding(FMargin(7.f, 2.f));
	Chip.Key = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextHi(), 100);
	Badge->SetContent(Chip.Key);
	if (UHorizontalBoxSlot* BadgeSlot = Row->AddChildToHorizontalBox(Badge))
	{
		BadgeSlot->SetVerticalAlignment(VAlign_Center);
		BadgeSlot->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
	}

	UVerticalBox* Text = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Chip.Name = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextHi(), 50);
	Chip.State = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 50);
	Text->AddChildToVerticalBox(Chip.Name);
	if (UVerticalBoxSlot* StateSlot = Text->AddChildToVerticalBox(Chip.State))
	{
		StateSlot->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f));
	}
	if (UHorizontalBoxSlot* TextSlot = Row->AddChildToHorizontalBox(Text))
	{
		TextSlot->SetVerticalAlignment(VAlign_Center);
		TextSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	Body->AddChildToVerticalBox(Row);

	Chip.Bar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass());
	Chip.Bar->SetPercent(1.f);
	Chip.Bar->SetFillColorAndOpacity(IBStyle::Cyan());
	USizeBox* BarSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	BarSize->SetHeightOverride(3.f);
	BarSize->SetContent(Chip.Bar);
	if (UVerticalBoxSlot* BarSlot = Body->AddChildToVerticalBox(BarSize))
	{
		BarSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}

	Chip.Frame->SetContent(Body);

	USizeBox* ChipSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ChipSize->SetWidthOverride(236.f);
	ChipSize->SetContent(Chip.Frame);
	if (UVerticalBoxSlot* ChipSlot = InColumn->AddChildToVerticalBox(ChipSize))
	{
		ChipSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	}
	return Chip;
}

void UIBKitHudWidget::RefreshLabels()
{
	UIBOperativeKitComponent* K = Kit.Get();
	if (!K) { return; }

	const FLinearColor Accent = IBStyle::Cyan();

	auto Apply = [&](FChip& Chip, const FIBKitAbilitySpec& Spec, const FKey& Key)
	{
		if (Chip.Key)  { Chip.Key->SetText(Key.GetDisplayName(false)); }
		if (Chip.Name) { Chip.Name->SetText(Spec.DisplayName.IsEmpty() ? NSLOCTEXT("IBKit", "Unassigned", "UNASSIGNED") : Spec.DisplayName); }
		if (Chip.Bar)  { Chip.Bar->SetFillColorAndOpacity(Accent); }
		if (Chip.Frame)
		{
			Chip.Frame->SetVisibility(Spec.IsUsable() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
	};
	for (int32 I=0; I<Chips.Num(); ++I) { Apply(Chips[I], K->GetSlotSpec(static_cast<EIBSkillSlot>(I)), K->GetSlotKey(static_cast<EIBSkillSlot>(I))); }
}

void UIBKitHudWidget::UpdateChip(const FChip& Chip, int32 SkillSlot)
{
	UIBOperativeKitComponent* K = Kit.Get();
	if (!K || !Chip.Bar || !Chip.State) { return; }

	const float Remaining = K->GetSlotCooldown(static_cast<EIBSkillSlot>(SkillSlot));
	const float Fraction = FMath::Clamp(Remaining/FMath::Max(.01f,K->GetSlotSpec(static_cast<EIBSkillSlot>(SkillSlot)).Cooldown),0.f,1.f);
	Chip.Bar->SetPercent(1.f - Fraction);
	if (Remaining > 0.05f)
	{
		FString Recovery=FString::Printf(TEXT("%.1fs"),Remaining);
        if (SkillSlot==0 && K->CanReturnToAnchor()) { Recovery=TEXT("PRESS AGAIN / RETURN"); }
        else if (SkillSlot==0 && K->IsConcealed()) { Recovery=TEXT("VEIL ACTIVE / ")+Recovery; }
        else if (SkillSlot==0 && K->GetOperativeClass()==EIBOperativeClass::Breaker)
        { Recovery=FString::Printf(TEXT("%s / ENERGY %.0f"),K->IsGuardActive() ? TEXT("GUARD") : *Recovery,K->GetGuardEnergy()); }
        Chip.State->SetText(FText::FromString(Recovery));
		Chip.State->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	}
	else
	{
		if (SkillSlot==0 && K->GetOperativeClass()==EIBOperativeClass::Breaker)
        { Chip.State->SetText(FText::FromString(FString::Printf(TEXT("READY  /  ENERGY %.0f / 100"),K->GetGuardEnergy()))); }
        else { Chip.State->SetText(NSLOCTEXT("IBKit", "Ready", "READY")); }
		Chip.State->SetColorAndOpacity(FSlateColor(IBStyle::Cyan()));
	}
}

void UIBKitHudWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	for (int32 I=0; I<Chips.Num(); ++I) { UpdateChip(Chips[I],I); }
}
