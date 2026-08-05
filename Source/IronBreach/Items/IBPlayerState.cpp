#include "Items/IBPlayerState.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"

AIBPlayerState::AIBPlayerState()
{
	InventoryComponent = CreateDefaultSubobject<UIBInventoryComponent>(TEXT("InventoryComponent"));

	// PlayerState's default 1Hz NetUpdateFrequency makes equip/loot feel laggy on
	// clients; inventory changes are bursty, not chatty, so this is cheap.
	SetNetUpdateFrequency(10.0f);
}

void AIBPlayerState::BeginPlay()
{
	Super::BeginPlay();

	// Server decides; grants replicate down. Guard against seamless-travel re-entry.
	if (!HasAuthority() || bStartersGranted || !InventoryComponent) { return; }
	bStartersGranted = true;

	for (const UIBItemDefinition* Def : StarterLoadout)
	{
		if (!Def) { continue; }
		const FIBItemInstance Granted = InventoryComponent->GrantItem(Def);
		if (bAutoEquipStarters && Granted.IsValid() && Def->EquipSlot != EIBEquipSlot::None)
		{
			InventoryComponent->RequestEquip(Granted.InstanceId);
		}
	}
}
