#include "IBCharacter_Infantry.h"
#include "IronBreach.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h" // Explicit include: ViewmodelMesh.LoadSynchronous() needs the complete UStaticMesh type
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
#include "Combat/WeaponCombatData.h"
#include "Combat/WeaponVisualData.h"
#include "Kismet/GameplayStatics.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h" // Auto-assign the default rifle viewmodel
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "Net/UnrealNetwork.h" // DOREPLIFETIME (ActiveWeaponSlot)

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

	// The template rifle is authored at full world scale. This is just the pre-data
	// default: BeginPlay/ApplyWeaponData overwrite it with CurrentVisualData's
	// ViewmodelScale so scale is a per-weapon, designer-facing knob (tune alongside
	// the rig's hip anchor — a smaller weapon sits closer to camera).
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
	// Explicitly the "render everything, minus HiddenComponents/HiddenActors" mode --
	// the OTHER two options on this enum (PRM_UseShowOnlyList / PRM_HideOnlyList) only
	// render primitives that are explicitly listed in ShowOnlyComponents/ShowOnlyActors,
	// which SetupScopePip() never populates (it only ever adds to HiddenComponents). If
	// this were resolving to either show-only mode, the capture would render nothing at
	// all -- a permanently blank/black render target -- regardless of camera position,
	// exactly the symptom this was chasing. PRM_LegacySceneCapture is the one guaranteed,
	// long-standing enum member that means "capture normally" across engine versions.
	ScopeCamera->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_LegacySceneCapture;
	ScopeCamera->FOVAngle = 20.0f; // overwritten from ScopeFOV in SetupScopePip

	// The third-person body should NOT render for the owning player (they see the viewmodel instead).
	GetMesh()->SetOwnerNoSee(true);

	// Crouch is off by default on UCharacterMovementComponent -- ACharacter::Crouch()
	// silently no-ops without this flag, which reads exactly like a missing binding.
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;

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

	// Re-assert here, not just in the constructor: BP_IBCharacter_Infantry's Character
	// Movement Component carries its own serialized override on top of this native class's
	// CDO (confirmed by CanEverCrouch() logging false at runtime despite the constructor
	// setting bCanCrouch = true). BeginPlay runs after the Blueprint's stored defaults have
	// already been applied to this instance, so setting it here wins regardless of what's
	// baked into the BP's component template. If someone later wants crouch fully disabled
	// again, this line -- not the constructor -- is the one to change.
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->NavAgentProps.bCanCrouch = true;
	}

	// The loadout property stays the designer-facing knob; the component does the firing.
	if (WeaponComponent && (CurrentCombatData || CurrentVisualData))
	{
		WeaponComponent->SetWeaponData(CurrentCombatData, CurrentVisualData);
	}

	// This path (the designer-default loadout) doesn't go through ApplyWeaponData,
	// so track it here too -- otherwise SetupScopePip() later in BeginPlay would
	// read a null EquippedVisualData and never find this weapon's PIP toggle/scale.
	if (CurrentVisualData) { EquippedVisualData = CurrentVisualData; }
	if (CurrentCombatData) { EquippedCombatData = CurrentCombatData; }

	// Swap in this weapon's viewmodel mesh before anything below reads socket
	// offsets off WeaponMesh -- scale and rig wiring both solve against whatever
	// mesh is currently attached.
	if (CurrentVisualData)
	{
		ApplyWeaponMesh(CurrentVisualData);
	}

	// Scale the viewmodel before the rig caches socket offsets below — GripLocal/AimLocal
	// are captured at whatever scale WeaponMesh has *right now*, so this must run first
	// or ADS alignment solves against the old (default) scale.
	if (WeaponMesh && CurrentVisualData)
	{
		WeaponMesh->SetRelativeScale3D(CurrentVisualData->ViewmodelScale);

		// TEMP DIAGNOSTIC (scale/location not visibly updating from DA_Visual edits):
		// confirms which asset BeginPlay actually resolved and what WeaponMesh's scale
		// reads back as immediately after we set it. If ReadBack != ViewmodelScale here,
		// something else (a BP Construction Script/EventGraph override, most likely) is
		// touching WeaponMesh's transform after this point. If ReadBack matches but the
		// gun still looks unchanged in PIE, the asset being edited isn't the one actually
		// resolved -- check the name logged here against what you're editing.
		UE_LOG(LogIronBreach, Warning,
			TEXT("[WeaponScaleDebug] BeginPlay: CurrentVisualData=%s ViewmodelScale=%s LocationOffset=%s RotationOffset=%s -> WeaponMesh ReadBack Scale=%s"),
			*CurrentVisualData->GetName(),
			*CurrentVisualData->ViewmodelScale.ToString(),
			*CurrentVisualData->ViewmodelLocationOffset.ToString(),
			*CurrentVisualData->ViewmodelRotationOffset.ToString(),
			*WeaponMesh->GetRelativeScale3D().ToString());
	}

	// Wire the first-person weapon rig: camera + viewmodel mesh + this weapon's ADS tuning.
	// SetReferences must run before SetAdsSettings so socket offsets (Grip/Aim) are cached
	// against the mesh that's actually attached before any pose math reads them.
	if (WeaponRig)
	{
		WeaponRig->SetReferences(FirstPersonCamera, WeaponMesh);
		UE_LOG(LogIronBreach, Log, TEXT("[Character] WeaponRig found and valid!"));

		if (CurrentVisualData)
		{
			WeaponRig->SetAdsSettings(ResolveAdsSettings(CurrentVisualData));
			WeaponRig->SetWeaponAlignmentOffset(CurrentVisualData->ViewmodelLocationOffset, CurrentVisualData->ViewmodelRotationOffset);
			UE_LOG(LogIronBreach, Log, TEXT("%s: ADS settings applied from %s"), *GetName(), *CurrentVisualData->GetName());
		}
		else
		{
			UE_LOG(LogIronBreach, Error, TEXT("%s: CurrentVisualData is NULL! Check Blueprint Class Defaults."), *GetName());
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

	// Spawn empty-handed (see bStartUnarmed's header comment) -- last thing in
	// BeginPlay so nothing above (scope pip mount, rig wiring) re-enables what this
	// turns off. The loot->gun seam (OnPlayerStateChanged/HandleEquipmentChanged)
	// re-arms this from the real inventory once the PlayerState/equipment catches up.
	if (bStartUnarmed)
	{
		SetUnarmed(true);
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
		UE_LOG(LogIronBreach, Verbose, TEXT("%s: [Scope] disabled by bEnableScopePip (character master switch)."), *GetName());
		return;
	}

	// Per-weapon override, on top of the character's master switch above: most
	// weapon meshes don't have a real lens/ScopeSocket authored, and forcing the
	// PIP on for one anyway mounts a floating render-target screen at the mesh
	// root instead of a lens (see the bSocketExists check below) -- which is
	// exactly what "PIP doesn't work" looks like for a weapon that was never
	// meant to have one. See UWeaponVisualData::bEnableScopePip/ScopePipSizeMultiplier.
	const UWeaponVisualData* Equipped = EquippedVisualData.Get();
	const bool bWeaponWantsScope = Equipped && Equipped->bEnableScopePip;
	if (!bWeaponWantsScope)
	{
		SetScopePipEnabled(false);
		UE_LOG(LogIronBreach, Verbose,
			TEXT("%s: [Scope] disabled -- %s."), *GetName(),
			Equipped ? TEXT("equipped weapon's bEnableScopePip is off") : TEXT("no equipped weapon tracked yet"));
		return;
	}
	// X/Y independent -- Z left at 1.0 since it's the plane's near-zero-thickness
	// axis and doesn't change what's visible on screen either way.
	const FVector PipSizeMultiplier(Equipped->ScopePipSizeMultiplier.X, Equipped->ScopePipSizeMultiplier.Y, 1.0f);

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

	if (!bSocketExists)
	{
		// This USED to fall back to mounting at the mesh root and hope for the best.
		// "Hope for the best" turned out to mean: the root of a custom-imported weapon
		// mesh is an arbitrary point the artist never authored as a lens position, so
		// ScopeScreenOffset/ScopeCameraOffset (tuned against an actual socket sitting at
		// the eyepiece) could land the screen anywhere -- including right on top of or
		// just in front of the camera, where a plane a few cm across covers half the
		// viewport through sheer proximity. That is exactly what "big black square
		// covering the left of the screen" looks like, and it's very likely every
		// custom weapon mesh hits this same fallback since none of them have a
		// 'ScopeSocket' authored yet. Disabling outright instead of guessing a position
		// converts a silently-broken visual into a clean off-state plus a fix path.
		SetScopePipEnabled(false);
		UE_LOG(LogIronBreach, Warning,
			TEXT("%s: [Scope] weapon mesh '%s' has no socket '%s' -- PIP disabled for this weapon rather than guessing a mount point. This weapon has bEnableScopePip on but no socket authored: add a socket named '%s' at the scope's eyepiece in the Static Mesh Editor (or on the skeleton, if this is a skeletal mesh), or turn bEnableScopePip off on its DA_Visual_* asset."),
			*GetName(), *GetNameSafe(WeaponMesh->GetStaticMesh()), *ScopeSocketName.ToString(), *ScopeSocketName.ToString());
		return;
	}

	const FAttachmentTransformRules Rules(EAttachmentRule::SnapToTarget, EAttachmentRule::SnapToTarget, EAttachmentRule::KeepWorld, false);
	ScopeScreen->AttachToComponent(WeaponMesh, Rules, ScopeSocketName);
	ScopeCamera->AttachToComponent(WeaponMesh, Rules, ScopeSocketName);

	// ScopeScreenOffset/ScopeCameraOffset/ScopeScreenScale are authored ONCE as
	// rig-wide constants, not per-weapon -- but they're set as RELATIVE transforms
	// on children now parented under WeaponMesh's socket, so Unreal composes them
	// through WeaponMesh's current world scale same as any other attached child.
	// A weapon whose ViewmodelScale is far from whatever these were tuned against
	// (exactly what the ViewmodelScale floor relaxation now allows) puts the optic
	// on top of the lens or shrinks the screen to nothing. Divide out WeaponMesh's
	// current scale here so the optic's WORLD position/size stays constant no
	// matter which weapon (or what scale it's authored at) is equipped.
	const FVector MeshScale = WeaponMesh->GetComponentScale();
	const FVector InvMeshScale(
		FMath::IsNearlyZero(MeshScale.X) ? 1.0f : 1.0f / MeshScale.X,
		FMath::IsNearlyZero(MeshScale.Y) ? 1.0f : 1.0f / MeshScale.Y,
		FMath::IsNearlyZero(MeshScale.Z) ? 1.0f : 1.0f / MeshScale.Z);

	// Screen: stand it up, face it at the eye, push it clear of the sight's baked glass.
	// PipSizeMultiplier is the per-weapon width/height knob (UWeaponVisualData::
	// ScopePipSizeMultiplier) -- applied on top of the InvMeshScale compensation so
	// a sniper's larger lens and a red dot's tiny one can differ, and so width and
	// height can be tuned independently, without touching the shared rig-wide constant.
	//
	// ScopeScreenRotationOffset/ScopeScreenLocationOffset (UWeaponVisualData) are the
	// per-weapon correction on top of the rig-wide ScopeScreenRotation/ScopeScreenOffset
	// constants above -- same reason ScopePipSizeMultiplier exists: ScopeSocket authoring
	// isn't consistent across meshes, so a single shared rotation only lands upright for
	// whichever weapon it happened to be tuned against. Composed the same order as
	// UWeaponRigComponent::UpdateWeaponPose composes PerWeaponMountOffset with
	// WeaponMountRotation -- per-weapon offset first, in the screen's own local space,
	// then the rig-wide constant on top -- so a weapon left at the offset defaults
	// behaves exactly as before this existed. The location offset is deliberately NOT
	// run through InvMeshScale, same as WeaponRigComponent's PerWeaponLocationOffset:
	// it's "shift the screen this many cm for this weapon," not a scale-relative nudge.
	const FQuat ScreenRotationQuat = ScopeScreenRotation.Quaternion() * Equipped->ScopeScreenRotationOffset.Quaternion();
	ScopeScreen->SetRelativeLocation((ScopeScreenOffset * InvMeshScale) + Equipped->ScopeScreenLocationOffset);
	ScopeScreen->SetRelativeRotation(ScreenRotationQuat.Rotator());
	ScopeScreen->SetRelativeScale3D(ScopeScreenScale * PipSizeMultiplier * InvMeshScale);
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
		// ALWAYS a dynamic instance now. The old "hardwired" path below used to
		// SetMaterial() the raw asset directly whenever ScopeTextureParameterName was
		// left at its NAME_None default -- which meant the screen never received the
		// live capture at all, it just showed whatever the material's Texture Sample
		// Parameter defaults to (black, for an unset default) forever. That is exactly
		// the "big black square" symptom -- the capture, positioning and render target
		// were all working, the screen was just never told to display them. A MID costs
		// nothing extra and is also where the shape-mask parameters below get pushed,
		// so there's one path now instead of two.
		if (UMaterialInstanceDynamic* MID = ScopeScreen->CreateDynamicMaterialInstance(0, ScopeScreenMaterial))
		{
			if (ScopeRenderTarget)
			{
				FName ResolvedParam = ScopeTextureParameterName;
				if (ResolvedParam == NAME_None)
				{
					// No parameter name configured -- auto-discover instead of silently
					// falling back to a black screen. Most optic materials only expose one
					// Texture Sample Parameter (the RT feed), so this covers the common case
					// without making ScopeTextureParameterName mandatory to get past black.
					TMap<FMaterialParameterInfo, FMaterialParameterMetadata> TextureParams;
					ScopeScreenMaterial->GetAllParametersOfType(EMaterialParameterType::Texture, TextureParams);

					if (TextureParams.Num() == 1)
					{
						ResolvedParam = TextureParams.CreateConstIterator()->Key.Name;
						UE_LOG(LogIronBreach, Verbose,
							TEXT("%s: [Scope] ScopeTextureParameterName not set -- auto-detected the material's only texture parameter '%s'."),
							*GetName(), *ResolvedParam.ToString());
					}
					else if (TextureParams.Num() > 1)
					{
						// Prefer one that looks meant for this; otherwise the first one found,
						// logged loudly since a silent guess here is exactly the kind of bug
						// this whole path exists to stop happening again.
						for (const TPair<FMaterialParameterInfo, FMaterialParameterMetadata>& Pair : TextureParams)
						{
							const FString NameStr = Pair.Key.Name.ToString();
							if (NameStr.Contains(TEXT("Scope")) || NameStr.Contains(TEXT("Texture")) || NameStr.Contains(TEXT("Screen")))
							{
								ResolvedParam = Pair.Key.Name;
								break;
							}
						}
						if (ResolvedParam == NAME_None)
						{
							ResolvedParam = TextureParams.CreateConstIterator()->Key.Name;
						}
						UE_LOG(LogIronBreach, Warning,
							TEXT("%s: [Scope] ScopeTextureParameterName not set and material '%s' exposes %d texture parameters -- guessed '%s'. Set ScopeTextureParameterName explicitly to be sure."),
							*GetName(), *GetNameSafe(ScopeScreenMaterial), TextureParams.Num(), *ResolvedParam.ToString());
					}
					else
					{
						UE_LOG(LogIronBreach, Error,
							TEXT("%s: [Scope] material '%s' has no Texture Sample Parameter at all -- the screen can only ever show a hardcoded texture, never the live capture. Add a Texture Sample Parameter 2D node to the material and expose it as a parameter."),
							*GetName(), *GetNameSafe(ScopeScreenMaterial));
					}
				}

				if (ResolvedParam != NAME_None)
				{
					MID->SetTextureParameterValue(ResolvedParam, ScopeRenderTarget);

					// SetTextureParameterValue() silently no-ops on a bad name -- there's no
					// error for that on its own. Read it back to catch a still-wrong guess/name.
					UTexture* Readback = nullptr;
					if (MID->GetTextureParameterValue(ResolvedParam, Readback))
					{
						UE_LOG(LogIronBreach, Verbose,
							TEXT("%s: [Scope] bound '%s' -> parameter '%s' on MID '%s' (base material '%s')."),
							*GetName(), *GetNameSafe(ScopeRenderTarget), *ResolvedParam.ToString(),
							*GetNameSafe(MID), *GetNameSafe(ScopeScreenMaterial));
					}
					else
					{
						UE_LOG(LogIronBreach, Error,
							TEXT("%s: [Scope] parameter '%s' does not exist on material '%s' — check the exact name of the Texture Sample Parameter node in the material graph (case-sensitive)."),
							*GetName(), *ResolvedParam.ToString(), *GetNameSafe(ScopeScreenMaterial));
					}
				}
			}

			// Shape mask, sourced from the equipped weapon's DA_Visual_* (Equipped is
			// guaranteed non-null here -- bWeaponWantsScope returned early otherwise).
			// Square is a no-op if the material was never wired for it (params just go
			// unused); Circle only actually masks anything once the material graph reads
			// these via a RadialGradientExponent node -- see
			// UWeaponVisualData::ScopePipShape's comment for the exact recipe.
			const bool bWantCircle = Equipped->ScopePipShape == EIBScopePipShape::Circle;
			MID->SetScalarParameterValue(TEXT("PipShapeIsCircle"), bWantCircle ? 1.0f : 0.0f);
			MID->SetScalarParameterValue(TEXT("PipCircleRadius"), Equipped->ScopePipCircleRadius);
		}
		else
		{
			UE_LOG(LogIronBreach, Error,
				TEXT("%s: [Scope] CreateDynamicMaterialInstance failed on slot 0 of ScopeScreen."), *GetName());
		}
	}
	else
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("%s: [Scope] no ScopeScreenMaterial assigned — the plane will render with the default material, not the optic feed."),
			*GetName());
	}

	// Capture: sits ahead of the screen looking downrange. Same InvMeshScale
	// compensation as the screen above -- keeps the capture's world offset from
	// the socket constant regardless of the equipped weapon's ViewmodelScale.
	//
	// ScopeCameraRotationOffset/ScopeCameraLocationOffset (UWeaponVisualData) are the
	// per-weapon correction on top of the rig-wide ScopeCameraRotation/ScopeCameraOffset
	// constants -- same composition order as the screen's own offsets above (per-weapon
	// first, in the camera's own local space, then the rig-wide constant on top), and
	// the fix for "screen faces the right way but shows a view aimed off to one side of
	// the reticle" -- that's the CAMERA's aim being wrong for this weapon's socket, not
	// the screen's rotation.
	const FQuat CameraRotationQuat = ScopeCameraRotation.Quaternion() * Equipped->ScopeCameraRotationOffset.Quaternion();
	ScopeCamera->SetRelativeLocation((ScopeCameraOffset * InvMeshScale) + Equipped->ScopeCameraLocationOffset);
	ScopeCamera->SetRelativeRotation(CameraRotationQuat.Rotator());
	// ScopeFOVOverride (UWeaponVisualData) lets one weapon's optic zoom in/out
	// differently from the rig-wide ScopeFOV constant -- 0 means "not set, use the
	// rig-wide value as authored," same fallback convention as ScopePipSizeMultiplier.
	const float ResolvedScopeFOV = (Equipped->ScopeFOVOverride > 0.0f) ? Equipped->ScopeFOVOverride : ScopeFOV;
	ScopeCamera->FOVAngle = ResolvedScopeFOV;
	ScopeCamera->TextureTarget = ScopeRenderTarget;
	ScopeCamera->bCaptureEveryFrame = true;
	// SetScopePipEnabled(false) -- called from every early-return guard clause above,
	// including the very first SetupScopePip() in BeginPlay before any weapon is
	// tracked yet -- also calls SetComponentTickEnabled(false) on ScopeCamera. USceneCapture
	// Component2D actually performs its per-frame capture from inside its OWN
	// TickComponent() override, so once that's been disabled once, setting
	// bCaptureEveryFrame back to true here is NOT enough to resume capturing --
	// the component's Tick itself has to be turned back on too, or CaptureScene()
	// never runs again and the render target sits frozen at its initial (black)
	// clear color forever, no matter how correct the position/material/render-mode
	// setup is. This is very likely why the PIP has read as a dead black square
	// this entire session regardless of what else got changed.
	ScopeCamera->SetComponentTickEnabled(true);

	UE_LOG(LogIronBreach, Verbose, TEXT("%s: [Scope] ScopeCamera->TextureTarget = %s"),
		*GetName(), *GetNameSafe(ScopeCamera->TextureTarget));

	// Scene captures pick up whatever PostProcessVolume covers their world position —
	// including a level's Manual-exposure volume tuned for the main camera's framing.
	// That is a different scene (a tight zoomed box a few cm from the muzzle) and Manual
	// mode with no Aperture/Shutter/ISO calibration for THIS framing reads as solid black.
	// Force the capture onto its own Auto exposure so the optic looks correct regardless
	// of what post-processing the level around it happens to use.
	ScopeCamera->PostProcessBlendWeight = 1.0f;
	ScopeCamera->PostProcessSettings.bOverride_AutoExposureMethod = true;
	ScopeCamera->PostProcessSettings.AutoExposureMethod = AEM_Histogram;
	ScopeCamera->PostProcessSettings.bOverride_AutoExposureBias = true;
	ScopeCamera->PostProcessSettings.AutoExposureBias = ScopeExposureBias;

	UE_LOG(LogIronBreach, Verbose, TEXT("%s: [Scope] AutoExposureBias applied = %.2f"), *GetName(), ScopeCamera->PostProcessSettings.AutoExposureBias);

	// Never let the capture see its own output: screen -> RT -> screen is a feedback
	// tunnel, and it costs a frame of latency even when it doesn't visibly recurse.
	ScopeCamera->HiddenComponents.Reset();
	ScopeCamera->HiddenComponents.Add(ScopeScreen);

	// The optic looks out at the world, not at the barrel two centimetres in front of it.
	if (bHideWeaponFromScopeCapture)
	{
		ScopeCamera->HiddenComponents.Add(WeaponMesh);
	}

	// Logged at Warning (not Verbose) for now -- the world-scale figure here is the
	// single most useful number for diagnosing "PIP is huge/tiny": it's what the
	// screen ACTUALLY measures in world cm regardless of the weapon's ViewmodelScale,
	// since ScopeScreen->GetComponentScale() already has WeaponMesh's scale folded
	// back in. A Plane primitive is ~100uu (1m) per side at scale 1.0, so e.g. a
	// world scale of 0.04 -> a ~4uu (4cm) screen; if this number is much bigger than
	// expected, ScopeScreenScale/ScopePipSizeMultiplier are set too high, not a
	// mesh-scale bug. Drop back to Verbose once the sizing is confirmed correct.
	UE_LOG(LogIronBreach, Warning,
		TEXT("%s: [Scope] mounted on '%s' | screen loc=%s rot=%s relScale=%s worldScale=%s | capture loc=%s fov=%.1f | RT=%s"),
		*GetName(),
		*ScopeSocketName.ToString(),
		*ScopeScreen->GetRelativeLocation().ToString(),
		*ScopeScreen->GetRelativeRotation().ToString(),
		*ScopeScreen->GetRelativeScale3D().ToString(),
		*ScopeScreen->GetComponentScale().ToString(),
		*ScopeCamera->GetRelativeLocation().ToString(),
		ResolvedScopeFOV,
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

void AIBCharacter_Infantry::SetWeaponMeshScale(FVector NewScale)
{
	if (!WeaponMesh)
	{
		UE_LOG(LogIronBreach, Error, TEXT("%s: SetWeaponMeshScale called with no WeaponMesh."), *GetName());
		return;
	}

	WeaponMesh->SetRelativeScale3D(NewScale);

	// TEMP DIAGNOSTIC (scale/location not visibly updating from DA_Visual edits): this
	// is the one place scale actually gets set from an equipped weapon (BeginPlay's
	// default-loadout path calls SetRelativeScale3D directly, everything else -- equip
	// changes, active-slot switches -- routes through here). If ReadBack below doesn't
	// match NewScale, something ran between this call and the log and reset it; if it
	// matches but the gun still looks the same size in PIE, the mesh itself isn't
	// changing -- check ApplyWeaponMesh actually swapped WeaponMesh's StaticMesh.
	UE_LOG(LogIronBreach, Warning,
		TEXT("[WeaponScaleDebug] SetWeaponMeshScale: requested=%s -> WeaponMesh ReadBack Scale=%s (mesh=%s)"),
		*NewScale.ToString(), *WeaponMesh->GetRelativeScale3D().ToString(), *GetNameSafe(WeaponMesh->GetStaticMesh()));

	// The rig caches Grip/Aim socket offsets in SetReferences() and does not track
	// scale changes on its own — re-cache now so hip/ADS pose keeps landing on the
	// authored anchor instead of drifting off it at the new size.
	if (WeaponRig)
	{
		WeaponRig->SetReferences(FirstPersonCamera, WeaponMesh);
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
		if (CrouchAction)
		{
			// Hold to crouch, same Started/Completed pattern as Sprint/Aim. Swap to a
			// single Triggered bind that flips bIsCrouched if you'd rather have toggle-crouch.
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::StartCrouch);
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Completed, this, &AIBCharacter_Infantry::StopCrouch);
			EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Canceled, this, &AIBCharacter_Infantry::StopCrouch);
		}
		else
		{
			UE_LOG(LogIronBreach, Error, TEXT("%s: CrouchAction not assigned -- Crouch will do nothing. Set it in Class Defaults > Input > Crouch Action."), *GetName());
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

	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		// Guarded like every other action above: binding a null UInputAction here
		// used to fail with no log line, so "hold shift does nothing" gave zero
		// clue whether SprintAction was actually unassigned. Now it says so.
		if (SprintAction)
		{
			EIC->BindAction(SprintAction, ETriggerEvent::Started, this, &AIBCharacter_Infantry::StartSprint);
			EIC->BindAction(SprintAction, ETriggerEvent::Completed, this, &AIBCharacter_Infantry::StopSprint);
		}
		else
		{
			UE_LOG(LogIronBreach, Error, TEXT("%s: SprintAction not assigned -- Shift/Sprint will do nothing. Set it in Class Defaults > Input > Sprint Action."), *GetName());
		}
	}

	// Weapon wells on 1/2/3 (Primary/Special/Heavy). Raw keys on purpose: the
	// slot grammar should work the moment the build boots, no IA assets needed.
	if (PlayerInputComponent)
	{
		PlayerInputComponent->BindKey(EKeys::One,   IE_Pressed, this, &AIBCharacter_Infantry::SelectPrimarySlot);
		PlayerInputComponent->BindKey(EKeys::Two,   IE_Pressed, this, &AIBCharacter_Infantry::SelectSpecialSlot);
		PlayerInputComponent->BindKey(EKeys::Three, IE_Pressed, this, &AIBCharacter_Infantry::SelectHeavySlot);
	}
}

