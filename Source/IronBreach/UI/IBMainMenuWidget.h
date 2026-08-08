#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Online/IBSessionSubsystem.h" // EIBSessionStatus in a UFUNCTION signature
#include "IBMainMenuWidget.generated.h"

class UButton;
class UTextBlock;

/**
 * C++ brains for the title screen / main menu (demo d1 + d5).
 *
 * Reparent WBP_MainMenu to this and name widgets to the optional binds below —
 * any subset works, visuals stay 100% Connor's. Buttons drive the session
 * subsystem; the status line narrates every beat so a failed join never looks
 * like a dead game.
 *
 * Input-mode law (learned the hard way when the menu froze the level): the
 * moment a travel is committed we set GameOnly + hide the cursor, BEFORE the
 * map switch — UIOnly persists across travels and bricks the next level. On a
 * terminal failure we hand the menu back: UIOnly + cursor + buttons re-enabled.
 */
UCLASS(Abstract)
class IRONBREACH_API UIBMainMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Solo play destination. Host destination lives on the subsystem (HostTravelURL). */
	UPROPERTY(EditDefaultsOnly, Category = "Menu")
	FString SoloTravelURL = TEXT("/Game/FirstPerson/Lvl_FirstPerson");

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeDestruct() override;

	// ---- Optional-bind layout hooks (names matter) ----

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UButton> Btn_Solo;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UButton> Btn_Host;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UButton> Btn_Join;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UButton> Btn_Quit;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UTextBlock> Txt_Status;

	/** Title-screen flourishes (pulse the status line, flicker on failure). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Session Status"))
	void BP_OnSessionStatus(EIBSessionStatus Status, const FText& Message);

	UFUNCTION() void HandleSolo();
	UFUNCTION() void HandleHost();
	UFUNCTION() void HandleJoin();
	UFUNCTION() void HandleQuit();

	UFUNCTION()
	void HandleSessionStatus(EIBSessionStatus Status, const FText& Message);

private:
	UIBSessionSubsystem* GetSessions() const;

	/** Commit to leaving the menu: buttons off, input to game, cursor away. */
	void LockForTravel();

	/** Terminal failure: hand the menu back to the player. */
	void UnlockAfterFailure();

	void SetButtonsEnabled(bool bEnabled);
	void SetStatus(const FText& Message);
};
