// ItemIconCaptureLibrary.cpp
#include "EditorTools/ItemIconCaptureLibrary.h"
#include "Items/IBItemDefinition.h"
#include "Combat/WeaponVisualData.h"
#include "EditorTools/WeaponGeneratorLibrary.h" // shared success/failure toast helper
#include "IronBreach.h"

#if WITH_EDITOR
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/PointLight.h"
#include "Components/PointLightComponent.h"
#include "Engine/SceneCapture2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "EditorAssetLibrary.h"
#include "Misc/Paths.h"
#endif

UTexture2D* UItemIconCaptureLibrary::CaptureItemIcon(UIBItemDefinition* Definition, int32 Resolution,
	float LightIntensity, float ExposureBias, FRotator MeshRotationOverride)
{
#if WITH_EDITOR
	if (!Definition)
	{
		return nullptr;
	}

	UWeaponVisualData* VisualData = Definition->VisualData;
	if (!VisualData)
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Icon capture failed: %s has no Visual Data assigned."), *Definition->GetName()), false);
		return nullptr;
	}

	UStaticMesh* Mesh = VisualData->ViewmodelMesh.LoadSynchronous();
	if (!Mesh)
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Icon capture failed: %s's weapon has no Viewmodel Mesh assigned yet."), *Definition->GetName()), false);
		return nullptr;
	}

	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(TEXT("Icon capture failed: no editor world available."), false);
		return nullptr;
	}

	// Spawned far above any real level geometry, and isolated further below via
	// PRM_UseShowOnlyList -- belt and braces so nothing from whatever level
	// happens to be open in the editor bleeds into the shot.
	const FVector LightboxOrigin(0.0f, 0.0f, 500000.0f);

	FActorSpawnParameters SpawnParams;
	SpawnParams.ObjectFlags |= RF_Transient;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AStaticMeshActor* MeshActor = World->SpawnActor<AStaticMeshActor>(LightboxOrigin, MeshRotationOverride, SpawnParams);
	if (!MeshActor || !MeshActor->GetStaticMeshComponent())
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(TEXT("Icon capture failed: could not spawn the lightbox mesh actor."), false);
		return nullptr;
	}
	MeshActor->SetActorEnableCollision(false);
	UStaticMeshComponent* MeshComp = MeshActor->GetStaticMeshComponent();
	MeshComp->SetMobility(EComponentMobility::Movable);
	MeshComp->SetStaticMesh(Mesh);

	const FBoxSphereBounds Bounds = MeshComp->Bounds;
	const float Radius = FMath::Max(Bounds.SphereRadius, 10.0f);
	const float CaptureDistance = Radius * 2.4f;

	// Fixed 3/4 product-shot angle -- deliberately NOT derived from the mesh's own
	// facing, since weapon meshes aren't authored to a consistent forward axis
	// (the same problem WeaponRigComponent's WeaponMountRotation corrects for
	// viewmodel posing). MeshRotationOverride is the escape hatch if this default
	// angle catches a particular weapon side-on or back-on.
	const FRotator ViewRotation(-20.0f, 215.0f, 0.0f);
	const FVector CameraLocation = Bounds.Origin - ViewRotation.Vector() * CaptureDistance;
	const FRotator CameraRotation = (Bounds.Origin - CameraLocation).Rotation();

	ASceneCapture2D* CaptureActor = World->SpawnActor<ASceneCapture2D>(CameraLocation, CameraRotation, SpawnParams);
	APointLight* KeyLight = World->SpawnActor<APointLight>(CameraLocation + FVector(0.0f, 0.0f, Radius * 1.5f), FRotator::ZeroRotator, SpawnParams);
	APointLight* FillLight = World->SpawnActor<APointLight>(
		Bounds.Origin + FVector(CaptureDistance * 0.4f, CaptureDistance * 0.7f, Radius * 0.3f), FRotator::ZeroRotator, SpawnParams);

	if (!CaptureActor || !CaptureActor->GetCaptureComponent2D() || !KeyLight || !FillLight)
	{
		if (MeshActor)    { MeshActor->Destroy(); }
		if (CaptureActor) { CaptureActor->Destroy(); }
		if (KeyLight)     { KeyLight->Destroy(); }
		if (FillLight)    { FillLight->Destroy(); }
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(TEXT("Icon capture failed: could not spawn the lightbox camera/lights."), false);
		return nullptr;
	}

	// Two-light rig so the icon has a consistent look regardless of whatever level
	// happens to be open -- not physically accurate, just legible and repeatable.
	KeyLight->GetLightComponent()->Intensity = LightIntensity;
	FillLight->GetLightComponent()->Intensity = LightIntensity * 0.5f;

	USceneCaptureComponent2D* Capture = CaptureActor->GetCaptureComponent2D();
	Capture->FOVAngle = 30.0f;
	Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	Capture->ShowOnlyActors.Add(MeshActor);
	Capture->bCaptureEveryFrame = false;
	Capture->bCaptureOnMovement = false;

	// Fixed exposure -- an isolated mesh against an empty backdrop confuses auto
	// exposure the same way the PIP scope capture did; don't let it guess here either.
	Capture->PostProcessSettings.bOverride_AutoExposureMethod = true;
	Capture->PostProcessSettings.AutoExposureMethod = AEM_Manual;
	Capture->PostProcessSettings.bOverride_AutoExposureBias = true;
	Capture->PostProcessSettings.AutoExposureBias = ExposureBias;

	UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>();
	RenderTarget->InitAutoFormat(Resolution, Resolution);
	RenderTarget->ClearColor = FLinearColor(0.045f, 0.045f, 0.055f, 1.0f); // neutral dark backdrop
	RenderTarget->UpdateResourceImmediate(true);
	Capture->TextureTarget = RenderTarget;

	Capture->CaptureScene();

	const FString CleanName = FPaths::MakeValidFileName(Definition->GetName());
	const FString DesiredPath = FString::Printf(TEXT("/Game/Items/Icons/Generated/T_Icon_%s"), *CleanName);

	UTexture2D* NewIcon = UKismetRenderingLibrary::RenderTargetCreateStaticTexture2DEditorOnly(
		RenderTarget, DesiredPath, TC_EditorIcon, TMGS_NoMipmaps);

	// Lightbox actors only need to exist for the single synchronous CaptureScene()
	// call above -- gone before anything else in the editor could even see them.
	MeshActor->Destroy();
	CaptureActor->Destroy();
	KeyLight->Destroy();
	FillLight->Destroy();

	if (!NewIcon)
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Icon capture failed: could not bake the render target for %s."), *Definition->GetName()), false);
		return nullptr;
	}

	// Defensive: RenderTargetCreateStaticTexture2DEditorOnly resolves Name into a
	// package path internally -- verify it landed where asked and correct it if
	// not, rather than silently saving somewhere unexpected.
	const FString ActualPath = NewIcon->GetOutermost()->GetName();
	if (ActualPath != DesiredPath && UEditorAssetLibrary::RenameAsset(ActualPath, DesiredPath))
	{
		if (UObject* Reloaded = UEditorAssetLibrary::LoadAsset(DesiredPath))
		{
			NewIcon = Cast<UTexture2D>(Reloaded);
		}
	}

	UEditorAssetLibrary::SaveLoadedAsset(NewIcon, /*bOnlyIfIsDirty=*/false);

	Definition->Icon = NewIcon;
	UEditorAssetLibrary::SaveLoadedAsset(Definition, /*bOnlyIfIsDirty=*/false);

	UE_LOG(LogIronBreach, Log, TEXT("Captured icon for %s -> %s"), *Definition->GetName(), *DesiredPath);
	UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(FString::Printf(TEXT("Captured icon for %s"), *Definition->GetName()), true);

	return NewIcon;
#else
	return nullptr;
#endif
}
