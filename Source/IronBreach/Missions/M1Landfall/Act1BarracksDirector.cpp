// Act1BarracksDirector.cpp

#include "Act1BarracksDirector.h"
#include "IronBreach.h"
#include "TimerManager.h"
#include "Engine/World.h"

AAct1BarracksDirector::AAct1BarracksDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AAct1BarracksDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- 04:12, Carrowgate garrison watch room. Mundane, day-job atmosphere. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("04:12 LOCAL -- CARROWGATE GARRISON, WATCH ROOM")),
		3.0f, 1.0f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("...and that's the thing, right, the Green Tomb hum isn't NEW, it's just the first time anyone pointed a mic at it long enough--")),
		4.5f, 0.4f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("Same frequency in the grid noise. Same frequency near the anomaly. That's not a coincidence, that's a SIGNATURE.")),
		4.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Nobody in the room is listening. This is the first time anyone in the unit has been right about the Nine.)")),
		3.5f, 1.0f));

	// --- Stand-To: Rhodes enters, sensor post lights up. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Lt. Rhodes enters the watch room.")),
		2.0f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Sensor post: micro-seismic cluster, inshore. Depth climbing.")),
		3.5f, 0.5f,
		FName("SeismicContact")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("That's a birthquake precursor. Get eyes on the district, now.")),
		3.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Platoon -- stand to. We're supporting evac. Move.")),
		3.5f, 1.0f,
		FName("StandToOrder")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Routine confidence. Nobody in this room knows yet how wrong that word -- \"supporting\" -- is about to feel.)")),
		4.0f, 1.0f));
}

void AAct1BarracksDirector::BeginPlay()
{
	Super::BeginPlay();

	if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AAct1BarracksDirector::StartAct1, InitialDelay, false);
	}
}

void AAct1BarracksDirector::StartAct1()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AAct1BarracksDirector::SkipToStandTo()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("SeismicContact"));
	HandleScriptedEvent(FName("StandToOrder"));
	FinishAct1();
}

void AAct1BarracksDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishAct1();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AAct1BarracksDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[Act I] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AAct1BarracksDirector::AdvanceToNextLine, TotalDelay, false);
}

void AAct1BarracksDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AAct1BarracksDirector::FinishAct1()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[Act I] Complete -- stand-to order given."));
	OnAct1Complete.Broadcast();
}

bool AAct1BarracksDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
