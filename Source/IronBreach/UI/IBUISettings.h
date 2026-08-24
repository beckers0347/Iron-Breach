#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "InputCoreTypes.h"
#include "Items/IBItemTypes.h"
#include "IBUISettings.generated.h"

class UIBMenuScreen;

/**
 * One registered full-screen menu. Array order in the settings IS the tab-cycle
 * order (Q/E, shoulder buttons) — Destiny's bumper grammar, data-driven.
 */
USTRUCT()
struct FIBMenuScreenDef
{
	GENERATED_BODY()

	/** Stable id C++/BP use to open this screen ("Inventory", "Ledger", "Map"). */
	UPROPERTY(EditAnywhere, Category = "Screen")
	FName ScreenId;

	UPROPERTY(EditAnywhere, Category = "Screen")
	FText TabLabel;

	/** Shane's WBP child of the matching C++ screen class. Soft: no cooked-in
	 *  content refs from code; loaded on first open, cached after. */
	UPROPERTY(EditAnywhere, Category = "Screen")
	TSoftClassPtr<UIBMenuScreen> WidgetClass;

	/** Keys that jump to this screen from INSIDE another menu screen (same key on
	 *  its own screen = close). Keep these matching the IA_Menu_* mappings so
	 *  in-game and in-menu behavior feel like one system. */
	UPROPERTY(EditAnywhere, Category = "Screen")
	TArray<FKey> Hotkeys;

	/** False = registered and openable (hotkey / Escape / buttons) but NOT a
	 *  tab: hidden from the banner and skipped by Q/E cycling. The Escape
	 *  layer (System, Settings) lives here — tabs are for the play loop. */
	UPROPERTY(EditAnywhere, Category = "Screen")
	bool bShowInTabBar = true;
};

/**
 * Project Settings > Game > Iron Breach UI. Everything Shane should be able to
 * tune without a rebuild lives here: which screens exist, their order, their
 * hotkeys, and the rarity palette. Written to DefaultGame.ini (defaultconfig)
 * so it versions through git like any other config.
 */
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Iron Breach UI"))
class IRONBREACH_API UIBUISettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UIBUISettings()
	{
		CategoryName = TEXT("Game");

		// Iron Breach palette start point, not Destiny's: cold service-metal ramp
		// up to Relic amber. Tune freely in Project Settings.
		RarityColors.Add(EIBItemRarity::Common,    FLinearColor(0.45f, 0.48f, 0.44f));
		RarityColors.Add(EIBItemRarity::Uncommon,  FLinearColor(0.22f, 0.52f, 0.34f));
		RarityColors.Add(EIBItemRarity::Rare,      FLinearColor(0.20f, 0.45f, 0.68f));
		RarityColors.Add(EIBItemRarity::Legendary, FLinearColor(0.42f, 0.26f, 0.60f));
		RarityColors.Add(EIBItemRarity::Exotic,    FLinearColor(0.85f, 0.62f, 0.18f));
	}

	static const UIBUISettings* Get() { return GetDefault<UIBUISettings>(); }

	/** The menu ring, in cycle order. */
	UPROPERTY(EditAnywhere, config, Category = "Screens")
	TArray<FIBMenuScreenDef> Screens;

	UPROPERTY(EditAnywhere, config, Category = "Style")
	TMap<EIBItemRarity, FLinearColor> RarityColors;

	FLinearColor GetRarityColor(EIBItemRarity Rarity) const
	{
		const FLinearColor* Found = RarityColors.Find(Rarity);
		return Found ? *Found : FLinearColor::White;
	}

	const FIBMenuScreenDef* FindScreen(FName ScreenId) const
	{
		return Screens.FindByPredicate([ScreenId](const FIBMenuScreenDef& S) { return S.ScreenId == ScreenId; });
	}
};
