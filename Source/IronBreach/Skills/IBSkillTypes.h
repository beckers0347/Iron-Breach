#pragma once
#include "CoreMinimal.h"
#include "Classes/IBClassKitTypes.h"
#include "IBSkillTypes.generated.h"

UENUM(BlueprintType)
enum class EIBSkillSlot : uint8 { Signature, TacticalOne, TacticalTwo, Overdrive };

/** IDs are stable save keys. A variant replaces its parent in an equipped slot. */
USTRUCT(BlueprintType)
struct FIBSkillState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) TArray<FName> Unlocked;
    UPROPERTY(BlueprintReadOnly) TArray<FName> Equipped;
    bool operator==(const FIBSkillState& Other) const { return Unlocked == Other.Unlocked && Equipped == Other.Equipped; }
};

enum class EIBSkillKind : uint8 { Signature, Tactical, Overdrive };
enum class EIBSkillIcon : uint8 { Dash, Charge, Sweep, Grapple, Overdrive, Veil, Dart, Decoy, Guard, Impact, Ward };

struct FIBSkillNode
{
    FName Id;
    FName Parent;
    EIBOperativeClass Class = EIBOperativeClass::Breaker;
    EIBSkillKind Kind = EIBSkillKind::Signature;
    EIBSkillIcon Icon = EIBSkillIcon::Dash;
    FText Name;
    FText Description;
    int32 Cost = 0;
    int32 Level = 1;
    FVector2D Position;
    FIBKitAbilitySpec Spec;
};

namespace IBSkills
{
    IRONBREACH_API const TArray<FIBSkillNode>& Catalog();
    IRONBREACH_API const FIBSkillNode* Find(FName Id);
    IRONBREACH_API FName RootAbility(FName Id);
    IRONBREACH_API FIBSkillState StarterState(EIBOperativeClass Class);
    IRONBREACH_API bool IsUnlocked(const FIBSkillState& State, FName Id);
    IRONBREACH_API int32 PointsAvailable(const FIBSkillState& State, int32 Level);
    IRONBREACH_API bool CanEquip(const FIBSkillNode& Node, EIBSkillSlot Slot);
    IRONBREACH_API bool Unlock(FIBSkillState& State, EIBOperativeClass Class, int32 Level, FName Id, FText& Error);
    IRONBREACH_API bool Equip(FIBSkillState& State, EIBOperativeClass Class, FName Id, EIBSkillSlot Slot, FText& Error);
    IRONBREACH_API FIBSkillState Sanitize(const FIBSkillState& State, EIBOperativeClass Class, int32 Level);
    IRONBREACH_API FText SlotName(EIBSkillSlot Slot);
}
