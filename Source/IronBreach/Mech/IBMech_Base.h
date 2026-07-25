#pragma once

#include "CoreMinimal.h"
#include "InputActionValue.h"
#include "GameFramework/Character.h"
#include "Combat/WeaponDataAsset.h"
#include "Combat/WeaponRigComponent.h"
#include "IBMech_Base.generated.h"


class AController;
class USpringArmComponent;
class UCameraComponent;
class UWeaponRigComponent;

UCLASS()
class IRONBREACH_API AIBMech_Base : public ACharacter
{
	GENERATED_BODY()

public:
	AIBMech_Base();

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	void PerformWeaponTrace();


public:
	// --- SEAT ASSIGNMENTS ---
	// Who is physically sitting where (Player or AI)
	UPROPERTY(BlueprintReadOnly, Category = "Mech|Seats")
	AController* LeftSeatController;

	UPROPERTY(BlueprintReadOnly, Category = "Mech|Seats")
	AController* RightSeatController;

	// --- ROLE ASSIGNMENTS ---
	// Who is doing what right now
	UPROPERTY(BlueprintReadOnly, Category = "Mech|Roles")
	AController* CurrentDriver;

	UPROPERTY(BlueprintReadOnly, Category = "Mech|Roles")
	AController* CurrentGunner;

	// --- SEATING FUNCTIONS ---
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void AssignToLeftSeat(AController* NewController);

	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void AssignToRightSeat(AController* NewController);

	// The instant-swap logic for testing/AI
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void PerformRoleSwap();

	// Allows a seated controller to request a role hot-swap
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RequestRoleSwap(AController* Requester);

	// Takes the movement signal and checks for driver privileges
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RouteMoveInput(AController* Requester, const FVector2D& InputValue);

	// Takes the mouse movement and checks for driver privileges
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RouteLookInput(AController* Requester, const FVector2D& InputValue);

	// Handles weapon firing triggers
	UFUNCTION(BlueprintCallable, Category = "Mech|Combat")
	void FireWeapon(AController* Requester);

	// Active weapon data reference
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|Combat")
	TObjectPtr<UWeaponDataAsset> CurrentWeaponData;

	// Weapon equip function
	UFUNCTION(BlueprintCallable, Category = "Mech|Combat")
	void EquipWeapon(UWeaponDataAsset* NewWeaponData);

	// The massive mech chassis and head mesh.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<USkeletalMeshComponent> MechMesh;

	// Driver's 3rd Person camera setup.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<USpringArmComponent> DriverSpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<UCameraComponent> DriverCamera_3PV;

	// Gunner's 1st Person cockpit camera setup.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<UCameraComponent> GunnerCamera_FPV;

	// Weapon Rig, essential for FPV posing and FPV view integration[cite: 4].
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Combat")
	TObjectPtr<UWeaponRigComponent> WeaponRigComponent;

	UPROPERTY(BlueprintReadWrite, Category = "Mech|Views")
	bool bIsDriverActive = true;

	// Function to toggle between views.
	UFUNCTION(BlueprintCallable, Category = "Mech|Views")
	void ToggleViewMode();

	// Reference to the Gunner's minimalist cockpit UI crosshair (e.g., from your image).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|UI")
	TSubclassOf<UUserWidget> CockpitCrosshairClass;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech State")
	bool bIsGunner;

	// This tells C++ to send a signal to the Blueprint. We don't write a body for it in .cpp!
	UFUNCTION(BlueprintImplementableEvent, Category = "Mech State")
	void OnRoleSwapped(bool bIsNowGunner);

	// --- ROUTED INPUT ACTIONS ---
	// These replace the standard Enhanced Input bindings
	void RouteMoveInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteLookInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteFireInput(AController* RequestingController);

private:
	// Cache the widget instance for performance.
	TObjectPtr<UUserWidget> CockpitCrosshairInstance;



};