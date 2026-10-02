#include "Skills/IBSkillComponent.h"
#include "Skills/IBSkillSave.h"
#include "Items/IBPlayerState.h"
#include "Progression/IBXPSubsystem.h"
#include "Online/IBWatchTypes.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"

UIBSkillComponent::UIBSkillComponent() { SetIsReplicatedByDefault(true); }
void UIBSkillComponent::CopyForTravel(const UIBSkillComponent* Previous)
{
    if (!GetOwner()->HasAuthority() || !Previous) { return; }
    State=Previous->State; SaveKey=Previous->SaveKey; bReady=Previous->bReady; Changed();
}
AIBPlayerState* UIBSkillComponent::Identity() const { return Cast<AIBPlayerState>(GetOwner()); }
void UIBSkillComponent::RestoreForIdentity()
{
    AIBPlayerState* PS = Identity();
    if (!PS || !PS->HasAuthority() || !PS->HasOperative()) { return; }
    UIBSkillSaveSubsystem* Store = PS->GetGameInstance()->GetSubsystem<UIBSkillSaveSubsystem>();
    SaveKey = UIBXPSubsystem::MakePlayerKey(PS->GetOwningController());
    const FIBSkillState* Saved = Store ? Store->Find(SaveKey) : nullptr;
    State = IBSkills::Sanitize(Saved ? *Saved : FIBSkillState(), PS->GetOperativeClass(), PS->GetOperativeLevel());
    bReady = true;
    Changed();
    PS->ForceNetUpdate();
}
int32 UIBSkillComponent::PointsAvailable() const
{
    const AIBPlayerState* PS = Identity();
    return IBSkills::PointsAvailable(State, PS ? PS->GetOperativeLevel() : 1);
}
bool UIBSkillComponent::CanRefund() const
{
    // Resolve the actual world on both sides; a client cannot assert that it is in a hub.
    return bReady && GetWorld() && IBWatch::DestinationForMap(GetWorld()->GetMapName()) == FName(TEXT("watch"));
}
void UIBSkillComponent::RequestUnlock(FName Id) { Server_Unlock(Id); }
void UIBSkillComponent::RequestEquip(FName Id, EIBSkillSlot Slot) { Server_Equip(Id, Slot); }
void UIBSkillComponent::RequestRefund() { Server_Refund(); }
void UIBSkillComponent::Server_Unlock_Implementation(FName Id)
{
    AIBPlayerState* PS = Identity(); if (!PS || !bReady) { return; }
    FIBSkillState Next = State; FText Error;
    if (!IBSkills::Unlock(Next, PS->GetOperativeClass(), PS->GetOperativeLevel(), Id, Error)) { Client_Status(Error); return; }
    Commit(Next, NSLOCTEXT("IBSkills", "UnlockedOK", "Skill unlocked. Choose a slot to equip it."));
}
void UIBSkillComponent::Server_Equip_Implementation(FName Id, EIBSkillSlot Slot)
{
    AIBPlayerState* PS = Identity(); if (!PS || !bReady) { return; }
    FIBSkillState Next = State; FText Error;
    if (!IBSkills::Equip(Next, PS->GetOperativeClass(), Id, Slot, Error)) { Client_Status(Error); return; }
    Commit(Next, NSLOCTEXT("IBSkills", "EquippedOK", "Loadout saved."));
}
void UIBSkillComponent::Server_Refund_Implementation()
{
    AIBPlayerState* PS = Identity(); if (!PS || !bReady) { return; }
    if (!CanRefund()) { Client_Status(NSLOCTEXT("IBSkills", "RefundHub", "Return to the Bastion to refund skills.")); return; }
    Commit(IBSkills::StarterState(PS->GetOperativeClass()), NSLOCTEXT("IBSkills", "RefundOK", "Points refunded. Your starter loadout is equipped."));
}
void UIBSkillComponent::Commit(const FIBSkillState& Candidate, const FText& Success)
{
    AIBPlayerState* PS = Identity();
    UIBSkillSaveSubsystem* Store = PS ? PS->GetGameInstance()->GetSubsystem<UIBSkillSaveSubsystem>() : nullptr;
    if (!Store || !Store->Store(SaveKey, Candidate))
    { Client_Status(NSLOCTEXT("IBSkills", "SaveFailed", "Couldn't save this change. Your previous loadout is intact.")); return; }
    State = Candidate; Changed(); PS->ForceNetUpdate(); Client_Status(Success);
}
void UIBSkillComponent::Client_Status_Implementation(const FText& Message) { Status = Message; Changed(); }
void UIBSkillComponent::Changed() { OnChanged.Broadcast(); }
void UIBSkillComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UIBSkillComponent, State);
    DOREPLIFETIME(UIBSkillComponent, bReady);
}
