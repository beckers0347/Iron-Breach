#include "IBMech_Base.h"
#include "GameFramework/Controller.h"
#include "Engine/LocalPlayer.h"
#include "IBMechAIController.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Combat/WeaponRigComponent.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/CharacterMovementComponent.h"

AIBMech_Base::AIBMech_Base()
{
	PrimaryActorTick.bCanEverTick = true;
	
	LeftSeatController = nullptr;
	RightSeatController = nullptr;
	CurrentDriver = nullptr;
	CurrentGunner = nullptr;
	bIsGunner = false; // We start as the Driver by default

	// Mech mesh must be initialized first.
	MechMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("MechMesh"));
	MechMesh->SetupAttachment(GetCapsuleComponent());

	// Create the weapon rig component in C++ so it's always attached
	WeaponRigComponent = CreateDefaultSubobject<UWeaponRigComponent>(TEXT("WeaponRigComponent"));

	// --- Initialize Driver Views (3PV) ---

	DriverSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("DriverSpringArm"));
	DriverSpringArm->SetupAttachment(GetCapsuleComponent());
	DriverSpringArm->TargetArmLength = 400.0f; // Adjust to your preferred distance
	DriverSpringArm->bUsePawnControlRotation = true; // We want it locked to the chassis
	DriverSpringArm->bInheritYaw = true;
	DriverSpringArm->bInheritPitch = true;
	DriverSpringArm->bInheritRoll = false;

	DriverCamera_3PV = CreateDefaultSubobject<UCameraComponent>(TEXT("DriverCamera_3PV"));
	DriverCamera_3PV->SetupAttachment(DriverSpringArm, USpringArmComponent::SocketName);
	DriverCamera_3PV->bUsePawnControlRotation = false;

	// --- Initialize Gunner Views (FPV Cockpit) ---

	GunnerCamera_FPV = CreateDefaultSubobject<UCameraComponent>(TEXT("GunnerCamera_FPV"));
	GunnerCamera_FPV->SetupAttachment(MechMesh); // Attach directly to the head/body.

	// Position precisely: For example, +150 forward, +80 up relative to MechRoot.
	GunnerCamera_FPV->SetRelativeLocation(FVector(150.f, 0.f, 80.f));
	GunnerCamera_FPV->bUsePawnControlRotation = false; // Gunner will point the weapons[cite: 4], not the view.
}

void AIBMech_Base::BeginPlay()
{
	Super::BeginPlay();

	// Initially ensure Driver Camera is active.
	if (DriverCamera_3PV)
	{
		DriverCamera_3PV->Activate();
	}
	if (GunnerCamera_FPV)
	{
		GunnerCamera_FPV->Deactivate();
	}

	// Link the Weapon Rig (cite: 3) to the GUNNER camera.
	// This is crucial because the gunner poses the weapon model relative to the FPV view.
	if (WeaponRigComponent)
	{
		WeaponRigComponent->SetReferences(GunnerCamera_FPV, MechMesh); // [cite: 4]
	}

	// Spawn the AI Co-Pilot
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	// Create the AI brain in the world
	AIBMechAIController* CoPilot = GetWorld()->SpawnActor<AIBMechAIController>(AIBMechAIController::StaticClass(), GetActorLocation(), GetActorRotation(), SpawnParams);

	if (CoPilot)
	{
		// Force the AI into the Right Seat pointer manually
		// DO NOT call CoPilot->Possess(this) or it will kick the human out!
		AssignToRightSeat(CoPilot);

		UE_LOG(LogTemp, Display, TEXT("[Mech] AI successfully loaded into the Right Seat."));
	}

}

void AIBMech_Base::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Note: Because two controllers are sending input, we don't bind directly to the mech here 
	// the way we do with the infantry. Instead, the PlayerControllers will read the Enhanced Input 
	// and call RouteMoveInput() or RouteFireInput() on this possessed Mech.
}

// --- SEAT & ROLE MANAGEMENT ---

void AIBMech_Base::AssignToLeftSeat(AController* NewController)
{
	if (!NewController) return;
	LeftSeatController = NewController;

	if (!CurrentDriver)
	{
		CurrentDriver = LeftSeatController;
	}
	else if (!CurrentGunner) // <--- PUT THE 'ELSE' BACK!
	{
		CurrentGunner = LeftSeatController;
	}
}

