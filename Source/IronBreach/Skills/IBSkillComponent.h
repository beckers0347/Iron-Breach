#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Skills/IBSkillTypes.h"
#include "IBSkillComponent.generated.h"

DECLARE_MULTICAST_DELEGATE(FIBSkillsChanged);
class AIBPlayerState;

/** Durable loadout on the PlayerState. All mutations validate and save on the server. */
UCLASS(ClassGroup=(IronBreach))
class IRONBREACH_API UIBSkillComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UIBSkillComponent();
    void RestoreForIdentity();
    void CopyForTravel(const UIBSkillComponent* Previous);
    const FIBSkillState& GetState() const { return State; }
    int32 PointsAvailable() const;
    bool CanRefund() const;
    bool IsReady() const { return bReady; }
    const FText& GetStatus() const { return Status; }
    void RequestUnlock(FName Id);
    void RequestEquip(FName Id, EIBSkillSlot Slot);
    void RequestRefund();
    FIBSkillsChanged OnChanged;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
private:
    AIBPlayerState* Identity() const;
    void Commit(const FIBSkillState& Candidate, const FText& Success);
    UFUNCTION() void Changed();
    UFUNCTION(Server, Reliable) void Server_Unlock(FName Id);
    UFUNCTION(Server, Reliable) void Server_Equip(FName Id, EIBSkillSlot Slot);
    UFUNCTION(Server, Reliable) void Server_Refund();
    UFUNCTION(Client, Reliable) void Client_Status(const FText& Message);
    UPROPERTY(ReplicatedUsing=Changed) FIBSkillState State;
    UPROPERTY(ReplicatedUsing=Changed) bool bReady = false;
    FString SaveKey;
    FText Status;
};
