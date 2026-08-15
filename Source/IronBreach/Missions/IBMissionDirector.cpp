#include "Missions/IBMissionDirector.h"
#include "IronBreach.h"
#include "Kaiju/IBCharacter_Kaiju.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Net/UnrealNetwork.h"

AIBMissionDirector::AIBMissionDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	bAlwaysRelevant = true; // mission state reaches every player, every distance
	NetUpdateFrequency = 5.0f; // phase changes are rare; keep it cheap
}

void AIBMissionDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBMissionDirector, MissionPhase);
}

void AIBMissionDirector::BeginPlay()
{
	Super::BeginPlay();

	if (!HasAuthority()) { return; }

	// Sweep begins the moment boots hit the ground.
	SetMissionPhase(EIBMissionPhase::Patrol);

	// Kaiju already in the world (hand-placed) ...
	for (TActorIterator<AIBCharacter_Kaiju> It(GetWorld()); It; ++It)
	{
		TrackKaiju(*It);
	}
	// ... and kaiju yet to come (Shane's spawner).
	ActorSpawnedHandle = GetWorld()->AddOnActorSpawnedHandler(
		FOnActorSpawned::FDelegate::CreateUObject(this, &AIBMissionDirector::OnWorldActorSpawned));
}

void AIBMissionDirector::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(ActorSpawnedHandle);
	}
	Super::EndPlay(EndPlayReason);
}

void AIBMissionDirector::OnWorldActorSpawned(AActor* Actor)
{
	if (AIBCharacter_Kaiju* Kaiju = Cast<AIBCharacter_Kaiju>(Actor))
	{
		TrackKaiju(Kaiju);
	}
}

void AIBMissionDirector::TrackKaiju(AIBCharacter_Kaiju* Kaiju)
{
	if (!Kaiju) { return; }

	++LiveKaiju;
	Kaiju->OnPhaseChanged.AddDynamic(this, &AIBMissionDirector::HandleKaijuFightPhase);

	UE_LOG(LogIronBreach, Log, TEXT("[Mission] Tracking kaiju %s (%d live)"), *Kaiju->GetName(), LiveKaiju);

	// First contact: the emergence beat, then kill orders.
	if (MissionPhase == EIBMissionPhase::Patrol || MissionPhase == EIBMissionPhase::Standby)
	{
		SetMissionPhase(EIBMissionPhase::Emergence);
		GetWorldTimerManager().SetTimer(EmergenceTimer, [this]()
		{
			if (MissionPhase == EIBMissionPhase::Emergence)
			{
				SetMissionPhase(EIBMissionPhase::Engaged);
			}
		}, FMath::Max(EmergenceDuration, 0.1f), false);
	}
	else if (MissionPhase == EIBMissionPhase::Secured)
	{
		// A new wave after victory reopens the fight.
		SetMissionPhase(EIBMissionPhase::Engaged);
	}
}

void AIBMissionDirector::HandleKaijuFightPhase(EKaijuFightPhase NewPhase)
{
	if (!HasAuthority() || NewPhase != EKaijuFightPhase::Dead) { return; }

	LiveKaiju = FMath::Max(LiveKaiju - 1, 0);
	UE_LOG(LogIronBreach, Log, TEXT("[Mission] Kaiju down (%d remain)"), LiveKaiju);

	if (LiveKaiju == 0 &&
		(MissionPhase == EIBMissionPhase::Engaged || MissionPhase == EIBMissionPhase::Emergence))
	{
		GetWorldTimerManager().ClearTimer(EmergenceTimer);
		SetMissionPhase(EIBMissionPhase::Secured);
	}
}

void AIBMissionDirector::SetMissionPhase(EIBMissionPhase NewPhase)
{
	if (!HasAuthority() || MissionPhase == NewPhase) { return; }

	MissionPhase = NewPhase;
	UE_LOG(LogIronBreach, Log, TEXT("[Mission] Phase -> %s"), *UEnum::GetValueAsString(NewPhase));

	// Server/listen-host hears it now; clients via OnRep.
	OnMissionPhaseChanged.Broadcast(MissionPhase);
	BP_OnMissionPhaseChanged(MissionPhase);
}

void AIBMissionDirector::OnRep_MissionPhase()
{
	OnMissionPhaseChanged.Broadcast(MissionPhase);
	BP_OnMissionPhaseChanged(MissionPhase);
}

FText AIBMissionDirector::GetObjectiveText() const
{
	switch (MissionPhase)
	{
	case EIBMissionPhase::Patrol:
		return NSLOCTEXT("IBMission", "Patrol", "SWEEP THE ZONE — HOSTILES ACTIVE");
	case EIBMissionPhase::Emergence:
		return NSLOCTEXT("IBMission", "Emergence", "!! KAIJU EMERGENCE DETECTED !!");
	case EIBMissionPhase::Engaged:
		return NSLOCTEXT("IBMission", "Engaged", "ELIMINATE THE KAIJU — THE CARYATID IS CLEARED FOR BOARDING");
	case EIBMissionPhase::Secured:
		return NSLOCTEXT("IBMission", "Secured", "ZONE SECURED — OUTSTANDING WORK, PILOT");
	default:
		return FText::GetEmpty();
	}
}
