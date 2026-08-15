// WeaponContextMenuExtensions.cpp
#include "EditorTools/WeaponContextMenuExtensions.h"

#if WITH_EDITOR

#include "EditorTools/WeaponGeneratorLibrary.h"
#include "EditorTools/ItemIconCaptureLibrary.h"
#include "Combat/WeaponDataAsset.h"
#include "Items/IBItemDefinition.h"
#include "ToolMenus.h"
#include "ContentBrowserMenuContexts.h"
#include "Misc/PackageName.h"

#define LOCTEXT_NAMESPACE "WeaponContextMenuExtensions"

namespace
{
	const FName MenuOwner(TEXT("IronBreachWeaponTools"));
	const FName SectionName(TEXT("IronBreachWeaponTools"));

	void AddGenerateWeaponVariantEntry()
	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("ContentBrowser.AssetContextMenu.WeaponDataAsset");
		if (!Menu)
		{
			return;
		}

		FToolMenuSection& Section = Menu->FindOrAddSection(SectionName);
		Section.Label = LOCTEXT("SectionLabel", "Weapon System");

		Section.AddDynamicEntry(TEXT("GenerateWeaponVariant"), FNewToolMenuSectionDelegate::CreateLambda([](FToolMenuSection& InSection)
		{
			UContentBrowserAssetContextMenuContext* Context = InSection.FindContext<UContentBrowserAssetContextMenuContext>();
			if (!Context)
			{
				return;
			}

			InSection.AddMenuEntry(
				"GenerateWeaponVariant",
				LOCTEXT("GenerateWeaponVariant", "Generate Weapon Variant"),
				LOCTEXT("GenerateWeaponVariantTooltip", "Duplicate this weapon's stats into a new _Variant asset alongside it."),
				FSlateIcon(),
				FUIAction(FExecuteAction::CreateLambda([Context]()
				{
					// Same clone-exact-stats logic WeaponAssetActions::GenerateWeaponVariant used --
					// mirrored here rather than shared since that class's Blueprint-driven path is
					// no longer the recommended entry point (see this file's header comment).
					for (UWeaponDataAsset* SourceWeapon : Context->LoadSelectedObjects<UWeaponDataAsset>())
					{
						if (!SourceWeapon)
						{
							continue;
						}

						const FString SourcePackagePath = SourceWeapon->GetOutermost()->GetName();
						const FString SourceName = SourceWeapon->WeaponName.IsNone()
							? SourceWeapon->GetName()
							: SourceWeapon->WeaponName.ToString();

						FWeaponGenerationParams Params;
						Params.NewWeaponName = SourceName + TEXT("_Variant");
						Params.TargetFolderPath = FPackageName::GetLongPackagePath(SourcePackagePath);
						Params.SourceTemplatePath = SourcePackagePath;
						Params.bAutoBalanceFromClassAndTier = false; // clone exact stats, not a fresh Tier roll
						Params.BaseDamage = SourceWeapon->BaseDamage;
						Params.FireRate = SourceWeapon->FireRate;
						Params.MaxRange = SourceWeapon->MaxRange;

						UWeaponGeneratorLibrary::GenerateWeaponAsset(Params);
					}
				}))
			);
		}));
	}

	void AddCaptureIconEntry()
	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("ContentBrowser.AssetContextMenu.IBItemDefinition");
		if (!Menu)
		{
			return;
		}

		FToolMenuSection& Section = Menu->FindOrAddSection(SectionName);
		Section.Label = LOCTEXT("SectionLabel", "Weapon System");

		Section.AddDynamicEntry(TEXT("CaptureIconFromMesh"), FNewToolMenuSectionDelegate::CreateLambda([](FToolMenuSection& InSection)
		{
			UContentBrowserAssetContextMenuContext* Context = InSection.FindContext<UContentBrowserAssetContextMenuContext>();
			if (!Context)
			{
				return;
			}

			InSection.AddMenuEntry(
				"CaptureIconFromMesh",
				LOCTEXT("CaptureIconFromMesh", "Capture Icon From Mesh"),
				LOCTEXT("CaptureIconFromMeshTooltip", "Render this item's weapon mesh in an isolated lightbox and assign the result as its Icon."),
				FSlateIcon(),
				FUIAction(FExecuteAction::CreateLambda([Context]()
				{
					// Multi-select works for free: LoadSelectedObjects returns every selected
					// IBItemDefinition, so selecting several DA_Item_* assets captures all of them.
					for (UIBItemDefinition* Item : Context->LoadSelectedObjects<UIBItemDefinition>())
					{
						UItemIconCaptureLibrary::CaptureItemIcon(Item);
					}
				}))
			);
		}));
	}
}

void WeaponContextMenuExtensions::RegisterWeaponContextMenus()
{
	if (!UToolMenus::IsToolMenuUIEnabled())
	{
		return;
	}

	FToolMenuOwnerScoped OwnerScoped(MenuOwner);
	AddGenerateWeaponVariantEntry();
	AddCaptureIconEntry();
}

void WeaponContextMenuExtensions::UnregisterWeaponContextMenus()
{
	if (UToolMenus::TryGet())
	{
		UToolMenus::Get()->UnregisterOwner(MenuOwner);
	}
}

#undef LOCTEXT_NAMESPACE

#endif // WITH_EDITOR
