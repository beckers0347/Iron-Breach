#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Classes/IBClassKitTypes.h"
#include "IBKitZone.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInterface;
class ACharacter;

/**
 * The built-in pylon for EIBKitEffect::DeployZone: a disc + post + colored
 * light, replicated to everyone, that pulses every quarter second and does two
 * things to HOSTILE characters inside its radius — slows them (MaxWalkSpeed ×
 * SlowFactor, restored on exit/expiry; server-only) and/or marks them (Custom
 * Depth stencil 1, every machine, for an outline post-process to pick up).
 * Infantry are never affected. Subclass in BP for a real look.
 */
UCLASS()
class IRONBREACH_API AIBKitZone : public AActor
{
	GENERATED_BODY()

public:
	AIBKitZone();

	/** Server: configure from the spec and arm the pulse. */
	void InitZone(const FIBKitAbilitySpec& Spec, const FLinearColor& InAccent, AActor* InOwnerPawn);

	UFUNCTION(BlueprintPure, Category = "Kit")
	float GetRadius() const { return Radius; }

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_Look();

	void ApplyLook();
	void Pulse();
	void ReleaseAll();
	bool IsHostile(const ACharacter* Character) const;

	UPROPERTY(VisibleAnywhere, Category = "Zone")
	TObjectPtr<USceneComponent> ZoneRoot;

	UPROPERTY(VisibleAnywhere, Category = "Zone")
	TObjectPtr<UStaticMeshComponent> Disc;

	UPROPERTY(VisibleAnywhere, Category = "Zone")
	TObjectPtr<UStaticMeshComponent> Post;

	UPROPERTY(VisibleAnywhere, Category = "Zone")
	TObjectPtr<UPointLightComponent> Light;

	/** Unlit glow material (M_IBKitZone: Color * Glow -> emissive, Opacity); missing -> the engine's lit shapes, tinted. */
	UPROPERTY(EditDefaultsOnly, Category = "Zone")
	TSoftObjectPtr<UMaterialInterface> ZoneMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> ResolvedZoneMaterial;
	bool bZoneMaterialResolved = false;

	UMaterialInterface* ResolveZoneMaterial();

	UPROPERTY(ReplicatedUsing = OnRep_Look)
	float Radius = 500.f;

	UPROPERTY(ReplicatedUsing = OnRep_Look)
	FLinearColor Accent = FLinearColor::White;

	UPROPERTY(Replicated)
	float SlowFactor = 1.f;

	UPROPERTY(Replicated)
	bool bMarksTargets = false;

	float Lifetime = 8.f;

	TWeakObjectPtr<AActor> OwnerPawn;
	TMap<TWeakObjectPtr<ACharacter>, float> SlowedOriginalSpeeds;
	TArray<TWeakObjectPtr<UPrimitiveComponent>> MarkedComponents;
	FTimerHandle PulseHandle;
	FTimerHandle ExpireHandle;
};
