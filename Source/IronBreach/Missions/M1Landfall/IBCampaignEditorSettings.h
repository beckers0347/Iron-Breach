// IBCampaignEditorSettings.h
//
// Editor-only switch for the scripted campaign (tutorial / act directors / guide route).
// Lives in Editor Preferences > Iron Breach > Campaign, saved per user (not shared, not
// shipped). Only read in editor builds and only for Play-In-Editor sessions, so a packaged
// game always runs the campaign regardless of what is ticked here.
//
// Untick "Run Campaign In PIE" to free-roam a mission level: the act directors stay dormant,
// the guide route never starts (no NPC walking, no player pull), and the NPCs stand where
// they are placed.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "IBCampaignEditorSettings.generated.h"

UCLASS(config = EditorPerProjectUserSettings, meta = (DisplayName = "Campaign"))
class IRONBREACH_API UIBCampaignEditorSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UIBCampaignEditorSettings();

	// Off = Play-In-Editor skips the scripted campaign/tutorial so you can roam freely.
	// Has no effect on packaged builds or standalone game sessions.
	UPROPERTY(config, EditAnywhere, Category = "Campaign")
	bool bRunCampaignInPIE = true;

	virtual FName GetContainerName() const override { return FName("Editor"); }
	virtual FName GetCategoryName() const override { return FName("Iron Breach"); }
};
