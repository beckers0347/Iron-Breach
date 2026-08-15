#include "Items/IBInventoryComponent.h"
#include "IronBreach.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBLedgerSubsystem.h"
#include "Items/IBWeaponRack.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Net/UnrealNetwork.h"

// ---- Fast-array client callbacks (mirror locally, HealthComponent OnRep style) ----

void FIBInventoryList::PostReplicatedAdd(const TArrayView<int32>& AddedIndices, int32 FinalSize)
{
	if (!OwnerComponent) { return; }
	for (int32 Index : AddedIndices)
	{
		if (Entries.IsValidIndex(Index))
		{
			OwnerComponent->NotifyItemAddedFromReplication(Entries[Index].Item);
		}
	}
	OwnerComponent->NotifyListChangedFromReplication();
}

void FIBInventoryList::PostReplicatedChange(const TArrayView<int32>& /*ChangedIndices*/, int32 /*FinalSize*/)
{
	if (OwnerComponent) { OwnerComponent->NotifyListChangedFromReplication(); }
}

void FIBInventoryList::PreReplicatedRemove(const TArrayView<int32>& /*RemovedIndices*/, int32 /*FinalSize*/)
{
	if (OwnerComponent) { OwnerComponent->NotifyListChangedFromReplication(); }
}

// ---- Component ----

UIBInventoryComponent::UIBInventoryComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
	InventoryList.OwnerComponent = this;
}

void UIBInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	// Your bag is yours; your equipped kit is public (remote weapon visuals).
	DOREPLIFETIME_CONDITION(UIBInventoryComponent, InventoryList, COND_OwnerOnly);
	DOREPLIFETIME(UIBInventoryComponent, Equipment);
}

bool UIBInventoryComponent::HasAuth() const
{
	const AActor* Owner = GetOwner();
	return Owner && Owner->HasAuthority();
}

FIBItemInstance UIBInventoryComponent::GrantItem(const UIBItemDefinition* Definition, int32 Count)
{
	if (!HasAuth())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Inventory] GrantItem called off-authority — ignored (clients request, the server decides)."));
		return FIBItemInstance();
	}
	if (!Definition || Count <= 0)
	{
		return FIBItemInstance();
	}

	int32 Remaining = Count;
	FIBItemInstance LastTouched;

	// Stackables top up existing stacks first — ALL of them. The previous
	// version clamped into one stack and silently discarded the overflow
	// (grant 5 chitin onto a 98/99 stack: 4 vanished). Loot must never
	// evaporate; whatever doesn't fit spills into fresh stacks below.
	if (Definition->MaxStack > 1)
	{
		for (FIBInventoryEntry& Entry : InventoryList.Entries)
		{
			if (Remaining <= 0) { break; }
			if (Entry.Item.Definition != Definition || Entry.Item.StackCount >= Definition->MaxStack) { continue; }

			const int32 Add = FMath::Min(Definition->MaxStack - Entry.Item.StackCount, Remaining);
			Entry.Item.StackCount += Add;
			Remaining -= Add;
			InventoryList.MarkItemDirty(Entry);
			LastTouched = Entry.Item;
		}
	}

	// Whatever's left becomes new entries (possibly several full stacks).
	while (Remaining > 0)
	{
		FIBInventoryEntry& NewEntry = InventoryList.Entries.AddDefaulted_GetRef();
		NewEntry.Item.InstanceId = FGuid::NewGuid();
		NewEntry.Item.Definition = Definition;
		NewEntry.Item.StackCount = FMath::Min(Remaining, FMath::Max(1, Definition->MaxStack));
		NewEntry.Item.ClearanceRating = Definition->BaseClearanceRating;
		Remaining -= NewEntry.Item.StackCount;
		InventoryList.MarkItemDirty(NewEntry);
		LastTouched = NewEntry.Item;
	}

	UE_LOG(LogIronBreach, Log, TEXT("[Inventory] %s granted %s x%d"),
		*GetNameSafe(GetOwner()), *Definition->GetName(), Count);

	// One fanout per grant call, not per stack touched — a 150-chitin grant is
	// one toast, not two.
	HandleItemAddedLocal(LastTouched);
	OnInventoryChanged.Broadcast();
	return LastTouched;
}

