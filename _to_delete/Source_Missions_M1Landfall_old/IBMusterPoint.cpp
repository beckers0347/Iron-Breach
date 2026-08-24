#include "IBMusterPoint.h"
#include "IronBreach.h"
#include "Components/BoxComponent.h"

AIBMusterPoint::AIBMusterPoint()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->SetBoxExtent(FVector(200.0f, 200.0f, 100.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));
}

void AIBMusterPoint::BeginPlay()
{
	Super::BeginPlay();
	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AIBMusterPoint::HandleBeginOverlap);
}

void AIBMusterPoint::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || !OtherActor->ActorHasTag(EvacueeTag) || Mustered.Contains(OtherActor))
	{
		return;
	}

	Mustered.Add(OtherActor);
	OnCivilianMustered.Broadcast(OtherActor);

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] %s mustered at %s (%d total here)"),
		*OtherActor->GetName(), *GetName(), Mustered.Num());
}
