#include "UI/IBItemTileWidget.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBUISettings.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "Engine/Texture2D.h"

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
