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

	/** Weapons only: the power-scaling half (damage, fire rate, range) this
	 *  item resolves to. Loot→gun seam — equipping WeaponPrimary forwards
	 *  this to UHitscanWeaponComponent. Populated for existing items by
	 *  migrate_weapon_data_split.py; set directly for new content. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponCombatData> CombatData;

	/** Weapons only: the presentation half (viewmodel mesh/scale/alignment,
	 *  fire effects, ADS handling) this item resolves to. Same seam as
	 *  CombatData, feeding AIBCharacter_Infantry::ApplyWeaponData and the
	 *  weapon rig instead of the fire component. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
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
