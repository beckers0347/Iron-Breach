#include "Mech/IBMech_Base.h"
#include "IronBreach.h"
#include "Mech/IBMechAIController.h"
#include "Mech/IBGunnerSeat.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "AIController.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/LocalPlayer.h"
#include "DrawDebugHelpers.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Combat/WeaponRigComponent.h"
#include "Combat/HitscanWeaponComponent.h"
#include "Combat/DamageableInterface.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "Kismet/GameplayStatics.h"

AIBMech_Base::AIBMech_Base()
{
	AIControllerClass = AIBMechAIController::StaticClass();

	// Leave auto-possess OFF. With it on, an AI controller possesses the hull during
	// PostInitializeComponents — BEFORE BeginPlay — and claims a seat. When the player then
	// boards, both roles are already held by a controller that is no longer possessing, so
	// every RouteXInput() call rejects the player and the mech appears frozen.
	// (BP_Mech has this serialized too — a BP override BEATS this default, keep it Disabled there.)
	AutoPossessAI = EAutoPossessAI::Disabled;

	PrimaryActorTick.bCanEverTick = true;

	// The hull replicates: CMC handles predicted movement for the possessing navigator,
	// simulated proxies for everyone else (ADR-002: listen server, standard replication).
	bReplicates = true;
	SetReplicatingMovement(true);

	LeftSeatController = nullptr;
	RightSeatController = nullptr;
	CurrentDriver = nullptr;
	CurrentGunner = nullptr;
	bIsGunner = false; // We start as the Driver by default

	// Mech mesh must be initialized first.
	MechMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("MechMesh"));
	MechMesh->SetupAttachment(GetCapsuleComponent());

	// The arm weapon has its own mesh. The rig poses THIS, not the chassis.
	MechWeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("MechWeaponMesh"));
	MechWeaponMesh->SetupAttachment(MechMesh);
	MechWeaponMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	MechWeaponMesh->bCastDynamicShadow = false;
	MechWeaponMesh->CastShadow = false;

	// Create the weapon rig component in C++ so it's always attached
	WeaponRigComponent = CreateDefaultSubobject<UWeaponRigComponent>(TEXT("WeaponRigComponent"));

	// CONCORD — the clasp. Server-side brain, replicated readouts (Caryatid doc §2).
	Concord = CreateDefaultSubobject<UConcordComponent>(TEXT("Concord"));

	// --- Initialize Driver Views (3PV) ---

	DriverSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("DriverSpringArm"));
	DriverSpringArm->SetupAttachment(GetCapsuleComponent());
	DriverSpringArm->TargetArmLength = 400.0f;
	DriverSpringArm->bUsePawnControlRotation = true;
	DriverSpringArm->bInheritYaw = true;
	DriverSpringArm->bInheritPitch = true;
	DriverSpringArm->bInheritRoll = false;

	DriverCamera_3PV = CreateDefaultSubobject<UCameraComponent>(TEXT("DriverCamera_3PV"));
	DriverCamera_3PV->SetupAttachment(DriverSpringArm, USpringArmComponent::SocketName);
	DriverCamera_3PV->bUsePawnControlRotation = false;

	// --- Initialize Gunner Views (FPV Cockpit) ---

	GunnerCamera_FPV = CreateDefaultSubobject<UCameraComponent>(TEXT("GunnerCamera_FPV"));
	GunnerCamera_FPV->SetupAttachment(MechMesh);
	GunnerCamera_FPV->SetRelativeLocation(FVector(150.f, 0.f, 80.f));
	GunnerCamera_FPV->bUsePawnControlRotation = false; // Gunner points the weapons, not the view.
}

void AIBMech_Base::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBMech_Base, GunnerSeat);
	DOREPLIFETIME(AIBMech_Base, CurrentHealth);
	DOREPLIFETIME(AIBMech_Base, CurrentAmmo);
	DOREPLIFETIME(AIBMech_Base, WeaponCooldownRemaining);
	DOREPLIFETIME(AIBMech_Base, PartnerName);
}

