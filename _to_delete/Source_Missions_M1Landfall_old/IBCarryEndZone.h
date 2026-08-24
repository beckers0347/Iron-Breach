#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBCarryEndZone.generated.h"

class UBoxComponent;
class AIBCharacter_Infantry;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCarryEndedSignature, AActor*, CarriedActor, AIBCharacter_Infantry*, Carrier);

/**
 * Placed at the hospital muster (Docs/M1_LANDFALL_Mission_Design.md §4.4). Any
 * carrying player who enters ends their carry here -- this is the ONLY thing
 * that ends a carry; per the doc "the carry cannot fail and cannot be skipped,"
 * so there is deliberately no player-input release, only reaching this zone.
 *
 * Broadcasts OnCarryEnded rather than calling the mission director directly
 * (same signals-only convention as AIBMusterPoint) -- AM1LandfallDirector
 * subscribes at BeginPlay and fires the naming beat (Bricks: "Ferryman").
 */
UCLASS()
class IRONBREACH_API AIBCarryEndZone : public AActor
{
	GENERATED_BODY()

public:
	AIBCarryEndZone();

	UPROPERTY(BlueprintAssignable, Category = "Mission|Landfall")
	FOnCarryEndedSignature OnCarryEnded;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> TriggerVolume;

private:
	bool bFired = false; // one-shot: the naming beat happens once
};
