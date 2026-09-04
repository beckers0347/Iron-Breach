#include "UI/IBMainMenuWidget.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBLobbyStripWidget.h"
#include "UI/IBCharacterSelectScreen.h"
#include "UI/IBStyleKit.h"
#include "Player/IBCharacterSubsystem.h"
#include "Player/IBCharacterTypes.h"
#include "Items/IBPlayerState.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "IronBreach.h"
#include "Engine/LocalPlayer.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "GameFramework/PlayerController.h"

void UIBMainMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	if (Btn_Solo) Btn_Solo->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleSolo);
	if (Btn_Host) Btn_Host->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleHost);
	if (Btn_Join) Btn_Join->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleJoin);
	if (Btn_Quit) Btn_Quit->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleQuit);
	if (Btn_Settings) Btn_Settings->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleSettings);
	if (Btn_Operative) Btn_Operative->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleSwitchOperative);

	if (bApplyHouseStyle)
	{
		ApplyHouseStyle();
	}

	UIBSessionSubsystem* Sessions = GetSessions();
	if (Sessions)
	{
		Sessions->OnSessionStatusChanged.AddDynamic(this, &UIBMainMenuWidget::HandleSessionStatus);
	}

	// The squad strip lives whenever the menu does — solo it just shows your
	// own banner and three open seats (and the FRIENDS flyout).
	if (!LobbyStrip)
	{
		LobbyStrip = CreateWidget<UIBLobbyStripWidget>(GetOwningPlayer(), UIBLobbyStripWidget::StaticClass());
		if (LobbyStrip)
		{
			LobbyStrip->AddToViewport(2);
		}
	}

	// Post-travel lobby detection: this widget just spawned in a lobby world.
	const ENetMode NetMode = GetWorld() ? GetWorld()->GetNetMode() : NM_Standalone;
	if (NetMode == NM_ListenServer && Sessions && Sessions->IsInSession())
	{
		EnterHostLobbyState();
	}
	else if (NetMode == NM_Client)
	{
		EnterClientLobbyState();
	}
	else
	{
		// Standalone front end (fresh boot or a return from the world): the
		// operative sheet IS the front end — pick who deploys, and go. The
		// Solo/Host/Join menu underneath never shows; the squad forms in-world.
		OpenOperativeSelect();
	}

	RefreshOperativeLine();
	PushIdentityToPlayerState(); // lobby worlds spawn a fresh PlayerState — re-stamp it
}

void UIBMainMenuWidget::EnterHostLobbyState()
{
	bHostingLobby = true;

	// Lobby is live — operative switching closes here.
	if (Btn_Operative) { Btn_Operative->SetIsEnabled(false); }
	if (InjectedOperativeChip) { InjectedOperativeChip->SetVisibility(ESlateVisibility::Collapsed); }

	// The Host button becomes the trigger.
	if (Btn_Host)
	{
		Btn_Host->SetIsEnabled(true);
		IBStyle::StyleButton(Btn_Host, /*bAccent=*/true);
		if (UTextBlock* Label = Cast<UTextBlock>(Btn_Host->GetChildAt(0)))
		{
			Label->SetText(NSLOCTEXT("IBMenu", "Deploy", "DEPLOY SQUAD"));
			Label->SetColorAndOpacity(FSlateColor(IBStyle::Amber()));
		}
	}
	if (Btn_Join) { Btn_Join->SetIsEnabled(false); }
	if (Btn_Solo) { Btn_Solo->SetIsEnabled(false); }

	SetStatus(FText::FromString(TEXT("LOBBY LIVE — INVITE YOUR SQUAD, THEN DEPLOY")));

	// The lobby is a mouse place; make sure the cursor survived the travel.
	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(Mode);
		PC->SetShowMouseCursor(true);
	}
}

void UIBMainMenuWidget::EnterClientLobbyState()
{
	if (Btn_Operative) { Btn_Operative->SetIsEnabled(false); }
	if (InjectedOperativeChip) { InjectedOperativeChip->SetVisibility(ESlateVisibility::Collapsed); }
	if (Btn_Host) { Btn_Host->SetIsEnabled(false); }
	if (Btn_Join) { Btn_Join->SetIsEnabled(false); }
	if (Btn_Solo) { Btn_Solo->SetIsEnabled(false); }

	SetStatus(FText::FromString(TEXT("LINKED — WAITING FOR HOST TO DEPLOY")));

	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(Mode);
		PC->SetShowMouseCursor(true);
	}
}

