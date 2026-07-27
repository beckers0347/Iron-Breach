#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ConcordComponent.generated.h"

class UConcordTuningData;

/**
 * Why sync dropped. Every loss is an event with a reason, never a silent drain
 * (spec §2). Reason strings shown to players name the EVENT, never the seat —
 * blame masking is a mechanic (spec §5.4).
 */
UENUM(BlueprintType)
enum class EConcordLossReason : uint8
{
	MissedResponse    UMETA(DisplayName = "Response Window Lost"),
	CrossedInputs     UMETA(DisplayName = "Inputs Crossed"),
	UnshieldedCrit    UMETA(DisplayName = "Unshielded Critical"),
	PilotDowned       UMETA(DisplayName = "Pilot Down"),
	SoloChain         UMETA(DisplayName = "Link Strain"),
	KaijuInterference UMETA(DisplayName = "Kaiju Interference")
};

/** Reconnection Ritual step verbs (spec §3.3). Dealt as a pattern; BothConfirm needs both seats. */
UENUM(BlueprintType)
enum class EConcordRitualStep : uint8
{
	NavBrace    UMETA(DisplayName = "NAV: Brace"),
	GunVent     UMETA(DisplayName = "GUN: Vent"),
	BothConfirm UMETA(DisplayName = "BOTH: Confirm")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnConcordSyncChanged, float, NewSync, float, Delta);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnConcordTierChanged, int32, NewTier, int32, OldTier);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnConcordDesyncStarted, EConcordLossReason, Reason, bool, bWasSyncSnap);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnConcordDesyncEnded);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnConcordLastLink);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnConcordRitualAdvanced, int32, StepIndex, EConcordRitualStep, ExpectedStep);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnConcordRitualMissed);

/**
 * CONCORD — the clasp. Server-side sync meter between the two Caryatid pilots.
 * UE port of the drama spec (Docs/SPEC-sync-failure-drama.md) per the Caryatid
 * architecture doc §2/§6: the meter is plain C++ (event-driven, no timers);
 * GAS later mirrors the value into an Attribute for effects/UI — meter logic
 * owns truth, GAS distributes consequences.
 *
 * Lives on the hull (AIBMech_Base creates it). ALL mutation is server-side;
 * values replicate with RepNotify so both cockpit HUDs (and the drama) work on
 * every machine. Route player inputs to it through the hull/seat RPCs — never
 * call the Register* functions from client code directly.
 *
 * Implemented from the spec: tier bands, loss taxonomy, T0 loss-ignore guard,
 * floor protection for ambient losses, Last Link (once per encounter), Sync
 * Snap (falling from Overdrive -> 4-step ritual), Reconnection Ritual with
 * seeded pattern + re-roll on miss, Adrenaline Window and Sync Debt.
 * Not yet: GAS mirroring, VO/audio hooks beyond the delegates, kaiju Neural
 * Howl emitter (kaiju side calls RegisterLoss(KaijuInterference)).
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UConcordComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UConcordComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** All numbers. Assign DA_ConcordTuning on the component in BP_Mech. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Concord")
	TObjectPtr<UConcordTuningData> Tuning;

	// ---- Server-side API (no-ops off-authority) ----

	/** A coordinated action landed (call answered, covered shot, synced dodge...). Applies
	 *  Adrenaline/Debt modifiers. The ONLY way sync goes up. */
	UFUNCTION(BlueprintCallable, Category = "Concord")
	void RegisterCoordinatedAction();

	/** A loss event with a reason. Applies floor protection, T0 guard, Last Link and
	 *  Sync Snap rules. */
	UFUNCTION(BlueprintCallable, Category = "Concord")
	void RegisterLoss(EConcordLossReason Reason);

	/** Ritual input from a seat. bFromDriver identifies the seat, Step is the verb the
	 *  player performed. Wrong verb (or wrong seat for the step) re-rolls the pattern. */
	UFUNCTION(BlueprintCallable, Category = "Concord")
	void RegisterRitualInput(bool bFromDriver, EConcordRitualStep Step);

	/** New encounter: re-arms Last Link, clears Adrenaline/Debt, restores the meter to the
	 *  T1 floor. Sync is per-encounter, never persisted (spec §9). */
	UFUNCTION(BlueprintCallable, Category = "Concord")
	void ResetEncounter();

	// ---- Reads (valid on every machine) ----

	UFUNCTION(BlueprintPure, Category = "Concord")
	float GetSync() const { return Sync; }

	/** 0 = DESYNC .. 4 = OVERDRIVE. */
	UFUNCTION(BlueprintPure, Category = "Concord")
	int32 GetTier() const { return CurrentTier; }

	UFUNCTION(BlueprintPure, Category = "Concord")
	bool IsDesynced() const { return bDesynced; }

	/** Heavy weapons safety-locked? (Desynced + tuning flag.) The mech checks this before firing. */
	UFUNCTION(BlueprintPure, Category = "Concord")
	bool AreHeavyWeaponsLocked() const;

	/** Hull walk-speed factor for the current state (1 when synced). */
	UFUNCTION(BlueprintPure, Category = "Concord")
	float GetMoveSpeedFactor() const;

	/** The dealt ritual pattern (empty when not desynced). Index RitualIndex is the live step. */
	UFUNCTION(BlueprintPure, Category = "Concord")
	const TArray<EConcordRitualStep>& GetRitualPattern() const { return RitualPattern; }

	UFUNCTION(BlueprintPure, Category = "Concord")
	int32 GetRitualIndex() const { return RitualIndex; }

	// ---- Events (fire on server AND, via RepNotify, on clients — bind HUD/audio to these) ----

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordSyncChanged OnSyncChanged;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordTierChanged OnTierChanged;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordDesyncStarted OnDesyncStarted;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordDesyncEnded OnDesyncEnded;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordLastLink OnLastLink;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordRitualAdvanced OnRitualAdvanced;

	UPROPERTY(BlueprintAssignable, Category = "Concord|Events")
	FOnConcordRitualMissed OnRitualMissed;

