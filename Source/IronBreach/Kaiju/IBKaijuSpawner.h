#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "KaijuSpeciesData.h"
#include "IBKaijuSpawner.generated.h"

class AIBCharacter_Kaiju;
class USphereComponent;
class USceneComponent;

UCLASS()
class IRONBREACH_API AIBKaijuSpawner : public AActor
{
	GENERATED_BODY()

public:
	AIBKaijuSpawner();

protected:
	virtual void BeginPlay() override;

	// The looping function that checks players and decides to spawn
	void ProcessSpawning();

	// Listens for when a Kaiju dies so we can spawn a replacement
	UFUNCTION()
	void HandleKaijuDestroyed(AActor* DestroyedActor);

public:
	// The root so we can scale the two spheres independently
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spawning")
	TObjectPtr<USceneComponent> SpawnerRoot;

	// The area where Kaijus physically appear
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spawning")
	TObjectPtr<USphereComponent> SpawnZone;

	// The area that detects players. Usually much larger than the SpawnZone.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Spawning")
	TObjectPtr<USphereComponent> ProximityZone;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Config")
	TSubclassOf<AIBCharacter_Kaiju> KaijuClassToSpawn;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Config")
	TArray<TObjectPtr<UKaijuSpeciesData>> PossibleSpecies;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Config")
	EKaijuClass MinClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Config")
	EKaijuClass MaxClass;

	// How many Kaijus this spawner is allowed to keep alive at one time
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Rules")
	int32 MaxConcurrentKaijus = 1;

	// How often (in seconds) the spawner checks to see if it should spawn a Kaiju
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning|Rules")
	float SpawnInterval = 5.0f;

private:
	// Tracks currently living Kaijus spawned by this spawner
	UPROPERTY()
	TArray<AIBCharacter_Kaiju*> ActiveKaijus;

	FTimerHandle SpawnTimerHandle;
};