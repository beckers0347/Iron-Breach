// Explicit development checks. Uses temporary actors far outside the playable area;
// never changes the user's XP, unlocks, equipment, or saved roster.
#include "CoreMinimal.h"
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "Skills/IBSkillTypes.h"
#include "Skills/IBSkillComponent.h"
#include "Skills/IBSkillDecoy.h"
#include "Classes/IBOperativeKitComponent.h"
#include "Classes/IBKitZone.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Enemy/IBCharacter_Enemy.h"
#include "Enemy/IBEnemyAIController.h"
#include "Combat/HealthComponent.h"
#include "Items/IBPlayerState.h"
#include "UI/IBSkillsScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "Player/IBOperativePreviewStage.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "TimerManager.h"
#include "Misc/Paths.h"
#include "Framework/Application/SlateApplication.h"
#include "IronBreach.h"

namespace IBSkillCheck
{
void Check(bool OK,const TCHAR* Message) { UE_LOG(LogIronBreach,Display,TEXT("[SkillsCheck] %s %s"),OK ? TEXT("PASS") : TEXT("FAIL"),Message); }
void Key(FKey K)
{
    FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(K,FModifierKeysState(),0,false,0,0));
    FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(K,FModifierKeysState(),0,false,0,0));
}
void Shot(const TCHAR* Name) { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("SkillsSystem/after")/Name,true,false); }
}
struct FIBSkillCombatCheck
{
static void Run(UWorld* World)
{
    using IBSkillCheck::Check;
    if (!World || World->GetNetMode()==NM_Client) { return; }
    TArray<AActor*> Spawned;
    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const FVector Origin(-180000,-180000,5000);
    AIBCharacter_Infantry* Owner=World->SpawnActor<AIBCharacter_Infantry>(Origin,FRotator::ZeroRotator,Params);
    AIBCharacter_Infantry* Ally=World->SpawnActor<AIBCharacter_Infantry>(Origin+FVector(0,220,0),FRotator::ZeroRotator,Params);
    AIBCharacter_Enemy* Enemy=World->SpawnActor<AIBCharacter_Enemy>(Origin+FVector(220,0,0),FRotator::ZeroRotator,Params);
    APlayerController* Controller=World->SpawnActor<APlayerController>();
    if (!Owner || !Ally || !Enemy || !Controller) { Check(false,TEXT("temporary combat actors")); if (Owner) Owner->Destroy(); if (Ally) Ally->Destroy(); if (Enemy) Enemy->Destroy(); if (Controller) Controller->Destroy(); return; }
    Spawned={Owner,Ally,Enemy,Controller}; if (Enemy->GetController()) { Spawned.Add(Enemy->GetController()); }
    Controller->Possess(Owner);
    Owner->GetCharacterMovement()->SetMovementMode(MOVE_None); Ally->GetCharacterMovement()->SetMovementMode(MOVE_None);
    UIBOperativeKitComponent* Kit=Owner->FindComponentByClass<UIBOperativeKitComponent>();
    UIBOperativeKitComponent* AllyKit=Ally->FindComponentByClass<UIBOperativeKitComponent>();
    UHealthComponent* Health=Owner->FindComponentByClass<UHealthComponent>();
    UHealthComponent* EnemyHealth=Enemy->FindComponentByClass<UHealthComponent>();
    auto Execute=[&](const TCHAR* Id)
    { Kit->SlotSpecs.SetNum(4); Kit->SlotSpecs[0]=IBSkills::Find(Id)->Spec; Kit->ExecuteEffect(EIBSkillSlot::Signature); };
    Execute(TEXT("guardian.guard"));
    const float Before=Health->GetHealthPercent();
    Owner->HandleTakeDamage_Implementation(50,FHitResult(),nullptr,Enemy);
    Check(FMath::IsNearlyEqual(Health->GetHealthPercent(),Before-.1f),TEXT("guard reduces an actual incoming hit"));
    Check(FMath::IsNearlyEqual(Kit->GetGuardEnergy(),40.f),TEXT("absorbed damage stores guard energy"));
    const float EnemyBefore=EnemyHealth->GetHealthPercent();
    Execute(TEXT("guardian.impact"));
    Check(EnemyHealth->GetHealthPercent()<EnemyBefore,TEXT("impact damages a hostile"));
    Check(Kit->GetGuardEnergy()==0,TEXT("impact consumes stored energy once"));
    Check(Ally->FindComponentByClass<UHealthComponent>()->GetHealthPercent()==1.f,TEXT("shockwave spares the fireteam"));
    Kit->RecordGuardedDamage(1000);
    Check(Kit->GetGuardEnergy()==100.f,TEXT("guard energy is capped"));

    AIBKitZone* Ward=World->SpawnActor<AIBKitZone>(Origin,FRotator::ZeroRotator,Params); Spawned.Add(Ward);
    Ward->InitZone(IBSkills::Find(TEXT("guardian.surge"))->Spec,FLinearColor::White,Owner); Ward->Pulse();
    Check(FMath::IsNearlyEqual(AllyKit->GetDamageTakenScale(),.65f),TEXT("protective surge covers nearby infantry"));
    Check(FMath::IsNearlyEqual(Kit->GetDamageTakenScale(),.2f),TEXT("weaker ward cannot replace a timed guard"));

    AIBEnemyAIController* AI=Cast<AIBEnemyAIController>(Enemy->GetController());
    if (AI)
    {
        AI->TargetActor=Owner; AI->LastSeenTime=World->GetTimeSeconds();
        Execute(TEXT("sentinel.veil")); AI->Tick(.01f);
        Check(Kit->IsConcealed() && AI->TargetActor!=Owner,TEXT("veil breaks ordinary AI tracking"));
        Kit->NotifyAttack(); Check(!Kit->IsConcealed(),TEXT("attacking breaks concealment"));
        AIBSkillDecoy* Echo=AIBSkillDecoy::Project(Owner,IBSkills::Find(TEXT("sentinel.decoy"))->Spec);
        Check(Echo!=nullptr,TEXT("decoy projects a damageable echo"));
        if (Echo)
        {
            Spawned.Add(Echo); AI->TargetActor=Owner; AI->Tick(.01f);
            Check(AI->TargetActor==Echo,TEXT("visible echo takes ordinary AI attention"));
            Echo->HandleTakeDamage_Implementation(100,FHitResult(),Controller,Owner);
            Check(Echo->IsActorBeingDestroyed(),TEXT("enemy fire can destroy the echo"));
        }
        AIBKitZone* Sensor=World->SpawnActor<AIBKitZone>(Origin,FRotator::ZeroRotator,Params); Spawned.Add(Sensor);
        Sensor->InitZone(IBSkills::Find(TEXT("sentinel.pin"))->Spec,FLinearColor::White,Owner);
        Sensor->Pulse(); Check(Sensor->GetMarkedTargets().Contains(Enemy),TEXT("sensor provides a visible HUD tracking target"));
        AI->SetMaxWalkSpeed(600); Check(FMath::IsNearlyEqual(Enemy->GetCharacterMovement()->MaxWalkSpeed,270.f),TEXT("sensor slow survives AI speed updates"));
        ACharacter* Walker=World->SpawnActor<ACharacter>(Origin+FVector(100,100,0),FRotator::ZeroRotator,Params); Spawned.Add(Walker);
        Walker->GetCharacterMovement()->MaxWalkSpeed=600;
        AIBKitZone* WeakSensor=World->SpawnActor<AIBKitZone>(Origin,FRotator::ZeroRotator,Params); Spawned.Add(WeakSensor);
        FIBKitAbilitySpec WeakSpec=IBSkills::Find(TEXT("sentinel.pin"))->Spec; WeakSpec.SlowFactor=.7f;
        WeakSensor->InitZone(WeakSpec,FLinearColor::White,Owner);
        WeakSensor->Pulse(); Sensor->Pulse();
        Check(FMath::IsNearlyEqual(Walker->GetCharacterMovement()->MaxWalkSpeed,270.f),TEXT("overlapping slows use the strongest effect on other walking targets"));
        Sensor->Destroy(); AI->SetMaxWalkSpeed(600);
        Check(FMath::IsNearlyEqual(Walker->GetCharacterMovement()->MaxWalkSpeed,420.f) && FMath::IsNearlyEqual(Enemy->GetCharacterMovement()->MaxWalkSpeed,420.f),TEXT("expiring a strong field retains a weaker field"));
        WeakSensor->Destroy(); AI->SetMaxWalkSpeed(600);
        Check(FMath::IsNearlyEqual(Walker->GetCharacterMovement()->MaxWalkSpeed,600.f) && FMath::IsNearlyEqual(Enemy->GetCharacterMovement()->MaxWalkSpeed,600.f),TEXT("speed recovers after all sensor fields expire"));
    }
    else { Check(false,TEXT("temporary enemy AI")); }

    // Re-equipping cannot erase either the slot's or the ability's recovery.
    Kit->AppliedSkills=IBSkills::StarterState(EIBOperativeClass::Bellringer);
    Kit->SlotReadyTime[1]=Kit->Now()+12;
    Kit->AbilityReadyTime.Add(TEXT("saber.breach"),Kit->Now()+12);
    Swap(Kit->AppliedSkills.Equipped[1],Kit->AppliedSkills.Equipped[2]);
    Check(Kit->GetSlotCooldown(EIBSkillSlot::TacticalOne)>11 && Kit->GetSlotCooldown(EIBSkillSlot::TacticalTwo)>11,TEXT("swapping slots preserves ability recovery"));
    Kit->ReturnAnchor=Origin; Kit->ReturnUntil=Kit->Now()+3;
    Owner->SetActorLocation(Origin+FVector(0,-200,0));
    Check(Kit->TryReturn() && Owner->GetActorLocation().Equals(Origin,1),TEXT("return vector restores a clear anchor"));
    Kit->ReturnAnchor=Ally->GetActorLocation(); Kit->ReturnUntil=Kit->Now()+3;
    Check(!Kit->TryReturn(),TEXT("return vector rejects an occupied anchor"));
    Kit->ReturnUntil=Kit->Now()-1; Check(!Kit->TryReturn(),TEXT("return vector expires"));
    for (AActor* A:Spawned) if (IsValid(A)) { A->Destroy(); }
    // Any delayed ability timers belong to the destroyed component and are cleared on EndPlay.
}
};

