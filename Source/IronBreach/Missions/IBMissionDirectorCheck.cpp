// Opt-in dev check for the mission director's kaiju bookkeeping (MP_HARDENING_2026-09-15.md §3).
//   Console:  IB.MissionDirectorCheck        (any authority game world: PIE, -game, listen host)
//   Or:       -ExecCmds="IB.MissionDirectorCheck"
// Spawns two bare kaiju, kills one through the damage interface, destroys the other without
// killing it, then lets the corpse time out — and asserts the director counts each beast exactly
// once, reaches ZONE SECURED, and can be found through the subsystem. Leaves two loot pickups
// behind (the kill pays like any kill). ~12 seconds. Log lines start with [MissionDirectorCheck].
#include "CoreMinimal.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "Missions/IBMissionDirector.h"
#include "Missions/IBMissionSubsystem.h"
#include "Kaiju/IBCharacter_Kaiju.h"
#include "Combat/DamageableInterface.h"
#include "Containers/Ticker.h"
#include "Engine/HitResult.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"

namespace IBMissionDirectorCheck
{
	struct FState
	{
		TWeakObjectPtr<UWorld> World;
		TWeakObjectPtr<AIBMissionDirector> Director;
		TWeakObjectPtr<AIBCharacter_Kaiju> KaijuA; // dies
		TWeakObjectPtr<AIBCharacter_Kaiju> KaijuB; // removed without dying
		bool bSpawnedDirector = false;
		int32 LiveBefore = 0;
		int32 Phase = 0;
		double PhaseStarted = 0.0;
		int32 Failures = 0;
	};

