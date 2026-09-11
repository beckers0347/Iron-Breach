#include "UI/IBMenuScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBUISettings.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBMenuNavButton.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBInventoryScreen.h"
#include "Items/IBPlayerState.h"
#include "Items/IBInventoryComponent.h"
#include "Player/IBCharacterTypes.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Engine/Texture2D.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"

void UIBMenuScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	SetIsFocusable(true); // required for NativeOnKeyDown to receive anything

	if (CloseKeys.IsEmpty())
	{
		CloseKeys = { EKeys::Escape, EKeys::Gamepad_FaceButton_Right };
	}
	if (NextScreenKeys.IsEmpty())
	{
		NextScreenKeys = { EKeys::E, EKeys::Gamepad_RightShoulder };
	}
	if (PrevScreenKeys.IsEmpty())
	{
		PrevScreenKeys = { EKeys::Q, EKeys::Gamepad_LeftShoulder };
	}
}

void UIBMenuScreen::EnsureTabBanner()
{
	if (TabLabels.Num() > 0) { return; } // built once; screens are cached
	const bool bFieldMenu = bHangarLayout || ScreenId == TEXT("Inventory") || ScreenId == TEXT("Ledger") || ScreenId == TEXT("Map");

	// No bind and no overlay root to inject into -> no banner (Shane's WBP
	// can always add a TabBannerBox to opt back in).
	if (!TabBannerBox)
	{
		UOverlay* Root = WidgetTree ? Cast<UOverlay>(WidgetTree->RootWidget) : nullptr;
		if (!Root) { return; }

		TabBannerBox = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

		// House chrome: the tab rail rides in a rounded ink chip.
		UBorder* Rail = IBStyle::MakePanel(WidgetTree, FLinearColor(0.008f, 0.012f, 0.022f, 0.85f), bFieldMenu ? 2.f : 18.f);
		Rail->SetPadding(bFieldMenu ? FMargin(4) : FMargin(10.f, 7.f));
		Rail->SetContent(TabBannerBox);
		if (UOverlaySlot* BannerSlot = Root->AddChildToOverlay(Rail))
		{
			BannerSlot->SetHorizontalAlignment(HAlign_Center);
			BannerSlot->SetVerticalAlignment(VAlign_Top);
			BannerSlot->SetPadding(FMargin(0.f, 40.f, 0.f, 0.f));
		}
	}

	if (bHangarLayout)
	{
		auto AddTab = [this](FName Id, const FText& Text)
		{
			UIBMenuNavButton* Button = WidgetTree->ConstructWidget<UIBMenuNavButton>();
			Button->Init(OwnerSubsystem, Id);
			UTextBlock* Label = IBHangar::Label(WidgetTree, Text.ToString().ToUpper(), 14);
			Button->SetContent(Label);
			TabBannerBox->AddChildToHorizontalBox(Button)->SetPadding(FMargin(2,0));
			TabIds.Add(Id); TabLabels.Add(Label);
		};
		for (const FIBMenuScreenDef& Def : UIBUISettings::Get()->Screens)
		{
			if (!Def.bShowInTabBar) { continue; }
			if (Def.ScreenId == TEXT("Inventory"))
			{
				AddTab(TEXT("Character"), NSLOCTEXT("IBMenu", "Character", "CHARACTER"));
				AddTab(TEXT("Backpack"), NSLOCTEXT("IBMenu", "Backpack", "INVENTORY"));
			}
			else { AddTab(Def.ScreenId, Def.TabLabel); }
		}
		return;
	}

	const UIBUISettings* Settings = UIBUISettings::Get();
	for (int32 i = 0; i < Settings->Screens.Num(); ++i)
	{
		const FIBMenuScreenDef& Def = Settings->Screens[i];
		if (!Def.bShowInTabBar) { continue; } // Escape-layer screens aren't tabs

		UTextBlock* Label = IBStyle::MakeText(WidgetTree,
			Def.TabLabel.IsEmpty() ? FText::FromName(Def.ScreenId) : Def.TabLabel,
			14, IBStyle::TextLo(), 500);
		UWidget* TabContent = Label;
		if (bFieldMenu)
		{
			Label->SetText(Label->GetText().ToUpper());
			FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(TEXT("BoldCondensed"), 16);
			Font.LetterSpacing = 80;
			Label->SetFont(Font);
			UIBMenuNavButton* Button = WidgetTree->ConstructWidget<UIBMenuNavButton>();
			Button->Init(OwnerSubsystem, Def.ScreenId);
			Button->SetContent(Label);
			TabContent = Button;
		}
		if (UHorizontalBoxSlot* LabelSlot = TabBannerBox->AddChildToHorizontalBox(TabContent))
		{
			LabelSlot->SetPadding(bFieldMenu ? FMargin(2, 0) : FMargin(16.f, 0.f));
		}
		TabLabels.Add(Label);
		TabIds.Add(Def.ScreenId);
	}
}

