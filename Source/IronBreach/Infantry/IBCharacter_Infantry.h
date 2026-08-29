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

/** UI binds this to clear/restore the HUD around the M1 LANDFALL carry
 *  (Docs/M1_LANDFALL_Mission_Design.md §4.4/§7: "the carry clears the HUD
 *  entirely"). Generic on purpose -- any future no-HUD beat reuses it. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCarryStateChangedSignature, bool, bIsCarrying);

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

	/** Third-person weapon mesh -- what everyone ELSE (and the owner in third-person
	 *  spectate/cinematics) actually sees. Rigidly attached to ThirdPersonWeaponSocket
	 *  on the body skeleton (GetMesh()) in BeginPlay, so it inherits that bone's full
	 *  animated transform every frame -- walk/run sway, aim offsets, everything --
	 *  automatically, with zero per-frame Blueprint work. Hidden from the owning
	 *  player (SetOwnerNoSee) since they already see WeaponMesh's first-person
	 *  viewmodel; visible to every other client by default (no OnlyOwnerSee). Kept
	 *  in sync with WeaponMesh's static mesh/scale in ApplyWeaponMesh/SetWeaponMeshScale,
	 *  and picked up on every client automatically via ActiveWeaponSlot's replication
	 *  -> OnRep_ActiveWeaponSlot -> ApplyWeaponData chain -- no extra networking needed. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UStaticMeshComponent> ThirdPersonWeaponMesh;

	/** Socket on the body skeleton (GetMesh()) ThirdPersonWeaponMesh rigidly attaches
	 *  to -- author this near/at the weapon's grip bone so the off-hand IK (which
	 *  reads ThirdPersonWeaponMesh's own Grip/OffHandGrip sockets) has a natural
	 *  reach to the foregrip. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	FName ThirdPersonWeaponSocket = TEXT("WeaponSocket");

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

	/** World interaction: coffee/log/dry-fire rig in M1's QUIET beat, Ms. Idris in
	 *  the carry. Bind as Started (press) -- see Interact(). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> InteractAction;

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

	/** Short trace from the first-person camera; if the hit actor implements
	 *  IIBInteractable, calls Interact on it. One verb for coffee pots, log
	 *  books, the dry-fire rig, and Ms. Idris -- see IBInteractableInterface.h. */
	void Interact();

	/** Trace range for Interact(), in cm. Coffee-pot/log-book distance, not sniping range. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Interact", meta = (ClampMin = "50.0", ClampMax = "500.0"))
	float InteractTraceDistance = 200.0f;

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

	// --- Read-only state accessors for UIBAnimInstance_Infantry / UI ---
	//
	// bIsArmed/bIsSprinting/bIsAiming are all UPROPERTY(BlueprintReadOnly) already
	// (visible to Blueprint graphs via reflection regardless of C++ access), but
	// they're declared in a `protected:` block above, so plain C++ code outside
	// this class -- like the native AnimInstance below -- can't read them
	// directly. Same situation IsUnarmed() was already in (see its own comment).
	// Small public wrappers here instead of relocating the underlying fields.

	UFUNCTION(BlueprintPure, Category = "Weapon")
	bool IsArmed() const { return bIsArmed; }

	UFUNCTION(BlueprintPure, Category = "Movement")
	bool IsSprinting() const { return bIsSprinting; }

	UFUNCTION(BlueprintPure, Category = "Weapon")
	bool IsAiming() const { return bIsAiming; }

	/** ThirdPersonWeaponMesh is also declared in a `protected:` block above --
	 *  same reasoning as IsArmed()/IsSprinting()/IsAiming() just above, but for a
	 *  component reference instead of a bool. UIBAnimInstance_Infantry reads this
	 *  once a frame (game thread, NativeUpdateAnimation) to compute the hand-IK
	 *  grip targets safely -- see that class's UpdateWeaponHandIKTargets(). */
	UFUNCTION(BlueprintPure, Category = "Weapon")
	UStaticMeshComponent* GetThirdPersonWeaponMesh() const { return ThirdPersonWeaponMesh; }

	/** True once HealthComponent has hit 0. Not inlined: HealthComponent.h is only
	 *  forward-declared up top, and this needs the full UHealthComponent type to
	 *  call IsDepleted() -- defined in the .cpp, which already includes it. */
	UFUNCTION(BlueprintPure, Category = "Health")
	bool IsDead() const;

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

	// Mouse wheel thunks -- same raw-key grammar as 1/2/3, no IA assets required.
	void CycleWeaponSlotUp()   { CycleWeaponSlot(-1); }
	void CycleWeaponSlotDown() { CycleWeaponSlot(1); }

	/** Scrolls to the next/previous OCCUPIED weapon well (Primary/Special/Heavy),
	 *  skipping empty ones so scrolling never lands on a slot with nothing in it —
	 *  a one-weapon loadout just doesn't move, same as pressing 2/3 already does
	 *  nothing when that well is empty. Primary is always a valid landing spot
	 *  even when empty (matches SetActiveWeaponSlot's existing grammar: an empty
	 *  Primary means truly unarmed, not "refused"). Direction: -1 = previous
	 *  (toward Primary), +1 = next (toward Heavy). */
	void CycleWeaponSlot(int32 Direction);

