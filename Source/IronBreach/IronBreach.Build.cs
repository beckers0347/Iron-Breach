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
			"UMG"
		});

		PrivateDependencyModuleNames.AddRange(new string[] {  });
	}
}