void UIBMenuScreen::RefreshTabBanner()
{
	if (bHangarLayout)
	{
		const APlayerController* PC = GetOwningPlayer();
		const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
		if (HangarCallsign) { HangarCallsign->SetText(PS ? FText::FromString(PS->GetDisplayCallsign().ToUpper()) : NSLOCTEXT("IBMenu", "Operative", "OPERATIVE")); }
		if (HangarRank) { HangarRank->SetText(PS ? FText::Format(NSLOCTEXT("IBMenu", "Rank", "LEVEL {0}  /  {1}"), PS->GetOperativeLevel(), IBCharacter::ClassName(PS->GetOperativeClass()).ToUpper()) : FText::GetEmpty()); }
		if (HangarClearance) { HangarClearance->SetText(FText::Format(NSLOCTEXT("IBMenu", "Rating", "CLEARANCE  {0}"), PS && PS->GetInventory() ? PS->GetInventory()->GetTotalClearanceRating() : 0)); }
	}
	// On an Escape-layer screen (System, Settings) the rail itself hides —
	// you're off the tab loop, the bar would just be noise.
	if (TabBannerBox)
	{
		const FIBMenuScreenDef* OwnDef = UIBUISettings::Get()->Screens.FindByPredicate(
			[this](const FIBMenuScreenDef& S) { return S.ScreenId == GetScreenId(); });
		const bool bOwnIsTab = !OwnDef || OwnDef->bShowInTabBar;
		UWidget* Rail = TabBannerBox->GetParent() ? static_cast<UWidget*>(TabBannerBox->GetParent()) : TabBannerBox;
		const bool bClickable = bHangarLayout || ScreenId == TEXT("Inventory") || ScreenId == TEXT("Ledger") || ScreenId == TEXT("Map");
		Rail->SetVisibility(bOwnIsTab ? (bClickable ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::HitTestInvisible) : ESlateVisibility::Collapsed);
	}

	for (int32 i = 0; i < TabLabels.Num(); ++i)
	{
		if (UTextBlock* Label = TabLabels[i])
		{
			const UIBInventoryScreen* Inventory = Cast<UIBInventoryScreen>(this);
			const FName ActiveId = bHangarLayout && Inventory ? FName(Inventory->IsBackpackTab() ? TEXT("Backpack") : TEXT("Character")) : ScreenId;
			const bool bActive = TabIds.IsValidIndex(i) && TabIds[i] == ActiveId;
			if (UIBMenuNavButton* Button = Cast<UIBMenuNavButton>(Label->GetParent()))
			{
				if (bHangarLayout) { IBHangar::StyleButton(Button, bActive); }
				else { IBMenuLayout::StyleButton(Button, bActive); }
			}
			Label->SetColorAndOpacity(FSlateColor(bActive
				? (bHangarLayout ? IBHangar::Cyan() : FLinearColor(0.85f, 0.62f, 0.18f))      // Relic amber: you are here
				: FLinearColor(0.5f, 0.56f, 0.68f)));    // service gray: reachable
			Label->SetRenderOpacity(bActive ? 1.0f : 0.75f);
		}
	}
}

void UIBMenuScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Focus is the menu's oxygen: every in-menu key (close, cycle, hotkeys)
	// routes through this widget, and a stray click on a non-focusable child
	// (the dim border, the map canvas) silently drops keyboard focus to the
	// viewport — where UI-only mode eats it. Reassert every frame while open;
	// it's a cheap check and it makes Escape unkillable.
	if (OwnerSubsystem && IsVisible() && !HasKeyboardFocus() && !HasFocusedDescendants())
	{
		SetKeyboardFocus();
	}
}

void UIBMenuScreen::NotifyScreenOpened(UIBMenuSubsystem* InOwner, FName InScreenId)
{
	OwnerSubsystem = InOwner;
	ScreenId = InScreenId;
	SetKeyboardFocus();
	EnsureTabBanner();
	RefreshTabBanner();
	NativeScreenOpened();
	BP_OnScreenOpened();
}

void UIBMenuScreen::NotifyScreenClosed()
{
	NativeScreenClosed();
	BP_OnScreenClosed();
}

