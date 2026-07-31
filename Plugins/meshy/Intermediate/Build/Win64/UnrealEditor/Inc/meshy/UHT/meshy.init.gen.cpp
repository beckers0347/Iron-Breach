// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
PRAGMA_DISABLE_DEPRECATION_WARNINGS
void EmptyLinkFunctionForGeneratedCodemeshy_init() {}
static_assert(!UE_WITH_CONSTINIT_UOBJECT, "This generated code can only be compiled with !UE_WITH_CONSTINIT_OBJECT");
	static FPackageRegistrationInfo Z_Registration_Info_UPackage__Script_meshy;
	FORCENOINLINE UPackage* Z_Construct_UPackage__Script_meshy(ETypeConstructPhase)
	{
		if (!Z_Registration_Info_UPackage__Script_meshy.OuterSingleton)
		{
		static const UECodeGen_Private::FPackageParams PackageParams = {
			"/Script/meshy",
			nullptr,
			0,
			PKG_CompiledIn | 0x00000040,
			0x45E56EAE,
			0x54D7E100,
			METADATA_PARAMS(0, nullptr)
		};
		UECodeGen_Private::ConstructUPackage(Z_Registration_Info_UPackage__Script_meshy.OuterSingleton, PackageParams);
	}
	return Z_Registration_Info_UPackage__Script_meshy.OuterSingleton;
}
static FRegisterCompiledInInfo Z_CompiledInDeferPackage_UPackage__Script_meshy(Z_Construct_UPackage__Script_meshy, TEXT("/Script/meshy"), Z_Registration_Info_UPackage__Script_meshy, CONSTRUCT_RELOAD_VERSION_INFO(FPackageReloadVersionInfo, 0x45E56EAE, 0x54D7E100));
PRAGMA_ENABLE_DEPRECATION_WARNINGS
