#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Classes/IBClassKitTypes.h"
#include "InputCoreTypes.h"
#include "IBOperativeKitComponent.generated.h"

class UIBClassKitData;
class UIBKitHudWidget;
class UInputAction;
class UInputComponent;
class ACharacter;
class APlayerController;

/**
 * The operative's class kit on the infantry pawn: resolves the trade from the
 * PlayerState's operative identity, loads DA_Kit_<Trade> (or built-in
 * defaults), binds Q (kit ability) and V (movement tool), runs the generic
 * effects with cooldowns, and shows a two-chip HUD for the local player.
 *
 * Authority (ADR-002): the owning client predicts movement effects locally
 * and asks the server; the server re-validates cooldowns, runs the effect
 * for real (damage, zones), and multicasts the activation so every machine
 * can play FX through BP_OnKitActivated. Designers: reshape the kits in the
 * data assets; add FX in a BP child of the pawn; use Effect = Blueprint for
 * anything the primitives don't cover.
 */
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

	/** Per-trade kit assets; missing entries fall back to the built-in defaults. */
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
	void Server_Activate(bool bMovementTool);

	UFUNCTION(NetMulticast, Unreliable)
	void Multicast_Activated(bool bMovementTool);

private:
	void TryActivate(bool bMovementTool);
	void ExecuteEffect(bool bMovementTool, bool bAuthority, bool bLocal);
	const FIBKitAbilitySpec& SpecFor(bool bMovementTool) const { return bMovementTool ? ActiveKit.MovementTool : ActiveKit.KitAbility; }

	FVector LookDirection(bool bFlatten) const;
	void DoDash(const FIBKitAbilitySpec& Spec);
	void DoGrapple(const FIBKitAbilitySpec& Spec);
	void DoGlide(const FIBKitAbilitySpec& Spec);
	void EndGlide();
	void DoConeStrikeDamage(const FIBKitAbilitySpec& Spec);
	void DoDeployZone(const FIBKitAbilitySpec& Spec);
	void OpenDefenseWindow(const FIBKitAbilitySpec& Spec);
	void EnsureHud();

	ACharacter* OwnerCharacter() const;
	APlayerController* OwnerPC() const;
	double Now() const;

	FIBClassKit ActiveKit;
	EIBOperativeClass ResolvedClass = EIBOperativeClass::Breaker;
	bool bResolvedFromIdentity = false;

	double KitReadyTime = 0.0;
	double MoveReadyTime = 0.0;

	double DefenseUntil = 0.0;
	float DefenseScale = 1.f;

	bool bGliding = false;
	float SavedGravityScale = 1.f;
	float SavedAirControl = 0.05f;
	FTimerHandle GlideHandle;
	FTimerHandle StrikeHandle;

	UPROPERTY(Transient)
	TObjectPtr<UIBKitHudWidget> Hud;
};