void AIBMech_Base::BeginPlay()
{
	Super::BeginPlay();

	SetGunnerViewActive(false);

	CurrentHealth = MaxHealth;
	CurrentAmmo = MaxAmmo;

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		BaseMaxWalkSpeed = (BaseMaxWalkSpeed > 0.0f) ? BaseMaxWalkSpeed : Move->MaxWalkSpeed;
	}

	// Rig poses the arm weapon, not the chassis.
	if (WeaponRigComponent)
	{
		WeaponRigComponent->SetReferences(GunnerCamera_FPV, MechWeaponMesh);
		if (CurrentVisualData && CurrentVisualData->CombatData)
		{
			WeaponRigComponent->SetAdsSettings(CurrentVisualData->CombatData->Ads);
		}
	}

	// Server-only spawns. BeginPlay runs on every machine; spawning actors on clients
	// creates phantoms the server knows nothing about.
	if (HasAuthority() && GetWorld())
	{
		SpawnGunnerSeat();

		FActorSpawnParameters SpawnParams;
		SpawnParams.Owner = this;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

		CoPilotController = GetWorld()->SpawnActor<AIBMechAIController>(
			AIBMechAIController::StaticClass(), GetActorLocation(), GetActorRotation(), SpawnParams);

		UE_LOG(LogIronBreach, Display, TEXT("[Mech] AI CoPilot %s."),
			CoPilotController ? TEXT("spawned, awaiting seat assignment") : TEXT("FAILED to spawn"));
	}
}

void AIBMech_Base::SpawnGunnerSeat()
{
	UWorld* World = GetWorld();
	if (!World || GunnerSeat) return;

	UClass* SeatClass = GunnerSeatClass ? GunnerSeatClass.Get() : AIBGunnerSeat::StaticClass();

	// Deferred so OwningMech is valid before the seat's BeginPlay runs.
	AIBGunnerSeat* Seat = World->SpawnActorDeferred<AIBGunnerSeat>(
		SeatClass, GetActorTransform(), this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (!Seat)
	{
		UE_LOG(LogIronBreach, Error, TEXT("[Mech] Gunner seat failed to spawn on %s."), *GetName());
		return;
	}

	Seat->OwningMech = this;
	Seat->FinishSpawning(GetActorTransform());

	if (MechMesh && MechMesh->DoesSocketExist(GunnerSeatSocket))
	{
		Seat->AttachToComponent(MechMesh, FAttachmentTransformRules::SnapToTargetNotIncludingScale, GunnerSeatSocket);
	}
	else
	{
		// No authored socket yet: sit the seat where the legacy cockpit camera sits.
		Seat->AttachToComponent(MechMesh, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		Seat->SetActorRelativeLocation(GunnerCamera_FPV ? GunnerCamera_FPV->GetRelativeLocation() : FVector(150.f, 0.f, 80.f));
	}

	GunnerSeat = Seat;
}

void AIBMech_Base::OnRep_GunnerSeat()
{
	// Nothing required yet — the property being valid is what BP/HUD needs. The seat
	// fixes its own weapon data via its OnRep_OwningMech.
}

void AIBMech_Base::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Cooldowns are authoritative on the server and replicate down for the HUD.
	if (HasAuthority())
	{
		if (WeaponCooldownRemaining > 0.0f)
		{
			WeaponCooldownRemaining = FMath::Max(0.0f, WeaponCooldownRemaining - DeltaSeconds);
		}
		if (PartnerCooldownRemaining > 0.0f)
		{
			PartnerCooldownRemaining = FMath::Max(0.0f, PartnerCooldownRemaining - DeltaSeconds);
		}
	}

	// Desync control profile (spec §3.2): weak, not helpless. Concord state replicates,
	// so every machine computes the same speed and CMC stays consistent.
	if (BaseMaxWalkSpeed > 0.0f && Concord)
	{
		if (UCharacterMovementComponent* Move = GetCharacterMovement())
		{
			Move->MaxWalkSpeed = BaseMaxWalkSpeed * Concord->GetMoveSpeedFactor();
		}
	}
}

void AIBMech_Base::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);

	// The dead-mech guard: if the incoming controller isn't already seated, the crew state
	// belongs to a previous occupant — wipe it so boarding starts clean. ServerBoard and
	// PerformPossessionSwap seat the pilot BEFORE possessing, so they never hit this.
	if (NewController && !IsControllerSeated(NewController))
	{
		ResetCrew();
	}
}