void AIBCharacter_Infantry::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBCharacter_Infantry, ActiveWeaponSlot);
}

void AIBCharacter_Infantry::SetActiveWeaponSlot(EIBEquipSlot NewSlot)
{
	if (NewSlot == ActiveWeaponSlot) { return; }
	if (NewSlot != EIBEquipSlot::WeaponPrimary &&
	    NewSlot != EIBEquipSlot::WeaponSpecial &&
	    NewSlot != EIBEquipSlot::WeaponHeavy)
	{
		return; // wells only
	}

	if (HasAuthority())
	{
		Server_SetActiveWeaponSlot_Implementation(NewSlot);
	}
	else
	{
		Server_SetActiveWeaponSlot(NewSlot);
	}
}

void AIBCharacter_Infantry::Server_SetActiveWeaponSlot_Implementation(EIBEquipSlot NewSlot)
{
	// An empty non-primary well is not a weapon: refuse the switch instead of
	// handing the player the designer-default rifle labeled "Heavy".
	if (NewSlot != EIBEquipSlot::WeaponPrimary)
	{
		FIBItemInstance Equipped;
		if (!BoundInventory.IsValid() || !BoundInventory->GetEquippedItem(NewSlot, Equipped) || !Equipped.Definition)
		{
			UE_LOG(LogIronBreach, Verbose, TEXT("%s: slot switch refused — nothing equipped in that well"), *GetName());
			return;
		}
	}

	ActiveWeaponSlot = NewSlot;
	ApplyActiveSlot();          // server truth for damage
	OnRep_ActiveWeaponSlot();   // listen-server host mirrors the cosmetic side
}

