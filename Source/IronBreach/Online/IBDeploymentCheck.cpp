// Opt-in integration check: -ExecCmds="IB.DeploymentCheck" from the title map.
// Uses the existing operative and real deploy buttons. Creates a host session,
// drops into Carrow Gate, returns to the Watch, and deploys again. No invites.
#include "CoreMinimal.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "Online/IBSessionSubsystem.h"
#include "Online/IBWatchTypes.h"
#include "UI/IBCharacterSelectScreen.h"
#include "UI/IBWatchScreen.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/Button.h"
#include "Containers/Ticker.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/NetDriver.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "OnlineSubsystem.h"
#include "OnlineSubsystemUtils.h"
#include "UObject/UnrealType.h"

namespace IBDeploymentCheck
{
	template<typename T> T* VisibleScreen(UWorld* World)
	{
		TArray<UUserWidget*> Widgets;
		UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, T::StaticClass(), true);
		for (UUserWidget* Widget : Widgets)
		{
			if (Widget->IsInViewport() && Widget->IsVisible()) { return Cast<T>(Widget); }
		}
		return nullptr;
	}

	static bool Click(UUserWidget* Screen, FName PropertyName)
	{
		const FObjectPropertyBase* Property = Screen ? FindFProperty<FObjectPropertyBase>(Screen->GetClass(), PropertyName) : nullptr;
		UButton* Button = Property ? Cast<UButton>(Property->GetObjectPropertyValue_InContainer(Screen)) : nullptr;
		if (!Button || !Button->GetIsEnabled() || !Button->IsVisible()) { return false; }
		Button->OnClicked.Broadcast();
		return true;
	}

	static FAutoConsoleCommandWithWorld Command(TEXT("IB.DeploymentCheck"),
		TEXT("Check operative deploy, listen lobby, Carrow Gate arrival, return and redeploy using the active online service."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* InitialWorld)
		{
			if (!InitialWorld || !InitialWorld->IsGameWorld() ||
				IBWatch::DestinationForMap(InitialWorld->GetMapName()) != TEXT("watch")) { return; }
			TWeakObjectPtr<UGameInstance> WeakGI(InitialWorld->GetGameInstance());
			// Core ticker survives the menu -> lobby -> mission world replacements.
			FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
				[WeakGI, Phase = 0, Started = FPlatformTime::Seconds(), SettledAt = 0.0](float) mutable
				{
					UGameInstance* GI = WeakGI.Get();
					UWorld* World = GI ? GI->GetWorld() : nullptr;
					if (!World) { return false; }
					const double Now = FPlatformTime::Seconds();
					if (Now - Started > 180.0)
					{
						UE_LOG(LogIronBreach, Error, TEXT("[DeploymentCheck] FAIL timeout phase=%d map=%s"), Phase, *World->GetMapName());
						return false;
					}
					if (Now - Started < 3.0) { return true; }
					UIBSessionSubsystem* Sessions = GI->GetSubsystem<UIBSessionSubsystem>();
					if (!Sessions) { return false; }
					const FName Destination = IBWatch::DestinationForMap(World->GetMapName());
					auto CheckTransport = [World, Sessions]()
					{
						const IOnlineSubsystem* OSS = Online::GetSubsystem(World);
						const bool bLAN = !OSS || OSS->GetSubsystemName() == TEXT("NULL");
						return Sessions->IsInSession() && World->GetNetMode() == NM_ListenServer &&
							World->GetNetDriver() && World->URL.HasOption(TEXT("bIsLanMatch")) == bLAN;
					};
					if (Phase == 0)
					{
						if (UIBCharacterSelectScreen* Sheet = VisibleScreen<UIBCharacterSelectScreen>(World))
						{
							if (Click(Sheet, TEXT("Btn_Deploy")))
							{
								UE_LOG(LogIronBreach, Display, TEXT("[DeploymentCheck] clicked operative DEPLOY"));
								Phase = 1;
							}
						}
						else
						{
							// The authored title screen's PRESS ANY BUTTON gate.
							FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(EKeys::SpaceBar, FModifierKeysState(), 0, false, 0, 0));
							FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(EKeys::SpaceBar, FModifierKeysState(), 0, false, 0, 0));
						}
					}
					else if (Phase == 1 || Phase == 4)
					{
						if (Destination == TEXT("watch") && CheckTransport() && VisibleScreen<UIBWatchScreen>(World))
						{
							UE_LOG(LogIronBreach, Display, TEXT("[DeploymentCheck] PASS %s url=%s driver=%s"),
								Phase == 1 ? TEXT("listen lobby and Watch") : TEXT("return to Watch"),
								*World->URL.ToString(), *World->GetNetDriver()->GetClass()->GetName());
							SettledAt = Now;
							++Phase;
						}
					}
					else if (Phase == 2 || Phase == 5)
					{
						if (Now - SettledAt > 4.0 && Click(VisibleScreen<UIBWatchScreen>(World), TEXT("PrimaryButton")))
						{
							UE_LOG(LogIronBreach, Display, TEXT("[DeploymentCheck] clicked Watch DEPLOY"));
							SettledAt = 0;
							++Phase;
						}
					}
					else if (Phase == 3 || Phase == 6)
					{
						APlayerController* PC = World->GetFirstPlayerController();
						if (Destination != TEXT("carrow_gate") || !CheckTransport() || !PC || !PC->GetPawn())
						{
							SettledAt = 0;
								return true;
							}
						if (SettledAt == 0) { SettledAt = Now; }
						if (Now - SettledAt < 8.0) { return true; }
						UE_LOG(LogIronBreach, Display, TEXT("[DeploymentCheck] PASS %s stable for 8s url=%s pawn=%s"),
							Phase == 3 ? TEXT("Carrow Gate arrival") : TEXT("Carrow Gate redeployment"),
							*World->URL.ToString(), *PC->GetPawn()->GetClass()->GetName());
						if (Phase == 6)
						{
							FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / TEXT("DeploymentFix/arrival.png"), true, false);
							UE_LOG(LogIronBreach, Display, TEXT("[DeploymentCheck] COMPLETE"));
							if (FParse::Param(FCommandLine::Get(), TEXT("IBReferenceMenusAfterDeploy")))
							{
								PC->ConsoleCommand(TEXT("IB.ReferenceMenuCheck"), true);
							}
							return false;
						}
						++Phase;
						Sessions->IBReturnToWatch();
					}
					return true;
				}), 1.0f);
		}));
}
#endif