void AIBMech_Base::PawnClientRestart()
{
	Super::PawnClientRestart();

	// Whoever locally possesses the hull is the navigator: driver view on this machine.
	bIsGunner = false;
	bIsDriverActive = true;
	SetGunnerViewActive(false);
}

void AIBMech_Base::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Two controllers feed this pawn, so movement/fire don't bind here —
	// AIBMechPlayerController reads Enhanced Input and calls RouteMoveInput()/FireWeapon().
	// Exit-seat is the exception: a raw key bind so dismounting works even with
	// zero IMC wiring (packaged build one had no way out of the hull).
	PlayerInputComponent->BindKey(EKeys::E, IE_Pressed, this, &AIBMech_Base::RequestExit);
}

void AIBMech_Base::RequestExit()
{
	if (HasAuthority())
	{
		ServerDisembark(GetController());
	}
	else
	{
		Server_RequestExit();
	}
}

void AIBMech_Base::Server_RequestExit_Implementation()
{
	ServerDisembark(GetController());
}

// --- SEAT & ROLE MANAGEMENT ---

void AIBMech_Base::ResetCrew()
{
	LeftSeatController = nullptr;
	RightSeatController = nullptr;
	CurrentDriver = nullptr;
	CurrentGunner = nullptr;
	bIsGunner = false;
	bIsDriverActive = true;
}

void AIBMech_Base::RecomputeRoles()
{
	// Roles are DERIVED from seats. This is the only function allowed to write them.
	const bool bDriverStillSeated = CurrentDriver && (CurrentDriver == LeftSeatController || CurrentDriver == RightSeatController);
	const bool bGunnerStillSeated = CurrentGunner && (CurrentGunner == LeftSeatController || CurrentGunner == RightSeatController);

	// A valid, distinct pairing survives a seat change untouched — this is what lets a
	// swapped pair keep their swapped roles when the second crew member boards.
	if (bDriverStillSeated && bGunnerStillSeated && CurrentDriver != CurrentGunner)
	{
		return;
	}

	// Otherwise rebuild from scratch: Left drives, Right shoots.
	if (LeftSeatController && RightSeatController)
	{
		CurrentDriver = LeftSeatController;
		CurrentGunner = RightSeatController;
	}
	else if (LeftSeatController)
	{
		CurrentDriver = LeftSeatController;
		CurrentGunner = nullptr;
	}
	else if (RightSeatController)
	{
		// Solo occupant always drives — a gunner with no driver is a mech that cannot move.
		CurrentDriver = RightSeatController;
		CurrentGunner = nullptr;
	}
	else
	{
		CurrentDriver = nullptr;
		CurrentGunner = nullptr;
	}
}

void AIBMech_Base::AssignToLeftSeat(AController* NewController)
{
	if (!NewController) return;

	// Don't let one controller hold both seats.
	if (RightSeatController == NewController)
	{
		RightSeatController = nullptr;
	}

	LeftSeatController = NewController;
	RecomputeRoles();
}

void AIBMech_Base::AssignToRightSeat(AController* NewController)
{
	if (!NewController) return;

	if (LeftSeatController == NewController)
	{
		LeftSeatController = nullptr;
	}

	RightSeatController = NewController;
	RecomputeRoles();
}

void AIBMech_Base::VacateSeat(AController* LeavingController)
{
	if (!LeavingController) return;

	if (LeftSeatController == LeavingController)  LeftSeatController = nullptr;
	if (RightSeatController == LeavingController) RightSeatController = nullptr;
	if (CurrentDriver == LeavingController)       CurrentDriver = nullptr;
	if (CurrentGunner == LeavingController)       CurrentGunner = nullptr;

	RecomputeRoles();
}

void AIBMech_Base::PerformRoleSwap()
{
	// A swap needs two distinct crew. Swapping with an empty seat produces the exact
	// null-role state that made the mech unresponsive.
	if (!CurrentDriver || !CurrentGunner)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Mech] Role swap refused — mech is not fully crewed."));
		return;
	}

	AController* Temp = CurrentDriver;
	CurrentDriver = CurrentGunner;
	CurrentGunner = Temp;

	UE_LOG(LogIronBreach, Log, TEXT("[Mech] Roles swapped. Driver is now: %s"), *GetNameSafe(CurrentDriver));

	// Re-derive local view from the controller that actually owns this pawn.
	ApplyLocalViewForRole(GetController());

	if (APlayerController* PC = Cast<APlayerController>(CurrentGunner))
	{
		PC->SetControlRotation(GetActorRotation());
	}
}

