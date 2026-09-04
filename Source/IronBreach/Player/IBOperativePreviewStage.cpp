#include "Player/IBOperativePreviewStage.h"
#include "IronBreach.h"
#include "Animation/AnimationAsset.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Kismet/KismetRenderingLibrary.h"

namespace
{
	// Where the body stands (feet at stage origin) and where the camera looks.
	const FVector BodyOrigin(0.f, 0.f, 0.f);
	const FVector LookTarget(0.f, 0.f, 98.f);

	FRotator LookAt(const FVector& From, const FVector& At)
	{
		return (At - From).Rotation();
	}
}

AIBOperativePreviewStage::AIBOperativePreviewStage()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = false;
	SetCanBeDamaged(false);

	StageRoot = CreateDefaultSubobject<USceneComponent>(TEXT("StageRoot"));
	RootComponent = StageRoot;

	// The body. Raw mannequin forward is +Y; the camera sits on -X, so +90 yaw
	// turns the face to the lens.
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Mesh->SetupAttachment(StageRoot);
	Mesh->SetRelativeLocationAndRotation(BodyOrigin, FRotator(0.f, 90.f, 0.f));
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetCastShadow(true);
	Mesh->SetVisibleInSceneCaptureOnly(true); // never leaks into the real view
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Mesh->SetVisibility(false);

	// Studio lights: warm key from front-left-high, cool fill front-right-low,
	// trade-colored rim from behind-right-high. Candelas at ~3 m against a
	// fixed EV0 exposure — small numbers on purpose.
	KeyLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("KeyLight"));
	KeyLight->SetupAttachment(StageRoot);
	KeyLight->SetRelativeLocation(FVector(-250.f, -190.f, 270.f));
	KeyLight->SetRelativeRotation(LookAt(FVector(-250.f, -190.f, 270.f), LookTarget));
	KeyLight->SetIntensityUnits(ELightUnits::Candelas);
	KeyLight->SetIntensity(68.f);
	KeyLight->SetLightColor(FLinearColor(1.0f, 0.93f, 0.84f));
	KeyLight->SetInnerConeAngle(18.f);
	KeyLight->SetOuterConeAngle(42.f);
	KeyLight->SetAttenuationRadius(1500.f);
	KeyLight->SetCastShadows(true);

	FillLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("FillLight"));
	FillLight->SetupAttachment(StageRoot);
	FillLight->SetRelativeLocation(FVector(-230.f, 230.f, 110.f));
	FillLight->SetIntensityUnits(ELightUnits::Candelas);
	FillLight->SetIntensity(14.f);
	FillLight->SetLightColor(FLinearColor(0.72f, 0.84f, 1.0f));
	FillLight->SetAttenuationRadius(1200.f);
	FillLight->SetCastShadows(false);

	RimLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("RimLight"));
	RimLight->SetupAttachment(StageRoot);
	RimLight->SetRelativeLocation(FVector(200.f, 140.f, 300.f));
	RimLight->SetRelativeRotation(LookAt(FVector(200.f, 140.f, 300.f), FVector(0.f, 0.f, 120.f)));
	RimLight->SetIntensityUnits(ELightUnits::Candelas);
	RimLight->SetIntensity(140.f);
	RimLight->SetLightColor(FLinearColor(0.25f, 0.75f, 0.85f));
	RimLight->SetInnerConeAngle(20.f);
	RimLight->SetOuterConeAngle(50.f);
	RimLight->SetAttenuationRadius(1500.f);
	RimLight->SetCastShadows(false);

	// The lens: full body, 30 degree horizontal FOV, a touch of downward tilt.
	// Aim from dead-center, then slide the lens 62 cm to the left (-Y): the body
	// lands right-of-center in the square, leaving the bottom-left corner for the
	// nameplate and the top-left for the title.
	Capture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("Capture"));
	Capture->SetupAttachment(StageRoot);
	Capture->SetRelativeRotation(LookAt(FVector(-440.f, 0.f, 105.f), LookTarget));
	Capture->SetRelativeLocation(FVector(-440.f, -62.f, 105.f));
	Capture->ProjectionType = ECameraProjectionMode::Perspective;
	Capture->FOVAngle = 30.f;
	Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Capture->bCaptureEveryFrame = true;
	Capture->bCaptureOnMovement = false;
	Capture->bAlwaysPersistRenderingState = true;

	// Nothing from the host world: no sky, fog, sun, skylight, auto-exposure.
	Capture->ShowFlags.SetAtmosphere(false);
	Capture->ShowFlags.SetFog(false);
	Capture->ShowFlags.SetVolumetricFog(false);
	Capture->ShowFlags.SetDirectionalLights(false);
	Capture->ShowFlags.SetSkyLighting(false);
	Capture->ShowFlags.SetEyeAdaptation(false);
	Capture->ShowFlags.SetMotionBlur(false);
	Capture->ShowFlags.SetBloom(false);
	Capture->ShowFlags.SetScreenSpaceReflections(false);
	Capture->ShowFlags.SetAmbientOcclusion(false);
	Capture->ShowFlags.SetLumenGlobalIllumination(false);
	Capture->ShowFlags.SetLumenReflections(false);
	Capture->ShowFlags.SetVignette(false);
	Capture->ShowFlags.SetGrain(false);

	Capture->PostProcessSettings.bOverride_AutoExposureMethod = true;
	Capture->PostProcessSettings.AutoExposureMethod = AEM_Manual;
	Capture->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
	Capture->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = false; // EV0, not the f/4 camera
	Capture->PostProcessSettings.bOverride_AutoExposureBias = true;
	Capture->PostProcessSettings.AutoExposureBias = 0.f;

	// Default bodies — the infantry's Manny and his counterpart Quinn, idle.
	MaleMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")));
	FemaleMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple")));
	IdleAnimation = TSoftObjectPtr<UAnimationAsset>(FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle")));
}