bool UIBInventoryComponent::RemoveItem(FGuid InstanceId, int32 Count)
{
	if (!HasAuth() || Count <= 0) { return false; }

	for (int32 i = 0; i < InventoryList.Entries.Num(); ++i)
	{
		FIBInventoryEntry& Entry = InventoryList.Entries[i];
		if (Entry.Item.InstanceId != InstanceId) { continue; }

		Entry.Item.StackCount -= Count;
		if (Entry.Item.StackCount <= 0)
		{
			// Removing an equipped item clears its slot too.
			for (const FIBEquipmentEntry& Eq : Equipment)
			{
				if (Eq.Item.InstanceId == InstanceId)
				{
					Unequip_OnServer(Eq.Slot);
					break;
				}
			}
			InventoryList.Entries.RemoveAt(i);
			InventoryList.MarkArrayDirty();
		}
		else
		{
			InventoryList.MarkItemDirty(Entry);
		}
		OnInventoryChanged.Broadcast();
		return true;
	}
	return false;
}

// ---- Request seam ----

void UIBInventoryComponent::RequestEquip(FGuid InstanceId)
{
	if (HasAuth()) { Equip_OnServer(InstanceId); }
	else           { Server_Equip(InstanceId); }
}

void UIBInventoryComponent::RequestUnequip(EIBEquipSlot Slot)
{
	if (HasAuth()) { Unequip_OnServer(Slot); }
	else           { Server_Unequip(Slot); }
}

void UIBInventoryComponent::Server_Equip_Implementation(FGuid InstanceId)   { Equip_OnServer(InstanceId); }
void UIBInventoryComponent::Server_Unequip_Implementation(EIBEquipSlot Slot) { Unequip_OnServer(Slot); }

void UIBInventoryComponent::RequestTakeFromRack(AIBWeaponRack* Rack, int32 Index)
{
	if (HasAuth()) { TakeFromRack_OnServer(Rack, Index); }
	else           { Server_TakeFromRack(Rack, Index); }
}

void UIBInventoryComponent::Server_TakeFromRack_Implementation(AIBWeaponRack* Rack, int32 Index)
{
	TakeFromRack_OnServer(Rack, Index);
}

void UIBInventoryComponent::TakeFromRack_OnServer(AIBWeaponRack* Rack, int32 Index)
{
	if (!Rack) { return; }

	// Server_TakeAt is the single source of truth: it re-validates Index against
	// the rack's own replicated stock and (unless bInfiniteStock) removes it, so
	// two players can't both claim the last copy of something in the same frame.
	if (const UIBItemDefinition* Definition = Rack->Server_TakeAt(Index))
	{
		GrantItem(Definition, 1);
	}
}

void UIBInventoryComponent::Equip_OnServer(FGuid InstanceId)
{
	FIBItemInstance Item;
	if (!FindItem(InstanceId, Item) || !Item.Definition || Item.Definition->EquipSlot == EIBEquipSlot::None)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Inventory] Equip rejected — unknown or non-equippable instance."));
		return;
	}
	SetEquipmentSlot(Item.Definition->EquipSlot, Item);
}

void UIBInventoryComponent::Unequip_OnServer(EIBEquipSlot Slot)
{
	SetEquipmentSlot(Slot, FIBItemInstance());
}

void UIBInventoryComponent::SetEquipmentSlot(EIBEquipSlot Slot, const FIBItemInstance& Item)
{
	if (Slot == EIBEquipSlot::None || Slot == EIBEquipSlot::Count) { return; }

	for (FIBEquipmentEntry& Entry : Equipment)
	{
		if (Entry.Slot == Slot)
		{
			Entry.Item = Item;
			OnEquipmentChanged.Broadcast(Slot, Item); // server-local; clients via OnRep
			return;
		}
	}
	FIBEquipmentEntry& NewEntry = Equipment.AddDefaulted_GetRef();
	NewEntry.Slot = Slot;
	NewEntry.Item = Item;
	OnEquipmentChanged.Broadcast(Slot, Item);
}

