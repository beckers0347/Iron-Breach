#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ConcordTuningData.generated.h"

/**
 * All CONCORD numbers live here — zero magic constants in code, per
 * Docs/SPEC-sync-failure-drama.md §14. Create one DA_ConcordTuning asset
 * (right-click Content -> Miscellaneous -> Data Asset -> Concord Tuning Data)
 * and assign it to the ConcordComponent on BP_Mech.
 *
 * Loss magnitudes are the spec §2 provisionals — run the BALANCE SIM deck op
 * before locking them.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UConcordTuningData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	// ---- Tier thresholds (spec §1: T0 DESYNC / T1 LINKED / T2 COHERENT / T3 HARMONIZED / T4 OVERDRIVE) ----
	/** Meter value where T1 begins. Below this is T0 (desync). Also the post-ritual restore floor. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tiers", meta = (ClampMin = "1", ClampMax = "100"))
	float Tier1Threshold = 20.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tiers", meta = (ClampMin = "1", ClampMax = "100"))
	float Tier2Threshold = 45.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tiers", meta = (ClampMin = "1", ClampMax = "100"))
	float Tier3Threshold = 70.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tiers", meta = (ClampMin = "1", ClampMax = "100"))
	float Tier4Threshold = 95.0f;

	// ---- Gains ----
	/** Sync gained per coordinated action at baseline. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gains", meta = (ClampMin = "0.0"))
	float BaseGain = 4.0f;

	/** Post-ritual Adrenaline Window: gain multiplier for the next AdrenalineActions coordinated actions. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gains", meta = (ClampMin = "1.0"))
	float AdrenalineMultiplier = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gains", meta = (ClampMin = "0"))
	int32 AdrenalineActions = 5;

	/** Sync Debt after recovery: gain multiplier until DebtActions coordinated actions land.
	 *  Adrenaline overrides Debt while it lasts (spec §4.4). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gains", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float DebtMultiplier = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Gains", meta = (ClampMin = "0"))
	int32 DebtActions = 3;

	// ---- Loss magnitudes (spec §2 taxonomy) ----
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_MissedResponse = 8.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_CrossedInputs = 4.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_UnshieldedCrit = 10.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_PilotDowned = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_SoloChain = 3.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0"))
	float Loss_KaijuInterference = 10.0f;

	/** Last Link (spec §4.1): the one free save dampens the NEXT loss event by this factor. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Losses", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LastLinkDampen = 0.5f;

	// ---- Ritual ----
	/** Steps dealt for a normal Reconnection Ritual. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ritual", meta = (ClampMin = "1", ClampMax = "8"))
	int32 RitualStepsNormal = 3;

	/** Steps dealt after a Sync Snap (falling from Overdrive, spec §4.2). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ritual", meta = (ClampMin = "1", ClampMax = "8"))
	int32 RitualStepsSnap = 4;

	// ---- Desync control profile (spec §3.2, applied by the mech) ----
	/** Hull walk-speed factor while desynced. Weak, not helpless — retreat stays viable. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Desync", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float DesyncMoveSpeedFactor = 0.6f;

	/** Heavy weapons safety-lock while desynced (gunner keeps secondaries only). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Desync")
	bool bDesyncLocksHeavyWeapons = true;
};
