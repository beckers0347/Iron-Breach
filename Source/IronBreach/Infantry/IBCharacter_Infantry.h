#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "InputActionValue.h"
#include "IBCharacter_Infantry.generated.h"

class UInputMappingContext;
class UInputAction;
class UHealthComponent;
class UHitscanWeaponComponent;
class UWeaponRigComponent;
class UWeaponDataAsset;
class UCameraComponent;
class UStaticMeshComponent;

UCLASS()
class IRONBREACH_API AIBCharacter_Infantry : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Infantry();

	/** Exposed so UHitscanWeaponComponent can read the current spread when firing. */
	UWeaponRigComponent* GetWeaponRig() const { return WeaponRig; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	// Core Components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHealthComponent> HealthComponent;

	/** Single damage path for the project: all player firing goes through this component
	 *  (cosmetic-first + Server_Fire). Uses CurrentWeaponData, forwarded in BeginPlay. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHitscanWeaponComponent> WeaponComponent;

	/** First-person camera at eye height. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	/** First-person viewmodel weapon mesh, posed by the rig. Owner-only visible. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UStaticMeshComponent> WeaponMesh;

	/** Poses the viewmodel and drives ADS (zoom, spread, move speed). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponRigComponent> WeaponRig;

	// Enhanced Input Data
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputMappingContext> DefaultMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> FireAction;

	/** Aim-down-sights: bind as Started (press) + Completed (release), or a Hold trigger. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> AimAction;

	// Current Weapon Context
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponDataAsset> CurrentWeaponData;

	/** Base walk speed the ADS move-speed multiplier scales from. Captured at BeginPlay. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	float BaseWalkSpeed = 0.0f;

	/** Seconds between death and the server respawning this player (networked play, u1-08).
	 *  A player-facing wait, not hidden timer logic. */
	UPROPERTY(EditAnywhere, Category = "Health", meta = (ClampMin = "0.5"))
	float RespawnDelay = 5.0f;

	/** Blueprint hook for death FX/UI (mirrors the enemy's BP_OnDied). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Health")
	void BP_OnDied(AActor* Killer);

	UFUNCTION()
	void HandleDeath(AActor* Killer);

	// Input Actions
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void Fire();
	void StartAiming();
	void StopAiming();

public:
	// Implementation of IDamageableInterface
	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

private:
	FTimerHandle RespawnTimerHandle;
	bool bDead = false;
};
