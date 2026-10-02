#include "UI/IBMenuSubsystem.h"
#include "IronBreach.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBInventoryScreen.h"
#include "UI/IBUISettings.h"
#include "Blueprint/UserWidget.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

APlayerController* UIBMenuSubsystem::GetOwningPC() const
{
	const ULocalPlayer* LP = GetLocalPlayer();
	return LP ? LP->GetPlayerController(LP->GetWorld()) : nullptr;
}

void UIBMenuSubsystem::PurgeStaleScreens(const APlayerController* CurrentPC)
{
	for (auto It = ScreenCache.CreateIterator(); It; ++It)
	{
		const UIBMenuScreen* Screen = It->Value;
		if (!Screen || Screen->GetOwningPlayer() != CurrentPC)
		{
			It.RemoveCurrent();
		}
	}

	// A menu that was open when the world died: no close signals — the world
	// (and every listener in it) is already gone. Just forget.
	if (ActiveScreen && ActiveScreen->GetOwningPlayer() != CurrentPC)
	{
		ActiveScreen = nullptr;
		ActiveScreenId = NAME_None;
	}
}

void UIBMenuSubsystem::ToggleScreen(FName ScreenId)
{
	// Debounce: one keypress can arrive through two routes (the raw Escape
	// floor AND the Enhanced Input action) — without this the menu opens and
	// closes in the same frame.
	const double Now = FPlatformTime::Seconds();
	if (ScreenId == LastToggleId && Now - LastToggleTime < 0.15)
	{
		return;
	}
	LastToggleId = ScreenId;
	LastToggleTime = Now;

	if (IsMenuOpen() && (GetActiveTabId() == ScreenId || ActiveScreenId == ScreenId))
	{
		CloseMenu();
	}
	else
	{
		OpenScreen(ScreenId);
	}
}

void UIBMenuSubsystem::OpenScreen(FName ScreenId)
{
	const FName RequestedTab = ScreenId;
	if (ScreenId == TEXT("Character") || ScreenId == TEXT("Backpack")) { ScreenId = TEXT("Inventory"); }
	APlayerController* PC = GetOwningPC();
	if (!PC) { return; }

	PurgeStaleScreens(PC); // cheap; guards the first open after any map travel

	UIBMenuScreen* Screen = GetOrCreateScreen(ScreenId);
	if (!Screen)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[Menu] No screen registered for '%s'. Check Project Settings > Iron Breach UI (MENUS_UI_WIRING.md §4)."),
			*ScreenId.ToString());
		return;
	}

	const bool bWasOpen = IsMenuOpen();
	const EIBMenuGroup Group = UIBUISettings::Get()->GetMenuGroup(ScreenId);
	if (Group != EIBMenuGroup::Utility) { ActiveMenuGroup = Group; }
	if (UIBInventoryScreen* Inventory = Cast<UIBInventoryScreen>(Screen))
	{
		if (RequestedTab == TEXT("Character")) { Inventory->ShowCharacterTab(); }
		else if (RequestedTab == TEXT("Backpack")) { Inventory->ShowBackpackTab(); }
	}

	// Sideways switch: swap widgets without churning input mode or re-firing
	// the open/close signals (the menu hum shouldn't restart on every tab).
	if (ActiveScreen && ActiveScreen != Screen)
	{
		ActiveScreen->NotifyScreenClosed();
		ActiveScreen->RemoveFromParent();
	}
	else if (ActiveScreen == Screen)
	{
		Screen->SetKeyboardFocus();
		return;
	}

	ActiveScreen = Screen;
	ActiveScreenId = ScreenId;

	Screen->AddToViewport(100); // above HUD
	Screen->NotifyScreenOpened(this, ScreenId);
	ApplyMenuInputMode(Screen);

	if (!bWasOpen)
	{
		OnMenuOpened.Broadcast(ScreenId);
	}
}

void UIBMenuSubsystem::CloseMenu()
{
	PurgeStaleScreens(GetOwningPC()); // stale active screen = nothing to close
	if (!IsMenuOpen()) { return; }

	ActiveScreen->NotifyScreenClosed();
	ActiveScreen->RemoveFromParent();
	ActiveScreen = nullptr;
	ActiveScreenId = NAME_None;

	RestoreGameInputMode();
	OnMenuClosed.Broadcast();
}

void UIBMenuSubsystem::CycleScreen(int32 Direction)
{
	const TArray<FName> Tabs = UIBUISettings::Get()->GetMenuTabs(ActiveMenuGroup);
	const int32 Num = Tabs.Num();
	if (!IsMenuOpen() || Num < 2 || Direction == 0) { return; }
	const int32 Index = Tabs.IndexOfByKey(GetActiveTabId());
	if (Index == INDEX_NONE) { return; } // System/Settings are outside either tab loop.
	OpenScreen(Tabs[(Index + (Direction > 0 ? 1 : -1) + Num) % Num]);
}

FName UIBMenuSubsystem::GetActiveTabId() const
{
	if (const UIBInventoryScreen* Inventory = Cast<UIBInventoryScreen>(ActiveScreen))
	{
		return Inventory->IsBackpackTab() ? FName(TEXT("Backpack")) : FName(TEXT("Character"));
	}
	return ActiveScreenId;
}

UIBMenuScreen* UIBMenuSubsystem::GetOrCreateScreen(FName ScreenId)
{
	if (TObjectPtr<UIBMenuScreen>* Cached = ScreenCache.Find(ScreenId))
	{
		return *Cached;
	}

	const FIBMenuScreenDef* Def = UIBUISettings::Get()->FindScreen(ScreenId);
	if (!Def || Def->WidgetClass.IsNull()) { return nullptr; }

	// Sync load is fine: first-open only, and menu widget classes are small.
	UClass* WidgetClass = Def->WidgetClass.LoadSynchronous();
	APlayerController* PC = GetOwningPC();
	if (!WidgetClass || !PC) { return nullptr; }

	UIBMenuScreen* Screen = CreateWidget<UIBMenuScreen>(PC, WidgetClass);
	if (Screen)
	{
		ScreenCache.Add(ScreenId, Screen);
	}
	return Screen;
}

void UIBMenuSubsystem::ApplyMenuInputMode(UIBMenuScreen* Screen)
{
	APlayerController* PC = GetOwningPC();
	if (!PC || !Screen) { return; }

	// UI-only while a menu is up: the pawn must not move/fire under the screen.
	// The pawn's Enhanced Input goes quiet here, which is why in-menu keys
	// (close, cycle, screen hotkeys) are handled by the screen widget itself.
	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(Screen->TakeWidget());
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PC->SetInputMode(InputMode);
	PC->SetShowMouseCursor(true);
	PC->FlushPressedKeys(); // no stuck WASD when the menu drops
}

void UIBMenuSubsystem::RestoreGameInputMode()
{
	if (APlayerController* PC = GetOwningPC())
	{
		// Front-end worlds (title / squad lobby) are cursor places: restoring
		// GameOnly there after closing a screen (e.g. the Squad tab opened from
		// the lobby strip) would strand the player cursor-less in a clickable
		// menu. Everywhere else, hand input back to the pawn as before.
		const UWorld* World = PC->GetWorld();
		const bool bFrontEndWorld = World && World->GetMapName().Contains(TEXT("MainMenu"));
		if (bFrontEndWorld)
		{
			FInputModeUIOnly Mode;
			Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
			PC->SetInputMode(Mode);
			PC->SetShowMouseCursor(true);
			return;
		}

		PC->SetInputMode(FInputModeGameOnly());
		PC->SetShowMouseCursor(false);
	}
}