void AIBCharacter_Infantry::OnRep_ActiveWeaponSlot()
{
	ApplyActiveSlot();
}

void AIBCharacter_Infantry::ApplyActiveSlot()
{
	// With a real inventory, the well is the truth: empty well = empty hands.
	// Without one (Shane's default-GM test maps), the designer default stays.
	if (BoundInventory.IsValid())
	{
		FIBItemInstance Equipped;
		if (BoundInventory->GetEquippedItem(ActiveWeaponSlot, Equipped) && Equipped.Definition)
		{
			SetUnarmed(false);
			UWeaponVisualData* ResolvedVisual = ResolveVisualData(Equipped.Definition.Get());
			UWeaponCombatData* ResolvedCombat = ResolveCombatData(Equipped.Definition.Get(), ResolvedVisual);
			ApplyWeaponData(
				ResolvedCombat ? ResolvedCombat : CurrentCombatData.Get(),
				ResolvedVisual ? ResolvedVisual : CurrentVisualData.Get());
		}
		else
		{
			SetUnarmed(true);
		}
		return;
	}

	SetUnarmed(false);
	ApplyWeaponData(CurrentCombatData.Get(), CurrentVisualData.Get());
}

void AIBCharacter_Infantry::SetUnarmed(bool bNewUnarmed)
{
	if (bUnarmed == bNewUnarmed) { return; }
	bUnarmed = bNewUnarmed;

	if (WeaponMesh)
	{
		WeaponMesh->SetVisibility(!bUnarmed, /*bPropagateToChildren=*/true);
	}
	if (bUnarmed)
	{
		SetScopePipEnabled(false); // rearm path re-runs SetupScopePip via ApplyWeaponData
	}

	UE_LOG(LogIronBreach, Log, TEXT("%s: %s"), *GetName(), bUnarmed ? TEXT("unarmed (well empty)") : TEXT("re-armed"));
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
	if (bIsSprinting)
	{
		return; // can't start aiming while sprinting
	}

	bIsAiming = true;

	UE_LOG(LogIronBreach, Log, TEXT("[Input] StartAiming called. WeaponRig valid: %s"), WeaponRig ? TEXT("Yes") : TEXT("No"));
	if (WeaponRig) WeaponRig->SetAiming(true);
}

