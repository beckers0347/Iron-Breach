#pragma once

#include "CoreMinimal.h"
#include "XPTypes.generated.h"

class UIBItemDefinition;

/**
 * Which XP ledger an event feeds. Deliberately separate from CONCORD (the sync meter is
 * per-encounter and never persisted, spec §9) -- XP is the opposite: cross-encounter,
 * cross-session, saved to disk.
 *
 *   Pilot -- individual. Earned fighting on foot as AIBCharacter_Infantry.
 *   Crew  -- the pairing. Earned fighting from the mech (hull or gunner seat), shared by
 *            whichever two humans are currently crewing it together.
 */
UENUM(BlueprintType)
enum class EXPTrack : uint8
{
	Pilot UMETA(DisplayName = "Pilot (Individual)"),
	Crew  UMETA(DisplayName = "Crew (Pair)")
};

/** Persisted XP state for one pilot or one crew pairing. */
USTRUCT()
struct FXPRecord
{
	GENERATED_BODY()

	UPROPERTY()
	int32 TotalXP = 0;

	UPROPERTY()
	int32 Level = 1;
};

/**
 * One level's unlock entry. Unlocks are sidegrades -- alternate loadout options, never a
 * stat upgrade of an existing weapon (progression design decision: leveling adds choice,
 * not power, so a raid's difficulty doesn't shift under a higher-level crew).
 *
 * Unlocks reference UIBItemDefinition (not the raw weapon data assets directly) -- the same
 * item-level abstraction the loot/inventory/rack systems already key off of, so a future
 * loadout system can grant these the same way GrantItem does elsewhere.
 */
USTRUCT(BlueprintType)
struct FXPLevelUnlock
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "XP", meta = (ClampMin = "1"))
	int32 Level = 1;

	/** Player-facing label for the unlock toast/menu entry. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "XP")
	FText UnlockLabel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "XP")
	TArray<TObjectPtr<UIBItemDefinition>> UnlockedWeapons;
};
