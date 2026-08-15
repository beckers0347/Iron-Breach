#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Items/IBItemTypes.h"
#include "IBInventoryComponent.generated.h"

class UIBItemDefinition;
class AIBWeaponRack;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInventoryChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemGranted, const FIBItemInstance&, Item);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnEquipmentChanged, EIBEquipSlot, Slot, const FIBItemInstance&, Item);

/**
 * The player's item state. Lives on AIBPlayerState — NOT the pawn — because
 * loadout must survive pawn churn: infantry death/respawn (u1-08) and the
 * infantry↔Caryatid seat swap both destroy or swap pawns, and the inventory
 * screen has to keep working through all of it.
 *
 * Authority model per ADR-002 / uq7: clients request (Server_* RPCs), the
 * server decides (all mutation authority-gated), replication informs (fast-array
 * list + equipment OnRep re-broadcast the same delegates locally on every
 * machine, so UI and pawn listeners bind once and never care where they run).
 * BP never branches on authority — Shane binds the BlueprintAssignable signals.
 *
 * Visibility split: the backpack list replicates OWNER-ONLY (your bag is yours);
 * Equipment replicates to everyone (other players must see/hear your equipped
 * weapon — the remote-cosmetics pass in the netcode notes builds on this).
 */
UCLASS(ClassGroup = (IronBreach), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UIBInventoryComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UIBInventoryComponent();

	//~ Signals (the seam — UI, ledger, and pawns listen; nothing reaches in)
	UPROPERTY(BlueprintAssignable, Category = "Inventory")
	FOnInventoryChanged OnInventoryChanged;

	UPROPERTY(BlueprintAssignable, Category = "Inventory")
	FOnItemGranted OnItemGranted;

	UPROPERTY(BlueprintAssignable, Category = "Inventory")
	FOnEquipmentChanged OnEquipmentChanged;

	// ---- Authority API (server-side systems: loot drops, vendors, debug) ----

	/** Grant Count of a definition. Stacks stackables, new instance otherwise.
	 *  No-op off authority (logs). Returns the created/updated instance. */
	UFUNCTION(BlueprintCallable, Category = "Inventory", meta = (ReturnDisplayName = "Granted Item"))
	FIBItemInstance GrantItem(const UIBItemDefinition* Definition, int32 Count = 1);

	/** Remove by instance id (consumption, dismantle). Authority only. */
	UFUNCTION(BlueprintCallable, Category = "Inventory")
	bool RemoveItem(FGuid InstanceId, int32 Count = 1);

	// ---- Request API (call from ANY machine; routes to the server itself) ----

	/** Equip an owned instance into its definition's slot. */
	UFUNCTION(BlueprintCallable, Category = "Inventory")
	void RequestEquip(FGuid InstanceId);

	UFUNCTION(BlueprintCallable, Category = "Inventory")
	void RequestUnequip(EIBEquipSlot Slot);

	/** Take slot Index off Rack and grant it to this inventory. Client-safe;
	 *  routes to the server, which re-validates Index against the rack's own
	 *  replicated stock — never trusts an index/definition the client claims. */
	UFUNCTION(BlueprintCallable, Category = "Inventory")
	void RequestTakeFromRack(AIBWeaponRack* Rack, int32 Index);

	// ---- Queries (safe everywhere; read replicated state) ----

	UFUNCTION(BlueprintPure, Category = "Inventory")
	TArray<FIBItemInstance> GetAllItems() const;

	UFUNCTION(BlueprintPure, Category = "Inventory")
	TArray<FIBItemInstance> GetItemsByCategory(EIBItemCategory Category) const;

	UFUNCTION(BlueprintPure, Category = "Inventory")
	bool FindItem(FGuid InstanceId, FIBItemInstance& OutItem) const;

	UFUNCTION(BlueprintPure, Category = "Inventory")
	bool GetEquippedItem(EIBEquipSlot Slot, FIBItemInstance& OutItem) const;

	/** Sum of equipped gear's Clearance Rating — the number on the character pane. */
	UFUNCTION(BlueprintPure, Category = "Inventory")
	int32 GetTotalClearanceRating() const;

	//~ Internal: fast-array client callbacks route here
	void NotifyListChangedFromReplication();
	void NotifyItemAddedFromReplication(const FIBItemInstance& Item);

protected:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(Server, Reliable)
	void Server_Equip(FGuid InstanceId);

	UFUNCTION(Server, Reliable)
	void Server_Unequip(EIBEquipSlot Slot);

	UFUNCTION(Server, Reliable)
	void Server_TakeFromRack(AIBWeaponRack* Rack, int32 Index);

	UFUNCTION()
	void OnRep_Equipment(const TArray<FIBEquipmentEntry>& OldEquipment);

	UPROPERTY(Replicated)
	FIBInventoryList InventoryList;

	UPROPERTY(ReplicatedUsing = OnRep_Equipment)
	TArray<FIBEquipmentEntry> Equipment;

private:
	// Server-side implementations behind the request seam.
	void Equip_OnServer(FGuid InstanceId);
	void Unequip_OnServer(EIBEquipSlot Slot);
	void TakeFromRack_OnServer(AIBWeaponRack* Rack, int32 Index);
	void SetEquipmentSlot(EIBEquipSlot Slot, const FIBItemInstance& Item);

	bool HasAuth() const;

	/** Ledger discovery + local delegate fanout for a newly granted item. Runs on
	 *  whichever machines see the add (server + owning client via fast-array). */
	void HandleItemAddedLocal(const FIBItemInstance& Item);
};
