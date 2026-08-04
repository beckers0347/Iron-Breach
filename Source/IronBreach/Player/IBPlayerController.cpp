#include "Player/IBPlayerController.h"
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h" // Explicit include: ULocalPlayer::GetSubsystem under IWYU
#include "InputMappingContext.h"

void AIBPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// Local players only — a server-side proxy controller has no input stack.
	if (!IsLocalPlayerController()) { return; }

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
		ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (MenuMappingContext)
		{
			// Priority 1: above the pawn's context (0). Menu keys must win no
			// matter which pawn — infantry, mech, or none at all — is possessed.
			Subsystem->AddMappingContext(MenuMappingContext, 1);
		}
		else
		{
			UE_LOG(LogIronBreach, Warning,
				TEXT("%s: MenuMappingContext not assigned — menus won't open from input (MENUS_UI_WIRING.md §6)."),
				*GetName());
		}
	}
}

void AIBPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(InputComponent);
	if (!EIC)
	{
		UE_LOG(LogIronBreach, Error,
			TEXT("%s: Expected an EnhancedInputComponent. Check DefaultInputComponentClass in DefaultInput.ini"),
			*GetName());
		return;
	}

	// Guarded: BindAction on an unassigned UInputAction asserts in newer engine versions.
	if (OpenInventoryAction) { EIC->BindAction(OpenInventoryAction, ETriggerEvent::Started, this, &AIBPlayerController::OpenInventoryMenu); }
	if (OpenMapAction)       { EIC->BindAction(OpenMapAction,       ETriggerEvent::Started, this, &AIBPlayerController::OpenMapMenu); }
	if (OpenLedgerAction)    { EIC->BindAction(OpenLedgerAction,    ETriggerEvent::Started, this, &AIBPlayerController::OpenLedgerMenu); }
	if (OpenSystemAction)    { EIC->BindAction(OpenSystemAction,    ETriggerEvent::Started, this, &AIBPlayerController::OpenSystemMenu); }
}

void AIBPlayerController::ToggleMenuScreen(FName ScreenId) const
{
	const ULocalPlayer* LP = GetLocalPlayer();
	if (UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr)
	{
		Menu->ToggleScreen(ScreenId);
	}
}

void AIBPlayerController::OpenInventoryMenu() { ToggleMenuScreen(TEXT("Inventory")); }
void AIBPlayerController::OpenMapMenu()       { ToggleMenuScreen(TEXT("Map")); }
void AIBPlayerController::OpenLedgerMenu()    { ToggleMenuScreen(TEXT("Ledger")); }
void AIBPlayerController::OpenSystemMenu()    { ToggleMenuScreen(TEXT("System")); }
