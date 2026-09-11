#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "IBWatchTypes.generated.h"

class UTexture2D;

/**
 * What a pin on the Watch's breach board IS. Colors the pin, words the card.
 *  Operation — a campaign mission (LANDFALL). Sector — an open-world zone under
 *  watch. Range — training. Bastion — the Watch itself (CARROW-1), the return
 *  point. Locked — on the board for the sense of a world, not deployable yet.
 */
UENUM(BlueprintType)
enum class EIBDestinationKind : uint8
{
	Operation,
	Sector,
	Range,
	Bastion,
	Locked
};

/**
 * One deployable place. Data, not code: the built-in list in IBWatchTypes.cpp
 * is the floor; drop a UIBDestinationRegistry at
 * /Game/IronBreach/Watch/DA_Destinations to replace it without a rebuild.
 *
 * The card (UIBWatchScreen) reads it top to bottom: Name / Codename, the recon
 * still, ThreatClass + ThreatLevel (the 5-bar meter), MissionType, Brief (the
 * OBJECTIVE line), Fireteam | MechDeployment. Everything but Id and MapPath is
 * copy Shane can rewrite.
 */
USTRUCT(BlueprintType)
struct IRONBREACH_API FIBDestination
{
	GENERATED_BODY()

	/** Stable key ("carrow_gate"). The board, the RPCs and the map lookup all use it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FName Id;

	/** Which orbital sector the pin belongs to (FIBSector::Id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FName SectorId = FName(TEXT("carrow"));

	/** CARROW GATE GARRISON */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText Name;

	/** Site chip on the card: GATE GARRISON */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText ShortName;

	/** OP. LANDFALL · M1 / PATROL GRID 7 / TRAINING STAND 2 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText Codename;

	/** Threat line on the card: "CLASS A — PALAWAN" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText ThreatClass;

	/** 0 none, 1 Class D, 2 C, 3 B, 4 A, 5 Catastrophe — fills the meter. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination", meta = (ClampMin = 0, ClampMax = 5))
	int32 ThreatLevel = 0;

	/** KAIJU SUPPRESSION · HOLD THE GATE */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText MissionType;

	/** The OBJECTIVE paragraph. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText Brief;

	/** 1–8 OPERATORS */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText Fireteam;

	/** AUTHORIZED · 1 PAIR / NOT REQUIRED / TRAINING FRAME / NOT AUTHORIZED */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FText MechDeployment;

	/** Optional card image (a captured screenshot of the level). Empty = the painted placeholder. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	TSoftObjectPtr<UTexture2D> ReconStill;

	/** Long package path of the map, no options: /Game/LevelPrototyping/CarrowGateGarrison */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FString MapPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	EIBDestinationKind Kind = EIBDestinationKind::Operation;

	/** Where the pin sits on the sector board, 0..1 of the board's width/height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	FVector2D BoardPosition = FVector2D(0.5, 0.5);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	int32 SquadMin = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	int32 SquadMax = 4;

	/** False = pinned but not deployable (Locked kind implies false). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Destination")
	bool bAvailable = true;

	bool IsValid() const { return !Id.IsNone(); }
	bool CanDeploy() const { return IsValid() && bAvailable && Kind != EIBDestinationKind::Locked && !MapPath.IsEmpty(); }
};

/**
 * A region of the world pinned on the orbital view. The pin is snapped onto
 * the nearest coastline of the generated planet at runtime (kaiju come out of
 * the sea), so Latitude/Longitude are a target, not a promise. Only bLive
 * sectors open a breach board — the rest are there for the sense of a world,
 * each with the reason it is closed.
 */
USTRUCT(BlueprintType)
struct IRONBREACH_API FIBSector
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FName Id;

	/** CARROW SECTOR */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FText Name;

	/** AURENTINE EAST COAST */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FText Region;

	/** BREACH ACTIVE · CLASS A */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FText Status;

	/** Card paragraph for a closed sector. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FText Brief;

	/** RELAY DARK — NO LINK TO THE REACH */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FText LockReason;

	/** Degrees, +N / +E. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	float Latitude = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	float Longitude = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FLinearColor Color = FLinearColor(0.25f, 0.75f, 0.85f);

	/** One character drawn inside the diamond: the threat class letter, ? for unknown, X for sealed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	FString Glyph = TEXT("A");

	/** 0 none .. 4 Class A, 5 Catastrophe. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector", meta = (ClampMin = 0, ClampMax = 5))
	int32 ThreatLevel = 0;

	/** Has destinations; opens the breach board. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	bool bLive = false;

	/** Sonar pulse on the pin (active breach somewhere). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	bool bHot = false;

	/** The Bastion's sector: drawn with the home glyph, where the lobby lives. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sector")
	bool bHome = false;

	bool IsValid() const { return !Id.IsNone(); }
};

/** Optional content override for the destination and sector lists. */
UCLASS(BlueprintType)
class IRONBREACH_API UIBDestinationRegistry : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Watch")
	TArray<FIBDestination> Destinations;

	/** Empty = built-in sectors. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Watch")
	TArray<FIBSector> Sectors;
};

namespace IBWatch
{
	/** The list the board draws: registry asset when present, else the built-ins. Cached after first call. */
	IRONBREACH_API const TArray<FIBDestination>& Destinations();

	IRONBREACH_API const FIBDestination* Find(FName Id);

	/** The orbital view's pins. */
	IRONBREACH_API const TArray<FIBSector>& Sectors();

	IRONBREACH_API const FIBSector* FindSector(FName Id);

	/** The sector the lobby lives in (bHome), else the first live one. */
	IRONBREACH_API FName HomeSectorId();

	/** Which destination a loaded map is: matches the map's short name. NAME_None if unknown. */
	IRONBREACH_API FName DestinationForMap(const FString& MapNameOrPath);

	/** The Watch itself — the lobby/menu map. */
	IRONBREACH_API FName WatchId();

	IRONBREACH_API FLinearColor KindColor(EIBDestinationKind Kind);
	IRONBREACH_API FText KindLabel(EIBDestinationKind Kind);

	/** "CLASS A" / "CATASTROPHE" / "NO THREAT" for a 0..5 level. */
	IRONBREACH_API FText ThreatLevelLabel(int32 Level);

	/**
	 * Host confirms -> this long before the squad travels. Not a countdown any
	 * more (Connor, 09-08): it is the length of the drop sequence every screen
	 * plays from the same server timestamp — aim, fall, white-out — so the
	 * travel lands on the black frame. Never shown as a number.
	 */
	constexpr float DeployDropSeconds = 2.4f;
}
