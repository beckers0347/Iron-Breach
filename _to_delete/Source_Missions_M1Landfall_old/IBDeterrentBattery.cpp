#include "IBDeterrentBattery.h"
#include "IronBreach.h"
#include "Components/StaticMeshComponent.h"
#include "IBPalawanActor.h"

AIBDeterrentBattery::AIBDeterrentBattery()
{
	PrimaryActorTick.bCanEverTick = true;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));

	InteractPrompt = NSLOCTEXT("IBDeterrent", "Prompt", "Ring it");
}

void AIBDeterrentBattery::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	CooldownRemaining = FMath::Max(CooldownRemaining - DeltaSeconds, 0.0f);
}

void AIBDeterrentBattery::Interact_Implementation(AActor* Interactor)
{
	FireCharge();
}

FText AIBDeterrentBattery::GetInteractPrompt_Implementation() const
{
	if (IsOnCooldown() || (MaxCharges >= 0 && ChargesFired >= MaxCharges))
	{
		return FText::GetEmpty(); // not currently interactable
	}
	return InteractPrompt;
}

void AIBDeterrentBattery::FireCharge()
{
	if (IsOnCooldown() || !Target) { return; }
	if (MaxCharges >= 0 && ChargesFired >= MaxCharges) { return; }

	CooldownRemaining = FireCooldown;
	++ChargesFired;

	Target->ReactToFlinch(TargetSocket); // redirect only -- see class comment

	const int32 Remaining = (MaxCharges < 0) ? -1 : FMath::Max(MaxCharges - ChargesFired, 0);
	OnDeterrentFired.Broadcast(Remaining);

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] deterrent battery fired (%d/%s charges used)"),
		ChargesFired, (MaxCharges < 0) ? TEXT("unlimited") : *FString::FromInt(MaxCharges));
}
