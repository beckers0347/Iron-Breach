#include "IBCharacter_Infantry.h"
#include "IronBreach.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h" // PIP optic capture
#include "Engine/TextureRenderTarget2D.h"       // PIP optic render target
#include "Kismet/KismetRenderingLibrary.h"      // Runtime render target creation
#include "Materials/MaterialInterface.h"        // PIP screen material
#include "Materials/MaterialInstanceDynamic.h"  // Optional runtime RT binding
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h" // Explicit include: required for ULocalPlayer::GetSubsystem under IWYU
#include "Engine/World.h"       // Explicit include: required for LineTraceSingleByChannel under IWYU
#include "Combat/HealthComponent.h"
#include "Combat/HitscanWeaponComponent.h"
#include "Combat/WeaponRigComponent.h"
#include "Combat/WeaponDataAsset.h"
#include "Kismet/GameplayStatics.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h" // Auto-assign the default rifle viewmodel
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"

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

	// ---- PIP scope ----
	// Both halves hang off WeaponMesh, so the rig's per-frame viewmodel posing
	// carries them without any Tick work here. The real socket snap happens in
	// SetupScopePip(); the constructor only establishes the parent and the
	// defaults that must exist before the first frame renders.
	ScopeScreen = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ScopeScreen"));
	ScopeScreen->SetupAttachment(WeaponMesh);
	ScopeScreen->SetOnlyOwnerSee(true); // viewmodel-only, same as the weapon
	ScopeScreen->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ScopeScreen->bCastDynamicShadow = false;
	ScopeScreen->CastShadow = false;
	// The BP version's actual bug: bHiddenInGame defaulted true, and SetVisibility()
	// does not clear it — IsVisible() returned false forever. Set both, explicitly.
	ScopeScreen->SetHiddenInGame(false);
	ScopeScreen->SetVisibility(true);

	// Default to the engine plane so the component is never meshless (a null mesh
	// reports IsVisible() == true and draws nothing, which reads exactly like a
	// transform bug and is not one). Override the mesh in the BP if you want a
	// curved lens or a bezel.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
	if (PlaneMesh.Succeeded())
	{
		ScopeScreen->SetStaticMesh(PlaneMesh.Object);
	}

	ScopeCamera = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("ScopeCamera"));
	ScopeCamera->SetupAttachment(WeaponMesh);
	ScopeCamera->bCaptureEveryFrame = true;
	ScopeCamera->bCaptureOnMovement = false; // every-frame already covers it; both is wasted work
	ScopeCamera->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	ScopeCamera->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_RenderScenePrimitives;
	ScopeCamera->FOVAngle = 20.0f; // overwritten from ScopeFOV in SetupScopePip

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
		UE_LOG(LogIronBreach, Log, TEXT("[Character] WeaponRig found and valid!"));

		if (CurrentWeaponData)
		{
			WeaponRig->SetAdsSettings(CurrentWeaponData->Ads);
			UE_LOG(LogIronBreach, Log, TEXT("%s: ADS settings applied from %s"), *GetName(), *CurrentWeaponData->GetName());
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

	// Mount the optic once the viewmodel mesh is settled.
	SetupScopePip();

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

// ---- PIP scope ----

void AIBCharacter_Infantry::SetupScopePip()
{
	if (!ScopeScreen || !ScopeCamera || !WeaponMesh)
	{
		UE_LOG(LogIronBreach, Error, TEXT("%s: [Scope] components missing — check the constructor."), *GetName());
		return;
	}

	if (!bEnableScopePip)
	{
		SetScopePipEnabled(false);
		UE_LOG(LogIronBreach, Verbose, TEXT("%s: [Scope] disabled by bEnableScopePip."), *GetName());
		return;
	}

	// The optic is a local viewmodel prop. Remote clients and the dedicated server
	// gain nothing from a scene capture running every frame for a gun they can't see.
	if (!IsLocallyControlled())
	{
		SetScopePipEnabled(false);
		return;
	}

	// Snap to the socket, then correct in code. Snapping alone inherits whatever the
	// artist authored — including a socket whose +X points at the sky, which poses a
	// plane flat and invisible. The offsets below are the correction, in one readable place.
	const bool bSocketExists = WeaponMesh->DoesSocketExist(ScopeSocketName);
	const FName AttachSocket = bSocketExists ? ScopeSocketName : NAME_None;

	if (!bSocketExists)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("%s: [Scope] weapon mesh '%s' has no socket '%s' — mounting to the mesh root. Add the socket or clear bEnableScopePip."),
			*GetName(), *GetNameSafe(WeaponMesh->GetStaticMesh()), *ScopeSocketName.ToString());
	}

	const FAttachmentTransformRules Rules(EAttachmentRule::SnapToTarget, EAttachmentRule::SnapToTarget, EAttachmentRule::KeepWorld, false);
	ScopeScreen->AttachToComponent(WeaponMesh, Rules, AttachSocket);
	ScopeCamera->AttachToComponent(WeaponMesh, Rules, AttachSocket);

	// Screen: stand it up, face it at the eye, push it clear of the sight's baked glass.
	ScopeScreen->SetRelativeLocation(ScopeScreenOffset);
	ScopeScreen->SetRelativeRotation(ScopeScreenRotation);
	ScopeScreen->SetRelativeScale3D(ScopeScreenScale);
	ScopeScreen->SetHiddenInGame(false);
	ScopeScreen->SetVisibility(true);

	// The render target must exist BEFORE the material is bound: the parameterised
	// path below needs something to push into the texture parameter, and a null RT
	// silently demotes it to the plain-material path (which renders the engine's
	// default bubble texture and looks exactly like a broken capture).
	if (!ScopeRenderTarget)
	{
		const int32 Res = FMath::Clamp(ScopeRenderTargetResolution, 128, 2048);
		ScopeRenderTarget = UKismetRenderingLibrary::CreateRenderTarget2D(this, Res, Res, RTF_RGBA8);

		UE_LOG(LogIronBreach, Verbose,
			TEXT("%s: [Scope] created a %dx%d transient render target."), *GetName(), Res, Res);
	}

	if (!ScopeRenderTarget)
	{
		UE_LOG(LogIronBreach, Error,
			TEXT("%s: [Scope] render target creation failed — the capture has nowhere to write."), *GetName());
	}

	if (ScopeScreenMaterial)
	{
		if (ScopeTextureParameterName != NAME_None && ScopeRenderTarget)
		{
			// Parameterised path: one material serves every optic, each with its own RT.
			if (UMaterialInstanceDynamic* MID = ScopeScreen->CreateDynamicMaterialInstance(0, ScopeScreenMaterial))
			{
				MID->SetTextureParameterValue(ScopeTextureParameterName, ScopeRenderTarget);

				UE_LOG(LogIronBreach, Verbose,
					TEXT("%s: [Scope] bound '%s' -> parameter '%s'."),
					*GetName(), *GetNameSafe(ScopeRenderTarget), *ScopeTextureParameterName.ToString());
			}
		}
		else
		{
			// Hardwired path: the material samples its RT directly, no parameter.
			ScopeScreen->SetMaterial(0, ScopeScreenMaterial);

			UE_LOG(LogIronBreach, Warning,
				TEXT("%s: [Scope] no texture parameter bound (ScopeTextureParameterName='%s'). If the optic shows the engine's default texture, set this to the TextureSampleParameter2D's name on the material."),
				*GetName(), *ScopeTextureParameterName.ToString());
		}
	}
	else
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("%s: [Scope] no ScopeScreenMaterial assigned — the plane will render with the default material, not the optic feed."),
			*GetName());
	}

	// Capture: sits ahead of the screen looking downrange.
	ScopeCamera->SetRelativeLocation(ScopeCameraOffset);
	ScopeCamera->SetRelativeRotation(ScopeCameraRotation);
	ScopeCamera->FOVAngle = ScopeFOV;
	ScopeCamera->TextureTarget = ScopeRenderTarget;
	ScopeCamera->bCaptureEveryFrame = true;

	// Never let the capture see its own output: screen -> RT -> screen is a feedback
	// tunnel, and it costs a frame of latency even when it doesn't visibly recurse.
	ScopeCamera->HiddenComponents.Reset();
	ScopeCamera->HiddenComponents.Add(ScopeScreen);

	// The optic looks out at the world, not at the barrel two centimetres in front of it.
	if (bHideWeaponFromScopeCapture)
	{
		ScopeCamera->HiddenComponents.Add(WeaponMesh);
	}

	UE_LOG(LogIronBreach, Verbose,
		TEXT("%s: [Scope] mounted on '%s' | screen loc=%s rot=%s scale=%s | capture loc=%s fov=%.1f | RT=%s"),
		*GetName(),
		bSocketExists ? *ScopeSocketName.ToString() : TEXT("<mesh root>"),
		*ScopeScreen->GetRelativeLocation().ToString(),
		*ScopeScreen->GetRelativeRotation().ToString(),
		*ScopeScreen->GetRelativeScale3D().ToString(),
		*ScopeCamera->GetRelativeLocation().ToString(),
		ScopeFOV,
		*GetNameSafe(ScopeRenderTarget));
}

