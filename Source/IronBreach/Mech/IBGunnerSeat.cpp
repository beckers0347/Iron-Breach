#include "Mech/IBGunnerSeat.h"
#include "Mech/IBMech_Base.h"
#include "IronBreach.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Combat/HitscanWeaponComponent.h"
#include "Combat/TargetingComponent.h"
#include "Combat/WeaponRigComponent.h"
#include "Combat/WeaponDataAsset.h"
#include "EnhancedInputComponent.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"

AIBGunnerSeat::AIBGunnerSeat()
{
	PrimaryActorTick.bCanEverTick = true;

	bReplicates = true;
	// Transform comes from the attachment to the hull, not from movement replication.
	SetReplicatingMovement(false);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("SeatRoot"));
	SetRootComponent(Root);

	CockpitCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("CockpitCamera"));
	CockpitCamera->SetupAttachment(Root);
	CockpitCamera->bUsePawnControlRotation = true; // gunner look = control rotation

	WeaponComponent = CreateDefaultSubobject<UHitscanWeaponComponent>(TEXT("WeaponComponent"));
	WeaponComponent->bAutoBindLegacyInput = false; // we fire explicitly; auto-bind double-fires

	TargetingComponent = CreateDefaultSubobject<UTargetingComponent>(TEXT("TargetingComponent"));

	// The seat itself never blocks anything.
	SetCanBeDamaged(false);
}

void AIBGunnerSeat::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBGunnerSeat, OwningMech);
	DOREPLIFETIME(AIBGunnerSeat, ReplicatedAim);
}

void AIBGunnerSeat::BeginPlay()
{
	Super::BeginPlay();
	SyncWeaponFromMech();
}

void AIBGunnerSeat::OnRep_OwningMech()
{
	SyncWeaponFromMech();
}

void AIBGunnerSeat::SyncWeaponFromMech()
{
	if (OwningMech && WeaponComponent && OwningMech->CurrentWeaponData)
	{
		WeaponComponent->SetWeaponData(OwningMech->CurrentWeaponData);
	}
}

void AIBGunnerSeat::PawnClientRestart()
{
	Super::PawnClientRestart();

	// The gunner's machine: run the hull's (local, cosmetic) weapon rig against OUR
	// cockpit camera so ADS zoom/pose work from this seat's point of view.
	if (OwningMech && OwningMech->WeaponRigComponent)
	{
		OwningMech->WeaponRigComponent->SetReferences(CockpitCamera, OwningMech->MechWeaponMesh);
		if (OwningMech->CurrentWeaponData)
		{
			OwningMech->WeaponRigComponent->SetAdsSettings(OwningMech->CurrentWeaponData->Ads);
		}
	}
	SyncWeaponFromMech();
}

void AIBGunnerSeat::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Owner-authoritative aim stream: local control rotation is the truth about intent;
	// the server mirrors it out so the hull can pose the arm cannon everywhere.
	if (IsLocallyControlled() && Controller)
	{
		const FRotator Aim = Controller->GetControlRotation();

		if (HasAuthority())
		{
			ReplicatedAim = Aim; // listen host / standalone: no RPC round-trip needed
		}
		else if (!Aim.Equals(LastSentAim, 0.5f))
		{
			Server_SetAim(Aim);
			LastSentAim = Aim;
		}
	}
}

FRotator AIBGunnerSeat::GetAimRotation() const
{
	if (IsLocallyControlled() && Controller)
	{
		return Controller->GetControlRotation();
	}
	return ReplicatedAim;
}

void AIBGunnerSeat::Server_SetAim_Implementation(FRotator NewAim)
{
	ReplicatedAim = NewAim;
}

// ---- Input ----

void AIBGunnerSeat::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	// Raw exit key, matching the hull's: dismounting must never depend on content wiring.
	PlayerInputComponent->BindKey(EKeys::E, IE_Pressed, this, &AIBGunnerSeat::RequestExit);

	// Optional own bindings (IMC_Gunner path). Guarded — unassigned actions are fine
	// because AIBMechPlayerController routes its bindings here anyway.
	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		if (LookAction) { Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AIBGunnerSeat::OnLookInput); }
		if (FireAction) { Input->BindAction(FireAction, ETriggerEvent::Started, this, &AIBGunnerSeat::OnFireInput); }
		if (SwapAction) { Input->BindAction(SwapAction, ETriggerEvent::Started, this, &AIBGunnerSeat::OnSwapInput); }
		if (ADSAction)
		{
			Input->BindAction(ADSAction, ETriggerEvent::Started, this, &AIBGunnerSeat::OnAdsInput);
			Input->BindAction(ADSAction, ETriggerEvent::Completed, this, &AIBGunnerSeat::OnAdsInput);
		}
	}
}

