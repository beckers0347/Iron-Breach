#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "DamageableInterface.generated.h"

UINTERFACE(MinusType, Blueprintable)
class UDamageableInterface : public UInterface
{
	GENERATED_BODY()
};

class IRONBREACH_API IDamageableInterface
{
	GENERATED_BODY()

public:
	// BlueprintNativeEvent allows us to implement core logic in C++ but override/extend it in Blueprints
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Combat")
	void HandleTakeDamage(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser);
};