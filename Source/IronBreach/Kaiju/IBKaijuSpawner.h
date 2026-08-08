#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "KaijuSpeciesData.h" 
#include "IBKaijuSpawner.generated.h"

class AIBCharacter_Kaiju;

UCLASS()
class IRONBREACH_API AIBKaijuSpawner : public AActor
{
	GENERATED_BODY()
	
public:	
	AIBKaijuSpawner();

protected:
	virtual void BeginPlay() override;

public:
    // The base Kaiju class to spawn (e.g., BP_Kaiju)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning")
	TSubclassOf<AIBCharacter_Kaiju> KaijuClassToSpawn;

    // The pool of possible DAs for this region/spawner
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning")
	TArray<TObjectPtr<UKaijuSpeciesData>> PossibleSpecies;

    // Minimum power level allowed to spawn here
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning")
	EKaijuClass MinClass;

    // Maximum power level allowed to spawn here
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawning")
	EKaijuClass MaxClass;
};