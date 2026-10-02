// IBGuideRoute.cpp

#include "IBGuideRoute.h"
#include "Act1BarracksDirector.h"
#include "IBDialogueVoice.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/SceneComponent.h"
#include "CollisionQueryParams.h"
#include "NavigationSystem.h"
#include "NavigationPath.h"
#include "DrawDebugHelpers.h"

AIBGuideRoute::AIBGuideRoute()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	// Default "keep up" call-outs; edit per instance in Details.
	CallOutLines.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Ferryman, with me. Move.")),
		2.5f, 0.5f));
	CallOutLines.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("Don't lag, Ferryman. We're on the clock.")),
		3.0f, 0.5f));
	CallOutLines.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Keep up. That's an order.")),
		2.5f, 0.5f));
}

void AIBGuideRoute::BeginPlay()
{
	Super::BeginPlay();

	if (AAct1BarracksDirector* Act1 = StartAfterAct1.Get())
	{
		Act1->OnAct1Complete.AddDynamic(this, &AIBGuideRoute::HandleAct1Complete);
		UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] '%s' will start when Act I completes."), *GetName());
	}

	if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AIBGuideRoute::StartRoute, FMath::Max(0.01f, StartDelaySeconds), false);
	}
}

void AIBGuideRoute::HandleAct1Complete()
{
	UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] Act I complete -> starting route in %.1fs."), StartDelaySeconds);
	GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AIBGuideRoute::StartRoute, FMath::Max(0.01f, StartDelaySeconds), false);
}

// ----------------------------------------------------------------------------
// Start / stop
// ----------------------------------------------------------------------------

void AIBGuideRoute::StartRoute()
{
	if (!HasAuthority())
	{
		return; // v1: authority only (see header notes)
	}

	AActor* Guide = GuideActor.Get();
	if (!Guide)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[GuideRoute] '%s': GuideActor is not set/loaded -- route not started."), *GetName());
		return;
	}
	if (Waypoints.Num() == 0)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[GuideRoute] '%s': no waypoints -- route not started."), *GetName());
		return;
	}

	BuildPath(Guide->GetActorLocation());
	NodeIdx = 0;
	bActive = true;
	bArrivalHandled = false;
	bPauseDone = false;
	bWasHolding = false;
	PauseRemaining = 0.0f;
	CallOutTimer = 0.0f;
	CallOutIndex = 0;
	SetActorTickEnabled(true);

	UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] '%s' started: guide='%s', %d waypoint(s), %d path node(s), speed=%.0f."),
		*GetName(), *Guide->GetName(), Waypoints.Num(), PathNodes.Num(), WalkSpeed);
}

void AIBGuideRoute::StopRoute()
{
	if (!bActive)
	{
		return;
	}
	bActive = false;
	HoldActor(GuideActor.Get());
	for (const TSoftObjectPtr<AActor>& F : Followers)
	{
		HoldActor(F.Get());
	}
	UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] '%s' stopped."), *GetName());
}

void AIBGuideRoute::FinishRoute()
{
	bActive = false;
	HoldActor(GuideActor.Get());
	for (const TSoftObjectPtr<AActor>& F : Followers)
	{
		HoldActor(F.Get());
	}
	UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] '%s' complete."), *GetName());
	OnRouteComplete.Broadcast();
}

// ----------------------------------------------------------------------------
// Path building
// ----------------------------------------------------------------------------

void AIBGuideRoute::BuildPath(const FVector& StartLocation)
{
	PathNodes.Reset();

	UWorld* World = GetWorld();
	UNavigationSystemV1* Nav = (bUseNavMesh && World) ? UNavigationSystemV1::GetCurrent(World) : nullptr;

	FVector From = StartLocation;
	for (int32 i = 0; i < Waypoints.Num(); ++i)
	{
		const FVector To = GetActorTransform().TransformPosition(Waypoints[i].Location);
		bool bAdded = false;

		if (Nav)
		{
			UNavigationPath* NavPath = Nav->FindPathToLocationSynchronously(World, From, To, nullptr);
			if (NavPath && NavPath->IsValid() && NavPath->PathPoints.Num() >= 2)
			{
				const int32 Last = NavPath->PathPoints.Num() - 1;
				for (int32 p = 1; p <= Last; ++p)
				{
					PathNodes.Emplace(NavPath->PathPoints[p], (p == Last) ? i : INDEX_NONE);
				}
				bAdded = true;
				UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] leg %d: nav path with %d point(s)."), i, NavPath->PathPoints.Num());
			}
		}

		if (!bAdded)
		{
			PathNodes.Emplace(To, i);
			UE_LOG(LogIronBreach, Warning, TEXT("[GuideRoute] leg %d: no nav path (nav mesh missing or unreachable) -- walking a direct line."), i);
		}
		From = To;
	}
}

// ----------------------------------------------------------------------------
// Tick
// ----------------------------------------------------------------------------

