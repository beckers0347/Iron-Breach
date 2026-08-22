#include "IBPalawanActor.h"
#include "IronBreach.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SplineComponent.h"

AIBPalawanActor::AIBPalawanActor()
{
	PrimaryActorTick.bCanEverTick = true;

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	SetRootComponent(BodyMesh);
	BodyMesh->SetCollisionProfileName(TEXT("BlockAll")); // "collision that world-destruction reacts to" (doc §5)

	LocomotionSpline = CreateDefaultSubobject<USplineComponent>(TEXT("LocomotionSpline"));
	LocomotionSpline->SetupAttachment(RootComponent);
}

void AIBPalawanActor::BeginPlay()
{
	Super::BeginPlay();
	SetActorTickEnabled(false); // idle until BeginLocomotion (the eruption trigger)
}

void AIBPalawanActor::BeginLocomotion()
{
	if (bIsMoving || bIsCalcified) { return; }
	bIsMoving = true;
	SetActorTickEnabled(true);
}

void AIBPalawanActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bIsMoving || bIsCalcified || !LocomotionSpline) { return; }

	const float SplineLength = LocomotionSpline->GetSplineLength();
	if (SplineLength <= 0.0f) { return; }

	DistanceAlongSpline = FMath::Min(DistanceAlongSpline + TraverseSpeed * DeltaSeconds, SplineLength);

	const FVector NewLocation = LocomotionSpline->GetLocationAtDistanceAlongSpline(DistanceAlongSpline, ESplineCoordinateSpace::World);
	const FRotator NewRotation = LocomotionSpline->GetRotationAtDistanceAlongSpline(DistanceAlongSpline, ESplineCoordinateSpace::World);
	SetActorLocationAndRotation(NewLocation, NewRotation);

	if (DistanceAlongSpline >= SplineLength)
	{
		bIsMoving = false;
		SetActorTickEnabled(false);
	}
}

void AIBPalawanActor::ReactToFlinch(FName HitSocket)
{
	// Redirect only -- LOCKED (§4.3): no health, no damage, this never touches
	// locomotion state. Cosmetic reaction is entirely BP_OnFlinch's job.
	OnFlinch.Broadcast(HitSocket);
	BP_OnFlinch(HitSocket);

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] PALAWAN flinch @ %s"), *HitSocket.ToString());
}

void AIBPalawanActor::BeginCalcify()
{
	if (bIsCalcified) { return; }

	bIsCalcified = true;
	bIsMoving = false;
	SetActorTickEnabled(false);

	OnCalcifyBegin.Broadcast();
	BP_OnCalcifyBegin();

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] PALAWAN calcifying, un-engaged."));
}
