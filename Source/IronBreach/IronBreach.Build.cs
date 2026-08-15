using UnrealBuildTool;

public class IronBreach : ModuleRules
{
	public IronBreach(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Allow module-root-relative includes like "Combat/DamageableInterface.h"
		PublicIncludePaths.Add(ModuleDirectory);

		// Core Engine Modules + Enhanced Input + Niagara (for MFX)
		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"Niagara",
			"AIModule",
			"NavigationSystem",
			"GameplayTasks",
			// Netcode (ADR-002): session interfaces + helpers. The Steam module itself is a
			// plugin loaded at runtime; only these two are compile-time dependencies.
			"OnlineSubsystem",
			"OnlineSubsystemUtils",
			// FUniqueNetIdRepl/FUniqueNetIdWrapper live here as of UE5 (split out of
			// OnlineSubsystem). Needed by Progression/IBXPSubsystem.cpp for cross-session
			// pilot identity (MakePlayerKey) -- OnlineSubsystem/Utils use these types too but
			// don't re-export the symbols, so linking without this gives an unresolved
			// external on FUniqueNetIdWrapper::ToString.
			"CoreOnline",
			"UMG",
			// Menus/UI + inventory (MENUS_UI_WIRING.md):
			"Slate",              // FReply / widget key & mouse handling in the menu screens
			"SlateCore",          // FGeometry, FKey, brush types
			"DeveloperSettings",  // UIBUISettings (Project Settings > Iron Breach UI)
			"NetCore"             // FFastArraySerializer — inventory delta replication
		});

		PrivateDependencyModuleNames.AddRange(new string[] {  });

		// Editor-only weapon generator tool (Source/IronBreach/EditorTools): duplicates
		// UWeaponDataAsset instances from the Content Browser / a Slate panel. Kept out of
		// packaged Game builds since this module doubles as both the Game and Editor target.
		if (Target.Type == TargetType.Editor)
		{
			PrivateDependencyModuleNames.AddRange(new string[] {
				"EditorScriptingUtilities", // UEditorAssetLibrary (asset duplicate/save)
				"Blutility"                 // UAssetActionUtility, UEditorUtilityWidget
			});
		}
	}
}