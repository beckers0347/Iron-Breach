#include "IBKaijuSpawner.h"
#include "IBCharacter_Kaiju.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"

AIBKaijuSpawner::AIBKaijuSpawner()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = false; // Server-only logic; the spawned Kaiju will replicate itself
}

void AIBKaijuSpawner::BeginPlay()
{
	Super::BeginPlay();

	// Rule 1: Clients request, Server decides
	if (!HasAuthority())
	{
		return;
	}

	if (!KaijuClassToSpawn || PossibleSpecies.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("KaijuSpawner %s is missing its Class or Species array."), *GetName());
		return;
	}

	// 1. Filter the possible species by the defined power range
	TArray<UKaijuSpeciesData*> FilteredSpecies;
	for (UKaijuSpeciesData* SpeciesDA : PossibleSpecies)
	{
		if (SpeciesDA)
		{
			// Assumes EKaijuClass is ordered lowest-to-highest (e.g., E=0, A=4)
			if (SpeciesDA->ThreatClass >= MinClass && SpeciesDA->ThreatClass <= MaxClass)
			{
				FilteredSpecies.Add(SpeciesDA);
			}
		}
	}

	if (FilteredSpecies.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("KaijuSpawner %s has no species that fit the Min/Max Class bounds."), *GetName());
		return;
	}

	// 2. Pick a random DA from the valid pool
	const int32 RandomIndex = FMath::RandRange(0, FilteredSpecies.Num() - 1);
	UKaijuSpeciesData* ChosenSpecies = FilteredSpecies[RandomIndex];

	// 3. Deferred Spawn: Create the actor, inject the DA, THEN run its BeginPlay
	FTransform SpawnTransform = GetActorTransform();
	AIBCharacter_Kaiju* SpawnedKaiju = GetWorld()->SpawnActorDeferred<AIBCharacter_Kaiju>(
		KaijuClassToSpawn,
		SpawnTransform,
		nullptr,
		nullptr,
		ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn
	);

	if (SpawnedKaiju)
	{
		// Inject the data asset before the Kaiju wakes up
		SpawnedKaiju->Species = ChosenSpecies;
		
		// Finalize spawning (This triggers the Kaiju's BeginPlay and ApplySpecies)
		SpawnedKaiju->FinishSpawning(SpawnTransform);
	}
}