void AIBCharacter_Infantry::SetScopePipEnabled(bool bEnabled)
{
	if (ScopeScreen)
	{
		ScopeScreen->SetHiddenInGame(!bEnabled);
		ScopeScreen->SetVisibility(bEnabled);
	}
	if (ScopeCamera)
	{
		// Stopping the capture is the part that actually costs anything.
		ScopeCamera->bCaptureEveryFrame = bEnabled;
		ScopeCamera->SetComponentTickEnabled(bEnabled);
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
		// Menu keys deliberately NOT bound here: they live on AIBPlayerController
		// so they survive death and the infantry<->mech swap.
	}
	else
	{
		UE_LOG(LogIronBreach, Error, TEXT("%s: Expected an EnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini"), *GetName());
	}

	// Fallback so aim-down-sights works out of the box on RIGHT MOUSE without any
	// content setup. If an AimAction asset is assigned and bound above, this is skipped.
	if (!AimAction && PlayerInputComponent)
	{
		PlayerInputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &AIBCharacter_Infantry::StartAiming);
		PlayerInputComponent->BindKey(EKeys::RightMouseButton, IE_Released, this, &AIBCharacter_Infantry::StopAiming);
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
	UE_LOG(LogIronBreach, Log, TEXT("[Input] StartAiming called. WeaponRig valid: %s"), WeaponRig ? TEXT("Yes") : TEXT("No"));
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

// ---- Inventory -> weapon (loot-to-gun seam) ----

void AIBCharacter_Infantry::OnPlayerStateChanged(APlayerState* NewPlayerState, APlayerState* OldPlayerState)
{
	Super::OnPlayerStateChanged(NewPlayerState, OldPlayerState);

	// Rebind, don't accumulate: this pawn may be the Nth body this PlayerState
	// has driven (respawns), and on clients the PS can arrive after possession.
	if (BoundInventory.IsValid())
	{
		BoundInventory->OnEquipmentChanged.RemoveDynamic(this, &AIBCharacter_Infantry::HandleEquipmentChanged);
		BoundInventory = nullptr;
	}

	const AIBPlayerState* IBPS = Cast<AIBPlayerState>(NewPlayerState);
	UIBInventoryComponent* Inventory = IBPS ? IBPS->GetInventory() : nullptr;
	if (!Inventory) { return; } // not an IBPlayerState (e.g. Shane's default GM) — designer default stays

	Inventory->OnEquipmentChanged.AddDynamic(this, &AIBCharacter_Infantry::HandleEquipmentChanged);
	BoundInventory = Inventory;

	// Pull, don't just subscribe: the equip likely happened before this pawn
	// existed (menu equip -> death -> respawn). This is what makes loadouts
	// survive the corpse.
	FIBItemInstance Equipped;
	if (Inventory->GetEquippedItem(EIBEquipSlot::WeaponPrimary, Equipped))
	{
		HandleEquipmentChanged(EIBEquipSlot::WeaponPrimary, Equipped);
	}
}

void AIBCharacter_Infantry::HandleEquipmentChanged(EIBEquipSlot Slot, const FIBItemInstance& Item)
{
	if (Slot != EIBEquipSlot::WeaponPrimary)
	{
		return; // armor/gear slots are stat/cosmetic concerns — nothing to wire on the pawn yet
	}

	UWeaponDataAsset* NewData = (Item.Definition && Item.Definition->WeaponData)
		? Item.Definition->WeaponData.Get()
		: CurrentWeaponData.Get(); // slot emptied -> fall back to the designer default (never unarmed)

	ApplyWeaponData(NewData);
}

void AIBCharacter_Infantry::ApplyWeaponData(UWeaponDataAsset* WeaponData)
{
	if (!WeaponData) { return; }

	// Same two forwards BeginPlay does for the default loadout — one weapon
	// truth for firing (component) and one for feel (rig ADS settings).
	if (WeaponComponent)
	{
		WeaponComponent->SetWeaponData(WeaponData);
	}
	if (WeaponRig)
	{
		WeaponRig->SetAdsSettings(WeaponData->Ads);
	}

	// A new weapon means a new mesh and a new scope socket — re-snap the optic,
	// or it keeps hanging off wherever the last gun's socket happened to be.
	SetupScopePip();

	UE_LOG(LogIronBreach, Log, TEXT("%s: weapon set from equipment -> %s"), *GetName(), *WeaponData->GetName());
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

	// Kill the capture before the corpse: a scene capture rendering every frame
	// from a ragdolling gun is pure cost with nothing looking at it.
	SetScopePipEnabled(false);

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