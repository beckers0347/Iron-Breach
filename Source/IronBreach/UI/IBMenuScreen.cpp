#include "UI/IBMenuScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBUISettings.h"
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

	// No bind and no overlay root to inject into -> no banner (Shane's WBP
	// can always add a TabBannerBox to opt back in).
	if (!TabBannerBox)
	{
		UOverlay* Root = WidgetTree ? Cast<UOverlay>(WidgetTree->RootWidget) : nullptr;
		if (!Root) { return; }

		TabBannerBox = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		if (UOverlaySlot* BannerSlot = Root->AddChildToOverlay(TabBannerBox))
		{
			BannerSlot->SetHorizontalAlignment(HAlign_Center);
			BannerSlot->SetVerticalAlignment(VAlign_Top);
			BannerSlot->SetPadding(FMargin(0.f, 44.f, 0.f, 0.f));
		}
	}

	const UIBUISettings* Settings = UIBUISettings::Get();
	for (int32 i = 0; i < Settings->Screens.Num(); ++i)
	{
		const FIBMenuScreenDef& Def = Settings->Screens[i];

		UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Label->SetText(Def.TabLabel.IsEmpty() ? FText::FromName(Def.ScreenId) : Def.TabLabel);
		FSlateFontInfo Font = Label->GetFont();
		Font.Size = 15;
		Label->SetFont(Font);
		Label->SetShadowOffset(FVector2D(1.f, 1.f));
		Label->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.7f));
		if (UHorizontalBoxSlot* LabelSlot = TabBannerBox->AddChildToHorizontalBox(Label))
		{
			LabelSlot->SetPadding(FMargin(18.f, 0.f));
		}
		TabLabels.Add(Label);
		TabIds.Add(Def.ScreenId);
	}
}

void UIBMenuScreen::RefreshTabBanner()
{
	for (int32 i = 0; i < TabLabels.Num(); ++i)
	{
		if (UTextBlock* Label = TabLabels[i])
		{
			const bool bActive = (TabIds.IsValidIndex(i) && TabIds[i] == ScreenId);
			Label->SetColorAndOpacity(FSlateColor(bActive
				? FLinearColor(0.85f, 0.62f, 0.18f)      // Relic amber: you are here
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
