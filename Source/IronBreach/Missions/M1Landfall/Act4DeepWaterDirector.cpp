// Act4DeepWaterDirector.cpp

#include "Act4DeepWaterDirector.h"
#include "Act3ContactDirector.h"
#include "IronBreach.h"
#include "IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

AAct4DeepWaterDirector::AAct4DeepWaterDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AAct4DeepWaterDirector::BuildDefaultBeats()
{
	Beats.Empty();

	// --- The eruption. 82m, Class B -- see KAIJU-CODEX.md, reclassified from Class C. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("Buildings shrug apart. Something stands up out of the residential block that dwarfs everything the line just held.")),
		4.5f, 0.6f,
		FName("PalawanEruption")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("That is not the same class. That is NOT the same class.")),
		3.5f, 0.4f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Copy. Gun line, work the battery. Command -- we need everything you've got.")),
		4.0f, 0.5f,
		FName("GunLineStart")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(Bellringer charges ring its lead limb. It flinches -- once per hit, never more. The siege gun fires beside them and accomplishes nothing but noise and spall.)")),
		4.5f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("Yeah. We know.")),
		2.5f, 0.8f));

	// --- The mech commits. It gets real hits in. It does not come close to winning. ---

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Doctrine says multiple units for this class. We have one. Vance, Achterberg -- you're cleared to engage.")),
		4.5f, 0.5f,
		FName("MechEngages")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The mech lands real hits. Armor doesn't break. It's not a token gesture -- it just isn't enough.)")),
		4.5f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Comms,
		FText::FromString(TEXT("Vance: -checklist cuts off mid-line as impact rocks the cockpit-")),
		3.5f, 0.6f,
		FName("MechLosing")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("All units, full withdrawal. Not a squad pullback -- everyone. Garrison falls back, now.")),
		4.5f, 1.0f,
		FName("FallBackOrder")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The mech covers the withdrawal, still fighting, as the line breaks for the rally point.)")),
		4.0f, 1.0f));
}

void AAct4DeepWaterDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Act IV] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (AAct3ContactDirector* Previous = PreviousActDirector.LoadSynchronous())
	{
		Previous->OnAct3Complete.AddDynamic(this, &AAct4DeepWaterDirector::OnPreviousActComplete);
	}
	else if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AAct4DeepWaterDirector::StartAct4, InitialDelay, false);
	}
}

void AAct4DeepWaterDirector::OnPreviousActComplete()
{
	StartAct4();
}

void AAct4DeepWaterDirector::StartAct4()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AAct4DeepWaterDirector::SkipToFallBack()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("PalawanEruption"));
	HandleScriptedEvent(FName("MechEngages"));
	HandleScriptedEvent(FName("FallBackOrder"));
	FinishAct4();
}

void AAct4DeepWaterDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishAct4();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AAct4DeepWaterDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[Act IV] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AAct4DeepWaterDirector::AdvanceToNextLine, TotalDelay, false);
}

void AAct4DeepWaterDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AAct4DeepWaterDirector::FinishAct4()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[Act IV] Complete -- full withdrawal ordered, cutting to Act V."));
	OnAct4Complete.Broadcast();
}

bool AAct4DeepWaterDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
