// M2DebrisFieldDirector.cpp

#include "M2DebrisFieldDirector.h"
#include "M2SearchDirector.h"
#include "IronBreach.h"
#include "../M1Landfall/IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

AM2DebrisFieldDirector::AM2DebrisFieldDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AM2DebrisFieldDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- Escalation ladder, environment-led per the design doc: unremarkable debris,
	// then identifiable armor plating, then personal effects, then the wreck itself. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Scattered wreckage starts appearing among the trees -- could be anything, at first.")),
		4.0f, 0.6f,
		FName("DebrisScattered")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("That's not anything. That's plating.")),
		3.0f, 0.5f,
		FName("ArmorPlatingFound")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(A single boot, half-buried. A comms headset, cord snapped. Nobody says anything.)")),
		4.5f, 0.8f,
		FName("PersonalEffectsFound")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("Beacon's close. Real close.")),
		2.5f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Around the last bend: the mech, slumped against the terrain where it finally stopped. Unmoving.)")),
		4.5f, 0.6f,
		FName("WreckSighted")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Hold up. Cautious approach -- we don't know who else has been here.")),
		4.0f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Something at the wreck line moves. Just once. Not the wind.)")),
		3.5f, 1.0f,
		FName("MovementSpotted")));
}

void AM2DebrisFieldDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[M2 Debris Field] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AM2SearchDirector* Previous = PreviousBeatDirector.LoadSynchronous())
	{
		Previous->OnM2SearchComplete.AddDynamic(this, &AM2DebrisFieldDirector::OnPreviousBeatComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AM2DebrisFieldDirector::StartDebrisField, InitialDelay, false);
	}
}

void AM2DebrisFieldDirector::OnPreviousBeatComplete()
{
	StartDebrisField();
}

void AM2DebrisFieldDirector::StartDebrisField()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AM2DebrisFieldDirector::SkipToWreckSighted()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("DebrisScattered"));
	HandleScriptedEvent(FName("WreckSighted"));
	HandleScriptedEvent(FName("MovementSpotted"));
	FinishDebrisField();
}

void AM2DebrisFieldDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishDebrisField();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AM2DebrisFieldDirector::PlayLineAtIndex(int32 Index)
{
	if (!Beats.IsValidIndex(Index))
	{
		return;
	}

	const FDialogueLine& Line = Beats[Index];

	if (Line.ScriptedEventTag != NAME_None)
	{
		HandleScriptedEvent(Line.ScriptedEventTag);
	}

	UE_LOG(LogIronBreach, Log, TEXT("[M2 Debris Field] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AM2DebrisFieldDirector::AdvanceToNextLine, TotalDelay, false);
}

void AM2DebrisFieldDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AM2DebrisFieldDirector::FinishDebrisField()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 Debris Field] Complete -- wreck sighted, cutting to Contact."));
	OnM2DebrisFieldComplete.Broadcast();
}

bool AM2DebrisFieldDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