public:
	// --- Carry (M1 LANDFALL "Four Hundred Meters" -- Docs/M1_LANDFALL_Mission_Design.md §4.4) ---
	//
	// Deliberately a character STATE, not a separate component: no stamina bar,
	// no timer, no fail state, no score (LOCKED). Reuses the existing
	// unarmed/re-arm path (SetUnarmed) for "weapon holstered" instead of a
	// parallel holster system, and folds into Tick()'s existing single-source-
	// of-truth MaxWalkSpeed calc for the forced walking pace.

	/** Starts carrying Target: attaches it to CarrySocket on the body mesh,
	 *  holsters the weapon, forces walk pace, and broadcasts OnCarryStateChanged
	 *  so UI clears the HUD. Returns false if already carrying something. Called
	 *  by IIBInteractable::Interact on the carryable (see M1Landfall/IBCarryablePawn). */
	UFUNCTION(BlueprintCallable, Category = "Carry")
	bool BeginCarry(AActor* Target);

	/** Detaches the carried actor in place (keeping its world transform -- the
	 *  level places the stretcher, this doesn't teleport her onto it), re-arms
	 *  the weapon, and restores normal move speed. Called by AIBCarryEndZone at
	 *  the hospital muster; never by player input (LOCKED: "cannot be skipped"). */
	UFUNCTION(BlueprintCallable, Category = "Carry")
	void EndCarry();

	UFUNCTION(BlueprintPure, Category = "Carry")
	bool IsCarrying() const { return bIsCarrying; }

	UFUNCTION(BlueprintPure, Category = "Carry")
	AActor* GetCarriedActor() const { return CarriedActor.Get(); }

	UPROPERTY(BlueprintAssignable, Category = "Carry|Events")
	FOnCarryStateChangedSignature OnCarryStateChanged;

	/** Forced pace while carrying (LOCKED: "walking pace is forced"), independent
	 *  of NormalWalkSpeed/ADS/sprint -- see Tick(). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Carry", meta = (ClampMin = "50.0", ClampMax = "400.0"))
	float CarryWalkSpeed = 220.0f;

	/** Socket on the third-person body mesh (GetMesh()) the carried actor attaches to. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Carry")
	FName CarrySocket = TEXT("CarrySocket");

protected:
	UPROPERTY(BlueprintReadOnly, Category = "Carry")
	bool bIsCarrying = false;

	UPROPERTY(BlueprintReadOnly, Category = "Carry")
	TWeakObjectPtr<AActor> CarriedActor;

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
