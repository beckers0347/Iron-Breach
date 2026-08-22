#include "IBCarryablePawn.h"
#include "IronBreach.h"
#include "Components/StaticMeshComponent.h"
#include "Infantry/IBCharacter_Infantry.h"

AIBCarryablePawn::AIBCarryablePawn()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
	Mesh->SetCollisionProfileName(TEXT("Pawn")); // interact trace needs to hit this

	InteractPrompt = NSLOCTEXT("IBCarryable", "CarryPrompt", "Carry");
}

void AIBCarryablePawn::Interact_Implementation(AActor* Interactor)
{
	if (AIBCharacter_Infantry* Carrier = Cast<AIBCharacter_Infantry>(Interactor))
	{
		if (Carrier->IsCarrying())
		{
			return; // hands full
		}
		Carrier->BeginCarry(this);
	}
}

FText AIBCarryablePawn::GetInteractPrompt_Implementation() const
{
	return InteractPrompt;
}

void AIBCarryablePawn::PlayVoiceLine(int32 Index)
{
	if (!VoiceLines.IsValidIndex(Index))
	{
		UE_LOG(LogIronBreach, Warning, TEXT("%s: PlayVoiceLine(%d) out of range (%d lines authored)."),
			*GetName(), Index, VoiceLines.Num());
		return;
	}

	OnVoiceLine.Broadcast(VoiceLines[Index]);
}
