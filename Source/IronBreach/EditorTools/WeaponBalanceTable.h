// WeaponBalanceTable.h
//
// Power-scaling tables for the Weapon Generator panel. Every Tier has a target
// DPS *budget* (randomized within a range); every Class has its own plausible
// fire-rate band, per-shot damage clamps, and a DPS multiplier relative to that
// budget. Damage-per-shot is solved as Budget / FireRate, so two rolls of the
// same Tier land on comparable overall power even when their Damage and Fire
// Rate numbers look very different -- a fast-firing low-damage roll and a
// slow-firing high-damage roll of the same Tier should feel equally strong.
//
// Not WITH_EDITOR-gated on purpose: EWeaponClass/EWeaponTier are used as
// UPROPERTY types on FWeaponGenerationParams (WeaponGeneratorLibrary.h), which
// compiles unconditionally, so the enums have to as well. Only the generation
// logic that USES this table is editor-only.
#pragma once

#include "CoreMinimal.h"
#include "WeaponBalanceTable.generated.h"

UENUM(BlueprintType)
enum class EWeaponClass : uint8
{
	Pistol,
	SMG,
	Rifle,
	Shotgun,
	LMG,
	Sniper,
	Count UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EWeaponTier : uint8
{
	S,
	A,
	B,
	C,
	D,
	E,
	Count UMETA(Hidden)
};

/** Result of one balance roll. Fire Rate is expressed two ways: RPS (rounds per
 *  second -- the intuitive "how fast does it shoot" number shown in the panel)
 *  and FireIntervalSeconds, the seconds-between-shots value that
 *  UWeaponCombatData::FireRate actually stores (its own field comment already
 *  calls this "Time between shots" -- functionally the weapon's per-shot
 *  cooldown, just the reciprocal of RPS rather than a separate stat). */
struct FRolledWeaponStats
{
	float Damage = 0.0f;
	float FireRateRPS = 0.0f;
	float FireIntervalSeconds = 0.0f;
	float MaxRange = 0.0f;
};

struct IRONBREACH_API FWeaponBalanceTable
{
	/** Rolls a full stat line for WeaponClass at Tier using Stream. Caller owns
	 *  the seed (fresh random per call, or a fixed seed for reproducible rolls). */
	static FRolledWeaponStats RollStats(EWeaponClass WeaponClass, EWeaponTier Tier, struct FRandomStream& Stream);

	static FString GetClassDisplayName(EWeaponClass WeaponClass);
	static FString GetTierDisplayName(EWeaponTier Tier);
};
