#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "GameFramework/SaveGame.h"
#include "Items/IBItemTypes.h"
#include "IBLedgerSubsystem.generated.h"

class UIBItemDefinition;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLedgerEntryDiscovered, const UIBItemDefinition*, Definition);

/** Disk format for the ledger. Asset ids stored as strings — survives asset
 *  moves as long as names hold (redirector lesson applies to item DAs too). */
UCLASS()
class IRONBREACH_API UIBLedgerSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY()
	TArray<FString> DiscoveredAssetIds;
};

/**
 * The Ledger — Iron Breach's Collections. The design docs already name this
 * ("collectible ledger", roadmap §persistence; "title strings from collectible
 * ledgers", progression doc), so the class does too.
 *
 * Local-profile data, not replicated: what YOU have catalogued on YOUR machine.
 * GameInstance-scoped so it survives level travel; persisted to a save slot on
 * every new discovery (writes are rare and tiny). When cloud persistence lands
 * (roadmap: EOS Player Data Storage), this subsystem is the single integration
 * point — swap the save backend, nothing upstream moves.
 *
 * The full catalog comes from the Asset Manager ("IBItem" primary assets), so
 * the ledger screen shows undiscovered silhouettes without any hand-kept list.
 */
UCLASS()
class IRONBREACH_API UIBLedgerSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Fires on genuinely-new discoveries only — Shane's "new entry" toast hook. */
	UPROPERTY(BlueprintAssignable, Category = "Ledger")
	FOnLedgerEntryDiscovered OnEntryDiscovered;

	/** Record a definition as seen. Safe to call repeatedly; saves when new. */
	UFUNCTION(BlueprintCallable, Category = "Ledger")
	void MarkDiscovered(const UIBItemDefinition* Definition);

	UFUNCTION(BlueprintPure, Category = "Ledger")
	bool IsDiscovered(const UIBItemDefinition* Definition) const;

	/** Every ledger-visible item definition in the project (loads them — item DAs
	 *  are lightweight). Empty + warning if the Asset Manager entry is missing. */
	UFUNCTION(BlueprintCallable, Category = "Ledger")
	TArray<UIBItemDefinition*> GetFullCatalog() const;

	UFUNCTION(BlueprintPure, Category = "Ledger")
	int32 GetDiscoveredCount() const { return Discovered.Num(); }

private:
	void LoadFromDisk();
	void SaveToDisk() const;

	TSet<FPrimaryAssetId> Discovered;

	static const TCHAR* SaveSlotName;
};
