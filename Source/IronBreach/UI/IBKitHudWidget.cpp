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
	KitChip = BuildChip(Column);
	MoveChip = BuildChip(Column);

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

	Chip.Frame = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.92f), 8.f);
	Chip.Frame->SetPadding(FMargin(10.f, 8.f));

	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	// Key badge.
	UBorder* Badge = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Badge->SetBrush(IBStyle::RoundedBrush(IBStyle::Chip(), 4.f, IBStyle::Line(), 1.f));
	Badge->SetPadding(FMargin(7.f, 2.f));
	Chip.Key = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextHi(), 100);
	Badge->SetContent(Chip.Key);
	if (UHorizontalBoxSlot* BadgeSlot = Row->AddChildToHorizontalBox(Badge))
	{
		BadgeSlot->SetVerticalAlignment(VAlign_Center);
		BadgeSlot->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
	}

	UVerticalBox* Text = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Chip.Name = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextHi(), 400);
	Chip.State = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 300);
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
	Chip.Bar->SetFillColorAndOpacity(IBStyle::Amber());
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

	const FLinearColor Accent = IBCharacter::ClassColor(K->GetOperativeClass());
	const FIBClassKit& KitData = K->GetKit();

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
	Apply(KitChip, KitData.KitAbility, K->GetKitAbilityKey());
	Apply(MoveChip, KitData.MovementTool, K->GetMovementToolKey());
}

void UIBKitHudWidget::UpdateChip(const FChip& Chip, bool bMovementTool)
{
	UIBOperativeKitComponent* K = Kit.Get();
	if (!K || !Chip.Bar || !Chip.State) { return; }

	const float Remaining = K->GetCooldownRemaining(bMovementTool);
	const float Fraction = K->GetCooldownFraction(bMovementTool);
	Chip.Bar->SetPercent(1.f - Fraction);
	if (Remaining > 0.05f)
	{
		Chip.State->SetText(FText::FromString(FString::Printf(TEXT("%.1fs"), Remaining)));
		Chip.State->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	}
	else
	{
		Chip.State->SetText(NSLOCTEXT("IBKit", "Ready", "READY"));
		Chip.State->SetColorAndOpacity(FSlateColor(IBStyle::Amber()));
	}
}

void UIBKitHudWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	UpdateChip(KitChip, false);
	UpdateChip(MoveChip, true);
}
