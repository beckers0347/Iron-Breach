#pragma once

#include "CoreMinimal.h"
#include "InputActionValue.h"
#include "GameFramework/Character.h"
#include "Combat/WeaponDataAsset.h"
#include "Combat/WeaponRigComponent.h"
#include "Mech/ConcordComponent.h"
#include "IBMech_Base.generated.h"

class AController;
class APlayerController;
class USpringArmComponent;
class UCameraComponent;
class UWeaponRigComponent;
class AIBMechAIController;
class AIBGunnerSeat;
class AIBCharacter_Infantry;

/**
 * Caryatid-class mech hull. Two crew: a navigator/driver (hull movement) and a gunner
 * (weapons). Implements decision uq4 Option B from Docs/CARYATID-architecture.md:
 *
 *   - The NAVIGATOR possesses this hull (an ACharacter) and gets UE's client-predicted
 *     CharacterMovement for free.
 *   - The GUNNER possesses the attached AIBGunnerSeat pawn (spawned by the hull,
 *     server-side) with owner-authoritative replicated aim and the Server_Fire
 *     cosmetic-first weapon path.
 *   - The AI co-pilot possesses that same seat when no human holds it — parity by
 *     construction.
 *   - Boarding is a server-arbitrated possession swap (ServerBoard/ServerDisembark):
 *     the infantry pawn is parked (hidden, collision off) and the pilot possesses the
 *     hull or the seat. Mid-fight seat swap is the same operation (ServerRequestCrewSwap).
 *   - UConcordComponent (the clasp) lives here, server-side, replicating sync state to
 *     both cockpit HUDs.
 *
 * SEATS vs ROLES (legacy single-machine flow — still supported):
 *   - Seat  = where a controller is physically sitting (Left / Right). Set on boarding.
 *   - Role  = what that controller is currently doing (Driver / Gunner). Swaps mid-fight.
 * Roles are always DERIVED from seats via RecomputeRoles(), never assigned ad hoc. The
 * BP seat-select flow (widget buttons -> ChooseSeat + Possess) and the AI-copilot role
 * swap continue to work exactly as before on a single machine; the possession-based
 * networked path activates automatically when a second human boards.
 */
UCLASS()
class IRONBREACH_API AIBMech_Base : public ACharacter
{
	GENERATED_BODY()

public:
	AIBMech_Base();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
	virtual void PawnClientRestart() override;

	/** Clears stale crew pointers when a new controller takes the hull (e.g. player boards
	 *  after an AI controller was auto-possessing). Without this the boarding player gets a
	 *  seat but no role, and every input route rejects them. ServerBoard seats the pilot
	 *  BEFORE possessing, so the legitimate boarding path never triggers the wipe. */
	virtual void PossessedBy(AController* NewController) override;

	void PerformWeaponTrace();

public:
	// --- SEAT ASSIGNMENTS ---
	// Who is physically sitting where (Player or AI)
	UPROPERTY(BlueprintReadOnly, Category = "Mech|Seats")
	TObjectPtr<AController> LeftSeatController;

	UPROPERTY(BlueprintReadOnly, Category = "Mech|Seats")
	TObjectPtr<AController> RightSeatController;

	// --- ROLE ASSIGNMENTS ---
	// Who is doing what right now. Derived from seats — do not set these directly.
	UPROPERTY(BlueprintReadOnly, Category = "Mech|Roles")
	TObjectPtr<AController> CurrentDriver;

	UPROPERTY(BlueprintReadOnly, Category = "Mech|Roles")
	TObjectPtr<AController> CurrentGunner;

	// --- SEATING FUNCTIONS (legacy single-machine flow + shared bookkeeping) ---
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void AssignToLeftSeat(AController* NewController);

	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void AssignToRightSeat(AController* NewController);

	/** Removes a controller from whatever seat it holds and re-derives roles. */
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void VacateSeat(AController* LeavingController);

	/** Wipes both seats and both roles. Called on possession change. */
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void ResetCrew();

	UFUNCTION(BlueprintPure, Category = "Mech|System")
	bool IsControllerSeated(AController* InController) const
	{
		return InController && (InController == LeftSeatController || InController == RightSeatController);
	}

	// The instant-swap logic for the single-machine flow (human + AI co-pilot)
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void PerformRoleSwap();

	// Allows a seated controller to request a role hot-swap
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RequestRoleSwap(AController* Requester);

	// --- CARYATID BOARDING / CREW (server-arbitrated possession, uq4 Option B) ---

