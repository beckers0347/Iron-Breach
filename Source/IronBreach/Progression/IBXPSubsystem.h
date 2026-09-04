#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Progression/XPTypes.h"
#include "IBXPSubsystem.generated.h"

class AController;
class AActor;
class AIBMech_Base;
class UXPTuningData;
class UXPSaveGame;
class UIBItemDefinition;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnXPAwarded, EXPTrack, Track, const FString&, RecordKey, int32, NewTotalXP);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnXPLevelUp, EXPTrack, Track, const FString&, RecordKey, int32, NewLevel, int32, OldLevel);

/**
 * Server-authoritative XP + leveling, two independent tracks (EXPTrack -- see XPTypes.h):
 *
 *   PILOT (individual) -- earned fighting on foot as AIBCharacter_Infantry.
 *   CREW (pair)         -- earned fighting from the mech (hull or gunner seat). One record
 *                          shared by whichever two humans are currently crewing it; a human
 *                          with the AI co-pilot resolves to a solo-crew record (see
 *                          MakeCrewKeyFromMech).
 *
 * Current source: damage dealt + kills only (design scope as of this writing). Everything
 * routes through ReportDamage, called from the existing damage pipeline -- HealthComponent::
 * ApplyDamage covers Infantry, Enemy, and post-armor Kaiju damage; AIBCharacter_Kaiju calls
 * ReportKaijuArmorDamage directly for its armor-phase branch, which bypasses HealthComponent
 * entirely. AwardPilotXP/AwardCrewXP are a direct-grant escape hatch for future sources
 * (raid-phase completion, clean-play bonuses) that were scoped out for now.
 *
 * Levels unlock loadout entries from Tuning -- sidegrades, never stat upgrades (see
 * XPTuningData). This subsystem does not touch CONCORD; sync is per-encounter and never
 * persisted (spec §9) and must stay that way -- XP is the deliberately-separate,
 * persisted axis.
 *
 * Authority: every call site this hooks into already early-returns off authority
 * (HealthComponent::ApplyDamage, IBCharacter_Kaiju's armor branch both guard on
 * HasAuthority()), so ReportDamage/ReportKaijuArmorDamage only ever fire on the server by
 * construction. HasServerAuthority() double-checks NetMode anyway since a
 * GameInstanceSubsystem has no per-actor HasAuthority() of its own, and AwardPilotXP/
 * AwardCrewXP are public BlueprintCallable entry points that don't have that guarantee
 * upstream.
 *
 * Not yet: replicating XP/level to owning clients for HUD -- the server has the truth now;
 * forwarding it to the owning PlayerController's HUD is a follow-up, same posture as
 * ConcordComponent's "not yet: GAS mirroring" note. Not yet: an inventory/loadout system to
 * push GetUnlockedWeapons results into -- query it from wherever loadout selection lives
 * once that exists.
 */
UCLASS()
class IRONBREACH_API UIBXPSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Assign the tuning asset once at startup (e.g. GameMode::InitGame, or a BP call from
	 *  the level blueprint / game instance). Nothing awards XP until this is set. */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void SetTuning(UXPTuningData* InTuning) { Tuning = InTuning; }

	/** Central damage/kill hook for the normal (non-armor) damage pipeline. InstigatedBy +
		 *  DamageCauser come straight from IDamageableInterface / HealthComponent::ApplyDamage.
		 *  Resolves track (pilot vs crew) and the record key from DamageCauser automatically.
		 *  Server-only; silently no-ops everywhere else (see class comment on authority). */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void ReportDamage(float DamageAmount, AController* InstigatedBy, AActor* DamageCauser, bool bWasKillingBlow, float VictimMaxHealth, float VictimMaxArmor = 0.0f);

	/** Kaiju armor-phase damage hook. Separate from ReportDamage because armor soak happens
	 *  in AIBCharacter_Kaiju::HandleTakeDamage_Implementation BEFORE UHealthComponent ever
	 *  sees the hit -- call this directly from that branch. Applies
	 *  Tuning->ArmorPhaseDamageWeight and, on the hit that breaks armor, the crew-track
	 *  CrewXPPerArmorBreak bonus. */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void ReportKaijuArmorDamage(float DamageAmount, AController* InstigatedBy, AActor* DamageCauser, bool bBrokeArmor);

	/** Direct award, bypassing damage resolution. Escape hatch for future sources (raid
	 *  phases, clean-play bonuses) or manual/debug grants. */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void AwardPilotXP(AController* Pilot, int32 Amount);

	/** Direct crew award. SeatB may be null (solo crew, AI co-pilot in the other seat). */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void AwardCrewXP(AController* SeatA, AController* SeatB, int32 Amount);

	UFUNCTION(BlueprintPure, Category = "XP")
	int32 GetPilotLevel(AController* Pilot) const;

	UFUNCTION(BlueprintPure, Category = "XP")
	int32 GetPilotXP(AController* Pilot) const;

	/** SeatB may be null to query a solo-crew record. */
	UFUNCTION(BlueprintPure, Category = "XP")
	int32 GetCrewLevel(AController* SeatA, AController* SeatB) const;

	UFUNCTION(BlueprintPure, Category = "XP")
	int32 GetCrewXP(AController* SeatA, AController* SeatB) const;

	/** Flattened list of every weapon item unlocked at or below UpToLevel on the given track. */
	UFUNCTION(BlueprintCallable, Category = "XP")
	TArray<UIBItemDefinition*> GetUnlockedWeapons(EXPTrack Track, int32 UpToLevel) const;

	/** Flush in-memory records to disk now. Call this from wherever a raid actually ends --
	 *  RaidStateMachine's owner reaching ERaidPhase::Completed is Blueprint-side today
	 *  (RaidStateMachine.h has no C++ owner reference), so bind OnPhaseChanged there and
	 *  call this on Completed. Also called automatically on every level-up and on
	 *  GameInstance shutdown as a safety net, so nothing is lost even if that binding is
	 *  never added -- it just checkpoints less often. */
	UFUNCTION(BlueprintCallable, Category = "XP")
	void SaveNow();

	UPROPERTY(BlueprintAssignable, Category = "XP|Events")
	FOnXPAwarded OnXPAwarded;

	UPROPERTY(BlueprintAssignable, Category = "XP|Events")
	FOnXPLevelUp OnXPLevelUp;

private:
	UPROPERTY()
	TObjectPtr<UXPTuningData> Tuning;

	UPROPERTY()
	TObjectPtr<UXPSaveGame> SaveData;

	bool HasServerAuthority() const;

	/** DamageCauser -> (Track, RecordKey). Empty OutKey means "couldn't attribute" (AI-only
	 *  causer, environmental hazard, etc.) -- callers must treat that as XP dropped, not
	 *  misattributed to whoever happens to be nearby. */
	void ResolveAttribution(AActor* DamageCauser, EXPTrack& OutTrack, FString& OutKey) const;

	void GrantXP(EXPTrack Track, const FString& Key, int32 Amount);

public:
	/** Record keys are shared with the vault (per player + operative) — public so
	 *  AIBPlayerState can key its progression the same way. */
	static FString MakePlayerKey(const AController* Controller);
	static FString MakeCrewKey(const AController* SeatA, const AController* SeatB);
	static FString MakeCrewKeyFromMech(const AIBMech_Base* Mech);
};