void UIBInventoryComponent::OnRep_Equipment(const TArray<FIBEquipmentEntry>& OldEquipment)
{
	// Diff old vs new so listeners only hear real changes.
	for (const FIBEquipmentEntry& NewEntry : Equipment)
	{
		const FIBEquipmentEntry* Old = OldEquipment.FindByPredicate(
			[&NewEntry](const FIBEquipmentEntry& E) { return E.Slot == NewEntry.Slot; });
		const bool bChanged = !Old
			|| Old->Item.InstanceId != NewEntry.Item.InstanceId
			|| Old->Item.Definition != NewEntry.Item.Definition;
		if (bChanged)
		{
			OnEquipmentChanged.Broadcast(NewEntry.Slot, NewEntry.Item);
		}
	}
}

// ---- Queries ----

TArray<FIBItemInstance> UIBInventoryComponent::GetAllItems() const
{
	TArray<FIBItemInstance> Out;
	Out.Reserve(InventoryList.Entries.Num());
	for (const FIBInventoryEntry& Entry : InventoryList.Entries)
	{
		Out.Add(Entry.Item);
	}
	return Out;
}

TArray<FIBItemInstance> UIBInventoryComponent::GetItemsByCategory(EIBItemCategory Category) const
{
	TArray<FIBItemInstance> Out;
	for (const FIBInventoryEntry& Entry : InventoryList.Entries)
	{
		if (Entry.Item.Definition && Entry.Item.Definition->Category == Category)
		{
			Out.Add(Entry.Item);
		}
	}
	return Out;
}

bool UIBInventoryComponent::FindItem(FGuid InstanceId, FIBItemInstance& OutItem) const
{
	for (const FIBInventoryEntry& Entry : InventoryList.Entries)
	{
		if (Entry.Item.InstanceId == InstanceId)
		{
			OutItem = Entry.Item;
			return true;
		}
	}
	return false;
}

bool UIBInventoryComponent::GetEquippedItem(EIBEquipSlot Slot, FIBItemInstance& OutItem) const
{
	for (const FIBEquipmentEntry& Entry : Equipment)
	{
		if (Entry.Slot == Slot && Entry.Item.IsValid())
		{
			OutItem = Entry.Item;
			return true;
		}
	}
	return false;
}

int32 UIBInventoryComponent::GetTotalClearanceRating() const
{
	int32 Total = 0;
	for (const FIBEquipmentEntry& Entry : Equipment)
	{
		if (Entry.Item.IsValid())
		{
			Total += Entry.Item.ClearanceRating;
		}
	}
	return Total;
}

// ---- Replication-side local fanout ----

void UIBInventoryComponent::NotifyListChangedFromReplication()
{
	OnInventoryChanged.Broadcast();
}

void UIBInventoryComponent::NotifyItemAddedFromReplication(const FIBItemInstance& Item)
{
	HandleItemAddedLocal(Item);
}

void UIBInventoryComponent::HandleItemAddedLocal(const FIBItemInstance& Item)
{
	OnItemGranted.Broadcast(Item);

	// Ledger discovery is a LOCAL-PROFILE concern: only the machine whose human
	// owns this inventory writes its ledger. GetPlayerController() returns null
	// for remote clients' player states, which filters exactly right.
	const APlayerState* PS = Cast<APlayerState>(GetOwner());
	APlayerController* PC = PS ? PS->GetPlayerController() : nullptr;
	if (PC && PC->IsLocalPlayerController() && Item.Definition)
	{
		if (UGameInstance* GI = GetWorld() ? GetWorld()->GetGameInstance() : nullptr)
		{
			if (UIBLedgerSubsystem* Ledger = GI->GetSubsystem<UIBLedgerSubsystem>())
			{
				Ledger->MarkDiscovered(Item.Definition);
			}
		}
	}
}
