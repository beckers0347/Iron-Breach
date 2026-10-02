// IBGuideRoute.h
//
// "Drag the player along": a lead NPC (e.g. Lt. Rhodes) walks a route and the player has
// to keep up. The guide stops and waits when the player falls behind, calls them on with
// (optionally voiced) call-out lines, and broadcasts events at each stop so dialogue,
// lighting, or the next act can hang off them. Squad followers trail behind the guide.
//
// Works with the placeholder NPCs as they are today: plain SkeletalMeshActors running
// ABP_NPC_Locomotion. The route moves them in code and keeps ComponentVelocity updated, so
// the ABP's "Get Owning Actor -> Get Velocity -> Vector Length -> Set Speed" graph blends
// Idle -> Walk by itself.
//
// Setup (ib_setup_guided_opening.py does this for you):
//   1. Drop one AIBGuideRoute in the level (placing it at the world origin makes waypoint
//      locations equal world coordinates).
//   2. Set GuideActor, optional Followers, and the Waypoints.
//   3. Either tick bAutoStart, set StartAfterAct1 (route begins when Act I completes), or
//      call StartRoute() from a trigger / Blueprint.
//
// Notes / limits (v1):
//   - Authority only: runs in single player and on the listen-server host. Co-op clients
//     see the NPCs stationary (movement replication is a v2 item).
//   - Movement is straight-line steps toward nav-mesh path points (falls back to direct
//     lines if no nav path), snapped to the ground with a trace.
//   - Subtitles: the route implements IActBeatProviderInterface, so the existing
//     MissionSubtitleHUD shows its call-out/arrival lines while one is on screen.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBLandfallDialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "IBGuideRoute.generated.h"

class AAct1BarracksDirector;
class APawn;

// One stop on the route.
USTRUCT(BlueprintType)
struct FIBGuideWaypoint
{
	GENERATED_BODY()

	// Position relative to the route actor (drag the diamond in the viewport).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Waypoint", meta = (MakeEditWidget = true))
	FVector Location = FVector::ZeroVector;

	// The guide holds here until a player is within this radius. 0 = never waits.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Waypoint")
	float WaitForPlayerRadius = 600.0f;

	// Extra seconds to stand at this stop (after the player has caught up).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Waypoint")
	float PauseSeconds = 0.0f;

	// Broadcast through OnWaypointReached when the guide arrives (NAME_None = no tag).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Waypoint")
	FName ArrivalEventTag = NAME_None;

	// Optional line shown (and voiced) on arrival. Empty Text = no line.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Waypoint")
	FDialogueLine ArrivalLine;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnGuideWaypointReached, int32, WaypointIndex, FName, EventTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGuideRouteComplete);

// Internal expanded path node (nav-mesh corners between waypoints). Not reflected.
struct FIBGuidePathNode
{
	FVector Pos = FVector::ZeroVector;
	int32 WaypointIndex = INDEX_NONE; // INDEX_NONE = intermediate corner, otherwise a waypoint stop

