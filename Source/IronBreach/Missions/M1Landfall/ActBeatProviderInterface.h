// ActBeatProviderInterface.h
//
// Common interface implemented by every act "Director" actor (Act1BarracksDirector,
// Act2EscalationDirector, and whatever follows). Lets ONE generic subtitle HUD
// (MissionSubtitleHUD) find whichever act is currently running without knowing about
// each act's concrete class -- new acts just implement this and the HUD picks them up
// automatically, no HUD changes needed.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "DialogueTypes.h"
#include "ActBeatProviderInterface.generated.h"

UINTERFACE(BlueprintType, MinimalAPI)
class UActBeatProviderInterface : public UInterface
{
	GENERATED_BODY()
};

class IRONBREACH_API IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	// Returns true and fills OutLine if this act currently has an active line to display.
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const = 0;

	// Whether this act's timeline is currently running (started, not yet complete).
	// Used to disambiguate if more than one director actor exists in the level at once
	// (e.g. Act I's director lingering after Act II has already started).
	virtual bool IsActRunning() const = 0;
};
