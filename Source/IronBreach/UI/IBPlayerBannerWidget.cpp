#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBHexBorder.h"
#include "UI/IBStyleKit.h"
#include "Items/IBPlayerState.h"
#include "Items/IBInventoryComponent.h"
#include "Player/IBCharacterTypes.h"
#include "GameFramework/PlayerState.h"
#include "Components/SizeBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"

void UIBPlayerBannerWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBPlayerBannerWidget::SetFeatured(bool bInFeatured)
{
	bFeatured = bInFeatured;
	BuildLayout();
	ApplySize();
}

void UIBPlayerBannerWidget::ApplySize()
{
	if (!Frame) { return; }
	// The hero card stands taller — the concept sheet's center banner. Heights
	// include the hex points, so content padding below clears them.
	Frame->SetWidthOverride(bFeatured ? 216.f : 178.f);
	Frame->SetHeightOverride(bFeatured ? 404.f : 336.f);
	if (Card)
	{
		Card->SetContentPadding(bFeatured
			? FMargin(16.f, 50.f, 16.f, 44.f)
			: FMargin(14.f, 42.f, 14.f, 38.f));
	}
}

void UIBPlayerBannerWidget::BuildLayout()
{
	if (!WidgetTree || MonogramText) { return; }

	Frame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Frame->SetClipping(EWidgetClipping::ClipToBounds); // long Steam names stay inside the card
	WidgetTree->RootWidget = Frame;

	// The banner silhouette — pointed hex, not a rounded box.
	Card = WidgetTree->ConstructWidget<UIBHexBorder>(UIBHexBorder::StaticClass());
	Frame->AddChild(Card);

	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Card->SetContent(Column);

	// Top accent edge.
	AccentBar = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Line());
	AccentBar->SetPadding(FMargin(0.f, 2.f));
	if (UVerticalBoxSlot* BarSlot = Column->AddChildToVerticalBox(AccentBar))
	{
		BarSlot->SetPadding(FMargin(12.f, 12.f, 12.f, 8.f));
	}

	// Portrait block: monogram / the big invite +.
	PortraitBlock = IBStyle::MakePanel(WidgetTree, IBStyle::Ink(), 9.f);
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
		PortraitSlot->SetPadding(FMargin(12.f, 0.f, 12.f, 8.f));
		PortraitSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	// Callsign, over its own accent underline (the concept's name plate).
	// Wraps: machine names in LAN PIE (DESKTOP-XXXX) and long Steam handles
	// fold to a second line instead of escaping the card.
	NameText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::TextHi(), 150);
	NameText->SetJustification(ETextJustify::Center);
	NameText->SetAutoWrapText(true);
	if (UVerticalBoxSlot* NameSlot = Column->AddChildToVerticalBox(NameText))
	{
		NameSlot->SetPadding(FMargin(12.f, 0.f, 12.f, 3.f));
		NameSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	UnderBar = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Line());
	UnderBar->SetPadding(FMargin(0.f, 1.f));
	if (UVerticalBoxSlot* UnderSlot = Column->AddChildToVerticalBox(UnderBar))
	{
		UnderSlot->SetPadding(FMargin(34.f, 0.f, 34.f, 6.f));
	}

	// The number: clearance big and centered (POWER LEVEL treatment).
	ClearanceValue = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 27, IBStyle::Amber(), 0);
	ClearanceValue->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* ValSlot = Column->AddChildToVerticalBox(ClearanceValue))
	{
		ValSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	ClearanceLabel = IBStyle::MakeText(WidgetTree, NSLOCTEXT("IBBanner", "Clearance", "CLEARANCE"), 9, IBStyle::TextLo(), 600);
	ClearanceLabel->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* LblSlot = Column->AddChildToVerticalBox(ClearanceLabel))
	{
		LblSlot->SetHorizontalAlignment(HAlign_Fill);
		LblSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	}

	// Status chip line.
	StatusChip = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 10, IBStyle::TextLo(), 450);
	StatusChip->SetJustification(ETextJustify::Center);
	if (UVerticalBoxSlot* ChipSlot = Column->AddChildToVerticalBox(StatusChip))
	{
		ChipSlot->SetPadding(FMargin(12.f, 0.f, 12.f, 12.f));
		ChipSlot->SetHorizontalAlignment(HAlign_Fill);
	}

	ApplySize();
}

