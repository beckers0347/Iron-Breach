#include "Progression/IBVaultSubsystem.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Kismet/GameplayStatics.h"

const TCHAR* UIBVaultSaveGame::SlotName = TEXT("IronBreach_Vault");
const int32 UIBVaultSaveGame::UserIndex = 0;

void UIBVaultSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	LoadFromDisk();
}

void UIBVaultSubsystem::Deinitialize()
{
	SaveNow();
	Super::Deinitialize();
}

void UIBVaultSubsystem::LoadFromDisk()
{
	Vaults.Reset();
	if (UGameplayStatics::DoesSaveGameExist(UIBVaultSaveGame::SlotName, UIBVaultSaveGame::UserIndex))
	{
		if (const UIBVaultSaveGame* Save = Cast<UIBVaultSaveGame>(
			UGameplayStatics::LoadGameFromSlot(UIBVaultSaveGame::SlotName, UIBVaultSaveGame::UserIndex)))
		{
			Vaults = Save->Vaults;
		}
	}
	UE_LOG(LogIronBreach, Log, TEXT("Vault: %d record(s) on file"), Vaults.Num());
}

void UIBVaultSubsystem::SaveNow()
{
	if (!bDirty) { return; }
	UIBVaultSaveGame* Save = Cast<UIBVaultSaveGame>(UGameplayStatics::CreateSaveGameObject(UIBVaultSaveGame::StaticClass()));
	if (!Save) { return; }
	Save->Vaults = Vaults;
	if (UGameplayStatics::SaveGameToSlot(Save, UIBVaultSaveGame::SlotName, UIBVaultSaveGame::UserIndex))
	{
		bDirty = false;
	}
	else
	{
		UE_LOG(LogIronBreach, Warning, TEXT("Vault: save to slot '%s' FAILED"), UIBVaultSaveGame::SlotName);
	}
}

bool UIBVaultSubsystem::FindVault(const FString& Key, FIBVaultRecord& OutRecord) const
{
	if (const FIBVaultRecord* Found = Vaults.Find(Key))
	{
		OutRecord = *Found;
		return true;
	}
	return false;
}

void UIBVaultSubsystem::StoreVault(const FString& Key, const FIBVaultRecord& Record)
{
	if (Key.IsEmpty()) { return; }
	FIBVaultRecord Stored = Record;
	Stored.SavedUtc = FDateTime::UtcNow();
	Vaults.Add(Key, Stored);
	bDirty = true;
	SaveNow(); // vault writes are tiny; checkpoint immediately (the PlayerState debounces the calls)
}

FIBVaultRecord UIBVaultSubsystem::Capture(const UIBInventoryComponent* Inventory)
{
	FIBVaultRecord Record;
	if (!Inventory) { return Record; }

	for (const FIBItemInstance& Item : Inventory->GetAllItems())
	{
		if (!Item.Definition) { continue; }
		FIBVaultItem& Saved = Record.Items.AddDefaulted_GetRef();
		Saved.Definition = FSoftObjectPath(Item.Definition);
		Saved.InstanceId = Item.InstanceId;
		Saved.StackCount = Item.StackCount;
		Saved.ClearanceRating = Item.ClearanceRating;
	}

	for (uint8 Slot = 1; Slot < static_cast<uint8>(EIBEquipSlot::Count); ++Slot)
	{
		FIBItemInstance Equipped;
		if (Inventory->GetEquippedItem(static_cast<EIBEquipSlot>(Slot), Equipped) && Equipped.IsValid())
		{
			Record.Equipped.Add(Slot, Equipped.InstanceId);
		}
	}
	return Record;
}

void UIBVaultSubsystem::Restore(UIBInventoryComponent* Inventory, const FIBVaultRecord& Record)
{
	if (!Inventory) { return; }

	Inventory->ClearAllItems();

	int32 Missing = 0;
	for (const FIBVaultItem& Saved : Record.Items)
	{
		const UIBItemDefinition* Definition = Cast<UIBItemDefinition>(Saved.Definition.TryLoad());
		if (!Definition)
		{
			++Missing;
			continue;
		}
		Inventory->GrantItemInstance(Definition, Saved.InstanceId, Saved.StackCount, Saved.ClearanceRating);
	}

	for (const TPair<uint8, FGuid>& Pair : Record.Equipped)
	{
		Inventory->RequestEquip(Pair.Value); // authority: routes straight to the server path
	}

	UE_LOG(LogIronBreach, Log, TEXT("Vault: restored %d item(s), %d equipped%s"),
		Record.Items.Num() - Missing, Record.Equipped.Num(),
		Missing > 0 ? *FString::Printf(TEXT(" (%d definitions no longer exist)"), Missing) : TEXT(""));
}
