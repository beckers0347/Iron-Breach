#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/HitResult.h" // Explicit include: FHitResult is used by value in the dynamic delegate payload
#include "HealthComponent.generated.h"

class AController;

// Delegates for Event-Driven UI and Game Logic
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnHealthChangedSignature, float, CurrentHealth, float, MaxHealth, const FHitResult&, HitResult);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeathSignature, AActor*, Killer);

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class IRONBREACH_API UHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UHealthComponent();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health")
	float MaxHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health")
	float CurrentHealth;

public:
	UPROPERTY(BlueprintAssignable, Category = "Health|Events")
	FOnHealthChangedSignature OnHealthChanged;

	UPROPERTY(BlueprintAssignable, Category = "Health|Events")
	FOnDeathSignature OnDeath;

	UFUNCTION(BlueprintCallable, Category = "Health")
	void ApplyDamage(float Amount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser);

	UFUNCTION(BlueprintPure, Category = "Health")
	float GetHealthPercent() const { return (MaxHealth > 0.0f) ? (CurrentHealth / MaxHealth) : 0.0f; }

	// Allows owning actors to set their base health safely
	void SetMaxHealth(float NewMaxHealth)
	{
		MaxHealth = NewMaxHealth;
	}
};
