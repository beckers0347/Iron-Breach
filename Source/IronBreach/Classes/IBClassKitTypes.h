#pragma once

#include "CoreMinimal.h"
#include "Player/IBCharacterTypes.h"
#include "IBClassKitTypes.generated.h"

class AIBKitZone;

/**
 * Class kits — OPEN BY DESIGN. Each combat trade gets two verbs, a kit
 * ability (Q) and a movement tool (V); what they DO is data
 * (FIBKitAbilitySpec), built from a small set of generic effects so the
 * trades can be reshaped without touching C++, plus a Blueprint-only effect
 * for anything the primitives don't cover. The shipped values are first-pass
 * placeholders from CLASSES_AND_PROGRESSION.md §3 — tune or replace freely in
 * DA_Kit_<Trade> (Content/IronBreach/Classes).
 */
UENUM(BlueprintType)
enum class EIBKitEffect : uint8
{
	None		UMETA(DisplayName = "None (disabled)"),
	Blueprint	UMETA(DisplayName = "Blueprint only (BP_OnKitActivated does the work)"),
	Dash		UMETA(DisplayName = "Dash (lunge along the look direction)"),
	Grapple		UMETA(DisplayName = "Grapple (zip to the aimed surface)"),
	Glide		UMETA(DisplayName = "Glide (low gravity + full air control)"),
	ConeStrike	UMETA(DisplayName = "Cone strike (short dash + damage/knockback ahead)"),
	DeployZone	UMETA(DisplayName = "Deploy zone (pylon: slow / mark hostiles inside)"),
};

USTRUCT(BlueprintType)
struct FIBKitAbilitySpec
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (MultiLine = true))
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	EIBKitEffect Effect = EIBKitEffect::None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Cooldown = 8.f;

	/** Dash: damage-reduction window. Glide: float time. DeployZone: lifetime. ConeStrike: strike delay after the lunge. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Duration = 0.f;

	/** Dash / ConeStrike: launch speed (cm/s). Grapple: zip speed. Glide: gravity scale while gliding (0..1). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Strength = 1200.f;

	/** Grapple: max reach. ConeStrike: reach of the strike. DeployZone (bPlaceAtAim): max throw distance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Range = 600.f;

	/** DeployZone: zone radius. ConeStrike: half-width of the strike cone (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Radius = 500.f;

	/** ConeStrike: damage per hostile hit (through IDamageableInterface — kaiju armor rules apply). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0"))
	float Damage = 0.f;

	/** Incoming-damage multiplier while the effect lasts (Bulwark Dash: 0.35). 1 = none. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0", ClampMax = "1"))
	float DamageTakenScale = 1.f;

	/** DeployZone: MaxWalkSpeed multiplier for hostiles inside. 1 = no slow. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit", meta = (ClampMin = "0.05", ClampMax = "1"))
	float SlowFactor = 1.f;

	/** DeployZone: hostiles inside render Custom Depth (stencil 1) — hook an outline post-process to it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	bool bMarksTargets = false;

	/** DeployZone: drop it where you're aiming (up to Range) instead of at your feet. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	bool bPlaceAtAim = false;

	/** DeployZone: spawn this instead of the built-in pylon (must derive from AIBKitZone). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	TSubclassOf<AIBKitZone> ZoneClass;

	bool IsUsable() const { return Effect != EIBKitEffect::None; }
};

USTRUCT(BlueprintType)
struct FIBClassKit
{
	GENERATED_BODY()

	/** Q — the trade's signature verb. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	FIBKitAbilitySpec KitAbility;

	/** V — the trade's way of moving. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kit")
	FIBKitAbilitySpec MovementTool;
};