void UIBMainMenuWidget::ApplyHouseStyle()
{
	// One pass over whatever the WBP bound: chip background + label treatment,
	// so the title buttons and the in-game screens read as one console.
	const UButton* const Buttons[] = { Btn_Solo.Get(), Btn_Host.Get(), Btn_Join.Get(), Btn_Settings.Get(), Btn_Quit.Get() };
	for (const UButton* ConstButton : Buttons)
	{
		UButton* Button = const_cast<UButton*>(ConstButton);
		if (!Button) { continue; }

		IBStyle::StyleButton(Button); // rounded chip + amber hover stroke

		if (UTextBlock* Label = Cast<UTextBlock>(Button->GetChildAt(0)))
		{
			FSlateFontInfo Font = Label->GetFont();
			Font.Size = FMath::Max(Font.Size, 19);
			Font.LetterSpacing = 250;
			Label->SetFont(Font);
			Label->SetColorAndOpacity(FSlateColor(IBStyle::TextHi()));
			Label->SetShadowOffset(FVector2D(1.f, 1.f));
			Label->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.7f));
		}
	}

	if (Txt_Status)
	{
		Txt_Status->SetColorAndOpacity(FSlateColor(IBStyle::Amber())); // amber narrator
	}
}

void UIBMainMenuWidget::HandleSettings()
{
	if (const ULocalPlayer* LP = GetOwningLocalPlayer())
	{
		if (UIBMenuSubsystem* Menu = LP->GetSubsystem<UIBMenuSubsystem>())
		{
			Menu->ToggleScreen(FName(TEXT("Settings")));
		}
	}
}

void UIBMainMenuWidget::NativeDestruct()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(IdentityRetryHandle);
	}
	CloseOperativeSelect();
	// The subsystem outlives every widget — leave no bindings behind.
	if (UIBSessionSubsystem* Sessions = GetSessions())
	{
		Sessions->OnSessionStatusChanged.RemoveDynamic(this, &UIBMainMenuWidget::HandleSessionStatus);
	}
	Super::NativeDestruct();
}

UIBSessionSubsystem* UIBMainMenuWidget::GetSessions() const
{
	UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr;
}

void UIBMainMenuWidget::HandleSolo()
{
	if (!EnsureOperativeReady()) { return; }
	LockForTravel();
	SetStatus(FText::FromString(TEXT("DEPLOYING SOLO...")));
	UGameplayStatics::OpenLevel(this, FName(*SoloTravelURL));
}

void UIBMainMenuWidget::HandleHost()
{
	if (!EnsureOperativeReady()) { return; }
	UIBSessionSubsystem* Sessions = GetSessions();
	if (!Sessions)
	{
		SetStatus(FText::FromString(TEXT("ONLINE SERVICE UNAVAILABLE")));
		return;
	}

	if (bHostingLobby)
	{
		// Second life of the button: the lobby is up, this is the trigger.
		LockForTravel();
		Sessions->IBDeploy();
		return;
	}

	LockForTravel();
	Sessions->IBHost();
}

void UIBMainMenuWidget::HandleJoin()
{
	if (!EnsureOperativeReady()) { return; }
	if (UIBSessionSubsystem* Sessions = GetSessions())
	{
		LockForTravel();
		Sessions->IBJoin();
	}
	else
	{
		SetStatus(FText::FromString(TEXT("ONLINE SERVICE UNAVAILABLE")));
	}
}

void UIBMainMenuWidget::HandleQuit()
{
	UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
}

void UIBMainMenuWidget::HandleSessionStatus(EIBSessionStatus Status, const FText& Message)
{
	SetStatus(Message);
	BP_OnSessionStatus(Status, Message);

	// Deploy-from-the-sheet: the sheet narrates every beat; the travel is
	// committed on HostLive; a dead online service still puts you in a world.
	if (bDeployPending)
	{
		switch (Status)
		{
		case EIBSessionStatus::Hosting:
			if (OperativeSelect) { OperativeSelect->SetDeploying(Message); }
			break;
		case EIBSessionStatus::HostLive:
		case EIBSessionStatus::LobbyLive:
		case EIBSessionStatus::Deploying:
			if (OperativeSelect) { OperativeSelect->SetDeploying(Message); }
			LockForTravel(); // input-mode law: GameOnly BEFORE the ServerTravel lands
			break;
		case EIBSessionStatus::Failed:
			DeploySoloFallback(FText::FromString(TEXT("BREAKWATER NET UNREACHABLE — DEPLOYING SOLO (NO DROP-IN)")));
			break;
		default:
			break;
		}
		return;
	}

	// Terminal failures hand the menu back; everything else is en route.
	switch (Status)
	{
	case EIBSessionStatus::NoneFound:
	case EIBSessionStatus::JoinFailed:
	case EIBSessionStatus::Failed:
		UnlockAfterFailure();
		break;
	default:
		break;
	}
}

