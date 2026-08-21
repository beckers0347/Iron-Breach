#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "Engine/NetSerialization.h" // Explicit include: FVector_NetQuantize in the multicast signature
#include "IBCharacter_Enemy.generated.h"

class UHealthComponent;
class UWeaponCombatData;
class UWeaponVisualData;
class UIBLootDropComponent;

/**
 * Basic hostile infantry. Patrol/chase/attack logic lives in AIBEnemyAIController;
 * this class owns health, damage handling, death, and firing.
 */
UCLASS()
class IRONBREACH_API AIBCharacter_Enemy : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Enemy();

	/** Fires at the target if the fire-rate cooldown allows it. Called by the AI controller (server-only). */
	void FireAt(AActor* Target);

	/** Cosmetic broadcast: clients hear/see enemy shots (AI runs server-side only). */
	UFUNCTION(NetMulticast, Unreliable)
	void Multicast_FireFX(FVector_NetQuantize TraceEnd);

	UFUNCTION(BlueprintPure, Category = "Enemy")
	bool IsDead() const { return bDead; }

	// Implementation of IDamageableInterface
	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHealthComponent> HealthComponent;

	/** Native loot faucet. BP assigns the table; unassigned falls back to
	 *  DA_Loot_ClassD at BeginPlay so every kill pays. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UIBLootDropComponent> LootDropComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Enemy|Combat")
	TObjectPtr<UWeaponCombatData> CurrentCombatData;

	/** Fire cosmetics only (sound, and eventually tracer FX). Not required to fire --
	 *  FireAt() only needs CurrentCombatData. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Enemy|Combat")
	TObjectPtr<UWeaponVisualData> CurrentVisualData;

	/** Max health applied to the HealthComponent on spawn. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Combat", meta = (ClampMin = "1"))
	float EnemyMaxHealth = 100.0f;

	/** Cone half-angle (degrees) of random aim error per shot. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Combat", meta = (ClampMin = "0", ClampMax = "45"))
	float AimSpreadDegrees = 2.5f;

	/** Blueprint hook: play hit reacts / FX. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Enemy")
	void BP_OnDamaged(const FHitResult& HitResult, AActor* DamageCauser);

	/** Blueprint hook: play death FX / sounds. Ragdoll already handled in C++. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Enemy")
	void BP_OnDied(AActor* Killer);

	UFUNCTION()
	void HandleDeath(AActor* Killer);

private:
	bool bDead = false;
	float LastFireTime = -1000.0f;
};
