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
 * Deliberately NOT abstract: the C++ class is the whole screen (arrow-cycled
 * rows built in code). Shane can still child it in a WBP later; any WBP child
 * with its own root simply suppresses the fallback rows the usual way.
 *
 * Rows:
 *   QUALITY ....... engine scalability preset (Low/Medium/High/Epic)
 *   WINDOW ........ Fullscreen / Borderless / Windowed
 *   RESOLUTION .... common-list cycle (applies with the window mode)
 *   MASTER VOLUME . 0..100% (FApp volume via IBUserSettings)
 *   MOUSE SENS .... 0.1..3.0 (read by infantry Look)
 */
UCLASS()
class IRONBREACH_API UIBSettingsScreen : public UIBMenuScreen
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeScreenOpened() override;

	// Arrow thunks (dynamic delegates carry no payload).
	UFUNCTION() void HandleQualityPrev()  { StepQuality(-1); }
	UFUNCTION() void HandleQualityNext()  { StepQuality(+1); }
	UFUNCTION() void HandleWindowPrev()   { StepWindowMode(-1); }
	UFUNCTION() void HandleWindowNext()   { StepWindowMode(+1); }
	UFUNCTION() void HandleResPrev()      { StepResolution(-1); }
	UFUNCTION() void HandleResNext()      { StepResolution(+1); }
	UFUNCTION() void HandleVolumeDown()   { StepVolume(-0.1f); }
	UFUNCTION() void HandleVolumeUp()     { StepVolume(+0.1f); }
	UFUNCTION() void HandleSensDown()     { StepSensitivity(-0.1f); }
	UFUNCTION() void HandleSensUp()       { StepSensitivity(+0.1f); }

private:
	void BuildFallbackLayout();

	/** One settings row: label left, [<] value [>] right. Returns the value
	 *  text block; Prev/Next receive the created arrow buttons. */
	UTextBlock* MakeRow(UVerticalBox* Column, const FText& Label, UButton*& OutPrev, UButton*& OutNext);

	void StepQuality(int32 Direction);
	void StepWindowMode(int32 Direction);
	void StepResolution(int32 Direction);
	void StepVolume(float Delta);
	void StepSensitivity(float Delta);

	/** Re-read everything from the settings objects into the row values. */
	void RefreshValues();

	/** Apply + persist after any change — no Apply button to forget. */
	void ApplyAndSave();

	UPROPERTY(Transient) TObjectPtr<UTextBlock> QualityValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> WindowValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ResolutionValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> VolumeValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SensitivityValue;

	/** Common 16:9 ladder; the current native res is inserted if missing. */
	TArray<FIntPoint> ResolutionOptions;
};
