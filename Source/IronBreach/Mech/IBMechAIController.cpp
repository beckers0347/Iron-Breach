#include "IBMechAIController.h"
#include "IBMech_Base.h"

AIBMechAIController::AIBMechAIController()
{
	// Standard AI setup
}

void AIBMechAIController::BeginPlay()
{
	Super::BeginPlay();
	
	// Start thinking if we have a brain
	if (MechBehaviorTree)
	{
		RunBehaviorTree(MechBehaviorTree);
	}
}

void AIBMechAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	// Try to get into the Mech
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(InPawn))
	{
		// The Player usually grabs Left. The AI will grab Right.
		Mech->AssignToRightSeat(this);
		
		UE_LOG(LogTemp, Display, TEXT("AI Co-Pilot successfully boarded the Mech chassis."));
	}
}