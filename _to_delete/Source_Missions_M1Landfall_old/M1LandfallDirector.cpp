#include "M1LandfallDirector.h"
#include "IronBreach.h"
#include "IBMusterPoint.h"
#include "IBCarryEndZone.h"
#include "IBPalawanActor.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

AM1LandfallDirector::AM1LandfallDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	bAlwaysRelevant = true; // beat/extraction-count state reaches every player, every distance
	NetUpdateFrequency = 5.0f; // beats and extraction counts change rarely
}

void AM1LandfallDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AM1LandfallDirector, CurrentBeat);
	DOREPLIFETIME(AM1LandfallDirector, ExtractionCount);
}

void AM1LandfallDirector::BeginPlay()
{
	Super::BeginPlay();

	if (!HasAuthority()) { return; }

	// Signals-only subscription (same convention as AIBMissionDirector's kaiju
	// tracking): find every muster point / carry-end zone the level placed and
	// bind to their events, rather than those actors reaching into this one.
	for (TActorIterator<AIBMusterPoint> It(GetWorld()); It; ++It)
	{
		It->OnCivilianMustered.AddDynamic(this, &AM1LandfallDirector::HandleCivilianMustered);
	}
	for (TActorIterator<AIBCarryEndZone> It(GetWorld()); It; ++It)
	{
		It->OnCarryEnded.AddDynamic(this, &AM1LandfallDirector::HandleCarryEnded);
	}

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] Director ready. Beat -> Quiet."));
}

void AM1LandfallDirector::HandleCivilianMustered(AActor* Civilian)
{
	if (!HasAuthority()) { return; }

	++ExtractionCount;
	OnExtractionCountChanged.Broadcast(ExtractionCount); // server/listen-host hears it now; clients via OnRep

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] Extraction count -> %d"), ExtractionCount);
}

void AM1LandfallDirector::HandleCarryEnded(AActor* CarriedActor, AIBCharacter_Infantry* Carrier)
{
	if (!HasAuthority()) { return; }

	// The naming beat (LOCKED §4.4): Bricks coins "Ferryman" over the stretcher.
	// Stays within Aftermath -- this doesn't advance CurrentBeat.
	OnNamingBeat.Broadcast(Carrier);
	BP_OnNamingBeat(Carrier);

	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] Naming beat -- %s carried her in."), *GetNameSafe(Carrier));
}

void AM1LandfallDirector::NotifyStandToCalled()
{
	if (!HasAuthority()) { return; }
	SetBeat(EIBLandfallBeat::Dread);
}

void AM1LandfallDirector::NotifyEruptionTriggered()
{
	if (!HasAuthority()) { return; }
	SetBeat(EIBLandfallBeat::Burst);

	if (PalawanActor)
	{
		PalawanActor->BeginLocomotion();
	}
}

void AM1LandfallDirector::NotifyLastBusCleared()
{
	if (!HasAuthority()) { return; }
	SetBeat(EIBLandfallBeat::Aftermath);
}

void AM1LandfallDirector::NotifyPalawanCalcify()
{
	if (!HasAuthority()) { return; }

	if (PalawanActor)
	{
		PalawanActor->BeginCalcify(); // no character comments on this, ever (LOCKED §4.4) -- BP_OnBeatChanged stays silent here on purpose
	}
}

void AM1LandfallDirector::NotifyMissionComplete()
{
	if (!HasAuthority()) { return; }
	SetBeat(EIBLandfallBeat::Complete);
}

void AM1LandfallDirector::SetBeat(EIBLandfallBeat NewBeat)
{
	if (CurrentBeat == NewBeat) { return; }

	CurrentBeat = NewBeat;
	UE_LOG(LogIronBreach, Log, TEXT("[Landfall] Beat -> %s"), *UEnum::GetValueAsString(NewBeat));

	OnBeatChanged.Broadcast(CurrentBeat);
	BP_OnBeatChanged(CurrentBeat);
}

void AM1LandfallDirector::OnRep_CurrentBeat()
{
	OnBeatChanged.Broadcast(CurrentBeat);
	BP_OnBeatChanged(CurrentBeat);
}

void AM1LandfallDirector::OnRep_ExtractionCount()
{
	OnExtractionCountChanged.Broadcast(ExtractionCount);
}

FText AM1LandfallDirector::GetObjectiveText() const
{
	// [PROPOSAL] copy -- radio-procedural per §7, final lines pending sign-off (§13).
	switch (CurrentBeat)
	{
	case EIBLandfallBeat::Quiet:
		return NSLOCTEXT("IBLandfall", "Quiet", "STAND THE WATCH");
	case EIBLandfallBeat::Dread:
		return NSLOCTEXT("IBLandfall", "Dread", "MARSHAL THE EVACUATION");
	case EIBLandfallBeat::Burst:
		return NSLOCTEXT("IBLandfall", "Burst", "RUN THE ROUTES");
	case EIBLandfallBeat::Aftermath:
		return NSLOCTEXT("IBLandfall", "Aftermath", "GET HER TO THE HOSPITAL");
	case EIBLandfallBeat::Complete:
	default:
		return FText::GetEmpty();
	}
}