namespace IBSkillCheck
{
static FAutoConsoleCommandWithWorld Command(TEXT("IB.SkillsCheck"),TEXT("Check class effects and Skills UI without changing progression."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
    APlayerController* PC=World ? World->GetFirstPlayerController() : nullptr;
    UIBMenuSubsystem* Menu=PC && PC->GetLocalPlayer() ? PC->GetLocalPlayer()->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    if (!Menu) { return; }
    const AIBPlayerState* PS=PC->GetPlayerState<AIBPlayerState>();
    Check(PS && PS->Skills && PS->Skills->IsReady(),TEXT("deployed player has replicated skill state"));
    Check(PS && PS->Skills && !PS->Skills->CanRefund(),TEXT("mission rejects a Bastion refund"));
    FIBSkillCombatCheck::Run(World);
    TWeakObjectPtr<UIBMenuSubsystem> M(Menu); TWeakObjectPtr<UWorld> W(World);
    auto At=[World](float Time,TFunction<void()> Fn) { FTimerHandle H; World->GetTimerManager().SetTimer(H,FTimerDelegate::CreateLambda(MoveTemp(Fn)),Time,false); };
    At(1,[M] { if (M.IsValid()) { M->OpenScreen(TEXT("Skills")); } });
    At(3,[M] { Check(M.IsValid() && Cast<UIBSkillsScreen>(M->GetActiveScreen()),TEXT("Skills opens from registered navigation")); Shot(TEXT("skills-starter.png")); });
    At(5,[M]
    {
        UIBSkillsScreen* S=M.IsValid() ? Cast<UIBSkillsScreen>(M->GetActiveScreen()) : nullptr;
        if (!S) { return; } const FIBSkillNode* Selected=IBSkills::Find(S->GetSelectedNode());
        if (Selected) for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Selected->Class && N.Kind==EIBSkillKind::Overdrive && N.Parent.IsNone()) { S->SelectNode(N.Id); break; }
    });
    At(7,[] { Shot(TEXT("skills-locked-overdrive.png")); });
    At(8,[] { Key(EKeys::Right); });
    At(9,[M]
    {
        UIBSkillsScreen* S=M.IsValid() ? Cast<UIBSkillsScreen>(M->GetActiveScreen()) : nullptr;
        const FIBSkillNode* N=S ? IBSkills::Find(S->GetSelectedNode()) : nullptr;
        Check(N && !N->Parent.IsNone(),TEXT("arrow input selects a constellation variant")); Shot(TEXT("skills-variant.png"));
    });
    At(10,[] { Key(EKeys::Escape); });
    At(11,[M,W]
    {
        Check(M.IsValid() && !M->IsMenuOpen(),TEXT("Escape closes Skills"));
        int32 Count=0; if (W.IsValid()) for (TActorIterator<AIBOperativePreviewStage> It(W.Get()); It; ++It) { ++Count; }
        Check(Count==0,TEXT("Skills releases its portrait stage")); Key(EKeys::K);
    });
    At(13,[M] { Check(M.IsValid() && M->GetActiveScreenId()==TEXT("Skills"),TEXT("K opens Skills in game")); Shot(TEXT("skills-final.png")); Check(true,TEXT("COMPLETE")); });
}));
}
#endif
