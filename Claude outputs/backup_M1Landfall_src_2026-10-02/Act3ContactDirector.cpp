// Act3ContactDirector.cpp

#include "Act3ContactDirector.h"
#include "Act2EscalationDirector.h"
#include "IronBreach.h"
#include "IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

AAct3ContactDirector::AAct3ContactDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AAct3ContactDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- Contact. Class D surfaces near the perimeter. Winnable, and meant to feel that way. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("GARRISON PERIMETER -- CONTACT")),
		3.0f, 0.6f,
		FName("ClassDContact")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Contact, perimeter line. Small profile, multiple. Hold and put them down.")),
		4.0f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("(The garrison's one mech powers up behind the line.)")),
		2.5f, 0.4f,
		FName("MechDeploys")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("That's Vance and Achterberg. Ugly and dependable, just how we like it.")),
		4.0f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Squad and mech work the line together. Route-clearing shots -- cable-stays, a demo charge, a vented gas line -- open the path as much as they clear it.)")),
		4.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("That's the last of them. Good work -- reform on the convoy.")),
		4.0f, 0.6f,
		FName("ClassDClear")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(For a few seconds, this sounds like a win.)")),
		3.0f, 1.0f));

	// --- Then the ground swells again. Bigger this time. Hard cut into Act IV. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("The street lifts again -- further this time. Not a tremor. A birth.")),
		4.0f, 1.0f));
}

void AAct3ContactDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Act III] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AAct2EscalationDirector* Previous = PreviousActDirector.LoadSynchronous())
	{
		Previous->OnAct2Complete.AddDynamic(this, &AAct3ContactDirector::OnPreviousActComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AAct3ContactDirector::StartAct3, InitialDelay, false);
	}
}

void AAct3ContactDirector::OnPreviousActComplete()
{
	StartAct3();
}

void AAct3ContactDirector::StartAct3()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AAct3ContactDirector::SkipToAllClear()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("ClassDContact"));
	HandleScriptedEvent(FName("ClassDClear"));
	FinishAct3();
}

void AAct3ContactDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishAct3();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AAct3ContactDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[Act III] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AAct3ContactDirector::AdvanceToNextLine, TotalDelay, false);
}

void AAct3ContactDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AAct3ContactDirector::FinishAct3()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[Act III] Complete -- Class D repelled, cutting to Act IV."));
	OnAct3Complete.Broadcast();
}

bool AAct3ContactDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
