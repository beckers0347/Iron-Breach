#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBSettingsScreen.generated.h"

class UTextBlock;
class UButton;
class UVerticalBox;
class UHorizontalBox;

/**
 * The Settings screen — registered as "Settings" in the screen registry (no
 * hotkey; reached from the System screen and the main menu). Escape closes it
 * like every other screen; every change applies immediately AND saves, so
 * there's no Apply button to forget.
 *
 * Two-column card:
 *   VIDEO ....... quality, window, resolution, render scale, vsync, fps cap,
 *                 fov, brightness, fps counter
 *   AUDIO ....... master / music / sfx
 *   CONTROLS .... mouse sens, ads sens, invert y, toggle ads
 * plus RESET TO DEFAULTS.
 *
 * Deliberately NOT abstract: the C++ class is the whole screen. Shane can
 * child it in a WBP later; a WBP with its own root suppresses the fallback.
 */
UCLASS()
class IRONBREACH_API UIBSettingsScreen : public UIBMenuScreen
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeScreenOpened() override;

	// Arrow thunks (dynamic delegates carry no payload).
	UFUNCTION() void HandleQualityPrev()   { StepQuality(-1); }
	UFUNCTION() void HandleQualityNext()   { StepQuality(+1); }
	UFUNCTION() void HandleWindowPrev()    { StepWindowMode(-1); }
	UFUNCTION() void HandleWindowNext()    { StepWindowMode(+1); }
	UFUNCTION() void HandleResPrev()       { StepResolution(-1); }
	UFUNCTION() void HandleResNext()       { StepResolution(+1); }
	UFUNCTION() void HandleScalePrev()     { StepRenderScale(-5); }
	UFUNCTION() void HandleScaleNext()     { StepRenderScale(+5); }
	UFUNCTION() void HandleVSyncToggle()   { ToggleVSync(); }
	UFUNCTION() void HandleFpsCapPrev()    { StepFpsCap(-1); }
	UFUNCTION() void HandleFpsCapNext()    { StepFpsCap(+1); }
	UFUNCTION() void HandleFovPrev()       { StepFov(-5.0f); }
	UFUNCTION() void HandleFovNext()       { StepFov(+5.0f); }
	UFUNCTION() void HandleGammaPrev()     { StepGamma(-0.1f); }
	UFUNCTION() void HandleGammaNext()     { StepGamma(+0.1f); }
	UFUNCTION() void HandleShowFpsToggle() { ToggleShowFps(); }
	UFUNCTION() void HandleMasterPrev()    { StepMaster(-0.1f); }
	UFUNCTION() void HandleMasterNext()    { StepMaster(+0.1f); }
	UFUNCTION() void HandleMusicPrev()     { StepMusic(-0.1f); }
	UFUNCTION() void HandleMusicNext()     { StepMusic(+0.1f); }
	UFUNCTION() void HandleSfxPrev()       { StepSfx(-0.1f); }
	UFUNCTION() void HandleSfxNext()       { StepSfx(+0.1f); }
	UFUNCTION() void HandleSensPrev()      { StepSensitivity(-0.1f); }
	UFUNCTION() void HandleSensNext()      { StepSensitivity(+0.1f); }
	UFUNCTION() void HandleAdsSensPrev()   { StepAdsSensitivity(-0.1f); }
	UFUNCTION() void HandleAdsSensNext()   { StepAdsSensitivity(+0.1f); }
	UFUNCTION() void HandleInvertToggle()  { ToggleInvertY(); }
	UFUNCTION() void HandleAdsModeToggle() { ToggleAdsMode(); }
	UFUNCTION() void HandleResetClicked();

private:
	void BuildFallbackLayout();

	/** One settings row: label left, [<] value [>] right. Returns the value
	 *  text block; Prev/Next receive the created arrow buttons. */
	UTextBlock* MakeRow(UVerticalBox* Column, const FText& Label, UButton*& OutPrev, UButton*& OutNext);
	void AddSection(UVerticalBox* Column, const FText& Label);

	void StepQuality(int32 Direction);
	void StepWindowMode(int32 Direction);
	void StepResolution(int32 Direction);
	void StepRenderScale(int32 Delta);
	void ToggleVSync();
	void StepFpsCap(int32 Direction);
	void StepFov(float Delta);
	void StepGamma(float Delta);
	void ToggleShowFps();
	void StepMaster(float Delta);
	void StepMusic(float Delta);
	void StepSfx(float Delta);
	void StepSensitivity(float Delta);
	void StepAdsSensitivity(float Delta);
	void ToggleInvertY();
	void ToggleAdsMode();

	/** Re-read everything from the settings object into the row values. */
	void RefreshValues();

	/** Apply + persist after any change — no Apply button to forget. */
	void ApplyAndSave();

	UPROPERTY(Transient) TObjectPtr<UTextBlock> QualityValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> WindowValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ResolutionValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ScaleValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> VSyncValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FpsCapValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FovValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> GammaValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ShowFpsValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MasterValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MusicValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SfxValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SensitivityValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AdsSensitivityValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> InvertValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AdsModeValue;

	/** Common 16:9 ladder; the current native res is inserted if missing. */
	TArray<FIntPoint> ResolutionOptions;

	/** 0 = uncapped, then the common caps. */
	TArray<int32> FpsCapOptions;
};