void AIBGuideRoute::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UpdateDisplayedLine();

	if (!bActive)
	{
		if (!bLineShowing)
		{
			SetActorTickEnabled(false);
		}
		return;
	}

	AActor* Guide = GuideActor.Get();
	if (!Guide)
	{
		StopRoute();
		return;
	}

	if (bDebugDraw && GetWorld())
	{
		for (int32 i = 0; i + 1 < PathNodes.Num(); ++i)
		{
			DrawDebugLine(GetWorld(), PathNodes[i].Pos + FVector(0, 0, 30), PathNodes[i + 1].Pos + FVector(0, 0, 30), FColor::Cyan, false, 0.0f, 0, 3.0f);
		}
		for (const FIBGuidePathNode& N : PathNodes)
		{
			if (N.WaypointIndex != INDEX_NONE)
			{
				DrawDebugSphere(GetWorld(), N.Pos + FVector(0, 0, 30), 40.0f, 8, FColor::Yellow, false, 0.0f);
			}
		}
	}

	const FVector GuidePos = Guide->GetActorLocation();
	const float PlayerDist = DistanceToNearestPlayer(GuidePos);

	// Standing still at a stop (PauseSeconds).
	if (PauseRemaining > 0.0f)
	{
		PauseRemaining -= DeltaSeconds;
		HoldActor(Guide);
		TickFollowers(DeltaSeconds, Guide);
		return;
	}

	if (!PathNodes.IsValidIndex(NodeIdx))
	{
		FinishRoute();
		return;
	}

	const FIBGuidePathNode Node = PathNodes[NodeIdx]; // copy: NodeIdx changes below
	FVector ToTarget = Node.Pos - GuidePos;
	ToTarget.Z = 0.0f;
	const float Dist = ToTarget.Size();

	// ---- Arrived at this node ----
	if (Dist <= ArrivalToleranceCm)
	{
		if (Node.WaypointIndex != INDEX_NONE && Waypoints.IsValidIndex(Node.WaypointIndex))
		{
			const FIBGuideWaypoint& WP = Waypoints[Node.WaypointIndex];

			if (!bArrivalHandled)
			{
				bArrivalHandled = true;
				UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] reached waypoint %d (tag=%s)."), Node.WaypointIndex, *WP.ArrivalEventTag.ToString());
				if (!WP.ArrivalLine.Text.IsEmpty())
				{
					ShowLine(WP.ArrivalLine, TEXT("GA"), Node.WaypointIndex);
				}
				OnWaypointReached.Broadcast(Node.WaypointIndex, WP.ArrivalEventTag);
			}

			// Wait here for a lagging player.
			if (WP.WaitForPlayerRadius > 0.0f && PlayerDist > WP.WaitForPlayerRadius)
			{
				if (!bWasHolding)
				{
					bWasHolding = true;
					UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] holding at waypoint %d for player (%.0f cm away, need %.0f)."),
						Node.WaypointIndex, PlayerDist, WP.WaitForPlayerRadius);
				}
				HoldActor(Guide);
				TickFollowers(DeltaSeconds, Guide);
				TickCallOuts(DeltaSeconds);
				return;
			}

			if (WP.PauseSeconds > 0.0f && !bPauseDone)
			{
				bPauseDone = true;
				PauseRemaining = WP.PauseSeconds;
				return;
			}
		}

		bWasHolding = false;
		bArrivalHandled = false;
		bPauseDone = false;
		++NodeIdx;
		if (!PathNodes.IsValidIndex(NodeIdx))
		{
			FinishRoute();
		}
		return;
	}

	// ---- Leash: player too far, wait and call them on ----
	if (PlayerDist > LeashDistanceCm)
	{
		if (!bWasHolding)
		{
			bWasHolding = true;
			UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] guide waiting: player is %.0f cm away (leash %.0f)."), PlayerDist, LeashDistanceCm);
		}
		HoldActor(Guide);
		TickFollowers(DeltaSeconds, Guide);
		TickCallOuts(DeltaSeconds);
		return;
	}

	if (bWasHolding)
	{
		bWasHolding = false;
		UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] player caught up -- guide moving again."));
	}
	CallOutTimer = 0.0f;

	// ---- Walk toward the node ----
	const FVector Dir = ToTarget / Dist;
	LastMoveDir = Dir;
	const float Step = FMath::Min(WalkSpeed * DeltaSeconds, Dist);
	FVector NewPos = GuidePos + Dir * Step;
	NewPos.Z = GetGroundZ(NewPos, GuidePos.Z, Guide);

	Guide->SetActorLocation(NewPos);
	FaceDirection(Guide, Dir, DeltaSeconds);
	SetActorWalkVelocity(Guide, Dir * WalkSpeed);

	TickFollowers(DeltaSeconds, Guide);
}

