// WeaponContextMenuExtensions.h
//
// Adds "Generate Weapon Variant" (UWeaponDataAsset) and "Capture Icon From Mesh"
// (UIBItemDefinition) directly onto the Content Browser's native asset right-click
// menu via UToolMenus. Deliberately NOT the Editor Utility Blueprint / Blutility
// route (see WeaponAssetActions.h, left in place but no longer the recommended
// path) -- that requires creating a Blueprint and reparenting it via the Class
// Picker, which turned out to hide native classes behind a couple of non-obvious
// filter toggles. Registering menu entries in C++ needs zero content-side setup:
// rebuild, and both entries are just there.
#pragma once

#include "CoreMinimal.h"

#if WITH_EDITOR

namespace WeaponContextMenuExtensions
{
	/** Call once, after UToolMenus has finished initializing (see IronBreach.cpp's
	 *  use of UToolMenus::RegisterStartupCallback -- calling this too early is a
	 *  silent no-op, not a crash, since ExtendMenu on an unready UToolMenus just
	 *  returns null and this bails out). */
	void RegisterWeaponContextMenus();

	/** Call from ShutdownModule so a hot-reload / editor shutdown doesn't leave
	 *  stale entries registered under our owner name. */
	void UnregisterWeaponContextMenus();
}

#endif // WITH_EDITOR
