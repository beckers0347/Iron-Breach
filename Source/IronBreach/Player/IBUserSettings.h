#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "IBUserSettings.generated.h"

/**
 * Iron Breach's user settings — engine video settings (resolution, window
 * mode, scalability) come from the base class for free; this adds the two the
 * engine doesn't own: master volume and mouse sensitivity. Persisted in
 * GameUserSettings.ini alongside everything else.
 *
 * Registered via DefaultEngine.ini:
 *   [/Script/Engine.Engine]
 *   GameUserSettingsClassName=/Script/IronBreach.IBUserSettings
 *
 * Readers: the settings screen writes, AIBCharacter_Infantry::Look reads
 * sensitivity, ApplyIBSettings pushes volume into FApp. Nothing else should
 * cache these values — always read through Get().
 */
UCLASS()
class IRONBREACH_API UIBUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:
	/** The engine's singleton, typed. Null only before engine init. */
	UFUNCTION(BlueprintPure, Category = "Settings")
	static UIBUserSettings* Get();

	UFUNCTION(BlueprintPure, Category = "Settings")
	float GetMasterVolume() const { return MasterVolume; }

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SetMasterVolume(float InVolume);

	UFUNCTION(BlueprintPure, Category = "Settings")
	float GetMouseSensitivity() const { return MouseSensitivity; }

	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SetMouseSensitivity(float InSensitivity);

	/** Push the custom settings into the running app (volume). Video settings
	 *  go through the base class's ApplySettings as usual. Called on load
	 *  (module startup isn't needed — first read applies) and on every set. */
	void ApplyIBSettings();

	/** Engine calls this on startup + every ApplySettings — piggyback the
	 *  custom values so saved volume takes effect at boot with no extra hook. */
	virtual void ApplyNonResolutionSettings() override;

	virtual void SetToDefaults() override;

private:
	/** 0..1, drives FApp's global volume multiplier — no sound-class setup needed. */
	UPROPERTY(Config)
	float MasterVolume = 1.0f;

	/** Look input scale, 0.1..3.0. 1.0 = raw. */
	UPROPERTY(Config)
	float MouseSensitivity = 1.0f;
};
