// Opt-in visual and navigation checks. Never spends points, changes settings,
// deletes characters, sends invitations, or takes/stores equipment.
#include "CoreMinimal.h"
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBWatchScreen.h"
#include "UI/IBWeaponRackScreen.h"
#include "UI/IBCharacterSelectScreen.h"
#include "UI/IBCharacterCreateScreen.h"
#include "UI/IBPlayerBannerWidget.h"
#include "UI/IBItemTileWidget.h"
#include "Player/IBUserSettings.h"
#include "Player/IBCharacterSubsystem.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/PanelWidget.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "Framework/Application/SlateApplication.h"

namespace IBMenuConsistencyCheck
{
static void Check(bool OK, const FString& What)
{
    UE_LOG(LogIronBreach, Display, TEXT("[MenuConsistency] %s %s"), OK ? TEXT("PASS") : TEXT("FAIL"), *What);
}
static UButton* Button(UUserWidget* Screen, const FString& Label)
{
    UButton* Found = nullptr;
    if (Screen && Screen->WidgetTree) Screen->WidgetTree->ForEachWidget([&](UWidget* W)
    {
        if (UTextBlock* Text = Cast<UTextBlock>(W); Text && Text->GetText().ToString() == Label)
        {
            for (UPanelWidget* Parent = Text->GetParent(); Parent; Parent = Parent->GetParent())
                if (UButton* B = Cast<UButton>(Parent)) { Found = B; break; }
        }
    });
    return Found;
}
static void Click(UUserWidget* Screen, const FString& Label)
{
    UButton* B = Button(Screen, Label);
    Check(B && B->GetIsEnabled(), TEXT("button: ") + Label);
    if (B && B->GetIsEnabled()) { B->OnClicked.Broadcast(); }
}
static void Key(FKey Value)
{
    FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
    FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
}
template<class T> static T* Visible(UWorld* World)
{
    TArray<UUserWidget*> All;
    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, All, T::StaticClass(), false);
    for (UUserWidget* W : All) if (W->IsVisible() && (W->IsInViewport() || W->GetParent())) { return Cast<T>(W); }
    return nullptr;
}
static void Shot(const TCHAR* Name)
{
    FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("MenuConsistency/after")/Name, true, false);
}
static FAutoConsoleCommandWithWorld Start(TEXT("IB.MenuConsistencyCheck"), TEXT("Capture remaining menu screens and check navigation."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
    APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
    ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
    UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    if (!Menu || !World->IsGameWorld()) { return; }
    TWeakObjectPtr<UIBMenuSubsystem> M(Menu); TWeakObjectPtr<UWorld> W(World);
    auto At = [World](float Time, TFunction<void()> Fn) { FTimerHandle T; World->GetTimerManager().SetTimer(T, FTimerDelegate::CreateLambda(MoveTemp(Fn)), Time, false); };
    auto Open = [M](const TCHAR* Id) { if (M.IsValid()) { M->OpenScreen(Id); } };
    At(2, [Open] { Open(TEXT("Ledger")); });
    At(4, [M] { Check(M.IsValid() && Button(M->GetActiveScreen(), TEXT("CHARACTER")), TEXT("Ledger shared navigation")); Shot(TEXT("ledger.png")); });
    At(5, [M] { if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("ARMOR")); } });
    At(6, [] { Shot(TEXT("ledger-filter.png")); });
    At(7, [M] { if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("DIRECTOR  [B]")); } });
    At(8, [M] { if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("MAP")); } });
    At(9, [M] { Check(M.IsValid() && M->GetActiveScreenId()==TEXT("Map"), TEXT("Map navigation")); Shot(TEXT("map.png")); });
    At(10, [Open] { Open(TEXT("System")); });
    At(12, [M] { Check(M.IsValid() && Button(M->GetActiveScreen(), TEXT("CHARACTER  [I]")), TEXT("System preserves Director header")); Shot(TEXT("system.png")); });
    At(13, [M] { if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("QUIT TO DESKTOP")); } });
    At(14, [M] { Check(M.IsValid() && Button(M->GetActiveScreen(), TEXT("CONFIRM — QUIT?")), TEXT("Quit requires confirmation")); Shot(TEXT("quit-confirm.png")); });
    At(15, [M] { if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("RESUME")); } });
    At(16, [M,Open] { Check(M.IsValid() && !M->IsMenuOpen(), TEXT("Resume closes menu")); Open(TEXT("System")); });
    At(17, [M] { Check(M.IsValid() && Button(M->GetActiveScreen(), TEXT("QUIT TO DESKTOP")), TEXT("Quit disarms on reopen")); if (M.IsValid()) { Click(M->GetActiveScreen(), TEXT("SETTINGS")); } });
    At(19, [M] { Check(M.IsValid() && M->GetActiveScreenId()==TEXT("Settings"), TEXT("Settings opens")); Shot(TEXT("settings.png")); });
    At(20, [] { Key(EKeys::Escape); });
    At(21, [M,Open] { Check(M.IsValid() && !M->IsMenuOpen(), TEXT("Escape closes Settings")); Open(TEXT("Squad")); });
    At(23, [] { Shot(TEXT("squad.png")); });
    At(24, [M]
    {
        if (!M.IsValid() || !M->GetActiveScreen()) { return; }
        bool Opened = false;
        M->GetActiveScreen()->WidgetTree->ForEachWidget([&](UWidget* Widget)
        {
            if (UIBPlayerBannerWidget* Banner=Cast<UIBPlayerBannerWidget>(Widget); Banner && !Opened)
            { Banner->OnInviteClicked.Broadcast(Banner); Opened = true; }
        });
        Check(Opened, TEXT("Squad opens social flyout"));
    });
    At(26, [] { Shot(TEXT("friends.png")); });
    At(27, [Open] { Open(TEXT("Watch")); });
    At(29, [] { Shot(TEXT("watch-orbit.png")); });
    At(30, [M] { if (M.IsValid()) if (UIBWatchScreen* S=Cast<UIBWatchScreen>(M->GetActiveScreen())) { S->FocusDestination(TEXT("carrow_gate")); } });
    At(33, [] { Shot(TEXT("watch-board.png")); });
    At(34, [M,W]
    {
        if (!M.IsValid() || !W.IsValid()) { return; }
        M->CloseMenu();
        UIBWeaponRackScreen* Rack=CreateWidget<UIBWeaponRackScreen>(W->GetFirstPlayerController(),UIBWeaponRackScreen::StaticClass());
        Rack->AddToViewport(110); Rack->SetKeyboardFocus();
    });
    At(36, [] { Shot(TEXT("weapon-rack.png")); });
    At(37, [W] { if (W.IsValid()) { Click(Visible<UIBWeaponRackScreen>(W.Get()), TEXT("CLOSE (ESC)")); } });
    At(38, [M,W]
    {
        if (M.IsValid()) { M->OpenScreen(TEXT("Inventory")); }
        Check(true,TEXT("COMPLETE"));
        if (W.IsValid() && FParse::Param(FCommandLine::Get(),TEXT("IBMenuFlowAfterMenus")))
        { W->GetFirstPlayerController()->ConsoleCommand(TEXT("IB.MenuFlowCheck"),true); }
        else if (W.IsValid() && FParse::Param(FCommandLine::Get(),TEXT("IBSkillsAfterMenus")))
        { W->GetFirstPlayerController()->ConsoleCommand(TEXT("IB.SkillsCheck"),true); }
    });
}));

