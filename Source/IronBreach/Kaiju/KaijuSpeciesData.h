#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "KaijuSpeciesData.generated.h"

class UTexture2D;
class USkeletalMesh;
class UAnimInstance;

/** Kaiju Threat Classification System (Defense Force Field Guide 7.1) */
UENUM(BlueprintType)
enum class EKaijuClass : uint8
{
	ClassD		UMETA(DisplayName = "Class D - Minor Threat (20-40m, Swarm/Pack)"),
	ClassC		UMETA(DisplayName = "Class C - Elevated Threat (40-80m, Territorial)"),
	ClassB		UMETA(DisplayName = "Class B - High Threat (80-120m, Aggressive)"),
	ClassA		UMETA(DisplayName = "Class A - Extreme Threat (120-200m, Highly Intelligent)"),
	Catastrophe	UMETA(DisplayName = "Catastrophe - Existential Threat (200m+, Apocalyptic)")
};

/**
 * One kaiju species definition. Create one data asset per species (DA_Kaiju_<Name>)
 * and feed it to AIBCharacter_Kaiju. Tuned around the 5-phase raid design:
 * ArmorBreak -> OrganDisable -> MechDeploy -> TheClimb -> FinalSync.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UKaijuSpeciesData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FName SpeciesName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity", meta = (MultiLine = "true"))
	FText FieldGuideEntry;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	EKaijuClass ThreatClass = EKaijuClass::ClassD;

	/** Reference art for modelers / UI codex. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	TObjectPtr<UTexture2D> ConceptArt;

	/** Height in meters; drives world scale of the placeholder/final mesh. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "5", ClampMax = "500"))
	float HeightMeters = 30.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "1"))
	float MaxHealth = 50000.0f;

	/** Outer armor pool that must break before organs are exposed (raid phase 1). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "0"))
	float ArmorHealth = 20000.0f;

	/** Number of destructible organ weak points (raid phase 2). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "1", ClampMax = "12"))
	int32 OrganCount = 3;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "0"))
	float WalkSpeed = 150.0f;

	/** Final creature mesh (leave empty while using the scaled placeholder). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
	TObjectPtr<USkeletalMesh> Mesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
	TSubclassOf<UAnimInstance> AnimClass;

	/** World-scale multiplier assuming a ~1.8m tall base skeleton. */
	UFUNCTION(BlueprintPure, Category = "Kaiju")
	float GetScaleFactor() const { return HeightMeters / 1.8f; }
};
