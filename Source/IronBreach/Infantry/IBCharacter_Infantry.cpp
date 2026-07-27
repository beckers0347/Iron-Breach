#include "IBCharacter_Infantry.h"
#include "IronBreach.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h" // Explicit include: required for ULocalPlayer::GetSubsystem under IWYU
#include "Engine/World.h"       // Explicit include: required for LineTraceSingleByChannel under IWYU
#include "Engine/OverlapResult.h"
#include "Combat/HealthComponent.h"
#include "Combat/HitscanWeaponComponent.h"
#include "Combat/WeaponRigComponent.h"
#include "Combat/WeaponDataAsset.h"
#include "Mech/IBMech_Base.h"
#include "Kismet/GameplayStatics.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h" // Auto-assign the default rifle viewmodel

AIBCharacter_Infantry::AIBCharacter_Infantry()
{
	PrimaryActorTick.bCanEverTick = true; // Rig feed + ADS move-speed each frame

	// First-person camera at roughly eye height, driven by the controller.
	FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
	FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
	FirstPersonCamera->SetRelativeLocation(FVector(0.0f, 0.0f, 64.0f)); // eye height
	FirstPersonCamera->bUsePawnControlRotation = true;

	// First-person viewmodel weapon, posed by the rig. Attached to the camera so
	// it rides the view. Owner-only see: remote players never see your viewmodel.
	WeaponMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponMesh"));
	WeaponMesh->SetupAttachment(FirstPersonCamera);
	WeaponMesh->SetOnlyOwnerSee(true);
	WeaponMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WeaponMesh->bCastDynamicShadow = false;
	WeaponMesh->CastShadow = false;

	// The template rifle is authored at full world scale; shrink it so the viewmodel
	// reads as "held" rather than filling the screen. Tune alongside the hip anchor.
	WeaponMesh->SetRelativeScale3D(FVector(1.0f));

	// The third-person body should NOT render for the owning player (they see the viewmodel instead).
	GetMesh()->SetOwnerNoSee(true);

	// Attach Modular Health
	HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("HealthComponent"));

	// Single project-wide fire path (consolidates the old inline Fire() trace)
	WeaponComponent = CreateDefaultSubobject<UHitscanWeaponComponent>(TEXT("WeaponComponent"));
	WeaponComponent->bAutoBindLegacyInput = false; // We fire via Enhanced Input; auto-bind would double-fire LMB

	// First-person weapon rig (viewmodel posing + ADS blend).
	WeaponRig = CreateDefaultSubobject<UWeaponRigComponent>(TEXT("WeaponRig"));

}

void AIBCharacter_Infantry::BeginPlay()
{
	Super::BeginPlay();

	// The loadout property stays the designer-facing knob; the component does the firing.
	if (WeaponComponent && CurrentWeaponData)
	{
		WeaponComponent->SetWeaponData(CurrentWeaponData);
	}

	// Wire the first-person weapon rig: camera + viewmodel mesh + this weapon's ADS tuning.
	// SetReferences must run before SetAdsSettings so socket offsets (Grip/Aim) are cached
	// against the mesh that's actually attached before any pose math reads them.
	if (WeaponRig)
	{
		WeaponRig->SetReferences(FirstPersonCamera, WeaponMesh);

		if (CurrentWeaponData)
		{
			WeaponRig->SetAdsSettings(CurrentWeaponData->Ads);
		}
		else
		{
			UE_LOG(LogIronBreach, Error, TEXT("%s: CurrentWeaponData is NULL! Check Blueprint Class Defaults."), *GetName());
		}
	}
	else
	{
		UE_LOG(LogIronBreach, Error, TEXT("[Character] WeaponRig is NULL! Check constructor."));
	}

	// Capture base walk speed so the ADS multiplier has something to scale from.
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		BaseWalkSpeed = (BaseWalkSpeed > 0.0f) ? BaseWalkSpeed : Move->MaxWalkSpeed;
	}

	// Death handling: cosmetic ragdoll everywhere, server-driven respawn (u1-08).
	if (HealthComponent)
	{
		HealthComponent->OnDeath.AddDynamic(this, &AIBCharacter_Infantry::HandleDeath);
	}

	// Add Input Mapping Context
	if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
		{
			if (DefaultMappingContext)
			{
				Subsystem->AddMappingContext(DefaultMappingContext, 0);
			}
			else
			{
				UE_LOG(LogIronBreach, Warning, TEXT("%s: DefaultMappingContext not assigned"), *GetName());
			}
		}
	}

}