void AIBMech_Base::RequestRoleSwap(AController* Requester)
{
	if (!Requester) return;
	if (!IsControllerSeated(Requester)) return;

	AController* CoPilot = (Requester == LeftSeatController) ? RightSeatController.Get() : LeftSeatController.Get();
	if (!CoPilot)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Mech] Swap requested but the other seat is empty."));
		return;
	}

	// AI co-pilots auto-accept. Human-to-human goes through the server handshake.
	if (Cast<AAIController>(CoPilot))
	{
		UE_LOG(LogIronBreach, Display, TEXT("[Mech] Swap requested by human. AI co-pilot auto-accepting."));
		PerformRoleSwap();
	}
	else
	{
		ServerRequestCrewSwap(Requester);
	}
}

// --- CARYATID BOARDING (server-arbitrated possession, uq4 Option B) ---

FString AIBMech_Base::DescribeCrewName(AController* CrewController) const
{
	if (!CrewController) return TEXT("Empty");
	if (Cast<AAIController>(CrewController)) return TEXT("VIRGIL (AI)");
	if (const APlayerState* PS = CrewController->PlayerState) return PS->GetPlayerName();
	return CrewController->GetName();
}

bool AIBMech_Base::ServerBoard(AController* BoardingController, AIBCharacter_Infantry* FromPawn, bool bWantLeftSeat)
{
	if (!HasAuthority())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Mech] ServerBoard called off-authority — route through the infantry's Server_RequestBoard."));
		return false;
	}
	APlayerController* PC = Cast<APlayerController>(BoardingController);
	if (!PC) return false;

	APlayerController* CurrentDriverPC = Cast<APlayerController>(GetController());
	APlayerController* CurrentGunnerPC = GunnerSeat ? Cast<APlayerController>(GunnerSeat->GetController()) : nullptr;
	const bool bHullHeldByHuman = (CurrentDriverPC != nullptr && CurrentDriverPC != PC);
	const bool bSeatHeldByHuman = (CurrentGunnerPC != nullptr && CurrentGunnerPC != PC);

	// A pilot boarding an empty mech always drives, whatever they asked for.
	bool bTakeHull = bWantLeftSeat;

	// If they want the Gunner seat, but a human is already in it, force them to the Hull (Driver) if it's empty.
	if (!bTakeHull && bSeatHeldByHuman && !bHullHeldByHuman)
	{
		bTakeHull = true;
	}
	// If they want the Hull, but a human is already in it, force them to the Gunner seat if it's empty.
	else if (bTakeHull && bHullHeldByHuman && !bSeatHeldByHuman)
	{
		bTakeHull = false;
	}

	if (bTakeHull && bHullHeldByHuman)
	{
		bTakeHull = false; // asked for the hull, it's taken — offer the seat
	}

	if (bTakeHull)
	{
		if (!bWantLeftSeat)
		{
			UE_LOG(LogIronBreach, Display, TEXT("[Mech] %s wanted the gunner seat but there is no driver — seating them at the helm (solo occupant always drives)."),
				*DescribeCrewName(PC));
		}

		// Evict a co-pilot AI that may be holding the hull (legacy flow leftovers).
		if (AAIController* AIHolding = Cast<AAIController>(GetController()))
		{
			AIHolding->UnPossess();
		}

		if (FromPawn) { ParkInfantryPawn(FromPawn); ParkedDriverPawn = FromPawn; }

		AssignToLeftSeat(PC); // seat BEFORE possess so PossessedBy doesn't wipe the crew
		PC->Possess(this);
	}
	else
	{
		if (bSeatHeldByHuman || !GunnerSeat)
		{
			UE_LOG(LogIronBreach, Warning, TEXT("[Mech] %s could not board — both stations are crewed."), *DescribeCrewName(PC));
			return false;
		}

		// Relieve the AI gunner if it holds the seat.
		if (AAIController* AIGunner = GunnerSeat ? Cast<AAIController>(GunnerSeat->GetController()) : nullptr)
		{
			AIGunner->UnPossess();
		}

		if (FromPawn) { ParkInfantryPawn(FromPawn); ParkedGunnerPawn = FromPawn; }

		AssignToRightSeat(PC);
		PC->Possess(GunnerSeat);
	}

	PartnerName = DescribeCrewName(bTakeHull ? (GunnerSeat ? GunnerSeat->GetController() : nullptr) : GetController());

	// Solo human aboard: the AI co-pilot takes the guns (parity by construction, u3-05).
	BackfillSeatWithAI();

	UE_LOG(LogIronBreach, Display, TEXT("[Mech] %s boarded as %s."),
		*DescribeCrewName(PC), bTakeHull ? TEXT("NAVIGATOR") : TEXT("GUNNER"));
	return true;
}

