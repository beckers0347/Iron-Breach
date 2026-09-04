// M2ContactDirector.cpp

#include "M2ContactDirector.h"
#include "M2DebrisFieldDirector.h"
#include "IronBreach.h"
#include "../M1Landfall/IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

const FName AM2ContactDirector::DeescalationBeginsTag(TEXT("DeescalationBegins"));

AM2ContactDirector::AM2ContactDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AM2ContactDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- Vance. Same sensitivity law as Ms. Idris in M1: no lingering gore, no slow-mo. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("In the cockpit: Cpl. Vance. It's quick to see, and quick to look away from.")),
		4.0f, 0.6f,
		FName("VanceFound")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Copy. Vance is KIA. Logging it. Keep moving -- we're not done here.")),
		4.0f, 0.8f));

	// --- Achterberg. Armed, cornered, not a villain -- a week alone with this. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("A voice, rough with disuse, from behind a collapsed strut: \"Don't come any closer.\"")),
		4.5f, 0.5f,
		FName("AchterbergRevealed")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Achterberg. Alive. A weapon levelled, hands not quite steady, eyes on all of them at once.)")),
		4.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("You're not the first people who've come up this hill looking to pick us clean. I don't care about your uniforms.")),
		5.0f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Sergeant Achterberg. Nobody here is a scavenger. We came for you and for Vance. Nothing else.")),
		4.5f, 0.5f,
		DeescalationBeginsTag));

	// --- Everything below plays AFTER ResumeAfterDeescalation() is called. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(A long moment. Achterberg doesn't relax, exactly -- she just stops pointing the weapon at people who turned out to be looking for her.)")),
		5.0f, 0.6f,
		FName("AchterbergStandsDown")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Achterberg,
		FText::FromString(TEXT("Nobody's flying that out of here. Not like this. But I'm not leaving him, and I'm not leaving her either.")),
		5.0f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Then walk us through it. We'll get all three of you home.")),
		4.0f, 1.0f,
		FName("AchterbergAgrees")));
}

void AM2ContactDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[M2 Contact] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AM2DebrisFieldDirector* Previous = PreviousBeatDirector.LoadSynchronous())
	{
		Previous->OnM2DebrisFieldComplete.AddDynamic(this, &AM2ContactDirector::OnPreviousBeatComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AM2ContactDirector::StartContact, InitialDelay, false);
	}
}

void AM2ContactDirector::OnPreviousBeatComplete()
{
	StartContact();
}

void AM2ContactDirector::StartContact()
{
	bHasCompleted = false;
	bWaitingForDeescalation = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AM2ContactDirector::SkipToDeescalation()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("VanceFound"));
	HandleScriptedEvent(FName("AchterbergRevealed"));
	HandleScriptedEvent(DeescalationBeginsTag);
	bWaitingForDeescalation = true;
}

void AM2ContactDirector::SkipToResolved()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);
	bWaitingForDeescalation = false;

	HandleScriptedEvent(FName("AchterbergStandsDown"));
	HandleScriptedEvent(FName("AchterbergAgrees"));
	FinishContact();
}

void AM2ContactDirector::ResumeAfterDeescalation()
{
	if (!bWaitingForDeescalation)
	{
		return;
	}

	bWaitingForDeescalation = false;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 Contact] De-escalation resolved -- resuming into Achterberg's agreement."));
	AdvanceToNextLine();
}

void AM2ContactDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishContact();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AM2ContactDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[M2 Contact] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	// The de-escalation hand-off line pauses the timeline instead of auto-advancing --
	// see class comment.
	if (Line.ScriptedEventTag == DeescalationBeginsTag)
	{
		bWaitingForDeescalation = true;
		UE_LOG(LogIronBreach, Log, TEXT("[M2 Contact] Reached de-escalation hand-off -- pausing until ResumeAfterDeescalation() is called."));
		return;
	}

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AM2ContactDirector::AdvanceToNextLine, TotalDelay, false);
}

void AM2ContactDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AM2ContactDirector::FinishContact()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 Contact] Complete -- Achterberg on side, cutting to First Seat."));
	OnM2ContactComplete.Broadcast();
}

bool AM2ContactDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
