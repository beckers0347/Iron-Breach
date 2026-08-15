#include "Missions/IBMissionSubsystem.h"
#include "IronBreach.h"
#include "Missions/IBMissionDirector.h"
#include "Kaiju/IBCharacter_Kaiju.h"
#include "Kaiju/IBKaijuSpawner.h"
#include "EngineUtils.h"
#include "Engine/World.h"

void UIBMissionSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);

	// A hand-placed director always wins.
	for (TActorIterator<AIBMissionDirector> It(&InWorld); It; ++It)
	{
		Director = *It;
		return;
	}

	// Server decides; clients meet the replicated director when it arrives.
	if (InWorld.GetNetMode() == NM_Client) { return; }

	bool bHasKaijuContent = TActorIterator<AIBCharacter_Kaiju>(&InWorld) ? true : false;
	if (!bHasKaijuContent)
	{
		bHasKaijuContent = TActorIterator<AIBKaijuSpawner>(&InWorld) ? true : false;
	}
	if (!bHasKaijuContent) { return; } // menu/title worlds: no mission, no banner

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Director = InWorld.SpawnActor<AIBMissionDirector>(AIBMissionDirector::StaticClass(),
		FTransform::Identity, Params);

	UE_LOG(LogIronBreach, Log, TEXT("[Mission] Auto-spawned director for %s"), *InWorld.GetName());
}
