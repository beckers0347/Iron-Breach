// Opt-in checks of actual menu controls. Does not grant items, equip gear, or deploy.
#include "CoreMinimal.h"
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBInventoryScreen.h"
#include "UI/IBMissionsScreen.h"
#include "UI/IBWatchScreen.h"
#include "UI/IBItemTileWidget.h"
#include "Online/IBWatchTypes.h"
#include "Online/IBWatchBoard.h"
#include "Player/IBOperativePreviewStage.h"
#include "Blueprint/WidgetTree.h"
#include "Components/TextBlock.h"
#include "Components/EditableTextBox.h"
#include "Components/Button.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "Framework/Application/SlateApplication.h"

namespace IBReferenceMenuCheck
{
static void Check(bool bOK, const TCHAR* Name)
{
    UE_LOG(LogIronBreach,Display,TEXT("[ReferenceMenus] %s %s"),bOK ? TEXT("PASS") : TEXT("FAIL"),Name);
}
static UButton* FindButton(UIBMenuScreen* Screen,const FString& Label)
{
    UButton* Found=nullptr;
    if (Screen && Screen->WidgetTree) Screen->WidgetTree->ForEachWidget([&](UWidget* Widget)
    {
        if (UButton* Button=Cast<UButton>(Widget))
            if (UTextBlock* Text=Cast<UTextBlock>(Button->GetContent()); Text && Text->GetText().ToString()==Label) { Found=Button; }
    });
    return Found;
}
static void Click(UIBMenuSubsystem* Menu,const TCHAR* Label)
{
    UButton* Button=FindButton(Menu ? Menu->GetActiveScreen() : nullptr,Label);
    Check(Button && Button->GetIsEnabled(),Label);
    if (Button && Button->GetIsEnabled()) { Button->OnClicked.Broadcast(); }
}
static int32 PreviewCount(UWorld* World)
{
    int32 Count=0; for (TActorIterator<AIBOperativePreviewStage> It(World); It; ++It) { ++Count; } return Count;
}
static int32 ItemCount(UIBMenuScreen* Screen)
{
    int32 Count=0;
    if (Screen) Screen->WidgetTree->ForEachWidget([&](UWidget* Widget)
    {
        if (UIBItemTileWidget* Tile=Cast<UIBItemTileWidget>(Widget); Tile && Tile->GetItem().IsValid()) { ++Count; }
    });
    return Count;
}
static FAutoConsoleCommandWithWorld Start(TEXT("IB.ReferenceMenuCheck"),TEXT("Check and capture the reference menu layouts."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
    APlayerController* PC=World ? World->GetFirstPlayerController() : nullptr;
    ULocalPlayer* LP=PC ? PC->GetLocalPlayer() : nullptr;
    UIBMenuSubsystem* Menu=LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    if (!Menu || !World->IsGameWorld()) { return; }
    TWeakObjectPtr<UIBMenuSubsystem> WeakMenu(Menu); TWeakObjectPtr<UWorld> WeakWorld(World);
    auto At=[World](float Time,TFunction<void()> Fn) { FTimerHandle Timer; World->GetTimerManager().SetTimer(Timer,FTimerDelegate::CreateLambda(MoveTemp(Fn)),Time,false); };
    auto Shot=[WeakWorld](const TCHAR* Name)
    {
        if (WeakWorld.IsValid()) { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("ReferenceMenus/after")/Name,true,false); }
    };
    At(2,[WeakMenu] { if (WeakMenu.IsValid()) { WeakMenu->OpenScreen(TEXT("Inventory")); } });
    At(5,[WeakMenu,WeakWorld,Shot]
    {
        if (!WeakMenu.IsValid() || !WeakWorld.IsValid()) { return; }
        Check(Cast<UIBInventoryScreen>(WeakMenu->GetActiveScreen())!=nullptr,TEXT("character screen opens"));
        Check(PreviewCount(WeakWorld.Get())==1,TEXT("one character capture")); Shot(TEXT("character.png"));
    });
    At(6,[WeakMenu] { Click(WeakMenu.Get(),TEXT("INVENTORY")); });
    At(8,[WeakMenu,WeakWorld,Shot]
    {
        if (!WeakMenu.IsValid() || !WeakWorld.IsValid()) { return; }
        UIBInventoryScreen* Screen=Cast<UIBInventoryScreen>(WeakMenu->GetActiveScreen());
        Check(Screen && Screen->IsBackpackTab(),TEXT("inventory is a separate tab"));
        Check(PreviewCount(WeakWorld.Get())==0,TEXT("backpack releases capture")); Shot(TEXT("inventory.png"));
    });
    At(9,[WeakMenu]
    {
        if (WeakMenu.IsValid()) if (UIBMenuScreen* Screen=WeakMenu->GetActiveScreen())
            if (UEditableTextBox* Search=Cast<UEditableTextBox>(Screen->WidgetTree->FindWidget(TEXT("InventorySearch"))))
                Search->SetText(FText::FromString(TEXT("__NO_MATCH_REFERENCE_CHECK__")));
    });
    At(10,[WeakMenu,Shot]
    {
        if (!WeakMenu.IsValid()) { return; }
        const UButton* Equip=FindButton(WeakMenu->GetActiveScreen(),TEXT("NOT EQUIPPABLE"));
        Check(Equip && !Equip->GetIsEnabled(),TEXT("empty search clears the equip action")); Shot(TEXT("inventory-empty-search.png"));
    });
    At(11,[WeakMenu]
    {
        if (WeakMenu.IsValid()) if (UIBMenuScreen* Screen=WeakMenu->GetActiveScreen())
            if (UEditableTextBox* Search=Cast<UEditableTextBox>(Screen->WidgetTree->FindWidget(TEXT("InventorySearch")))) { Search->SetText(FText::GetEmpty()); }
    });
    At(12,[WeakMenu] { Click(WeakMenu.Get(),TEXT("ARMOR")); });
    At(13,[WeakMenu]
    {
        if (!WeakMenu.IsValid()) { return; }
        UIBInventoryScreen* Screen=Cast<UIBInventoryScreen>(WeakMenu->GetActiveScreen());
        Check(Screen && !Screen->IsFilterAll() && Screen->GetCategoryFilter()==EIBItemCategory::Armor,TEXT("armor category"));
        Click(WeakMenu.Get(),TEXT("ALL ITEMS")); Click(WeakMenu.Get(),TEXT("SORT: RARITY"));
        Check(FindButton(WeakMenu->GetActiveScreen(),TEXT("SORT: NAME"))!=nullptr,TEXT("name sorting"));
        Click(WeakMenu.Get(),TEXT("SORT: NAME"));
        Check(FindButton(WeakMenu->GetActiveScreen(),TEXT("SORT: CLEARANCE"))!=nullptr,TEXT("clearance sorting"));
    });
    At(15,[WeakMenu] { Click(WeakMenu.Get(),TEXT("MISSIONS")); });
    At(17,[WeakMenu,Shot]
    {
        if (!WeakMenu.IsValid()) { return; }
        UIBMissionsScreen* Screen=Cast<UIBMissionsScreen>(WeakMenu->GetActiveScreen());
        Check(Screen && IBWatch::Find(Screen->GetSelectedDestination()),TEXT("mission reads destination registry"));
        if (Screen) { Screen->SelectDestination(TEXT("carrow_gate")); } Shot(TEXT("missions.png"));
    });
    At(18,[WeakMenu]
    {
        if (WeakMenu.IsValid()) if (UIBMissionsScreen* Screen=Cast<UIBMissionsScreen>(WeakMenu->GetActiveScreen())) { Screen->SelectDestination(TEXT("drowned_quarter")); }
    });
    At(19,[WeakMenu,Shot]
    {
        if (!WeakMenu.IsValid()) { return; }
        UIBMissionsScreen* Screen=Cast<UIBMissionsScreen>(WeakMenu->GetActiveScreen());
        const FIBDestination* D=Screen ? IBWatch::Find(Screen->GetSelectedDestination()) : nullptr;
        Check(D && !D->CanDeploy(),TEXT("locked briefing stays non-deployable")); Shot(TEXT("missions-locked.png"));
    });
    At(20,[WeakMenu] { Click(WeakMenu.Get(),TEXT("TRAINING")); });
    At(21,[WeakMenu]
    {
        if (!WeakMenu.IsValid()) { return; }
        UIBMissionsScreen* Screen=Cast<UIBMissionsScreen>(WeakMenu->GetActiveScreen());
        Check(Screen && Screen->GetSelectedDestination()==TEXT("firing_line"),TEXT("training filter selects range"));
    });
    At(22,[WeakMenu] { Click(WeakMenu.Get(),TEXT("VIEW ON WATCH  >")); });
    At(24,[WeakMenu,WeakWorld,Shot]
    {
        if (!WeakMenu.IsValid() || !WeakWorld.IsValid()) { return; }
        UIBWatchScreen* Watch=Cast<UIBWatchScreen>(WeakMenu->GetActiveScreen());
        Check(Watch && Watch->GetFocusedDestinationId()==TEXT("firing_line"),TEXT("Watch opens selected destination"));
        AIBWatchBoard* Board=AIBWatchBoard::Get(WeakWorld.Get());
        Check(!Board || !Board->IsArmed(),TEXT("browsing did not deploy")); Shot(TEXT("watch-from-missions.png"));
        WeakMenu->OpenScreen(TEXT("Missions"));
    });
    At(25,[WeakMenu] { Click(WeakMenu.Get(),TEXT("CHARACTER")); });
    At(27,[WeakMenu,WeakWorld]
    {
        if (!WeakMenu.IsValid() || !WeakWorld.IsValid()) { return; }
        Check(PreviewCount(WeakWorld.Get())==1,TEXT("return to character recreates one capture"));
        FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(EKeys::Escape,FModifierKeysState(),0,false,0,0));
        FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(EKeys::Escape,FModifierKeysState(),0,false,0,0));
    });
    At(28,[WeakMenu,WeakWorld]
    {
        if (!WeakMenu.IsValid() || !WeakWorld.IsValid()) { return; }
        Check(!WeakMenu->IsMenuOpen(),TEXT("Escape returns to game"));
        Check(PreviewCount(WeakWorld.Get())==0,TEXT("close releases character capture"));
        UE_LOG(LogIronBreach,Display,TEXT("[ReferenceMenus] COMPLETE"));
    });
    At(30,[WeakMenu] { if (WeakMenu.IsValid()) { WeakMenu->OpenScreen(TEXT("Inventory")); } });
}));
}
#endif
