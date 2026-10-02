#include "Skills/IBSkillSave.h"
#include "Kismet/GameplayStatics.h"
#include "IronBreach.h"

namespace { const TCHAR* IBSkillSaveSlotName = TEXT("IronBreach_Skills"); }
void UIBSkillSaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    if (UGameplayStatics::DoesSaveGameExist(IBSkillSaveSlotName, 0))
    {
        Save = Cast<UIBSkillSave>(UGameplayStatics::LoadGameFromSlot(IBSkillSaveSlotName, 0));
        // Preserve an unreadable or newer file instead of overwriting a career.
        bCanWrite = Save && Save->Version == 1;
        if (!bCanWrite) { UE_LOG(LogIronBreach, Error, TEXT("Skills: save unavailable or newer than this build; file preserved.")); }
    }
    if (!Save) { Save = NewObject<UIBSkillSave>(this); }
}
const FIBSkillState* UIBSkillSaveSubsystem::Find(const FString& Key) const
{
    return Save ? Save->Operatives.Find(Key) : nullptr;
}
bool UIBSkillSaveSubsystem::Store(const FString& Key, const FIBSkillState& State)
{
    if (!bCanWrite || !Save || Key.IsEmpty()) { return false; }
    const FIBSkillState* Previous = Save->Operatives.Find(Key);
    const TOptional<FIBSkillState> Backup = Previous ? TOptional<FIBSkillState>(*Previous) : TOptional<FIBSkillState>();
    Save->Operatives.Add(Key, State);
    if (UGameplayStatics::SaveGameToSlot(Save, IBSkillSaveSlotName, 0)) { return true; }
    if (Backup.IsSet()) { Save->Operatives.Add(Key, Backup.GetValue()); } else { Save->Operatives.Remove(Key); }
    UE_LOG(LogIronBreach, Warning, TEXT("Skills: save failed; purchase/equipment change rolled back."));
    return false;
}
