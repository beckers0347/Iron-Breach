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
#include "UI/IBMenuLayout.h"
#include "UI/IBHangarStyle.h"
#include "Online/IBWatchTypes.h"
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
	if (Btn_Watch)    Btn_Watch->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleWatchClicked);

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

	const FIBDestination* Destination = IBWatch::Find(IBWatch::DestinationForMap(World->GetMapName()));
	const FString Location = Destination ? Destination->Name.ToString() : TEXT("FIELD OPERATIONS");
	const int32 Players = World->GetGameState() ? World->GetGameState()->PlayerArray.Num() : 1;
	Txt_SessionInfo->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s  ·  %d %s"),
		*Location,
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

void UIBSystemScreen::HandleWatchClicked()
{
	if (UIBMenuSubsystem* Menu = GetMenuSubsystem())
	{
		Menu->ToggleScreen(FName(TEXT("Watch")));
	}
}

UButton* UIBSystemScreen::MakeFallbackButton(UVerticalBox* Box, const FText& Label, TObjectPtr<UTextBlock>* OutLabel)
{
	UTextBlock* Text = nullptr;
	UButton* Button = IBMenuLayout::Button(WidgetTree, Label, &Text);
	if (UVerticalBoxSlot* ButtonSlot = Box->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 6.f));
		ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	if (OutLabel) { *OutLabel = Text; }
	return Button;
}

namespace IBSystemPaint
{
	/** The exit control, marked as one. Same geometry and the same four states
	 *  as every other button on the page — only the edge changes, so it reads
	 *  as the end of the list rather than as a different kind of thing. */
	static void StyleExit(UButton* Button)
	{
		if (!Button) { return; }
		const FLinearColor Edge = IBStyle::Danger() * FLinearColor(1.f, 1.f, 1.f, 0.55f);
		FButtonStyle Style = Button->GetStyle();
		Style.Normal   = IBStyle::RoundedBrush(FLinearColor(.020f, .010f, .012f, .55f), 0.f, Edge, 1.f);
		Style.Hovered  = IBStyle::RoundedBrush(FLinearColor(.140f, .040f, .035f, .90f), 0.f, IBStyle::Danger(), 1.f);
		Style.Pressed  = IBStyle::RoundedBrush(FLinearColor(.200f, .060f, .050f, .95f), 0.f, IBStyle::Danger(), 1.f);
		Style.Disabled = IBStyle::RoundedBrush(FLinearColor(.020f, .010f, .012f, .45f), 0.f, IBStyle::Line(), 1.f);
		Button->SetStyle(Style);
	}
}

void UIBSystemScreen::ConstructFallbackLayout()
{
	const auto Page = BuildHangarSection(
		NSLOCTEXT("IBSystem", "Title", "SYSTEM"),
		NSLOCTEXT("IBSystem", "Kicker", "OPERATIVE / SESSION CONTROLS"),
		NSLOCTEXT("IBSystem", "Controls", "ESC / RETURN TO GAME"));
	if (!Page.Body) { return; }
	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
	Page.Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	UVerticalBox* Context = WidgetTree->ConstructWidget<UVerticalBox>();
	Context->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
		NSLOCTEXT("IBSystem", "BrandKicker", "BREAKWATER / OPERATIVE TERMINAL"), 12, IBStyle::Cyan(), 160));
	UTextBlock* Brand = IBMenuLayout::Heading(WidgetTree, NSLOCTEXT("IBSystem", "Brand", "IRON\nBREACH"), 96);
	Context->AddChildToVerticalBox(Brand)->SetPadding(FMargin(0, 14, 0, 20));
	// A rule between the mark and the live session line, so the brand reads as a
	// masthead and the state below it reads as state.
	UBorder* ContextRule = IBStyle::MakeAccentBar(WidgetTree, FLinearColor(.13f, .33f, .40f, .6f));
	ContextRule->SetPadding(FMargin(0.f, 0.5f));
	Context->AddChildToVerticalBox(ContextRule)->SetPadding(FMargin(0, 0, 120, 18));
	Txt_SessionInfo = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 20);
	Txt_SessionInfo->SetAutoWrapText(true);
	Context->AddChildToVerticalBox(Txt_SessionInfo)->SetPadding(FMargin(0, 0, 0, 14));
	UTextBlock* ContextHint = IBMenuLayout::Text(WidgetTree,
		NSLOCTEXT("IBSystem", "SessionHint", "Your operation remains active while this menu is open."), 14);
	ContextHint->SetAutoWrapText(true);
	Context->AddChildToVerticalBox(ContextHint);
	UHorizontalBoxSlot* ContextSlot = Columns->AddChildToHorizontalBox(Context);
	ContextSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	ContextSlot->SetPadding(FMargin(12, 30, 96, 0));

	// Commands, in two bands. Everything above the second heading keeps you in
	// the session; everything below it takes you out of one. The destinations
	// and their order are unchanged — only the grouping is new.
	UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>();
	// The shared helper takes an FString, so the label is resolved through
	// NSLOCTEXT first and stays a localized source string.
	IBHangar::SectionTitle(WidgetTree, Column,
		NSLOCTEXT("IBSystem", "Commands", "SESSION COMMANDS").ToString(), 0.f, 14.f);
	Btn_Resume = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Resume", "RESUME"), &Txt_Resume);
	IBMenuLayout::StyleButton(Btn_Resume, true);
	Btn_Settings = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Settings", "SETTINGS"));
	Btn_Watch = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Watch", "THE WATCH"));
	Column->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
		NSLOCTEXT("IBSystem", "TravelHint", "Plan your next deployment from orbit."), 12))->SetPadding(FMargin(0, 6, 0, 0));

	IBHangar::SectionTitle(WidgetTree, Column,
		NSLOCTEXT("IBSystem", "ExitBand", "EXIT").ToString(), 26.f, 14.f);
	Btn_Leave = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"), &Txt_Leave);
	Btn_Quit = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"), &Txt_Quit);
	IBSystemPaint::StyleExit(Btn_Quit);
	Column->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
		NSLOCTEXT("IBSystem", "QuitHint", "Quit requires a second click to confirm."), 12))->SetPadding(FMargin(0, 10, 0, 0));
	UHorizontalBoxSlot* CommandsSlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,
		IBMenuLayout::Card(WidgetTree, Column, FMargin(30, 28, 30, 26)), 480));
	CommandsSlot->SetVerticalAlignment(VAlign_Center);
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