static FAutoConsoleCommandWithWorld Frontend(TEXT("IB.FrontendStyleCheck"), TEXT("Inspect title, operative selection and creation without saving."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
    if (!World || !World->IsGameWorld()) { return; }
    TWeakObjectPtr<UWorld> W(World);
    const TSharedRef<bool> TriedCreation = MakeShared<bool>(false);
    auto At = [World](float Time, TFunction<void()> Fn) { FTimerHandle T; World->GetTimerManager().SetTimer(T, FTimerDelegate::CreateLambda(MoveTemp(Fn)), Time, false); };
    At(3, [] { Shot(TEXT("title.png")); });
    At(4, [] { Key(EKeys::SpaceBar); });
    At(7, [W] { Check(W.IsValid() && Visible<UIBCharacterSelectScreen>(W.Get()),TEXT("operative selection")); Shot(TEXT("operative-select.png")); });
    At(8, [W,TriedCreation]
    {
        if (!W.IsValid()) { return; }
        UIBCharacterSubsystem* Roster = W->GetGameInstance()->GetSubsystem<UIBCharacterSubsystem>();
        Check(Roster != nullptr,TEXT("operative roster available"));
        if (!Roster) { return; }
        *TriedCreation = Roster->CanCreateCharacter();
        if (*TriedCreation) { Click(Visible<UIBCharacterSelectScreen>(W.Get()), TEXT("NEW OPERATIVE")); }
        else { Check(Button(Visible<UIBCharacterSelectScreen>(W.Get()),TEXT("NEW OPERATIVE")) == nullptr,TEXT("full roster omits new operative action")); }
    });
    At(11, [W,TriedCreation]
    {
        if (*TriedCreation) { Check(W.IsValid() && Visible<UIBCharacterCreateScreen>(W.Get()),TEXT("operative creation")); Shot(TEXT("operative-create.png")); }
        else { Check(W.IsValid() && !Visible<UIBCharacterCreateScreen>(W.Get()),TEXT("full roster remains on selection")); }
    });
    At(12, [TriedCreation] { if (*TriedCreation) { Key(EKeys::Escape); } });
    At(14, [W] { Check(W.IsValid() && !Visible<UIBCharacterCreateScreen>(W.Get()),TEXT("creation cancel")); Shot(TEXT("operative-return.png")); });
    At(16, [W] { if (W.IsValid() && W->GetFirstPlayerController()) { W->GetFirstPlayerController()->ConsoleCommand(TEXT("IB.DeploymentCheck"),true); } });
}));
}
#endif
