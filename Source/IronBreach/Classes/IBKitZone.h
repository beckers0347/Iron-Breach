#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Classes/IBClassKitTypes.h"
#include "IBKitZone.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInterface;
class ACharacter;

/** Replicated field: protects friendly infantry, slows hostiles, and supplies sensor HUD marks. */
UCLASS()
class IRONBREACH_API AIBKitZone : public AActor
{
	GENERATED_BODY()

public:
    friend struct FIBSkillCombatCheck;
	AIBKitZone();

	/** Server: configure from the spec and arm the pulse. */
	void InitZone(const FIBKitAbilitySpec& Spec, const FLinearColor& InAccent, AActor* InOwnerPawn);

	UFUNCTION(BlueprintPure, Category = "Kit")
	float GetRadius() const { return Radius; }
	static float GetActiveSlowScale(const ACharacter* Character);
	const TArray<TWeakObjectPtr<ACharacter>>& GetMarkedTargets() const { return MarkedTargets; }

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

	UPROPERTY(Replicated) float FriendlyDamageScale = 1.f;

	float Lifetime = 8.f;

	TWeakObjectPtr<AActor> OwnerPawn;
	TMap<TWeakObjectPtr<ACharacter>, float> SlowedOriginalSpeeds;
	TArray<TWeakObjectPtr<ACharacter>> MarkedTargets;
	FTimerHandle PulseHandle;
	FTimerHandle ExpireHandle;
};
