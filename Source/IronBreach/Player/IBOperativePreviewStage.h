#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Player/IBCharacterTypes.h"
#include "IBOperativePreviewStage.generated.h"

class USkeletalMeshComponent;
class UStaticMeshComponent;
class USceneCaptureComponent2D;
class USpotLightComponent;
class UPointLightComponent;
class UTextureRenderTarget2D;
class USkeletalMesh;
class UAnimationAsset;

/**
 * The operative preview stage: a mannequin under three studio lights, filmed
 * by a scene capture into a render target the front-end sheets draw behind
 * their cards. Spawned far below the menu world while a sheet is open,
 * destroyed with it. Capture is ShowOnly (the mannequin alone), no sky / fog /
 * world lights, fixed exposure — the look is entirely this actor's, whatever
 * level the menu happens to run in.
 *
 * Male -> SKM_Manny_Simple (the infantry body), Female -> SKM_Quinn_Simple,
 * both on the shared mannequin skeleton with MM_Idle. Swap the soft paths on a
 * BP child when real operative bodies land.
 */
UCLASS()
class IRONBREACH_API AIBOperativePreviewStage : public AActor
{
	GENERATED_BODY()

public:
	AIBOperativePreviewStage();

	/** Spawn off-world (transient, local-only) and start capturing. */
	static AIBOperativePreviewStage* Spawn(UWorld* World);

	UFUNCTION(BlueprintPure, Category = "Operative")
	UTextureRenderTarget2D* GetRenderTarget() const { return RenderTarget; }

	/** Put a body on the stage; Accent tints the rim light (trade color). */
	UFUNCTION(BlueprintCallable, Category = "Operative")
	void ShowOperative(EIBOperativeGender Gender, FLinearColor Accent);

	UFUNCTION(BlueprintCallable, Category = "Operative")
	void ShowNothing();

	/** Inventory-only framing and the live infantry body's mesh/materials, plus
	 *  the weapon that body is actually carrying (its third-person mesh, same
	 *  socket and offset). Reads the pawn only; never modifies it or the
	 *  front-end preview's default framing. */
	void ConfigureForInventory(const USkeletalMeshComponent* SourceBody, const UStaticMeshComponent* SourceWeapon = nullptr);

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditDefaultsOnly, Category = "Preview")
	TSoftObjectPtr<USkeletalMesh> MaleMesh;

	UPROPERTY(EditDefaultsOnly, Category = "Preview")
	TSoftObjectPtr<USkeletalMesh> FemaleMesh;

	UPROPERTY(EditDefaultsOnly, Category = "Preview")
	TSoftObjectPtr<UAnimationAsset> IdleAnimation;

	UPROPERTY(EditDefaultsOnly, Category = "Preview")
	int32 RenderTargetSize = 1024;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<USceneComponent> StageRoot;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<USkeletalMeshComponent> Mesh;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<USceneCaptureComponent2D> Capture;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<USpotLightComponent> KeyLight;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<UPointLightComponent> FillLight;

	UPROPERTY(VisibleAnywhere, Category = "Preview")
	TObjectPtr<USpotLightComponent> RimLight;

	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> RenderTarget;

	/** Mirror of the pawn's third-person weapon, created on first use. */
	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> WeaponProp;

private:
	/** Plays the idle clip only when it fits the body's skeleton; otherwise runs the source
	 *  body's own animation class on the copied mesh, else holds the reference pose. */
	void ApplyIdlePose(const USkeletalMeshComponent* SourceBody);
	void SyncWeapon(const UStaticMeshComponent* SourceWeapon);

	/** Which body is loaded, so re-showing the same gender doesn't reload/restart the idle. */
	bool bHasBody = false;
	EIBOperativeGender LoadedGender = EIBOperativeGender::Male;
};
