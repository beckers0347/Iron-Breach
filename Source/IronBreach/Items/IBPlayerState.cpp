#include "Items/IBPlayerState.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Player/IBCharacterSubsystem.h"
#include "Progression/IBVaultSubsystem.h"
#include "Progression/IBXPSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"

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

	// Host-side: level-ups on this player's pilot record mirror onto the PlayerState.
	if (HasAuthority())
	{
		if (UGameInstance* GI = GetGameInstance())
		{
			if (UIBXPSubsystem* XP = GI->GetSubsystem<UIBXPSubsystem>())
			{
				XP->OnXPLevelUp.AddDynamic(this, &AIBPlayerState::HandleXPLevelUp);
			}
		}
	}

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

// ---- Operative identity ----

void AIBPlayerState::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (HasAuthority())
	{
		SaveVaultNow(); // logout / travel: the vault is whatever you had in your hands
		if (UGameInstance* GI = GetGameInstance())
		{
			if (UIBXPSubsystem* XP = GI->GetSubsystem<UIBXPSubsystem>())
			{
				XP->OnXPLevelUp.RemoveDynamic(this, &AIBPlayerState::HandleXPLevelUp);
			}
		}
	}
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(VaultSaveHandle);
	}
	Super::EndPlay(EndPlayReason);
}

void AIBPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBPlayerState, OperativeCallsign);
	DOREPLIFETIME(AIBPlayerState, OperativeClass);
	DOREPLIFETIME(AIBPlayerState, OperativeGender);
	DOREPLIFETIME(AIBPlayerState, bHasOperative);
	DOREPLIFETIME(AIBPlayerState, OperativeId);
	DOREPLIFETIME(AIBPlayerState, OperativeLevel);
}

void AIBPlayerState::SetOperativeIdentity(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId)
{
	if (!HasAuthority()) { return; }

	// Never trust the wire: same sanitizer the roster uses, same class gate.
	FString Clean = UIBCharacterSubsystem::SanitizeCallsign(Callsign);
	if (Clean.IsEmpty()) { Clean = TEXT("OPERATIVE"); }
	if (!IBCharacter::ClassAvailable(Class)) { Class = EIBOperativeClass::Breaker; }

	const bool bChanged = !bHasOperative || Clean != OperativeCallsign || Class != OperativeClass
		|| Gender != OperativeGender || CharacterId != OperativeId;

	OperativeCallsign = Clean;
	OperativeClass = Class;
	OperativeGender = Gender;
	OperativeId = CharacterId;
	bHasOperative = true;

	if (bChanged)
	{
		UE_LOG(LogIronBreach, Log, TEXT("%s: operative on station -> %s (%s)"), *GetName(), *OperativeCallsign,
			*IBCharacter::ClassName(OperativeClass).ToString());
		OnRep_Operative(); // listen host / standalone get the same notification clients do

		// This operative's career: vault + level live under their own key on this host.
		bVaultRestored = false;
		RestoreVault();
		if (UGameInstance* GI = GetGameInstance())
		{
			if (UIBXPSubsystem* XP = GI->GetSubsystem<UIBXPSubsystem>())
			{
				SetOperativeLevel(XP->GetPilotLevel(GetOwningController()));
			}
		}
	}
}

void AIBPlayerState::SetOperativeLevel(int32 NewLevel)
{
	if (!HasAuthority()) { return; }
	NewLevel = FMath::Max(1, NewLevel);
	if (NewLevel == OperativeLevel) { return; }
	OperativeLevel = NewLevel;
	OnRep_OperativeLevel();
}

void AIBPlayerState::OnRep_OperativeLevel()
{
	SyncLevelToRoster();
	OnOperativeIdentityChanged.Broadcast(); // banners re-read the level
}

void AIBPlayerState::SyncLevelToRoster()
{
	// Only the machine whose human this is writes the roster (same rule as the ledger).
	const APlayerController* PC = GetPlayerController();
	if (!PC || !PC->IsLocalPlayerController() || !bHasOperative || !OperativeId.IsValid()) { return; }
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UIBCharacterSubsystem* Characters = GI->GetSubsystem<UIBCharacterSubsystem>())
		{
			Characters->SetCharacterLevel(OperativeId, OperativeLevel);
		}
	}
}

