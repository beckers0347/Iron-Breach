#include "CoreMinimal.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Algo/Reverse.h"
#include "Skills/IBSkillTypes.h"
#include "Skills/IBSkillSave.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIBSkillRulesTest,"IronBreach.Skills.ProgressionAndSaves",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FIBSkillRulesTest::RunTest(const FString&)
{
    FText Error; TSet<FName> Ids;
    for (const FIBSkillNode& N:IBSkills::Catalog())
    {
        TestFalse(TEXT("Stable node IDs are unique"),Ids.Contains(N.Id)); Ids.Add(N.Id);
        TestTrue(TEXT("Every node has a usable live effect"),N.Spec.IsUsable());
        TestTrue(TEXT("Node fits constellation bounds"),N.Position.X>.02 && N.Position.X<.98 && N.Position.Y>.02 && N.Position.Y<.98);
        if (!N.Parent.IsNone())
        {
            const FIBSkillNode* P=IBSkills::Find(N.Parent);
            TestTrue(TEXT("Variant parent matches class and slot kind"),P && P->Class==N.Class && P->Kind==N.Kind && P->Parent.IsNone());
        }
    }
    TestEqual(TEXT("Three classes, fifteen choices each"),Ids.Num(),45);
    for (auto Class:{EIBOperativeClass::Breaker,EIBOperativeClass::Picket,EIBOperativeClass::Bellringer})
    {
        FIBSkillState State=IBSkills::StarterState(Class);
        TestEqual(TEXT("Four loadout slots"),State.Equipped.Num(),4);
        TestEqual(TEXT("Starter kit has three unlocked abilities"),State.Unlocked.Num(),3);
        TestTrue(TEXT("Overdrive starts empty"),State.Equipped[3].IsNone());
        TestEqual(TEXT("No points at level one"),IBSkills::PointsAvailable(State,1),0);
        TestEqual(TEXT("Forty-nine points at level fifty"),IBSkills::PointsAvailable(State,50),49);
        TestEqual(TEXT("No extra points above cap"),IBSkills::PointsAvailable(State,1000),49);
        for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class && N.Cost>0)
            TestTrue(TEXT("Full class catalog can unlock within earned budget"),IBSkills::Unlock(State,Class,50,N.Id,Error));
        TestTrue(TEXT("Fully unlocked save sanitizes without loss"),IBSkills::Sanitize(State,Class,50)==State);
        TestTrue(TEXT("A lower-level restore repairs overspending"),IBSkills::Sanitize(State,Class,1)==IBSkills::StarterState(Class));
    }
    auto State=IBSkills::StarterState(EIBOperativeClass::Bellringer);
    TestFalse(TEXT("Reject another class"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,50,TEXT("guardian.parry"),Error));
    TestFalse(TEXT("Reject unknown IDs"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,50,TEXT("invented"),Error));
    TestFalse(TEXT("Enforce required level"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,2,TEXT("saber.long"),Error));
    TestFalse(TEXT("Enforce parent before variant"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,50,TEXT("saber.afterburn"),Error));
    TestTrue(TEXT("Spend two points"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,3,TEXT("saber.long"),Error));
    TestEqual(TEXT("Purchase deducts points once"),IBSkills::PointsAvailable(State,3),0);
    TestFalse(TEXT("Duplicate unlock rejected"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,3,TEXT("saber.long"),Error));
    auto Budget=State;
    IBSkills::Unlock(Budget,EIBOperativeClass::Bellringer,50,TEXT("saber.return"),Error);
    TestFalse(TEXT("Insufficient balance rejected independently of level gate"),IBSkills::Unlock(Budget,EIBOperativeClass::Bellringer,7,TEXT("saber.line"),Error));
    TestTrue(TEXT("Variant replaces its signature"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.long"),EIBSkillSlot::Signature,Error));
    TestFalse(TEXT("Wrong slot rejected"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.long"),EIBSkillSlot::Overdrive,Error));
    TestFalse(TEXT("Out-of-range slot rejected"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.long"),static_cast<EIBSkillSlot>(255),Error));
    TestFalse(TEXT("Locked ability cannot equip"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.line"),EIBSkillSlot::TacticalOne,Error));
    TestFalse(TEXT("Same ability cannot fill two tacticals"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.breach"),EIBSkillSlot::TacticalTwo,Error));
    TestTrue(TEXT("Unlock tactical variant"),IBSkills::Unlock(State,EIBOperativeClass::Bellringer,50,TEXT("saber.fan"),Error));
    TestFalse(TEXT("Two variants of one ability cannot fill two slots"),IBSkills::Equip(State,EIBOperativeClass::Bellringer,TEXT("saber.fan"),EIBSkillSlot::TacticalTwo,Error));
    auto Swapped=State; Swap(Swapped.Equipped[1],Swapped.Equipped[2]);
    TestTrue(TEXT("Restore preserves tactical order"),IBSkills::Sanitize(Swapped,EIBOperativeClass::Bellringer,50)==Swapped);
    auto Broken=State; Broken.Unlocked.Add(TEXT("invented")); Broken.Unlocked.Add(TEXT("guardian.parry")); Broken.Unlocked.Add(TEXT("saber.long")); Broken.Equipped[2]=Broken.Equipped[1];
    TestTrue(TEXT("Restore repairs bad IDs and duplicated tactical without an empty starter slot"),IBSkills::Sanitize(Broken,EIBOperativeClass::Bellringer,50)==State);
    auto Reversed=State; Algo::Reverse(Reversed.Unlocked);
    auto Clean=IBSkills::Sanitize(Reversed,EIBOperativeClass::Bellringer,50);
    TestEqual(TEXT("Restore handles variants appearing before parents"),Clean.Unlocked.Num(),State.Unlocked.Num());
    UIBSkillSave* Save=NewObject<UIBSkillSave>(); Save->Operatives.Add(TEXT("host/a/operative-1"),State); Save->Operatives.Add(TEXT("host/b/operative-1"),IBSkills::StarterState(EIBOperativeClass::Picket));
    TArray<uint8> Bytes; TestTrue(TEXT("Serialize skill save"),UGameplayStatics::SaveGameToMemory(Save,Bytes));
    UIBSkillSave* Loaded=Cast<UIBSkillSave>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestTrue(TEXT("Save round trip preserves unlocks and equipped variants"),Loaded && Loaded->Operatives.Contains(TEXT("host/a/operative-1")) && Loaded->Operatives[TEXT("host/a/operative-1")]==State);
    TestTrue(TEXT("Players' records stay separate"),Loaded && Loaded->Operatives[TEXT("host/b/operative-1")]==IBSkills::StarterState(EIBOperativeClass::Picket));
    return true;
}
#endif
