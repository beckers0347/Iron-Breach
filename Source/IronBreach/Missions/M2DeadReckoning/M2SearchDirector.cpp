// M2SearchDirector.cpp

#include "M2SearchDirector.h"
#include "IronBreach.h"
#include "../M1Landfall/IBCampaignDebugLibrary.h"
#include "TimerManager.h"
#include "Engine/World.h"

AM2SearchDirector::AM2SearchDirector()
{
	PrimaryActorTick.bCanEverTick = false;
	BuildDefaultBeats();
}

void AM2SearchDirector::BuildDefaultBeats()
{
	Beats.Empty();

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("NINE DAYS AFTER LANDFALL -- FOOTHILLS, INLAND OF CARROWGATE")),
		3.0f, 0.8f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Same ridge the helo clipped on the way out. If it came down anywhere, it's up here.")),
		4.0f, 0.5f,
		FName("SearchBriefed")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("Find the mech, find whoever's in it. In that order, if we get a choice.")),
		4.0f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(The squad moves into the treeline. No sirens, no dust, no district. Just quiet.)")),
		4.0f, 0.6f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Static,
		FText::FromString(TEXT("Still reading a beacon, real faint. Bearing's this way.")),
		3.5f, 0.5f,
		FName("BeaconPing")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::None,
		FText::FromString(TEXT("(A broken branch. Then another. Bricks slows, reading the ground.)")),
		3.5f, 0.5f));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Bricks,
		FText::FromString(TEXT("That's not weather damage. Something came through here moving fast and low.")),
		4.0f, 0.6f,
		FName("TrailFound")));

	Beats.Add(FDialogueLine(
		EDialogueSpeaker::Rhodes,
		FText::FromString(TEXT("Follow it.")),
		2.0f, 1.0f));
}

void AM2SearchDirector::BeginPlay()
{
	Super::BeginPlay();

	if (UIBCampaignDebugLibrary::IsCampaignDisabled())
	{
		UE_LOG(LogIronBreach, Log, TEXT("[M2 Search] Campaign disabled (IronBreach.DisableCampaign) -- staying dormant."));
		return;
	}

	if (bAutoStart)
	{
		GetWorldTimerManager().SetTimer(StartTimerHandle, this, &AM2SearchDirector::StartSearch, InitialDelay, false);
	}
}

void AM2SearchDirector::StartSearch()
{
	bHasCompleted = false;
	CurrentLineIndex = -1;
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	AdvanceToNextLine();
}

void AM2SearchDirector::SkipToTrailFound()
{
	GetWorldTimerManager().ClearTimer(LineTimerHandle);
	GetWorldTimerManager().ClearTimer(StartTimerHandle);

	HandleScriptedEvent(FName("SearchBriefed"));
	HandleScriptedEvent(FName("TrailFound"));
	FinishSearch();
}

void AM2SearchDirector::AdvanceToNextLine()
{
	CurrentLineIndex++;

	if (!Beats.IsValidIndex(CurrentLineIndex))
	{
		FinishSearch();
		return;
	}

	PlayLineAtIndex(CurrentLineIndex);
}

void AM2SearchDirector::PlayLineAtIndex(int32 Index)
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

	UE_LOG(LogIronBreach, Log, TEXT("[M2 Search] %s: %s"),
		*GetSpeakerDisplayName(Line.Speaker).ToString(),
		*Line.Text.ToString());

	const float TotalDelay = FMath::Max(0.01f, Line.HoldDuration + Line.PauseAfter);
	GetWorldTimerManager().SetTimer(LineTimerHandle, this, &AM2SearchDirector::AdvanceToNextLine, TotalDelay, false);
}

void AM2SearchDirector::HandleScriptedEvent(FName EventTag)
{
	OnScriptedEvent.Broadcast(EventTag);
}

void AM2SearchDirector::FinishSearch()
{
	if (bHasCompleted)
	{
		return;
	}

	bHasCompleted = true;
	UE_LOG(LogIronBreach, Log, TEXT("[M2 Search] Complete -- trail found, cutting to Debris Field."));
	OnM2SearchComplete.Broadcast();
}

bool AM2SearchDirector::GetCurrentLine(FDialogueLine& OutLine) const
{
	if (Beats.IsValidIndex(CurrentLineIndex))
	{
		OutLine = Beats[CurrentLineIndex];
		return true;
	}
	return false;
}
