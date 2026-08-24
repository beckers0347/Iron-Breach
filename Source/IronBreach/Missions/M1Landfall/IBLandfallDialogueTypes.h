// IBLandfallDialogueTypes.h
// Shared data types for the M1 "Landfall" mission's scripted dialogue/subtitle beats.
// No editor assets required -- everything here is plain code + data.

#pragma once

#include "CoreMinimal.h"
#include "IBLandfallDialogueTypes.generated.h"

UENUM(BlueprintType)
enum class EDialogueSpeaker : uint8
{
	None		UMETA(DisplayName = "None (Ambient/Narration)"),
	Player		UMETA(DisplayName = "Player (FERRYMAN)"),
	Static		UMETA(DisplayName = "Spc. Theo \"Static\" Yun"),
	Rhodes		UMETA(DisplayName = "Lt. Imani Rhodes"),
	Bricks		UMETA(DisplayName = "Sgt. Adaeze \"Bricks\" Okafor"),
	Idris		UMETA(DisplayName = "Ms. Idris"),
	Comms		UMETA(DisplayName = "Garrison Comms / Sirens")
};

// A single scripted line in a mission act. Acts are just ordered arrays of these,
// played back on a timer by a Director actor (see Act1BarracksDirector).
USTRUCT(BlueprintType)
struct FDialogueLine
{
	GENERATED_BODY()

	// Who is speaking (or None for ambient/environmental narration text).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	EDialogueSpeaker Speaker = EDialogueSpeaker::None;

	// The subtitle text itself.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FText Text;

	// Seconds to hold this line on screen before advancing to the next one.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	float HoldDuration = 3.0f;

	// Extra pause AFTER this line finishes, before the next one starts (silence beats,
	// e.g. the gap after Ms. Idris stops talking in Act IV, or a radio-static pause here).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	float PauseAfter = 0.5f;

	// If true, firing this line also raises the named gameplay event on the Director
	// (see Act1BarracksDirector::HandleScriptedEvent). Used to hang non-dialogue beats
	// (seismic detection, stand-to order, lighting cues) off the same timeline as the VO.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FName ScriptedEventTag = NAME_None;

	FDialogueLine() = default;

	FDialogueLine(EDialogueSpeaker InSpeaker, const FText& InText, float InHold = 3.0f, float InPause = 0.5f, FName InEventTag = NAME_None)
		: Speaker(InSpeaker), Text(InText), HoldDuration(InHold), PauseAfter(InPause), ScriptedEventTag(InEventTag)
	{
	}
};

// Human-readable speaker label helper (used by the subtitle HUD).
inline FText GetSpeakerDisplayName(EDialogueSpeaker Speaker)
{
	switch (Speaker)
	{
	case EDialogueSpeaker::Player:  return FText::FromString(TEXT("FERRYMAN"));
	case EDialogueSpeaker::Static:  return FText::FromString(TEXT("SPC. YUN \"STATIC\""));
	case EDialogueSpeaker::Rhodes:  return FText::FromString(TEXT("LT. RHODES"));
	case EDialogueSpeaker::Bricks:  return FText::FromString(TEXT("SGT. OKAFOR \"BRICKS\""));
	case EDialogueSpeaker::Idris:   return FText::FromString(TEXT("MS. IDRIS"));
	case EDialogueSpeaker::Comms:   return FText::FromString(TEXT("COMMS"));
	default:                        return FText::GetEmpty();
	}
}
