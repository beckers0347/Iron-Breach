#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "InputActionValue.h"
#include "Items/IBItemTypes.h" // EIBEquipSlot / FIBItemInstance in the equipment handler signature
#include "IBCharacter_Infantry.generated.h"

class UInputMappingContext;
class UInputAction;
class UIBInventoryComponent;
class UHealthComponent;
class UHitscanWeaponComponent;
class UWeaponRigComponent;
class UWeaponDataAsset;
class UCameraComponent;
class UStaticMeshComponent;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class UMaterialInterface;

UCLASS()
class IRONBREACH_API AIBCharacter_Infantry : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Infantry();

	/** Exposed so UHitscanWeaponComponent can read the current spread when firing. */
	UWeaponRigComponent* GetWeaponRig() const { return WeaponRig; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	// Core Components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHealthComponent> HealthComponent;

	/** Single damage path for the project: all player firing goes through this component
	 *  (cosmetic-first + Server_Fire). Uses CurrentWeaponData, forwarded in BeginPlay. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHitscanWeaponComponent> WeaponComponent;

	/** First-person camera at eye height. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	/** First-person viewmodel weapon mesh, posed by the rig. Owner-only visible. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UStaticMeshComponent> WeaponMesh;

	/** Poses the viewmodel and drives ADS (zoom, spread, move speed). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponRigComponent> WeaponRig;

	// ---------------------------------------------------------------------
	// Picture-in-picture scope (render-target optic)
	//
	// Replaces the old Event Graph attach sequence. Everything the BP version
	// did by hand — attach to socket, correct the socket's authored rotation,
	// push the screen clear of the baked sight geometry, force visibility —
	// happens in SetupScopePip() where the values are readable and diffable.
	//
	// The screen and camera both hang off WeaponMesh's scope socket, so the
	// rig's per-frame viewmodel posing carries them along for free.
	// ---------------------------------------------------------------------

	/** Zoomed capture that feeds ScopeRenderTarget. Sits just ahead of the screen. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Scope")
	TObjectPtr<USceneCaptureComponent2D> ScopeCamera;

	/** Flat plane displaying the render target inside the optic. Owner-only visible. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Scope")
	TObjectPtr<UStaticMeshComponent> ScopeScreen;

	/** Master switch. Off = no capture cost, no screen, weapon renders untouched. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	bool bEnableScopePip = true;

	/** Socket on WeaponMesh the optic mounts to. Missing socket -> falls back to
	 *  the mesh root and logs a warning rather than silently posing at the origin. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FName ScopeSocketName = TEXT("ScopeSocket");

	/** Render target the capture writes and the screen material reads. OPTIONAL:
	 *  leave it empty and one is created at runtime at ScopeRenderTargetResolution.
	 *  Only assign an asset if something outside this pawn needs to sample the feed. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	TObjectPtr<UTextureRenderTarget2D> ScopeRenderTarget;

	/** Square resolution for the auto-created render target. 512 is plenty for an
	 *  optic a few centimetres across; 1024 costs real memory for no visible gain. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope", meta = (ClampMin = "128", ClampMax = "2048"))
	int32 ScopeRenderTargetResolution = 512;

	/** Unlit material sampling the render target into Emissive. Assign M_ScopeScreen.
	 *  IMPORTANT: enable Two Sided on it, or a half-turn of yaw culls the whole plane. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	TObjectPtr<UMaterialInterface> ScopeScreenMaterial;

	/** Optional texture parameter name on the screen material. When set, the render
	 *  target is pushed into a dynamic instance at runtime instead of being hardwired
	 *  in the material — lets several weapons share one material with distinct RTs. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FName ScopeTextureParameterName = NAME_None;

	/** Screen offset from the socket, socket-local. Push along +X until the plane
	 *  clears the sight's baked glass geometry. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FVector ScopeScreenOffset = FVector(1.0f, 0.0f, 0.0f);

	/** Screen rotation relative to the socket. A UE Plane's face normal is +Z, so it
	 *  needs pitch to stand upright — yaw alone leaves it lying flat. If the plane
	 *  vanishes at a correct transform, flip this yaw by 180: you're looking at the
	 *  culled back face. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FRotator ScopeScreenRotation = FRotator(90.0f, 180.0f, 0.0f);

	/** Screen scale. The engine Plane is 100cm square — reflex-sight size is ~0.03-0.05. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FVector ScopeScreenScale = FVector(0.04f);

	/** Capture offset from the socket, socket-local. Keep it ahead of the screen so
	 *  the screen never lands inside the capture's near plane. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FVector ScopeCameraOffset = FVector(5.0f, 0.0f, 0.0f);

	/** Capture rotation relative to the socket. Identity assumes the socket's +X
	 *  points downrange; correct here rather than re-authoring the socket. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	FRotator ScopeCameraRotation = FRotator::ZeroRotator;

	/** Capture FOV. Lower = more magnification. ~20 reads as a 4x optic against a 90 FOV view. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope", meta = (ClampMin = "5.0", ClampMax = "170.0"))
	float ScopeFOV = 20.0f;

	/** Hide the viewmodel from the scope's own capture. Off means the gun body fills
	 *  the optic; there is rarely a reason to want that. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope")
	bool bHideWeaponFromScopeCapture = true;

	// Enhanced Input Data
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputMappingContext> DefaultMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> FireAction;

	/** Aim-down-sights: bind as Started (press) + Completed (release), or a Hold trigger. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> AimAction;

	// Current Weapon Context
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponDataAsset> CurrentWeaponData;

	/** Base walk speed the ADS move-speed multiplier scales from. Captured at BeginPlay. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	float BaseWalkSpeed = 0.0f;

	/** Seconds between death and the server respawning this player (networked play, u1-08).
	 *  A player-facing wait, not hidden timer logic. */
	UPROPERTY(EditAnywhere, Category = "Health", meta = (ClampMin = "0.5"))
	float RespawnDelay = 5.0f;

	/** Blueprint hook for death FX/UI (mirrors the enemy's BP_OnDied). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Health")
	void BP_OnDied(AActor* Killer);

	UFUNCTION()
	void HandleDeath(AActor* Killer);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon")
	bool bIsArmed = false;

	// Input Actions
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void Fire();
	void StartAiming();
	void StopAiming();

	/** Inventory lives on AIBPlayerState (it must survive pawn churn — death,
	 *  respawn, infantry<->mech swap). The pawn is a subscriber: whenever the
	 *  PlayerState arrives/changes, rebind and pull the equipped weapon. This
	 *  fires on every machine (PS replicates), so remote players' pawns pick
	 *  up loadout changes too. */
	virtual void OnPlayerStateChanged(APlayerState* NewPlayerState, APlayerState* OldPlayerState) override;

	/** Loot -> gun seam: an equipped WeaponPrimary with WeaponData is forwarded
	 *  to the weapon component + ADS rig; anything else leaves the designer
	 *  default (CurrentWeaponData) in place. */
	UFUNCTION()
	void HandleEquipmentChanged(EIBEquipSlot Slot, const FIBItemInstance& Item);

public:
	// Implementation of IDamageableInterface
	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

	/** Re-run the PIP mount. Call after swapping the weapon mesh so the optic
	 *  re-snaps to the new mesh's socket instead of dangling off the old one. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Scope")
	void SetupScopePip();

	/** Runtime toggle for both halves of the optic (screen + capture cost). */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Scope")
	void SetScopePipEnabled(bool bEnabled);

private:
	void ApplyWeaponData(UWeaponDataAsset* WeaponData);

	FTimerHandle RespawnTimerHandle;
	bool bDead = false;

	/** Weak: the PlayerState (and its inventory) outlives this pawn, not the
	 *  other way round — never keep it alive from a corpse. */
	TWeakObjectPtr<UIBInventoryComponent> BoundInventory;
};
