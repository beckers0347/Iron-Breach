// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
#include "TripoProtocol.h"

PRAGMA_DISABLE_DEPRECATION_WARNINGS
static_assert(!UE_WITH_CONSTINIT_UOBJECT, "This generated code can only be compiled with !UE_WITH_CONSTINIT_UOBJECT");
void EmptyLinkFunctionForGeneratedCodeTripoProtocol() {}

// ********** Begin Cross Module References ********************************************************
// ********** End Cross Module References **********************************************************

// ********** Begin Same Module References *********************************************************
UPackage* Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferAckPayload(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferPayload(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoHandshakeAckPayload(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoHandshakePayload(ETypeConstructPhase);
TRIPO3DUEBRIDGE_API UScriptStruct* Z_Construct_UScriptStruct_FTripoImportCompletePayload(ETypeConstructPhase);
// ********** End Same Module References ***********************************************************
#define UHT_STRUCT_BASE(INIT) UE::CodeGen::ConstInit::TCompiledInObjectPtr<const FStructBaseChain>(UE::Private::AsStructBaseChain(INIT))

// ********** Begin ScriptStruct FTripoHandshakePayload ********************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoHandshakePayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoHandshakePayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoHandshakePayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "/**\n * Message structures for JSON serialization\n */// Handshake message from client\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "Message structures for JSON serialization\n // Handshake message from client" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_clientName_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_protocolVersion_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoHandshakePayload constinit property declarations ************
	static const UECodeGen_Private::FStrPropertyParams NewProp_clientName;
	static const UECodeGen_Private::FStrPropertyParams NewProp_protocolVersion;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoHandshakePayload constinit property declarations **************
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoHandshakePayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoHandshakePayload Property Definitions ***********************
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_clientName = { "clientName", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakePayload, clientName), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_clientName_MetaData), NewProp_clientName_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_protocolVersion = { "protocolVersion", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakePayload, protocolVersion), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_protocolVersion_MetaData), NewProp_protocolVersion_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_clientName,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_protocolVersion,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoHandshakePayload Property Definitions *************************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoHandshakePayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoHandshakePayload>(),
	alignof(FTripoHandshakePayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoHandshakePayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoHandshakePayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoHandshakePayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoHandshakePayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoHandshakePayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoHandshakePayload **********************************************

// ********** Begin ScriptStruct FTripoHandshakeAckPayload *****************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoHandshakeAckPayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoHandshakeAckPayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoHandshakeAckPayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "// Handshake acknowledgment from server\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "Handshake acknowledgment from server" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_success_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_clientName_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_dccVersion_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_pluginVersion_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_protocolVersion_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoHandshakeAckPayload constinit property declarations *********
	static void NewProp_success_SetBit(void* Obj)
	{
		((FTripoHandshakeAckPayload*)Obj)->success = 1;
	}
	static const UECodeGen_Private::FBoolPropertyParams NewProp_success;
	static const UECodeGen_Private::FStrPropertyParams NewProp_clientName;
	static const UECodeGen_Private::FStrPropertyParams NewProp_dccVersion;
	static const UECodeGen_Private::FStrPropertyParams NewProp_pluginVersion;
	static const UECodeGen_Private::FStrPropertyParams NewProp_protocolVersion;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoHandshakeAckPayload constinit property declarations ***********
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoHandshakeAckPayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoHandshakeAckPayload Property Definitions ********************
const UECodeGen_Private::FBoolPropertyParams UHT_STATICS::NewProp_success = { "success", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Bool | UECodeGen_Private::EPropertyGenFlags::NativeBool, nullptr, nullptr, 1, sizeof(bool), sizeof(FTripoHandshakeAckPayload), &UHT_STATICS::NewProp_success_SetBit, METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_success_MetaData), NewProp_success_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_clientName = { "clientName", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakeAckPayload, clientName), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_clientName_MetaData), NewProp_clientName_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_dccVersion = { "dccVersion", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakeAckPayload, dccVersion), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_dccVersion_MetaData), NewProp_dccVersion_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_pluginVersion = { "pluginVersion", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakeAckPayload, pluginVersion), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_pluginVersion_MetaData), NewProp_pluginVersion_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_protocolVersion = { "protocolVersion", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoHandshakeAckPayload, protocolVersion), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_protocolVersion_MetaData), NewProp_protocolVersion_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_success,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_clientName,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_dccVersion,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_pluginVersion,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_protocolVersion,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoHandshakeAckPayload Property Definitions **********************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoHandshakeAckPayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoHandshakeAckPayload>(),
	alignof(FTripoHandshakeAckPayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoHandshakeAckPayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoHandshakeAckPayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoHandshakeAckPayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoHandshakeAckPayload *******************************************

// ********** Begin ScriptStruct FTripoFileTransferPayload *****************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoFileTransferPayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoFileTransferPayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoFileTransferPayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "// File transfer message payload\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "File transfer message payload" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileId_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileName_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileType_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_chunkIndex_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_chunkTotal_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_chunkSize_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoFileTransferPayload constinit property declarations *********
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileId;
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileName;
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileType;
	static const UECodeGen_Private::FIntPropertyParams NewProp_chunkIndex;
	static const UECodeGen_Private::FIntPropertyParams NewProp_chunkTotal;
	static const UECodeGen_Private::FIntPropertyParams NewProp_chunkSize;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoFileTransferPayload constinit property declarations ***********
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoFileTransferPayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoFileTransferPayload Property Definitions ********************
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileId = { "fileId", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, fileId), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileId_MetaData), NewProp_fileId_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileName = { "fileName", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, fileName), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileName_MetaData), NewProp_fileName_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileType = { "fileType", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, fileType), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileType_MetaData), NewProp_fileType_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_chunkIndex = { "chunkIndex", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, chunkIndex), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_chunkIndex_MetaData), NewProp_chunkIndex_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_chunkTotal = { "chunkTotal", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, chunkTotal), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_chunkTotal_MetaData), NewProp_chunkTotal_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_chunkSize = { "chunkSize", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferPayload, chunkSize), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_chunkSize_MetaData), NewProp_chunkSize_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileId,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileName,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileType,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_chunkIndex,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_chunkTotal,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_chunkSize,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoFileTransferPayload Property Definitions **********************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoFileTransferPayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoFileTransferPayload>(),
	alignof(FTripoFileTransferPayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferPayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoFileTransferPayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoFileTransferPayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoFileTransferPayload *******************************************

// ********** Begin ScriptStruct FTripoFileTransferAckPayload **************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoFileTransferAckPayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoFileTransferAckPayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoFileTransferAckPayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "// File transfer acknowledgment payload\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "File transfer acknowledgment payload" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_success_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileId_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileIndex_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_code_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoFileTransferAckPayload constinit property declarations ******
	static void NewProp_success_SetBit(void* Obj)
	{
		((FTripoFileTransferAckPayload*)Obj)->success = 1;
	}
	static const UECodeGen_Private::FBoolPropertyParams NewProp_success;
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileId;
	static const UECodeGen_Private::FIntPropertyParams NewProp_fileIndex;
	static const UECodeGen_Private::FIntPropertyParams NewProp_code;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoFileTransferAckPayload constinit property declarations ********
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoFileTransferAckPayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoFileTransferAckPayload Property Definitions *****************
const UECodeGen_Private::FBoolPropertyParams UHT_STATICS::NewProp_success = { "success", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Bool | UECodeGen_Private::EPropertyGenFlags::NativeBool, nullptr, nullptr, 1, sizeof(bool), sizeof(FTripoFileTransferAckPayload), &UHT_STATICS::NewProp_success_SetBit, METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_success_MetaData), NewProp_success_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileId = { "fileId", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferAckPayload, fileId), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileId_MetaData), NewProp_fileId_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_fileIndex = { "fileIndex", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferAckPayload, fileIndex), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileIndex_MetaData), NewProp_fileIndex_MetaData) };
const UECodeGen_Private::FIntPropertyParams UHT_STATICS::NewProp_code = { "code", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Int, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferAckPayload, code), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_code_MetaData), NewProp_code_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_success,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileId,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileIndex,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_code,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoFileTransferAckPayload Property Definitions *******************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoFileTransferAckPayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoFileTransferAckPayload>(),
	alignof(FTripoFileTransferAckPayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferAckPayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoFileTransferAckPayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoFileTransferAckPayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoFileTransferAckPayload ****************************************

// ********** Begin ScriptStruct FTripoFileTransferCompletePayload *********************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoFileTransferCompletePayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoFileTransferCompletePayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "// File transfer complete payload\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "File transfer complete payload" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileId_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_status_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_message_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoFileTransferCompletePayload constinit property declarations *
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileId;
	static const UECodeGen_Private::FStrPropertyParams NewProp_status;
	static const UECodeGen_Private::FStrPropertyParams NewProp_message;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoFileTransferCompletePayload constinit property declarations ***
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoFileTransferCompletePayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoFileTransferCompletePayload Property Definitions ************
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileId = { "fileId", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferCompletePayload, fileId), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileId_MetaData), NewProp_fileId_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_status = { "status", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferCompletePayload, status), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_status_MetaData), NewProp_status_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_message = { "message", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoFileTransferCompletePayload, message), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_message_MetaData), NewProp_message_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileId,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_status,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_message,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoFileTransferCompletePayload Property Definitions **************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoFileTransferCompletePayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoFileTransferCompletePayload>(),
	alignof(FTripoFileTransferCompletePayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoFileTransferCompletePayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoFileTransferCompletePayload ***********************************

// ********** Begin ScriptStruct FTripoImportCompletePayload ***************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_Construct_UScriptStruct_FTripoImportCompletePayload_Statics
struct UHT_STATICS
{
	static inline consteval int32 GetStructSize() { return DataSizeOf<FTripoImportCompletePayload>(); }
	static inline consteval int16 GetStructAlignment() { return alignof(FTripoImportCompletePayload); }
#if WITH_METADATA
	static constexpr UECodeGen_Private::FMetaDataPairParam Type_MetaData[] = {
		{ "Comment", "// Import complete payload\n" },
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
		{ "ToolTip", "Import complete payload" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_fileId_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_success_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
	static constexpr UECodeGen_Private::FMetaDataPairParam NewProp_message_MetaData[] = {
		{ "ModuleRelativePath", "Public/TripoProtocol.h" },
	};
#endif // WITH_METADATA

// ********** Begin ScriptStruct FTripoImportCompletePayload constinit property declarations *******
	static const UECodeGen_Private::FStrPropertyParams NewProp_fileId;
	static void NewProp_success_SetBit(void* Obj)
	{
		((FTripoImportCompletePayload*)Obj)->success = 1;
	}
	static const UECodeGen_Private::FBoolPropertyParams NewProp_success;
	static const UECodeGen_Private::FStrPropertyParams NewProp_message;
	static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
// ********** End ScriptStruct FTripoImportCompletePayload constinit property declarations *********
	static void* NewStructOps()
	{
		return (UScriptStruct::ICppStructOps*)new UScriptStruct::TCppStructOps<FTripoImportCompletePayload>();
	}
	static const UECodeGen_Private::FStructParams StructParams;
}; // struct UHT_STATICS

// ********** Begin ScriptStruct FTripoImportCompletePayload Property Definitions ******************
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_fileId = { "fileId", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoImportCompletePayload, fileId), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_fileId_MetaData), NewProp_fileId_MetaData) };
const UECodeGen_Private::FBoolPropertyParams UHT_STATICS::NewProp_success = { "success", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Bool | UECodeGen_Private::EPropertyGenFlags::NativeBool, nullptr, nullptr, 1, sizeof(bool), sizeof(FTripoImportCompletePayload), &UHT_STATICS::NewProp_success_SetBit, METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_success_MetaData), NewProp_success_MetaData) };
const UECodeGen_Private::FStrPropertyParams UHT_STATICS::NewProp_message = { "message", nullptr, (EPropertyFlags)0x0010000000000000, UECodeGen_Private::EPropertyGenFlags::Str, nullptr, nullptr, 1, STRUCT_OFFSET(FTripoImportCompletePayload, message), METADATA_PARAMS(UE_ARRAY_COUNT(NewProp_message_MetaData), NewProp_message_MetaData) };
const UECodeGen_Private::FPropertyParamsBase* const UHT_STATICS::PropPointers[] = {
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_fileId,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_success,
	(const UECodeGen_Private::FPropertyParamsBase*)&UHT_STATICS::NewProp_message,
};
static_assert(UE_ARRAY_COUNT(UHT_STATICS::PropPointers) < 2048);
// ********** End ScriptStruct FTripoImportCompletePayload Property Definitions ********************
const UECodeGen_Private::FStructParams UHT_STATICS::StructParams = {
	(FTypeConstructFunc*)Z_Construct_UPackage__Script_Tripo3DUEBridge,
	nullptr,
	&NewStructOps,
	"TripoImportCompletePayload",
	UHT_STATICS::PropPointers,
	UE_ARRAY_COUNT(UHT_STATICS::PropPointers),
	DataSizeOf<FTripoImportCompletePayload>(),
	alignof(FTripoImportCompletePayload),
	RF_Public|RF_Transient|RF_MarkAsNative,
	EStructFlags(0x00000001),
	METADATA_PARAMS(UE_ARRAY_COUNT(UHT_STATICS::Type_MetaData), UHT_STATICS::Type_MetaData)
};
static FStructRegistrationInfo Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload;
UScriptStruct* Z_Construct_UScriptStruct_FTripoImportCompletePayload(ETypeConstructPhase Phase)
{
	if (Phase == ETypeConstructPhase::Outer)
	{
		if (!Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.OuterSingleton)
		{
			Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.OuterSingleton = GetStaticStruct(Z_Construct_UScriptStruct_FTripoImportCompletePayload, (UObject*)Z_Construct_UPackage__Script_Tripo3DUEBridge(ETypeConstructPhase::Outer), TEXT("TripoImportCompletePayload"));
		}
		return Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.OuterSingleton;
	}
	if (!Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.InnerSingleton)
	{
		UECodeGen_Private::ConstructUScriptStruct(Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.InnerSingleton, UHT_STATICS::StructParams);
	}
	return CastChecked<UScriptStruct>(Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload.InnerSingleton);
}
#undef UHT_STATICS
// ********** End ScriptStruct FTripoImportCompletePayload *****************************************

