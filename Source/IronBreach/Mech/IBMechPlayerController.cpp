#include "IBMechPlayerController.h"
#include "IBMech_Base.h"
#include "IBGunnerSeat.h"
#include "IronBreach.h"
#include "Combat/WeaponRigComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Camera/PlayerCameraManager.h"
#include "Blueprint/UserWidget.h"

void AIBMechPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (MechMappingContext)
		{
			Subsystem->AddMappingContext(MechMappingContext, 0);
		}
	}

	// Guarded: a controller whose camera manager hasn't spawned yet (or a non-local
	// controller on the server) crashes on an unguarded dereference here.
	if (PlayerCameraManager)
	{
		PlayerCameraManager->ViewPitchMin = -90.0f;
		PlayerCameraManager->ViewPitchMax = 90.0f;
	}
	else
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[MechPC] No PlayerCameraManager at BeginPlay; pitch limits not applied."));
	}
}

void AIBMechPlayerController::OnPossess(APawn* aPawn)
{
	Super::OnPossess(aPawn);

	AIBMech_Base* Mech = Cast<AIBMech_Base>(aPawn);
	if (!Mech) return; // gunner-seat possession needs no widget

	// OnPossess runs on the authority for EVERY controller, including remote ones that
	// have no LocalPlayer. CreateWidget in that situation is a known crash surface, and
	// SetInputMode on a remote controller is meaningless. Local controllers only.
	if (!IsLocalController()) return;

	// The BP seat-select flow (widget buttons -> ChooseSeat, then Possess) seats us BEFORE
	// possession. In that case the choice is already made — don't pop a second menu or
	// force a different seat on top of it.
	if (Mech->IsControllerSeated(this))
	{
		Mech->ApplyLocalViewForRole(this);
		return;
	}

	if (!Mech->SeatSelectWidgetClass)
	{
		// No menu wired: seat straight into the helm rather than leaving the player roleless.
		Mech->ChooseSeat(this, /*bWantLeftSeat=*/true);
		return;
	}

	UUserWidget* SeatWidget = CreateWidget<UUserWidget>(this, Mech->SeatSelectWidgetClass);
	if (!SeatWidget)
	{
		// Never leave the player in UIOnly input mode with no UI — that reads as a hard lock.
		UE_LOG(LogIronBreach, Error, TEXT("[MechPC] Seat-select widget failed to create; seating into the left seat instead."));
		Mech->ChooseSeat(this, /*bWantLeftSeat=*/true);
		return;
	}

	SeatWidget->AddToViewport();
	bShowMouseCursor = true;
	SetInputMode(FInputModeUIOnly());
}

void AIBMechPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent);
	if (!EnhancedInputComponent)
	{
		UE_LOG(LogIronBreach, Error, TEXT("[MechPC] Expected an EnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini"));
		return;
	}

	if (MoveAction)
	{
		EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AIBMechPlayerController::HandleMove);
	}
	if (LookAction)
	{
		EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AIBMechPlayerController::HandleLook);
	}
	if (SwapAction)
	{
		EnhancedInputComponent->BindAction(SwapAction, ETriggerEvent::Started, this, &AIBMechPlayerController::HandleSwap);
	}
	// Bound once — a second binding here is a double shot per trigger pull.
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

void AIBMechPlayerController::HandleMove(const FInputActionValue& Value)
{
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RouteMoveInput(this, Value.Get<FVector2D>());
	}
	// Gunner seat: movement keys do nothing — the navigator drives.
}

void AIBMechPlayerController::HandleSwap(const FInputActionValue& Value)
{
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RequestRoleSwap(this);
	}
	else if (AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(GetPawn()))
	{
		Seat->RequestSwap();
	}
}

void AIBMechPlayerController::HandleLook(const FInputActionValue& Value)
{
	// Route the whole 2D vector and let the pawn own it — the mech is the only place
	// that knows whether this controller is driving or gunning, and the seat owns its
	// own clamped turret look.
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->RouteLookInput(this, Value.Get<FVector2D>());
	}
	else if (AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(GetPawn()))
	{
		Seat->ProcessLook(Value.Get<FVector2D>());
	}
}

void AIBMechPlayerController::HandleFire(const FInputActionValue& Value)
{
	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		Mech->FireWeapon(this);
	}
	else if (AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(GetPawn()))
	{
		Seat->HandleFirePressed();
	}
}

void AIBMechPlayerController::HandleADS(const FInputActionValue& Value)
{
	const bool bNewAimState = Value.Get<bool>();

	if (AIBMech_Base* Mech = Cast<AIBMech_Base>(GetPawn()))
	{
		if (UWeaponRigComponent* Rig = Mech->WeaponRigComponent)
		{
			Rig->SetAiming(bNewAimState);
		}
	}
	else if (AIBGunnerSeat* Seat = Cast<AIBGunnerSeat>(GetPawn()))
	{
		Seat->SetAiming(bNewAimState);
	}
}
