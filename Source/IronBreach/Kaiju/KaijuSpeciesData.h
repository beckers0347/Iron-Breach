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

	/** Number of destructible organ weak points (raid phase 2). Informational /
	 *  spawn-tool hint — the organs that actually exist are the
	 *  UIBKaijuOrganComponent spheres placed on the kaiju BP. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "1", ClampMax = "12"))
	int32 OrganCount = 3;

	/** Health of each organ (an organ can override this on its component). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fight|OrganPhase", meta = (ClampMin = "1"))
	float OrganHealth = 4000.0f;

	/** Body hits during the organ phase are dampened by this — the fight says
	 *  "shoot the glowing bits", the multiplier makes it true without making
	 *  body shots worthless. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fight|OrganPhase", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HardenedBodyMultiplier = 0.25f;

	/** Each organ destroyed instantly chunks this fraction of MaxHealth off the
	 *  boss — the visible reward beat for popping a sac. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fight|OrganPhase", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float OrganBreakDamagePercent = 0.08f;

	/** All organs down -> Exposed: every hit is multiplied by this until death.
	 *  The execute window where the mech earns its finisher. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fight|Exposed", meta = (ClampMin = "1.0"))
	float ExposedDamageMultiplier = 2.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Stats", meta = (ClampMin = "0"))
	float WalkSpeed = 150.0f;

	/** Final creature mesh (leave empty while using the scaled placeholder). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
	TObjectPtr<USkeletalMesh> Mesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
	TSubclassOf<UAnimInstance> AnimClass;

	/** Height of the source mesh as authored, in metres. Manny/Quinn = 1.8.
	 *  Custom creature meshes are usually authored at their real size � set this
	 *  to whatever the mesh actually measures so HeightMeters means what it says. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals", meta = (ClampMin = "0.1"))
	float AuthoredHeightMeters = 2.0f;

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	float GetScaleFactor() const { return HeightMeters / FMath::Max(AuthoredHeightMeters, 0.1f); }
};
