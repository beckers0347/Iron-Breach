#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/IBMapTypes.h"
#include "IBMapPOIComponent.generated.h"

class UTexture2D;

/**
 * Drop this on any actor and it becomes a pin on the zone map — vendors,
 * fast-travel pads, mission givers, public-event anchors. Self-registers with
 * UIBMapSubsystem on BeginPlay, deregisters on EndPlay; the map screen never
 * knows or cares what the actor is (signals-only, ZoneConfirmed pattern).
 *
 * Shane: this is level-side content — add it to your placed BPs freely. The
 * map redraws itself whenever pins appear/vanish.
 */
UCLASS(ClassGroup = (IronBreach), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UIBMapPOIComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	/** Optional stable id for quest/director systems to find this pin by name. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "POI")
	FName POIId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "POI")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "POI")
	EIBMapPOIType POIType = EIBMapPOIType::Mission;

	/** Overrides the marker widget's per-type default icon when set. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "POI")
	TSoftObjectPtr<UTexture2D> IconOverride;

	/** Hidden pins support fog-of-war style reveals; call SetDiscovered from
	 *  quest/exploration logic. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "POI")
	bool bStartDiscovered = true;

	UFUNCTION(BlueprintCallable, Category = "POI")
	void SetDiscovered(bool bNewDiscovered);

	UFUNCTION(BlueprintPure, Category = "POI")
	bool IsDiscovered() const { return bDiscovered; }

	UFUNCTION(BlueprintPure, Category = "POI")
	FVector GetPOIWorldLocation() const;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	bool bDiscovered = true;
};
