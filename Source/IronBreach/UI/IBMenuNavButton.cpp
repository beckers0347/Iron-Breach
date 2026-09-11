#include "UI/IBMenuNavButton.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBInventoryScreen.h"

void UIBMenuNavButton::Init(UIBMenuSubsystem* InMenu, FName InScreenId)
{
	Menu = InMenu;
	Destination = InScreenId;
	OnClicked.AddUniqueDynamic(this, &UIBMenuNavButton::OpenDestination);
}

void UIBMenuNavButton::OpenDestination()
{
	if (!Menu.IsValid()) { return; }
	if (Destination == TEXT("Character") || Destination == TEXT("Backpack"))
	{
		Menu->OpenScreen(TEXT("Inventory"));
		if (UIBInventoryScreen* Screen = Cast<UIBInventoryScreen>(Menu->GetActiveScreen()))
		{
			if (Destination == TEXT("Character")) { Screen->ShowCharacterTab(); }
			else { Screen->ShowBackpackTab(); }
		}
	}
	else { Menu->OpenScreen(Destination); }
}