	static void Check(FState& S, bool bCondition, const FString& What)
	{
		if (bCondition)
		{
			UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] PASS %s"), *What);
		}
		else
		{
			++S.Failures;
			UE_LOG(LogIronBreach, Error, TEXT("[MissionDirectorCheck] FAIL %s"), *What);
		}
	}

	static AIBCharacter_Kaiju* SpawnBareKaiju(UWorld* World, const FVector& At, const TCHAR* Tag)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Params.ObjectFlags |= RF_Transient;
		AIBCharacter_Kaiju* Kaiju = World->SpawnActor<AIBCharacter_Kaiju>(AIBCharacter_Kaiju::StaticClass(), At, FRotator::ZeroRotator, Params);
		UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] spawned %s %s (no species: zero armour, no organs — first hit exposes, a big hit kills)"),
			Tag, *GetNameSafe(Kaiju));
		return Kaiju;
	}

	static FString PhaseName(const AIBMissionDirector* Director)
	{
		return Director ? UEnum::GetValueAsString(Director->GetMissionPhase()) : TEXT("<no director>");
	}

	static FAutoConsoleCommandWithWorld Command(TEXT("IB.MissionDirectorCheck"),
		TEXT("Spawn two kaiju, kill one, destroy one, time out the corpse; assert the mission director counts each once and reaches ZONE SECURED."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* InWorld)
		{
			if (!InWorld || !InWorld->IsGameWorld()) { return; }
			if (InWorld->GetNetMode() == NM_Client)
			{
				UE_LOG(LogIronBreach, Error, TEXT("[MissionDirectorCheck] FAIL run this on the authority (host / standalone / PIE server), not a client"));
				return;
			}

			TSharedRef<FState> State = MakeShared<FState>();
			State->World = InWorld;
			State->PhaseStarted = FPlatformTime::Seconds();

			FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([State](float) -> bool
			{
				FState& S = *State;
				UWorld* World = S.World.Get();
				if (!World)
				{
					UE_LOG(LogIronBreach, Error, TEXT("[MissionDirectorCheck] FAIL world went away"));
					return false;
				}
				const double Now = FPlatformTime::Seconds();
				const double InPhase = Now - S.PhaseStarted;
				auto Advance = [&S, Now]() { ++S.Phase; S.PhaseStarted = Now; };

				switch (S.Phase)
				{
				case 0: // find or spawn the director, spawn two beasts
				{
					UIBMissionSubsystem* Missions = World->GetSubsystem<UIBMissionSubsystem>();
					AIBMissionDirector* Director = Missions ? Missions->GetDirector() : nullptr;
					if (!Director)
					{
						FActorSpawnParameters Params;
						Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
						Params.ObjectFlags |= RF_Transient;
						Director = World->SpawnActor<AIBMissionDirector>(AIBMissionDirector::StaticClass(), FTransform::Identity, Params);
						S.bSpawnedDirector = true;
						UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] no director in %s — spawned one for the check"), *World->GetMapName());
						// The lazy lookup is the point: the subsystem never saw this spawn.
						Check(S, Missions && Missions->GetDirector() == Director, TEXT("subsystem GetDirector() finds a director it did not spawn (the client path)"));
					}
					if (!Director)
					{
						Check(S, false, TEXT("director available"));
						UE_LOG(LogIronBreach, Error, TEXT("[MissionDirectorCheck] COMPLETE with %d failure(s)"), S.Failures);
						return false;
					}
					S.Director = Director;
					S.LiveBefore = Director->GetLiveKaijuCount();
					UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] director %s phase=%s live=%d before"),
						*Director->GetName(), *PhaseName(Director), S.LiveBefore);

					FVector At = FVector(0.f, 0.f, 300.f);
					if (const APlayerController* PC = World->GetFirstPlayerController())
					{
						if (const APawn* Pawn = PC->GetPawn()) { At = Pawn->GetActorLocation() + Pawn->GetActorForwardVector() * 3000.f + FVector(0.f, 0.f, 300.f); }
					}
					S.KaijuA = SpawnBareKaiju(World, At, TEXT("A"));
					S.KaijuB = SpawnBareKaiju(World, At + FVector(0.f, 1500.f, 0.f), TEXT("B"));
					Check(S, S.KaijuA.IsValid() && S.KaijuB.IsValid(), TEXT("two kaiju spawned"));
					Advance();
					return true;
				}
				case 1: // both tracked, first contact fired
				{
					if (InPhase < 0.5) { return true; }
					AIBMissionDirector* Director = S.Director.Get();
					const int32 Live = Director ? Director->GetLiveKaijuCount() : -1;
					Check(S, Live == S.LiveBefore + 2, FString::Printf(TEXT("director tracks both (live=%d, expected %d)"), Live, S.LiveBefore + 2));
					const EIBMissionPhase Phase = Director ? Director->GetMissionPhase() : EIBMissionPhase::Standby;
					Check(S, Phase == EIBMissionPhase::Emergence || Phase == EIBMissionPhase::Engaged,
						FString::Printf(TEXT("first contact moved the phase to Emergence/Engaged (is %s)"), *PhaseName(Director)));
					// Kill A through the project damage seam (the same path the guns use).
					if (AIBCharacter_Kaiju* A = S.KaijuA.Get())
					{
						FHitResult Hit;
						Hit.ImpactPoint = A->GetActorLocation();
						Hit.TraceStart = Hit.ImpactPoint + FVector(-1000.f, 0.f, 0.f);
						IDamageableInterface::Execute_HandleTakeDamage(A, 1.0e9f, Hit, nullptr, nullptr);
						if (A->GetFightPhase() != EKaijuFightPhase::Dead)
						{
							// The first hit on a zero-armour beast only exposes it; the second one is lethal.
							IDamageableInterface::Execute_HandleTakeDamage(A, 1.0e9f, Hit, nullptr, nullptr);
						}
					}
					Advance();
					return true;
				}
				case 2: // A is dead and released exactly once
				{
					if (InPhase < 0.5) { return true; }
					AIBMissionDirector* Director = S.Director.Get();
					AIBCharacter_Kaiju* A = S.KaijuA.Get();
					Check(S, A && A->GetFightPhase() == EKaijuFightPhase::Dead, TEXT("kaiju A reports Dead after the lethal hit"));
					const int32 Live = Director ? Director->GetLiveKaijuCount() : -1;
					Check(S, Live == S.LiveBefore + 1, FString::Printf(TEXT("death released A (live=%d, expected %d)"), Live, S.LiveBefore + 1));
					if (A) { A->SetLifeSpan(1.0f); } // hurry the corpse along so the double-count check runs inside the ticker budget
					// B leaves the world WITHOUT dying (spawner reset / level script / dev command shape).
					if (AIBCharacter_Kaiju* B = S.KaijuB.Get()) { B->Destroy(); }
					Advance();
					return true;
				}
				case 3: // B released by destruction; ZONE SECURED if nothing else was alive
				{
					if (InPhase < 0.5) { return true; }
					AIBMissionDirector* Director = S.Director.Get();
					const int32 Live = Director ? Director->GetLiveKaijuCount() : -1;
					Check(S, Live == S.LiveBefore, FString::Printf(TEXT("destruction without death released B (live=%d, expected %d)"), Live, S.LiveBefore));
					if (S.LiveBefore == 0)
					{
						Check(S, Director && Director->GetMissionPhase() == EIBMissionPhase::Secured,
							FString::Printf(TEXT("ZONE SECURED once the last beast is gone (is %s)"), *PhaseName(Director)));
					}
					else
					{
						UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] %d other kaiju were alive before the check — SECURED not expected"), S.LiveBefore);
					}
					Advance();
					return true;
				}
				case 4: // A's corpse times out: OnDestroyed fires for an already-released kaiju -> no double count
				{
					if (S.KaijuA.IsValid() && InPhase < 6.0) { return true; } // wait for the lifespan to expire
					AIBMissionDirector* Director = S.Director.Get();
					const int32 Live = Director ? Director->GetLiveKaijuCount() : -1;
					Check(S, !S.KaijuA.IsValid(), TEXT("A's corpse was destroyed by its lifespan"));
					Check(S, Live == S.LiveBefore, FString::Printf(TEXT("corpse removal did not double-count (live=%d, expected %d)"), Live, S.LiveBefore));
					if (S.LiveBefore == 0)
					{
						Check(S, Director && Director->GetMissionPhase() == EIBMissionPhase::Secured,
							FString::Printf(TEXT("still SECURED after the corpse went (is %s)"), *PhaseName(Director)));
					}
					if (S.bSpawnedDirector && Director)
					{
						Director->Destroy();
						UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] removed the director this check spawned"));
					}
					if (S.Failures) { UE_LOG(LogIronBreach, Error, TEXT("[MissionDirectorCheck] COMPLETE with %d failure(s)"), S.Failures); }
					else            { UE_LOG(LogIronBreach, Display, TEXT("[MissionDirectorCheck] COMPLETE — all checks passed")); }
					return false;
				}
				default:
					return false;
				}
			}), 0.25f);
		}));
}
#endif
