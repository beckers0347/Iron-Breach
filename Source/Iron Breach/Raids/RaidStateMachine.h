#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RaidStateMachine.generated.h"

// Define your strict 5-Phase Raid States
UENUM(BlueprintType)
enum class ERaidPhase : uint8
{
	ArmorBreak		UMETA(DisplayName = "Armor Break"),
	OrganDisable	UMETA(DisplayName = "Organ Disable"),
	MechDeploy		UMETA(DisplayName = "Mech Deploy"),
	TheClimb		UMETA(DisplayName = "The Climb"),
	FinalSync		UMETA(DisplayName = "Final Sync"),
	Completed		UMETA(DisplayName = "Completed")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRaidPhaseChangedSignature, ERaidPhase, NewPhase);

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class IRONBREACH_API URaidStateMachine : public UActorComponent
{
	GENERATED_BODY()

public:	
	URaidStateMachine();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Raid State")
	ERaidPhase CurrentPhase;

public:	
	UPROPERTY(BlueprintAssignable, Category = "Raid State|Events")
	FOnRaidPhaseChangedSignature OnPhaseChanged;

	UFUNCTION(BlueprintCallable, Category = "Raid State")
	void AdvanceRaidPhase();

	UFUNCTION(BlueprintPure, Category = "Raid State")
	ERaidPhase GetCurrentPhase() const { return CurrentPhase; }
};