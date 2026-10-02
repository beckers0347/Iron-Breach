#include "UI/IBMenuNavButton.h"
#include "UI/IBMenuSubsystem.h"

UIBMenuNavButton::UIBMenuNavButton(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer)
{
	InitIsFocusable(false); // Navigation leaves keyboard focus on the active screen.
}

void UIBMenuNavButton::Init(UIBMenuSubsystem* InMenu, FName InScreenId)
{
	Menu = InMenu;
	Destination = InScreenId;
	OnClicked.AddUniqueDynamic(this, &UIBMenuNavButton::OpenDestination);
}

void UIBMenuNavButton::OpenDestination()
{
	if (!Menu.IsValid()) { return; }
	Menu->OpenScreen(Destination);
}
