#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Items/IBItemTypes.h"
#include "IBItemDefinition.generated.h"

class UTexture2D;
class UWeaponCombatData;
class UWeaponVisualData;

/**
 * The static half of an item (DA_Item_* assets). Instance-varying data lives in
 * FIBItemInstance. Field MEANINGS are C++ (Connor), field VALUES are content
 * (either) — per conventions §3.
 *
 * Registered with the Asset Manager under PrimaryAssetType "IBItem" so the
 * ledger can enumerate the full catalog without hard references. The wiring doc
 * covers the one-time Project Settings entry.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UIBItemDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	static const FPrimaryAssetType PrimaryAssetType;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FText DisplayName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity", meta = (MultiLine = "true"))
	FText Description;

	/** Lore line for the details pane footer (bible voice; italics in UI). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity", meta = (MultiLine = "true"))
	FText Flavor;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	EIBItemCategory Category = EIBItemCategory::Weapon;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	EIBItemRarity Rarity = EIBItemRarity::Common;

	/** None = not equippable (materials, collectibles, consumables). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	EIBEquipSlot EquipSlot = EIBEquipSlot::None;

	/** Soft so the inventory grid can exist before art does; tiles sync-load on
	 *  display (icons are tiny). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UTexture2D> Icon;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stacking", meta = (ClampMin = "1"))
	int32 MaxStack = 1;

	/** Base Clearance Rating for gear drops; instances copy this at grant time
	 *  (drop-roll variance comes later with the loot generator, M2 §3.3). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "0"))
	int32 BaseClearanceRating = 0;

	/** Detail-pane stat bars. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats")
	TArray<FIBItemStat> Stats;

	/** DEPRECATED -- UWeaponVisualData is now itself a UIBItemDefinition subclass (see
	 *  Combat/WeaponVisualData.h), so a weapon's item data lives directly on that one
	 *  asset instead of a separate DA_Item_* wrapper pointing at it. Named LegacyCombatData
	 *  rather than CombatData because (a) that name collides with UWeaponVisualData's own
	 *  new CombatData field -- UHT rejects a derived class member shadowing a base class
	 *  member of the same name -- and (b) the literal suffix "_DEPRECATED" is a reserved
	 *  UHT convention that requires the property to drop all Edit/BlueprintReadOnly
	 *  specifiers (UHT errors otherwise), and this still needs to stay editor-visible so
	 *  Python's get_editor_property can read it during migration. Both this field and
	 *  VisualData below are left in place ONLY so the migration script (Content/Python/
	 *  migrate_item_into_visual.py) can still read each old item's Combat link and copy
	 *  this item's own fields (DisplayName, Icon, EquipSlot, Rarity, Stats, ...) onto the
	 *  matching VisualData asset's newly-inherited fields. Do not point new content at
	 *  this -- once the migration has run and been verified, both fields go away and
	 *  weapons stop needing a DA_Item_* wrapper at all. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Deprecated")
	TObjectPtr<UWeaponCombatData> LegacyCombatData;

	/** DEPRECATED (weapons only) -- see the note on LegacyCombatData above. New
	 *  weapon content doesn't need a DA_Item_* at all: create a UWeaponVisualData asset
	 *  directly (it IS an item now) and attach THAT to the rack/inventory/loadout. This
	 *  field stays only so the migration script can find the VisualData asset a legacy
	 *  DA_Item_* used to point at. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Deprecated")
	TObjectPtr<UWeaponVisualData> VisualData;

	/** Untick for quest tokens etc. that should never appear in the ledger. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ledger")
	bool bShowInLedger = true;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override
	{
		return FPrimaryAssetId(PrimaryAssetType, GetFName());
	}
};

inline const FPrimaryAssetType UIBItemDefinition::PrimaryAssetType(TEXT("IBItem"));
