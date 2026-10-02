// IBDialogueVoice.h
//
// Voice-over playback for the M1 "Landfall" scripted dialogue lines.
//
// A line's voice is found in this order:
//   1. FDialogueLine::VoiceSound, if you set one on the line.
//   2. By naming convention, with NO wiring: a USoundBase asset at
//        /Game/IronBreach/Audio/VO/M1/<ActTag>_L<NNN>
//      e.g. A1_L003 = Act I, line index 3 (0-based, zero-padded to 3 digits).
//      ActTags: A1..A5 (acts), GA (guide-route arrival lines), GC (guide-route call-outs).
//
// Where it plays:
//   - Rhodes / Bricks / Static / Vance / Achterberg: 3D, attached to the NPC actor
//     tagged VO_Rhodes / VO_Bricks / VO_Static / VO_Vance / VO_Achterberg (nearest to
//     the local player if several are tagged).
//   - Player / Idris / Comms / ambient, or if no tagged actor exists: 2D.
//
// Returns the clip length so the director can hold the subtitle (and the next line)
// until the voice finishes. If no sound is found it returns 0 and nothing changes --
// subtitle-only behaviour is exactly as before.

#pragma once

#include "CoreMinimal.h"
#include "IBLandfallDialogueTypes.h"

class AActor;
class UObject;

namespace IBDialogueVoice
{
	// Actor tag that marks the NPC who "speaks" this speaker's lines (NAME_None = always 2D).
	IRONBREACH_API FName GetSpeakerTag(EDialogueSpeaker Speaker);

	// Nearest visible actor carrying the speaker's tag, or nullptr.
	IRONBREACH_API AActor* FindSpeakerActor(UObject* WorldContext, EDialogueSpeaker Speaker);

	// Plays the line's voice (if any). Returns its duration in seconds, 0 if none.
	IRONBREACH_API float PlayLine(UObject* WorldContext, const FDialogueLine& Line, const TCHAR* ActTag, int32 LineIndex);
}
