#include "Player/IBUserSettings.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/App.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundMix.h"
#include "Sound/SoundClass.h"
#include "GameFramework/PlayerController.h"

namespace
{
	// Created by Scripts/ib_create_audio_assets.py; soft-loaded so the code
	// works (Master-only) before the assets exist.
	const TCHAR* MixPath      = TEXT("/Game/IronBreach/Audio/SMix_IB.SMix_IB");
	const TCHAR* MusicClassPath = TEXT("/Game/IronBreach/Audio/SC_Music.SC_Music");
	const TCHAR* SFXClassPath   = TEXT("/Game/IronBreach/Audio/SC_SFX.SC_SFX");
}

UIBUserSettings* UIBUserSettings::Get()
{
	return GEngine ? Cast<UIBUserSettings>(GEngine->GetGameUserSettings()) : nullptr;
}

void UIBUserSettings::ApplyIBSettings()
{
	// Master: global app volume — no sound-class setup needed, hits everything.
	FApp::SetVolumeMultiplier(MasterVolume);

	// Gamma: whole-screen brightness.
	if (GEngine)
	{
		GEngine->DisplayGamma = Gamma;
	}

	ApplyAudioMix();
	ApplyShowFPS();

	OnIBSettingsApplied.Broadcast();
}

void UIBUserSettings::ApplyAudioMix()
{
	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	if (!World) { return; } // engine boot / no play session yet — mix applies on next apply in-game

	USoundMix* Mix = LoadObject<USoundMix>(nullptr, MixPath);
	USoundClass* Music = LoadObject<USoundClass>(nullptr, MusicClassPath);
	USoundClass* SFX = LoadObject<USoundClass>(nullptr, SFXClassPath);
	if (!Mix || (!Music && !SFX)) { return; } // audio assets not created yet — Master still rules

	if (Music)
	{
		UGameplayStatics::SetSoundMixClassOverride(World, Mix, Music, MusicVolume, 1.0f, 0.2f, true);
	}
	if (SFX)
	{
		UGameplayStatics::SetSoundMixClassOverride(World, Mix, SFX, SFXVolume, 1.0f, 0.2f, true);
	}
	UGameplayStatics::PushSoundMixModifier(World, Mix);
}

void UIBUserSettings::ApplyShowFPS()
{
	if (bShowFPS == bShowFPSApplied) { return; }

	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	if (!PC) { return; } // no session yet; toggled next time it's applied in-game

	PC->ConsoleCommand(TEXT("stat fps")); // engine toggle — tracked so it never double-fires
	bShowFPSApplied = bShowFPS;
}

void UIBUserSettings::ApplyNonResolutionSettings()
{
	Super::ApplyNonResolutionSettings();
	ApplyIBSettings();
}

void UIBUserSettings::SetToDefaults()
{
	Super::SetToDefaults();
	MasterVolume = 1.0f;
	MusicVolume = 1.0f;
	SFXVolume = 1.0f;
	FieldOfView = 95.0f;
	Gamma = 2.2f;
	bShowFPS = false;
	MouseSensitivity = 1.0f;
	ADSSensitivity = 1.0f;
	bInvertY = false;
	bToggleADS = false;
}
