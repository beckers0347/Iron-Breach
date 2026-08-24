// Act2EscalationDirector.cpp

#include "Act2EscalationDirector.h"
#include "Act1BarracksDirector.h"
#include "IronBreach.h"
#include "TimerManager.h"
#include "Engine/World.h"

AAct2EscalationDirector::AAct2EscalationDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AAct2EscalationDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- The civilian district. Evacuation already underway when the squad arrives. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("CIVILIAN DISTRICT -- EVACUATION IN PROGRESS")),
		3.0f, 1.0f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Civilians in coats thrown over pajamas are ushered onto buses. Routine, for now.")),
		4.0f, 0.8f,
		FName("BusesLoading")));

	// --- Escalation is environmental, not explosive. Nature reacts first. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("The harbor gulls are gone. All of them. Nobody noticed them leave.")),
		4.0f, 0.8f,
		FName("GullsVanish")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("A K9 shepherd flattens itself against a wall and will not move. Its handler can't coax it forward.")),
		4.5f, 0.8f,
		FName("K9Refusal")));

	// --- The glow-veins. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Gold-green filaments crawl up through the seams of the asphalt. Block by block, they brighten.")),
		4.5f, 0.6f,
		FName("GlowVeinsAppear")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("A young evacuee breaks from the line, reaching for one -- mistaking it for a flower.")),
		4.0f, 0.3f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("A parent yanks her back before she touches it.")),
		3.0f, 0.8f,
		FName("ChildTouchesVein")));

	// --- The Swell. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("The street begins to lift. Not an explosion -- a swell. Like the earth is inhaling.")),
		4.5f, 0.4f,
		FName("TheSwellBegins")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("(The sirens change tone.)")),
		2.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Contact is directly beneath us. All units, move -- NOW.")),
		3.5f, 0.5f,
		FName("ContactBeneath")));

	// This final beat's ScriptedEventTag ("ContactBeneath") is also treated as the
	// hard cut into Act III -- see PlayLineAtIndex/FinishAct2.
}

void AAct2EscalationDirector::BeginPlay()
{
	Super::BeginPlay();

	if (AAct1BarracksDirector* Previous = PreviousActDirector.LoadSynchronous())
	{
		Previous->OnAct1Complete.AddDynamic(this, &AAct2EscalationDirector::OnPreviousActComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AAct2EscalationDirector::StartAct2, InitialDelay, false);
	}
}

void AAct2EscalationDirector::OnPreviousActComplete()
{
	StartAct2();
}

void AAct2EscalationDirector::StartAct2()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AAct2EscalationDirector::SkipToEruption()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("TheSwellBegins"));
	HandleScriptedEvent(FName("ContactBeneath"));
	FinishAct2();
}

void AAct2EscalationDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishAct2();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AAct2EscalationDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[Act II] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	// "ContactBeneath" is the hard cut into Act III -- end the act the moment this
	// line's hold finishes, same as every other line, but the FinishAct2() that
	// follows is really the beat everything upstream has been building to.
	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AAct2EscalationDirector::AdvanceToNextLine, TotalDelay, false);
}

void AAct2EscalationDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AAct2EscalationDirector::FinishAct2()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[Act II] Complete -- contact beneath them, cutting to Act III."));
	OnAct2Complete.Broadcast();
}

bool AAct2EscalationDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