void AIBCharacter_Infantry::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (EnhancedInputComponent)
	{
		// Guarded: BindAction on an unassigned UInputAction asserts in newer engine versions
		if (MoveAction) { EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AIBCharacter_Infantry::Move); }
		if (LookAction) { EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AIBCharacter_Infantry::Look); }
		if (FireAction) { EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::Fire); }
		if (AimAction)
		{
			// Hold to aim: press raises the sights, release lowers them.
			EnhancedInputComponent->BindAction(AimAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::StartAiming);
			EnhancedInputComponent->BindAction(AimAction, ETriggerEvent::Completed, this, &AIBCharacter_Infantry::StopAiming);
			EnhancedInputComponent->BindAction(AimAction, ETriggerEvent::Canceled, this, &AIBCharacter_Infantry::StopAiming);
		}
		if (InteractAction)
		{
			EnhancedInputComponent->BindAction(InteractAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::TryBoardMech);
		}
	}
	else
	{
		UE_LOG(LogIronBreach, Error, TEXT("%s: Expected an EnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini"), *GetName());
	}

	// Fallbacks so ADS and boarding work out of the box without any content setup.
	// If the action assets are assigned and bound above, these are skipped.
	if (!AimAction && PlayerInputComponent)
	{
		PlayerInputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &AIBCharacter_Infantry::StartAiming);
		PlayerInputComponent->BindKey(EKeys::RightMouseButton, IE_Released, this, &AIBCharacter_Infantry::StopAiming);
	}
	if (!InteractAction && PlayerInputComponent)
	{
		PlayerInputComponent->BindKey(EKeys::E, IE_Pressed, this, &AIBCharacter_Infantry::TryBoardMech);
	}
}

void AIBCharacter_Infantry::Move(const FInputActionValue& Value)
{
	FVector2D MovementVector = Value.Get<FVector2D>();

	if (Controller != nullptr)
	{
		const FRotator Rotation = Controller->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);

		const FVector ForwardDirection = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
		const FVector RightDirection = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);

		AddMovementInput(ForwardDirection, MovementVector.Y);
		AddMovementInput(RightDirection, MovementVector.X);
	}
}

void AIBCharacter_Infantry::Look(const FInputActionValue& Value)
{
	FVector2D LookAxisVector = Value.Get<FVector2D>();

	if (Controller != nullptr)
	{
		// Damp look sensitivity while zoomed so ADS aim isn't twitchy (tracks FOV ratio).
		const float Sens = WeaponRig ? WeaponRig->GetLookSensitivityMultiplier() : 1.0f;
		AddControllerYawInput(LookAxisVector.X * Sens);
		AddControllerPitchInput(LookAxisVector.Y * Sens);

		// Feed the raw delta to the rig for weapon sway.
		if (WeaponRig)
		{
			WeaponRig->SetLookDelta(LookAxisVector);
		}
	}
}

void AIBCharacter_Infantry::StartAiming()
{
	if (WeaponRig) WeaponRig->SetAiming(true);
}

void AIBCharacter_Infantry::StopAiming()
{
	if (WeaponRig) WeaponRig->SetAiming(false);
}

void AIBCharacter_Infantry::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Apply the ADS move-speed multiplier (slower while aiming). Cheap, and keeps
	// the movement authority-agnostic — MaxWalkSpeed already replicates via CMC.
	if (WeaponRig && BaseWalkSpeed > 0.0f)
	{
		if (UCharacterMovementComponent* Move = GetCharacterMovement())
		{
			Move->MaxWalkSpeed = BaseWalkSpeed * WeaponRig->GetMoveSpeedMultiplier();
		}
	}
}

void AIBCharacter_Infantry::Fire()
{
	// Consolidated: cosmetics + Server_Fire routing + authoritative trace all live in the
	// weapon component now (ADR-002 pattern-setter). One fire path for the whole project.
	if (WeaponComponent)
	{
		WeaponComponent->Fire();
	}
}

// --- CARYATID BOARDING (u3-07) ---

