#include "Player/IBPlayerController.h"
#include "IronBreach.h"
#include "Player/IBCharacterSubsystem.h"
#include "Items/IBPlayerState.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBObjectiveWidget.h"
#include "UI/IBLootToastWidget.h"
#include "Blueprint/UserWidget.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h" // Explicit include: ULocalPlayer::GetSubsystem under IWYU
#include "InputMappingContext.h"

void AIBPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// Local players only — a server-side proxy controller has no input stack.
	if (!IsLocalPlayerController()) { return; }

	// Whoever this player brought through operative select rides along into
	// every level (menu lobby, Carrow, the raid) via the PlayerState.
	PushOperativeIdentity();

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

	// HUD layer: objective banner + loot toasts. C++ classes as the floor so
	// they exist in every build; assign WBP children in the BP to reskin.
	{
		UClass* ObjectiveClass = ObjectiveWidgetClass ? *ObjectiveWidgetClass : UIBObjectiveWidget::StaticClass();
		ObjectiveWidget = CreateWidget<UIBObjectiveWidget>(this, ObjectiveClass);
		if (ObjectiveWidget) { ObjectiveWidget->AddToViewport(5); }

		UClass* ToastClass = LootToastWidgetClass ? *LootToastWidgetClass : UIBLootToastWidget::StaticClass();
		LootToastWidget = CreateWidget<UIBLootToastWidget>(this, ToastClass);
		if (LootToastWidget) { LootToastWidget->AddToViewport(6); }
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

	// Raw floor: Escape ALWAYS raises the System menu in-game — any pawn, any
	// map, even if IMC_Menus / the IA assets aren't wired there (the packaged
	// zero-content rule; "Esc quits and there's no way out" must never recur).
	// Safe alongside OpenSystemAction: the menu subsystem debounces the toggle.
	// NB: through the BASE UInputComponent pointer — UEnhancedInputComponent
	// deletes BindKey on the derived type (the infantry's raw binds work the
	// same way).
	InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &AIBPlayerController::OpenSystemMenu);
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

// ---- Operative identity ----

void AIBPlayerController::PushOperativeIdentity()
{
	if (!IsLocalPlayerController()) { return; }

	const UGameInstance* GI = GetGameInstance();
	const UIBCharacterSubsystem* Characters = GI ? GI->GetSubsystem<UIBCharacterSubsystem>() : nullptr;

	FIBCharacterRecord Active;
	if (!Characters || !Characters->GetActiveCharacter(Active))
	{
		return; // nobody on station yet (PIE straight into a level, or pre-select)
	}

	// The PlayerState owns the wire path (direct on authority, Server RPC on clients).
	if (AIBPlayerState* PS = GetPlayerState<AIBPlayerState>())
	{
		PS->PushOperativeIdentity(Active);
	}
}

void AIBPlayerController::OnRep_PlayerState()
{
	Super::OnRep_PlayerState();
	PushOperativeIdentity();
}