void UIBPlayerBannerWidget::SetFromPlayerState(const APlayerState* PS, bool bIsHost)
{
	BuildLayout();
	if (!PS || !MonogramText) { return; }
	bEmptyInvitable = false;

	// Callsign once the operative identity has replicated; platform name until then.
	const AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS);
	FString Name = IBPS ? IBPS->GetDisplayCallsign() : PS->GetPlayerName();
	if (Name.IsEmpty()) { Name = TEXT("OPERATIVE"); }
	const FLinearColor Accent = IBStyle::Cyan(); // the fireteam ice-blue; host reads amber on the chip
	// Top edge takes the combat trade's color when we know it (Breaker red, Picket cyan...).
	const FLinearColor TradeColor = (IBPS && IBPS->HasOperative()) ? IBCharacter::ClassColor(IBPS->GetOperativeClass()) : Accent;

	Card->SetFillColor(IBStyle::Panel());
	Card->SetOutlineColor(bFeatured ? Accent : Accent * FLinearColor(1.f, 1.f, 1.f, 0.55f));
	Card->SetOutlineThickness(bFeatured ? 2.0f : 1.25f);
	AccentBar->SetBrush(IBStyle::RoundedBrush(TradeColor, 2.f));

	// Filled card shows the full plate again (banners are pooled and reused).
	NameText->SetVisibility(ESlateVisibility::HitTestInvisible);
	UnderBar->SetVisibility(ESlateVisibility::HitTestInvisible);
	StatusChip->SetVisibility(ESlateVisibility::HitTestInvisible);
	UnderBar->SetBrush(IBStyle::RoundedBrush(Accent * FLinearColor(1.f, 1.f, 1.f, 0.8f), 2.f));
	MonogramText->SetText(FText::FromString(Name.Left(1).ToUpper()));
	MonogramText->SetColorAndOpacity(FSlateColor(Accent * FLinearColor(1.f, 1.f, 1.f, 0.55f)));
	MonogramText->SetFont([this]{ FSlateFontInfo F = MonogramText->GetFont(); F.Size = bFeatured ? 78 : 64; return F; }());
	NameText->SetText(FText::FromString(Name.ToUpper()));
	NameText->SetColorAndOpacity(FSlateColor(IBStyle::TextHi()));
	NameText->SetFont([this]{ FSlateFontInfo F = NameText->GetFont(); F.Size = bFeatured ? 14 : 12; return F; }());

	int32 Clearance = 0;
	if (IBPS)
	{
		if (const UIBInventoryComponent* Inventory = IBPS->GetInventory())
		{
			Clearance = Inventory->GetTotalClearanceRating();
		}
	}
	ClearanceValue->SetText(FText::AsNumber(Clearance));
	ClearanceValue->SetVisibility(ESlateVisibility::HitTestInvisible);
	ClearanceLabel->SetVisibility(ESlateVisibility::HitTestInvisible);

	StatusChip->SetText(bIsHost
		? NSLOCTEXT("IBBanner", "Host", "★ HOST")
		: NSLOCTEXT("IBBanner", "Linked", "LINKED"));
	StatusChip->SetColorAndOpacity(FSlateColor(bIsHost ? IBStyle::Amber() : Accent));
}

void UIBPlayerBannerWidget::SetEmptySlot(int32 /*SlotIndex*/, bool bInvitable)
{
	BuildLayout();
	if (!MonogramText) { return; }
	bEmptyInvitable = bInvitable;

	Card->SetFillColor(FLinearColor(0.018f, 0.026f, 0.045f, 0.92f));
	Card->SetOutlineColor(IBStyle::Line());
	Card->SetOutlineThickness(1.0f);
	AccentBar->SetBrush(IBStyle::RoundedBrush(IBStyle::Line(), 2.f));

	// Just the +. It IS the invite button — no caption needed (Connor's call).
	MonogramText->SetText(FText::FromString(TEXT("+")));
	MonogramText->SetColorAndOpacity(FSlateColor(IBStyle::Cyan() * FLinearColor(1.f, 1.f, 1.f, 0.75f)));
	NameText->SetVisibility(ESlateVisibility::Collapsed);
	UnderBar->SetVisibility(ESlateVisibility::Collapsed);
	ClearanceValue->SetVisibility(ESlateVisibility::Collapsed);
	ClearanceLabel->SetVisibility(ESlateVisibility::Collapsed);
	StatusChip->SetVisibility(ESlateVisibility::Collapsed);
}

FReply UIBPlayerBannerWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (bEmptyInvitable)
	{
		OnInviteClicked.Broadcast(this);
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}
