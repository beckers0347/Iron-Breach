#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "InputActionValue.h"
#include "Mech/ConcordComponent.h"
#include "IBGunnerSeat.generated.h"

class AIBMech_Base;
class UCameraComponent;
class UHitscanWeaponComponent;
class UInputAction;
class UTargetingComponent;

/**
 * The gunner's half of the Caryatid (Docs/CARYATID-architecture.md, decision uq4 Option B):
 * the navigator possesses the hull and gets client-predicted CMC for free; the GUNNER
 * possesses this lightweight pawn, attached to the hull at the cockpit.
 *
 *  - Aim is owner-authoritative: the owning client aims locally (instant), streams the
 *    rotation to the server (unreliable RPC), and the server replicates it to everyone
 *    else — the hull reads GetAimRotation() to pose the arm cannon for all machines.
 *  - Firing reuses UHitscanWeaponComponent: cosmetic-first + Server_Fire, the exact
 *    ADR-002 pattern the infantry rifle already ships with. Same code family, no forks.
 *  - An AI co-pilot (AIBMechAIController) possesses this same pawn when the second seat
 *    is empty — parity with a human gunner by construction.
 *
 * Input reaches the seat two ways, both supported: AIBMechPlayerController routes its
 * existing bindings here when it possesses a seat (zero new content needed), and the
 * seat also binds its own optional action assets for a future IMC_Gunner context.
 */
UCLASS()
class IRONBREACH_API AIBGunnerSeat : public APawn
{
	GENERATED_BODY()

public:
	AIBGunnerSeat();

	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void PawnClientRestart() override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Hull this seat belongs to. Set by the hull at spawn (deferred), replicated. */
	UPROPERTY(ReplicatedUsing = OnRep_OwningMech, BlueprintReadOnly, Category = "Seat")
	TObjectPtr<AIBMech_Base> OwningMech;

	/** Cockpit first-person camera. Renders only for the possessing gunner. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Seat")
	TObjectPtr<UCameraComponent> CockpitCamera;

	/** The mech's gun, fired from this seat. Cosmetic-first + Server_Fire (ADR-002). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Seat")
	TObjectPtr<UHitscanWeaponComponent> WeaponComponent;

	/** Lock-on assist for the cockpit HUD (um-08). Local, per-gunner. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Seat")
	TObjectPtr<UTargetingComponent> TargetingComponent;

	// ---- Optional Enhanced Input assets (assign in a BP subclass for IMC_Gunner; the
	//      MechPlayerController routing works without them) ----
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> FireAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> ADSAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<UInputAction> SwapAction;

	// ---- Called by the possessing machine (input handlers or MechPC routing) ----

	/** Full 2D look vector. Yaw clamps against the hull's forward (GunnerYawLimit). */
	UFUNCTION(BlueprintCallable, Category = "Seat")
	void ProcessLook(const FVector2D& LookVector);

	UFUNCTION(BlueprintCallable, Category = "Seat")
	void HandleFirePressed();

	UFUNCTION(BlueprintCallable, Category = "Seat")
	void SetAiming(bool bNewAiming);

	/** Ask the server to swap this gunner with the driver (possession swap / handshake). */
	UFUNCTION(BlueprintCallable, Category = "Seat")
	void RequestSwap();

	/** Ask the server to dismount back into the parked infantry pawn. */
	UFUNCTION(BlueprintCallable, Category = "Seat")
	void RequestExit();

	/** Reconnection Ritual verb from the gunner seat. */
	UFUNCTION(BlueprintCallable, Category = "Seat")
	void SendRitualInput(EConcordRitualStep Step);

	// ---- Reads ----

	/** World-space aim of this seat, valid on every machine (server + proxies use the
	 *  replicated value; the owning client uses its live control rotation). */
	UFUNCTION(BlueprintPure, Category = "Seat")
	FRotator GetAimRotation() const;

	UFUNCTION(BlueprintPure, Category = "Seat")
	bool IsAiming() const { return bWantAds; }

protected:
	virtual void BeginPlay() override;

	/** Owner->server aim stream. Unreliable by design: the next update supersedes a drop. */
	UFUNCTION(Server, Unreliable)
	void Server_SetAim(FRotator NewAim);

	UFUNCTION(Server, Reliable)
	void Server_RequestSwap();

	UFUNCTION(Server, Reliable)
	void Server_RequestExit();

	UFUNCTION(Server, Reliable)
	void Server_SendRitualInput(EConcordRitualStep Step);

	UFUNCTION()
	void OnRep_OwningMech();

	// Input-asset handler shims
	void OnLookInput(const FInputActionValue& Value);
	void OnFireInput(const FInputActionValue& Value);
	void OnAdsInput(const FInputActionValue& Value);
	void OnSwapInput(const FInputActionValue& Value);

private:
	/** Server-set, replicated to proxies. The hull poses the arm from this. */
	UPROPERTY(Replicated)
	FRotator ReplicatedAim = FRotator::ZeroRotator;

	FRotator LastSentAim = FRotator::ZeroRotator;
	bool bWantAds = false;

	/** Pull the hull's weapon data into our weapon component (idempotent). */
	void SyncWeaponFromMech();
};
