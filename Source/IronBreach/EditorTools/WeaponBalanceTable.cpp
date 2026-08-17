// WeaponBalanceTable.cpp
#include "EditorTools/WeaponBalanceTable.h"
#include "Math/RandomStream.h"

namespace
{
	struct FClassProfile
	{
		float MinRPS;
		float MaxRPS;
		float MinDamage;   // hard per-shot clamps -- keep a fast-rolling Sniper from
		float MaxDamage;   // reading like an SMG, or a slow SMG roll from one-shotting.
		float MinRange;
		float MaxRange;
		float DPSMultiplier; // relative to Rifle's 1.00 baseline at the same Tier.
	};

	struct FTierBudget
	{
		float MinDPS;
		float MaxDPS;
		float RangeMultiplier; // small tier-based range bonus, independent of DPS.
	};

	// Baseline: 100 HP (HealthComponent::MaxHealth). Tier S ~130-150 DPS puts a
	// clean two-body-shot-ish kill (~0.7-0.8s) within reach; Tier E sits closer to
	// 2-3s. Class DPSMultiplier then spreads that same Tier budget across
	// archetypes that are meant to feel different in strength by design (a Sniper
	// isn't meant to out-DPS a Rifle sustained -- it's meant to hit once, hard).
	const FClassProfile& GetClassProfile(EWeaponClass WeaponClass)
	{
		static const FClassProfile Profiles[(uint8)EWeaponClass::Count] = {
			/* Pistol  */ { 2.2f,  4.5f,  10.f,  35.f, 1800.f,  3200.f, 0.70f },
			/* SMG     */ { 8.0f, 13.0f,   8.f,  20.f, 2200.f,  3800.f, 0.88f },
			/* Rifle   */ { 5.5f,  9.0f,  15.f,  40.f, 4200.f,  6200.f, 1.00f },
			/* Shotgun */ { 0.9f,  1.8f,  55.f, 140.f, 1000.f,  2000.f, 1.25f },
			/* LMG     */ { 7.5f, 11.0f,  12.f,  30.f, 4800.f,  6800.f, 1.05f },
			/* Sniper  */ { 0.5f,  1.1f,  90.f, 220.f, 8500.f, 14000.f, 0.60f },
		};
		return Profiles[(uint8)WeaponClass];
	}

	const FTierBudget& GetTierBudget(EWeaponTier Tier)
	{
		static const FTierBudget Budgets[(uint8)EWeaponTier::Count] = {
			/* S */ { 130.f, 150.f, 1.15f },
			/* A */ { 108.f, 129.f, 1.10f },
			/* B */ {  88.f, 107.f, 1.05f },
			/* C */ {  68.f,  87.f, 1.00f },
			/* D */ {  50.f,  67.f, 0.93f },
			/* E */ {  34.f,  49.f, 0.85f },
		};
		return Budgets[(uint8)Tier];
	}
}

FRolledWeaponStats FWeaponBalanceTable::RollStats(EWeaponClass WeaponClass, EWeaponTier Tier, FRandomStream& Stream)
{
	const FClassProfile& ClassProfile = GetClassProfile(WeaponClass);
	const FTierBudget& TierBudget = GetTierBudget(Tier);

	const float FireRateRPS = Stream.FRandRange(ClassProfile.MinRPS, ClassProfile.MaxRPS);

	// Same Tier == same power budget (scaled by the Class's own multiplier). Damage
	// is solved FROM the budget, not rolled independently, so a fast/low-damage
	// roll and a slow/high-damage roll of the same Tier land on comparable DPS --
	// e.g. two Tier S rifles at 50 dmg/1 RPS and 25 dmg/2 RPS both read as "S tier."
	const float DPSBudget = Stream.FRandRange(TierBudget.MinDPS, TierBudget.MaxDPS) * ClassProfile.DPSMultiplier;

	float Damage = DPSBudget / FMath::Max(FireRateRPS, 0.01f);
	Damage = FMath::Clamp(Damage, ClassProfile.MinDamage, ClassProfile.MaxDamage);

	const float RolledRange = Stream.FRandRange(ClassProfile.MinRange, ClassProfile.MaxRange) * TierBudget.RangeMultiplier;

	FRolledWeaponStats Result;
	Result.Damage = FMath::RoundToFloat(Damage);
	Result.FireRateRPS = FireRateRPS;
	Result.FireIntervalSeconds = 1.0f / FMath::Max(FireRateRPS, 0.01f);
	Result.MaxRange = FMath::RoundToFloat(RolledRange);
	return Result;
}

FString FWeaponBalanceTable::GetClassDisplayName(EWeaponClass WeaponClass)
{
	switch (WeaponClass)
	{
	case EWeaponClass::Pistol:  return TEXT("Pistol");
	case EWeaponClass::SMG:     return TEXT("SMG");
	case EWeaponClass::Rifle:   return TEXT("Rifle");
	case EWeaponClass::Shotgun: return TEXT("Shotgun");
	case EWeaponClass::LMG:     return TEXT("LMG");
	case EWeaponClass::Sniper:  return TEXT("Sniper");
	default:                    return TEXT("Unknown");
	}
}

FString FWeaponBalanceTable::GetTierDisplayName(EWeaponTier Tier)
{
	switch (Tier)
	{
	case EWeaponTier::S: return TEXT("S");
	case EWeaponTier::A: return TEXT("A");
	case EWeaponTier::B: return TEXT("B");
	case EWeaponTier::C: return TEXT("C");
	case EWeaponTier::D: return TEXT("D");
	case EWeaponTier::E: return TEXT("E");
	default:             return TEXT("?");
	}
}
