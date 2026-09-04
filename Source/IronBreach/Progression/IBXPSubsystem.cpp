#include "Progression/IBXPSubsystem.h"
#include "Progression/XPTuningData.h"
#include "Progression/XPSaveGame.h"
#include "IronBreach.h"
#include "Items/IBPlayerState.h"
#include "Mech/IBMech_Base.h"
#include "Mech/IBGunnerSeat.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

void UIBXPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	SaveData = Cast<UXPSaveGame>(UGameplayStatics::LoadGameFromSlot(UXPSaveGame::SlotName, UXPSaveGame::UserIndex));
	if (!SaveData)
	{
		SaveData = Cast<UXPSaveGame>(UGameplayStatics::CreateSaveGameObject(UXPSaveGame::StaticClass()));
	}
}

void UIBXPSubsystem::Deinitialize()
{
	SaveNow(); // Safety net -- bind a real checkpoint to raid-end via SaveNow() as noted in the header.
	Super::Deinitialize();
}

bool UIBXPSubsystem::HasServerAuthority() const
{
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	return World && World->GetNetMode() != NM_Client;
}

FString UIBXPSubsystem::MakePlayerKey(const AController* Controller)
{
	if (!Controller) return FString();

	const APlayerState* PS = Controller->PlayerState;
	if (!PS) return FString();

	// Stable across sessions when a real online subsystem is present (Steam, per ADR-002).
	// PIE/LAN (NULL OSS) synthesizes a per-session ID instead -- same caveat
	// UIBSessionSubsystem already lives with.
	FString Key = PS->GetUniqueId().IsValid()
		? PS->GetUniqueId().ToString()
		: FString::Printf(TEXT("name:%s"), *PS->GetPlayerName()); // dev/PIE fallback

	// Per-operative: three billets are three careers. The id rides on the
	// replicated PlayerState identity, so the host keys it the same for everyone.
	if (const AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS))
	{
		if (IBPS->HasOperative() && IBPS->GetOperativeId().IsValid())
		{
			Key += TEXT("#") + IBPS->GetOperativeId().ToString(EGuidFormats::Digits);
		}
	}
	return Key;
}

FString UIBXPSubsystem::MakeCrewKey(const AController* SeatA, const AController* SeatB)
{
	TArray<FString> Keys;
	for (const AController* Seat : { SeatA, SeatB })
	{
		// Only human seats count toward the pairing key -- the AI co-pilot filling an empty
		// seat must not turn a solo player's record into a shared one.
		if (Seat && Seat->IsA<APlayerController>())
		{
			FString Key = MakePlayerKey(Seat);
			if (!Key.IsEmpty())
			{
				Keys.Add(Key);
			}
		}
	}

	if (Keys.IsEmpty()) return FString();

	// Sorted + joined so the key is order-independent: same two humans, same record,
	// regardless of which seat each is in.
	Keys.Sort();
	return FString::Join(Keys, TEXT("|"));
}

FString UIBXPSubsystem::MakeCrewKeyFromMech(const AIBMech_Base* Mech)
{
	if (!Mech) return FString();
	return MakeCrewKey(Mech->LeftSeatController.Get(), Mech->RightSeatController.Get());
}

void UIBXPSubsystem::ResolveAttribution(AActor* DamageCauser, EXPTrack& OutTrack, FString& OutKey) const
{
	OutKey.Empty();
	if (!DamageCauser) return;

	// Crew: the gunner seat resolves back to its hull; the hull itself is also a valid
	// causer (legacy single-machine hull-fired path -- see IBMech_Base::FireWeapon).
	const AIBMech_Base* Mech = Cast<AIBMech_Base>(DamageCauser);
	if (!Mech)
	{
		if (const AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(DamageCauser))
		{
			Mech = Seat->OwningMech;
		}
	}

	if (Mech)
	{
		OutTrack = EXPTrack::Crew;
		OutKey = MakeCrewKeyFromMech(Mech);
		return;
	}

	if (const AIBCharacter_Infantry* Infantry = Cast<AIBCharacter_Infantry>(DamageCauser))
	{
		OutTrack = EXPTrack::Pilot;
		OutKey = MakePlayerKey(Infantry->GetController());
		return;
	}

	// Unrecognized causer (enemy AI, environmental hazard, etc.) -- leave OutKey empty.
	// XP is dropped, never misattributed.
}

void UIBXPSubsystem::GrantXP(EXPTrack Track, const FString& Key, int32 Amount)
{
	if (Amount <= 0 || Key.IsEmpty() || !SaveData) return;

	TMap<FString, FXPRecord>& Records = (Track == EXPTrack::Pilot) ? SaveData->PilotRecords : SaveData->CrewRecords;
	FXPRecord& Record = Records.FindOrAdd(Key);

	const TArray<int32> EmptyThresholds;
	const TArray<int32>& Thresholds = Tuning
		? ((Track == EXPTrack::Pilot) ? Tuning->PilotLevelThresholds : Tuning->CrewLevelThresholds)
		: EmptyThresholds;

	Record.TotalXP += Amount;
	const int32 OldLevel = Record.Level;
	Record.Level = UXPTuningData::LevelForXP(Record.TotalXP, Thresholds);

	OnXPAwarded.Broadcast(Track, Key, Record.TotalXP);

	if (Record.Level != OldLevel)
	{
		OnXPLevelUp.Broadcast(Track, Key, Record.Level, OldLevel);
		UE_LOG(LogIronBreach, Display, TEXT("[XP] %s %s reached level %d (%d XP)."),
			Track == EXPTrack::Pilot ? TEXT("Pilot") : TEXT("Crew"), *Key, Record.Level, Record.TotalXP);
		SaveNow(); // A level-up (and its unlocks) is never lost to a crash.
	}
}