void AIBGuideRoute::TickFollowers(float DeltaSeconds, const AActor* Guide)
{
	if (!Guide || DeltaSeconds <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	const FVector GuidePos = Guide->GetActorLocation();
	const FVector Side(-LastMoveDir.Y, LastMoveDir.X, 0.0f);

	for (int32 i = 0; i < Followers.Num(); ++i)
	{
		AActor* F = Followers[i].Get();
		if (!F || F == Guide)
		{
			continue;
		}

		const float Back = FollowerSpacingCm * (i + 1);
		const float Lateral = ((i % 2 == 0) ? 1.0f : -1.0f) * FollowerSideOffsetCm;
		FVector Target = GuidePos - LastMoveDir * Back + Side * Lateral;

		const FVector FPos = F->GetActorLocation();
		FVector ToTarget = Target - FPos;
		ToTarget.Z = 0.0f;
		const float Dist = ToTarget.Size();

		if (Dist < 12.0f)
		{
			HoldActor(F);
			continue;
		}

		// Ease in: slow near the slot, up to 1.5x walk speed when far behind.
		const float Speed = FMath::Clamp(Dist * 2.0f, 0.0f, WalkSpeed * 1.5f);
		const FVector Dir = ToTarget / Dist;
		const float Step = FMath::Min(Speed * DeltaSeconds, Dist);
		FVector NewPos = FPos + Dir * Step;
		NewPos.Z = GetGroundZ(NewPos, FPos.Z, F);

		F->SetActorLocation(NewPos);
		FaceDirection(F, Dir, DeltaSeconds);
		SetActorWalkVelocity(F, Dir * Speed);
	}
}

void AIBGuideRoute::TickCallOuts(float DeltaSeconds)
{
	if (CallOutLines.Num() == 0)
	{
		return;
	}
	CallOutTimer += DeltaSeconds;
	if (CallOutTimer >= FMath::Max(1.0f, CallOutIntervalSeconds) && !bLineShowing)
	{
		CallOutTimer = 0.0f;
		const int32 Idx = CallOutIndex % CallOutLines.Num();
		UE_LOG(LogIronBreach, Verbose, TEXT("[GuideRoute] call-out #%d."), Idx);
		ShowLine(CallOutLines[Idx], TEXT("GC"), Idx);
		++CallOutIndex;
	}
}

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

float AIBGuideRoute::DistanceToNearestPlayer(const FVector& From) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return 0.0f;
	}

	float Best = -1.0f;
	for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
	{
		const APlayerController* PC = It->Get();
		const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
		if (!Pawn)
		{
			continue;
		}
		const float D = FVector::Dist2D(From, Pawn->GetActorLocation());
		if (Best < 0.0f || D < Best)
		{
			Best = D;
		}
	}
	return Best < 0.0f ? 0.0f : Best; // no player pawn yet: don't block the guide
}

float AIBGuideRoute::GetGroundZ(const FVector& Pos, float FallbackZ, const AActor* IgnoreActor) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return FallbackZ;
	}

	FCollisionQueryParams Params(SCENE_QUERY_STAT(IBGuideGround), false, IgnoreActor);
	FHitResult Hit;
	const FVector TraceStart = Pos + FVector(0.0f, 0.0f, 150.0f);
	const FVector TraceEnd = Pos - FVector(0.0f, 0.0f, 300.0f);
	if (World->LineTraceSingleByObjectType(Hit, TraceStart, TraceEnd, FCollisionObjectQueryParams(ECC_WorldStatic), Params))
	{
		return Hit.ImpactPoint.Z;
	}
	return FallbackZ;
}

void AIBGuideRoute::SetActorWalkVelocity(AActor* Actor, const FVector& Velocity) const
{
	// The ABP reads speed through Get Velocity; plain actors only report what we set here.
	if (Actor && Actor->GetRootComponent())
	{
		Actor->GetRootComponent()->ComponentVelocity = Velocity;
	}
}

void AIBGuideRoute::HoldActor(AActor* Actor) const
{
	SetActorWalkVelocity(Actor, FVector::ZeroVector);
}

void AIBGuideRoute::FaceDirection(AActor* Actor, const FVector& Direction, float DeltaSeconds) const
{
	if (!Actor || Direction.IsNearlyZero())
	{
		return;
	}
	const float DesiredYaw = Direction.Rotation().Yaw + FacingYawOffset;
	const float CurrentYaw = Actor->GetActorRotation().Yaw;
	const float NewYaw = FMath::FixedTurn(CurrentYaw, DesiredYaw, TurnRateDegPerSec * DeltaSeconds);
	Actor->SetActorRotation(FRotator(0.0f, NewYaw, 0.0f));
}

// ----------------------------------------------------------------------------
// Subtitles / voice for call-outs and arrival lines
// ----------------------------------------------------------------------------

void AIBGuideRoute::ShowLine(const FDialogueLine& Line, const TCHAR* VoiceTag, int32 VoiceIndex)
{
	const float VoDuration = IBDialogueVoice::PlayLine(this, Line, VoiceTag, VoiceIndex);
	DisplayedLine = Line;
	bLineShowing = true;

	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	LineEndTime = Now + FMath::Max(Line.HoldDuration, VoDuration);

	UE_LOG(LogIronBreach, Log, TEXT("[GuideRoute] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(), *Line.Text.ToString());
}

void AIBGuideRoute::UpdateDisplayedLine()
{
	if (bLineShowing && GetWorld() && GetWorld()->GetTimeSeconds() >= LineEndTime)
	{
		bLineShowing = false;
	}
}

bool AIBGuideRoute::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (bLineShowing)
	{
		OutLine = DisplayedLine;
		return true;
	}
	return false;
}
