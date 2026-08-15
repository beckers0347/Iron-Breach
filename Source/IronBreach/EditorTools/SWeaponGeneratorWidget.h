// SWeaponGeneratorWidget.h
//
// Editor panel: name + Weapon Type + Weapon Tier, "Generate Weapon" button.
// Damage/Fire Rate/Range are NOT entered by hand -- they're auto-rolled from
// Type + Tier by FWeaponBalanceTable (see WeaponBalanceTable.h) so weapons of
// the same Tier land on comparable overall power no matter which Type you pick.
// Wraps UWeaponGeneratorLibrary::GenerateWeaponAsset (duplicates
// /Game/Weapons/Rifle/DA_AssultRifle by default -- see WeaponGeneratorLibrary.h).
//
// To launch it in-editor: Window > Weapon Generator (registered as a dockable
// tab in IronBreach.cpp -- no Blueprint/Editor Utility Widget asset needed).
#pragma once

#include "CoreMinimal.h"

#if WITH_EDITOR

#include "Widgets/SCompoundWidget.h"
#include "EditorUtilityWidget.h"
#include "EditorTools/WeaponBalanceTable.h"
#include "SWeaponGeneratorWidget.generated.h"

class SEditableTextBox;
template <typename OptionType> class SComboBox;

class SWeaponGeneratorWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWeaponGeneratorWidget) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	FReply OnGenerateClicked();

	TSharedRef<SWidget> MakeClassComboBox();
	TSharedRef<SWidget> MakeTierComboBox();

	FText GetSelectedClassText() const;
	FText GetSelectedTierText() const;

	TSharedPtr<SEditableTextBox> WeaponNameTextBox;

	TArray<TSharedPtr<EWeaponClass>> ClassOptions;
	TArray<TSharedPtr<EWeaponTier>> TierOptions;

	TSharedPtr<SComboBox<TSharedPtr<EWeaponClass>>> ClassComboBox;
	TSharedPtr<SComboBox<TSharedPtr<EWeaponTier>>> TierComboBox;

	EWeaponClass SelectedClass = EWeaponClass::Rifle;
	EWeaponTier SelectedTier = EWeaponTier::C;
};

/** Thin UMG host so the native Slate panel above can be opened as an Editor
 *  Utility Widget tab (Blutility has no way to spawn raw SCompoundWidgets directly).
 *  Kept even though the Window > Weapon Generator tab (IronBreach.cpp) is now the
 *  primary way to launch this -- harmless to leave as a second entry point if an
 *  Editor Utility Widget Blueprint ever gets reparented to this successfully. */
UCLASS()
class IRONBREACH_API UWeaponGeneratorEditorWidget : public UEditorUtilityWidget
{
	GENERATED_BODY()

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
};

#endif // WITH_EDITOR
