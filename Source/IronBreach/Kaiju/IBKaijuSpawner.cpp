#include "IBKaijuSpawner.h"
#include "IBCharacter_Kaiju.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "Components/SphereComponent.h"
#include "NavigationSystem.h" // Required for NavMesh queries

AIBKaijuSpawner::AIBKaijuSpawner()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = false;

	// Create the Sphere Component to define the zone
	SpawnZone = CreateDefaultSubobject<USphereComponent>(TEXT("SpawnZone"));
	RootComponent = SpawnZone;

	// Default to a 50m radius zone (5000 units). You can scale this in the editor.
	SpawnZone->InitSphereRadius(5000.0f);
	SpawnZone->SetCollisionEnabled(ECollisionEnabled::NoCollision); // It's just for math/visuals
}

void AIBKaijuSpawner::BeginPlay()
{
	Super::BeginPlay();

	if (!HasAuthority()) return;

	if (!KaijuClassToSpawn || PossibleSpecies.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("KaijuSpawner %s is missing its Class or Species array."), *GetName());
		return;
	}

	// 1. Filter the possible species by the defined power range
	TArray<UKaijuSpeciesData*> FilteredSpecies;
	for (UKaijuSpeciesData* SpeciesDA : PossibleSpecies)
	{
		if (SpeciesDA && SpeciesDA->ThreatClass >= MinClass && SpeciesDA->ThreatClass <= MaxClass)
		{
			FilteredSpecies.Add(SpeciesDA);
		}
	}

	if (FilteredSpecies.IsEmpty()) return;

	// 2. Pick a random DA from the valid pool
	const int32 RandomIndex = FMath::RandRange(0, FilteredSpecies.Num() - 1);
	UKaijuSpeciesData* ChosenSpecies = FilteredSpecies[RandomIndex];

	// 3. Find a random valid point on the NavMesh inside the sphere
	FVector SpawnLocation = GetActorLocation(); // Fallback to center
	UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld());

	if (NavSys)
	{
		FNavLocation RandomNavLoc;
		// Ask the NavMesh for a safe spot within the sphere's radius
		if (NavSys->GetRandomReachablePointInRadius(GetActorLocation(), SpawnZone->GetScaledSphereRadius(), RandomNavLoc))
		{
			SpawnLocation = RandomNavLoc.Location;
		}
	}

	// 4. Deferred Spawn
	FTransform SpawnTransform(GetActorRotation(), SpawnLocation);
	AIBCharacter_Kaiju* SpawnedKaiju = GetWorld()->SpawnActorDeferred<AIBCharacter_Kaiju>(
		KaijuClassToSpawn,
		SpawnTransform,
		nullptr,
		nullptr,
		ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn
	);

	if (SpawnedKaiju)
	{
		SpawnedKaiju->Species = ChosenSpecies;
		SpawnedKaiju->FinishSpawning(SpawnTransform);
	}
}