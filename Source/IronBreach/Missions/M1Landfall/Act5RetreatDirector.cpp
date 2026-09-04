// Act5RetreatDirector.cpp

#include "Act5RetreatDirector.h"
#include "Act4DeepWaterDirector.h"
#include "IronBreach.h"
#include "IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

const FName AAct5RetreatDirector::CarryBeginsTag(TEXT("CarryBegins"));

AAct5RetreatDirector::AAct5RetreatDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AAct5RetreatDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- The toss. The mission's second-biggest spectacle beat after the eruption. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Covering the withdrawal, the mech takes one hit too many.")),
		3.5f, 0.3f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("PALAWAN takes hold of it and throws it clear off the battlefield -- up, out, into the high ground past the district.")),
		5.0f, 0.6f,
		FName("MechToss")));

	// Current assumption per v2 mission doc §13 Q7: this is where Vance is lost. Flagged,
	// not locked -- confirm before treating this line as canon.
	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Vance: -checklist cuts off mid-word. Nothing after it.")),
		3.5f, 0.5f,
		FName("VanceDown")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Achterberg: I have control. I have control -- I don't have Vance. Say again, I don't have Vance.")),
		4.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Copy, Achterberg. Get her down, get yourself down. We'll find you after. Squad -- sweep the collapsed row for stragglers.")),
		5.0f, 1.0f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The team splits to search the ruined block. In a caved-in stairwell, alive and alone: Ms. Idris.)")),
		4.5f, 1.0f));

	// --- Hand-off to the interactive carry. The timeline PAUSES here -- see class comment. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Idris,
		FText::FromString(TEXT("There you are. Alright -- alright, love, help me up, we'll walk it.")),
		4.0f, 0.5f,
		CarryBeginsTag));

	// --- Everything below plays AFTER ResumeAfterCarry() is called. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("(At the hospital muster, the squad takes her weight onto a stretcher. Paperwork, procedural.)")),
		4.0f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Who brought her in?")),
		2.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("The one who carries people across. Ferryman.")),
		3.5f, 0.6f,
		FName("NamingScene")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("Ferryman.")),
		2.0f, 1.0f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("(Two blocks short of the hospital, PALAWAN -- having taken the mech and everything else thrown at it -- slows, folds down onto itself, and calcifies. It won. It stopped anyway.)")),
		5.5f, 0.6f,
		FName("PalawanCalcifies")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Contact is static, say again, static.")),
		3.0f, 1.0f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Walking back along the sea-wall at first light: a Caryatid kneels in the shallows, crew hand-painting a fresh ring onto its greave.)")),
		5.0f, 0.6f,
		FName("SeaWallGlimpse")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("Rings are people carried out. Nobody paints kills.")),
		4.0f, 1.2f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("IRON BREACH")),
		3.0f, 0.5f,
		FName("MissionEnd")));
}

void AAct5RetreatDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Act V] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AAct4DeepWaterDirector* Previous = PreviousActDirector.LoadSynchronous())
	{
		Previous->OnAct4Complete.AddDynamic(this, &AAct5RetreatDirector::OnPreviousActComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AAct5RetreatDirector::StartAct5, InitialDelay, false);
	}
}

void AAct5RetreatDirector::OnPreviousActComplete()
{
	StartAct5();
}

void AAct5RetreatDirector::StartAct5()
{
	bHasCompleted = false;
	bWaitingForCarry = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AAct5RetreatDirector::SkipToCarry()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("MechToss"));
	HandleScriptedEvent(FName("VanceDown"));
	HandleScriptedEvent(CarryBeginsTag);
	bWaitingForCarry = true;
}

void AAct5RetreatDirector::SkipToEnding()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);
	bWaitingForCarry = false;

	HandleScriptedEvent(FName("NamingScene"));
	HandleScriptedEvent(FName("PalawanCalcifies"));
	HandleScriptedEvent(FName("SeaWallGlimpse"));
	HandleScriptedEvent(FName("MissionEnd"));
	FinishAct5();
}

void AAct5RetreatDirector::ResumeAfterCarry()
{
	if (!bWaitingForCarry)
	{
		return;
	}

	bWaitingForCarry = false;
	UE_LOG(LogIronBreach, Log, TEXT("[Act V] Carry complete -- resuming into the naming/ending beats."));
	AdvanceToNextLine();
}

void AAct5RetreatDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishAct5();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AAct5RetreatDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[Act V] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	// The carry hand-off line pauses the timeline instead of auto-advancing -- see class
	// comment. Everything else behaves exactly like Acts I-IV.
	if (Line.ScriptedEventTag == CarryBeginsTag)
	{
		bWaitingForCarry = true;
		UE_LOG(LogIronBreach, Log, TEXT("[Act V] Reached carry hand-off -- pausing until ResumeAfterCarry() is called."));
		return;
	}

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AAct5RetreatDirector::AdvanceToNextLine, TotalDelay, false);
}

void AAct5RetreatDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AAct5RetreatDirector::FinishAct5()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[Act V] Complete -- M1 'Landfall' finished."));
	OnAct5Complete.Broadcast();
}

bool AAct5RetreatDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
