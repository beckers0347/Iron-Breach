#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Skills/IBSkillTypes.h"
#include "IBSkillSave.generated.h"

UCLASS()
class IRONBREACH_API UIBSkillSave : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY() int32 Version = 1;
    UPROPERTY() TMap<FString, FIBSkillState> Operatives;
};

/** Host-owned career store, keyed identically to XP and the vault. */
UCLASS()
class IRONBREACH_API UIBSkillSaveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    const FIBSkillState* Find(const FString& Key) const;
    bool Store(const FString& Key, const FIBSkillState& State);
private:
    UPROPERTY() TObjectPtr<UIBSkillSave> Save;
    bool bCanWrite = true;
};