void AIBMech_Base::AssignToRightSeat(AController* NewController)
{
	if (!NewController) return;
	RightSeatController = NewController;

	if (!CurrentDriver)
	{
		CurrentDriver = RightSeatController;
	}
	else if (!CurrentGunner) // <--- PUT THE 'ELSE' BACK!
	{
		CurrentGunner = RightSeatController;
	}
}

void AIBMech_Base::PerformRoleSwap()
{
	// Swap the pointers
	AController* Temp = CurrentDriver;
	CurrentDriver = CurrentGunner;
	CurrentGunner = Temp;

	UE_LOG(LogTemp, Log, TEXT("[Mech] Roles Swapped! Driver is now: %s"), 
		CurrentDriver ? *CurrentDriver->GetName() : TEXT("None"));

	bIsGunner = !bIsGunner;

	// Grab the character movement component safely
	UCharacterMovementComponent* MechMovement = GetCharacterMovement();

	// If we just swapped to the Gunner role:
	if (bIsGunner)
	{

		if (MechMovement)
		{
			MechMovement->bUseControllerDesiredRotation = false;
		}

		DriverCamera_3PV->Deactivate();
		GunnerCamera_FPV->Activate();
	}
	// If we just swapped back to the Driver role:
	else
	{

		if (MechMovement)
		{
			MechMovement->bUseControllerDesiredRotation = true;
		}

		GunnerCamera_FPV->SetActive(false);
		DriverCamera_3PV->SetActive(true);
	}

	if (APlayerController* PC = Cast<APlayerController>(CurrentGunner))
	{
		FRotator ResetRot = GetActorRotation();
		PC->SetControlRotation(ResetRot);
	}

	// ... (your existing camera swap code) ...

	// Tell the Blueprint that the swap just happened!
	OnRoleSwapped(bIsGunner);
}

// --- INPUT ROUTING (THE GATEKEEPER) ---

void AIBMech_Base::RouteMoveInput(AController* Requester, const FVector2D& InputValue)
{
	if (Requester != CurrentDriver) return;

	// If we are in the gunner seat, movement keys shouldn't drive the chassis 
	// (or you can allow them if you want a pilot/gunner hybrid setup). 
	// Assuming only the Driver moves the mech:
	if (bIsGunner) return;

	if (InputValue.Y != 0.0f)
	{
		AddMovementInput(GetActorForwardVector(), InputValue.Y);
	}

	if (InputValue.X != 0.0f)
	{
		AddMovementInput(GetActorRightVector(), InputValue.X);
	}
}

void AIBMech_Base::RouteFireInput(AController* RequestingController)
{
	// STRICT FILTER: Only the current gunner can fire the main weapons
	if (RequestingController != CurrentGunner)
	{
		return; // Ignore trigger pulls from the Driver
	}

	// Now check which side tank this gunner is sitting in
	if (RequestingController == LeftSeatController)
	{
		UE_LOG(LogTemp, Warning, TEXT("Firing LEFT side weapon systems! Building Left Heat."));
	}
	else if (RequestingController == RightSeatController)
	{
		UE_LOG(LogTemp, Warning, TEXT("Firing RIGHT side weapon systems! Building Right Heat."));
	}
}

void AIBMech_Base::RequestRoleSwap(AController* Requester)
{
	// Check if the requester is actually sitting in the mech
	if (Requester != LeftSeatController && Requester != RightSeatController) return;

	AController* CoPilot = (Requester == LeftSeatController) ? RightSeatController : LeftSeatController;

	// If the co-pilot is an AI, they auto-accept the swap. 
	// (Later, we will add human-to-human pending logic here)
	if (Cast<AAIController>(CoPilot))
	{
		UE_LOG(LogTemp, Display, TEXT("[Mech] Swap requested by Human. AI Co-pilot auto-accepting."));
		PerformRoleSwap();
	}
}

void AIBMech_Base::RouteLookInput(AController* Requester, const FVector2D& InputValue)
{
	if (Requester != CurrentDriver && Requester != CurrentGunner) return;

	if (bIsGunner)
	{
		APlayerController* PC = Cast<APlayerController>(Requester);
		if (!PC) return;

		if (InputValue.X != 0.0f)
		{
			FRotator CurrentControlRot = PC->GetControlRotation();
			float MechYaw = GetActorRotation().Yaw;

			// How far the view currently is from the mech's forward, normalized to -180..180
			float CurrentDeltaYaw = FMath::UnwindDegrees(CurrentControlRot.Yaw - MechYaw);

			// Apply the input, then clamp the result to +/-90 from center
			float NewDeltaYaw = FMath::Clamp(CurrentDeltaYaw + InputValue.X, -90.0f, 90.0f);

			CurrentControlRot.Yaw = MechYaw + NewDeltaYaw;
			PC->SetControlRotation(CurrentControlRot);
		}

		if (InputValue.Y != 0.0f)
		{
			AddControllerPitchInput(InputValue.Y);
		}
	}
	else
	{
		// DRIVER MODE — unchanged, free look
		if (InputValue.X != 0.0f)
		{
			AddControllerYawInput(InputValue.X);
		}
		if (InputValue.Y != 0.0f)
		{
			AddControllerPitchInput(InputValue.Y);
		}
	}
}

