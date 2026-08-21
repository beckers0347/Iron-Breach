#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "Combat/AdsSettings.h" // FIBAdsSettings return type on ResolveAdsSettings
#include "InputActionValue.h"
#include "Items/IBItemTypes.h" // EIBEquipSlot / FIBItemInstance in the equipment handler signature
#include "IBCharacter_Infantry.generated.h"

class UInputMappingContext;
class UInputAction;
class UIBInventoryComponent;
class UHealthComponent;
class UHitscanWeaponComponent;
class UWeaponRigComponent;
class UWeaponCombatData;
class UWeaponVisualData;
class UIBItemDefinition;
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
	 *  (cosmetic-first + Server_Fire). Uses CurrentCombatData/CurrentVisualData, forwarded in BeginPlay. */
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

	/** Texture parameter name on the screen material that the render target gets
	 *  pushed into. Optional -- leave at None and SetupScopePip() auto-detects the
	 *  material's Texture Sample Parameter as long as it only exposes one (logs
	 *  which name it picked). Only set this explicitly if the material exposes more
	 *  than one texture parameter and the auto-guess picks the wrong one, or if you
	 *  just want to be unambiguous about it. A material with NO texture parameter at
	 *  all (a hardcoded Texture Sample instead) can never show the live capture no
	 *  matter what this is set to — that shows up as a solid black (or static)
	 *  screen and logs an Error explaining exactly that. */
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

	/** EV stops added on top of the capture's forced Auto (Histogram) exposure —
	 *  see the comment in SetupScopePip(). Turns out NOT to be why the optic reads
	 *  dim: the capture's own exposure was already correct, but the RESULT still
	 *  passes through the main FirstPersonCamera's own auto-exposure/tonemapping
	 *  (ScopeScreen is Unlit, which skips lighting, not tonemapping), which
	 *  compresses it back down to match the bright outdoor scene. If you need the
	 *  optic brighter, boost the Emissive multiplier on M_ScopeScreen instead —
	 *  that's what actually survives the outer exposure pass. Left as a knob here
	 *  in case a future scene genuinely needs it. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Scope", meta = (ClampMin = "-4.0", ClampMax = "6.0"))
	float ScopeExposureBias = 1.0f;

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
	TObjectPtr<UWeaponCombatData> CurrentCombatData;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponVisualData> CurrentVisualData;

	/** Skip arming the designer-default loadout at spawn -- the pawn starts with
	 *  WeaponMesh hidden and Fire() refusing (SetUnarmed(true) in BeginPlay), same
	 *  as walking into storage and emptying the active well. A real inventory
	 *  (IBPlayerState) re-arms this the moment its equipped-item pull/
	 *  HandleEquipmentChanged runs, so this only changes what's in your hands for
	 *  the first instant of a spawn. On maps with no IBPlayerState at all (Shane's
	 *  default-GM test maps) there's no equipment signal to re-arm from, so this
	 *  flag alone decides armed vs. unarmed there. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bStartUnarmed = true;

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

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	class UInputAction* SprintAction;

	/** Assign an IA_Crouch asset here and map it to whatever key you want; bound as
	 *  Started (press) + Completed (release), same hold pattern as Sprint/Aim. */
	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> CrouchAction;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float NormalWalkSpeed = 500.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float SprintSpeed = 900.f;

	UPROPERTY(BlueprintReadOnly, Category = "Movement")
	bool bIsSprinting = false;

	UPROPERTY(BlueprintReadOnly, Category = "Weapon")
	bool bIsAiming = false;

	void StartSprint();
	void StopSprint();
	void StartCrouch();
	void StopCrouch();

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

	/** Loot -> gun seam: an equipped weapon in the ACTIVE slot is forwarded
	 *  to the weapon component + ADS rig; anything else leaves the designer
	 *  default (CurrentCombatData/CurrentVisualData) in place. */
	UFUNCTION()
	void HandleEquipmentChanged(EIBEquipSlot Slot, const FIBItemInstance& Item);

