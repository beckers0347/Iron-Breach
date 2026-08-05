#pragma once

#include "CoreMinimal.h"
#include "Net/Serialization/FastArraySerializer.h" // Module dep: NetCore (added in Build.cs)
#include "IBItemTypes.generated.h"

class UIBItemDefinition;
class UIBInventoryComponent;

/**
 * Item taxonomy uses the design docs' own vocabulary (CLASSES_AND_PROGRESSION.md):
 * Splices are armor-socketed mods, Doctrines are build-defining drops, Collectibles
 * feed the ledger/lore layer. Keep enum IDENTIFIERS stable forever (they serialize
 * into saves + replicated state); reskin via DisplayName only.
 */
UENUM(BlueprintType)
enum class EIBItemCategory : uint8
{
	None          UMETA(Hidden),
	Weapon,
	Armor,
	Splice        UMETA(DisplayName = "Splice (Armor Mod)"),
	Doctrine,
	Consumable,
	KaijuMaterial UMETA(DisplayName = "Kaiju Material"),
	Collectible   UMETA(DisplayName = "Lore Collectible"),
	Cosmetic
};

/**
 * Rarity ladder. Identifiers are the functional names the design docs already use
 * ("exotics" is load-bearing vocabulary in CLASSES_AND_PROGRESSION.md). Thematic
 * renames (e.g. "Standard Issue", "Prototype") are DisplayName edits — free at any
 * time. Colors live in UIBUISettings so Shane tunes the palette without a rebuild.
 */
UENUM(BlueprintType)
enum class EIBItemRarity : uint8
{
	Common,
	Uncommon,
	Rare,
	Legendary,
	Exotic
};

/** Equip layout: Destiny's 3-weapon / 4-armor grammar, plus the anti-kaiju gear slot
 *  from the GDD. New slots append BEFORE Count; never reorder (serialized). */
UENUM(BlueprintType)
enum class EIBEquipSlot : uint8
{
	None          UMETA(Hidden),
	WeaponPrimary UMETA(DisplayName = "Primary"),
	WeaponSpecial UMETA(DisplayName = "Special"),
	WeaponHeavy   UMETA(DisplayName = "Heavy"),
	ArmorHead     UMETA(DisplayName = "Helm"),
	ArmorChest    UMETA(DisplayName = "Chestplate"),
	ArmorArms     UMETA(DisplayName = "Gauntlets"),
	ArmorLegs     UMETA(DisplayName = "Greaves"),
	GearAntiKaiju UMETA(DisplayName = "Anti-Kaiju Gear"),
	Count         UMETA(Hidden)
};

/** A named stat line for the item details pane (impact/range/handling-style bars). */
USTRUCT(BlueprintType)
struct FIBItemStat
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stat")
	FText StatName;

	/** 0..100 UI-space value; the bar widget normalizes off 100. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stat", meta = (ClampMin = "0", ClampMax = "100"))
	float Value = 0.0f;
};

/**
 * One owned item. The instance carries what varies per drop; everything static
 * lives on the definition asset. Definition replicates as an asset reference
 * (path via the package map) — valid as long as the asset is loaded on clients,
 * which holds for anything granted/equipped. If streaming ever strands a client
 * without the asset loaded, switch this field to a soft path + resolve (noted,
 * not needed at current scale).
 */
USTRUCT(BlueprintType)
struct FIBItemInstance
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Item")
	FGuid InstanceId;

	UPROPERTY(BlueprintReadOnly, Category = "Item")
	TObjectPtr<const UIBItemDefinition> Definition = nullptr;

	UPROPERTY(BlueprintReadOnly, Category = "Item")
	int32 StackCount = 1;

	/** Per-drop Clearance Rating contribution (gear score — CLASSES_AND_PROGRESSION
	 *  "Post-30"). 0 for non-gear. */
	UPROPERTY(BlueprintReadOnly, Category = "Item")
	int32 ClearanceRating = 0;

	bool IsValid() const { return Definition != nullptr && StackCount > 0; }
};

/** Fast-array entry wrapper. */
USTRUCT()
struct FIBInventoryEntry : public FFastArraySerializerItem
{
	GENERATED_BODY()

	UPROPERTY()
	FIBItemInstance Item;
};

/**
 * Replicated item list (FFastArraySerializer): per-entry deltas instead of
 * whole-array resends, per ADR-002's "replication informs" and the netcode
 * notes' pass-1 simplicity rule. Owner-only condition is set by the component.
 */
USTRUCT()
struct FIBInventoryList : public FFastArraySerializer
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<FIBInventoryEntry> Entries;

	/** Back-pointer for client-side change broadcasts. Not replicated. */
	UPROPERTY(NotReplicated)
	TObjectPtr<UIBInventoryComponent> OwnerComponent = nullptr;

	bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
	{
		return FFastArraySerializer::FastArrayDeltaSerialize<FIBInventoryEntry, FIBInventoryList>(Entries, DeltaParms, *this);
	}

	// Client-side notifications: re-broadcast locally so UI listeners work on
	// every machine unchanged (same pattern HealthComponent uses for OnRep).
	void PostReplicatedAdd(const TArrayView<int32>& AddedIndices, int32 FinalSize);
	void PostReplicatedChange(const TArrayView<int32>& ChangedIndices, int32 FinalSize);
	void PreReplicatedRemove(const TArrayView<int32>& RemovedIndices, int32 FinalSize);
};

template <>
struct TStructOpsTypeTraits<FIBInventoryList> : public TStructOpsTypeTraitsBase2<FIBInventoryList>
{
	enum { WithNetDeltaSerializer = true };
};

/** One equipped slot. Plain replicated array on the component (8 slots — delta
 *  serialization would be overkill). */
USTRUCT(BlueprintType)
struct FIBEquipmentEntry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Equipment")
	EIBEquipSlot Slot = EIBEquipSlot::None;

	UPROPERTY(BlueprintReadOnly, Category = "Equipment")
	FIBItemInstance Item;
};
