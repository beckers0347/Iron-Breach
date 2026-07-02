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
			"GameplayTasks"
		});

		PrivateDependencyModuleNames.AddRange(new string[] {  });
	}
}