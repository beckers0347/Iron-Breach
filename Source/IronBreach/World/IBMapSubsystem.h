#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "World/IBMapTypes.h"
#include "IBMapSubsystem.generated.h"

class UIBMapPOIComponent;
class AIBMapZoneInfo;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMapDataChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMapPOIActivated, UIBMapPOIComponent*, POI);

/**
 * Per-world registry gluing the map layer together: zone data (from the placed
 * AIBMapZoneInfo) + every live POI component. The map screen reads it; POIs
 * write themselves into it; nobody references anybody.
 *
 * OnPOIActivated is the outbound signal for "the player committed to this pin"
 * (the Deploy button). Fast travel, mission launch, and the event director each
 * just listen for their POI types — same delivery contract as ZoneConfirmed,
 * and it keeps this subsystem authority-free (deciding what activation MEANS
 * is server logic that lives with those systems, not with the map).
 */
UCLASS()
class IRONBREACH_API UIBMapSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Map")
	FOnMapDataChanged OnMapDataChanged;

	UPROPERTY(BlueprintAssignable, Category = "Map")
	FOnMapPOIActivated OnPOIActivated;

	void RegisterPOI(UIBMapPOIComponent* POI);
	void UnregisterPOI(UIBMapPOIComponent* POI);
	void RegisterZoneInfo(AIBMapZoneInfo* ZoneInfo);
	void NotifyMapDataChanged();

	/** Live, discovered pins (weak registry is compacted on read). */
	UFUNCTION(BlueprintPure, Category = "Map")
	TArray<UIBMapPOIComponent*> GetVisiblePOIs() const;

	UFUNCTION(BlueprintPure, Category = "Map")
	UIBMapZoneData* GetZoneData() const;

	UFUNCTION(BlueprintPure, Category = "Map")
	UIBMapPOIComponent* FindPOIById(FName POIId) const;

	/** The map screen's Deploy path. Broadcasts OnPOIActivated. */
	UFUNCTION(BlueprintCallable, Category = "Map")
	void RequestPOIActivation(UIBMapPOIComponent* POI);

private:
	/** Weak: World Partition streams cells (and their actors) in and out under
	 *  us; a stale strong ref here would fight garbage collection. */
	TArray<TWeakObjectPtr<UIBMapPOIComponent>> RegisteredPOIs;

	TWeakObjectPtr<AIBMapZoneInfo> ActiveZoneInfo;
};
