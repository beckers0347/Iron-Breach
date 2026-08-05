#include "UI/IBMenuScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBUISettings.h"

void UIBMenuScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	SetIsFocusable(true); // required for NativeOnKeyDown to receive anything

	if (CloseKeys.IsEmpty())
	{
		CloseKeys = { EKeys::Escape, EKeys::Gamepad_FaceButton_Right };
	}
	if (NextScreenKeys.IsEmpty())
	{
		NextScreenKeys = { EKeys::E, EKeys::Gamepad_RightShoulder };
	}
	if (PrevScreenKeys.IsEmpty())
	{
		PrevScreenKeys = { EKeys::Q, EKeys::Gamepad_LeftShoulder };
	}
}

void UIBMenuScreen::NotifyScreenOpened(UIBMenuSubsystem* InOwner, FName InScreenId)
{
	OwnerSubsystem = InOwner;
	ScreenId = InScreenId;
	SetKeyboardFocus();
	NativeScreenOpened();
	BP_OnScreenOpened();
}

void UIBMenuScreen::NotifyScreenClosed()
{
	NativeScreenClosed();
	BP_OnScreenClosed();
}

FReply UIBMenuScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();

	if (OwnerSubsystem)
	{
		if (CloseKeys.Contains(Key))
		{
			OwnerSubsystem->CloseMenu();
			return FReply::Handled();
		}
		if (NextScreenKeys.Contains(Key))
		{
			OwnerSubsystem->CycleScreen(+1);
			return FReply::Handled();
		}
		if (PrevScreenKeys.Contains(Key))
		{
			OwnerSubsystem->CycleScreen(-1);
			return FReply::Handled();
		}

		// Screen hotkeys from settings: same key toggles closed, another
		// screen's key jumps sideways — mirrors the in-game bindings so the
		// menu keys feel like one system inside and out.
		for (const FIBMenuScreenDef& Def : UIBUISettings::Get()->Screens)
		{
			if (Def.Hotkeys.Contains(Key))
			{
				OwnerSubsystem->ToggleScreen(Def.ScreenId);
				return FReply::Handled();
			}
		}
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
