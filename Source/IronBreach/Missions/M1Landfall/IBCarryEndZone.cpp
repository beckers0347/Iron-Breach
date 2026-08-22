#include "IBCarryEndZone.h"
#include "IronBreach.h"
#include "Components/BoxComponent.h"
#include "Infantry/IBCharacter_Infantry.h"

AIBCarryEndZone::AIBCarryEndZone()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->SetBoxExtent(FVector(200.0f, 200.0f, 150.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));
}

void AIBCarryEndZone::BeginPlay()
{
	Super::BeginPlay();
	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AIBCarryEndZone::HandleBeginOverlap);
}

void AIBCarryEndZone::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bFired) { return; }

	AIBCharacter_Infantry* Carrier = Cast<AIBCharacter_Infantry>(OtherActor);
	if (!Carrier || !Carrier->IsCarrying()) { return; }

	bFired = true;
	AActor* CarriedActor = Carrier->GetCarriedActor();

	Carrier->EndCarry();
	OnCarryEnded.Broadcast(CarriedActor, Carrier);

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] carry ended at %s"), *GetName());
}
