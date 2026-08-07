#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Progression/XPTypes.h"
#include "XPTuningData.generated.h"

/**
 * All XP numbers live here -- zero magic constants in code, matching DA_ConcordTuning's
 * convention (Mech/ConcordTuningData.h). Create one DA_XPTuning asset and assign it to
 * UIBXPSubsystem::SetTuning at startup (e.g. from GameMode::InitGame or a BP call).
 *
 * Current design scope: XP is earned from damage dealt and kills only. Raid-phase and
 * clean-play bonuses were considered and deferred -- IBXPSubsystem::AwardPilotXP /
 * AwardCrewXP are ready for them if that changes, no rework needed here.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UXPTuningData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	// ---- Earn rates: damage dealt ----
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Damage", meta = (ClampMin = "0.0"))
	float PilotXPPerDamage = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Damage", meta = (ClampMin = "0.0"))
	float CrewXPPerDamage = 0.5f;

	/** Kaiju armor is a very large HP pool that bypasses UHealthComponent entirely (it's
	 *  soaked directly on AIBCharacter_Kaiju before health damage even starts) -- weight it
	 *  down relative to normal damage so chipping a raid boss's armor doesn't dwarf every
	 *  other kill in the game. Applies to both tracks. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Damage", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float ArmorPhaseDamageWeight = 0.25f;

	// ---- Earn rates: kills ----
		// Calculates a kill bonus proportional to the victim's total durability (MaxHealth + MaxArmor).
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Kills", meta = (ClampMin = "0.0"))
	float PilotKillBonusMultiplier = 0.1f; // 10% of total HP+Armor awarded on kill

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Kills", meta = (ClampMin = "0.0"))
	float CrewKillBonusMultiplier = 0.15f;

	/** One-time milestone bonus for the hit that breaks a kaiju's armor. Crew track only --
	 *  breaking armor is squarely a mech job. An infantry chip-shot that happens to land the
	 *  break still earns its (weighted) damage XP on the pilot track, just not this bonus. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Earn Rates|Kills", meta = (ClampMin = "0"))
	int32 CrewXPPerArmorBreak = 150;

	// ---- Level curves: TotalXP required to REACH level N (index 0 = level 1's floor, always 0) ----
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Levels")
	TArray<int32> PilotLevelThresholds = { 0, 100, 250, 500, 900, 1500, 2400, 3600 };

	/** Crew levels a little steeper than pilot -- two people's damage feeds one meter. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Levels")
	TArray<int32> CrewLevelThresholds = { 0, 150, 375, 750, 1350, 2250, 3500, 5200 };

	// ---- Unlocks (sidegrades only -- see class comment) ----
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Unlocks")
	TArray<FXPLevelUnlock> PilotUnlocks;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Unlocks")
	TArray<FXPLevelUnlock> CrewUnlocks;

	/** Highest level whose threshold TotalXP has reached, against a threshold table built like
	 *  PilotLevelThresholds/CrewLevelThresholds. 1-based; never returns below level 1. */
	static int32 LevelForXP(int32 TotalXP, const TArray<int32>& Thresholds);
};
