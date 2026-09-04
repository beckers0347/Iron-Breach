#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Classes/IBClassKitTypes.h"
#include "IBClassKitData.generated.h"

/**
 * One combat trade's kit, as an asset designers own. UIBOperativeKitComponent
 * looks up /Game/IronBreach/Classes/DA_Kit_<Trade> for the operative's class
 * and falls back to its built-in defaults when the asset is missing — the
 * game never depends on content to have a kit.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UIBClassKitData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	EIBOperativeClass OperativeClass = EIBOperativeClass::Breaker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ShowOnlyInnerProperties))
	FIBClassKit Kit;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override
	{
		return FPrimaryAssetId(TEXT("IBClassKit"), GetFName());
	}
};
