#include "Mech/ConcordComponent.h"
#include "Mech/ConcordTuningData.h"
#include "IronBreach.h"
#include "Net/UnrealNetwork.h"
#include "Math/RandomStream.h"

UConcordComponent::UConcordComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // Event-driven. No decay timers, ever (spec §2).
	SetIsReplicatedByDefault(true);
}

void UConcordComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UConcordComponent, Sync);
	DOREPLIFETIME(UConcordComponent, CurrentTier);
	DOREPLIFETIME(UConcordComponent, bDesynced);
	DOREPLIFETIME(UConcordComponent, bLastDesyncWasSnap);
	DOREPLIFETIME(UConcordComponent, LastLossReason);
	DOREPLIFETIME(UConcordComponent, RitualPattern);
	DOREPLIFETIME(UConcordComponent, RitualIndex);
}

void UConcordComponent::BeginPlay()
{
	Super::BeginPlay();

	if (!Tuning)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Concord] No tuning data assigned on %s — using code defaults via a transient asset. Create DA_ConcordTuning and assign it."),
			*GetNameSafe(GetOwner()));
		Tuning = NewObject<UConcordTuningData>(this, TEXT("TransientConcordTuning"));
	}

	if (HasConcordAuthority())
	{
		Sync = TierFloor(2); // Start at the bottom of COHERENT — room to climb, room to fall.
		CurrentTier = TierForSync(Sync);
	}
	ClientPrevSync = Sync;
	ClientPrevTier = CurrentTier;
}

bool UConcordComponent::HasConcordAuthority() const
{
	const AActor* Owner = GetOwner();
	return Owner && Owner->HasAuthority();
}

float UConcordComponent::LossMagnitude(EConcordLossReason Reason) const
{
	switch (Reason)
	{
	case EConcordLossReason::MissedResponse:    return Tuning->Loss_MissedResponse;
	case EConcordLossReason::CrossedInputs:     return Tuning->Loss_CrossedInputs;
	case EConcordLossReason::UnshieldedCrit:    return Tuning->Loss_UnshieldedCrit;
	case EConcordLossReason::PilotDowned:       return Tuning->Loss_PilotDowned;
	case EConcordLossReason::SoloChain:         return Tuning->Loss_SoloChain;
	case EConcordLossReason::KaijuInterference: return Tuning->Loss_KaijuInterference;
	default:                                    return 0.0f;
	}
}

bool UConcordComponent::IsAmbientLoss(EConcordLossReason Reason)
{
	// Floor protection (spec §5.2): ambient losses cannot push below T1. Only acute
	// events can enter T0.
	return Reason == EConcordLossReason::CrossedInputs
		|| Reason == EConcordLossReason::SoloChain
		|| Reason == EConcordLossReason::MissedResponse;
}

int32 UConcordComponent::TierForSync(float Value) const
{
	if (Value >= Tuning->Tier4Threshold) return 4;
	if (Value >= Tuning->Tier3Threshold) return 3;
	if (Value >= Tuning->Tier2Threshold) return 2;
	if (Value >= Tuning->Tier1Threshold) return 1;
	return 0;
}

float UConcordComponent::TierFloor(int32 Tier) const
{
	switch (Tier)
	{
	case 4:  return Tuning->Tier4Threshold;
	case 3:  return Tuning->Tier3Threshold;
	case 2:  return Tuning->Tier2Threshold;
	case 1:  return Tuning->Tier1Threshold;
	default: return 0.0f;
	}
}

void UConcordComponent::SetSyncInternal(float NewValue)
{
	const float Old = Sync;
	Sync = FMath::Clamp(NewValue, 0.0f, 100.0f);

	if (!FMath::IsNearlyEqual(Old, Sync))
	{
		OnSyncChanged.Broadcast(Sync, Sync - Old);
	}

	const int32 OldTier = CurrentTier;
	CurrentTier = TierForSync(Sync);
	if (CurrentTier != OldTier)
	{
		OnTierChanged.Broadcast(CurrentTier, OldTier);
	}
}

