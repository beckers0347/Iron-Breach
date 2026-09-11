// Opt-in development QA: -ExecCmds="DisableAllScreenMessages,IB.MenuTour"
// Opens registered screens, captures settled frames, and checks UI navigation.
// No inventory grants, save changes, travel, online requests, or settings writes.
#include "CoreMinimal.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBInventoryScreen.h"
#include "UI/IBItemTileWidget.h"
#include "UI/IBMenuNavButton.h"
#include "Player/IBOperativePreviewStage.h"
#include "Kismet/GameplayStatics.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "Framework/Application/SlateApplication.h"

namespace IBMenuVisualTour
{
	static UIBMenuScreen* Active(UWorld* World)
	{
		TArray<UUserWidget*> Screens;
		UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Screens, UIBMenuScreen::StaticClass(), true);
		for (UUserWidget* Widget : Screens)
			if (UIBMenuScreen* Screen = Cast<UIBMenuScreen>(Widget); Screen && Screen->IsInViewport()) { return Screen; }
		return nullptr;
	}
	static void Key(FKey Value)
	{
		FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
		FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
	}
	static void Check(UIBMenuSubsystem* Menu, FName Expected, const TCHAR* Case)
	{
		const bool bOK = Menu && Menu->GetActiveScreenId() == Expected;
		UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s %s (screen=%s)"), bOK ? TEXT("PASS") : TEXT("FAIL"), Case,
			Menu ? *Menu->GetActiveScreenId().ToString() : TEXT("missing"));
	}
	static void CheckPreview(UWorld* World, int32 Expected)
	{
		TArray<AActor*> Stages;
		UGameplayStatics::GetAllActorsOfClass(World, AIBOperativePreviewStage::StaticClass(), Stages);
		UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s preview lifecycle (%d stages, expected %d)"),
			Stages.Num() == Expected ? TEXT("PASS") : TEXT("FAIL"), Stages.Num(), Expected);
	}
	static FAutoConsoleCommandWithWorld Start(TEXT("IB.MenuTour"), TEXT("Capture and check the in-game menu presentation."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
		{
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
			UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
			if (!Menu || !World->IsGameWorld()) { return; }
			TWeakObjectPtr<UIBMenuSubsystem> WeakMenu(Menu);
			TWeakObjectPtr<UWorld> WeakWorld(World);
			auto At = [World](float Time, TFunction<void()> Action)
			{
				FTimerHandle Handle;
				World->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda(MoveTemp(Action)), Time, false);
			};
			auto Open = [WeakMenu](const TCHAR* Id) { if (WeakMenu.IsValid()) { WeakMenu->OpenScreen(FName(Id)); } };
			auto Shot = [WeakWorld, WeakMenu](const TCHAR* Name)
			{
				if (!WeakWorld.IsValid()) { return; }
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
				{
					UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] CAPTURE %s class=%s"), Name, *Screen->GetClass()->GetPathName());
					Screen->WidgetTree->ForEachWidgetAndDescendants([](UWidget* Widget)
					{
						if (UTextBlock* Text = Cast<UTextBlock>(Widget); Text && Text->IsVisible() && !Text->GetText().IsEmpty())
						{
							const FVector2D Size = Text->GetCachedGeometry().GetLocalSize();
							UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] TEXT %s [%.0fx%.0f]"), *Text->GetText().ToString().Replace(TEXT("\n"), TEXT(" / ")), Size.X, Size.Y);
						}
					});
				}
				FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / TEXT("MenuPolish/after") / FString(Name), true, false);
			};
			At(2, [Open] { Open(TEXT("Inventory")); });
			At(4, [Shot] { Shot(TEXT("01-inventory.png")); });
			At(5, [Open] { Open(TEXT("Ledger")); });
			At(7, [Shot] { Shot(TEXT("02-ledger.png")); });
			At(8, [WeakWorld]
			{
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
				{
					bool bHovered = false;
					Screen->WidgetTree->ForEachWidget([&bHovered](UWidget* Widget)
					{
						if (UIBItemTileWidget* Tile = Cast<UIBItemTileWidget>(Widget); Tile && !bHovered)
						{
							Tile->OnTileHoverChanged.Broadcast(Tile, true);
							bHovered = true;
						}
					});
				}
			});
			At(9, [Shot] { Shot(TEXT("03-ledger-inspect.png")); });
			At(10, [Open] { Open(TEXT("Map")); });
			At(12, [Shot] { Shot(TEXT("04-map.png")); });
			At(13, [Open] { Open(TEXT("System")); });
			At(15, [Shot] { Shot(TEXT("05-system.png")); });
			At(16, [Open] { Open(TEXT("Settings")); });
			At(18, [Shot] { Shot(TEXT("06-settings.png")); });
			At(19, [Open] { Open(TEXT("Inventory")); });
			At(19.5f, [] { Key(EKeys::Right); });
			At(20, [WeakWorld]
			{
				if (UIBInventoryScreen* Screen = Cast<UIBInventoryScreen>(Active(WeakWorld.Get())))
				{
					UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s Right opens Backpack"), Screen->IsBackpackTab() ? TEXT("PASS") : TEXT("FAIL"));
					CheckPreview(WeakWorld.Get(), 0);
					Screen->SetCategoryFilter(EIBItemCategory::Armor);
					UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s armor filter"), !Screen->IsFilterAll() && Screen->GetCategoryFilter() == EIBItemCategory::Armor ? TEXT("PASS") : TEXT("FAIL"));
				}
			});
			At(21, [Shot] { Shot(TEXT("07-inventory-filter.png")); });
			At(22, [WeakWorld]
			{
				if (UIBInventoryScreen* Screen = Cast<UIBInventoryScreen>(Active(WeakWorld.Get())))
				{
					Screen->SetFilterAll();
					UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s all filter"), Screen->IsFilterAll() ? TEXT("PASS") : TEXT("FAIL"));
				}
				Key(EKeys::E);
			});
			At(23, [WeakMenu] { Check(WeakMenu.Get(), TEXT("Ledger"), TEXT("E cycles to Ledger")); Key(EKeys::Q); });
			At(24, [WeakMenu] { Check(WeakMenu.Get(), TEXT("Inventory"), TEXT("Q cycles to Inventory")); Key(EKeys::Escape); });
			At(25, [WeakMenu] { Check(WeakMenu.Get(), NAME_None, TEXT("Escape closes menu")); });
			At(26, [Open] { Open(TEXT("System")); });
			At(27, [WeakWorld]
			{
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
				{
					// First click only: exercise the existing confirmation without quitting.
					Screen->WidgetTree->ForEachWidget([](UWidget* Widget)
					{
						if (UButton* Button = Cast<UButton>(Widget))
							if (const UTextBlock* Text = Cast<UTextBlock>(Button->GetContent()); Text && Text->GetText().ToString() == TEXT("QUIT TO DESKTOP"))
								Button->OnClicked.Broadcast();
					});
				}
			});
			At(28, [Shot] { Shot(TEXT("08-quit-confirm.png")); });
			At(29, [Open] { Open(TEXT("Inventory")); });
			At(30, [Open] { Open(TEXT("System")); });
			At(31, [Shot] { Shot(TEXT("09-quit-reset.png")); });
			At(32, [Open] { Open(TEXT("Inventory")); Key(EKeys::Left); });
			At(34, [Shot, WeakWorld]
			{
				CheckPreview(WeakWorld.Get(), 1);
				Shot(TEXT("10-character-reopened.png"));
			});
			At(35, [WeakWorld]
			{
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
					Screen->WidgetTree->ForEachWidget([](UWidget* Widget)
					{
						if (UButton* Button = Cast<UButton>(Widget))
							if (const UTextBlock* Text = Cast<UTextBlock>(Button->GetContent()); Text && Text->GetText().ToString() == TEXT("INVENTORY"))
								Button->OnClicked.Broadcast();
					});
			});
			At(36, [Shot, WeakWorld]
			{
				if (const UIBInventoryScreen* Screen = Cast<UIBInventoryScreen>(Active(WeakWorld.Get())))
					UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] %s Backpack tab click"), Screen->IsBackpackTab() ? TEXT("PASS") : TEXT("FAIL"));
				CheckPreview(WeakWorld.Get(), 0);
				Shot(TEXT("11-backpack.png"));
			});
			At(37, [WeakWorld]
			{
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
				{
					bool bFound = false;
					Screen->WidgetTree->ForEachWidget([&bFound](UWidget* Widget)
					{
						if (UIBItemTileWidget* Tile = Cast<UIBItemTileWidget>(Widget); Tile && Tile->GetDefinition() && !bFound)
						{
							Tile->OnTileHoverChanged.Broadcast(Tile, true);
							bFound = true;
						}
					});
				}
			});
			At(38, [Shot] { Shot(TEXT("12-backpack-inspect.png")); });
			At(39, [WeakWorld]
			{
				if (UIBMenuScreen* Screen = Active(WeakWorld.Get()))
					Screen->WidgetTree->ForEachWidget([](UWidget* Widget)
					{
						if (UIBMenuNavButton* Button = Cast<UIBMenuNavButton>(Widget))
							if (const UTextBlock* Text = Cast<UTextBlock>(Button->GetContent()); Text && Text->GetText().ToString() == TEXT("LEDGER"))
								Button->OnClicked.Broadcast();
					});
			});
			At(40, [WeakMenu] { Check(WeakMenu.Get(), TEXT("Ledger"), TEXT("navigation tab click")); Key(EKeys::Escape); });
			At(41, [WeakMenu, WeakWorld]
			{
				Check(WeakMenu.Get(), NAME_None, TEXT("Escape after mouse tab navigation"));
				CheckPreview(WeakWorld.Get(), 0);
				UE_LOG(LogIronBreach, Display, TEXT("[MenuTour] COMPLETE"));
			});
		}));
}
#endif
