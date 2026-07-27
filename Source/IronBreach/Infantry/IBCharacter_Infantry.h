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
class AIBMech_Base;

UCLASS()
class IRONBREACH_API AIBCharacter_Infantry : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Infantry();

	/** Exposed so UHitscanWeaponComponent can read the current spread when firing. */
	UWeaponRigComponent* GetWeaponRig() const { return WeaponRig; }

	// --- CARYATID BOARDING (u3-07: interact -> Server_Board possession swap) ---

	/** Interact input: find a boardable mech in front of us and start boarding. Fires
	 *  BP_OnMechInteract for a seat-select UI; when bAutoBoardOnInteract is set (default)
	 *  it also boards the navigator station directly so the flow works with zero UI. */
	UFUNCTION(BlueprintCallable, Category = "Boarding")
	void TryBoardMech();

	/** Board a specific mech/station. Call this from seat-select widget buttons
	 *  (LEFT = navigator/hull, RIGHT = gunner seat). Routes to the server automatically. */
	UFUNCTION(BlueprintCallable, Category = "Boarding")
	void RequestBoard(AIBMech_Base* Mech, bool bWantLeftSeat);

	/** UI hook: a boardable mech was found by TryBoardMech. Show your seat-select here
	 *  and call RequestBoard from its buttons. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Boarding")
	void BP_OnMechInteract(AIBMech_Base* Mech);

	/** Skip the UI and take the helm directly on interact. Turn off once the seat-select
	 *  widget flow drives RequestBoard itself. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Boarding")
	bool bAutoBoardOnInteract = true;

	/** How far ahead (cm) the interact sweep looks for a mech. Mechs are big — generous. */
	UPROPERTY(EditAnywhere, Category = "Boarding", meta = (ClampMin = "100.0"))
	float BoardReach = 600.0f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	/** Boarding is server-arbitrated (ADR-002: the server owns the truth about seats). */
	UFUNCTION(Server, Reliable)
	void Server_RequestBoard(AIBMech_Base* Mech, bool bWantLeftSeat);

	/** Find the mech this pawn could board right now (sweep, then proximity fallback). */
	AIBMech_Base* FindBoardableMech() const;

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

	/** Board a mech (IA_Interact). Unassigned -> falls back to the E key so boarding
	 *  works before any content wiring. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> InteractAction;

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

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon")
	bool bIsArmed = false;

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
