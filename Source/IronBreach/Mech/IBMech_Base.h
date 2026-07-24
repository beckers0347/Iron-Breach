#pragma once

#include "CoreMinimal.h"
#include "InputActionValue.h"
#include "GameFramework/Character.h"
#include "IBMech_Base.generated.h"


class AController;

UCLASS()
class IRONBREACH_API AIBMech_Base : public ACharacter
{
	GENERATED_BODY()

public:
	AIBMech_Base();

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

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

	// --- ROUTED INPUT ACTIONS ---
	// These replace the standard Enhanced Input bindings
	void RouteMoveInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteLookInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteFireInput(AController* RequestingController);
};