	/** SERVER ONLY. Boards a pilot: parks the infantry pawn and possesses them into the
	 *  hull (bWantLeftSeat / navigator) or the gunner seat. A pilot boarding an empty mech
	 *  always drives — a gunner with no driver is a mech that cannot move. Returns success. */
	UFUNCTION(BlueprintCallable, Category = "Mech|Boarding")
	bool ServerBoard(AController* BoardingController, AIBCharacter_Infantry* FromPawn, bool bWantLeftSeat);

	/** SERVER ONLY. Dismounts a pilot back into their parked infantry pawn beside the hull. */
	UFUNCTION(BlueprintCallable, Category = "Mech|Boarding")
	void ServerDisembark(AController* LeavingController);

	/** SERVER ONLY. Seat swap: human+AI uses the legacy role swap; human+human arms a
	 *  confirm handshake — when the partner also presses swap within the window, the two
	 *  pilots exchange pawns (hull <-> seat). */
	UFUNCTION(BlueprintCallable, Category = "Mech|Boarding")
	void ServerRequestCrewSwap(AController* Requester);

	/** The gunner seat pawn this hull spawned (server) — replicated. */
	UPROPERTY(ReplicatedUsing = OnRep_GunnerSeat, BlueprintReadOnly, Category = "Mech|Boarding")
	TObjectPtr<AIBGunnerSeat> GunnerSeat;

	/** Optional BP subclass for the seat (cockpit dressing, input assets). Falls back to
	 *  the C++ class when unset. */
	UPROPERTY(EditDefaultsOnly, Category = "Mech|Boarding")
	TSubclassOf<AIBGunnerSeat> GunnerSeatClass;

	/** Socket on MechMesh the seat attaches to. Missing socket -> cockpit-camera offset. */
	UPROPERTY(EditDefaultsOnly, Category = "Mech|Boarding")
	FName GunnerSeatSocket = TEXT("GunnerSeat");

	// --- CONCORD (the clasp) ---
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Concord")
	TObjectPtr<UConcordComponent> Concord;

	UFUNCTION(BlueprintPure, Category = "Mech|Concord")
	UConcordComponent* GetConcord() const { return Concord; }

	/** Desync safety-lock on the heavy weapons (spec §3.2). Checked by both fire paths. */
	UFUNCTION(BlueprintPure, Category = "Mech|Concord")
	bool AreWeaponsSafetyLocked() const;

	/** HUD hook: a fire attempt was refused by the desync safety lock. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Mech|Concord")
	void OnWeaponsSafetyLocked();

	/** Reconnection Ritual verb from the DRIVER side (gunner sends via the seat). */
	UFUNCTION(BlueprintCallable, Category = "Mech|Concord")
	void SendRitualInput(EConcordRitualStep Step);

	// --- INPUT ROUTING (legacy single-machine gatekeeper) ---
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RouteMoveInput(AController* Requester, const FVector2D& InputValue);

	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void RouteLookInput(AController* Requester, const FVector2D& InputValue);

	// Handles weapon firing triggers (legacy hull path; the seat fires via its component)
	UFUNCTION(BlueprintCallable, Category = "Mech|Combat")
	void FireWeapon(AController* Requester);

	// Active weapon data reference
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|Combat")
	TObjectPtr<UWeaponDataAsset> CurrentWeaponData;

	// Weapon equip function
	UFUNCTION(BlueprintCallable, Category = "Mech|Combat")
	void EquipWeapon(UWeaponDataAsset* NewWeaponData);

	// The massive mech chassis and head mesh.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<USkeletalMeshComponent> MechMesh;

