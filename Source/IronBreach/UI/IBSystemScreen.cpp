#include "UI/IBSystemScreen.h"
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBUISettings.h"
#include "Online/IBSessionSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/KismetSystemLibrary.h"
#include "UI/IBStyleKit.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

void UIBSystemScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Bare WBP (no Btn_ binds anywhere)? Build the minimal column so the
	// packaged game always has Resume / Leave / Quit — build one taught us
	// an empty system screen means no way out of the game at all.
	if (!Btn_Resume && !Btn_Leave && !Btn_Quit)
	{
		ConstructFallbackLayout();
	}

	if (Btn_Resume)   Btn_Resume->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleResumeClicked);
	if (Btn_Leave)    Btn_Leave->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleLeaveClicked);
	if (Btn_Quit)     Btn_Quit->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleQuitClicked);
	if (Btn_Settings) Btn_Settings->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleSettingsClicked);

	if (Txt_Resume) Txt_Resume->SetText(NSLOCTEXT("IBSystem", "Resume", "RESUME"));
	if (Txt_Leave)  Txt_Leave->SetText(IsInNetworkedSession()
		? NSLOCTEXT("IBSystem", "LeaveSession", "LEAVE SESSION")
		: NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"));
	if (Txt_Quit)   Txt_Quit->SetText(NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"));
}

void UIBSystemScreen::NativeScreenOpened()
{
	// Disarm the quit confirm every time the screen comes up — an armed quit
	// must never survive a Resume.
	bQuitArmed = false;
	if (Txt_Quit)
	{
		Txt_Quit->SetText(NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"));
		Txt_Quit->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.9f, 1.0f)));
	}
	// Leave label can change between opens (solo PIE -> joined session).
	if (Txt_Leave)
	{
		Txt_Leave->SetText(IsInNetworkedSession()
			? NSLOCTEXT("IBSystem", "LeaveSession", "LEAVE SESSION")
			: NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"));
	}
	RefreshSessionInfo();
}

void UIBSystemScreen::RefreshSessionInfo()
{
	if (!Txt_SessionInfo) { return; }

	const UWorld* World = GetWorld();
	if (!World) { return; }

	FString Mode;
	switch (World->GetNetMode())
	{
	case NM_Standalone:      Mode = TEXT("SOLO");   break;
	case NM_ListenServer:    Mode = TEXT("HOSTING"); break;
	case NM_Client:          Mode = TEXT("DEPLOYED WITH SQUAD"); break;
	default:                 Mode = TEXT("ONLINE"); break;
	}

	const int32 Players = World->GetGameState() ? World->GetGameState()->PlayerArray.Num() : 1;
	Txt_SessionInfo->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s  ·  %d %s"),
		*World->GetMapName().Replace(TEXT("UEDPIE_0_"), TEXT("")), // PIE prefix is noise
		*Mode, Players, Players == 1 ? TEXT("OPERATIVE") : TEXT("OPERATIVES"))));
}

void UIBSystemScreen::HandleResumeClicked() { ResumeGame(); }
void UIBSystemScreen::HandleLeaveClicked()  { LeaveToMainMenu(); }

void UIBSystemScreen::HandleQuitClicked()
{
	// Two-step: arm, then fire. A single misclick must not dump the squad.
	if (!bQuitArmed)
	{
		bQuitArmed = true;
		if (Txt_Quit)
		{
			Txt_Quit->SetText(NSLOCTEXT("IBSystem", "QuitConfirm", "CONFIRM — QUIT?"));
			Txt_Quit->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.62f, 0.18f))); // Relic amber
		}
		return;
	}
	QuitToDesktop();
}

void UIBSystemScreen::HandleSettingsClicked()
{
	if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
	{
		Menu->ToggleScreen(FName(TEXT("Settings")));
	}
}

UButton* UIBSystemScreen::MakeFallbackButton(UVerticalBox* Box, const FText& Label, TObjectPtr<UTextBlock>* OutLabel)
{
	UTextBlock* Text = nullptr;
	UButton* Button = IBStyle::MakeButton(WidgetTree, Label, 17, false, &Text);
	if (UVerticalBoxSlot* ButtonSlot = Box->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 5.f));
		ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	if (OutLabel) { *OutLabel = Text; }
	return Button;
}

void UIBSystemScreen::ConstructFallbackLayout()
{
	if (!WidgetTree) return;

	// Root overlay -> dim border -> centered column of buttons.
	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!WidgetTree->RootWidget)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	if (!Root) return; // WBP has a non-overlay root with no binds — leave it be

	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Dim->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.55f)); // menu, not blackout
	if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
	{
		DimSlot->SetHorizontalAlignment(HAlign_Fill);
		DimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

	// Header: title + amber accent bar + session context line.
	UTextBlock* Title = IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBSystem", "Title", "SYSTEM"));
	Column->AddChildToVerticalBox(Title);

	UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Amber());
	Accent->SetPadding(FMargin(0.f, 1.5f));
	if (UVerticalBoxSlot* AccentSlot = Column->AddChildToVerticalBox(Accent))
	{
		AccentSlot->SetPadding(FMargin(0.f, 6.f, 260.f, 0.f));
	}

	UTextBlock* Info = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 200);
	if (UVerticalBoxSlot* InfoSlot = Column->AddChildToVerticalBox(Info))
	{
		InfoSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 18.f));
	}
	Txt_SessionInfo = Info;

	Btn_Resume = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Resume", "RESUME"), &Txt_Resume);
	Btn_Settings = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Settings", "SETTINGS"));
	Btn_Leave  = MakeFallbackButton(Column, IsInNetworkedSession()
		? NSLOCTEXT("IBSystem", "LeaveSession", "LEAVE SESSION")
		: NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"), &Txt_Leave);
	Btn_Quit   = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"), &Txt_Quit);

	// The whole thing rides in a rounded card.
	UBorder* Card = IBStyle::MakePanel(WidgetTree, FLinearColor(0.015f, 0.022f, 0.04f, 0.96f), 14.f);
	Card->SetPadding(FMargin(30.f, 26.f));
	Card->SetContent(Column);

	USizeBox* ColumnSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	ColumnSize->SetWidthOverride(400.f);
	ColumnSize->AddChild(Card);
	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(ColumnSize))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Center);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
	}
}

void UIBSystemScreen::ResumeGame()
{
	if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
	{
		Menu->CloseMenu();
	}
}

void UIBSystemScreen::LeaveToMainMenu()
{
	// Drop the menu first so the input-mode restore runs against THIS world;
	// after travel the whole local player UI state is rebuilt anyway.
	ResumeGame();

	const UGameInstance* GI = GetGameInstance();
	if (UIBSessionSubsystem* Session = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr)
	{
		Session->IBLeave(); // handles session teardown + the travel itself
	}
}

void UIBSystemScreen::QuitToDesktop()
{
	UKismetSystemLibrary::QuitGame(GetWorld(), GetOwningPlayer(), EQuitPreference::Quit, false);
}

bool UIBSystemScreen::IsInNetworkedSession() const
{
	const UWorld* World = GetWorld();
	return World && World->GetNetMode() != NM_Standalone;
}
