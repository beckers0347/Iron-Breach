#include "Skills/IBSkillDecoy.h"
#include "Classes/IBKitZone.h"
#include "Components/CapsuleComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "GameFramework/Character.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"

AIBSkillDecoy::AIBSkillDecoy()
{
    bReplicates=true;
    Capsule=CreateDefaultSubobject<UCapsuleComponent>(TEXT("EchoCollision")); RootComponent=Capsule;
    Capsule->InitCapsuleSize(34,88); Capsule->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Capsule->SetCollisionObjectType(ECC_Pawn); Capsule->SetCollisionResponseToAllChannels(ECR_Ignore);
    Capsule->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block); Capsule->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    Body=CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("EchoBody")); Body->SetupAttachment(Capsule);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision); Body->SetCastShadow(false);
}
AIBSkillDecoy* AIBSkillDecoy::Project(ACharacter* InSource,const FIBKitAbilitySpec& Spec)
{
    if (!InSource || !InSource->HasAuthority()) { return nullptr; }
    UWorld* World=InSource->GetWorld();
    FVector Direction=InSource->GetControlRotation().Vector().GetSafeNormal2D();
    FVector Place=InSource->GetActorLocation()+Direction*Spec.Range;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(IBEcho),false,InSource); FHitResult Hit;
    if (World->LineTraceSingleByChannel(Hit,InSource->GetActorLocation(),Place,ECC_Visibility,Query))
    { Place=Hit.ImpactPoint-Direction*50; }
    if (World->LineTraceSingleByChannel(Hit,Place+FVector(0,0,120),Place-FVector(0,0,1500),ECC_Visibility,Query))
    { Place=Hit.ImpactPoint+FVector(0,0,90); }
    FActorSpawnParameters Params; Params.Owner=InSource; Params.Instigator=InSource;
    Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding;
    AIBSkillDecoy* Echo=World->SpawnActor<AIBSkillDecoy>(Place,InSource->GetActorRotation(),Params);
    if (!Echo) { return nullptr; }
    Echo->Source=InSource; Echo->AttractionRadius=Spec.Radius; Echo->Burst=Spec;
    Echo->OnRep_Source(); Echo->ForceNetUpdate();
    World->GetTimerManager().SetTimer(Echo->ExpireHandle,Echo,&AIBSkillDecoy::Finish,FMath::Max(.5f,Spec.Duration),false);
    return Echo;
}
void AIBSkillDecoy::OnRep_Source()
{
    if (!Source || !Source->GetMesh() || !Source->GetMesh()->GetSkeletalMeshAsset()) { return; }
    Body->SetSkeletalMesh(Source->GetMesh()->GetSkeletalMeshAsset());
    Body->SetRelativeTransform(Source->GetMesh()->GetRelativeTransform());
    Body->CopyPoseFromSkeletalComponent(Source->GetMesh());
    UMaterialInterface* Glow=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/IronBreach/Classes/M_IBKitZone.M_IBKitZone"));
    if (Glow) for (int32 I=0; I<Body->GetNumMaterials(); ++I)
    {
        UMaterialInstanceDynamic* Material=UMaterialInstanceDynamic::Create(Glow,this);
        Material->SetVectorParameterValue(TEXT("Color"),FLinearColor(.12,.65,1));
        Material->SetScalarParameterValue(TEXT("Glow"),2); Material->SetScalarParameterValue(TEXT("Opacity"),.55f);
        Body->SetMaterial(I,Material);
    }
}
void AIBSkillDecoy::HandleTakeDamage_Implementation(float DamageAmount,const FHitResult&,AController*,AActor*)
{
    if (!HasAuthority() || !FMath::IsFinite(DamageAmount) || DamageAmount<=0) { return; }
    Health-=DamageAmount; if (Health<=0) { Finish(); }
}
void AIBSkillDecoy::Finish()
{
    if (!HasAuthority() || bFinished) { return; } bFinished=true;
    if (Burst.bMarksTargets || Burst.SlowFactor<1)
    {
        Burst.Duration=5; Burst.Radius=650;
        FActorSpawnParameters Params; Params.Owner=Source; Params.Instigator=Source;
        if (AIBKitZone* Zone=GetWorld()->SpawnActor<AIBKitZone>(GetActorLocation()-FVector(0,0,88),FRotator::ZeroRotator,Params))
        { Zone->InitZone(Burst,FLinearColor(.12,.65,1),Source); }
    }
    Destroy();
}
void AIBSkillDecoy::EndPlay(const EEndPlayReason::Type Reason)
{ GetWorld()->GetTimerManager().ClearTimer(ExpireHandle); Super::EndPlay(Reason); }
void AIBSkillDecoy::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{ Super::GetLifetimeReplicatedProps(OutLifetimeProps); DOREPLIFETIME(AIBSkillDecoy,Source); }
