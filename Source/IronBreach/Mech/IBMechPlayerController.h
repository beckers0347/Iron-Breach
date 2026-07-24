#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "InputActionValue.h"
#include "IBMechPlayerController.generated.h"

class UInputAction;
class UInputMappingContext;

UCLASS()
class IRONBREACH_API AIBMechPlayerController : public APlayerController
{
	GENERATED_BODY()

protected:
	virtual void SetupInputComponent() override;
	virtual void BeginPlay() override;
	virtual void OnPossess(APawn* aPawn) override;

public:
	// --- ENHANCED INPUT ASSETS ---
	UPROPERTY(EditAnywhere, Category = "Mech Input")
	UInputMappingContext* MechMappingContext;

	UPROPERTY(EditAnywhere, Category = "Mech Input")
	UInputAction* MoveAction;

	UPROPERTY(EditAnywhere, Category = "Mech Input")
	UInputAction* FireAction;

	UPROPERTY(EditAnywhere, Category = "Mech Input")
	UInputAction* SwapAction;

private:
	// --- INTERCEPT FUNCTIONS ---
	void HandleSwap(const FInputActionValue& Value);
	void HandleMove(const FInputActionValue& Value);
	void HandleFire(const FInputActionValue& Value);
};