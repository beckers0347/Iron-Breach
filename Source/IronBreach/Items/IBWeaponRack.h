// IBWeaponRack.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBWeaponRack.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UIBItemDefinition;
class UInputAction;
class UIBWeaponRackScreen;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnRackStockChanged);

/**
 * Walk-up weapon picker for a physical rack in the world.
 *
 * Pass 1 (now): hand-place a few generated weapons on it. Run the weapon
 * generator (right-click a UWeaponCombatData -> Generate Weapon Variant, or the
 * Weapon Generator editor widget) to get a few DA_Combat_* assets, pair each
 * with a DA_Visual_* (mesh/FX/ADS), wrap the pair in a DA_Item_* per
 * IBItemDefinition.h (Category = Weapon, CombatData/VisualData = the pair),
 * and drop those item definitions into StockedWeapons on the placed
 * BP_WeaponRack instance.
 *
 * Pass 2 (later, per Shane): this becomes the shared bulk-storage / prize
 * rack. Same actor, same request path — only StockedWeapons's source changes
 * (fed by a storage/prize system instead of hand-authored defaults), and
 * bInfiniteStock flips to false so taking actually depletes shared stock.
 *
 * Networking follows the inventory component's own grammar (ADR-002 / uq7):
 * the picker widget calls UIBInventoryComponent::RequestTakeFromRack (safe
 * from any machine, routes to the server), which validates against this
 * actor's replicated stock and grants through the normal GrantItem path. This
 * actor never talks to the inventory directly the other way — no
 * client-trusted grants, matching how every other mutation in this project works.
 *
 * Interaction is entirely self-contained (no Character Blueprint changes
 * needed): this actor enables input on the overlapping local pawn's own
 * controller while in range, the same trick AIBLootPickup uses for overlap
 * collection, just extended to a keypress instead of automatic pickup.
 */
UCLASS()
class IRONBREACH_API AIBWeaponRack : public AActor
{
	GENERATED_BODY()

public:
	AIBWeaponRack();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	// Note: returns by value (TArray<UIBItemDefinition*>), not a reference to the
	// TObjectPtr-typed member below -- UHT rejects TObjectPtr in UFUNCTION
	// signatures (parameters or return values), only UPROPERTY supports it.
	UFUNCTION(BlueprintPure, Category = "Weapon Rack")
	TArray<UIBItemDefinition*> GetStockedWeapons() const;

	/** Authority only. Validates Index and, unless bInfiniteStock, removes the
	 *  entry so it's gone for everyone. Returns null on a bad/already-taken
	 *  index (two players clicking the same last slot in the same frame). */
	const UIBItemDefinition* Server_TakeAt(int32 Index);

	/** Authority only. Puts Definition on the rack (the storage deposit —
	 *  called through UIBInventoryComponent::RequestStoreToRack, never with a
	 *  client-claimed definition). Returns false off-authority or on null. */
	bool Server_DepositItem(const UIBItemDefinition* Definition);

	/** Fires on this machine whenever StockedWeapons changes (server grant, or
	 *  OnRep on clients) so an open picker widget can refresh live. */
	UPROPERTY(BlueprintAssignable, Category = "Weapon Rack")
	FOnRackStockChanged OnStockChanged;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void HandleEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

	void HandleInteract();

	UFUNCTION()
	void OnRep_StockedWeapons();

	/** Fires on the interacting player's own machine when they enter/leave range —
	 *  hook a "Press [E] to browse weapons" prompt widget to this in BP. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Weapon Rack", meta = (DisplayName = "On Focus Changed"))
	void BP_OnFocusChanged(bool bFocused);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USphereComponent> InteractionSphere;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> RackMesh;

	UPROPERTY(EditDefaultsOnly, Category = "Weapon Rack", meta = (ClampMin = "50.0"))
	float InteractionRadius = 200.0f;

	/** What's currently on the rack. Populate in the level (or later, from a
	 *  storage/prize system) with item definitions whose Category is Weapon. */
	UPROPERTY(EditAnywhere, ReplicatedUsing = OnRep_StockedWeapons, Category = "Weapon Rack")
	TArray<TObjectPtr<UIBItemDefinition>> StockedWeapons;

	/** True (default): taking a weapon grants a copy and the rack stays full —
	 *  right for a test rack or a "prize" pool that regenerates. Flip to false
	 *  for the eventual bulk-storage rack, where taking removes it for everyone. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rack")
	bool bInfiniteStock = true;

	/** Enhanced Input action that opens the picker while in range. No default
	 *  asset exists yet in Content/Input — create IA_Interact (Digital/bool,
	 *  Started trigger) and assign it here, matching how MoveAction/LookAction
	 *  etc. are wired on the Character. Left unassigned = rack does nothing
	 *  (guarded, like every other optional action in this project). */
	UPROPERTY(EditDefaultsOnly, Category = "Weapon Rack|Input")
	TObjectPtr<UInputAction> InteractAction;

	/** WBP child of UIBWeaponRackScreen for Shane's layout, or leave unset to
	 *  use the built-in C++ fallback (functional, unstyled). */
	UPROPERTY(EditDefaultsOnly, Category = "Weapon Rack|UI")
	TSubclassOf<UIBWeaponRackScreen> PickerWidgetClass;

private:
	void BindInputFor(APawn* Pawn);
	void UnbindInputFor(APawn* Pawn);
	void OpenPickerFor(APawn* Pawn);
	void ClosePicker();

	/** Called by the picker widget itself when it closes (Escape / Close button /
	 *  clicked outside) so this actor's ActivePicker bookkeeping stays in sync. */
	friend class UIBWeaponRackScreen;
	void NotifyPickerClosed();

	UPROPERTY(Transient)
	TObjectPtr<APawn> FocusedPawn;

	UPROPERTY(Transient)
	TObjectPtr<UIBWeaponRackScreen> ActivePicker;
};
