#include "IBMechAIController.h"
#include "IBMech_Base.h"
#include "IBGunnerSeat.h"
#include "IronBreach.h"

AIBMechAIController::AIBMechAIController()
{
	// Standard AI setup
}

void AIBMechAIController::BeginPlay()
{
	Super::BeginPlay();

	if (MechBehaviorTree)
	{
		RunBehaviorTree(MechBehaviorTree);
	}
}

void AIBMechAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	// NOTE: no seat claiming here. This used to call AssignToRightSeat(this)
	// unconditionally — with auto-possess it fired before BeginPlay, claimed both roles
	// for a controller that got unpossessed the moment the player boarded, and the mech
	// ignored every input. Seat assignment is owned by AIBMech_Base (ChooseSeat for the
	// single-machine flow, ServerBoard/BackfillSeatWithAI for the networked flow).
	if (const AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(InPawn))
	{
		UE_LOG(LogIronBreach, Display, TEXT("[MechAI] Co-pilot on the guns of %s."), *GetNameSafe(Seat->OwningMech));
	}
	else if (const AIBMech_Base* Mech = Cast<AIBMech_Base>(InPawn))
	{
		UE_LOG(LogIronBreach, Display, TEXT("[MechAI] Possessed hull %s. Awaiting seat assignment."), *GetNameSafe(Mech));
	}
}

void AIBMechAIController::OnUnPossess()
{
	// Release whatever seat we held so a stale pointer can't keep a role occupied.
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->VacateSeat(this);
	}
	else if (const AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(GetPawn()))
	{
		if (Seat->OwningMech)
		{
			Seat->OwningMech->VacateSeat(this);
		}
	}

	Super::OnUnPossess();
}
