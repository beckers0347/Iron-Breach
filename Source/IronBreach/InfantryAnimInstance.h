#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "InfantryAnimInstance.generated.h"

UCLASS()
class IRONBREACH_API UInfantryAnimInstance : public UAnimInstance
{
    GENERATED_BODY()

public:
    // This is the C++ version of the "Event Blueprint Update Animation" node
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;

    // This exposes the variable to your visual AnimGraph
    UPROPERTY(BlueprintReadOnly, Category = "Combat State")
    bool bIsHoldingGun;

    // Tracks how fast the character is currently moving
    UPROPERTY(BlueprintReadOnly, Category = "Combat State")
    float MovementSpeed;

};