void AIBCharacter_Infantry::StopAiming()
{
	// bIsAiming was never cleared here, so it stuck true forever after the first ADS,
	// permanently blocking StartSprint()'s "can't sprint while aiming" guard.
	bIsAiming = false;

	if (WeaponRig) WeaponRig->SetAiming(false);
}

void AIBCharacter_Infantry::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Single source of truth for MaxWalkSpeed: base walk speed run through the ADS
	// multiplier (slower while aiming) and the sprint multiplier (faster while
	// sprinting). This used to be split between here (ADS, every tick) and
	// StartSprint/StopSprint (a one-time direct set) — Tick ran the frame right
	// after Start/StopSprint and silently overwrote the sprint speed back to walk
	// speed, since the ADS multiplier is 1.0 while not aiming. bIsSprinting still
	// flipped correctly (gating Fire/Aim), the character just never sped up.
	if (BaseWalkSpeed > 0.0f)
	{
		if (UCharacterMovementComponent* Move = GetCharacterMovement())
		{
			const float AdsMultiplier = WeaponRig ? WeaponRig->GetMoveSpeedMultiplier() : 1.0f;
			const float SprintMultiplier = (bIsSprinting && NormalWalkSpeed > 0.0f) ? (SprintSpeed / NormalWalkSpeed) : 1.0f;
			Move->MaxWalkSpeed = BaseWalkSpeed * AdsMultiplier * SprintMultiplier;
		}
	}
}