// ********** Begin Registration *******************************************************************
#ifdef UHT_STATICS
#error UHT_STATICS already defined
#endif
#define UHT_STATICS Z_CompiledInDeferFile_FID_Tripo3D_UE_Bridge_Builds_Tripo3DUEBridge_UE5_8_Win64_HostProject_Plugins_Tripo3DUEBridge_Source_Tripo3DUEBridge_Public_TripoProtocol_h__Script_Tripo3DUEBridge_Statics
struct UHT_STATICS
{
	static constexpr FStructRegisterCompiledInInfo ScriptStructInfo[] = {
		{ Z_Construct_UScriptStruct_FTripoHandshakePayload, Z_Construct_UScriptStruct_FTripoHandshakePayload_Statics::NewStructOps, TEXT("TripoHandshakePayload"),&Z_Registration_Info_UScriptStruct_FTripoHandshakePayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoHandshakePayload), 3821541374U) },
		{ Z_Construct_UScriptStruct_FTripoHandshakeAckPayload, Z_Construct_UScriptStruct_FTripoHandshakeAckPayload_Statics::NewStructOps, TEXT("TripoHandshakeAckPayload"),&Z_Registration_Info_UScriptStruct_FTripoHandshakeAckPayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoHandshakeAckPayload), 1103583963U) },
		{ Z_Construct_UScriptStruct_FTripoFileTransferPayload, Z_Construct_UScriptStruct_FTripoFileTransferPayload_Statics::NewStructOps, TEXT("TripoFileTransferPayload"),&Z_Registration_Info_UScriptStruct_FTripoFileTransferPayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoFileTransferPayload), 3156624507U) },
		{ Z_Construct_UScriptStruct_FTripoFileTransferAckPayload, Z_Construct_UScriptStruct_FTripoFileTransferAckPayload_Statics::NewStructOps, TEXT("TripoFileTransferAckPayload"),&Z_Registration_Info_UScriptStruct_FTripoFileTransferAckPayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoFileTransferAckPayload), 98992985U) },
		{ Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload, Z_Construct_UScriptStruct_FTripoFileTransferCompletePayload_Statics::NewStructOps, TEXT("TripoFileTransferCompletePayload"),&Z_Registration_Info_UScriptStruct_FTripoFileTransferCompletePayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoFileTransferCompletePayload), 1660550074U) },
		{ Z_Construct_UScriptStruct_FTripoImportCompletePayload, Z_Construct_UScriptStruct_FTripoImportCompletePayload_Statics::NewStructOps, TEXT("TripoImportCompletePayload"),&Z_Registration_Info_UScriptStruct_FTripoImportCompletePayload, CONSTRUCT_RELOAD_VERSION_INFO(FStructReloadVersionInfo, sizeof(FTripoImportCompletePayload), 3199396428U) },
	};
}; // UHT_STATICS 
static FRegisterCompiledInInfo Z_CompiledInDeferFile_FID_Tripo3D_UE_Bridge_Builds_Tripo3DUEBridge_UE5_8_Win64_HostProject_Plugins_Tripo3DUEBridge_Source_Tripo3DUEBridge_Public_TripoProtocol_h__Script_Tripo3DUEBridge_3cd1b509ccad085bff1b239da1d408e4e4fed644{
	TEXT("/Script/Tripo3DUEBridge"),
	nullptr, 0,
	UHT_STATICS::ScriptStructInfo, UE_ARRAY_COUNT(UHT_STATICS::ScriptStructInfo),
	nullptr, 0,
	nullptr, 0,
};
#undef UHT_STATICS
// ********** End Registration *********************************************************************
#undef UHT_STRUCT_BASE

PRAGMA_ENABLE_DEPRECATION_WARNINGS
