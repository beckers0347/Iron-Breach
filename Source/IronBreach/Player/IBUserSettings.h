#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "IBUserSettings.generated.h"

/**
 * Iron Breach's user settings — engine video settings (resolution, window
 * mode, scalability, VSync, frame cap, resolution scale) come from the base
 * class; this adds everything the engine doesn't own: gamma, the audio
 * channel volumes, and the shooter controls (FOV, sensitivities, invert,
 * toggle-ADS, FPS counter). Persisted in GameUserSettings.ini.
 *
 * Registered via DefaultEngine.ini:
 *   [/Script/Engine.Engine]
 *   GameUserSettingsClassName=/Script/IronBreach.IBUserSettings
 *
 * Readers subscribe to OnIBSettingsApplied (native) for live changes — the
 * infantry pawn re-reads FOV that way. Nothing should cache values; always
 * read through Get().
 *
 * Audio channels: MusicVolume/SFXVolume push through a sound mix
 * (/Game/IronBreach/Audio/SMix_IB + SC_Music/SC_SFX, created by the audio
 * asset pass). Sounds Shane hasn't assigned to a class yet only respond to
 * Master (FApp global) — the plumbing leads the content, as usual.
 */
UCLASS()
class IRONBREACH_API UIBUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:
	/** The engine's singleton, typed. Null only before engine init. */
	UFUNCTION(BlueprintPure, Category = "Settings")
	static UIBUserSettings* Get();

	/** Fires after every ApplyIBSettings — pawns re-read FOV etc. here. */
	FSimpleMulticastDelegate OnIBSettingsApplied;

	// ---- Audio ----
	UFUNCTION(BlueprintPure, Category = "Settings|Audio")
	float GetMasterVolume() const { return MasterVolume; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Audio")
	void SetMasterVolume(float InVolume) { MasterVolume = FMath::Clamp(InVolume, 0.0f, 1.0f); }

	UFUNCTION(BlueprintPure, Category = "Settings|Audio")
	float GetMusicVolume() const { return MusicVolume; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Audio")
	void SetMusicVolume(float InVolume) { MusicVolume = FMath::Clamp(InVolume, 0.0f, 1.0f); }

	UFUNCTION(BlueprintPure, Category = "Settings|Audio")
	float GetSFXVolume() const { return SFXVolume; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Audio")
	void SetSFXVolume(float InVolume) { SFXVolume = FMath::Clamp(InVolume, 0.0f, 1.0f); }

	// ---- Video (on top of the base class) ----
	UFUNCTION(BlueprintPure, Category = "Settings|Video")
	float GetFieldOfView() const { return FieldOfView; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Video")
	void SetFieldOfView(float InFOV) { FieldOfView = FMath::Clamp(InFOV, 60.0f, 120.0f); }

	UFUNCTION(BlueprintPure, Category = "Settings|Video")
	float GetGamma() const { return Gamma; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Video")
	void SetGamma(float InGamma) { Gamma = FMath::Clamp(InGamma, 1.0f, 3.4f); }

	UFUNCTION(BlueprintPure, Category = "Settings|Video")
	bool GetShowFPS() const { return bShowFPS; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Video")
	void SetShowFPS(bool bInShow) { bShowFPS = bInShow; }

	// ---- Controls ----
	UFUNCTION(BlueprintPure, Category = "Settings|Controls")
	float GetMouseSensitivity() const { return MouseSensitivity; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Controls")
	void SetMouseSensitivity(float InSens) { MouseSensitivity = FMath::Clamp(InSens, 0.1f, 3.0f); }

	/** Extra multiplier while aiming, on top of the FOV-tracking damping. */
	UFUNCTION(BlueprintPure, Category = "Settings|Controls")
	float GetADSSensitivity() const { return ADSSensitivity; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Controls")
	void SetADSSensitivity(float InSens) { ADSSensitivity = FMath::Clamp(InSens, 0.1f, 2.0f); }

	UFUNCTION(BlueprintPure, Category = "Settings|Controls")
	bool GetInvertY() const { return bInvertY; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Controls")
	void SetInvertY(bool bInInvert) { bInvertY = bInInvert; }

	/** True: RMB toggles ADS. False (default): hold to aim. */
	UFUNCTION(BlueprintPure, Category = "Settings|Controls")
	bool GetToggleADS() const { return bToggleADS; }
	UFUNCTION(BlueprintCallable, Category = "Settings|Controls")
	void SetToggleADS(bool bInToggle) { bToggleADS = bInToggle; }

	/** Push the custom settings into the running app (volume, gamma, mix,
	 *  FPS counter) and broadcast OnIBSettingsApplied. Video settings go
	 *  through the base ApplySettings as usual. */
	void ApplyIBSettings();

	/** Engine calls this on startup + every ApplySettings — piggyback the
	 *  custom values so saved settings take effect at boot with no extra hook. */
	virtual void ApplyNonResolutionSettings() override;

	virtual void SetToDefaults() override;

private:
	void ApplyAudioMix();
	void ApplyShowFPS();

	// -- Audio --
	UPROPERTY(Config) float MasterVolume = 1.0f;   // FApp global — everything
	UPROPERTY(Config) float MusicVolume = 1.0f;    // SC_Music via SMix_IB
	UPROPERTY(Config) float SFXVolume = 1.0f;      // SC_SFX via SMix_IB

	// -- Video extras --
	UPROPERTY(Config) float FieldOfView = 95.0f;   // hip-fire FOV; ADS zoom is relative
	UPROPERTY(Config) float Gamma = 2.2f;          // engine default
	UPROPERTY(Config) bool bShowFPS = false;

	// -- Controls --
	UPROPERTY(Config) float MouseSensitivity = 1.0f;
	UPROPERTY(Config) float ADSSensitivity = 1.0f;
	UPROPERTY(Config) bool bInvertY = false;
	UPROPERTY(Config) bool bToggleADS = false;

	/** Tracks whether "stat fps" is currently on so re-applies don't flicker it. */
	bool bShowFPSApplied = false;
};