void AIBCharacter_Infantry::Fire()
{
	if (bIsSprinting || bUnarmed)
	{
		return; // empty hands don't shoot
	}
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
	if (!Inventory)
	{
		// Not a real IBPlayerState (e.g. Shane's default-GM test maps) -- there's no
		// loot->gun seam to ever re-arm from here, so bStartUnarmed's BeginPlay call
		// would otherwise leave the pawn (and the scope pip, which SetUnarmed(true)
		// switches off) unarmed for good. Re-run ApplyActiveSlot()'s own no-inventory
		// branch (BoundInventory is null at this point) to bring back the designer
		// default -- and, via ApplyWeaponData's SetupScopePip() call, the pip -- same
		// as before bStartUnarmed existed.
		ApplyActiveSlot();
		return;
	}

	Inventory->OnEquipmentChanged.AddDynamic(this, &AIBCharacter_Infantry::HandleEquipmentChanged);
	BoundInventory = Inventory;

	// Pull, don't just subscribe: the equip likely happened before this pawn
	// existed (menu equip -> death -> respawn). This is what makes loadouts
	// survive the corpse.
	FIBItemInstance Equipped;
	if (Inventory->GetEquippedItem(ActiveWeaponSlot, Equipped))
	{
		HandleEquipmentChanged(ActiveWeaponSlot, Equipped);
	}
}

