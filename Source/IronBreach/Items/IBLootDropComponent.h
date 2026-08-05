#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "IBLootDropComponent.generated.h"

class UIBLootTableAsset;
class AIBPlayerState;
class AIBLootPickup;

/** Who gets a loot roll when this thing dies. */
UENUM(BlueprintType)
enum class EIBLootEligibility : uint8
{
	/** Everyone who damaged it (HealthComponent's contributor set). Falls back
	 *  to AllPlayers if the set resolves empty — environmental or scripted
	 *  kills should never void loot. The Destiny rule. */
	DamageContributors,
	/** Every player in the session. The co-op-generosity rule (DRG/Helldivers
	 *  spirit) — right for story beats and public-event completion rewards. */
	AllPlayers
};

/** How each player's rolls reach them. */
UENUM(BlueprintType)
enum class EIBLootDelivery : uint8
{
	/** Scatter AIBLootPickup actors — per player: you only see and can only
	 *  collect YOUR drops (the engram moment, no ninja-looting). */
	PhysicalPickups,
	/** Straight into each eligible inventory. Mission rewards, things that
	 *  shouldn't sit on the ground. */
	DirectGrant
};

/**
 * The loot faucet — per-player instanced. Drop this on any enemy/kaiju BP,
 * assign a table, done: when the owner's HealthComponent fires OnDeath
 * (server), EVERY eligible player rolls the table INDEPENDENTLY and receives
 * their own loot. Your drops are invisible and untouchable to everyone else;
 * two players killing the same Class-D each walk away with their own roll.
 *
 * No enemy/kaiju code knows this exists and this knows nothing about them
 * (signals-only; it finds the HealthComponent by class at BeginPlay).
 *
 * If PhysicalPickups is chosen but no PickupClass is assigned, it falls back
 * to direct grant rather than eating the loot silently (and logs the miss).
 *
 * Shane: this is level/content side — yours to add freely, like the map POI.
 */
UCLASS(ClassGroup = (IronBreach), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UIBLootDropComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot")
	TObjectPtr<UIBLootTableAsset> LootTable;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot")
	EIBLootEligibility Eligibility = EIBLootEligibility::DamageContributors;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot")
	EIBLootDelivery Delivery = EIBLootDelivery::PhysicalPickups;

	/** Shane's BP_LootPickup (mesh/light/Niagara live there). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot", meta = (EditCondition = "Delivery == EIBLootDelivery::PhysicalPickups"))
	TSubclassOf<AIBLootPickup> PickupClass;

	/** Drops scatter on a ring of this radius around the corpse (cm). Every
	 *  player's ring occupies the same spots — they're mutually invisible, so
	 *  it just reads as "my drops" to each of them. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot", meta = (EditCondition = "Delivery == EIBLootDelivery::PhysicalPickups", ClampMin = "0.0"))
	float ScatterRadius = 140.0f;

	/** Lift off the ground so drops don't clip terrain (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loot", meta = (EditCondition = "Delivery == EIBLootDelivery::PhysicalPickups"))
	float SpawnHeightOffset = 60.0f;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleOwnerDeath(AActor* Killer);

private:
	/** Eligibility -> the concrete player set, per the mode + fallback rule. */
	void GatherEligiblePlayers(TArray<AIBPlayerState*>& OutPlayers) const;

	void SpawnPickupsFor(AIBPlayerState* Player, const struct FIBLootRoll* Rolls, int32 NumRolls) const;

	bool bDropped = false; // one payout per life, whatever OnDeath does
};
