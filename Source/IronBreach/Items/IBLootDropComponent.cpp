#include "Items/IBLootDropComponent.h"
#include "IronBreach.h"
#include "Combat/HealthComponent.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBLootPickup.h"
#include "Items/IBLootTableAsset.h"
#include "Items/IBPlayerState.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"

void UIBLootDropComponent::BeginPlay()
{
	Super::BeginPlay();

	// Server-only wiring: eligibility (damage contributors) is server
	// knowledge, rolling and granting are authority acts, and the client-side
	// OnDeath re-broadcast arrives with Killer = nullptr anyway.
	if (!GetOwner() || !GetOwner()->HasAuthority()) { return; }

	if (UHealthComponent* Health = GetOwner()->FindComponentByClass<UHealthComponent>())
	{
		Health->OnDeath.AddDynamic(this, &UIBLootDropComponent::HandleOwnerDeath);
	}
	else
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[Loot] %s has an IBLootDrop component but no HealthComponent — nothing will ever drop."),
			*GetNameSafe(GetOwner()));
	}
}

void UIBLootDropComponent::HandleOwnerDeath(AActor* /*Killer*/)
{
	// Killer is unused by design: per-player eligibility supersedes "who
	// landed the last hit" — the contributor set includes the killer anyway.
	if (bDropped) { return; }
	bDropped = true;

	if (!LootTable)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Loot] %s died with no LootTable assigned."), *GetNameSafe(GetOwner()));
		return;
	}

	TArray<AIBPlayerState*> Eligible;
	GatherEligiblePlayers(Eligible);
	if (Eligible.Num() == 0)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Loot] %s: no eligible players resolved — loot skipped."), *GetNameSafe(GetOwner()));
		return;
	}

	// Fallback path: physical requested but no pickup BP exists yet — grant
	// direct instead of silently deleting the payout. Loud, so it gets fixed.
	const bool bPhysical = Delivery == EIBLootDelivery::PhysicalPickups && PickupClass != nullptr;
	if (Delivery == EIBLootDelivery::PhysicalPickups && !PickupClass)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[Loot] %s: PickupClass unset — granting directly instead (MENUS_UI_WIRING.md §8)."),
			*GetNameSafe(GetOwner()));
	}

	// The per-player core: every eligible player rolls the table
	// INDEPENDENTLY. Two hunters, one kaiju, two separate fates — your drop
	// is your drop and nobody can take it.
	int32 TotalRolls = 0;
	for (AIBPlayerState* Player : Eligible)
	{
		const TArray<FIBLootRoll> Rolls = LootTable->Roll();
		if (Rolls.Num() == 0) { continue; } // the table said not today (for this one)
		TotalRolls += Rolls.Num();

		if (bPhysical)
		{
			SpawnPickupsFor(Player, Rolls.GetData(), Rolls.Num());
		}
		else if (UIBInventoryComponent* Inventory = Player->GetInventory())
		{
			for (const FIBLootRoll& LootRoll : Rolls)
			{
				Inventory->GrantItem(LootRoll.Definition, LootRoll.Count);
			}
		}
	}

	UE_LOG(LogIronBreach, Log, TEXT("[Loot] %s: %d roll(s) across %d player(s) (%s)."),
		*GetNameSafe(GetOwner()), TotalRolls, Eligible.Num(),
		bPhysical ? TEXT("pickups") : TEXT("direct"));
}

void UIBLootDropComponent::GatherEligiblePlayers(TArray<AIBPlayerState*>& OutPlayers) const
{
	OutPlayers.Reset();
	const UWorld* World = GetWorld();

	if (Eligibility == EIBLootEligibility::DamageContributors)
	{
		if (const UHealthComponent* Health = GetOwner()->FindComponentByClass<UHealthComponent>())
		{
			TArray<AController*> Contributors;
			Health->GetDamageContributors(Contributors);
			for (const AController* Contributor : Contributors)
			{
				// The PlayerState filter quietly excludes AI controllers —
				// a kaiju that mauls another kaiju is not owed a Doctrine.
				if (AIBPlayerState* PS = Contributor ? Contributor->GetPlayerState<AIBPlayerState>() : nullptr)
				{
					OutPlayers.AddUnique(PS);
				}
			}
		}

		if (OutPlayers.Num() > 0) { return; }
		// Fallback: killed by the environment, a script, or before the
		// contributor patch landed — the payout still happens, for everyone.
		UE_LOG(LogIronBreach, Verbose, TEXT("[Loot] %s: no player contributors — falling back to AllPlayers."), *GetNameSafe(GetOwner()));
	}

	const AGameStateBase* GameState = World ? World->GetGameState() : nullptr;
	if (!GameState) { return; }
	for (APlayerState* PS : GameState->PlayerArray)
	{
		if (AIBPlayerState* IBPS = Cast<AIBPlayerState>(PS))
		{
			OutPlayers.AddUnique(IBPS);
		}
	}
}

void UIBLootDropComponent::SpawnPickupsFor(AIBPlayerState* Player, const FIBLootRoll* Rolls, int32 NumRolls) const
{
	UWorld* World = GetWorld();
	if (!World || !Player) { return; }

	// The pickup's owner (for net relevancy) is the player's CONTROLLER —
	// bOnlyRelevantToOwner routes each drop to exactly one connection, so
	// four players' worth of drops costs the same bandwidth as one.
	APlayerController* OwnerPC = Player->GetPlayerController();
	const FVector Origin = GetOwner()->GetActorLocation();

	for (int32 Index = 0; Index < NumRolls; ++Index)
	{
		// Even ring: N drops read as a payout, not a pile. Same spots for
		// every player — the rings are mutually invisible.
		const float Angle = (2.0f * PI) * (static_cast<float>(Index) / NumRolls) + FMath::FRandRange(0.0f, 0.5f);
		const FVector Offset(FMath::Cos(Angle) * ScatterRadius, FMath::Sin(Angle) * ScatterRadius, SpawnHeightOffset);
		const FTransform SpawnTM(FRotator::ZeroRotator, Origin + Offset);

		// Deferred spawn: payload + ownership must be set BEFORE BeginPlay so
		// relevancy and the server's own init see them, and initial
		// replication carries everything in one packet.
		AIBLootPickup* Pickup = World->SpawnActorDeferred<AIBLootPickup>(
			PickupClass, SpawnTM, OwnerPC, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
		if (!Pickup) { continue; }

		Pickup->SetLoot(Rolls[Index].Definition, Rolls[Index].Count, Player);
		Pickup->FinishSpawning(SpawnTM);
	}
}
