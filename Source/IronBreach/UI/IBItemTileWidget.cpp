#include "UI/IBItemTileWidget.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBUISettings.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/Texture2D.h"

void UIBItemTileWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Bare WBP (or raw C++ tile): build the square ourselves — rarity frame,
	// icon fill, name label for icon-less early content, stack count corner.
	if (!RarityBorder && !IconImage && WidgetTree)
	{
		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetWidthOverride(88.f);
		Size->SetHeightOverride(88.f);
		WidgetTree->RootWidget = Size;

		UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Frame->SetPadding(FMargin(3.f));
		Frame->SetBrushColor(FLinearColor(0.45f, 0.48f, 0.44f)); // Common; RefreshVisuals recolors
		Size->AddChild(Frame);

		UBorder* Inner = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Inner->SetBrushColor(FLinearColor(0.03f, 0.035f, 0.05f, 0.95f));
		Inner->SetPadding(FMargin(0.f));
		Frame->SetContent(Inner);

		UOverlay* Stack = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		Inner->SetContent(Stack);

		UImage* Icon = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		if (UOverlaySlot* IconSlot = Stack->AddChildToOverlay(Icon))
		{
			IconSlot->SetHorizontalAlignment(HAlign_Fill);
			IconSlot->SetVerticalAlignment(VAlign_Fill);
		}

		UTextBlock* Name = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		FSlateFontInfo NameFont = Name->GetFont();
		NameFont.Size = 9;
		Name->SetFont(NameFont);
		Name->SetJustification(ETextJustify::Center);
		Name->SetAutoWrapText(true);
		Name->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.9f, 1.f)));
		if (UOverlaySlot* NameSlot = Stack->AddChildToOverlay(Name))
		{
			NameSlot->SetHorizontalAlignment(HAlign_Center);
			NameSlot->SetVerticalAlignment(VAlign_Center);
			NameSlot->SetPadding(FMargin(4.f));
		}

		UTextBlock* Count = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		FSlateFontInfo CountFont = Count->GetFont();
		CountFont.Size = 11;
		Count->SetFont(CountFont);
		Count->SetColorAndOpacity(FSlateColor(FLinearColor::White));
		Count->SetShadowOffset(FVector2D(1.f, 1.f));
		if (UOverlaySlot* CountSlot = Stack->AddChildToOverlay(Count))
		{
			CountSlot->SetHorizontalAlignment(HAlign_Right);
			CountSlot->SetVerticalAlignment(VAlign_Bottom);
			CountSlot->SetPadding(FMargin(0.f, 0.f, 5.f, 3.f));
		}

		RarityBorder = Frame;
		IconImage = Icon;
		NameText = Name;
		StackText = Count;
	}

	RefreshVisuals();
}

void UIBItemTileWidget::SetItem(const FIBItemInstance& InItem)
{
	Item = InItem;
	Definition = InItem.Definition;
	RepresentedSlot = Definition ? Definition->EquipSlot : EIBEquipSlot::None;
	bLocked = false;
	RefreshVisuals();
}

void UIBItemTileWidget::SetLocked(const UIBItemDefinition* InDefinition)
{
	Item = FIBItemInstance();
	Definition = InDefinition;
	RepresentedSlot = EIBEquipSlot::None;
	bLocked = true;
	RefreshVisuals();
}

void UIBItemTileWidget::SetEmptySlot(EIBEquipSlot InSlot)
{
	Item = FIBItemInstance();
	Definition = nullptr;
	RepresentedSlot = InSlot;
	bLocked = false;
	RefreshVisuals();
}

void UIBItemTileWidget::RefreshVisuals()
{
	if (IconImage)
	{
		UTexture2D* IconTexture = Definition ? Definition->Icon.LoadSynchronous() : nullptr;
		if (IconTexture)
		{
			IconImage->SetBrushFromTexture(IconTexture);
		}
		IconImage->SetVisibility(IconTexture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
		// Silhouette: black out the icon, keep the shape — the classic
		// "you haven't found this yet" read.
		IconImage->SetColorAndOpacity(bLocked ? LockedTint : FLinearColor::White);
	}

	if (StackText)
	{
		const bool bShowStack = !bLocked && Item.IsValid() && Item.StackCount > 1;
		StackText->SetText(FText::AsNumber(Item.StackCount));
		StackText->SetVisibility(bShowStack ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}

	if (NameText)
	{
		// Icon-less content (most of it, this early) reads as a labeled chip;
		// once real icons land the label collapses automatically.
		const bool bHasIcon = Definition && !Definition->Icon.IsNull();
		if (bLocked)
		{
			NameText->SetText(NSLOCTEXT("IBTile", "Sealed", "DATA\nSEALED"));
		}
		else if (Definition)
		{
			NameText->SetText(Definition->DisplayName);
		}
		else
		{
			NameText->SetText(FText::GetEmpty());
		}
		NameText->SetVisibility((!bHasIcon && Definition)
			? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}

	if (RarityBorder)
	{
		FLinearColor Frame = FLinearColor(0.1f, 0.1f, 0.1f, 0.6f); // empty-well default
		if (Definition)
		{
			Frame = UIBUISettings::Get()->GetRarityColor(Definition->Rarity);
			if (bLocked)
			{
				Frame *= 0.35f; // dimmed frame still whispers the rarity
				Frame.A = 1.0f;
			}
		}
		RarityBorder->SetBrushColor(Frame);
	}

	BP_OnTileUpdated();
}

FReply UIBItemTileWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		OnTileClicked.Broadcast(this);
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UIBItemTileWidget::NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseEnter(InGeometry, InMouseEvent);
	OnTileHoverChanged.Broadcast(this, true);
}

void UIBItemTileWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseLeave(InMouseEvent);
	OnTileHoverChanged.Broadcast(this, false);
}
