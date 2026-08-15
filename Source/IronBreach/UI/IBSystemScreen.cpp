#include "UI/IBSystemScreen.h"
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "Online/IBSessionSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
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

	if (Btn_Resume) Btn_Resume->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleResumeClicked);
	if (Btn_Leave)  Btn_Leave->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleLeaveClicked);
	if (Btn_Quit)   Btn_Quit->OnClicked.AddDynamic(this, &UIBSystemScreen::HandleQuitClicked);

	if (Txt_Resume) Txt_Resume->SetText(NSLOCTEXT("IBSystem", "Resume", "RESUME"));
	if (Txt_Leave)  Txt_Leave->SetText(IsInNetworkedSession()
		? NSLOCTEXT("IBSystem", "LeaveSession", "LEAVE SESSION")
		: NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"));
	if (Txt_Quit)   Txt_Quit->SetText(NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"));
}

void UIBSystemScreen::HandleResumeClicked() { ResumeGame(); }
void UIBSystemScreen::HandleLeaveClicked()  { LeaveToMainMenu(); }
void UIBSystemScreen::HandleQuitClicked()   { QuitToDesktop(); }

UButton* UIBSystemScreen::MakeFallbackButton(UVerticalBox* Box, const FText& Label)
{
	UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	Text->SetText(Label);
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = 22;
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.9f, 1.0f)));
	Button->AddChild(Text);

	if (UVerticalBoxSlot* ButtonSlot = Box->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 8.f));
		ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
	}
	return Button;
}

void UIBSystemScreen::ConstructFallbackLayout()
{
	if (!WidgetTree) return;

	// Root overlay -> dim border -> centered column of three buttons.
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
	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Column))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Center);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
	}

	Btn_Resume = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Resume", "RESUME"));
	Btn_Leave  = MakeFallbackButton(Column, IsInNetworkedSession()
		? NSLOCTEXT("IBSystem", "LeaveSession", "LEAVE SESSION")
		: NSLOCTEXT("IBSystem", "MainMenu", "MAIN MENU"));
	Btn_Quit   = MakeFallbackButton(Column, NSLOCTEXT("IBSystem", "Quit", "QUIT TO DESKTOP"));
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
