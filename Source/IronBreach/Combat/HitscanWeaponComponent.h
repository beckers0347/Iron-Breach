#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/NetSerialization.h" // Explicit include: FVector_NetQuantize used in the Server RPC signature
#include "HitscanWeaponComponent.generated.h"

class UWeaponDataAsset;

/**
 * Drop-in hitscan gun for any pawn. Fire() may be called from anywhere (Enhanced Input,
 * legacy BindKey, Blueprints); it plays cosmetics immediately on the firing client and
 * routes the authoritative trace + damage to the server (ADR-002: cosmetic-first firing).
 * On a listen host / standalone, Fire() traces directly.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class IRONBREACH_API UHitscanWeaponComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UHitscanWeaponComponent();

	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void Fire();

	/** Lets owning characters forward their equipped weapon data (e.g. infantry loadout). */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void SetWeaponData(UWeaponDataAsset* NewWeaponData) { WeaponData = NewWeaponData; }

	/** Auto-bind left mouse via the legacy input path (used by the template character,
	 *  which has no Enhanced Input graph). Owners that call Fire() themselves must
	 *  disable this or one click fires twice. */
	UPROPERTY(EditAnywhere, Category = "Weapon")
	bool bAutoBindLegacyInput = true;

protected:
	virtual void BeginPlay() override;

	/** Optional data asset; overrides the loose values below when set. */
	UPROPERTY(EditAnywhere, Category = "Weapon")
	TObjectPtr<UWeaponDataAsset> WeaponData;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "0"))
	float Damage = 25.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "100"))
	float Range = 5000.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "0.05"))
	float FireInterval = 0.2f;

	/** Authoritative trace + damage. Runs only where GetOwner()->HasAuthority(). */
	UFUNCTION(Server, Reliable, WithValidation)
	void Server_Fire(FVector_NetQuantize ViewLocation, FVector_NetQuantizeNormal ViewDirection);

private:
	void TryBindInput();

	/** Shared authoritative fire path (server + standalone). */
	void PerformFire(const FVector& ViewLocation, const FVector& ViewDirection);

	/** Local cosmetics on the machine that pulled the trigger (sound now; tracer later). */
	void PlayFireCosmetics() const;

	bool GetOwnerViewPoint(FVector& OutLocation, FRotator& OutRotation) const;

	float LastFireTime = -1000.0f;       // Client-side UX cooldown (spam guard)
	float LastServerFireTime = -1000.0f; // Authoritative cooldown (the law)
	FTimerHandle BindRetryHandle;
};
