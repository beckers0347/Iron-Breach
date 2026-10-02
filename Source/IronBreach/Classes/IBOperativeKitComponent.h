#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Classes/IBClassKitTypes.h"
#include "InputCoreTypes.h"
#include "Skills/IBSkillTypes.h"
#include "IBOperativeKitComponent.generated.h"

class UIBClassKitData;
class UIBKitHudWidget;
class UInputAction;
class UInputComponent;
class ACharacter;
class APlayerController;

/** Four-slot operative abilities. Unlocks live on PlayerState; gameplay runs on authority. */
UCLASS(ClassGroup = (IronBreach), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UIBOperativeKitComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UIBOperativeKitComponent();

	/** Pawn calls this from SetupPlayerInputComponent: raw keys + optional Input Actions. */
	void BindInput(UInputComponent* PlayerInputComponent, UInputAction* KitAbilityAction, UInputAction* MovementToolAction);

	UFUNCTION(BlueprintCallable, Category = "Kit")
	void ActivateKitAbility();

	UFUNCTION(BlueprintCallable, Category = "Kit")
	void ActivateMovementTool();

	/** Re-resolve from the PlayerState (identity arrived or changed). */
	UFUNCTION(BlueprintCallable, Category = "Kit")
	void RefreshKit();
    void ActivateSlot(EIBSkillSlot Slot);
    void ActivateTacticalTwo() { ActivateSlot(EIBSkillSlot::TacticalTwo); }
    void ActivateOverdrive() { ActivateSlot(EIBSkillSlot::Overdrive); }
    const FIBKitAbilitySpec& GetSlotSpec(EIBSkillSlot Slot) const;
    float GetSlotCooldown(EIBSkillSlot Slot) const;
    FKey GetSlotKey(EIBSkillSlot Slot) const;
    void NotifyAttack();
    void RecordGuardedDamage(float IncomingDamage);
    void ApplyWardDefense(float Scale, float Duration);
    bool IsConcealed() const { return bConcealed; }
    float GetGuardEnergy() const { return GuardEnergy; }
    bool IsGuardActive() const;
    bool CanReturnToAnchor() const { return Now()<ReturnUntil; }
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(BlueprintPure, Category = "Kit")
	const FIBClassKit& GetKit() const { return ActiveKit; }

	UFUNCTION(BlueprintPure, Category = "Kit")
	EIBOperativeClass GetOperativeClass() const { return ResolvedClass; }

	UFUNCTION(BlueprintPure, Category = "Kit")
	float GetCooldownRemaining(bool bMovementTool) const;

	/** 1 = just used, 0 = ready. */
	UFUNCTION(BlueprintPure, Category = "Kit")
	float GetCooldownFraction(bool bMovementTool) const;

	UFUNCTION(BlueprintPure, Category = "Kit")
	FKey GetKitAbilityKey() const { return KitAbilityKey; }

	UFUNCTION(BlueprintPure, Category = "Kit")
	FKey GetMovementToolKey() const { return MovementToolKey; }

	/** Incoming-damage multiplier while a defensive window is live (the pawn reads it on the server). */
	float GetDamageTakenScale() const;

	/** Legacy Blueprint property. Playable skill tuning now lives in IBSkills::Catalog. */
	UPROPERTY(EditDefaultsOnly, Category = "Kit")
	TMap<EIBOperativeClass, TSoftObjectPtr<UIBClassKitData>> KitData;

	UPROPERTY(EditDefaultsOnly, Category = "Kit|Input")
	FKey KitAbilityKey;

	UPROPERTY(EditDefaultsOnly, Category = "Kit|Input")
	FKey MovementToolKey;

	UPROPERTY(EditDefaultsOnly, Category = "Kit|HUD")
	bool bShowHud = true;

	/** Fires on EVERY machine when an activation goes through (server multicast) — FX/sound/anim hook. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Kit", meta = (DisplayName = "On Kit Activated"))
	void BP_OnKitActivated(bool bMovementTool, const FIBKitAbilitySpec& Spec);

	/** Built-in first-pass kits (CLASSES_AND_PROGRESSION.md §3), used when no asset exists. */
	static FIBClassKit DefaultKitFor(EIBOperativeClass Class);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(Server, Reliable)
	void Server_Activate(EIBSkillSlot Slot);

	UFUNCTION(NetMulticast, Unreliable)
	void Multicast_Activated(EIBSkillSlot Slot, const FIBKitAbilitySpec& Spec);

    UFUNCTION(Client, Reliable) void Client_Cooldown(EIBSkillSlot Slot, FName Ability, float Remaining);
    UFUNCTION() void OnRep_Concealed();
    UFUNCTION(Client, Reliable) void Client_ReturnWindow(float Seconds);

private:
    friend struct FIBSkillCombatCheck;

	void ExecuteEffect(EIBSkillSlot Slot);
	const FIBKitAbilitySpec& SpecFor(bool bMovementTool) const { return bMovementTool ? ActiveKit.MovementTool : ActiveKit.KitAbility; }

	FVector LookDirection(bool bFlatten) const;
	void DoDash(const FIBKitAbilitySpec& Spec);
	void DoGrapple(const FIBKitAbilitySpec& Spec);
	void DoGlide(const FIBKitAbilitySpec& Spec);
	void EndGlide();
	void DoConeStrikeDamage(const FIBKitAbilitySpec& Spec);
    void DoStrikeDamage(FIBKitAbilitySpec Spec, bool bRadial);
    bool TryReturn();
    bool CanActivate() const;
	void DoDeployZone(const FIBKitAbilitySpec& Spec);
	void OpenDefenseWindow(const FIBKitAbilitySpec& Spec);
	void EnsureHud();

	ACharacter* OwnerCharacter() const;
	APlayerController* OwnerPC() const;
	double Now() const;

	FIBClassKit ActiveKit;
	EIBOperativeClass ResolvedClass = EIBOperativeClass::Breaker;
	bool bResolvedFromIdentity = false;
	/** A kit (identity-resolved or defaults) has been applied at least once. Lets the
	 *  identity-less tick path (AI pawns, previews, pre-PlayerState clients) skip the
	 *  re-resolve + asset load + log every frame -- it only re-runs when something changed. */
	bool bKitApplied = false;

	FIBSkillState AppliedSkills;
    TArray<FIBKitAbilitySpec> SlotSpecs;
    double SlotReadyTime[4] = {};
    TMap<FName, double> AbilityReadyTime;
    double ReturnUntil = 0;
    FVector ReturnAnchor;
    UPROPERTY(ReplicatedUsing=OnRep_Concealed) bool bConcealed = false;
    UPROPERTY(Replicated) float GuardEnergy = 0;
    double CloakUntil = 0;
    double GuardUntil = 0;
    float GuardScale = 1;
    double WardUntil = 0;
    float WardScale = 1;
    TArray<TWeakObjectPtr<class UMeshComponent>> ConcealedMeshes;

	double DefenseUntil = 0.0;
	float DefenseScale = 1.f;

	bool bGliding = false;
	float SavedGravityScale = 1.f;
	float SavedAirControl = 0.05f;
	FTimerHandle GlideHandle;
	TArray<FTimerHandle> EffectHandles;

	UPROPERTY(Transient)
	TObjectPtr<UIBKitHudWidget> Hud;
};