void AIBCharacter_Infantry::HandleEquipmentChanged(EIBEquipSlot Slot, const FIBItemInstance& Item)
{
	if (Slot != ActiveWeaponSlot)
	{
		return; // armor/gear/off-hand wells are stat/cosmetic concerns until they're the active slot
	}

	// Slot emptied with a real inventory -> truly unarmed (Shane's storage
	// loop: the gun must leave your hands). The old designer-default fallback
	// only applies where no inventory exists at all (ApplyActiveSlot handles
	// that path); here we KNOW there's an inventory — it just signaled us.
	if (!Item.Definition)
	{
		SetUnarmed(true);
		return;
	}

	UWeaponVisualData* NewVisualData = ResolveVisualData(Item.Definition.Get());
	UWeaponCombatData* NewCombatData = ResolveCombatData(Item.Definition.Get(), NewVisualData);
	if (!NewVisualData) { NewVisualData = CurrentVisualData.Get(); }
	if (!NewCombatData) { NewCombatData = CurrentCombatData.Get(); } // item with no combat data yet -> keep the floor

	SetUnarmed(false);
	ApplyWeaponData(NewCombatData, NewVisualData);
}

UWeaponVisualData* AIBCharacter_Infantry::ResolveVisualData(const UIBItemDefinition* Definition) const
{
	if (!Definition) { return nullptr; }

	// Current pattern: the rack/inventory point directly at a DA_Visual_* asset,
	// which IS the item definition now (UWeaponVisualData : public UIBItemDefinition
	// -- see that class's comment). Nothing to look up; the item itself is the answer.
	if (const UWeaponVisualData* AsVisual = Cast<UWeaponVisualData>(Definition))
	{
		return const_cast<UWeaponVisualData*>(AsVisual);
	}

	// Legacy pattern: an old DA_Item_* wrapper still carrying its own (deprecated)
	// VisualData link -- content that hasn't been migrated/re-pointed yet.
	return Definition->VisualData.Get();
}

