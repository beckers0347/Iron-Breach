#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "IBCharacter_Enemy.generated.h"

class UHealthComponent;
class UWeaponDataAsset;

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

	/** Fires at the target if the fire-rate cooldown allows it. Called by the AI controller. */
	void FireAt(AActor* Target);

	UFUNCTION(BlueprintPure, Category = "Enemy")
	bool IsDead() const { return bDead; }

	// Implementation of IDamageableInterface
	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHealthComponent> HealthComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Enemy|Combat")
	TObjectPtr<UWeaponDataAsset> CurrentWeaponData;

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