void UIBMainMenuWidget::LockForTravel()
{
	SetButtonsEnabled(false);

	// Input-mode law: commit to GameOnly BEFORE any travel. UIOnly survives
	// map switches and bricks the destination level (the menu-freeze bug).
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->SetShowMouseCursor(false);
	}
}

void UIBMainMenuWidget::UnlockAfterFailure()
{
	SetButtonsEnabled(true);

	// Hand the cursor back so the player can try again.
	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(Mode);
		PC->SetShowMouseCursor(true);
	}
}

void UIBMainMenuWidget::SetButtonsEnabled(bool bEnabled)
{
	if (Btn_Solo) Btn_Solo->SetIsEnabled(bEnabled);
	if (Btn_Host) Btn_Host->SetIsEnabled(bEnabled);
	if (Btn_Join) Btn_Join->SetIsEnabled(bEnabled);
	// Quit stays live always — never trap the player in a stuck menu.
}

void UIBMainMenuWidget::SetStatus(const FText& Message)
{
	if (Txt_Status)
	{
		Txt_Status->SetText(Message);
	}
	UE_LOG(LogIronBreach, Log, TEXT("MainMenu status: %s"), *Message.ToString());
}

// ---- Operative flow (select / create / switch) ----

UIBCharacterSubsystem* UIBMainMenuWidget::GetCharacters() const
{
	UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBCharacterSubsystem>() : nullptr;
}

bool UIBMainMenuWidget::EnsureOperativeReady()
{
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters || Characters->HasActiveCharacter())
	{
		return true; // no subsystem = never block the menu
	}

	SetStatus(FText::FromString(TEXT("NO OPERATIVE ON STATION — CHOOSE ONE FIRST")));
	OpenOperativeSelect();
	return false;
}

void UIBMainMenuWidget::MaybeOpenCharacterGate()
{
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (Characters && !Characters->HasActiveCharacter())
	{
		OpenOperativeSelect();
	}
}

void UIBMainMenuWidget::OpenOperativeSelect()
{
	if (OperativeSelect) { return; }

	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters) { return; }

	OperativeSelect = CreateWidget<UIBCharacterSelectScreen>(GetOwningPlayer(), UIBCharacterSelectScreen::StaticClass());
	if (!OperativeSelect) { return; }

	// Never dismissible: there is no menu behind it any more — DEPLOY is the only way forward.
	OperativeSelect->InitSelect(false);
	OperativeSelect->OnFlowFinished.AddDynamic(this, &UIBMainMenuWidget::HandleOperativeFlowFinished);
	OperativeSelect->AddToViewport(40); // over the menu and the lobby strip

	// The front end is a mouse place; keep that true under the sheet — and hand
	// keyboard focus to the sheet so Escape/BACK reach it (menu-subsystem pattern).
	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Mode.SetWidgetToFocus(OperativeSelect->TakeWidget());
		PC->SetInputMode(Mode);
		PC->SetShowMouseCursor(true);
	}
}

void UIBMainMenuWidget::CloseOperativeSelect()
{
	if (OperativeSelect)
	{
		OperativeSelect->OnFlowFinished.RemoveDynamic(this, &UIBMainMenuWidget::HandleOperativeFlowFinished);
		OperativeSelect->RemoveFromParent(); // remove, never hide — the click-eating lesson
		OperativeSelect = nullptr;
	}
}

void UIBMainMenuWidget::HandleOperativeFlowFinished()
{
	RefreshOperativeLine();

	FIBCharacterRecord Active;
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters || !Characters->GetActiveCharacter(Active))
	{
		// Nobody chosen: the door stays shut (the sheet isn't dismissible, so
		// this is belt-and-braces).
		MaybeOpenCharacterGate();
		return;
	}

	SetStatus(FText::FromString(FString::Printf(TEXT("%s ON STATION — %s"),
		*Active.Callsign, *IBCharacter::ClassName(Active.Class).ToString())));
	PushIdentityToPlayerState();

	// The sheet stays up as the loading screen; straight into their own world.
	DeployToWorld(Active);
}

void UIBMainMenuWidget::DeployToWorld(const FIBCharacterRecord& Operative)
{
	if (bDeployPending) { return; }
	bDeployPending = true;

	const FText Status = FText::FromString(FString::Printf(TEXT("%s ON STATION — LINKING TO THE BREAKWATER NET..."), *Operative.Callsign));
	if (OperativeSelect) { OperativeSelect->SetDeploying(Status); }
	SetStatus(Status);
	SetButtonsEnabled(false);

	UIBSessionSubsystem* Sessions = GetSessions();
	if (!Sessions)
	{
		DeploySoloFallback(FText::FromString(TEXT("NO ONLINE SERVICE — DEPLOYING SOLO (NO DROP-IN)")));
		return;
	}

	// Listen-host the mission map straight away (bLobbyBeforeDeploy is off):
	// HostLive commits the travel, Failed falls back to solo — see HandleSessionStatus.
	Sessions->IBHost();
}

