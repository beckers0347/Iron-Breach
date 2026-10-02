// Opt-in, bounded UI regression check: IB.MenuFlowCheck in a standalone game.
// Sends real Slate mouse/key events; never grants, equips, saves, or deploys.
// Temporarily checks two window sizes, restores the original size/mode, and
// leaves Watch open. Screenshots: Saved/MenuFlow/after.
#include "CoreMinimal.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBInventoryScreen.h"
#include "UI/IBWatchScreen.h"
#include "Online/IBWatchBoard.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/Button.h"
#include "Components/PanelWidget.h"
#include "Components/TextBlock.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealEngine.h"
#include "UnrealClient.h"
#include "Framework/Application/SlateApplication.h"
#include "Layout/WidgetPath.h"
#include "Widgets/SWindow.h"

namespace IBMenuFlowCheck
{
struct FRun
{
    TWeakObjectPtr<UIBMenuSubsystem> Menu;
    TWeakObjectPtr<UWorld> World;
    int32 Passed = 0;
    int32 Failed = 0;

    void Check(bool bOK, const FString& What)
    {
        bOK ? ++Passed : ++Failed;
        UE_LOG(LogIronBreach, Display, TEXT("[MenuFlow] %s %s"), bOK ? TEXT("PASS") : TEXT("FAIL"), *What);
    }

    UButton* Button(const FString& Label) const
    {
        UIBMenuScreen* Screen = Menu.IsValid() ? Menu->GetActiveScreen() : nullptr;
        UButton* Found = nullptr;
        if (Screen && Screen->WidgetTree) Screen->WidgetTree->ForEachWidget([&](UWidget* Widget)
        {
            if (UTextBlock* Text = Cast<UTextBlock>(Widget); Text && Text->GetText().ToString() == Label)
            {
                for (UPanelWidget* Parent = Text->GetParent(); Parent; Parent = Parent->GetParent())
                    if (UButton* Candidate = Cast<UButton>(Parent)) { Found = Candidate; break; }
            }
        });
        return Found;
    }

    void Click(const TCHAR* Label)
    {
        UButton* Target = Button(Label);
        const TSharedPtr<SWidget> SlateButton = Target ? Target->GetCachedWidget() : nullptr;
        Check(Target && Target->GetIsEnabled() && SlateButton.IsValid(), FString(TEXT("mouse target: ")) + Label);
        if (!Target || !Target->GetIsEnabled() || !SlateButton.IsValid()) { return; }

        const FGeometry& Geometry = Target->GetCachedGeometry();
        const FVector2D Point = Geometry.LocalToAbsolute(Geometry.GetLocalSize() * .5f);
        FSlateApplication& Slate = FSlateApplication::Get();
        const FWidgetPath HitPath = Slate.LocateWindowUnderMouse(Point, Slate.GetInteractiveTopLevelWindows());
        const bool bHitsTarget = HitPath.ContainsWidget(SlateButton.Get());
        Check(bHitsTarget, FString(TEXT("visible hit target: ")) + Label);
        if (!bHitsTarget) { return; }

        const TSharedPtr<SWindow> Window = Slate.FindWidgetWindow(SlateButton.ToSharedRef());
        if (!Window.IsValid()) { Check(false, TEXT("target window exists")); return; }
        const FVector2D Previous = Slate.GetCursorPos();
        const TSet<FKey> Released;
        const TSet<FKey> Pressed = { EKeys::LeftMouseButton };
        Slate.SetCursorPos(Point);
        Slate.ProcessMouseMoveEvent(FPointerEvent(0, Point, Previous, Released, EKeys::Invalid, 0.f, FModifierKeysState()));
        Slate.ProcessMouseButtonDownEvent(Window->GetNativeWindow(), FPointerEvent(0, Point, Point, Pressed, EKeys::LeftMouseButton, 0.f, FModifierKeysState()));
        Slate.ProcessMouseButtonUpEvent(FPointerEvent(0, Point, Point, Released, EKeys::LeftMouseButton, 0.f, FModifierKeysState()));
    }

    void Key(FKey Value, bool bRequireOpenMenu = true)
    {
        if (!Menu.IsValid() || (bRequireOpenMenu && !Menu->IsMenuOpen())) { Check(false, TEXT("menu available for key input")); return; }
        FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
        FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
    }

    bool Is(FName Expected) const
    {
        if (!Menu.IsValid()) { return false; }
        if (Expected == TEXT("Character") || Expected == TEXT("Backpack"))
        {
            const UIBInventoryScreen* Inventory = Cast<UIBInventoryScreen>(Menu->GetActiveScreen());
            return Inventory && Inventory->IsBackpackTab() == (Expected == TEXT("Backpack"));
        }
        return Menu->GetActiveScreenId() == Expected;
    }