void UConcordComponent::RegisterCoordinatedAction()
{
	if (!HasConcordAuthority() || bDesynced) return;

	float Mult = 1.0f;
	if (AdrenalineRemaining > 0)
	{
		// Adrenaline overrides Debt while it lasts (spec §4.4): strong start, then earn the rest.
		Mult = Tuning->AdrenalineMultiplier;
		AdrenalineRemaining--;
	}
	else if (DebtRemaining > 0)
	{
		Mult = Tuning->DebtMultiplier;
		DebtRemaining--;
	}

	SetSyncInternal(Sync + Tuning->BaseGain * Mult);
}

void UConcordComponent::RegisterLoss(EConcordLossReason Reason)
{
	if (!HasConcordAuthority()) return;

	// T0 guard (spec §3.2/§5.3): you cannot dig deeper than the bottom, and the ritual
	// cannot be interrupted by sync loss.
	if (bDesynced) return;

	float Magnitude = LossMagnitude(Reason);
	if (bNextLossDampened)
	{
		Magnitude *= Tuning->LastLinkDampen;
		bNextLossDampened = false;
	}

	const int32 TierBefore = CurrentTier;
	float Proposed = Sync - Magnitude;

	// Floor protection: ambient losses stop at the T1 floor.
	if (IsAmbientLoss(Reason))
	{
		Proposed = FMath::Max(Proposed, TierFloor(1));
	}

	const bool bWouldDesync = TierForSync(Proposed) == 0;

	// Last Link (spec §4.1): first time per encounter a single event would carry the meter
	// from T2+ into T0, stop at the T1 floor instead and dampen the next loss.
	if (bWouldDesync && TierBefore >= 2 && bLastLinkAvailable)
	{
		bLastLinkAvailable = false;
		bNextLossDampened = true;
		SetSyncInternal(TierFloor(1));
		OnLastLink.Broadcast();
		UE_LOG(LogIronBreach, Display, TEXT("[Concord] LAST LINK — held at the T1 floor (%s)."), *UEnum::GetValueAsString(Reason));
		return;
	}

	SetSyncInternal(Proposed);

	if (CurrentTier == 0)
	{
		// Sync Snap (spec §4.2): desync triggered from Overdrive is special.
		EnterDesync(Reason, /*bSyncSnap=*/ TierBefore == 4);
	}
}

void UConcordComponent::EnterDesync(EConcordLossReason Reason, bool bSyncSnap)
{
	bDesynced = true;
	bLastDesyncWasSnap = bSyncSnap;
	LastLossReason = Reason;

	DealRitual(bSyncSnap ? Tuning->RitualStepsSnap : Tuning->RitualStepsNormal);

	OnDesyncStarted.Broadcast(Reason, bSyncSnap);
	UE_LOG(LogIronBreach, Display, TEXT("[Concord] DESYNC (%s)%s — ritual dealt, %d steps."),
		*UEnum::GetValueAsString(Reason), bSyncSnap ? TEXT(" [SYNC SNAP]") : TEXT(""), RitualPattern.Num());
}

void UConcordComponent::DealRitual(int32 Steps)
{
	RitualSeed = FMath::Rand();
	FRandomStream Stream(RitualSeed);

	RitualPattern.Reset();
	// Alternate seat verbs (deterministic per seed), always closing on BothConfirm —
	// recovery ends with the clasp, both hands on it.
	for (int32 i = 0; i < Steps - 1; ++i)
	{
		RitualPattern.Add(Stream.RandRange(0, 1) == 0 ? EConcordRitualStep::NavBrace : EConcordRitualStep::GunVent);
	}
	RitualPattern.Add(EConcordRitualStep::BothConfirm);

	RitualIndex = 0;
	bRitualNavConfirmed = false;
	bRitualGunConfirmed = false;

	if (RitualPattern.IsValidIndex(0))
	{
		OnRitualAdvanced.Broadcast(0, RitualPattern[0]);
	}
}

