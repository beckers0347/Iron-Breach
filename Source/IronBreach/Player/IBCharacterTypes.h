#pragma once

#include "CoreMinimal.h"
#include "IBCharacterTypes.generated.h"

/**
 * Operative identity types — the account's up-to-3 playable characters
 * (CLASSES_AND_PROGRESSION.md §3: the four Breakwater combat trades).
 * Character choice is per-local-player, client-side data (ADR-002 posture:
 * nothing here replicates; the PlayerState can mirror it later when class
 * kits come online).
 */

UENUM(BlueprintType)
enum class EIBOperativeClass : uint8
{
	Breaker		UMETA(DisplayName = "Guardian"),
	Picket		UMETA(DisplayName = "Sentinel"),
	Bellringer	UMETA(DisplayName = "Saber"),
	Corpsman	UMETA(DisplayName = "Corpsman"),
};

UENUM(BlueprintType)
enum class EIBOperativeGender : uint8
{
	Male		UMETA(DisplayName = "Male"),
	Female		UMETA(DisplayName = "Female"),
};

/** One saved operative. Lives in UIBCharacterSaveGame's roster (max 3). */
USTRUCT(BlueprintType)
struct FIBCharacterRecord
{
	GENERATED_BODY()

	/** Stable identity — future per-character saves (XP, vault) key off this. */
	UPROPERTY(BlueprintReadOnly, Category = "Character")
	FGuid CharacterId;

	UPROPERTY(BlueprintReadOnly, Category = "Character")
	FString Callsign;

	UPROPERTY(BlueprintReadOnly, Category = "Character")
	EIBOperativeClass Class = EIBOperativeClass::Breaker;

	UPROPERTY(BlueprintReadOnly, Category = "Character")
	EIBOperativeGender Gender = EIBOperativeGender::Male;

	/** Display level — 1 until the XP subsystem starts feeding it. */
	UPROPERTY(BlueprintReadOnly, Category = "Character")
	int32 Level = 1;

	UPROPERTY(BlueprintReadOnly, Category = "Character")
	FDateTime CreatedUtc = FDateTime(0);

	/** Zero-tick == never deployed. */
	UPROPERTY(BlueprintReadOnly, Category = "Character")
	FDateTime LastPlayedUtc = FDateTime(0);

	bool IsValidRecord() const { return CharacterId.IsValid(); }
};

/** Display helpers, header-only like IBStyleKit — one place for the strings. */
namespace IBCharacter
{
	inline FText ClassName(EIBOperativeClass C)
	{
		switch (C)
		{
		case EIBOperativeClass::Breaker:    return NSLOCTEXT("IBCharacter", "ClassBreaker", "GUARDIAN");
		case EIBOperativeClass::Picket:     return NSLOCTEXT("IBCharacter", "ClassPicket", "SENTINEL");
		case EIBOperativeClass::Bellringer: return NSLOCTEXT("IBCharacter", "ClassBellringer", "SABER");
		case EIBOperativeClass::Corpsman:   return NSLOCTEXT("IBCharacter", "ClassCorpsman", "CORPSMAN");
		}
		return FText::GetEmpty();
	}

	/** The trade's motto + role, straight from the classes doc. */
	inline FText ClassRoleLine(EIBOperativeClass C)
	{
		switch (C)
		{
		case EIBOperativeClass::Breaker:    return NSLOCTEXT("IBCharacter", "RoleBreaker", "GUARD / PROTECT / DISCHARGE");
		case EIBOperativeClass::Picket:     return NSLOCTEXT("IBCharacter", "RolePicket", "CONCEAL / MISDIRECT / TRACK");
		case EIBOperativeClass::Bellringer: return NSLOCTEXT("IBCharacter", "RoleBellringer", "DASH / BREACH / SWEEP");
		case EIBOperativeClass::Corpsman:   return NSLOCTEXT("IBCharacter", "RoleCorpsman", "“BRING THEM HOME” — SUSTAIN");
		}
		return FText::GetEmpty();
	}

	inline FText ClassDescription(EIBOperativeClass C)
	{
		switch (C)
		{
		case EIBOperativeClass::Breaker:    return NSLOCTEXT("IBCharacter", "DescBreaker", "Time your guard, store the impact, and protect your fireteam with defensive fields.");
		case EIBOperativeClass::Picket:     return NSLOCTEXT("IBCharacter", "DescPicket", "Break enemy tracking with camouflage and decoys. Mark targets and control the approach.");
		case EIBOperativeClass::Bellringer: return NSLOCTEXT("IBCharacter", "DescBellringer", "Cross exposed ground with Vector Dash. Break through enemies with charges and kinetic sweeps.");
		case EIBOperativeClass::Corpsman:   return NSLOCTEXT("IBCharacter", "DescCorpsman", "The extraction specialist. Sustain, revive economy, and the rescue scoring the Breakwater decorates.");
		}
		return FText::GetEmpty();
	}

	/** Phase-1 ships 3 trades; the medical corps opens post-launch (§8). */
	inline bool ClassAvailable(EIBOperativeClass C)
	{
		return C == EIBOperativeClass::Breaker || C == EIBOperativeClass::Picket || C == EIBOperativeClass::Bellringer;
	}

	inline FText ClassLockedLine(EIBOperativeClass C)
	{
		return ClassAvailable(C) ? FText::GetEmpty()
			: NSLOCTEXT("IBCharacter", "LockedCorpsman", "CORPS NOT YET OPEN");
	}

	/** Per-trade accent color for cards and banners. */
	inline FLinearColor ClassColor(EIBOperativeClass C)
	{
		switch (C)
		{
		case EIBOperativeClass::Breaker:    return FLinearColor(0.80f, 0.32f, 0.16f); // breach red-orange
		case EIBOperativeClass::Picket:     return FLinearColor(0.25f, 0.75f, 0.85f); // uplink cyan
		case EIBOperativeClass::Bellringer: return FLinearColor(0.58f, 0.38f, 0.88f); // harmonic violet
		case EIBOperativeClass::Corpsman:   return FLinearColor(0.30f, 0.72f, 0.42f); // medic green
		}
		return FLinearColor::White;
	}

	inline FText GenderName(EIBOperativeGender G)
	{
		return G == EIBOperativeGender::Male
			? NSLOCTEXT("IBCharacter", "GenderMale", "MALE")
			: NSLOCTEXT("IBCharacter", "GenderFemale", "FEMALE");
	}
}