    void Expect(FName Expected, const TCHAR* What) { Check(Is(Expected), What); }

    void CheckGroup(bool bDirector)
    {
        const TCHAR* Personal[] = { TEXT("CHARACTER"), TEXT("INVENTORY"), TEXT("MECH"), TEXT("SKILLS"), TEXT("LEDGER") };
        const TCHAR* Director[] = { TEXT("WATCH"), TEXT("MAP"), TEXT("MISSIONS"), TEXT("SQUAD") };
        for (const TCHAR* Label : Personal)
            Check((Button(Label) != nullptr) == !bDirector, FString(bDirector ? TEXT("Director excludes ") : TEXT("Personal includes ")) + Label);
        for (const TCHAR* Label : Director)
            Check((Button(Label) != nullptr) == bDirector, FString(bDirector ? TEXT("Director includes ") : TEXT("Personal excludes ")) + Label);
        Check(Button(bDirector ? TEXT("CHARACTER  [I]") : TEXT("DIRECTOR  [B]")) != nullptr, TEXT("other menu group has an explicit link"));
    }

    void Shot(const TCHAR* Name)
    {
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / TEXT("MenuFlow/after") / Name, true, false);
    }

    void CheckWatchGeometry(FIntPoint ExpectedSize)
    {
        UWorld* CurrentWorld = World.Get();
        UIBWatchScreen* Watch = Menu.IsValid() ? Cast<UIBWatchScreen>(Menu->GetActiveScreen()) : nullptr;
        Check(Watch && CurrentWorld && CurrentWorld->GetGameViewport(), TEXT("Watch present for geometry check"));
        if (!Watch || !CurrentWorld || !CurrentWorld->GetGameViewport()) { return; }
        FViewport* Viewport = CurrentWorld->GetGameViewport()->Viewport;
        Check(Viewport && Viewport->GetSizeXY() == ExpectedSize, FString::Printf(TEXT("viewport is %dx%d"), ExpectedSize.X, ExpectedSize.Y));
        const FGeometry View = UWidgetLayoutLibrary::GetViewportWidgetGeometry(CurrentWorld);
        const FVector2D TopLeft = View.LocalToAbsolute(FVector2D::ZeroVector);
        const FVector2D BottomRight = View.LocalToAbsolute(View.GetLocalSize());
        for (const FName Name : { FName(TEXT("DirectorScene")), FName(TEXT("WatchPlanet")) })
        {
            const UWidget* Widget = Watch->WidgetTree->FindWidget(Name);
            Check(Widget != nullptr, FString(TEXT("full screen widget exists: ")) + Name.ToString());
            if (!Widget) { continue; }
            const FGeometry& Geometry = Widget->GetCachedGeometry();
            const FVector2D Start = Geometry.LocalToAbsolute(FVector2D::ZeroVector);
            const FVector2D End = Geometry.LocalToAbsolute(Geometry.GetLocalSize());
            Check(Start.Equals(TopLeft, 2.f) && End.Equals(BottomRight, 2.f), FString::Printf(
                TEXT("%s reaches all viewport edges (%0.0f,%0.0f)-(%0.0f,%0.0f), viewport (%0.0f,%0.0f)-(%0.0f,%0.0f)"),
                *Name.ToString(), Start.X, Start.Y, End.X, End.Y, TopLeft.X, TopLeft.Y, BottomRight.X, BottomRight.Y));
        }
        const UWidget* Deploy = Watch->WidgetTree->FindWidget(TEXT("WatchDeployButton"));
        Check(Deploy != nullptr, TEXT("deployment action has stable geometry"));
        if (Deploy)
        {
            const FGeometry& Geometry = Deploy->GetCachedGeometry();
            const FVector2D Start = Geometry.LocalToAbsolute(FVector2D::ZeroVector);
            const FVector2D End = Geometry.LocalToAbsolute(Geometry.GetLocalSize());
            Check(End.X > Start.X && End.Y > Start.Y && Start.X >= TopLeft.X && Start.Y >= TopLeft.Y &&
                End.X <= BottomRight.X + 2.f && End.Y <= BottomRight.Y + 2.f, TEXT("deployment action fits inside viewport"));
            const UWidget* Briefing = Watch->WidgetTree->FindWidget(TEXT("WatchBriefingPanel"));
            Check(Briefing != nullptr, TEXT("briefing panel has stable geometry"));
            if (Briefing)
            {
                const FGeometry& Card = Briefing->GetCachedGeometry();
                const FVector2D CardStart = Card.LocalToAbsolute(FVector2D::ZeroVector);
                const FVector2D CardEnd = Card.LocalToAbsolute(Card.GetLocalSize());
                Check(Start.X >= CardStart.X - 2.f && Start.Y >= CardStart.Y - 2.f &&
                    End.X <= CardEnd.X + 2.f && End.Y <= CardEnd.Y + 2.f, TEXT("deployment action stays inside its briefing panel"));
            }
        }
    }
};