FReply UIBMenuScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();

	if (OwnerSubsystem)
	{
		if (CloseKeys.Contains(Key))
		{
			OwnerSubsystem->CloseMenu();
			return FReply::Handled();
		}
		if (NextScreenKeys.Contains(Key))
		{
			OwnerSubsystem->CycleScreen(+1);
			return FReply::Handled();
		}
		if (PrevScreenKeys.Contains(Key))
		{
			OwnerSubsystem->CycleScreen(-1);
			return FReply::Handled();
		}

		// Screen hotkeys from settings: same key toggles closed, another
		// screen's key jumps sideways — mirrors the in-game bindings so the
		// menu keys feel like one system inside and out.
		for (const FIBMenuScreenDef& Def : UIBUISettings::Get()->Screens)
		{
			if (Def.Hotkeys.Contains(Key))
			{
				OwnerSubsystem->ToggleScreen(Def.ScreenId);
				return FReply::Handled();
			}
		}
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

UVerticalBox* UIBMenuScreen::BuildHangarPage(const FText& Hint)
{
	bHangarLayout = true;
	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(); WidgetTree->RootWidget = Root;
	UImage* Background = WidgetTree->ConstructWidget<UImage>();
	Background->SetBrushFromTexture(LoadObject<UTexture2D>(nullptr, TEXT("/Game/IronBreach/UI/Hangar/T_MenuHangar.T_MenuHangar")));
	Background->SetVisibility(ESlateVisibility::HitTestInvisible);
	Root->AddChildToOverlay(Background);
	UBorder* Shade = IBStyle::MakePanel(WidgetTree, FLinearColor(.002f,.009f,.018f,.28f), 0);
	Shade->SetVisibility(ESlateVisibility::HitTestInvisible); Root->AddChildToOverlay(Shade);
	UVerticalBox* Sheet = WidgetTree->ConstructWidget<UVerticalBox>();
	UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>();
	UTextBlock* Crest = IBHangar::Label(WidgetTree, TEXT("◇"), 42, IBHangar::Cyan());
	Header->AddChildToHorizontalBox(Crest)->SetPadding(FMargin(0,0,16,0));
	UVerticalBox* Identity = WidgetTree->ConstructWidget<UVerticalBox>();
	HangarCallsign = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 26);
	HangarCallsign->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
	HangarRank = IBHangar::Label(WidgetTree, TEXT(""), 11, IBHangar::Cyan());
	Identity->AddChildToVerticalBox(HangarCallsign); Identity->AddChildToVerticalBox(HangarRank);
	Header->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, Identity, 230))->SetVerticalAlignment(VAlign_Center);
	TabBannerBox = WidgetTree->ConstructWidget<UHorizontalBox>();
	UHorizontalBoxSlot* NavSlot = Header->AddChildToHorizontalBox(TabBannerBox);
	NavSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); NavSlot->SetVerticalAlignment(VAlign_Center);
	HangarClearance = IBHangar::Label(WidgetTree, TEXT(""), 13, IBHangar::Cyan());
	Header->AddChildToHorizontalBox(HangarClearance)->SetVerticalAlignment(VAlign_Center);
	UIBMenuNavButton* Settings = WidgetTree->ConstructWidget<UIBMenuNavButton>();
	// OwnerSubsystem is assigned when opening; use the local player's stable menu here.
	Settings->Init(GetOwningLocalPlayer()->GetSubsystem<UIBMenuSubsystem>(), TEXT("Settings"));
	Settings->SetContent(IBHangar::Label(WidgetTree, TEXT("•••"), 18)); IBHangar::StyleButton(Settings);
	Header->AddChildToHorizontalBox(Settings)->SetPadding(FMargin(20,0,0,0));
	Sheet->AddChildToVerticalBox(IBHangar::Panel(WidgetTree, Header, FMargin(36,20)));
	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>();
	UVerticalBoxSlot* BodySlot = Sheet->AddChildToVerticalBox(Body);
	BodySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); BodySlot->SetPadding(FMargin(48,28,48,20));
	Sheet->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree, Hint, 11, FLinearColor(.62f,.74f,.79f),60))->SetPadding(FMargin(48,0,48,20));
	USizeBox* Design = IBMenuLayout::Width(WidgetTree, Sheet, 1600); Design->SetHeightOverride(900);
	UScaleBox* Fit = WidgetTree->ConstructWidget<UScaleBox>(); Fit->SetStretch(EStretch::ScaleToFit); Fit->SetContent(Design);
	Root->AddChildToOverlay(Fit);
	return Body;
}