void AIBMech_Base::BackfillSeatWithAI()
{
	if (!HasAuthority() || !GunnerSeat || !CoPilotController) return;

	const bool bHullHasPlayer = Cast<APlayerController>(GetController()) != nullptr;
	if (bHullHasPlayer && GunnerSeat->GetController() == nullptr)
	{
		AssignToRightSeat(CoPilotController);
		CoPilotController->Possess(GunnerSeat);
		if (PartnerName.IsEmpty() || PartnerName == TEXT("Partner") || PartnerName == TEXT("Empty"))
		{
			PartnerName = DescribeCrewName(CoPilotController);
		}
	}
}

void AIBMech_Base::ParkInfantryPawn(AIBCharacter_Infantry* Pawn)
{
	if (!Pawn) return;
	Pawn->SetActorHiddenInGame(true);
	Pawn->SetActorEnableCollision(false);
	if (UCharacterMovementComponent* Move = Pawn->GetCharacterMovement())
	{
		Move->StopMovementImmediately();
		Move->DisableMovement();
	}
}

void AIBMech_Base::UnparkInfantryPawn(APawn* Pawn, const FVector& AtLocation)
{
	if (!Pawn) return;
	Pawn->TeleportTo(AtLocation, GetActorRotation(), false, true);
	Pawn->SetActorHiddenInGame(false);
	Pawn->SetActorEnableCollision(true);
	if (ACharacter* AsCharacter = Cast<ACharacter>(Pawn))
	{
		if (UCharacterMovementComponent* Move = AsCharacter->GetCharacterMovement())
		{
			Move->SetMovementMode(MOVE_Walking);
		}
	}
}

void AIBMech_Base::ServerDisembark(AController* LeavingController)
{
	if (!HasAuthority() || !LeavingController) return;
	APlayerController* PC = Cast<APlayerController>(LeavingController);
	if (!PC) return;

	const bool bWasDriver = (PC == GetController());
	const bool bWasGunner = (GunnerSeat && PC == GunnerSeat->GetController());
	if (!bWasDriver && !bWasGunner) return;

	APawn* Parked = bWasDriver ? ParkedDriverPawn.Get() : ParkedGunnerPawn.Get();
	if (!Parked)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Mech] %s has no parked pawn to dismount into."), *DescribeCrewName(PC));
		return;
	}

	// Drop the pilot at the hull's flank, outside the capsule.
	const float ExitDistance = (GetCapsuleComponent() ? GetCapsuleComponent()->GetScaledCapsuleRadius() : 200.0f) + 200.0f;
	const FVector ExitSpot = GetActorLocation() + GetActorRightVector() * ExitDistance;

	VacateSeat(PC);
	PC->Possess(Parked);
	UnparkInfantryPawn(Parked, ExitSpot);

	if (bWasDriver) { ParkedDriverPawn = nullptr; }
	else            { ParkedGunnerPawn = nullptr; }

	// The guns never go quiet just because a human left.
	BackfillSeatWithAI();

	UE_LOG(LogIronBreach, Display, TEXT("[Mech] %s dismounted."), *DescribeCrewName(PC));
}