static TWeakObjectPtr<UWorld> RunningWorld;
static FAutoConsoleCommandWithWorld Start(TEXT("IB.MenuFlowCheck"), TEXT("Check real single-click navigation, separate tab rings, and full screen Watch at two sizes."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
    APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
    ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
    UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    if (!Menu || !World->IsGameWorld() || !FSlateApplication::IsInitialized() || RunningWorld.IsValid()) { return; }
    if (World->WorldType == EWorldType::PIE)
    {
        UE_LOG(LogIronBreach, Warning, TEXT("[MenuFlow] Run in a standalone game; this check temporarily resizes its window."));
        return;
    }
    RunningWorld = World;
    const TSharedRef<FRun> Run = MakeShared<FRun>();
    Run->Menu = Menu; Run->World = World;
    const FSystemResolution OriginalResolution = GSystemResolution;
    const FVector2D OriginalCursor = FSlateApplication::Get().GetCursorPos();
    auto At = [World](float Time, TFunction<void()> Action)
    {
        FTimerHandle Timer;
        World->GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateLambda(MoveTemp(Action)), Time, false);
    };
    FSystemResolution::RequestResolutionChange(1280, 720, EWindowMode::Windowed);
    Menu->OpenScreen(TEXT("Character"));
    At(3, [Run] { Run->Expect(TEXT("Character"), TEXT("Character opens directly")); Run->CheckGroup(false); Run->Click(TEXT("INVENTORY")); });
    At(4, [Run] { Run->Expect(TEXT("Backpack"), TEXT("one mouse click selects Inventory")); Run->Click(TEXT("CHARACTER")); });
    At(5, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click returns to Character")); Run->Click(TEXT("SKILLS")); });
    At(6, [Run] { Run->Expect(TEXT("Skills"), TEXT("one mouse click opens Skills")); Run->Click(TEXT("CHARACTER")); });
    At(7, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click reopens cached Character")); Run->Shot(TEXT("character-1280x720.png")); });
    At(8, [Run]
    {
        Run->Click(TEXT("DIRECTOR  [B]"));
        // Prior checks may have left Watch on its sector board. Settle the
        // globe view for comparable fullscreen screenshots in either context.
        if (Run->Menu.IsValid()) if (UIBWatchScreen* Watch = Cast<UIBWatchScreen>(Run->Menu->GetActiveScreen())) { Watch->DevOpenOrbit(); }
    });
    At(9, [Run] { Run->Expect(TEXT("Watch"), TEXT("one mouse click switches to Director")); Run->CheckGroup(true); Run->CheckWatchGeometry(FIntPoint(1280, 720)); });
    At(9.8f, [Run] { Run->Shot(TEXT("watch-1280x720.png")); });
    At(10, [Run] { Run->Key(EKeys::Q); });
    At(11, [Run] { Run->Expect(TEXT("Squad"), TEXT("Director Q wraps Watch to Squad")); Run->Key(EKeys::E); });
    At(12, [Run] { Run->Expect(TEXT("Watch"), TEXT("Director E wraps Squad to Watch")); Run->Key(EKeys::E); });
    At(13, [Run] { Run->Expect(TEXT("Map"), TEXT("Director E visits Map")); Run->Key(EKeys::E); });
    At(14, [Run] { Run->Expect(TEXT("Missions"), TEXT("Director E visits Missions")); Run->Key(EKeys::E); });
    At(15, [Run] { Run->Expect(TEXT("Squad"), TEXT("Director E visits Squad")); Run->Key(EKeys::E); });
    At(16, [Run] { Run->Expect(TEXT("Watch"), TEXT("Director cycle stays within its four pages")); Run->Click(TEXT("CHARACTER  [I]")); });
    At(17, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click switches to Personal")); Run->Key(EKeys::Q); });
    At(18, [Run] { Run->Expect(TEXT("Ledger"), TEXT("Personal Q wraps Character to Ledger")); Run->Key(EKeys::E); });
    At(19, [Run] { Run->Expect(TEXT("Character"), TEXT("Personal E wraps Ledger to Character")); Run->Key(EKeys::E); });
    At(20, [Run] { Run->Expect(TEXT("Backpack"), TEXT("Personal E visits Inventory as a distinct page")); Run->Key(EKeys::E); });
    At(20.7f, [Run] { Run->Expect(TEXT("Mech"), TEXT("Personal E visits Mech")); Run->Key(EKeys::E); });
    At(21.4f, [Run] { Run->Expect(TEXT("Skills"), TEXT("Personal E visits Skills")); Run->Key(EKeys::E); });
    At(22.1f, [Run] { Run->Expect(TEXT("Ledger"), TEXT("Personal E visits Ledger")); Run->Key(EKeys::E); });
    At(23, [Run] { Run->Expect(TEXT("Character"), TEXT("Personal cycle stays within its five pages")); Run->Click(TEXT("DIRECTOR  [B]")); });
    At(24, [] { FSystemResolution::RequestResolutionChange(1600, 900, EWindowMode::Windowed); });
    At(27, [Run] { Run->CheckWatchGeometry(FIntPoint(1600, 900)); Run->Shot(TEXT("watch-1600x900.png")); });
    At(28, [Run] { Run->Click(TEXT("CHARACTER  [I]")); });
    At(29, [Run] { Run->Expect(TEXT("Character"), TEXT("Character link works at 1600x900")); Run->Click(TEXT("INVENTORY")); });
    At(30, [Run] { Run->Expect(TEXT("Backpack"), TEXT("single-click Inventory works at 1600x900")); Run->Click(TEXT("CHARACTER")); });
    At(31, [Run] { Run->Expect(TEXT("Character"), TEXT("single-click Character works at 1600x900")); Run->Shot(TEXT("character-1600x900.png")); });
    At(31.3f, [Run] { Run->Click(TEXT("INVENTORY")); });
    At(32, [Run] { Run->Expect(TEXT("Backpack"), TEXT("Inventory selected before closing")); Run->Key(EKeys::Escape); });
    At(33, [Run]
    {
        Run->Check(Run->Menu.IsValid() && !Run->Menu->IsMenuOpen(), TEXT("Escape closes from Inventory"));
        Run->Key(EKeys::I, false);
    });
    At(34, [Run] { Run->Expect(TEXT("Character"), TEXT("gameplay I reopens Character after closing Inventory")); Run->Click(TEXT("DIRECTOR  [B]")); });
    At(35, [Run] { Run->Expect(TEXT("Watch"), TEXT("Director reopens after gameplay I")); Run->Click(TEXT("MAP")); });
    At(36, [Run] { Run->Expect(TEXT("Map"), TEXT("Map selected for Character return")); Run->Click(TEXT("CHARACTER  [I]")); });
    At(37, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click returns from Map to Character")); Run->Click(TEXT("DIRECTOR  [B]")); });
    At(38, [Run] { Run->Expect(TEXT("Watch"), TEXT("Director opens for Missions return check")); Run->Click(TEXT("MISSIONS")); });
    At(39, [Run] { Run->Expect(TEXT("Missions"), TEXT("Missions selected for Character return")); Run->Click(TEXT("CHARACTER  [I]")); });
    At(40, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click returns from Missions to Character")); Run->Click(TEXT("DIRECTOR  [B]")); });
    At(41, [Run] { Run->Expect(TEXT("Watch"), TEXT("Director opens for Squad return check")); Run->Click(TEXT("SQUAD")); });
    At(42, [Run] { Run->Expect(TEXT("Squad"), TEXT("Squad selected for Character return")); Run->Click(TEXT("CHARACTER  [I]")); });
    At(43, [Run] { Run->Expect(TEXT("Character"), TEXT("one mouse click returns from Squad to Character")); Run->Click(TEXT("DIRECTOR  [B]")); });
    At(44, [Run, OriginalResolution, OriginalCursor]
    {
        Run->Expect(TEXT("Watch"), TEXT("check leaves Watch open"));
        if (Run->Menu.IsValid() && !Run->Is(TEXT("Watch"))) { Run->Menu->OpenScreen(TEXT("Watch")); }
        if (Run->World.IsValid())
        {
            const AIBWatchBoard* Board = AIBWatchBoard::Get(Run->World.Get());
            Run->Check(!Board || !Board->IsArmed(), TEXT("menu browsing never armed deployment"));
        }
        FSystemResolution::RequestResolutionChange(OriginalResolution.ResX, OriginalResolution.ResY, OriginalResolution.WindowMode);
        FSlateApplication::Get().SetCursorPos(OriginalCursor);
        UE_LOG(LogIronBreach, Display, TEXT("[MenuFlow] COMPLETE: %d passed, %d failed"), Run->Passed, Run->Failed);
        RunningWorld.Reset();
    });
}));
}
#endif
