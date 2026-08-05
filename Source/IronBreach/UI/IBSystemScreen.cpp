#include "UI/IBSystemScreen.h"
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "Online/IBSessionSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/KismetSystemLibrary.h"

void UIBSystemScreen::ResumeGame()
{
	if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
	{
		Menu->CloseMenu();
	}
}

void UIBSystemScreen::LeaveToMainMenu()
{
	// Drop the menu first so the input-mode restore runs against THIS world;
	// after travel the whole local player UI state is rebuilt anyway.
	ResumeGame();

	const UGameInstance* GI = GetGameInstance();
	if (UIBSessionSubsystem* Session = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr)
	{
		Session->IBLeave(); // handles session teardown + the travel itself
	}
}

void UIBSystemScreen::QuitToDesktop()
{
	UKismetSystemLibrary::QuitGame(GetWorld(), GetOwningPlayer(), EQuitPreference::Quit, false);
}

bool UIBSystemScreen::IsInNetworkedSession() const
{
	const UWorld* World = GetWorld();
	return World && World->GetNetMode() != NM_Standalone;
}