void AIBMech_Base::ServerRequestCrewSwap(AController* Requester)
{
	if (!HasAuthority() || !Requester) return;

	APlayerController* DriverPC = Cast<APlayerController>(GetController());
	APlayerController* GunnerPC = GunnerSeat ? Cast<APlayerController>(GunnerSeat->GetController()) : nullptr;

	// One human + AI co-pilot: the legacy in-place role swap is the whole experience
	// (camera flips, AI auto-accepts). Keep it exactly as playtested.
	if (!DriverPC || !GunnerPC)
	{
		if (Cast<AAIController>(CurrentDriver.Get()) || Cast<AAIController>(CurrentGunner.Get()))
		{
			PerformRoleSwap();
		}
		else
		{
			RequestRoleSwap(Requester);
		}
		return;
	}

	// Two humans: confirm handshake. First press arms it; the partner's press inside the
	// window executes the pawn exchange. Server-arbitrated so both can't trade into the
	// same seat (Caryatid doc §2).
	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (SwapRequestedBy.IsValid() && SwapRequestedBy.Get() != Requester && Now <= SwapRequestExpiry)
	{
		SwapRequestedBy = nullptr;
		PerformPossessionSwap(DriverPC, GunnerPC);
	}
	else
	{
		SwapRequestedBy = Requester;
		SwapRequestExpiry = Now + SwapConfirmWindow;
		Multicast_PartnerSwapRequested();
	}
}

void AIBMech_Base::Multicast_PartnerSwapRequested_Implementation()
{
	OnPartnerSwapNotified();
}

void AIBMech_Base::PerformPossessionSwap(APlayerController* DriverPC, APlayerController* GunnerPC)
{
	if (!DriverPC || !GunnerPC || !GunnerSeat) return;

	// Reseat FIRST so PossessedBy sees both pilots as legitimate crew and keeps the state.
	AssignToLeftSeat(GunnerPC);
	AssignToRightSeat(DriverPC);

	// The parked pawns travel with their pilots.
	Swap(ParkedDriverPawn, ParkedGunnerPawn);

	DriverPC->UnPossess();
	GunnerPC->UnPossess();
	GunnerPC->Possess(this);
	DriverPC->Possess(GunnerSeat);

	// Fresh eyes forward for the new gunner.
	DriverPC->SetControlRotation(GetActorRotation());

	UE_LOG(LogIronBreach, Display, TEXT("[Mech] Crew swap: %s now drives, %s now shoots."),
		*DescribeCrewName(GunnerPC), *DescribeCrewName(DriverPC));
}

// --- CONCORD ROUTING ---

bool AIBMech_Base::AreWeaponsSafetyLocked() const
{
	return Concord && Concord->AreHeavyWeaponsLocked();
}

void AIBMech_Base::SendRitualInput(EConcordRitualStep Step)
{
	if (HasAuthority())
	{
		if (Concord) { Concord->RegisterRitualInput(/*bFromDriver=*/true, Step); }
	}
	else
	{
		Server_SendRitualInput(Step);
	}
}

void AIBMech_Base::Server_SendRitualInput_Implementation(EConcordRitualStep Step)
{
	if (Concord) { Concord->RegisterRitualInput(/*bFromDriver=*/true, Step); }
}

// --- INPUT ROUTING (legacy single-machine gatekeeper) ---

void AIBMech_Base::RouteMoveInput(AController* Requester, const FVector2D& InputValue)
{
	if (!Requester || Requester != CurrentDriver) return;

	if (InputValue.Y != 0.0f)
	{
		AddMovementInput(GetActorForwardVector(), InputValue.Y);
	}
	if (InputValue.X != 0.0f)
	{
		AddMovementInput(GetActorRightVector(), InputValue.X);
	}
}

void AIBMech_Base::RouteLookInput(AController* Requester, const FVector2D& InputValue)
{
	if (!Requester) return;
	if (Requester != CurrentDriver && Requester != CurrentGunner) return;

	const bool bRequesterIsGunner = (Requester == CurrentGunner);

	if (bRequesterIsGunner)
	{
		APlayerController* PC = Cast<APlayerController>(Requester);
		if (!PC) return;

		if (InputValue.X != 0.0f)
		{
			FRotator ControlRot = PC->GetControlRotation();
			const float MechYaw = GetActorRotation().Yaw;

			const float CurrentDeltaYaw = FMath::UnwindDegrees(ControlRot.Yaw - MechYaw);
			const float NewDeltaYaw = FMath::Clamp(
				CurrentDeltaYaw + (InputValue.X * GunnerYawSensitivity),
				-GunnerYawLimit, GunnerYawLimit);

			ControlRot.Yaw = MechYaw + NewDeltaYaw;
			PC->SetControlRotation(ControlRot);
		}
		if (InputValue.Y != 0.0f)
		{
			AddControllerPitchInput(InputValue.Y);
		}
	}
	else
	{
		if (InputValue.X != 0.0f) AddControllerYawInput(InputValue.X);
		if (InputValue.Y != 0.0f) AddControllerPitchInput(InputValue.Y);
	}
}

