#include "Items/IBLootPickup.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "UI/IBUISettings.h"
#include "Components/SphereComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"

AIBLootPickup::AIBLootPickup()
{
	PrimaryActorTick.bCanEverTick = true; // hover is cosmetic, but constant

	bReplicates = true;
	// Location replicates once at spawn; the bob/spin is identical local math
	// on every machine, so movement replication would be pure waste.
	SetReplicatingMovement(false);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	CollectionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("CollectionSphere"));
	CollectionSphere->SetupAttachment(Root);
	CollectionSphere->SetSphereRadius(CollectionRadius);
	// Pawn-only overlap: bullets, kaiju, and debris shouldn't "collect" loot.
	CollectionSphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	CollectionSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
	CollectionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void AIBLootPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBLootPickup, Definition);
	DOREPLIFETIME(AIBLootPickup, Count);
	DOREPLIFETIME(AIBLootPickup, OwningPlayer);
}

void AIBLootPickup::SetLoot(const UIBItemDefinition* InDefinition, int32 InCount, AIBPlayerState* InOwningPlayer)
{
	if (!HasAuthority()) { return; }
	Definition = InDefinition;
	Count = FMath::Max(1, InCount);
	OwningPlayer = InOwningPlayer;

	// Owned drops replicate to exactly one connection — the owning player's.
	// Not just bandwidth: a client that never receives an actor cannot render,
	// probe, or exploit it. Ownerless (shared/hand-placed) pickups keep
	// default relevancy and go to everyone. (Direct member write: the setter's
	// name has drifted across engine versions; the public bool hasn't.)
	bOnlyRelevantToOwner = (OwningPlayer != nullptr);
}

void AIBLootPickup::BeginPlay()
{
	Super::BeginPlay();

	BaseLocation = GetActorLocation();
	HoverTime = FMath::FRand() * 10.0f; // desync bobbing across a drop ring
	CollectionSphere->SetSphereRadius(CollectionRadius);

	// Hide-first: on a listen host, foreign drops exist locally, and the BP
	// init below must fire on an ALREADY-hidden actor (else a spawn flash or
	// sound in Shane's On Loot Initialized would leak the squad's drops).
	RefreshLocalVisibility();

	if (HasAuthority())
	{
		CollectionSphere->OnComponentBeginOverlap.AddDynamic(this, &AIBLootPickup::HandleOverlap);
		if (DespawnSeconds > 0.0f)
		{
			SetLifeSpan(DespawnSeconds); // replicated teardown for free
		}
		// Server has the payload immediately; clients get it via the OnReps.
		OnRep_Loot();
	}
}

void AIBLootPickup::OnRep_Loot()
{
	if (!Definition) { return; }

	// Pre-resolve the rarity color so the BP never touches settings plumbing.
	const FLinearColor RarityColor = UIBUISettings::Get()->GetRarityColor(Definition->Rarity);
	BP_OnLootInitialized(Definition, Count, RarityColor);
}

void AIBLootPickup::OnRep_OwningPlayer()
{
	// PlayerState references can resolve a beat after the actor arrives
	// (separate channel) — re-evaluate whenever it lands.
	RefreshLocalVisibility();
}

void AIBLootPickup::RefreshLocalVisibility()
{
	// "Is the human at THIS machine the owner?" — one local player per
	// machine in this project, so first PC is the local human. Host and
	// client take the same path. Ownerless = everyone's.
	const APlayerController* LocalPC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	const bool bForLocalPlayer =
		!OwningPlayer || (LocalPC && LocalPC->PlayerState == OwningPlayer);

	SetActorHiddenInGame(!bForLocalPlayer);
	SetActorTickEnabled(bForLocalPlayer); // no point bobbing what nobody sees
	// Collision untouched: the server instance (which on a listen host is the
	// hidden one) still needs the overlap to award the real owner.
}

void AIBLootPickup::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	HoverTime += DeltaSeconds;
	FVector NewLocation = BaseLocation;
	NewLocation.Z += FMath::Sin(HoverTime * BobSpeed) * BobAmplitude;
	SetActorLocation(NewLocation);
	AddActorLocalRotation(FRotator(0.0f, SpinSpeed * DeltaSeconds, 0.0f));
}

void AIBLootPickup::HandleOverlap(UPrimitiveComponent* /*OverlappedComponent*/, AActor* OtherActor,
	UPrimitiveComponent* /*OtherComp*/, int32 /*OtherBodyIndex*/, bool /*bFromSweep*/, const FHitResult& /*SweepResult*/)
{
	// Bound on authority only, but belt-and-braces: grants are server acts.
	if (!HasAuthority() || bCollected) { return; }

	APawn* Pawn = Cast<APawn>(OtherActor);
	AIBPlayerState* PS = Pawn ? Pawn->GetPlayerState<AIBPlayerState>() : nullptr;
	UIBInventoryComponent* Inventory = PS ? PS->GetInventory() : nullptr;
	if (!Inventory || !Definition)
	{
		// AI pawns / kaiju stepping through, or a player without the project
		// PlayerState: leave the drop for someone who can carry it.
		return;
	}

	// The per-player gate: not yours, not collectible. (You also can't SEE
	// it — this catches the blind walk-through.)
	if (OwningPlayer && PS != OwningPlayer)
	{
		return;
	}

	bCollected = true; // re-entrancy guard: two pawns in one frame, one payout
	Inventory->GrantItem(Definition, Count);
	UE_LOG(LogIronBreach, Log, TEXT("[Loot] %s x%d collected by %s%s"),
		*GetNameSafe(Definition), Count, *GetNameSafe(Pawn),
		OwningPlayer ? TEXT(" (owned drop)") : TEXT(" (shared drop)"));

	BP_OnCollected(Pawn);
	Destroy(); // replicates; the collector's FEEDBACK rides OnItemGranted
}
