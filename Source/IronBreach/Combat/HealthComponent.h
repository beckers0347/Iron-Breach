#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/HitResult.h" // Explicit include: FHitResult is used by value in the dynamic delegate payload
#include "HealthComponent.generated.h"

class AController;
class UDamageType;

// Delegates for Event-Driven UI and Game Logic
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnHealthChangedSignature, float, CurrentHealth, float, MaxHealth, const FHitResult&, HitResult);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeathSignature, AActor*, Killer);

/**
 * Replicated health. Authority model (ADR-002): damage is applied ONLY on the server;
 * clients learn about it through replication and re-broadcast the same delegates locally,
 * so UI/FX listeners work identically on every machine.
 * Client-side OnDeath fires with Killer = nullptr (killer identity is server knowledge;
 * replicate it later if a killcam ever needs it).
 */
UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class IRONBREACH_API UHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UHealthComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Health")
	float MaxHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_CurrentHealth, Category = "Health")
	float CurrentHealth;

	/** Prototype convenience: reload the current level when this component's owner dies (enable on the player).
	 *  Only honored in standalone — in networked play the respawn flow owns death (see u1-08). */
	UPROPERTY(EditAnywhere, Category = "Health")
	bool bRestartLevelOnDeath = false;

	/** Bridges Unreal's generic damage pipeline (UGameplayStatics::ApplyDamage / TakeDamage) into this component. */
	UFUNCTION()
	void HandleAnyDamage(AActor* DamagedActor, float Damage, const UDamageType* DamageType, AController* InstigatedBy, AActor* DamageCauser);

	UFUNCTION()
	void OnRep_CurrentHealth(float OldHealth);

public:
	UPROPERTY(BlueprintAssignable, Category = "Health|Events")
	FOnHealthChangedSignature OnHealthChanged;

	UPROPERTY(BlueprintAssignable, Category = "Health|Events")
	FOnDeathSignature OnDeath;

	/** Server-only: silently ignored on clients (authority applies damage, replication informs). */
	UFUNCTION(BlueprintCallable, Category = "Health")
	void ApplyDamage(float Amount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser);

	UFUNCTION(BlueprintPure, Category = "Health")
	float GetHealthPercent() const { return (MaxHealth > 0.0f) ? (CurrentHealth / MaxHealth) : 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Health")
	bool IsDepleted() const { return CurrentHealth <= 0.0f; }

	// Allows owning actors to set their base health safely (server-authoritative; call before/at BeginPlay)
	void SetMaxHealth(float NewMaxHealth)
	{
		MaxHealth = NewMaxHealth;
	}

private:
	/** Guards double death broadcasts on a single machine (server broadcast vs OnRep). */
	bool bDeathHandled = false;
};