void AIBMech_Base::FireWeapon(AController* Requester)
{
	if (!Requester || Requester != CurrentGunner) return;
	if (!CurrentCombatData) return;

	// Desync safety-lock (spec §3.2): heavy weapons refuse while the clasp is broken.
	if (AreWeaponsSafetyLocked())
	{
		OnWeaponsSafetyLocked();
		return;
	}

	if (WeaponCooldownRemaining > 0.0f) return;
	if (CurrentAmmo <= 0) return;

	CurrentAmmo--;
	// UWeaponCombatData already carries FireRate (seconds between shots) — use it, and only
	// fall back to the chassis default if the asset leaves it at zero.
	WeaponCooldownRemaining = (CurrentCombatData->FireRate > 0.0f) ? CurrentCombatData->FireRate : WeaponFireInterval;

	// Left/right heat tracking (folded in from the orphaned RouteFireInput).
	if (Requester == LeftSeatController)
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("[Mech] LEFT weapon systems fired."));
	}
	else if (Requester == RightSeatController)
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("[Mech] RIGHT weapon systems fired."));
	}

	PerformWeaponTrace();

	if (GEngine)
	{
		const FString DisplayName = CurrentVisualData && !CurrentVisualData->WeaponName.IsNone()
			? CurrentVisualData->WeaponName.ToString()
			: GetNameSafe(CurrentCombatData);
		GEngine->AddOnScreenDebugMessage(-1, 2.0f, FColor::Red,
			FString::Printf(TEXT("Firing %s! Damage: %.1f | Ammo: %d"),
				*DisplayName, CurrentCombatData->BaseDamage, CurrentAmmo));
	}
}

void AIBMech_Base::EquipWeapon(UWeaponCombatData* NewCombatData, UWeaponVisualData* NewVisualData)
{
	if (!NewCombatData && !NewVisualData) return;

	CurrentCombatData = NewCombatData;
	CurrentVisualData = NewVisualData;

	if (WeaponRigComponent && NewVisualData && NewVisualData->CombatData)
	{
		WeaponRigComponent->SetAdsSettings(NewVisualData->CombatData->Ads);
	}

	// The seat fires the same weapon — keep its component in step.
	if (GunnerSeat && GunnerSeat->WeaponComponent)
	{
		GunnerSeat->WeaponComponent->SetWeaponData(NewCombatData, NewVisualData);
	}
}

void AIBMech_Base::PerformWeaponTrace()
{
	UWorld* World = GetWorld();
	if (!World) return;

	FVector CamLoc;
	FRotator CamRot;

	// Trace from the GUNNER's viewpoint — not GetController()'s, which may be the driver.
	if (GunnerCamera_FPV && GunnerCamera_FPV->IsActive())
	{
		CamLoc = GunnerCamera_FPV->GetComponentLocation();
		CamRot = GunnerCamera_FPV->GetComponentRotation();
	}
	else if (APlayerController* GunnerPC = Cast<APlayerController>(CurrentGunner))
	{
		GunnerPC->GetPlayerViewPoint(CamLoc, CamRot);
	}
	else if (Controller)
	{
		Controller->GetPlayerViewPoint(CamLoc, CamRot);
	}
	else
	{
		CamLoc = GetActorLocation();
		CamRot = GetActorRotation();
	}

	const float Range = CurrentCombatData ? CurrentCombatData->MaxRange : 5000.0f;
	const FVector StartTrace = CamLoc;
	const FVector EndTrace = StartTrace + (CamRot.Vector() * Range);

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this);
	if (GunnerSeat) { QueryParams.AddIgnoredActor(GunnerSeat); }

	// ECC_Pawn: pawn capsules ignore ECC_Visibility — the same fix the infantry hitscan
	// needed. A mech cannon that can't hit characters is not a cannon.
	if (World->LineTraceSingleByChannel(HitResult, StartTrace, EndTrace, ECC_Pawn, QueryParams))
	{
#if ENABLE_DRAW_DEBUG
		DrawDebugLine(World, StartTrace, HitResult.Location, FColor::Cyan, false, 1.0f, 0, 0.3f);
		DrawDebugPoint(World, HitResult.Location, 10.0f, FColor::Red, false, 1.0f);
#endif

		// --- DAMAGE ---
		// Prefer the project damage seam: IDamageableInterface carries the FHitResult,
		// which is how the kaiju routes armor plates vs organ weak points. The generic
		// ApplyDamage path lands in HealthComponent's AnyDamage bridge and SKIPS both —
		// a mech cannon that ignores the boss fight's phases defeats the whole design.
		// Non-damageable actors still get the generic path as a fallback.
		AActor* HitActor = HitResult.GetActor();
		if (HitActor && CurrentCombatData)
		{
			if (HitActor->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass()))
			{
				IDamageableInterface::Execute_HandleTakeDamage(
					HitActor, CurrentCombatData->BaseDamage, HitResult, CurrentGunner, this);
			}
			else
			{
				UGameplayStatics::ApplyDamage(
					HitActor,
					CurrentCombatData->BaseDamage,
					CurrentGunner,
					this,
					UDamageType::StaticClass()
				);
			}
		}
	}
}