UWeaponCombatData* AIBCharacter_Infantry::ResolveCombatData(const UIBItemDefinition* Definition, UWeaponVisualData* ResolvedVisual) const
{
	// Current pattern: Combat is reached through the resolved Visual asset's own link.
	if (ResolvedVisual && ResolvedVisual->CombatData)
	{
		return ResolvedVisual->CombatData.Get();
	}

	// Legacy pattern: the DA_Item_* wrapper's own (deprecated) Combat link.
	return Definition ? Definition->LegacyCombatData.Get() : nullptr;
}

FIBAdsSettings AIBCharacter_Infantry::ResolveAdsSettings(const UWeaponVisualData* VisualData) const
{
	// Ads lives on the linked CombatData asset (see WeaponCombatData.h). The old
	// deprecated UWeaponVisualData::Ads field has been removed -- a weapon with no
	// CombatData link just gets default ADS tuning rather than a stale/duplicate
	// value that could silently disagree with the Combat asset.
	if (VisualData && VisualData->CombatData)
	{
		return VisualData->CombatData->Ads;
	}

	return FIBAdsSettings();
}

void AIBCharacter_Infantry::ApplyWeaponData(UWeaponCombatData* CombatData, UWeaponVisualData* VisualData)
{
	if (!CombatData && !VisualData) { return; }

	// Track what's actually equipped (unlike CurrentCombatData/CurrentVisualData,
	// which stay pinned to the designer-default floor) so SetupScopePip() can read
	// the equipped weapon's own PIP toggle/scale, and so the editor-only live-tune
	// binding below always rebinds to the right asset.
#if WITH_EDITOR
	// Live-tune: (re)bind to whichever VisualData is being applied so editing its
	// ViewmodelScale/alignment-offset/ViewmodelMesh in the editor re-runs this same
	// apply path on a running PIE session -- see RefreshLiveTunedWeapon. Only rebind
	// the delegate when the asset itself changed.
	if (VisualData && VisualData != EquippedVisualData.Get())
	{
		if (UWeaponVisualData* Previous = EquippedVisualData.Get())
		{
			Previous->OnVisualDataChanged.RemoveAll(this);
		}
		VisualData->OnVisualDataChanged.AddUObject(this, &AIBCharacter_Infantry::RefreshLiveTunedWeapon);
	}
#endif
	if (VisualData)
	{
		EquippedVisualData = VisualData;
		EquippedCombatData = CombatData;
	}

	// Same two forwards BeginPlay does for the default loadout — one weapon
	// truth for firing (component) and one for feel (rig ADS settings).
	if (WeaponComponent)
	{
		WeaponComponent->SetWeaponData(CombatData, VisualData);
	}

	if (VisualData)
	{
		if (WeaponRig)
		{
			WeaponRig->SetAdsSettings(ResolveAdsSettings(VisualData));
			WeaponRig->SetWeaponAlignmentOffset(VisualData->ViewmodelLocationOffset, VisualData->ViewmodelRotationOffset);
		}

		// New weapon, new mesh — swap it in before scale/rig/scope below all re-solve
		// against whatever's attached. No-ops (keeps the current mesh) if this weapon
		// has no ViewmodelMesh assigned yet.
		ApplyWeaponMesh(VisualData);

		// Apply this weapon's viewmodel scale (also re-caches the rig's Grip/Aim socket
		// offsets — see SetWeaponMeshScale) before re-snapping the optic below, so the
		// scope mounts against the mesh at its final size, not the previous weapon's.
		SetWeaponMeshScale(VisualData->ViewmodelScale);
	}

	// A new weapon means a new mesh and a new scope socket — re-snap the optic,
	// or it keeps hanging off wherever the last gun's socket happened to be.
	SetupScopePip();

	UE_LOG(LogIronBreach, Log, TEXT("%s: weapon set from equipment -> combat=%s visual=%s"),
		*GetName(), *GetNameSafe(CombatData), *GetNameSafe(VisualData));
}