void UIBMainMenuWidget::DeploySoloFallback(const FText& Why)
{
	UE_LOG(LogIronBreach, Warning, TEXT("Deploy: %s"), *Why.ToString());
	if (OperativeSelect) { OperativeSelect->SetDeploying(Why); }
	SetStatus(Why);
	LockForTravel();
	UGameplayStatics::OpenLevel(this, FName(*SoloTravelURL));
}

void UIBMainMenuWidget::HandleSwitchOperative()
{
	OpenOperativeSelect();
}

void UIBMainMenuWidget::RefreshOperativeLine()
{
	FIBCharacterRecord Active;
	UIBCharacterSubsystem* Characters = GetCharacters();
	const bool bHasActive = Characters && Characters->GetActiveCharacter(Active);

	const FText Line = bHasActive
		? FText::FromString(FString::Printf(TEXT("OPERATIVE — %s · %s"),
			*Active.Callsign, *IBCharacter::ClassName(Active.Class).ToString()))
		: FText::FromString(TEXT("NO OPERATIVE ON STATION"));

	if (Txt_Operative) { Txt_Operative->SetText(Line); }
	if (InjectedOperativeText) { InjectedOperativeText->SetText(Line); }
}

void UIBMainMenuWidget::InjectOperativeChip()
{
	// Connor bound his own button: his art wins, nothing to inject.
	if (Btn_Operative || InjectedOperativeChip || !WidgetTree) { return; }

	UWidget* Root = GetRootWidget();
	if (!Root) { return; }

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	InjectedOperativeText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 300);
	if (UHorizontalBoxSlot* TextSlot = Row->AddChildToHorizontalBox(InjectedOperativeText))
	{
		TextSlot->SetVerticalAlignment(VAlign_Center);
		TextSlot->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));
	}

	UButton* Switch = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBMenu", "SwitchOperative", "SWITCH"), 10);
	Switch->OnClicked.AddDynamic(this, &UIBMainMenuWidget::HandleSwitchOperative);
	if (UHorizontalBoxSlot* SwitchSlot = Row->AddChildToHorizontalBox(Switch))
	{
		SwitchSlot->SetVerticalAlignment(VAlign_Center);
	}

	UBorder* Chip = IBStyle::MakePanel(WidgetTree, IBStyle::Panel(), 8.f);
	Chip->SetPadding(FMargin(12.f, 8.f));
	Chip->SetContent(Row);

	if (UCanvasPanel* Canvas = Cast<UCanvasPanel>(Root))
	{
		if (UCanvasPanelSlot* ChipSlot = Canvas->AddChildToCanvas(Chip))
		{
			ChipSlot->SetAnchors(FAnchors(0.f, 1.f, 0.f, 1.f));
			ChipSlot->SetAlignment(FVector2D(0.f, 1.f));
			ChipSlot->SetAutoSize(true);
			ChipSlot->SetPosition(FVector2D(28.f, -28.f));
			ChipSlot->SetZOrder(5);
			InjectedOperativeChip = Chip;
		}
	}
	else if (UOverlay* Over = Cast<UOverlay>(Root))
	{
		if (UOverlaySlot* ChipSlot = Over->AddChildToOverlay(Chip))
		{
			ChipSlot->SetHorizontalAlignment(HAlign_Left);
			ChipSlot->SetVerticalAlignment(VAlign_Bottom);
			ChipSlot->SetPadding(FMargin(28.f, 0.f, 0.f, 28.f));
			InjectedOperativeChip = Chip;
		}
	}
	else
	{
		// No canvas/overlay root to live in — the Txt_Operative/Btn_Operative
		// binds are the path on exotic layouts.
		InjectedOperativeText = nullptr;
	}
}

void UIBMainMenuWidget::PushIdentityToPlayerState()
{
	FIBCharacterRecord Active;
	UIBCharacterSubsystem* Characters = GetCharacters();
	if (!Characters || !Characters->GetActiveCharacter(Active))
	{
		return; // nobody on station (the gate is up, or this is a PIE straight-in)
	}

	// Through the PlayerState, so it works under the template controller the
	// front end runs (authority sets directly, clients Server-RPC).
	const APlayerController* PC = GetOwningPlayer();
	if (AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr)
	{
		PS->PushOperativeIdentity(Active);
		IdentityRetries = 0;
		return;
	}

	// Joining clients receive their PlayerState shortly after the widget exists.
	if (IdentityRetries++ < 20)
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(IdentityRetryHandle, this,
				&UIBMainMenuWidget::PushIdentityToPlayerState, 0.5f, false);
		}
	}
}
