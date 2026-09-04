// MissionSubtitleHUD.h
//
// Generic subtitle renderer for ANY act director that implements
// IActBeatProviderInterface (Act1BarracksDirector, Act2EscalationDirector, and
// whatever acts follow). Finds whichever director actor currently reports
// IsActRunning() == true and draws its current line as bottom-of-screen subtitles
// using a plain Canvas -- no UMG widget asset required.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "MissionSubtitleHUD.generated.h"

class UObject;

UCLASS()
class IRONBREACH_API AMissionSubtitleHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitles")
	FLinearColor SpeakerColor = FLinearColor(0.85f, 0.75f, 0.35f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitles")
	FLinearColor TextColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitles")
	float BottomMarginPx = 140.0f;

protected:
	// Cached each frame rather than once, since which act is "running" changes over
	// the course of the mission (Act I hands off to Act II, etc.).
	UObject* FindActiveBeatProvider() const;
};
