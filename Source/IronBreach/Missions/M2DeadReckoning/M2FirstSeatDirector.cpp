// M2FirstSeatDirector.cpp

#include "M2FirstSeatDirector.h"
#include "M2ContactDirector.h"
#include "IronBreach.h"
#include "../M1Landfall/IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

const FName AM2FirstSeatDirector::WalkoutBeginsTag(TEXT("WalkoutBegins"));

AM2FirstSeatDirector::AM2FirstSeatDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AM2FirstSeatDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- The seat. Nobody comments on whose it was. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("Second seat's empty. It won't fly like this, but it can walk, if someone runs the board while I fly it.")),
		4.5f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The player climbs into the gunnery/systems position. The seat still remembers someone else's shape.)")),
		4.5f, 0.6f,
		FName("PlayerSeated")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("Power-up sequence first. Watch the board, tell me what's red. We are not doing anything fast today.")),
		4.5f, 0.5f,
		FName("PowerUpBegins")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("Good. Now we walk. Forward's forward. You'll feel it before you see it work.")),
		4.5f, 0.6f,
		WalkoutBeginsTag));

	// --- Everything below plays AFTER ResumeAfterWalkout() is called. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The mech clears the treeline, walking rough but upright, as the transport comes in low over the clearing.)")),
		4.5f, 0.6f,
		FName("ClearingReached")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Good work. All of you. Let's get everyone home.")),
		4.0f, 0.8f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("You held the board. That's the job, from here on.")),
		3.5f, 1.0f,
		FName("MissionEnd")));
}

void AM2FirstSeatDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[M2 First Seat] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AM2ContactDirector* Previous = PreviousBeatDirector.LoadSynchronous())
	{
		Previous->OnM2ContactComplete.AddDynamic(this, &AM2FirstSeatDirector::OnPreviousBeatComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AM2FirstSeatDirector::StartFirstSeat, InitialDelay, false);
	}
}

void AM2FirstSeatDirector::OnPreviousBeatComplete()
{
	StartFirstSeat();
}

void AM2FirstSeatDirector::StartFirstSeat()
{
	bHasCompleted = false;
	bWaitingForWalkout = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AM2FirstSeatDirector::SkipToWalkout()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("PlayerSeated"));
	HandleScriptedEvent(FName("PowerUpBegins"));
	HandleScriptedEvent(WalkoutBeginsTag);
	bWaitingForWalkout = true;
}

void AM2FirstSeatDirector::SkipToEnding()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);
	bWaitingForWalkout = false;

	HandleScriptedEvent(FName("ClearingReached"));
	HandleScriptedEvent(FName("MissionEnd"));
	FinishM2();
}

void AM2FirstSeatDirector::ResumeAfterWalkout()
{
	if (!bWaitingForWalkout)
	{
		return;
	}

	bWaitingForWalkout = false;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 First Seat] Walkout complete -- resuming into the mission's closing beat."));
	AdvanceToNextLine();
}

void AM2FirstSeatDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishM2();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AM2FirstSeatDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[M2 First Seat] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	// The walk-out hand-off line pauses the timeline instead of auto-advancing -- see
	// class comment.
	if (Line.ScriptedEventTag == WalkoutBeginsTag)
	{
		bWaitingForWalkout = true;
		UE_LOG(LogIronBreach, Log, TEXT("[M2 First Seat] Reached walk-out hand-off -- pausing until ResumeAfterWalkout() is called."));
		return;
	}

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AM2FirstSeatDirector::AdvanceToNextLine, TotalDelay, false);
}

void AM2FirstSeatDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AM2FirstSeatDirector::FinishM2()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 First Seat] Complete -- M2 'Dead Reckoning' finished."));
	OnM2Complete.Broadcast();
}

bool AM2FirstSeatDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
