#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "GameFramework/SaveGame.h"
#include "IBVaultSubsystem.generated.h"

class UIBInventoryComponent;

/** One saved item — definition by path so the vault survives content moves being logged, not silently lost. */
USTRUCT()
struct FIBVaultItem
{
	GENERATED_BODY()

	UPROPERTY() FSoftObjectPath Definition;
	UPROPERTY() FGuid InstanceId;
	UPROPERTY() int32 StackCount = 1;
	UPROPERTY() int32 ClearanceRating = 0;
};

/** Everything one operative owns and wears. */
USTRUCT()
struct FIBVaultRecord
{
	GENERATED_BODY()

	UPROPERTY() TArray<FIBVaultItem> Items;

	/** Slot (EIBEquipSlot as uint8) -> equipped instance id. */
	UPROPERTY() TMap<uint8, FGuid> Equipped;

	UPROPERTY() FDateTime SavedUtc = FDateTime(0);

	bool IsEmpty() const { return Items.Num() == 0; }
};

/** Local save file: every operative's vault this machine has hosted, keyed like XP records. */
UCLASS()
class IRONBREACH_API UIBVaultSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY() int32 SaveVersion = 1;
	UPROPERTY() TMap<FString, FIBVaultRecord> Vaults;

	static const TCHAR* SlotName;
	static const int32 UserIndex;
};

/**
 * Per-operative loadout persistence — the "vault". Same posture as XP
 * (ADR-002): the HOST's disk is the truth for its world, records are keyed by
 * UIBXPSubsystem::MakePlayerKey (player + operative), so three billets are
 * three vaults. AIBPlayerState restores on identity arrival and checkpoints
 * on every inventory/equipment change (debounced) and on logout.
 */
UCLASS()
class IRONBREACH_API UIBVaultSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	bool FindVault(const FString& Key, FIBVaultRecord& OutRecord) const;
	void StoreVault(const FString& Key, const FIBVaultRecord& Record);

	/** Snapshot an inventory into a record. */
	static FIBVaultRecord Capture(const UIBInventoryComponent* Inventory);

	/** Authority only: replace the inventory's contents with the record's. */
	static void Restore(UIBInventoryComponent* Inventory, const FIBVaultRecord& Record);

	UFUNCTION(BlueprintCallable, Category = "Vault")
	void SaveNow();

private:
	void LoadFromDisk();

	UPROPERTY(Transient)
	TMap<FString, FIBVaultRecord> Vaults;

	bool bDirty = false;
};
