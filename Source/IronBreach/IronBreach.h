#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

// Set up a custom log category so you can easily filter Iron Breach specific messages in the output log
DECLARE_LOG_CATEGORY_EXTERN(LogIronBreach, Log, All);

/**
 * Custom module entry point (replaces the plain IMPLEMENT_PRIMARY_GAME_MODULE stub)
 * so there's a StartupModule hook to register the Weapon Generator's dockable tab
 * directly -- Window > Weapon Generator, no Blueprint asset involved.
 *
 * Why not the Editor Utility Widget Blueprint route (EditorTools/SWeaponGeneratorWidget.h):
 * that requires creating/reparenting a Blueprint to WeaponGeneratorEditorWidget via
 * the Class Picker, which filters out native classes behind a couple of non-obvious
 * toggles ("Show Only Imported Types" etc.) -- flaky enough in practice that it's not
 * worth depending on. A registered nomad tab spawner shows the exact same native
 * SWeaponGeneratorWidget panel with no asset/Blueprint dependency at all.
 */
class FIronBreachModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
#if WITH_EDITOR
	TSharedRef<class SDockTab> SpawnWeaponGeneratorTab(const class FSpawnTabArgs& Args);

	/** Deferred past StartupModule -- UToolMenus isn't guaranteed ready this early,
	 *  and ExtendMenu on an unready UToolMenus silently no-ops rather than erroring,
	 *  so registering too soon would just produce a menu with nothing added. */
	void RegisterWeaponContextMenus();
#endif
};
