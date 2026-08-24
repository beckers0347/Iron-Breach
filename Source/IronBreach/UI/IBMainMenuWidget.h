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

	/** Opens the Settings screen (registry id "Settings") over the title. */
	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UButton> Btn_Settings;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<UTextBlock> Txt_Status;

	/** House pass over whatever buttons the WBP bound: service-console chip
	 *  background + label font/color, so the title buttons match the in-game
	 *  screens without Shane restyling each one. Untick to keep WBP art. */
	UPROPERTY(EditDefaultsOnly, Category = "Menu|Style")
	bool bApplyHouseStyle = true;

	/** Title-screen flourishes (pulse the status line, flicker on failure). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Session Status"))
	void BP_OnSessionStatus(EIBSessionStatus Status, const FText& Message);

	UFUNCTION() void HandleSolo();
	UFUNCTION() void HandleHost();
	UFUNCTION() void HandleJoin();
	UFUNCTION() void HandleQuit();
	UFUNCTION() void HandleSettings();

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
	void ApplyHouseStyle();

	/** Post-travel lobby detection: a fresh menu widget in a ?listen menu
	 *  world IS the lobby screen. Host gets DEPLOY, clients get patience. */
	void EnterHostLobbyState();
	void EnterClientLobbyState();

	/** The Valorant strip: banners + friends flyout, viewport-anchored. */
	UPROPERTY(Transient)
	TObjectPtr<class UIBLobbyStripWidget> LobbyStrip;

	bool bHostingLobby = false;
};