void AIBGunnerSeat::OnLookInput(const FInputActionValue& Value) { ProcessLook(Value.Get<FVector2D>()); }
void AIBGunnerSeat::OnFireInput(const FInputActionValue& Value) { HandleFirePressed(); }
void AIBGunnerSeat::OnAdsInput(const FInputActionValue& Value)  { SetAiming(Value.Get<bool>()); }
void AIBGunnerSeat::OnSwapInput(const FInputActionValue& Value) { RequestSwap(); }

void AIBGunnerSeat::ProcessLook(const FVector2D& LookVector)
{
	APlayerController* PC = Cast<APlayerController>(Controller);
	if (!PC) return;

	const float Sens = OwningMech ? OwningMech->GunnerYawSensitivity : 1.0f;
	const float YawLimit = OwningMech ? OwningMech->GunnerYawLimit : 90.0f;

	if (LookVector.X != 0.0f)
	{
		FRotator ControlRot = PC->GetControlRotation();
		// Clamp traverse against the HULL's forward — the turret can't shoot through
		// the mech's own shoulders. Without a hull we free-look.
		if (OwningMech)
		{
			const float MechYaw = OwningMech->GetActorRotation().Yaw;
			const float CurrentDeltaYaw = FMath::UnwindDegrees(ControlRot.Yaw - MechYaw);
			const float NewDeltaYaw = FMath::Clamp(CurrentDeltaYaw + (LookVector.X * Sens), -YawLimit, YawLimit);
			ControlRot.Yaw = MechYaw + NewDeltaYaw;
			PC->SetControlRotation(ControlRot);
		}
		else
		{
			AddControllerYawInput(LookVector.X * Sens);
		}
	}

	if (LookVector.Y != 0.0f)
	{
		// Pitch limits come from the PlayerCameraManager (MechPC sets ±90).
		AddControllerPitchInput(LookVector.Y);
	}

	// Feed sway on the gunner's machine.
	if (OwningMech && OwningMech->WeaponRigComponent)
	{
		OwningMech->WeaponRigComponent->SetLookDelta(LookVector);
	}
}

void AIBGunnerSeat::HandleFirePressed()
{
	// Client-side desync gate (UX): heavy weapons are safety-locked in T0 (spec §3.2).
	// The server-side fire path stays authoritative regardless.
	if (OwningMech && OwningMech->AreWeaponsSafetyLocked())
	{
		OwningMech->OnWeaponsSafetyLocked();
		return;
	}

	if (WeaponComponent)
	{
		WeaponComponent->Fire(); // cosmetic-first + Server_Fire (ADR-002)
	}
}

void AIBGunnerSeat::SetAiming(bool bNewAiming)
{
	bWantAds = bNewAiming;
	if (OwningMech && OwningMech->WeaponRigComponent)
	{
		OwningMech->WeaponRigComponent->SetAiming(bNewAiming);
	}
}

void AIBGunnerSeat::RequestSwap()
{
	if (HasAuthority())
	{
		if (OwningMech) { OwningMech->ServerRequestCrewSwap(Controller); }
	}
	else
	{
		Server_RequestSwap();
	}
}

void AIBGunnerSeat::Server_RequestSwap_Implementation()
{
	if (OwningMech) { OwningMech->ServerRequestCrewSwap(Controller); }
}

void AIBGunnerSeat::RequestExit()
{
	if (HasAuthority())
	{
		if (OwningMech) { OwningMech->ServerDisembark(Controller); }
	}
	else
	{
		Server_RequestExit();
	}
}

void AIBGunnerSeat::Server_RequestExit_Implementation()
{
	if (OwningMech) { OwningMech->ServerDisembark(Controller); }
}

void AIBGunnerSeat::SendRitualInput(EConcordRitualStep Step)
{
	if (HasAuthority())
	{
		if (OwningMech && OwningMech->GetConcord())
		{
			OwningMech->GetConcord()->RegisterRitualInput(/*bFromDriver=*/false, Step);
		}
	}
	else
	{
		Server_SendRitualInput(Step);
	}
}

void AIBGunnerSeat::Server_SendRitualInput_Implementation(EConcordRitualStep Step)
{
	if (OwningMech && OwningMech->GetConcord())
	{
		OwningMech->GetConcord()->RegisterRitualInput(/*bFromDriver=*/false, Step);
	}
}
