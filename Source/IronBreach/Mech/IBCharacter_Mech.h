#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "IBCharacter_Mech.generated.h"

class UHealthComponent;

UCLASS()
class IRONBREACH_API AIBCharacter_Mech : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Mech();

protected:
	virtual void BeginPlay() override;

	// Core Components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UHealthComponent* HealthComponent;

	// Sync Meter System Placeholder
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sync")
	float CurrentSyncLevel;

public:	
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	// Implementation of IDamageableInterface
	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;
};