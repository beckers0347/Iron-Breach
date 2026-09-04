#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "Player/IBCharacterTypes.h"
#include "Items/IBItemTypes.h"
#include "Progression/XPTypes.h"
#include "IBPlayerState.generated.h"

class UIBInventoryComponent;
class UIBItemDefinition;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBOperativeIdentityChanged);

/**
 * Project player state: the durable per-player home. Inventory lives here so
 * loadout survives respawns and the infantry↔Caryatid pawn swap.
 *
 * Wiring (Shane, per §3 ownership — GameMode content is yours): set
 * BP_IronBreachGameMode's Player State Class to a BP child of this, and fill
 * StarterLoadout there so first-run players have something on the grid.
 * MENUS_UI_WIRING.md §3 has the exact clicks.
 */
UCLASS()
class IRONBREACH_API AIBPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	AIBPlayerState();

	UFUNCTION(BlueprintPure, Category = "Inventory")
	UIBInventoryComponent* GetInventory() const { return InventoryComponent; }

	// ---- Operative identity (who this player brought) ----
	// Mirrored from the owning client's local roster (UIBCharacterSubsystem)
	// via AIBPlayerController::PushOperativeIdentity -> Server RPC -> here, then
	// replicated to everyone. Identity is presentation + future class-kit
	// selection; it is NOT progression truth (that stays on the host per ADR-002).

	UFUNCTION(BlueprintPure, Category = "Operative")
	bool HasOperative() const { return bHasOperative; }

	UFUNCTION(BlueprintPure, Category = "Operative")
	const FString& GetOperativeCallsign() const { return OperativeCallsign; }

	UFUNCTION(BlueprintPure, Category = "Operative")
	EIBOperativeClass GetOperativeClass() const { return OperativeClass; }

	UFUNCTION(BlueprintPure, Category = "Operative")
	EIBOperativeGender GetOperativeGender() const { return OperativeGender; }

	/** Roster id — keys this operative's XP record and vault on the host. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	FGuid GetOperativeId() const { return OperativeId; }

	/** Pilot level from the host's XP ledger, mirrored for banners and the roster card. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	int32 GetOperativeLevel() const { return OperativeLevel; }

	/** Callsign when known, else the platform name — what banners should print. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	FString GetDisplayCallsign() const;

	/** Server-only. Sanitizes again; clients never write this directly. Restores
	 *  the operative's vault and level the first time an identity lands. */
	void SetOperativeIdentity(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId);

	/** Server-only: mirror of the XP ledger. */
	void SetOperativeLevel(int32 NewLevel);

	/**
	 * Owning-client entry point: authority sets directly, clients go through the
	 * Server RPC below. Lives on the PlayerState (not the controller) so the
	 * menu can push identity under ANY GameMode/controller class — the front
	 * end still runs the FirstPerson template controller.
	 */
	UFUNCTION(BlueprintCallable, Category = "Operative")
	void PushOperativeIdentity(const FIBCharacterRecord& Record);

	UPROPERTY(BlueprintAssignable, Category = "Operative")
	FOnIBOperativeIdentityChanged OnOperativeIdentityChanged;

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void CopyProperties(APlayerState* PlayerState) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void OnRep_Operative();

	UFUNCTION()
	void OnRep_OperativeLevel();

	UFUNCTION(Server, Reliable)
	void Server_SetOperativeIdentity(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId);

	// ---- Per-operative progression (host-side truth, ADR-002) ----

	/** XP + vault key: player + operative (see UIBXPSubsystem::MakePlayerKey). */
	FString MakeProgressionKey() const;

	/** Server: swap the starter bag for this operative's saved vault (or seed the vault with the starters). */
	void RestoreVault();

	UFUNCTION() void HandleInventoryChangedForVault();
	UFUNCTION() void HandleEquipmentChangedForVault(EIBEquipSlot Slot, const FIBItemInstance& Item);
	UFUNCTION() void HandleXPLevelUp(EXPTrack Track, const FString& RecordKey, int32 NewLevel, int32 OldLevel);

	void ScheduleVaultSave();
	void SaveVaultNow();

	/** Owning machine only: push the level onto the roster card. */
	void SyncLevelToRoster();

	FTimerHandle VaultSaveHandle;
	bool bVaultBound = false;
	bool bVaultRestored = false;

	UPROPERTY(ReplicatedUsing = OnRep_Operative, BlueprintReadOnly, Category = "Operative")
	FString OperativeCallsign;

	UPROPERTY(ReplicatedUsing = OnRep_Operative, BlueprintReadOnly, Category = "Operative")
	EIBOperativeClass OperativeClass = EIBOperativeClass::Breaker;

	UPROPERTY(ReplicatedUsing = OnRep_Operative, BlueprintReadOnly, Category = "Operative")
	EIBOperativeGender OperativeGender = EIBOperativeGender::Male;

	UPROPERTY(ReplicatedUsing = OnRep_Operative, BlueprintReadOnly, Category = "Operative")
	bool bHasOperative = false;

	UPROPERTY(ReplicatedUsing = OnRep_Operative, BlueprintReadOnly, Category = "Operative")
	FGuid OperativeId;

	UPROPERTY(ReplicatedUsing = OnRep_OperativeLevel, BlueprintReadOnly, Category = "Operative")
	int32 OperativeLevel = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UIBInventoryComponent> InventoryComponent;

	/** Granted once, server-side, on first BeginPlay. Placeholder for the real
	 *  loot/persistence spine (M2 §3.3) — replace with profile load when saves land. */
	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	TArray<TObjectPtr<UIBItemDefinition>> StarterLoadout;

	/** Auto-equip each starter item whose definition has an equip slot. */
	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	bool bAutoEquipStarters = true;

private:
	bool bStartersGranted = false;
};
