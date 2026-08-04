#include "Items/IBLedgerSubsystem.h"
#include "IronBreach.h"
#include "Items/IBItemDefinition.h"
#include "Engine/AssetManager.h"
#include "Kismet/GameplayStatics.h"

const TCHAR* UIBLedgerSubsystem::SaveSlotName = TEXT("IronBreach_Ledger");

void UIBLedgerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	LoadFromDisk();
	UE_LOG(LogIronBreach, Log, TEXT("[Ledger] Initialized — %d entries discovered."), Discovered.Num());
}

void UIBLedgerSubsystem::MarkDiscovered(const UIBItemDefinition* Definition)
{
	if (!Definition || !Definition->bShowInLedger) { return; }

	bool bAlreadyIn = false;
	Discovered.Add(Definition->GetPrimaryAssetId(), &bAlreadyIn);
	if (bAlreadyIn) { return; }

	SaveToDisk();
	OnEntryDiscovered.Broadcast(Definition);
	UE_LOG(LogIronBreach, Log, TEXT("[Ledger] New entry: %s"), *Definition->GetName());
}

bool UIBLedgerSubsystem::IsDiscovered(const UIBItemDefinition* Definition) const
{
	return Definition && Discovered.Contains(Definition->GetPrimaryAssetId());
}

TArray<UIBItemDefinition*> UIBLedgerSubsystem::GetFullCatalog() const
{
	TArray<UIBItemDefinition*> Out;

	UAssetManager& Manager = UAssetManager::Get();
	TArray<FPrimaryAssetId> Ids;
	Manager.GetPrimaryAssetIdList(UIBItemDefinition::PrimaryAssetType, Ids);

	if (Ids.Num() == 0)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[Ledger] No IBItem primary assets registered. Add the 'IBItem' entry under Project Settings > Asset Manager (see MENUS_UI_WIRING.md §2)."));
		return Out;
	}

	for (const FPrimaryAssetId& Id : Ids)
	{
		const FSoftObjectPath Path = Manager.GetPrimaryAssetPath(Id);
		if (UIBItemDefinition* Def = Cast<UIBItemDefinition>(Path.TryLoad()))
		{
			if (Def->bShowInLedger)
			{
				Out.Add(Def);
			}
		}
	}

	// Stable, readable ordering: category, then rarity descending, then name.
	Out.Sort([](const UIBItemDefinition& A, const UIBItemDefinition& B)
	{
		if (A.Category != B.Category) { return A.Category < B.Category; }
		if (A.Rarity != B.Rarity)     { return A.Rarity > B.Rarity; }
		return A.DisplayName.CompareTo(B.DisplayName) < 0;
	});
	return Out;
}

void UIBLedgerSubsystem::LoadFromDisk()
{
	if (!UGameplayStatics::DoesSaveGameExist(SaveSlotName, 0)) { return; }

	if (const UIBLedgerSaveGame* Save = Cast<UIBLedgerSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, 0)))
	{
		for (const FString& IdString : Save->DiscoveredAssetIds)
		{
			const FPrimaryAssetId Id = FPrimaryAssetId::FromString(IdString);
			if (Id.IsValid())
			{
				Discovered.Add(Id);
			}
		}
	}
}

void UIBLedgerSubsystem::SaveToDisk() const
{
	UIBLedgerSaveGame* Save = Cast<UIBLedgerSaveGame>(UGameplayStatics::CreateSaveGameObject(UIBLedgerSaveGame::StaticClass()));
	if (!Save) { return; }

	Save->DiscoveredAssetIds.Reserve(Discovered.Num());
	for (const FPrimaryAssetId& Id : Discovered)
	{
		Save->DiscoveredAssetIds.Add(Id.ToString());
	}
	UGameplayStatics::SaveGameToSlot(Save, SaveSlotName, 0);
}
