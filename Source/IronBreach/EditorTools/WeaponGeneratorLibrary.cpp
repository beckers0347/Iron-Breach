// WeaponGeneratorLibrary.cpp
#include "EditorTools/WeaponGeneratorLibrary.h"
#include "Combat/WeaponDataAsset.h"
#include "IronBreach.h"

#if WITH_EDITOR
#include "EditorAssetLibrary.h"
#include "Misc/Paths.h"
#include "Math/RandomStream.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Framework/Notifications/NotificationManager.h"
#endif

void UWeaponGeneratorLibrary::SpawnWeaponGeneratorNotification(const FString& Message, bool bSuccess)
{
#if WITH_EDITOR
	FNotificationInfo Info(FText::FromString(Message));
	Info.ExpireDuration = 4.0f;
	Info.bUseLargeFont = false;
	Info.bFireAndForget = true;

	TSharedPtr<SNotificationItem> NotificationItem = FSlateNotificationManager::Get().AddNotification(Info);
	if (NotificationItem.IsValid())
	{
		NotificationItem->SetCompletionState(bSuccess ? SNotificationItem::CS_Success : SNotificationItem::CS_Fail);
	}
#endif
}

UWeaponDataAsset* UWeaponGeneratorLibrary::GenerateWeaponAsset(const FWeaponGenerationParams& Params)
{
#if WITH_EDITOR
	const FString CleanWeaponName = FPaths::MakeValidFileName(Params.NewWeaponName);
	if (CleanWeaponName.IsEmpty())
	{
		SpawnWeaponGeneratorNotification(TEXT("Weapon generation failed: name is empty."), false);
		return nullptr;
	}

	if (!UEditorAssetLibrary::DoesAssetExist(Params.SourceTemplatePath))
	{
		SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Weapon generation failed: template not found at %s"), *Params.SourceTemplatePath), false);
		return nullptr;
	}

	// Resolve stats: auto-balance rolls from Class+Tier (the panel's mode), manual
	// mode trusts the caller's numbers as-is (WeaponAssetActions' "_Variant" clone).
	float ResolvedDamage = Params.BaseDamage;
	float ResolvedFireRate = Params.FireRate;
	float ResolvedMaxRange = Params.MaxRange;
	FString AssetNameSuffix;
	FString EffectiveFolderPath = Params.TargetFolderPath;

	if (Params.bAutoBalanceFromClassAndTier)
	{
		FRandomStream Stream(Params.RandomSeed != 0 ? Params.RandomSeed : FMath::Rand());
		const FRolledWeaponStats Rolled = FWeaponBalanceTable::RollStats(Params.WeaponClass, Params.Tier, Stream);

		ResolvedDamage = Rolled.Damage;
		ResolvedFireRate = Rolled.FireIntervalSeconds;
		ResolvedMaxRange = Rolled.MaxRange;

		AssetNameSuffix = FString::Printf(TEXT("_%s"), *FWeaponBalanceTable::GetTierDisplayName(Params.Tier));
		// Group generated weapons by Class so the Content Browser doesn't turn into
		// one giant flat folder after a few generation sessions.
		EffectiveFolderPath = Params.TargetFolderPath / FWeaponBalanceTable::GetClassDisplayName(Params.WeaponClass);
	}

	const FString DataAssetName = FString::Printf(TEXT("DA_%s%s"), *CleanWeaponName, *AssetNameSuffix);
	const FString TargetObjectPath = EffectiveFolderPath / DataAssetName;

	if (UEditorAssetLibrary::DoesAssetExist(TargetObjectPath))
	{
		SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Weapon generation failed: %s already exists."), *TargetObjectPath), false);
		return nullptr;
	}

	UObject* DuplicatedObject = UEditorAssetLibrary::DuplicateAsset(Params.SourceTemplatePath, TargetObjectPath);
	UWeaponDataAsset* NewWeaponDA = Cast<UWeaponDataAsset>(DuplicatedObject);
	if (!NewWeaponDA)
	{
		SpawnWeaponGeneratorNotification(TEXT("Weapon generation failed: could not duplicate template asset."), false);
		return nullptr;
	}

	// Override the stats the generator resolved; everything else (Ads tuning, tracer,
	// fire sound, viewmodel scale) carries over from the template untouched.
	NewWeaponDA->WeaponName = FName(*Params.NewWeaponName);
	NewWeaponDA->BaseDamage = ResolvedDamage;
	NewWeaponDA->FireRate = ResolvedFireRate;
	NewWeaponDA->MaxRange = ResolvedMaxRange;

	UEditorAssetLibrary::SaveLoadedAsset(NewWeaponDA, /*bOnlyIfIsDirty=*/false);

	UE_LOG(LogIronBreach, Log, TEXT("Generated weapon '%s' at %s (template: %s, dmg=%.1f, fireInterval=%.2fs, range=%.0f)"),
		*CleanWeaponName, *TargetObjectPath, *Params.SourceTemplatePath, ResolvedDamage, ResolvedFireRate, ResolvedMaxRange);

	if (Params.bAutoBalanceFromClassAndTier)
	{
		const float DisplayRPS = ResolvedFireRate > 0.0f ? (1.0f / ResolvedFireRate) : 0.0f;
		SpawnWeaponGeneratorNotification(
			FString::Printf(TEXT("Generated %s (%s, Tier %s): %.0f dmg @ %.2f RPS (%.2fs cooldown), %.0f range"),
				*DataAssetName,
				*FWeaponBalanceTable::GetClassDisplayName(Params.WeaponClass),
				*FWeaponBalanceTable::GetTierDisplayName(Params.Tier),
				ResolvedDamage, DisplayRPS, ResolvedFireRate, ResolvedMaxRange),
			true);
	}
	else
	{
		SpawnWeaponGeneratorNotification(FString::Printf(TEXT("Generated %s"), *DataAssetName), true);
	}

	return NewWeaponDA;
#else
	return nullptr;
#endif
}
