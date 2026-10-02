#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "IBMissionSubsystem.generated.h"

class AIBMissionDirector;

/**
 * Ensures gameplay worlds have a mission director without anyone placing one:
 * on server world-begin, if the world contains kaiju (or a kaiju spawner) and
 * no director, spawn one. Menu/title worlds have neither, so they stay clean —
 * no phantom "SWEEP THE ZONE" banner over the main menu.
 */
UCLASS()
class IRONBREACH_API UIBMissionSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	/** The world's director, if any (placed or auto-spawned). On clients the auto-spawned
	 *  director arrives by replication some time after world begin, so this resolves lazily:
	 *  the first call after it lands finds and caches it. Null until then (and in menu worlds). */
	UFUNCTION(BlueprintPure, Category = "Mission")
	AIBMissionDirector* GetDirector() const;

private:
	/** Cache — filled on the server at spawn, on clients by the first successful lookup. */
	mutable TWeakObjectPtr<AIBMissionDirector> Director;
};