AIBOperativePreviewStage* AIBOperativePreviewStage::Spawn(UWorld* World)
{
	if (!World) { return nullptr; }

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.ObjectFlags |= RF_Transient;

	// Far from anything a menu level could contain; below world, off to the side.
	const FVector FarAway(180000.f, 180000.f, -60000.f);
	return World->SpawnActor<AIBOperativePreviewStage>(AIBOperativePreviewStage::StaticClass(), FarAway, FRotator::ZeroRotator, Params);
}

void AIBOperativePreviewStage::BeginPlay()
{
	Super::BeginPlay();

	RenderTarget = UKismetRenderingLibrary::CreateRenderTarget2D(this, RenderTargetSize, RenderTargetSize,
		ETextureRenderTargetFormat::RTF_RGBA8_SRGB, FLinearColor::Black, /*bAutoGenerateMipMaps=*/false);
	if (Capture)
	{
		Capture->TextureTarget = RenderTarget;
		Capture->ShowOnlyComponent(Mesh); // the body is the only thing the lens sees
	}
}

void AIBOperativePreviewStage::ShowOperative(EIBOperativeGender Gender, FLinearColor Accent)
{
	if (!Mesh) { return; }

	if (!bHasBody || LoadedGender != Gender)
	{
		USkeletalMesh* Body = (Gender == EIBOperativeGender::Female ? FemaleMesh : MaleMesh).LoadSynchronous();
		if (!Body)
		{
			UE_LOG(LogIronBreach, Warning, TEXT("PreviewStage: body mesh for %s failed to load"),
				*IBCharacter::GenderName(Gender).ToString());
			ShowNothing();
			return;
		}

		Mesh->SetSkeletalMeshAsset(Body);
		if (UAnimationAsset* Idle = IdleAnimation.LoadSynchronous())
		{
			Mesh->PlayAnimation(Idle, /*bLooping=*/true);
		}
		bHasBody = true;
		LoadedGender = Gender;
	}

	if (RimLight)
	{
		// The trade's color licks the shoulder line — the one cue that reads at a glance.
		FLinearColor Rim = Accent;
		Rim.A = 1.f;
		RimLight->SetLightColor(Rim);
	}

	Mesh->SetVisibility(true);
}

void AIBOperativePreviewStage::ShowNothing()
{
	if (Mesh)
	{
		Mesh->SetVisibility(false);
	}
}