void AIBPlayerState::HandleXPLevelUp(EXPTrack Track, const FString& RecordKey, int32 NewLevel, int32 /*OldLevel*/)
{
	if (Track == EXPTrack::Pilot && bHasOperative && RecordKey == MakeProgressionKey())
	{
		SetOperativeLevel(NewLevel);
	}
}

FString AIBPlayerState::MakeProgressionKey() const
{
	return UIBXPSubsystem::MakePlayerKey(GetOwningController());
}

void AIBPlayerState::RestoreVault()
{
	if (!HasAuthority() || bVaultRestored || !InventoryComponent || !bHasOperative) { return; }
	bVaultRestored = true;

	UGameInstance* GI = GetGameInstance();
	UIBVaultSubsystem* Vault = GI ? GI->GetSubsystem<UIBVaultSubsystem>() : nullptr;
	if (!Vault) { return; }

	const FString Key = MakeProgressionKey();
	FIBVaultRecord Record;
	if (Vault->FindVault(Key, Record))
	{
		UIBVaultSubsystem::Restore(InventoryComponent, Record); // the vault is the truth, not the starters
	}
	else
	{
		Vault->StoreVault(Key, UIBVaultSubsystem::Capture(InventoryComponent)); // first deployment: seed it
	}

	if (!bVaultBound)
	{
		bVaultBound = true;
		InventoryComponent->OnInventoryChanged.AddDynamic(this, &AIBPlayerState::HandleInventoryChangedForVault);
		InventoryComponent->OnEquipmentChanged.AddDynamic(this, &AIBPlayerState::HandleEquipmentChangedForVault);
	}
}

void AIBPlayerState::HandleInventoryChangedForVault() { ScheduleVaultSave(); }
void AIBPlayerState::HandleEquipmentChangedForVault(EIBEquipSlot /*Slot*/, const FIBItemInstance& /*Item*/) { ScheduleVaultSave(); }

void AIBPlayerState::ScheduleVaultSave()
{
	// Loot comes in bursts; one write a couple of seconds after the last change.
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(VaultSaveHandle, this, &AIBPlayerState::SaveVaultNow, 2.0f, false);
	}
}

void AIBPlayerState::SaveVaultNow()
{
	if (!HasAuthority() || !bVaultRestored || !InventoryComponent || !bHasOperative) { return; }
	UGameInstance* GI = GetGameInstance();
	if (UIBVaultSubsystem* Vault = GI ? GI->GetSubsystem<UIBVaultSubsystem>() : nullptr)
	{
		Vault->StoreVault(MakeProgressionKey(), UIBVaultSubsystem::Capture(InventoryComponent));
	}
}

void AIBPlayerState::OnRep_Operative()
{
	OnOperativeIdentityChanged.Broadcast();
}

FString AIBPlayerState::GetDisplayCallsign() const
{
	if (bHasOperative && !OperativeCallsign.IsEmpty())
	{
		return OperativeCallsign;
	}
	return GetPlayerName();
}

void AIBPlayerState::CopyProperties(APlayerState* PlayerState)
{
	Super::CopyProperties(PlayerState);

	// Seamless travel hands a fresh PlayerState the old one's soul.
	if (AIBPlayerState* Other = Cast<AIBPlayerState>(PlayerState))
	{
		Other->OperativeCallsign = OperativeCallsign;
		Other->OperativeClass = OperativeClass;
		Other->OperativeGender = OperativeGender;
		Other->bHasOperative = bHasOperative;
		Other->OperativeId = OperativeId;
		Other->OperativeLevel = OperativeLevel;
	}
}

void AIBPlayerState::PushOperativeIdentity(const FIBCharacterRecord& Record)
{
	if (!Record.IsValidRecord()) { return; }

	if (HasAuthority())
	{
		SetOperativeIdentity(Record.Callsign, Record.Class, Record.Gender, Record.CharacterId); // standalone / listen host
	}
	else
	{
		Server_SetOperativeIdentity(Record.Callsign, Record.Class, Record.Gender, Record.CharacterId); // joining client
	}
}

void AIBPlayerState::Server_SetOperativeIdentity_Implementation(const FString& Callsign,
	EIBOperativeClass Class, EIBOperativeGender Gender, const FGuid& CharacterId)
{
	SetOperativeIdentity(Callsign, Class, Gender, CharacterId);
}