bool AIBMech_Base::TryEnterSeat(AController* InputController, bool bTargetLeftSeat)
{
	if (!InputController) return false;

	if (bTargetLeftSeat)
	{
		if (LeftSeatController == nullptr || LeftSeatController == InputController)
		{
			AssignToLeftSeat(InputController);
			return true;
		}
	}
	else
	{
		if (RightSeatController == nullptr || RightSeatController == InputController)
		{
			AssignToRightSeat(InputController);
			return true;
		}
	}
	return false; // Seat is already taken by someone else.
}

void AIBMech_Base::ChooseSeat(AController* SelectingController, bool bWantLeftSeat)
{
	if (!SelectingController) return;

	// Seat the human first.
	if (!TryEnterSeat(SelectingController, bWantLeftSeat))
	{
		// Requested seat was occupied — fall back to the other one rather than leaving
		// the player seated nowhere with no role.
		if (!TryEnterSeat(SelectingController, !bWantLeftSeat))
		{
			UE_LOG(LogIronBreach, Warning, TEXT("[Mech] Both seats occupied; %s could not board."),
				*GetNameSafe(SelectingController));
			return;
		}
	}

	// Backfill the AI into whatever's left.
	if (CoPilotController)
	{
		if (!LeftSeatController)       AssignToLeftSeat(CoPilotController);
		else if (!RightSeatController) AssignToRightSeat(CoPilotController);
	}

	ApplyLocalViewForRole(SelectingController);
}

void AIBMech_Base::SetGunnerViewActive(bool bGunnerView)
{
	// Null-safe: BP subclasses can end up with missing subobjects after a reparent/hot-reload,
	// and an unguarded Deactivate() on a null component is a hard crash on boarding.
	if (UCharacterMovementComponent* MechMovement = GetCharacterMovement())
	{
		MechMovement->bUseControllerDesiredRotation = !bGunnerView;
	}

	if (DriverCamera_3PV) DriverCamera_3PV->SetActive(!bGunnerView);
	if (GunnerCamera_FPV) GunnerCamera_FPV->SetActive(bGunnerView);
}

void AIBMech_Base::ApplyLocalViewForRole(AController* SelectingController)
{
	const bool bNowGunner = (SelectingController != nullptr && SelectingController == CurrentGunner);

	bIsGunner = bNowGunner;
	bIsDriverActive = !bNowGunner;

	SetGunnerViewActive(bNowGunner);
	OnRoleSwapped(bIsGunner);
}

void AIBMech_Base::ToggleViewMode()
{
	// Declared BlueprintCallable — UHT emits execToggleViewMode in the .gen.cpp, which
	// references this native symbol even if nothing calls it, so the body must exist.
	bIsDriverActive = !bIsDriverActive;
	bIsGunner = !bIsDriverActive;

	SetGunnerViewActive(bIsGunner);
	OnRoleSwapped(bIsGunner);
}
