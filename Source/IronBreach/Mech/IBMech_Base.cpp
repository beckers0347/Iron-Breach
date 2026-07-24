#include "IBMech_Base.h"
#include "GameFramework/Controller.h"
#include "Engine/LocalPlayer.h"

AIBMech_Base::AIBMech_Base()
{
	PrimaryActorTick.bCanEverTick = true;
	
	LeftSeatController = nullptr;
	RightSeatController = nullptr;
	CurrentDriver = nullptr;
	CurrentGunner = nullptr;
}

void AIBMech_Base::BeginPlay()
{
	Super::BeginPlay();
}

void AIBMech_Base::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Note: Because two controllers are sending input, we don't bind directly to the mech here 
	// the way we do with the infantry. Instead, the PlayerControllers will read the Enhanced Input 
	// and call RouteMoveInput() or RouteFireInput() on this possessed Mech.
}

// --- SEAT & ROLE MANAGEMENT ---

void AIBMech_Base::AssignToLeftSeat(AController* NewController)
{
	if (!NewController) return;
	LeftSeatController = NewController;

	// If no driver is assigned yet, default the left seat to driving
	if (!CurrentDriver)
	{
		CurrentDriver = LeftSeatController;
	}
	else if (!CurrentGunner)
	{
		CurrentGunner = LeftSeatController;
	}
}

void AIBMech_Base::AssignToRightSeat(AController* NewController)
{
	if (!NewController) return;
	RightSeatController = NewController;

	// Fill whatever role is empty
	if (!CurrentDriver)
	{
		CurrentDriver = RightSeatController;
	}
	else if (!CurrentGunner)
	{
		CurrentGunner = RightSeatController;
	}
}

void AIBMech_Base::PerformRoleSwap()
{
	// Swap the pointers
	AController* Temp = CurrentDriver;
	CurrentDriver = CurrentGunner;
	CurrentGunner = Temp;

	UE_LOG(LogTemp, Log, TEXT("[Mech] Roles Swapped! Driver is now: %s"), 
		CurrentDriver ? *CurrentDriver->GetName() : TEXT("None"));
}

// --- INPUT ROUTING (THE GATEKEEPER) ---

void AIBMech_Base::RouteMoveInput(const FInputActionValue& Value, AController* RequestingController)
{
	// STRICT FILTER: Only the current driver can move the chassis
	if (RequestingController != CurrentDriver)
	{
		return; // Ignore input from the Gunner
	}

	FVector2D MovementVector = Value.Get<FVector2D>();

	// Add your standard movement logic here (AddMovementInput, etc.)
}

void AIBMech_Base::RouteFireInput(AController* RequestingController)
{
	// STRICT FILTER: Only the current gunner can fire the main weapons
	if (RequestingController != CurrentGunner)
	{
		return; // Ignore trigger pulls from the Driver
	}

	// Now check which side tank this gunner is sitting in
	if (RequestingController == LeftSeatController)
	{
		UE_LOG(LogTemp, Warning, TEXT("Firing LEFT side weapon systems! Building Left Heat."));
	}
	else if (RequestingController == RightSeatController)
	{
		UE_LOG(LogTemp, Warning, TEXT("Firing RIGHT side weapon systems! Building Right Heat."));
	}
}