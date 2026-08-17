#include "EditorTools/SWeaponGeneratorWidget.h"

#if WITH_EDITOR

#include "EditorTools/WeaponGeneratorLibrary.h"
#include "Widgets/SBoxPanel.h"          // SVerticalBox
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SComboBox.h"

#define LOCTEXT_NAMESPACE "WeaponGeneratorUI"

namespace
{
	TSharedRef<SWidget> MakeLabeledField(const FText& Label, TSharedRef<SWidget> Field)
	{
		return SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.f, 5.f, 5.f, 0.f)
			[
				SNew(STextBlock)
				.Text(Label)
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.f, 0.f, 5.f, 5.f)
			[
				Field
			];
	}
}

void SWeaponGeneratorWidget::Construct(const FArguments& InArgs)
{
	for (uint8 i = 0; i < (uint8)EWeaponClass::Count; ++i)
	{
		ClassOptions.Add(MakeShared<EWeaponClass>(static_cast<EWeaponClass>(i)));
	}
	for (uint8 i = 0; i < (uint8)EWeaponTier::Count; ++i)
	{
		TierOptions.Add(MakeShared<EWeaponTier>(static_cast<EWeaponTier>(i)));
	}

	ChildSlot
	[
		SNew(SVerticalBox)

		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			MakeLabeledField(LOCTEXT("WeaponNameLabel", "Weapon Name:"),
				SAssignNew(WeaponNameTextBox, SEditableTextBox)
				.HintText(LOCTEXT("WeaponNameHint", "e.g., PlasmaRifle")))
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			MakeLabeledField(LOCTEXT("WeaponClassLabel", "Weapon Type:"), MakeClassComboBox())
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			MakeLabeledField(LOCTEXT("WeaponTierLabel", "Weapon Tier:"), MakeTierComboBox())
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5.f, 15.f, 5.f, 5.f)
		[
			SNew(SButton)
			.Text(LOCTEXT("GenerateButtonText", "Generate Weapon"))
			.HAlign(HAlign_Center)
			.OnClicked(this, &SWeaponGeneratorWidget::OnGenerateClicked)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5.f, 10.f, 5.f, 5.f)
		[
			SNew(STextBlock)
			.AutoWrapText(true)
			.ColorAndOpacity(FSlateColor(FLinearColor(0.6f, 0.6f, 0.6f)))
			.Text(LOCTEXT("GeneratorHint",
				"Damage, Fire Rate, and Range are auto-balanced from Type + Tier -- "
				"same Tier means comparable overall power, different Types trade those "
				"stats differently. Check the notification (or Output Log) after "
				"generating to see the rolled numbers."))
		]
	];
}

TSharedRef<SWidget> SWeaponGeneratorWidget::MakeClassComboBox()
{
	ClassComboBox = SNew(SComboBox<TSharedPtr<EWeaponClass>>)
		.OptionsSource(&ClassOptions)
		.OnGenerateWidget_Lambda([](TSharedPtr<EWeaponClass> Option)
		{
			return SNew(STextBlock).Text(FText::FromString(FWeaponBalanceTable::GetClassDisplayName(*Option)));
		})
		.OnSelectionChanged_Lambda([this](TSharedPtr<EWeaponClass> NewSelection, ESelectInfo::Type)
		{
			if (NewSelection.IsValid())
			{
				SelectedClass = *NewSelection;
			}
		})
		[
			SNew(STextBlock).Text(this, &SWeaponGeneratorWidget::GetSelectedClassText)
		];

	return ClassComboBox.ToSharedRef();
}

TSharedRef<SWidget> SWeaponGeneratorWidget::MakeTierComboBox()
{
	TierComboBox = SNew(SComboBox<TSharedPtr<EWeaponTier>>)
		.OptionsSource(&TierOptions)
		.OnGenerateWidget_Lambda([](TSharedPtr<EWeaponTier> Option)
		{
			return SNew(STextBlock).Text(FText::FromString(FWeaponBalanceTable::GetTierDisplayName(*Option)));
		})
		.OnSelectionChanged_Lambda([this](TSharedPtr<EWeaponTier> NewSelection, ESelectInfo::Type)
		{
			if (NewSelection.IsValid())
			{
				SelectedTier = *NewSelection;
			}
		})
		[
			SNew(STextBlock).Text(this, &SWeaponGeneratorWidget::GetSelectedTierText)
		];

	return TierComboBox.ToSharedRef();
}

FText SWeaponGeneratorWidget::GetSelectedClassText() const
{
	return FText::FromString(FWeaponBalanceTable::GetClassDisplayName(SelectedClass));
}

FText SWeaponGeneratorWidget::GetSelectedTierText() const
{
	return FText::FromString(FWeaponBalanceTable::GetTierDisplayName(SelectedTier));
}

FReply SWeaponGeneratorWidget::OnGenerateClicked()
{
	if (!WeaponNameTextBox.IsValid())
	{
		return FReply::Handled();
	}

	const FString InputName = WeaponNameTextBox->GetText().ToString();
	if (InputName.IsEmpty())
	{
		UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(TEXT("Enter a weapon name first."), false);
		return FReply::Handled();
	}

	FWeaponGenerationParams Params;
	Params.NewWeaponName = InputName;
	Params.WeaponClass = SelectedClass;
	Params.Tier = SelectedTier;
	// bAutoBalanceFromClassAndTier defaults true; TargetFolderPath / SourceTemplatePath /
	// RandomSeed keep their defaults (fresh random roll every click).

	UWeaponGeneratorLibrary::GenerateWeaponAsset(Params);

	return FReply::Handled();
}

TSharedRef<SWidget> UWeaponGeneratorEditorWidget::RebuildWidget()
{
	return SNew(SWeaponGeneratorWidget);
}

#undef LOCTEXT_NAMESPACE

#endif // WITH_EDITOR