	/** The mech's arm-mounted weapon. SEPARATE from MechMesh on purpose: the weapon rig
	 *  writes SetRelativeLocation every tick, so pointing it at MechMesh drags the entire
	 *  chassis off its capsule as the ADS blend moves. Assign the arm cannon mesh here. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<USkeletalMeshComponent> MechWeaponMesh;

	// Driver's 3rd Person camera setup.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<USpringArmComponent> DriverSpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<UCameraComponent> DriverCamera_3PV;

	// Gunner's 1st Person cockpit camera setup (legacy single-machine gunner view; the
	// networked gunner renders through the seat's own camera instead).
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Components")
	TObjectPtr<UCameraComponent> GunnerCamera_FPV;

	// Weapon Rig — FPV posing + ADS blend for the mech's arm weapon (local/cosmetic).
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech|Combat")
	TObjectPtr<UWeaponRigComponent> WeaponRigComponent;

	UPROPERTY(BlueprintReadWrite, Category = "Mech|Views")
	bool bIsDriverActive = true;

	// Function to toggle between views.
	UFUNCTION(BlueprintCallable, Category = "Mech|Views")
	void ToggleViewMode();

	// Reference to the Gunner's minimalist cockpit UI crosshair.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|UI")
	TSubclassOf<UUserWidget> CockpitCrosshairClass;

	/** LOCAL VIEW STATE ONLY — "is the locally-viewing pilot currently the gunner".
	 *  This is not per-seat crew state; do not use it to decide who may fire. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech State")
	bool bIsGunner;

	// This tells C++ to send a signal to the Blueprint. We don't write a body for it in .cpp!
	UFUNCTION(BlueprintImplementableEvent, Category = "Mech State")
	void OnRoleSwapped(bool bIsNowGunner);

	// --- HUD & STATS DATA (Shane's WBP_MechHUD bindings — names unchanged) ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech Stats")
	float MaxHealth = 100.0f;

	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Mech Stats")
	float CurrentHealth = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech Stats")
	int32 MaxAmmo = 50;

	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Mech Stats")
	int32 CurrentAmmo = 50;

	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Mech Stats")
	float WeaponCooldownRemaining = 0.0f;

	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Mech Stats")
	FString PartnerName = "Partner";

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mech Stats")
	float PartnerCooldownRemaining = 0.0f;

	/** Seconds between shots. Falls back to this when CurrentWeaponData has no fire rate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech Stats", meta = (ClampMin = "0.0"))
	float WeaponFireInterval = 0.35f;

	/** Degrees of gunner yaw per unit of look input. The driver path goes through
	 *  AddControllerYawInput (which applies engine sensitivity); the gunner path writes the
	 *  rotation directly, so it needs its own scalar or the two feel wildly different. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|Views", meta = (ClampMin = "0.01"))
	float GunnerYawSensitivity = 1.0f;

	/** How far off the hull's forward axis the gunner may traverse, in degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|Views", meta = (ClampMin = "5.0", ClampMax = "180.0"))
	float GunnerYawLimit = 90.0f;

	// Broadcast event for when your partner presses the swap button
	UFUNCTION(BlueprintImplementableEvent, Category = "Mech State")
	void OnPartnerSwapNotified();

	// Specific seat assignment functions
	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	bool TryEnterSeat(AController* InputController, bool bTargetLeftSeat);

	UFUNCTION(BlueprintCallable, Category = "Mech|System")
	void ChooseSeat(AController* SelectingController, bool bWantLeftSeat);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mech|UI")
	TSubclassOf<class UUserWidget> SeatSelectWidgetClass;

	UPROPERTY()
	TObjectPtr<AIBMechAIController> CoPilotController;

	UFUNCTION(BlueprintCallable, Category = "Mech|Views")
	void ApplyLocalViewForRole(AController* SelectingController);

protected:
	/** Driver-side ritual verb routing (hull is owned by the driver's connection). */
	UFUNCTION(Server, Reliable)
	void Server_SendRitualInput(EConcordRitualStep Step);

	/** Both machines need the "partner wants to swap" ping, not just the server. */
	UFUNCTION(NetMulticast, Reliable)
	void Multicast_PartnerSwapRequested();

	UFUNCTION()
	void OnRep_GunnerSeat();

private:
	/** Single place that decides who drives and who shoots, based purely on seat occupancy.
	 *  Preserves an existing valid role pairing; otherwise defaults Left=Driver, Right=Gunner. */
	void RecomputeRoles();

	/** Null-safe camera switch. */
	void SetGunnerViewActive(bool bGunnerView);

	/** Server: spawn + attach the gunner seat pawn. */
	void SpawnGunnerSeat();

	/** Server: AI co-pilot possesses the seat when no human holds it. */
	void BackfillSeatWithAI();

	/** Server: hide/park and restore infantry pawns across boarding. */
	void ParkInfantryPawn(AIBCharacter_Infantry* Pawn);
	void UnparkInfantryPawn(APawn* Pawn, const FVector& AtLocation);

	/** Server: swap the two human pilots between hull and seat (handshake completion). */
	void PerformPossessionSwap(APlayerController* DriverPC, APlayerController* GunnerPC);

	FString DescribeCrewName(AController* CrewController) const;

	// Cache the widget instance for performance.
	UPROPERTY()
	TObjectPtr<UUserWidget> CockpitCrosshairInstance;

	// Server-only: pawns parked by boarding, per station.
	UPROPERTY()
	TObjectPtr<APawn> ParkedDriverPawn;

	UPROPERTY()
	TObjectPtr<APawn> ParkedGunnerPawn;

	// Server-only: pending human-human swap handshake.
	TWeakObjectPtr<AController> SwapRequestedBy;
	double SwapRequestExpiry = 0.0;

	/** Seconds the partner has to confirm a human-human seat swap. */
	UPROPERTY(EditAnywhere, Category = "Mech|Boarding", meta = (ClampMin = "1.0"))
	float SwapConfirmWindow = 5.0f;

	float BaseMaxWalkSpeed = 0.0f;
};
