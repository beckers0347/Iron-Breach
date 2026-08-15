#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBSystemScreen.generated.h"

class UButton;
class UTextBlock;

/**
 * Escape's screen: the pause-menu-that-isn't (a co-op world never pauses;
 * this is just a menu like the others). The C++ is intentionally thin — three
 * verbs behind BlueprintCallables — because the whole screen is buttons, and
 * buttons are Shane's. Build them in the WBP, wire clicks to these.
 *
 * A Settings page belongs here eventually; it's a content problem (what
 * settings exist?) before it's a code one, so this screen ships without it
 * and gains a sub-panel later without any C++ churn.
 *
 * Optional binds: name buttons Btn_Resume / Btn_Leave / Btn_Quit and C++
 * wires the clicks (and labels them via Txt_* if present). If the WBP has
 * NO Btn_ binds at all, C++ constructs a minimal centered three-button
 * column at runtime — the packaged game must never lack an exit path just
 * because the widget is still bare (learned from build one: no way to quit).
 */
UCLASS(Abstract)
class IRONBREACH_API UIBSystemScreen : public UIBMenuScreen
{
	GENERATED_BODY()

public:
	/** Close the menu, back to the fight. */
	UFUNCTION(BlueprintCallable, Category = "System")
	void ResumeGame();

	/** Destroy/leave the online session and travel to the main menu.
	 *  Works solo too (plain travel). Host beware: on a listen server the
	 *  host leaving ends the session for everyone — that's the listen-server
	 *  deal (ADR-002), not a bug. */
	UFUNCTION(BlueprintCallable, Category = "System")
	void LeaveToMainMenu();

	UFUNCTION(BlueprintCallable, Category = "System")
	void QuitToDesktop();

	/** For the Leave button's label/visibility: true when actually connected
	 *  to (or hosting) a networked session, false in solo/standalone. */
	UFUNCTION(BlueprintPure, Category = "System")
	bool IsInNetworkedSession() const;

protected:
	virtual void NativeOnInitialized() override;

	// ---- Optional-bind layout hooks (names matter; all optional) ----

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UButton> Btn_Resume;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UButton> Btn_Leave;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UButton> Btn_Quit;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UTextBlock> Txt_Resume;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UTextBlock> Txt_Leave;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "System")
	TObjectPtr<UTextBlock> Txt_Quit;

	UFUNCTION() void HandleResumeClicked();
	UFUNCTION() void HandleLeaveClicked();
	UFUNCTION() void HandleQuitClicked();

private:
	/** Bare-WBP fallback: build a centered Resume/Leave/Quit column in code. */
	void ConstructFallbackLayout();

	/** Make a fallback button+label pair and register it in the given box. */
	UButton* MakeFallbackButton(class UVerticalBox* Box, const FText& Label);
};