void UIBXPSubsystem::ReportDamage(float DamageAmount, AController* InstigatedBy, AActor* DamageCauser, bool bWasKillingBlow, float VictimMaxHealth, float VictimMaxArmor)
{
	if (!HasServerAuthority() || !SaveData || DamageAmount <= 0.0f) return;

	EXPTrack Track;
	FString Key;
	ResolveAttribution(DamageCauser, Track, Key);
	if (Key.IsEmpty()) return;

	const float DamageRate = Tuning ? ((Track == EXPTrack::Pilot) ? Tuning->PilotXPPerDamage : Tuning->CrewXPPerDamage) : 0.0f;

	int32 KillXP = 0;
	if (bWasKillingBlow && Tuning)
	{
		// Scale the kill reward by the sheer size of the enemy's total pool
		const float KillMultiplier = (Track == EXPTrack::Pilot) ? Tuning->PilotKillBonusMultiplier : Tuning->CrewKillBonusMultiplier;
		KillXP = FMath::RoundToInt((VictimMaxHealth + VictimMaxArmor) * KillMultiplier);
	}

	const int32 DamageXP = FMath::RoundToInt(DamageAmount * DamageRate);

	GrantXP(Track, Key, DamageXP + KillXP);
}

void UIBXPSubsystem::ReportKaijuArmorDamage(float DamageAmount, AController* InstigatedBy, AActor* DamageCauser, bool bBrokeArmor)
{
	if (!HasServerAuthority() || !SaveData || !Tuning || DamageAmount <= 0.0f) return;

	EXPTrack Track;
	FString Key;
	ResolveAttribution(DamageCauser, Track, Key);
	if (Key.IsEmpty()) return;

	const float DamageRate = (Track == EXPTrack::Pilot) ? Tuning->PilotXPPerDamage : Tuning->CrewXPPerDamage;
	const int32 DamageXP = FMath::RoundToInt(DamageAmount * DamageRate * Tuning->ArmorPhaseDamageWeight);
	const int32 BreakXP = (bBrokeArmor && Track == EXPTrack::Crew) ? Tuning->CrewXPPerArmorBreak : 0;

	GrantXP(Track, Key, DamageXP + BreakXP);
}

void UIBXPSubsystem::AwardPilotXP(AController* Pilot, int32 Amount)
{
	if (!HasServerAuthority()) return;
	GrantXP(EXPTrack::Pilot, MakePlayerKey(Pilot), Amount);
}

void UIBXPSubsystem::AwardCrewXP(AController* SeatA, AController* SeatB, int32 Amount)
{
	if (!HasServerAuthority()) return;
	GrantXP(EXPTrack::Crew, MakeCrewKey(SeatA, SeatB), Amount);
}

int32 UIBXPSubsystem::GetPilotLevel(AController* Pilot) const
{
	const FString Key = MakePlayerKey(Pilot);
	if (Key.IsEmpty() || !SaveData) return 1;
	const FXPRecord* Record = SaveData->PilotRecords.Find(Key);
	return Record ? Record->Level : 1;
}

int32 UIBXPSubsystem::GetPilotXP(AController* Pilot) const
{
	const FString Key = MakePlayerKey(Pilot);
	if (Key.IsEmpty() || !SaveData) return 0;
	const FXPRecord* Record = SaveData->PilotRecords.Find(Key);
	return Record ? Record->TotalXP : 0;
}

int32 UIBXPSubsystem::GetCrewLevel(AController* SeatA, AController* SeatB) const
{
	const FString Key = MakeCrewKey(SeatA, SeatB);
	if (Key.IsEmpty() || !SaveData) return 1;
	const FXPRecord* Record = SaveData->CrewRecords.Find(Key);
	return Record ? Record->Level : 1;
}

int32 UIBXPSubsystem::GetCrewXP(AController* SeatA, AController* SeatB) const
{
	const FString Key = MakeCrewKey(SeatA, SeatB);
	if (Key.IsEmpty() || !SaveData) return 0;
	const FXPRecord* Record = SaveData->CrewRecords.Find(Key);
	return Record ? Record->TotalXP : 0;
}

TArray<UIBItemDefinition*> UIBXPSubsystem::GetUnlockedWeapons(EXPTrack Track, int32 UpToLevel) const
{
	TArray<UIBItemDefinition*> Result;
	if (!Tuning) return Result;

	const TArray<FXPLevelUnlock>& Unlocks = (Track == EXPTrack::Pilot) ? Tuning->PilotUnlocks : Tuning->CrewUnlocks;
	for (const FXPLevelUnlock& Entry : Unlocks)
	{
		if (Entry.Level > UpToLevel) continue;

		for (UIBItemDefinition* Weapon : Entry.UnlockedWeapons)
		{
			if (Weapon)
			{
				Result.Add(Weapon);
			}
		}
	}
	return Result;
}

void UIBXPSubsystem::SaveNow()
{
	if (SaveData && HasServerAuthority())
	{
		UGameplayStatics::SaveGameToSlot(SaveData, UXPSaveGame::SlotName, UXPSaveGame::UserIndex);
	}
}
