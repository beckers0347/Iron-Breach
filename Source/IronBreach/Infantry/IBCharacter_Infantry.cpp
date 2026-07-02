#include "IBCharacter_Infantry.h"
#include "IronBreach.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h" // Explicit include: required for ULocalPlayer::GetSubsystem under IWYU
#include "Engine/World.h"       // Explicit include: required for LineTraceSingleByChannel under IWYU
#include "Combat/HealthComponent.h"
#include "Combat/WeaponDataAsset.h"
#include "Kismet/GameplayStatics.h"

AIBCharacter_Infantry::AIBCharacter_Infantry()
{
	PrimaryActorTick.bCanEverTick = false;

	// Camera setup for tracking fast gameplay
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 300.0f;
	CameraBoom->bUsePawnControlRotation = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	// Attach Modular Health
	HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("HealthComponent"));
}

void AIBCharacter_Infantry::BeginPlay()
{
	Super::BeginPlay();

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

	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		// Guarded: BindAction on an unassigned UInputAction asserts in newer engine versions
		if (MoveAction) { EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AIBCharacter_Infantry::Move); }
		if (LookAction) { EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AIBCharacter_Infantry::Look); }
		if (FireAction) { EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::Fire); }
	}
	else
	{
		UE_LOG(LogIronBreach, Error, TEXT("%s: Expected an EnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini"), *GetName());
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
		AddControllerYawInput(LookAxisVector.X);
		AddControllerPitchInput(LookAxisVector.Y);
	}
}

void AIBCharacter_Infantry::Fire()
{
	if (!CurrentWeaponData) return;

	// Audio Visuals (SFX)
	if (CurrentWeaponData->FireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, CurrentWeaponData->FireSound, GetActorLocation());
	}

	// Calculate Trace Vectors from Camera Screen Space Center
	FVector CameraLocation;
	FRotator CameraRotation;
	GetActorEyesViewPoint(CameraLocation, CameraRotation);

	FVector TraceStart = CameraLocation;
	FVector TraceEnd = TraceStart + (CameraRotation.Vector() * CurrentWeaponData->MaxRange);

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this); // Don't shoot yourself

	// ECC_Pawn: pawn capsules ignore ECC_Visibility, so hitscan must trace a channel pawns block
	bool bHit = GetWorld()->LineTraceSingleByChannel(HitResult, TraceStart, TraceEnd, ECC_Pawn, QueryParams);

	if (bHit && HitResult.GetActor())
	{
		// Native Interface Check: Decoupled check to see if the target can take damage
		if (HitResult.GetActor()->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass()))
		{
			IDamageableInterface::Execute_HandleTakeDamage(HitResult.GetActor(), CurrentWeaponData->BaseDamage, HitResult, GetController(), this);
		}
		else
		{
			// Fallback: generic engine damage for actors without the interface
			UGameplayStatics::ApplyDamage(HitResult.GetActor(), CurrentWeaponData->BaseDamage, GetController(), this, nullptr);
		}
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
