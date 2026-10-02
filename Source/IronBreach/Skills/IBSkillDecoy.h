#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Combat/DamageableInterface.h"
#include "Classes/IBClassKitTypes.h"
#include "IBSkillDecoy.generated.h"
class ACharacter;
class UCapsuleComponent;
class UPoseableMeshComponent;

/** A damageable, replicated echo. Only ordinary infantry AI gives it priority. */
UCLASS()
class IRONBREACH_API AIBSkillDecoy : public AActor, public IDamageableInterface
{
    GENERATED_BODY()
public:
    AIBSkillDecoy();
    static AIBSkillDecoy* Project(ACharacter* Source, const FIBKitAbilitySpec& Spec);
    float GetAttractionRadius() const { return AttractionRadius; }
    virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& Hit, AController* Instigator, AActor* Causer) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UFUNCTION() void OnRep_Source();
    void Finish();
    UPROPERTY() TObjectPtr<UCapsuleComponent> Capsule;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> Body;
    UPROPERTY(ReplicatedUsing=OnRep_Source) TObjectPtr<ACharacter> Source;
    float AttractionRadius = 1800;
    float Health = 80;
    FIBKitAbilitySpec Burst;
    FTimerHandle ExpireHandle;
    bool bFinished = false;
};
