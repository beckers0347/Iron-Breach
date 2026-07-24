#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "InputActionValue.h"
#include "IBMech_Base.generated.h"

class AController;

UCLASS()
class IRONBREACH_API AIBMech_Base : public APawn
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

	// --- ROUTED INPUT ACTIONS ---
	// These replace the standard Enhanced Input bindings
	void RouteMoveInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteLookInput(const FInputActionValue& Value, AController* RequestingController);
	void RouteFireInput(AController* RequestingController);
};