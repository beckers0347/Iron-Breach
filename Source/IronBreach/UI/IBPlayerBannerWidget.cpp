#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBStyleKit.h"
#include "Items/IBPlayerState.h"
#include "Items/IBInventoryComponent.h"
#include "GameFramework/PlayerState.h"
#include "Components/SizeBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"

void UIBPlayerBannerWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBPlayerBannerWidget::BuildLayout()
{
	if (!WidgetTree || MonogramText) { return; }

	USizeBox* Frame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Frame->SetWidthOverride(176.f);
	Frame->SetHeightOverride(292.f);
	WidgetTree->RootWidget = Frame;

	UBorder* Card = IBStyle::MakePanel(WidgetTree, IBStyle::Panel(), 10.f);
	Card->SetPadding(FMargin(0.f));
	Frame->AddChild(Card);

	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Card->SetContent(Column);

	// Accent bar: the card's allegiance at a glance.
	AccentBar = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Line());
	if (UVerticalBoxSlot* BarSlot = Column->AddChildToVerticalBox(AccentBar))
	{
		BarSlot->SetPadding(FMargin(10.f, 10.f, 10.f, 8.f));
	}
	AccentBar->SetPadding(FMargin(0.f, 2.f)); // 4px bar via padding on an empty border

	// Portrait block: monogram now, Shane's operative render later.
	PortraitBlock = IBStyle::MakePanel(WidgetTree, IBStyle::Ink(), 8.f);
	UOverlay* PortraitOverlay = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	PortraitBlock->SetContent(PortraitOverlay);
	MonogramText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 64, FLinearColor(0.28f, 0.34f, 0.46f), 0);
	if (UOverlaySlot* MonoSlot = PortraitOverlay->AddChildToOverlay(MonogramText))
	{
		MonoSlot->SetHorizontalAlignment(HAlign_Center);
		MonoSlot->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* PortraitSlot = Column->AddChildToVerticalBox(PortraitBlock))
	{
		PortraitSlot->SetPadding(FMargin(10.f, 0.f, 10.f, 8.f));
		PortraitSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	// Callsign.
	NameText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 14, IBStyle::TextHi(), 200);
	NameText->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* NameSlot = Column->AddChildToVerticalBox(NameText))
	{
		NameSlot->SetPadding(FMargin(10.f, 0.f, 10.f, 6.f));
		NameSlot->SetHorizontalAlignment(HAlign_Fill);
	}

	// Clearance row.
	UHorizontalBox* ClearRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	ClearanceLabel = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBBanner", "Clearance", "CLEARANCE"), 9, IBStyle::TextLo(), 500);
	ClearanceValue = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 20, IBStyle::Amber(), 0);
	if (UHorizontalBoxSlot* CL = ClearRow->AddChildToHorizontalBox(ClearanceLabel))
	{
		CL->SetVerticalAlignment(VAlign_Center);
		CL->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	if (UHorizontalBoxSlot* CV = ClearRow->AddChildToHorizontalBox(ClearanceValue))
	{
		CV->SetVerticalAlignment(VAlign_Center);
	}
	if (UVerticalBoxSlot* RowSlot = Column->AddChildToVerticalBox(ClearRow))
	{
		RowSlot->SetPadding(FMargin(12.f, 0.f, 12.f, 6.f));
	}

	// Status chip line.
	StatusChip = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 10, IBStyle::TextLo(), 400);
	StatusChip->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* ChipSlot = Column->AddChildToVerticalBox(StatusChip))
	{
		ChipSlot->SetPadding(FMargin(10.f, 0.f, 10.f, 10.f));
		ChipSlot->SetHorizontalAlignment(HAlign_Fill);
	}
}

void UIBPlayerBannerWidget::SetFromPlayerState(const APlayerState* PS, bool bIsHost)
{
	BuildLayout();
	if (!PS || !MonogramText) { return; }

	const FString Name = PS->GetPlayerName().IsEmpty() ? TEXT("OPERATIVE") : PS->GetPlayerName();

	const FLinearColor Accent = bIsHost ? IBStyle::Amber() : IBStyle::Cyan();
	AccentBar->SetBrush(IBStyle::RoundedBrush(Accent, 2.f));
	MonogramText->SetText(FText::FromString(Name.Left(1).ToUpper()));
	MonogramText->SetColorAndOpacity(FSlateColor(Accent * FLinearColor(1.f, 1.f, 1.f, 0.55f)));
	NameText->SetText(FText::FromString(Name.ToUpper()));
	NameText->SetColorAndOpacity(FSlateColor(IBStyle::TextHi()));

	int32 Clearance = 0;
	if (const AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS))
	{
		if (const UIBInventoryComponent* Inventory = IBPS->GetInventory())
		{
			Clearance = Inventory->GetTotalClearanceRating();
		}
	}
	ClearanceLabel->SetVisibility(ESlateVisibility::HitTestInvisible);
	ClearanceValue->SetText(FText::AsNumber(Clearance));
	ClearanceValue->SetVisibility(ESlateVisibility::HitTestInvisible);

	StatusChip->SetText(bIsHost
		? NSLOCTEXT("IBBanner", "Host", "HOST")
		: NSLOCTEXT("IBBanner", "Linked", "LINKED"));
	StatusChip->SetColorAndOpacity(FSlateColor(Accent));
}

void UIBPlayerBannerWidget::SetEmptySlot(int32 SlotIndex)
{
	BuildLayout();
	if (!MonogramText) { return; }
	ApplyEmptyVisuals();
	NameText->SetText(FText::Format(
		NSLOCTEXT("IBBanner", "EmptyName", "SLOT {0}"), FText::AsNumber(SlotIndex + 1)));
}

void UIBPlayerBannerWidget::ApplyEmptyVisuals()
{
	AccentBar->SetBrush(IBStyle::RoundedBrush(IBStyle::Line(), 2.f));
	MonogramText->SetText(FText::FromString(TEXT("+")));
	MonogramText->SetColorAndOpacity(FSlateColor(FLinearColor(0.18f, 0.23f, 0.32f)));
	NameText->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	ClearanceLabel->SetVisibility(ESlateVisibility::Hidden);
	ClearanceValue->SetVisibility(ESlateVisibility::Hidden);
	StatusChip->SetText(NSLOCTEXT("IBBanner", "Awaiting", "AWAITING OPERATIVE"));
	StatusChip->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
}