void UConcordComponent::RegisterRitualInput(bool bFromDriver, EConcordRitualStep Step)
{
	if (!HasConcordAuthority() || !bDesynced || !RitualPattern.IsValidIndex(RitualIndex)) return;

	const EConcordRitualStep Expected = RitualPattern[RitualIndex];

	// Seat must match the verb: NavBrace is the driver's, GunVent the gunner's.
	const bool bSeatMatches =
		(Expected == EConcordRitualStep::NavBrace && bFromDriver) ||
		(Expected == EConcordRitualStep::GunVent && !bFromDriver) ||
		(Expected == EConcordRitualStep::BothConfirm);

	if (Step != Expected || !bSeatMatches)
	{
		// Miss does not punish — re-roll with a new seed (spec §3.3). The cost is time
		// under pressure, which the kaiju is already supplying.
		OnRitualMissed.Broadcast();
		DealRitual(RitualPattern.Num());
		return;
	}

	if (Expected == EConcordRitualStep::BothConfirm)
	{
		bRitualNavConfirmed |= bFromDriver;
		bRitualGunConfirmed |= !bFromDriver;
		if (!(bRitualNavConfirmed && bRitualGunConfirmed))
		{
			return; // waiting on the partner's hand
		}
	}

	RitualIndex++;
	if (RitualIndex >= RitualPattern.Num())
	{
		CompleteRitual();
	}
	else
	{
		bRitualNavConfirmed = false;
		bRitualGunConfirmed = false;
		OnRitualAdvanced.Broadcast(RitualIndex, RitualPattern[RitualIndex]);
	}
}

void UConcordComponent::CompleteRitual()
{
	bDesynced = false;
	RitualPattern.Reset();
	RitualIndex = 0;

	// Restore to the T1 floor with an Adrenaline Window; Debt makes the rest a climb.
	AdrenalineRemaining = Tuning->AdrenalineActions;
	DebtRemaining = Tuning->DebtActions;
	SetSyncInternal(TierFloor(1));

	OnDesyncEnded.Broadcast();
	UE_LOG(LogIronBreach, Display, TEXT("[Concord] Ritual complete — link restored. Adrenaline window open."));
}

void UConcordComponent::ResetEncounter()
{
	if (!HasConcordAuthority()) return;

	bLastLinkAvailable = true;
	bNextLossDampened = false;
	AdrenalineRemaining = 0;
	DebtRemaining = 0;
	bDesynced = false;
	RitualPattern.Reset();
	RitualIndex = 0;
	SetSyncInternal(TierFloor(2));
}

bool UConcordComponent::AreHeavyWeaponsLocked() const
{
	return bDesynced && Tuning && Tuning->bDesyncLocksHeavyWeapons;
}

float UConcordComponent::GetMoveSpeedFactor() const
{
	return (bDesynced && Tuning) ? Tuning->DesyncMoveSpeedFactor : 1.0f;
}

// ---- RepNotify: rebroadcast on clients so HUD/audio hooks work on every machine ----

void UConcordComponent::OnRep_Sync()
{
	OnSyncChanged.Broadcast(Sync, Sync - ClientPrevSync);
	ClientPrevSync = Sync;
}

void UConcordComponent::OnRep_Tier()
{
	OnTierChanged.Broadcast(CurrentTier, ClientPrevTier);
	ClientPrevTier = CurrentTier;
}

void UConcordComponent::OnRep_Desynced()
{
	if (bDesynced)
	{
		OnDesyncStarted.Broadcast(LastLossReason, bLastDesyncWasSnap);
	}
	else
	{
		OnDesyncEnded.Broadcast();
	}
}

void UConcordComponent::OnRep_Ritual()
{
	if (bDesynced && RitualPattern.IsValidIndex(RitualIndex))
	{
		OnRitualAdvanced.Broadcast(RitualIndex, RitualPattern[RitualIndex]);
	}
}
