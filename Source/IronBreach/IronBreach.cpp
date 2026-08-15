#include "IronBreach.h"
#include "Modules/ModuleManager.h"

#if WITH_EDITOR
#include "EditorTools/SWeaponGeneratorWidget.h"
#include "Widgets/Docking/SDockTab.h"
#include "Framework/Docking/TabManager.h"
#include "Framework/Application/SlateApplication.h"
#endif

DEFINE_LOG_CATEGORY(LogIronBreach);

#if WITH_EDITOR
static const FName WeaponGeneratorTabName(TEXT("WeaponGeneratorTab"));
#endif

void FIronBreachModule::StartupModule()
{
#if WITH_EDITOR
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(WeaponGeneratorTabName,
		FOnSpawnTab::CreateRaw(this, &FIronBreachModule::SpawnWeaponGeneratorTab))
		.SetDisplayName(NSLOCTEXT("IronBreach", "WeaponGeneratorTabTitle", "Weapon Generator"))
		.SetTooltipText(NSLOCTEXT("IronBreach", "WeaponGeneratorTabTooltip",
			"Generate weapon data asset variants for testing (e.g. stocking the Weapon Rack)."))
		.SetMenuType(ETabSpawnerMenuType::Enabled);
#endif
}

void FIronBreachModule::ShutdownModule()
{
#if WITH_EDITOR
	// FGlobalTabmanager::Get() returns a TSharedRef, not a Ptr -- it's always
	// "valid" as an object, but Slate itself may already be torn down by the
	// time module shutdown runs (e.g. editor exit), so guard on that instead.
	if (FSlateApplication::IsInitialized())
	{
		FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(WeaponGeneratorTabName);
	}
#endif
}

#if WITH_EDITOR
TSharedRef<SDockTab> FIronBreachModule::SpawnWeaponGeneratorTab(const FSpawnTabArgs& Args)
{
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			SNew(SWeaponGeneratorWidget)
		];
}
#endif

IMPLEMENT_PRIMARY_GAME_MODULE(FIronBreachModule, IronBreach, "IronBreach");
