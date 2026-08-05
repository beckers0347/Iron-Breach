#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBSystemScreen.generated.h"

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
 * No BindWidget names on this one — nothing for C++ to drive.
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
};
