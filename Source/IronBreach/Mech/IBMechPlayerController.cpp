#include "IBMechPlayerController.h"
#include "IBMech_Base.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Blueprint/UserWidget.h"
#include "UObject/ConstructorHelpers.h"

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

	// IBMechPlayerController.cpp — in BeginPlay(), or the constructor if you add one
	PlayerCameraManager->ViewPitchMin = -90.0f;
	PlayerCameraManager->ViewPitchMax = 90.0f;
	// IBMechPlayerController.cpp — in BeginPlay(), or the constructor if you add one
	PlayerCameraManager->ViewPitchMin = -90.0f;
	PlayerCameraManager->ViewPitchMax = 90.0f;
}

void AIBMechPlayerController::OnPossess(APawn* aPawn)
{
	Super::OnPossess(aPawn);

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(aPawn))
	{
		if (Mech->SeatSelectWidgetClass)
		{
			UUserWidget* SeatWidget = CreateWidget<UUserWidget>(this, Mech->SeatSelectWidgetClass);
			if (SeatWidget)
			{
				SeatWidget->AddToViewport();
				bShowMouseCursor = true;
				SetInputMode(FInputModeUIOnly());
			}
		}
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
		if (LookAction)
		{
			EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AIBMechPlayerController::HandleLook);
		}
		if (FireAction)
		{
			EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Started, this, &AIBMechPlayerController::HandleFire);
		}
		if (ADSAction)
		{
			EnhancedInputComponent->BindAction(ADSAction, ETriggerEvent::Started, this, &AIBMechPlayerController::HandleADS);
			EnhancedInputComponent->BindAction(ADSAction, ETriggerEvent::Completed, this, &AIBMechPlayerController::HandleADS);
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


void AIBMechPlayerController::HandleSwap(const FInputActionValue& Value)
{
	UE_LOG(LogTemp, Display, TEXT("PlayerController: 'F' key pressed, routing swap request to Mech..."));

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RequestRoleSwap(this);
	}
}

void AIBMechPlayerController::HandleLook(const FInputActionValue& Value)
{
	FVector2D LookAxisVector = Value.Get<FVector2D>();

	// 1. Handle Vertical Look (Pitch) locally on the controller/camera
	if (LookAxisVector.Y != 0.0f)
	{
		AddPitchInput(LookAxisVector.Y);
	}

	// 2. Route Horizontal Look (Yaw) to the possessed Mech pawn
	if (LookAxisVector.X != 0.0f)
	{
		if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
		{
			Mech->RouteLookInput(this, FVector2D(LookAxisVector.X, 0.0f));
		}
	}
}

void AIBMechPlayerController::HandleFire(const FInputActionValue& Value)
{
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->FireWeapon(this);
	}
}

void AIBMechPlayerController::HandleADS(const FInputActionValue& Value)
{
	bool bNewAimState = Value.Get<bool>();

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		if (UWeaponRigComponent* Rig = Mech->FindComponentByClass<UWeaponRigComponent>())
		{
			Rig->SetAiming(bNewAimState); // Calls the smooth ADS blend on your rig[cite: 3]
		}
	}
}