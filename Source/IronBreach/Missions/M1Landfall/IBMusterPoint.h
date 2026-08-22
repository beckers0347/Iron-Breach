#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBMusterPoint.generated.h"

class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCivilianMusteredSignature, AActor*, Civilian);

/**
 * A bus/muster trigger for M1 LANDFALL's DREAD and BURST beats (Docs/
 * M1_LANDFALL_Mission_Design.md §7): "extraction counts on-screen, kills
 * don't" -- CIVILIANS EXTRACTED is the burst's only number.
 *
 * Signals-only per the project's collab conventions (see IBMissionDirector's
 * kaiju-tracking pattern): this counts overlaps and broadcasts, it does not
 * reach into a director/HUD directly. AM1LandfallDirector finds every muster
 * point placed in the level at BeginPlay and subscribes -- place as many of
 * these as the evacuation route needs, no wiring required beyond dropping the
 * actor and tagging the civilians "Evacuee".
 *
 * Deliberately does NOT spawn or animate evacuee crowd agents -- that's level/
 * content work (doc §12 calls crowd polish one of M1's biggest content costs).
 * This only counts whatever evacuee actors the level places/scripts, however
 * they get here (nav-move BP, a simple move-to-point script, or a Sequencer walk cycle).
 */
UCLASS()
class IRONBREACH_API AIBMusterPoint : public AActor
{
	GENERATED_BODY()

public:
	AIBMusterPoint();

	UPROPERTY(BlueprintAssignable, Category = "Mission|Landfall")
	FOnCivilianMusteredSignature OnCivilianMustered;

	/** Actor tag an evacuee must carry to count. Keeps this generic -- doesn't
	 *  need an evacuee base class, just a tag any crowd-agent BP can add. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Mission|Landfall")
	FName EvacueeTag = TEXT("Evacuee");

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> TriggerVolume;

private:
	/** Never counts the same evacuee twice, even if their nav path clips the volume repeatedly. */
	UPROPERTY()
	TArray<TObjectPtr<AActor>> Mustered;
};
