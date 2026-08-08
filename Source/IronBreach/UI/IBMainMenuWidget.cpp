#include "UI/IBMainMenuWidget.h"
#include "IronBreach.h"
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

	if (UIBSessionSubsystem* Sessions = GetSessions())
	{
		Sessions->OnSessionStatusChanged.AddDynamic(this, &UIBMainMenuWidget::HandleSessionStatus);
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
	if (UIBSessionSubsystem* Sessions = GetSessions())
	{
		LockForTravel();
		Sessions->IBHost();
	}
	else
	{
		SetStatus(FText::FromString(TEXT("ONLINE SERVICE UNAVAILABLE")));
	}
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