AIBMech_Base* AIBCharacter_Infantry::FindBoardableMech() const
{
	UWorld* World = GetWorld();
	if (!World) return nullptr;

	FVector ViewLoc;
	FRotator ViewRot;
	if (Controller)
	{
		Controller->GetPlayerViewPoint(ViewLoc, ViewRot);
	}
	else
	{
		GetActorEyesViewPoint(ViewLoc, ViewRot);
	}

	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);

	// A forward sweep first — "the mech I'm looking at".
	FHitResult Hit;
	if (World->SweepSingleByChannel(Hit, ViewLoc, ViewLoc + ViewRot.Vector() * BoardReach,
		FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(100.0f), Params))
	{
		if (AIBMech_Base* Mech = Cast<AIBMech_Base>(Hit.GetActor()))
		{
			return Mech;
		}
	}

	// Fallback: any mech we're standing next to. A 60m machine fills the screen — the
	// player is often too close for the aim sweep to make sense.
	TArray<FOverlapResult> Overlaps;
	if (World->OverlapMultiByChannel(Overlaps, GetActorLocation(), FQuat::Identity, ECC_Pawn,
		FCollisionShape::MakeSphere(BoardReach), Params))
	{
		for (const FOverlapResult& Overlap : Overlaps)
		{
			if (AIBMech_Base* Mech = Cast<AIBMech_Base>(Overlap.GetActor()))
			{
				return Mech;
			}
		}
	}
	return nullptr;
}

void AIBCharacter_Infantry::TryBoardMech()
{
	AIBMech_Base* Mech = FindBoardableMech();
	if (!Mech)
	{
		return;
	}

	// Give UI a chance to offer the seat choice...
	BP_OnMechInteract(Mech);

	// ...and/or board the helm directly (default) so the loop works with zero content.
	if (bAutoBoardOnInteract)
	{
		RequestBoard(Mech, /*bWantLeftSeat=*/true);
	}
}

void AIBCharacter_Infantry::RequestBoard(AIBMech_Base* Mech, bool bWantLeftSeat)
{
	if (!Mech) return;

	if (HasAuthority())
	{
		Mech->ServerBoard(GetController(), this, bWantLeftSeat);
	}
	else
	{
		Server_RequestBoard(Mech, bWantLeftSeat);
	}
}

void AIBCharacter_Infantry::Server_RequestBoard_Implementation(AIBMech_Base* Mech, bool bWantLeftSeat)
{
	if (Mech)
	{
		Mech->ServerBoard(GetController(), this, bWantLeftSeat);
	}
}

// Interface Implementation handling incoming damage
void AIBCharacter_Infantry::HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	if (HealthComponent)
	{
		HealthComponent->ApplyDamage(DamageAmount, HitResult, InstigatedBy, DamageCauser);
	}
}

void AIBCharacter_Infantry::HandleDeath(AActor* Killer)
{
	if (bDead) return;
	bDead = true;

	// --- Cosmetics: every machine ragdolls the corpse (same recipe as the enemy) ---
	if (GetCapsuleComponent())
	{
		GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->StopMovementImmediately();
		GetCharacterMovement()->DisableMovement();
	}
	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		MeshComp->SetCollisionProfileName(TEXT("Ragdoll"));
		MeshComp->SetSimulatePhysics(true);
	}

	BP_OnDied(Killer);

	// --- Authority: schedule the comeback ---
	// RestartPlayer spawns a fresh pawn from the CURRENT GameMode's pawn class at a
	// PlayerStart, so this works untouched under BP GameModes. Detaching first also
	// makes the corpse stop counting as player-controlled, which drops AI aggro.
	if (HasAuthority())
	{
		TWeakObjectPtr<AController> DeadController = GetController();
		DetachFromControllerPendingDestroy();
		SetLifeSpan(RespawnDelay + 4.0f); // corpse outlives the respawn, then cleans up

		GetWorldTimerManager().SetTimer(RespawnTimerHandle, FTimerDelegate::CreateWeakLambda(this,
			[this, DeadController]()
			{
				AGameModeBase* GameMode = GetWorld() ? GetWorld()->GetAuthGameMode() : nullptr;
				if (GameMode && DeadController.IsValid())
				{
					UE_LOG(LogIronBreach, Log, TEXT("Respawning %s"), *GetNameSafe(DeadController.Get()));
					GameMode->RestartPlayer(DeadController.Get());
				}
			}), RespawnDelay, false);
	}
}