	FIBGuidePathNode() = default;
	FIBGuidePathNode(const FVector& InPos, int32 InWaypointIndex) : Pos(InPos), WaypointIndex(InWaypointIndex) {}
};

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AIBGuideRoute : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AIBGuideRoute();

	virtual void Tick(float DeltaSeconds) override;

	// ---------------- Who walks ----------------

	// The NPC that leads (a SkeletalMeshActor, Character, or any actor).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Actors")
	TSoftObjectPtr<AActor> GuideActor;

	// Squad members who trail the guide.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Actors")
	TArray<TSoftObjectPtr<AActor>> Followers;

	// ---------------- Route ----------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Route")
	TArray<FIBGuideWaypoint> Waypoints;

	// Route around obstacles using the nav mesh when one exists.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Route")
	bool bUseNavMesh = true;

	// ---------------- Movement ----------------

	// Walking speed in cm/s. ~150 is the walk pose in BS_NPC_Unarmed_Locomotion, 375 the run.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float WalkSpeed = 180.0f;

	// Degrees/second the NPCs turn toward their walking direction.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float TurnRateDegPerSec = 300.0f;

	// Added to the walking direction yaw. Use if the mesh's "forward" isn't +X.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float FacingYawOffset = 0.0f;

	// Within this distance of a path node counts as arrived.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float ArrivalToleranceCm = 60.0f;

	// How far behind the guide each follower trails (multiplied by their index + 1).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float FollowerSpacingCm = 170.0f;

	// Sideways stagger so followers don't stand in a perfect line (alternates left/right).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Movement")
	float FollowerSideOffsetCm = 70.0f;

	// ---------------- Keeping the player with us ----------------

	// If the nearest player is farther than this from the guide, the guide stops and waits.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Leash")
	float LeashDistanceCm = 900.0f;

	// While waiting for a lagging player, speak a call-out this often (seconds).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Leash")
	float CallOutIntervalSeconds = 7.0f;

	// Lines cycled while waiting. Voiced via VoiceSound or A-tag "GC" (GC_L000, GC_L001, ...).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Leash")
	TArray<FDialogueLine> CallOutLines;

	// ---------------- Dragging the player along ----------------

	// Physically pull the player toward the guide when they lag or stray (the squad "drags" them).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	bool bPullPlayer = true;

	// Seconds the player may stay beyond LeashDistanceCm (while call-outs play) before being pulled.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float PullGraceSeconds = 3.0f;

	// Beyond this distance from the guide the player is pulled immediately (no grace). Also stops
	// the player from running far ahead of the squad.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float MaxStrayDistanceCm = 1600.0f;

	// How fast the player is pulled (cm/s). Faster than a sprint so they can't resist.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float PullSpeedCm = 650.0f;

	// Pulling stops once the player is this close to the guide.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float PullTargetDistanceCm = 450.0f;

	// Turn the player's view toward the direction they are being pulled.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	bool bTurnPlayerWhilePulled = true;

	// How fast the view turns (degrees/second) while being pulled.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float PullTurnRateDegPerSec = 140.0f;

	// If a wall blocks the pull for this long, the player is placed beside the guide instead.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Pull")
	float BlockedTeleportSeconds = 1.5f;

	// ---------------- Starting ----------------

	// Start automatically at BeginPlay (after StartDelaySeconds).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Start")
	bool bAutoStart = false;

	// Start when this Act I director finishes (stand-to order given).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Start")
	TSoftObjectPtr<AAct1BarracksDirector> StartAfterAct1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Start")
	float StartDelaySeconds = 1.5f;

	// Draw the path and waypoints in the world while playing.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guide|Debug")
	bool bDebugDraw = false;

	// ---------------- Events ----------------

	UPROPERTY(BlueprintAssignable, Category = "Guide|Events")
	FOnGuideWaypointReached OnWaypointReached;

	UPROPERTY(BlueprintAssignable, Category = "Guide|Events")
	FOnGuideRouteComplete OnRouteComplete;

	// ---------------- API ----------------

	UFUNCTION(BlueprintCallable, Category = "Guide")
	void StartRoute();

	UFUNCTION(BlueprintCallable, Category = "Guide")
	void StopRoute();

	UFUNCTION(BlueprintPure, Category = "Guide")
	bool IsRouteActive() const { return bActive; }

	// ---------------- IActBeatProviderInterface (subtitles) ----------------

	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;
	virtual bool IsActRunning() const override { return bLineShowing; }

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleAct1Complete();

	void BuildPath(const FVector& StartLocation);
	void FinishRoute();

	float DistanceToNearestPlayer(const FVector& From) const;
	float GetGroundZ(const FVector& Pos, float FallbackZ, const AActor* IgnoreActor) const;

	void HoldActor(AActor* Actor) const;
	void SetActorWalkVelocity(AActor* Actor, const FVector& Velocity) const;
	void FaceDirection(AActor* Actor, const FVector& Direction, float DeltaSeconds) const;
	void TickFollowers(float DeltaSeconds, const AActor* Guide);
	void TickCallOuts(float DeltaSeconds);
	void TickPlayerPull(float DeltaSeconds, const AActor* Guide);

	void ShowLine(const FDialogueLine& Line, const TCHAR* VoiceTag, int32 VoiceIndex);
	void UpdateDisplayedLine();

	TArray<FIBGuidePathNode> PathNodes;
	int32 NodeIdx = 0;
	bool bActive = false;
	bool bArrivalHandled = false;
	bool bPauseDone = false;
	bool bWasHolding = false;
	float PauseRemaining = 0.0f;
	float CallOutTimer = 0.0f;
	int32 CallOutIndex = 0;
	FVector LastMoveDir = FVector::ForwardVector;

	// Subtitle state
	FDialogueLine DisplayedLine;
	bool bLineShowing = false;
	double LineEndTime = 0.0;

	TMap<TWeakObjectPtr<const APawn>, float> PullTimers;
	TMap<TWeakObjectPtr<const APawn>, float> PullBlockedTimers;

	FTimerHandle StartTimerHandle;
};