#if WITH_EDITOR
void AIBCharacter_Infantry::RefreshLiveTunedWeapon()
{
	// UWeaponVisualData::OnVisualDataChanged fired -- re-run the exact same apply
	// path BeginPlay/equip already use, with whatever this weapon was last paired
	// with, so ViewmodelScale/alignment-offset/ViewmodelMesh edits show up on a
	// running PIE session immediately instead of needing a restart.
	if (UWeaponVisualData* Visual = EquippedVisualData.Get())
	{
		ApplyWeaponData(EquippedCombatData.Get(), Visual);
	}
}
#endif

void AIBCharacter_Infantry::ApplyWeaponMesh(UWeaponVisualData* VisualData)
{
	if (!WeaponMesh || !VisualData)
	{
		return;
	}

	if (VisualData->ViewmodelMesh.IsNull())
	{
		// No mesh authored for this weapon yet (e.g. freshly generated, no art
		// assigned) -- keep whatever's currently shown rather than going blank.
		return;
	}

	if (UStaticMesh* NewMesh = VisualData->ViewmodelMesh.LoadSynchronous())
	{
		WeaponMesh->SetStaticMesh(NewMesh);
	}
	else
	{
		UE_LOG(LogIronBreach, Warning, TEXT("%s: ViewmodelMesh on %s failed to load -- keeping previous mesh."),
			*GetName(), *VisualData->GetName());
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

void AIBCharacter_Infantry::StartSprint()
{
	if (bIsAiming || bIsCrouched)
	{
		return; // can't sprint while aiming or crouched
	}

	bIsSprinting = true;
	// MaxWalkSpeed is now driven exclusively by Tick() (base * ADS multiplier *
	// sprint multiplier) so nothing overwrites it a frame later — see Tick().

	if (WeaponRig)
	{
		WeaponRig->SetSprinting(true); // blends the viewmodel to the tucked-in sprint pose
	}
}

void AIBCharacter_Infantry::StopSprint()
{
	bIsSprinting = false;

	if (WeaponRig)
	{
		WeaponRig->SetSprinting(false); // blends back out of the sprint pose
	}
}

void AIBCharacter_Infantry::StartCrouch()
{
	if (bIsSprinting)
	{
		StopSprint(); // dropping into crouch cancels an active sprint, same as ADS does
	}

	Crouch(); // ACharacter builtin: handles capsule half-height + bIsCrouched (replicated)
}

void AIBCharacter_Infantry::StopCrouch()
{
	UnCrouch();
}