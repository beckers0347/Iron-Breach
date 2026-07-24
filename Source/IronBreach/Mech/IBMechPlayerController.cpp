#include "IBMechPlayerController.h"
#include "IBMech_Base.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"

void AIBMechPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// Add the Input Mapping Context
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (MechMappingContext)
		{
			Subsystem->AddMappingContext(MechMappingContext, 0);
		}
	}
}

void AIBMechPlayerController::OnPossess(APawn* aPawn)
{
	Super::OnPossess(aPawn);

	// Automatically assign this human player to the Left Seat upon possession
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(aPawn))
	{
		Mech->AssignToLeftSeat(this);
	}
}

void AIBMechPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent))
	{
		if (MoveAction)
		{
			EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AIBMechPlayerController::HandleMove);
		}
		if (FireAction)
		{
			EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Started, this, &AIBMechPlayerController::HandleFire);
		}
		if (SwapAction)
		{
			EnhancedInputComponent->BindAction(SwapAction, ETriggerEvent::Started, this, &AIBMechPlayerController::HandleSwap);
		}
	}
}

void AIBMechPlayerController::HandleMove(const FInputActionValue& Value)
{
	// Extract the 2D Axis data from the WASD keys
	FVector2D MoveVector = Value.Get<FVector2D>();

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RouteMoveInput(this, MoveVector);
	}
}

void AIBMechPlayerController::HandleFire(const FInputActionValue& Value)
{
	UE_LOG(LogTemp, Display, TEXT("PlayerController: Mouse clicked, routing to Mech..."));

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RouteFireInput(this);
	}
}

void AIBMechPlayerController::HandleSwap(const FInputActionValue& Value)
{
	UE_LOG(LogTemp, Display, TEXT("PlayerController: 'F' key pressed, routing swap request to Mech..."));

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RequestRoleSwap(this);
	}
}