protected:
	virtual void BeginPlay() override;

private:
	// ---- Replicated state ----
	UPROPERTY(ReplicatedUsing = OnRep_Sync)
	float Sync = 50.0f;

	UPROPERTY(ReplicatedUsing = OnRep_Tier)
	int32 CurrentTier = 2;

	UPROPERTY(ReplicatedUsing = OnRep_Desynced)
	bool bDesynced = false;

	UPROPERTY(Replicated)
	bool bLastDesyncWasSnap = false;

	UPROPERTY(Replicated)
	EConcordLossReason LastLossReason = EConcordLossReason::MissedResponse;

	UPROPERTY(ReplicatedUsing = OnRep_Ritual)
	TArray<EConcordRitualStep> RitualPattern;

	UPROPERTY(ReplicatedUsing = OnRep_Ritual)
	int32 RitualIndex = 0;

	// ---- Server-only state ----
	bool bLastLinkAvailable = true;   // once per encounter (spec §4.1)
	bool bNextLossDampened = false;   // armed by Last Link
	int32 AdrenalineRemaining = 0;    // actions left at boosted gain
	int32 DebtRemaining = 0;          // actions left at halved gain
	bool bRitualNavConfirmed = false; // BothConfirm needs both seats
	bool bRitualGunConfirmed = false;
	int32 RitualSeed = 0;

	// Client-side mirrors so RepNotify can compute deltas / edge-detect.
	float ClientPrevSync = 50.0f;
	int32 ClientPrevTier = 2;

	bool HasConcordAuthority() const;
	float LossMagnitude(EConcordLossReason Reason) const;
	static bool IsAmbientLoss(EConcordLossReason Reason);
	int32 TierForSync(float Value) const;
	float TierFloor(int32 Tier) const;
	void SetSyncInternal(float NewValue);          // clamps, retiers, broadcasts (server)
	void EnterDesync(EConcordLossReason Reason, bool bSyncSnap);
	void DealRitual(int32 Steps);
	void CompleteRitual();

	UFUNCTION() void OnRep_Sync();
	UFUNCTION() void OnRep_Tier();
	UFUNCTION() void OnRep_Desynced();
	UFUNCTION() void OnRep_Ritual();
};
