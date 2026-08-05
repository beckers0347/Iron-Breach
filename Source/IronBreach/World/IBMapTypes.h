#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "IBMapTypes.generated.h"

class UTexture2D;

/** What a map pin IS — drives icon fallback + Shane's per-type styling.
 *  KaijuAlert is reserved for the public-event director's zone-wide announce
 *  (roadmap §3): when a breach opens, the director flips a POI to this type
 *  and the whole map grammar already knows how to scream about it. */
UENUM(BlueprintType)
enum class EIBMapPOIType : uint8
{
	Mission,
	Patrol,
	PublicEvent  UMETA(DisplayName = "Public Event"),
	Undercroft   UMETA(DisplayName = "Undercroft (Mini-Dungeon)"),
	Vendor,
	FastTravel   UMETA(DisplayName = "Fast Travel"),
	KaijuAlert   UMETA(DisplayName = "Kaiju Alert"),
	Custom
};

/**
 * DA_Map_* — one per zone: the top-down map image plus the world rectangle it
 * covers, which is everything needed to project actor positions onto the
 * screen. Capture recipe for the texture is in MENUS_UI_WIRING.md §7 (a
 * BugItGo top-down ortho shot of Lvl_Plains works fine as a first pass).
 */
UCLASS(BlueprintType)
class IRONBREACH_API UIBMapZoneData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	/** "Carrow Exclusion Zone" — the map screen's header. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	FText ZoneName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	TSoftObjectPtr<UTexture2D> MapTexture;

	/** World-space XY corners the texture spans (cm). For a 2 km zone centered
	 *  on origin: Min (-100000,-100000), Max (100000,100000). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	FVector2D WorldMin = FVector2D(-100000.0f, -100000.0f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	FVector2D WorldMax = FVector2D(100000.0f, 100000.0f);

	/** Capture-orientation fixups. Defaults match a straight-down (-90 pitch)
	 *  screenshot with world +X pointing up the image: U from world Y, V from
	 *  world X inverted. If pins land mirrored, flip these — no math required. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	bool bFlipU = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Zone")
	bool bFlipV = true;

	/** World position → 0..1 map UV. Positions outside the rect clamp to the edge
	 *  (pins pinned to the border beat pins in the void). */
	FVector2D WorldToMapUV(const FVector& WorldLocation) const
	{
		const FVector2D Size = WorldMax - WorldMin;
		if (Size.X <= 0.0f || Size.Y <= 0.0f) { return FVector2D(0.5f, 0.5f); }

		float U = (WorldLocation.Y - WorldMin.Y) / Size.Y;
		float V = (WorldLocation.X - WorldMin.X) / Size.X;
		if (bFlipU) { U = 1.0f - U; }
		if (bFlipV) { V = 1.0f - V; }
		return FVector2D(FMath::Clamp(U, 0.0f, 1.0f), FMath::Clamp(V, 0.0f, 1.0f));
	}
};
