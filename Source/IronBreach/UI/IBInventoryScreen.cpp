#include "UI/IBInventoryScreen.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "UI/IBItemTileWidget.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
#include "GameFramework/PlayerController.h"

UIBInventoryComponent* UIBInventoryScreen::GetInventory() const
{
	const APlayerController* PC = GetOwningPlayer();
	const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	return PS ? PS->GetInventory() : nullptr;
}

void UIBInventoryScreen::NativeScreenOpened()
{
	BindInventory();
	RebuildAll();
}

void UIBInventoryScreen::NativeScreenClosed()
{
	UnbindInventory();
	BP_OnItemUnfocused();
}

void UIBInventoryScreen::BindInventory()
{
	UIBInventoryComponent* Inventory = GetInventory();
	if (Inventory == BoundInventory) { return; }
	UnbindInventory();

	BoundInventory = Inventory;
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.AddDynamic(this, &UIBInventoryScreen::HandleInventoryChanged);
		BoundInventory->OnEquipmentChanged.AddDynamic(this, &UIBInventoryScreen::HandleEquipmentChanged);
	}
	else
	{
		// Loudly, once, in the log — the #1 setup miss will be the GameMode still
		// pointing at the engine's default PlayerState.
		UE_LOG(LogIronBreach, Warning,
			TEXT("[InventoryScreen] No UIBInventoryComponent — is the GameMode's Player State Class set to IBPlayerState? (MENUS_UI_WIRING.md §3)"));
	}
}

void UIBInventoryScreen::UnbindInventory()
{
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleInventoryChanged);
		BoundInventory->OnEquipmentChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleEquipmentChanged);
		BoundInventory = nullptr;
	}
}

void UIBInventoryScreen::SetCategoryFilter(EIBItemCategory Category)
{
	if (CategoryFilter != Category)
	{
		CategoryFilter = Category;
		RebuildGrid();
	}
}

void UIBInventoryScreen::HandleInventoryChanged()
{
	RebuildGrid();
	RefreshEquipmentWells(); // stack counts/removals can touch equipped items too
}

void UIBInventoryScreen::HandleEquipmentChanged(EIBEquipSlot /*ChangedSlot*/, const FIBItemInstance& /*ChangedItem*/)
{
	RefreshEquipmentWells();
}

void UIBInventoryScreen::RebuildAll()
{
	RebuildGrid();
	RefreshEquipmentWells();
}

void UIBInventoryScreen::RebuildGrid()
{
	if (!ItemGrid) { return; }
	ItemGrid->ClearChildren();

	if (!BoundInventory || !GridTileClass) { return; }

	// Equipped instances stay out of the backpack grid (they live in the wells).
	TSet<FGuid> EquippedIds;
	for (uint8 SlotIndex = 1; SlotIndex < static_cast<uint8>(EIBEquipSlot::Count); ++SlotIndex)
	{
		FIBItemInstance Equipped;
		if (BoundInventory->GetEquippedItem(static_cast<EIBEquipSlot>(SlotIndex), Equipped))
		{
			EquippedIds.Add(Equipped.InstanceId);
		}
	}

	int32 CellIndex = 0;
	for (const FIBItemInstance& Item : BoundInventory->GetItemsByCategory(CategoryFilter))
	{
		if (EquippedIds.Contains(Item.InstanceId)) { continue; }

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }
		Tile->SetItem(Item);
		WireTile(Tile);

		UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns);
		if (GridSlot)
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
	}
}

void UIBInventoryScreen::RefreshEquipmentWells()
{
	if (ClearanceText && BoundInventory)
	{
		ClearanceText->SetText(FText::AsNumber(BoundInventory->GetTotalClearanceRating()));
	}

	for (uint8 SlotIndex = 1; SlotIndex < static_cast<uint8>(EIBEquipSlot::Count); ++SlotIndex)
	{
		const EIBEquipSlot EquipSlot = static_cast<EIBEquipSlot>(SlotIndex);
		UIBItemTileWidget* Well = GetWellForSlot(EquipSlot);
		if (!Well) { continue; }

		WireTile(Well);

		FIBItemInstance Equipped;
		if (BoundInventory && BoundInventory->GetEquippedItem(EquipSlot, Equipped))
		{
			Well->SetItem(Equipped);
		}
		else
		{
			Well->SetEmptySlot(EquipSlot);
		}
	}
}

void UIBInventoryScreen::WireTile(UIBItemTileWidget* Tile)
{
	// Idempotent: Remove+Add so cached/rebuilt tiles never double-fire.
	Tile->OnTileClicked.RemoveDynamic(this, &UIBInventoryScreen::HandleTileClicked);
	Tile->OnTileClicked.AddDynamic(this, &UIBInventoryScreen::HandleTileClicked);
	Tile->OnTileHoverChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleTileHoverChanged);
	Tile->OnTileHoverChanged.AddDynamic(this, &UIBInventoryScreen::HandleTileHoverChanged);
}

UIBItemTileWidget* UIBInventoryScreen::GetWellForSlot(EIBEquipSlot InSlot) const
{
	switch (InSlot)
	{
	case EIBEquipSlot::WeaponPrimary: return Tile_WeaponPrimary;
	case EIBEquipSlot::WeaponSpecial: return Tile_WeaponSpecial;
	case EIBEquipSlot::WeaponHeavy:   return Tile_WeaponHeavy;
	case EIBEquipSlot::ArmorHead:     return Tile_ArmorHead;
	case EIBEquipSlot::ArmorChest:    return Tile_ArmorChest;
	case EIBEquipSlot::ArmorArms:     return Tile_ArmorArms;
	case EIBEquipSlot::ArmorLegs:     return Tile_ArmorLegs;
	case EIBEquipSlot::GearAntiKaiju: return Tile_GearAntiKaiju;
	default:                          return nullptr;
	}
}

void UIBInventoryScreen::HandleTileClicked(UIBItemTileWidget* Tile)
{
	if (!Tile || !BoundInventory) { return; }

	// Equipment well with something in it → unequip. Backpack tile that can be
	// worn → equip. Server decides; the redraw comes back through the signals.
	const bool bIsWell = (GetWellForSlot(Tile->GetRepresentedSlot()) == Tile);
	const FIBItemInstance& Item = Tile->GetItem();

	if (bIsWell && Item.IsValid())
	{
		BoundInventory->RequestUnequip(Tile->GetRepresentedSlot());
	}
	else if (!bIsWell && Item.IsValid() && Item.Definition && Item.Definition->EquipSlot != EIBEquipSlot::None)
	{
		BoundInventory->RequestEquip(Item.InstanceId);
	}
}

void UIBInventoryScreen::HandleTileHoverChanged(UIBItemTileWidget* Tile, bool bHovered)
{
	if (!Tile) { return; }

	if (bHovered && Tile->GetItem().IsValid())
	{
		const bool bIsWell = (GetWellForSlot(Tile->GetRepresentedSlot()) == Tile);
		BP_OnItemFocused(Tile->GetItem(), bIsWell);
	}
	else
	{
		BP_OnItemUnfocused();
	}
}
