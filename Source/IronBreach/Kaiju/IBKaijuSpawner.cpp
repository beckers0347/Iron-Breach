#include "IBKaijuSpawner.h"
#include "IBCharacter_Kaiju.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "Components/SphereComponent.h"
#include "Components/SceneComponent.h"
#include "NavigationSystem.h"
#include "TimerManager.h"
#include "GameFramework/PlayerController.h"

AIBKaijuSpawner::AIBKaijuSpawner()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = false;

	SpawnerRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SpawnerRoot"));
	RootComponent = SpawnerRoot;

	SpawnZone = CreateDefaultSubobject<USphereComponent>(TEXT("SpawnZone"));
	SpawnZone->SetupAttachment(RootComponent);
	SpawnZone->InitSphereRadius(3000.0f); // 30 meters
	SpawnZone->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	ProximityZone = CreateDefaultSubobject<USphereComponent>(TEXT("ProximityZone"));
	ProximityZone->SetupAttachment(RootComponent);
	ProximityZone->InitSphereRadius(10000.0f); // 100 meters
	ProximityZone->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AIBKaijuSpawner::BeginPlay()
{
	Super::BeginPlay();

	if (!HasAuthority()) return;

	// Start the looping check every 'SpawnInterval' seconds
	GetWorld()->GetTimerManager().SetTimer(SpawnTimerHandle, this, &AIBKaijuSpawner::ProcessSpawning, SpawnInterval, true);
}

void AIBKaijuSpawner::ProcessSpawning()
{
	// 1. Clean up array in case a Kaiju was destroyed without triggering the delegate
	ActiveKaijus.RemoveAll([](AIBCharacter_Kaiju* K) { return K == nullptr || K->IsActorBeingDestroyed(); });

	// 2. Are we at the max limit?
	if (ActiveKaijus.Num() >= MaxConcurrentKaijus) return;

	// 3. Is a player inside the ProximityZone?
	bool bPlayerInRange = false;
	float ProxRadiusSq = FMath::Square(ProximityZone->GetScaledSphereRadius());
	FVector SpawnerLoc = GetActorLocation();

	// Loop through all connected players (works perfectly for your listen server)
	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		if (APlayerController* PC = It->Get())
		{
			if (APawn* PlayerPawn = PC->GetPawn())
			{
				if (FVector::DistSquared(SpawnerLoc, PlayerPawn->GetActorLocation()) <= ProxRadiusSq)
				{
					bPlayerInRange = true;
					break; // Found one, no need to check others
				}
			}
		}
	}

	if (!bPlayerInRange) return; // Nobody is close enough

	// 4. Player is near, and we have room! Run the spawn logic.
	if (!KaijuClassToSpawn || PossibleSpecies.IsEmpty()) return;

	TArray<UKaijuSpeciesData*> FilteredSpecies;
	for (UKaijuSpeciesData* SpeciesDA : PossibleSpecies)
	{
		if (SpeciesDA && SpeciesDA->ThreatClass >= MinClass && SpeciesDA->ThreatClass <= MaxClass)
		{
			FilteredSpecies.Add(SpeciesDA);
		}
	}

	if (FilteredSpecies.IsEmpty()) return;

	const int32 RandomIndex = FMath::RandRange(0, FilteredSpecies.Num() - 1);
	UKaijuSpeciesData* ChosenSpecies = FilteredSpecies[RandomIndex];

	FVector SpawnLocation = GetActorLocation();
	UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld());
	if (NavSys)
	{
		FNavLocation RandomNavLoc;
		if (NavSys->GetRandomReachablePointInRadius(GetActorLocation(), SpawnZone->GetScaledSphereRadius(), RandomNavLoc))
		{
			SpawnLocation = RandomNavLoc.Location;
		}
	}

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

		// 5. Track the newly spawned Kaiju and listen for its death
		ActiveKaijus.Add(SpawnedKaiju);
		SpawnedKaiju->OnDestroyed.AddDynamic(this, &AIBKaijuSpawner::HandleKaijuDestroyed);
	}
}

void AIBKaijuSpawner::HandleKaijuDestroyed(AActor* DestroyedActor)
{
	AIBCharacter_Kaiju* DeadKaiju = Cast<AIBCharacter_Kaiju>(DestroyedActor);
	if (DeadKaiju)
	{
		ActiveKaijus.Remove(DeadKaiju);
	}
}