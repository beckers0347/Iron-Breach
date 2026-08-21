#pragma once

#include "CoreMinimal.h"
#include "Combat/AdsSettings.h"
#include "Items/IBItemDefinition.h"
#include "WeaponVisualData.generated.h"

class UNiagaraSystem;
class USoundBase;
class UStaticMesh;
class UWeaponCombatData;

/** Shape mask for the scope PIP screen -- see UWeaponVisualData::ScopePipShape. */
UENUM(BlueprintType)
enum class EIBScopePipShape : uint8
{
	Square,
	Circle,
};

/**
 * The presentation half of a weapon's data -- AND, by inheriting from
 * UIBItemDefinition, the SAME asset used everywhere an item is referenced (the
 * weapon rack's stock list, GrantItem, the inventory, the ledger). One asset per
 * weapon now covers both roles: it carries the item-facing fields (DisplayName,
 * Icon, EquipSlot, Rarity, Stats, MaxStack -- all inherited from
 * UIBItemDefinition, see that class for what they do) AND the weapon-facing
 * fields below (mesh, scale, alignment, fire cosmetics), plus a CombatData link
 * out to the sibling UWeaponCombatData asset that carries damage/fire-rate/range
 * and ADS tuning. Attach THIS asset wherever a weapon needs to be referenced --
 * the rack, a loadout list, a loot table -- and everything else (combat stats,
 * item metadata) comes along for free through inheritance/CombatData, instead of
 * wiring a separate Item + Visual + Combat trio by hand.
 *
 * AIBCharacter_Infantry::ApplyWeaponData resolves CombatData through this
 * asset's own CombatData link. Non-weapon items (materials, consumables, etc.)
 * are unaffected -- they keep using plain UIBItemDefinition directly.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UWeaponVisualData : public UIBItemDefinition
{
	GENERATED_BODY()

public:
	/** Display/identity tag -- logging and the Weapon Generator's naming, not a
	 *  balance concern and not the same thing as the inherited player-facing
	 *  DisplayName (FText). Kept here since it travels with "what the weapon
	 *  presents as" rather than "how hard it hits." */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FName WeaponName;

	/** The sibling asset that supplies this weapon's damage/fire rate/range and ADS
	 *  tuning. This is the ONLY other weapon asset you need to wire up -- attach
	 *  this VisualData to the item/rack/loadout, and Combat is reached through here. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UWeaponCombatData> CombatData;

	// TObjectPtr: Epic-standard for UPROPERTY object references (UE5+, required direction for UE6)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<UNiagaraSystem> MFXTracer;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<USoundBase> FireSound;

	/** Scale applied to the first-person viewmodel mesh when this weapon is equipped.
	 *  The template rifle is authored at full world scale, so most weapons will want
	 *  something in the 0.4-1.0 range to read as "held" rather than filling the screen.
	 *  Some generated weapon meshes are authored much larger than that (mech-scale
	 *  assets reused for the infantry viewmodel) and need far smaller than 0.01 to
	 *  read correctly -- ClampMin is set low enough not to block that rather than
	 *  assuming every mesh fits the "normal" range. Applied by
	 *  AIBCharacter_Infantry::SetWeaponMeshScale() in BeginPlay/ApplyWeaponData --
	 *  tune alongside the rig's Hip Anchor since a smaller weapon sits closer to
	 *  camera, and see WeaponVisualData.h's OnVisualDataChanged for tuning this
	 *  live in a running PIE session instead of restarting each time. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel", meta = (ClampMin = "0.0001"))
	FVector ViewmodelScale = FVector(1.0f);

	/** Fine-alignment nudge for this weapon's viewmodel, layered on top of the
	 *  rig's shared WeaponMountRotation/Grip-socket solve (WeaponRigComponent::
	 *  SetWeaponAlignmentOffset). Use this to correct one mesh's alignment without
	 *  touching rig-wide settings or re-exporting the mesh with different sockets.
	 *  Rotation is applied in the mesh's own local space BEFORE the rig's
	 *  WeaponMountRotation; Location shifts where the Grip/Aim sockets are treated
	 *  as being, so it stays correct across Hip, ADS, and Sprint poses.
	 *
	 *  Only affects Hip pose, Socket-mode ADS, and Sprint pose — Authored ADS
	 *  transform mode (FIBAdsSettings::bUseAuthoredAdsTransform) is deliberately
	 *  verbatim and ignores this. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Alignment")
	FVector ViewmodelLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Alignment")
	FRotator ViewmodelRotationOffset = FRotator::ZeroRotator;

	/** The first-person viewmodel mesh swapped in when this weapon becomes the
	 *  active slot (AIBCharacter_Infantry::ApplyWeaponData). Soft reference —
	 *  loaded synchronously only at the moment a weapon is actually equipped, same
	 *  "small, load-on-demand" reasoning as UIBItemDefinition::Icon.
	 *
	 *  Must carry the same named sockets WeaponRigComponent expects (Grip / Aim,
	 *  see WeaponRigComponent.h's class comment) or the viewmodel will pose at the
	 *  mesh origin instead of a held-looking position. Left unset = the character
	 *  keeps whatever mesh it already had rather than going blank, so it's safe to
	 *  generate/stock weapons before art exists — assign this once a mesh is ready. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	TSoftObjectPtr<UStaticMesh> ViewmodelMesh;

	/** Enable the picture-in-picture scope render (AIBCharacter_Infantry::
	 *  SetupScopePip) for THIS weapon. Off by default -- most weapon meshes don't
	 *  have a real lens/ScopeSocket authored, and turning the PIP on for one anyway
	 *  mounts a floating render-target screen at the mesh root instead of a lens
	 *  (watch the Output Log for "[Scope] weapon mesh ... has no socket" if that
	 *  happens). This is on top of AIBCharacter_Infantry::bEnableScopePip, which is
	 *  still the master switch (off there means off for every weapon regardless of
	 *  this) -- turn THIS on only for weapons with a proper optic authored. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope")
	bool bEnableScopePip = false;

	/** Multiplies the character's base ScopeScreenScale for THIS weapon's optic --
	 *  lets each scope's lens size differ (a red dot's tiny screen vs. a sniper
	 *  scope's larger one) without touching AIBCharacter_Infantry's shared
	 *  rig-wide ScopeScreenScale constant. (1,1) = use that constant as authored.
	 *  X and Y are independent -- one widens/narrows the screen, the other
	 *  makes it taller/shorter -- because ScopeScreenRotation (the rig-wide
	 *  constant that stands the screen upright) determines which is which, try
	 *  nudging X alone vs Y alone in a running PIE session (live-tunes
	 *  immediately, no restart) to see which reads as "width" for your setup
	 *  rather than assuming.
	 *  This is a WORLD-SPACE size multiplier -- it is NOT compensated by the
	 *  weapon's own ViewmodelScale the way position/scale otherwise are (that
	 *  compensation is what keeps the optic the same physical size no matter how
	 *  small a weapon's viewmodel is), so cranking this up is a direct, uncapped
	 *  way to make the PIP screen physically huge. ClampMax below exists because
	 *  that's exactly what "PIP is a giant black square blocking the view" turned
	 *  out to be for at least one weapon -- if the optic is too small, prefer
	 *  raising ScopeScreenScale/this multiplier in small steps (0.1-0.5 at a time)
	 *  over the socket, not jumping straight to a large value. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope",
		meta = (ClampMin = "0.01", ClampMax = "5.0", EditCondition = "bEnableScopePip"))
	FVector2D ScopePipSizeMultiplier = FVector2D(1.0f, 1.0f);

	/** Square = the raw PIP quad, no masking -- works with ANY ScopeScreenMaterial,
	 *  including one that hasn't been touched for this feature at all. Circle asks
	 *  AIBCharacter_Infantry::SetupScopePip to push PipShapeIsCircle=1 and
	 *  PipCircleRadius (below) as scalar parameters onto the screen's dynamic
	 *  material instance -- but the actual masking only happens if the material
	 *  graph reads them. Recipe for M_ScopeScreen: Blend Mode = Masked, add two
	 *  Scalar Parameters named exactly "PipShapeIsCircle" and "PipCircleRadius",
	 *  feed the Engine's RadialGradientExponent material function (UV = the
	 *  screen's texture UVs, Radius = PipCircleRadius param), then
	 *  Lerp(A = 1.0, B = that function's output, Alpha = PipShapeIsCircle) into
	 *  Opacity Mask. Leaving the material untouched just means Circle behaves
	 *  like Square until that's wired up -- nothing breaks either way. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope")
	EIBScopePipShape ScopePipShape = EIBScopePipShape::Square;

	/** Radius (material-graph units, whatever RadialGradientExponent's Radius input
	 *  expects for your UVs -- typically 0-1 for a 0-1 UV space) passed to the
	 *  screen material as PipCircleRadius when ScopePipShape is Circle. Only takes
	 *  visible effect once the material graph actually reads it -- see ScopePipShape. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope",
		meta = (ClampMin = "0.01", ClampMax = "1.0", EditCondition = "ScopePipShape == EIBScopePipShape::Circle"))
	float ScopePipCircleRadius = 0.45f;

	/** Per-weapon rotation correction for the scope screen, composed with
	 *  AIBCharacter_Infantry's rig-wide ScopeScreenRotation the same way
	 *  UWeaponRigComponent composes PerWeaponMountOffset with WeaponMountRotation --
	 *  THIS offset is applied first, in the screen's own local space, then the
	 *  rig-wide constant on top. Left at zero, a weapon behaves exactly as before
	 *  this field existed.
	 *
	 *  Exists because ScopeScreenRotation is one constant shared by every weapon,
	 *  but ScopeSocket authoring isn't consistent mesh to mesh -- one weapon's
	 *  socket may come out upright under that shared constant while another's
	 *  comes out rotated off to the side. Nudge THIS weapon's rotation here
	 *  instead of touching the shared constant, which would fix one weapon by
	 *  breaking the others. Tune live in a running PIE session the same way as
	 *  ScopePipSizeMultiplier above -- no restart needed to see the change. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope", meta = (EditCondition = "bEnableScopePip"))
	FRotator ScopeScreenRotationOffset = FRotator::ZeroRotator;

	/** Per-weapon location correction for the scope screen, socket-local, added on
	 *  top of AIBCharacter_Infantry's rig-wide ScopeScreenOffset. Unlike that
	 *  rig-wide offset, this is NOT compensated by the inverse of this weapon's
	 *  own ViewmodelScale -- same reasoning as WeaponRigComponent's
	 *  PerWeaponLocationOffset: it's authored as "shift the screen this many cm
	 *  for THIS weapon," which should mean the same physical distance regardless
	 *  of how small or large this weapon's viewmodel is scaled. Leave at zero
	 *  unless fixing ScopeScreenRotationOffset above also reveals the screen now
	 *  faces correctly but sits in the wrong spot (inside the housing, or floating
	 *  clear of it). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope", meta = (EditCondition = "bEnableScopePip"))
	FVector ScopeScreenLocationOffset = FVector::ZeroVector;

	/** Per-weapon override for the character's rig-wide ScopeFOV. 0 (the default)
	 *  means "use the rig-wide constant as authored" -- same fallback convention as
	 *  ScopePipSizeMultiplier's (1,1) default, just expressed as a sentinel here
	 *  since 0 is otherwise a meaningless FOV. Set this when one weapon's optic
	 *  needs to zoom in more or less than the shared default: a real scope's glass/
	 *  reticle mesh reads correctly at very different FOVs depending on how the
	 *  optic was modeled, so a single rig-wide ScopeFOV that suits a red-dot can
	 *  leave a sniper scope zoomed in so far it's unreadable (a LOWER ScopeFOV is
	 *  MORE magnification -- if the view is too zoomed in and you can't make
	 *  anything out, raise this, don't lower it). Tune live in PIE, no restart
	 *  needed, same as the other Scope fields above. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope",
		meta = (ClampMin = "0.0", ClampMax = "170.0", EditCondition = "bEnableScopePip"))
	float ScopeFOVOverride = 0.0f;

	/** Per-weapon aim correction for the CAPTURE camera itself -- composed with
	 *  AIBCharacter_Infantry's rig-wide ScopeCameraRotation exactly the way
	 *  ScopeScreenRotationOffset composes with ScopeScreenRotation above (this
	 *  weapon's offset applied first, in the camera's own local space, then the
	 *  rig-wide constant on top). Left at zero, a weapon behaves exactly as before
	 *  this field existed.
	 *
	 *  Symptom this fixes: the SCREEN can be rotated upright and still show a view
	 *  that's aimed off to one side of where the crosshair/reticle actually points
	 *  -- that's the CAPTURE camera's aim being wrong, not the screen's rotation.
	 *  Same root cause as everything else Scope-related this session: ScopeSocket
	 *  authoring isn't consistent mesh to mesh, so the rig-wide ScopeCameraRotation
	 *  (which assumes the socket's local +X points straight downrange) only lands
	 *  true for whichever weapon it happened to be tuned against. Nudge THIS
	 *  weapon's aim here rather than the shared constant. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope", meta = (EditCondition = "bEnableScopePip"))
	FRotator ScopeCameraRotationOffset = FRotator::ZeroRotator;

	/** Per-weapon location correction for the capture camera, socket-local, added
	 *  on top of AIBCharacter_Infantry's rig-wide ScopeCameraOffset. Like
	 *  ScopeScreenLocationOffset, this is NOT compensated by the inverse of this
	 *  weapon's ViewmodelScale -- it's a fixed "shift the camera this many cm for
	 *  THIS weapon" nudge, same physical distance regardless of how this weapon's
	 *  viewmodel is scaled. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Scope", meta = (EditCondition = "bEnableScopePip"))
	FVector ScopeCameraLocationOffset = FVector::ZeroVector;

#if WITH_EDITOR
	/** Broadcasts whenever one of this asset's properties changes in the editor --
	 *  property panel edits, and Unreal's own re-notify after an in-PIE undo/redo.
	 *  AIBCharacter_Infantry binds this for whichever weapon is currently equipped
	 *  (see ApplyWeaponData's editor-only binding block) so a ViewmodelScale/
	 *  alignment-offset/ViewmodelMesh tweak applies to a running PIE session
	 *  immediately -- no more exit-PIE-edit-reenter-PIE loop to see a change.
	 *  Editor-only: this delegate and the override below compile out entirely in
	 *  packaged builds, so live-tuning costs nothing at runtime. */
	FSimpleMulticastDelegate OnVisualDataChanged;

	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif
};
