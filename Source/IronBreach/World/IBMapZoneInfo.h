#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "IBMapZoneInfo.generated.h"

class UIBMapZoneData;

/**
 * Place exactly one per zone level (Shane — it's level content). Points the
 * world at its DA_Map_* asset; the map subsystem picks it up on BeginPlay.
 * Plays perfectly with One File Per Actor — it's just another tiny actor file.
 */
UCLASS()
class IRONBREACH_API AIBMapZoneInfo : public AInfo
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Map")
	TObjectPtr<UIBMapZoneData> ZoneData;

protected:
	virtual void BeginPlay() override;
};