public:
	// --- Weapon slot switching (1/2/3 = Primary/Special/Heavy; MENUS §11.1) ---

	/** Which equipment well is in-hand. Server-authoritative: firing reads the
	 *  weapon component's data on the server, so the swap must be too. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Slots")
	void SetActiveWeaponSlot(EIBEquipSlot NewSlot);

	UFUNCTION(BlueprintPure, Category = "Weapon|Slots")
	EIBEquipSlot GetActiveWeaponSlot() const { return ActiveWeaponSlot; }

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	UPROPERTY(ReplicatedUsing = OnRep_ActiveWeaponSlot, VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Slots")
	EIBEquipSlot ActiveWeaponSlot = EIBEquipSlot::WeaponPrimary;

	UFUNCTION(Server, Reliable)
	void Server_SetActiveWeaponSlot(EIBEquipSlot NewSlot);

	UFUNCTION()
	void OnRep_ActiveWeaponSlot();

	/** Resolve the active slot's item -> weapon data -> ApplyWeaponData. */
	void ApplyActiveSlot();

	/** Empty hands: weapon mesh hidden, optic off, Fire() refuses. Entered when
	 *  the active well is EMPTY and a real inventory exists (unequip/storage —
	 *  the gun must actually leave your hands or storage feels fake). Maps
	 *  without an IBPlayerState keep the designer-default gun as before. */
	void SetUnarmed(bool bNewUnarmed);

	UFUNCTION(BlueprintPure, Category = "Weapon|Slots")
	bool IsUnarmed() const { return bUnarmed; }

	/** See SetUnarmed. Not replicated: derived from replicated Equipment on
	 *  every machine via HandleEquipmentChanged/ApplyActiveSlot. */
	bool bUnarmed = false;

	// Raw 1/2/3 input thunks (BindKey — no IA assets required).
	void SelectPrimarySlot()  { SetActiveWeaponSlot(EIBEquipSlot::WeaponPrimary); }
	void SelectSpecialSlot()  { SetActiveWeaponSlot(EIBEquipSlot::WeaponSpecial); }
	void SelectHeavySlot()    { SetActiveWeaponSlot(EIBEquipSlot::WeaponHeavy); }

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

	/** Rescale the first-person viewmodel mesh. Normally driven by CurrentVisualData's
	 *  ViewmodelScale (BeginPlay/ApplyWeaponData), but exposed for runtime tuning, a
	 *  debug console command, etc. Re-caches the rig's Grip/Aim socket offsets so ADS
	 *  alignment stays correct at the new scale instead of drifting off the anchor. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void SetWeaponMeshScale(FVector NewScale);

private:
	void ApplyWeaponData(UWeaponCombatData* CombatData, UWeaponVisualData* VisualData);

	/** Swaps WeaponMesh's static mesh to VisualData->ViewmodelMesh (sync-loading the
	 *  soft reference). Split out of ApplyWeaponData because BeginPlay needs the same
	 *  swap for the starting loadout, before ApplyWeaponData's rig/scope wiring runs.
	 *  No-op (keeps current mesh) if ViewmodelMesh is unset -- see its header comment. */
	void ApplyWeaponMesh(UWeaponVisualData* VisualData);

	/** Resolve an equipped item's UWeaponVisualData. Handles both wiring styles so
	 *  in-progress content migration doesn't break pickups: if Definition itself IS
	 *  a UWeaponVisualData (the rack/inventory point directly at a DA_Visual_* asset
	 *  -- see WeaponVisualData.h's class comment), that's the answer; otherwise falls
	 *  back to the legacy DA_Item_*::VisualData link for content not yet migrated.
	 *  Returns null if neither resolves. */
	UWeaponVisualData* ResolveVisualData(const UIBItemDefinition* Definition) const;

	/** Resolve an equipped item's UWeaponCombatData: through ResolvedVisual's own
	 *  CombatData link first (the current wiring), falling back to the legacy
	 *  DA_Item_*::LegacyCombatData link. Returns null if neither resolves. */
	UWeaponCombatData* ResolveCombatData(const UIBItemDefinition* Definition, UWeaponVisualData* ResolvedVisual) const;

	/** Resolve a weapon's ADS tuning: VisualData->CombatData->Ads (current wiring --
	 *  Ads lives on the Combat asset now) if a CombatData link is set, else falls
	 *  back to VisualData's own (deprecated) Ads field for content that hasn't been
	 *  migrated yet. Was reading VisualData->Ads unconditionally, which is why ADS
	 *  looked right only for whichever weapon's deprecated field happened to still
	 *  match its real tuning -- every other weapon read stale/default settings. */
	FIBAdsSettings ResolveAdsSettings(const UWeaponVisualData* VisualData) const;

	/** Whichever Visual/Combat pair ApplyWeaponData most recently applied. Tracked
	 *  (unlike CurrentCombatData/CurrentVisualData, which stay pinned to the
	 *  designer-default floor -- see HandleEquipmentChanged's comment) so anything
	 *  that needs to know what's ACTUALLY in the character's hands right now has
	 *  somewhere to read that from. Used by SetupScopePip() to read the equipped
	 *  weapon's own PIP toggle/scale, and (editor-only) by RefreshLiveTunedWeapon. */
	TWeakObjectPtr<UWeaponVisualData> EquippedVisualData;
	TWeakObjectPtr<UWeaponCombatData> EquippedCombatData;

#if WITH_EDITOR
	/** Bound to EquippedVisualData->OnVisualDataChanged in ApplyWeaponData. Re-runs
	 *  ApplyWeaponData with whatever's currently equipped so a ViewmodelScale/
	 *  alignment-offset/ViewmodelMesh edit shows up without exiting PIE. Editor-only;
	 *  compiled out of packaged builds. */
	void RefreshLiveTunedWeapon();
#endif

	FTimerHandle RespawnTimerHandle;
	bool bDead = false;

	/** Weak: the PlayerState (and its inventory) outlives this pawn, not the
	 *  other way round — never keep it alive from a corpse. */
	TWeakObjectPtr<UIBInventoryComponent> BoundInventory;
};
