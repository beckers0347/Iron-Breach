// IBCampaignDebugLibrary.h
//
// PIE/testing convenience: lets you temporarily disable the M1 campaign's scripted
// act directors (Barracks/Escalation/Contact/DeepWater/Retreat) without touching the
// level or recompiling, so other systems (weapons, hand-IK, movement, whatever) can be
// iterated on in CarrowGateGarrison without the mission auto-playing over you every PIE run.
//
// Backed by a console variable so it's toggleable live from the in-game console (~):
//   IronBreach.DisableCampaign 1   -- placed directors go dormant on their next BeginPlay
//   IronBreach.DisableCampaign 0   -- normal behavior
// Also exposed as a Blueprint-callable pair (SetCampaignDisabled/IsCampaignDisabled) so
// it can be wired to a debug menu button instead of typing console commands every time.
//
// Note: this only stops the Directors from auto-starting/auto-chaining -- it does not
// destroy already-placed director actors or touch anything else in the level. Flipping
// it back on mid-session will not retroactively resume a run that was skipped; it just
// means the NEXT BeginPlay (next PIE session) runs normally again.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "IBCampaignDebugLibrary.generated.h"

UCLASS()
class IRONBREACH_API UIBCampaignDebugLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// True if M1's act directors (and the generic AIBMissionDirector auto-spawn) should
	// stay dormant. Checked once, at BeginPlay, by each director -- not polled per-tick.
	UFUNCTION(BlueprintPure, Category = "Mission|Debug")
	static bool IsCampaignDisabled();

	// Flip the console variable from Blueprint (e.g. a debug menu toggle) instead of
	// typing the console command by hand. Takes effect for any director that hasn't
	// run its BeginPlay check yet -- won't interrupt one already mid-scene.
	UFUNCTION(BlueprintCallable, Category = "Mission|Debug")
	static void SetCampaignDisabled(bool bDisabled);
};
