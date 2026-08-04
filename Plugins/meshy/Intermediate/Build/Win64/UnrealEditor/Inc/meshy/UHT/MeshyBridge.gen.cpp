// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
#include "MeshyBridge.h"

PRAGMA_DISABLE_DEPRECATION_WARNINGS
static_assert(!UE_WITH_CONSTINIT_UOBJECT, "This generated code can only be compiled with !UE_WITH_CONSTINIT_UOBJECT");
void EmptyLinkFunctionForGeneratedCodeMeshyBridge() {}

// ********** Begin Cross Module References ********************************************************
// ********** End Cross Module References **********************************************************

// ********** Begin Same Module References *********************************************************
UPackage* Z_Construct_UPackage__Script_meshy(ETypeConstructPhase);
MESHY_API UScriptStruct* Z_Construct_UScriptStruct_FMeshTransfer(ETypeConstructPhase);
// ********** End Same Module References ***********************************************************
#define UHT_STRUCT_BASE(INIT) UE::CodeGen::ConstInit::TCompiledInObjectPtr<const FStructBaseChain>(UE::Private::AsStructBaseChain(INIT))

// ********** Begin ScriptStruct FMeshTransfer *****************************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FMeshTransfer_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FMeshTransfer>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FMeshTransfer); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
#if !UE_BUILD_SHIPPING
		{ "Comment", "// UE 5.6/5.7 \xe7\x89\x88\xe6\x9c\xac\xe5\x85\xbc\xe5\xae\xb9\xe6\x80\xa7\xe5\xae\x8f\n" },
#endif
		{ "ModuleRelativePath", "Public/MeshyBridge.h" },
#if !UE_BUILD_SHIPPING
		{ "ToolTip", "UE 5.6/5.7 \xe7\x89\x88\xe6\x9c\xac\xe5\x85\xbc\xe5\xae\xb9\xe6\x80\xa7\xe5\xae\x8f" },
#endif
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_FileFormat_MetaData[] = {
		{ "ModuleRelativePath", "Public/MeshyBridge.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_Path_MetaData[] = {
		{ "ModuleRelativePath", "Public/MeshyBridge.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_Name_MetaData[] = {
		{ "ModuleRelativePath", "Public/MeshyBridge.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_FrameRate_MetaData[] = {
		{ "ModuleRelativePath", "Public/MeshyBridge.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FMeshTransfer constinit property declarations *********************
	static const UECodeGen_Private::FStrPropertyParams NewProp_FileFormat;
	static const UECodeGen_Private::FStrPropertyParams NewProp_Path;
	static const UECodeGen_Private::FStrPropertyParams NewProp_Name;
	static const UECodeGen_Private::FIntPropertyParams NewProp_FrameRate;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FMeshTransfer constinit property declarations ***********************
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FMeshTransfer>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FMeshTransfer Property Definitions ********************************
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_FileFormat = { "FileFormat", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FMeshTransfer, FileFormat), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_FileFormat_MetaData), NewProp_FileFormat_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_Path = { "Path", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FMeshTransfer, Path), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_Path_MetaData), NewProp_Path_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_Name = { "Name", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FMeshTransfer, Name), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_Name_MetaData), NewProp_Name_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_FrameRate = { "FrameRate", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FMeshTransfer, FrameRate), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_FrameRate_MetaData), NewProp_FrameRate_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_FileFormat,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_Path,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_Name,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_FrameRate,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FMeshTransfer Property Definitions **********************************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_meshy,
	nullptr,
	&NewStructOps,
	"MeshTransfer",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FMeshTransfer>(),
	alignof(FMeshTransfer),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FMeshTransfer;
UScriptStruct* Z_Construct_UScriptStruct_FMeshTransfer(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FMeshTransfer.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FMeshTransfer.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FMeshTransfer, (UObject*)Z_Construct_UPackage__Script_meshy(ETypeConstructPhase::Outer), TEXT("MeshTransfer"));
		}
		return Z_Registration_Info_UScriptStruct_FMeshTransfer.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FMeshTransfer.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FMeshTransfer.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FMeshTransfer.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FMeshTransfer *******************************************************

// ********** Begin Registration *******************************************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_CompiledInDeferFile_FID_IronBreach_Plugins_meshy_Source_meshy_Public_MeshyBridge_h__Script_meshy_Statics
struct UHT_STATICS
{
	static constexpr FStructRegisterCompiledInInfo ScriptStructInfo[] = {
		{ Z_Construct_UScriptStruct_FMeshTransfer, Z_Construct_UScriptStruct_FMeshTransfer_Statics::NewStructOps, TEXT("MeshTransfer"),&Z_Registration_Info_UScriptStruct_FMeshTransfer, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FMeshTransfer), 148850749U) },
	};
}; // UHT_STATICS 
static FRegisterCompiledInInfo Z_CompiledInDeferFile_FID_IronBreach_Plugins_meshy_Source_meshy_Public_MeshyBridge_h__Script_meshy_f5991a16f8037a024f0855b45a73069b05cfb5f6{
	TEXT("/Script/meshy"),
	nullptr, 0,
	UHT_STATICS::ScriptStructInfo, UE_ARRAY_COUNT(UHT_STATICS::ScriptStructInfo),
	nullptr, 0,
	nullptr, 0,
};
#undef UHT_STATICS
// ********** End Registration *********************************************************************
#undef UHT_STRUCT_BASE

PRAGMA_ENABLE_DEPRECATION_WARNINGS