void AIBMech_Base::FireWeapon(AController* Requester)
{
	if (Requester != CurrentDriver) return;
	if (!CurrentWeaponData) return;

	// Perform the hit scan trace
	PerformWeaponTrace();

	// Debug message
	if (GEngine)
	{
		FString Msg = FString::Printf(TEXT("Firing %s! Damage: %.1f"), *CurrentWeaponData->WeaponName.ToString(), CurrentWeaponData->BaseDamage);
		GEngine->AddOnScreenDebugMessage(-1, 2.0f, FColor::Red, Msg);
	}
}

// Example: When equipping your weapon asset
void AIBMech_Base::EquipWeapon(UWeaponDataAsset* NewWeaponData)
{
	if (!NewWeaponData) return;

	// Cache or apply stats from your weapon asset
	CurrentWeaponData = NewWeaponData;

	// Pass the ADS configuration directly to your existing WeaponRigComponent!
	if (WeaponRigComponent)
	{
		WeaponRigComponent->SetAdsSettings(NewWeaponData->Ads);
	}
}

void AIBMech_Base::PerformWeaponTrace()
{
	if (!Controller) return;

	// Get the player's camera view point (origin and direction)
	FVector CamLoc;
	FRotator CamRot;
	Controller->GetPlayerViewPoint(CamLoc, CamRot);

	// Calculate trace start and end using the weapon data's MaxRange
	const float Range = CurrentWeaponData ? CurrentWeaponData->MaxRange : 5000.0f;
	FVector StartTrace = CamLoc;
	FVector EndTrace = StartTrace + (CamRot.Vector() * Range);

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this); // Don't shoot ourselves

	// Execute line trace against the world
	bool bHit = GetWorld()->LineTraceSingleByChannel(
		HitResult,
		StartTrace,
		EndTrace,
		ECC_Visibility,
		QueryParams
	);

	if (bHit)
	{
		// Draw a temporary debug line and point to verify hits in editor
		DrawDebugLine(GetWorld(), StartTrace, HitResult.Location, FColor::Cyan, false, 1.0f, 0, 1.5f);
		DrawDebugPoint(GetWorld(), HitResult.Location, 10.0f, FColor::Red, false, 1.0f);

		// If we hit an actor, apply damage using your weapon data base damage
		if (AActor* HitActor = HitResult.GetActor())
		{
			// Example: Apply standard engine damage
			// UGameplayStatics::ApplyDamage(HitActor, CurrentWeaponData->BaseDamage, Controller, this, UDamageType::StaticClass());
		}
	}
}

void AIBMech_Base::ToggleViewMode()
{
	bIsDriverActive = !bIsDriverActive;

	if (!DriverCamera_3PV || !GunnerCamera_FPV) return;

	if (bIsDriverActive)
	{
		// Activate Driver 3PV
		DriverCamera_3PV->Activate();
		GunnerCamera_FPV->Deactivate();

		// Hide Gunner minimalist crosshair
		if (CockpitCrosshairInstance)
		{
			CockpitCrosshairInstance->SetVisibility(ESlateVisibility::Hidden);
		}
	}
	else
	{
		// Activate Gunner FPV
		GunnerCamera_FPV->Activate();
		DriverCamera_3PV->Deactivate();

		// Ensure the Gunner minimalist UI overlay is visible.
		if (CockpitCrosshairClass)
		{
			if (!CockpitCrosshairInstance)
			{
				if (APlayerController* PC = Cast<APlayerController>(GetController()))
				{
					CockpitCrosshairInstance = CreateWidget<UUserWidget>(PC, CockpitCrosshairClass);
					CockpitCrosshairInstance->AddToViewport(10); // High Z-Order for HUD.
				}
			}

			if (CockpitCrosshairInstance)
			{
				CockpitCrosshairInstance->SetVisibility(ESlateVisibility::Visible);
			}
		}
	}
}