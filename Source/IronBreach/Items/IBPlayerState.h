#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "Player/IBCharacterTypes.h"
#include "Items/IBItemTypes.h"
#include "Progression/XPTypes.h"
#include "IBPlayerState.generated.h"

class UIBInventoryComponent;
class UIBItemDefinition;
class UIBSkillComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBOperativeIdentityChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBOperativeXPChanged);

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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Skills")
	TObjectPtr<UIBSkillComponent> Skills;

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

	/** Pilot XP mirrored from the host's ledger: the total, where the current level began and
	 *  where the next one begins (0 = top of the ladder, or no ladder tuned). Real numbers only —
	 *  the menu header draws its progress from these. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	int32 GetOperativeXP() const { return OperativeXP; }

	UFUNCTION(BlueprintPure, Category = "Operative")
	int32 GetOperativeLevelFloorXP() const { return OperativeLevelFloorXP; }

	UFUNCTION(BlueprintPure, Category = "Operative")
	int32 GetOperativeNextLevelXP() const { return OperativeNextLevelXP; }

	/** 0..1 through the current level; 1 at the top of the ladder. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	float GetOperativeLevelProgress() const;

	/** True while a next level exists on the tuned ladder. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	bool HasNextLevel() const { return OperativeNextLevelXP > OperativeLevelFloorXP; }

	/** Callsign when known, else the platform name — what banners should print. */
	UFUNCTION(BlueprintPure, Category = "Operative")
	FString GetDisplayCallsign() const;

	/** Server-only. Sanitizes again; clients never write this directly. Restores
	 *  the operative's vault and level the first time an identity lands. */
	void SetOperativeIdentity(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId);

	/** Server-only: mirror of the XP ledger. */
	void SetOperativeLevel(int32 NewLevel);

	/** Server-only: mirror of the XP ledger's total for this operative; derives the level bounds. */
	void SetOperativeXP(int32 TotalXP);

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

	/** XP mirror moved (every award during a fight): separate from identity so HUD/menu
	 *  listeners can be as cheap as they need to be. Level-ups still raise the identity event. */
	UPROPERTY(BlueprintAssignable, Category = "Operative")
	FOnIBOperativeXPChanged OnOperativeXPChanged;

	// ---- The Watch (breach board): anyone proposes, the host confirms ----
	// Owning-client entry points: authority applies directly, clients Server-RPC.
	// The state itself lives on AIBWatchBoard (replicated) — Online/IBWatchBoard.h.
	UFUNCTION(BlueprintCallable, Category = "Watch")
	void WatchPropose(FName DestinationId);
	UFUNCTION(BlueprintCallable, Category = "Watch")
	void WatchConfirm();
	UFUNCTION(BlueprintCallable, Category = "Watch")
	void WatchCancel();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void CopyProperties(APlayerState* PlayerState) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void OnRep_Operative();

	UFUNCTION()
	void OnRep_OperativeLevel();

	UFUNCTION()
	void OnRep_OperativeXP();

	UFUNCTION(Server, Reliable)
	void Server_SetOperativeIdentity(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId);

	UFUNCTION(Server, Reliable) void Server_WatchPropose(FName DestinationId);
	UFUNCTION(Server, Reliable) void Server_WatchConfirm();
	UFUNCTION(Server, Reliable) void Server_WatchCancel();

	// ---- Per-operative progression (host-side truth, ADR-002) ----

	/** XP + vault key: player + operative (see UIBXPSubsystem::MakePlayerKey). */
	FString MakeProgressionKey() const;

	/** Server: swap the starter bag for this operative's saved vault (or seed the vault with the starters). */
	void RestoreVault();

	UFUNCTION() void HandleInventoryChangedForVault();
	UFUNCTION() void HandleEquipmentChangedForVault(EIBEquipSlot Slot, const FIBItemInstance& Item);
	UFUNCTION() void HandleXPLevelUp(EXPTrack Track, const FString& RecordKey, int32 NewLevel, int32 OldLevel);
	UFUNCTION() void HandleXPAwarded(EXPTrack Track, const FString& RecordKey, int32 NewTotalXP);

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

	// XP mirror (host writes, everyone reads). Bounds ride along so clients need no tuning asset.
	UPROPERTY(ReplicatedUsing = OnRep_OperativeXP, BlueprintReadOnly, Category = "Operative")
	int32 OperativeXP = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Operative")
	int32 OperativeLevelFloorXP = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Operative")
	int32 OperativeNextLevelXP = 0;

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
