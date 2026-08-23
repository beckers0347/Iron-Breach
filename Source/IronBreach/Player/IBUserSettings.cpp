#include "Player/IBUserSettings.h"
#include "Engine/Engine.h"
#include "Misc/App.h"

UIBUserSettings* UIBUserSettings::Get()
{
	return GEngine ? Cast<UIBUserSettings>(GEngine->GetGameUserSettings()) : nullptr;
}

void UIBUserSettings::SetMasterVolume(float InVolume)
{
	MasterVolume = FMath::Clamp(InVolume, 0.0f, 1.0f);
	ApplyIBSettings();
}

void UIBUserSettings::SetMouseSensitivity(float InSensitivity)
{
	MouseSensitivity = FMath::Clamp(InSensitivity, 0.1f, 3.0f);
}

void UIBUserSettings::ApplyIBSettings()
{
	// Global app volume: affects every sound without touching sound classes.
	FApp::SetVolumeMultiplier(MasterVolume);
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
	MouseSensitivity = 1.0f;
}
