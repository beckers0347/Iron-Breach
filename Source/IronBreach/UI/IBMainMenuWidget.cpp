#include "UI/IBMainMenuWidget.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBLobbyStripWidget.h"
#include "UI/IBStyleKit.h"
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
}

void UIBMainMenuWidget::EnterHostLobbyState()
{
	bHostingLobby = true;

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
	LockForTravel();
	SetStatus(FText::FromString(TEXT("DEPLOYING SOLO...")));
	UGameplayStatics::OpenLevel(this, FName(*SoloTravelURL));
}

void UIBMainMenuWidget::HandleHost()
{
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
