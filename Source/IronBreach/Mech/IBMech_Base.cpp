#include "IBMech_Base.h"
#include "GameFramework/Controller.h"
#include "Engine/LocalPlayer.h"
#include "IBMechAIController.h"

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

	// Spawn the AI Co-Pilot
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	// Create the AI brain in the world
	AIBMechAIController* CoPilot = GetWorld()->SpawnActor<AIBMechAIController>(AIBMechAIController::StaticClass(), GetActorLocation(), GetActorRotation(), SpawnParams);

	if (CoPilot)
	{
		// Force the AI into the Right Seat pointer manually
		// DO NOT call CoPilot->Possess(this) or it will kick the human out!
		AssignToRightSeat(CoPilot);

		UE_LOG(LogTemp, Display, TEXT("[Mech] AI successfully loaded into the Right Seat."));
	}

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

	if (!CurrentDriver)
	{
		CurrentDriver = LeftSeatController;
	}
	else if (!CurrentGunner) // <--- PUT THE 'ELSE' BACK!
	{
		CurrentGunner = LeftSeatController;
	}
}

void AIBMech_Base::AssignToRightSeat(AController* NewController)
{
	if (!NewController) return;
	RightSeatController = NewController;

	if (!CurrentDriver)
	{
		CurrentDriver = RightSeatController;
	}
	else if (!CurrentGunner) // <--- PUT THE 'ELSE' BACK!
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

void AIBMech_Base::RouteMoveInput(AController* Requester, const FVector2D& InputValue)
{
	// Gatekeeper: Only the designated driver is allowed to steer the chassis
	if (Requester != CurrentDriver) return;

	// X is Forward/Backward (W/S), Y is Left/Right (A/D) based on standard 2D Axis setup
	if (InputValue.Y != 0.0f)
	{
		AddMovementInput(GetActorForwardVector(), InputValue.Y);
	}

	if (InputValue.X != 0.0f)
	{
		AddMovementInput(GetActorRightVector(), InputValue.X);
	}
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

void AIBMech_Base::RequestRoleSwap(AController* Requester)
{
	// Check if the requester is actually sitting in the mech
	if (Requester != LeftSeatController && Requester != RightSeatController) return;

	AController* CoPilot = (Requester == LeftSeatController) ? RightSeatController : LeftSeatController;

	// If the co-pilot is an AI, they auto-accept the swap. 
	// (Later, we will add human-to-human pending logic here)
	if (Cast<AAIController>(CoPilot))
	{
		UE_LOG(LogTemp, Display, TEXT("[Mech] Swap requested by Human. AI Co-pilot auto-accepting."));
		PerformRoleSwap();
	}
}