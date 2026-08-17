#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBLootPickup.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UIBItemDefinition;
class AIBPlayerState;

/**
 * The engram moment: a physical, rarity-lit drop in the world — PER PLAYER.
 * When owned (the loot component path), only the owning player sees it and
 * only they can collect it; everyone else's machine never even receives it
 * (bOnlyRelevantToOwner) and the listen host hides it locally. Your drop is
 * your drop.
 *
 * Ownerless pickups are the escape hatch: hand-place one in a level (or spawn
 * with a null owner) and it's a shared, visible-to-all, first-come pickup —
 * chest/cache behavior for free.
 *
 * Spawnable as-is: C++ builds a fallback visual (rarity-tinted glowing
 * sphere + point light) so the loop works before any content exists. Shane:
 * make BP_LootPickup when ready — untick bUseFallbackVisuals, add a
 * mesh + Niagara + point light under the root, and drive them from
 * BP_OnLootInitialized (fires wherever the pickup exists, with the rarity
 * color from Project Settings > Iron Breach UI). BP_OnCollected fires
 * server-side just before destruction; the collector's pickup FEEDBACK should
 * come from the inventory's OnItemGranted signal instead (it fires on the
 * collecting player's own machine — the loot toast hook).
 */
UCLASS()
class IRONBREACH_API AIBLootPickup : public AActor
{
	GENERATED_BODY()

public:
	AIBLootPickup();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Authority, before FinishSpawning. InOwningPlayer null = shared pickup
	 *  (anyone sees, anyone takes). Non-null = that player's, exclusively —
	 *  pair it with spawning Owner = their PlayerController so relevancy
	 *  routes it to only their connection. */
	void SetLoot(const UIBItemDefinition* InDefinition, int32 InCount, AIBPlayerState* InOwningPlayer);

	UFUNCTION(BlueprintPure, Category = "Loot")
	const UIBItemDefinition* GetDefinition() const { return Definition; }

	UFUNCTION(BlueprintPure, Category = "Loot")
	int32 GetCount() const { return Count; }

	UFUNCTION(BlueprintPure, Category = "Loot")
	AIBPlayerState* GetOwningPlayer() const { return OwningPlayer; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void OnRep_Loot();

	UFUNCTION()
	void OnRep_OwningPlayer();

	/** Fires wherever the pickup exists once the payload is known. Definition
	 *  can be read for icon/name; RarityColor is pre-resolved from settings —
	 *  feed it to the light/Niagara so a Relic drop reads amber from across
	 *  the field. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Loot", meta = (DisplayName = "On Loot Initialized"))
	void BP_OnLootInitialized(const UIBItemDefinition* InDefinition, int32 InCount, FLinearColor RarityColor);

	/** Server-only, just before Destroy. Collector is the pawn that walked in. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Loot", meta = (DisplayName = "On Collected"))
	void BP_OnCollected(APawn* Collector);

	/** Trigger volume; Shane's visuals attach to the root beside it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Loot")
	TObjectPtr<USphereComponent> CollectionSphere;

	// --- C++ fallback visual (the zero-content floor) ---
	// A small engine-sphere + point light, both tinted the rarity color in
	// OnRep_Loot. BP children with real art untick bUseFallbackVisuals and
	// both components hide themselves.

	UPROPERTY(EditDefaultsOnly, Category = "Loot|Fallback Visual")
	bool bUseFallbackVisuals = true;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Loot|Fallback Visual")
	TObjectPtr<UStaticMeshComponent> FallbackMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Loot|Fallback Visual")
	TObjectPtr<UPointLightComponent> FallbackLight;

	UPROPERTY(EditDefaultsOnly, Category = "Loot", meta = (ClampMin = "10.0"))
	float CollectionRadius = 90.0f;

	/** Uncollected drops despawn (server-timed). 0 = forever — don't. */
	UPROPERTY(EditDefaultsOnly, Category = "Loot", meta = (ClampMin = "0.0"))
	float DespawnSeconds = 300.0f;

	// Cosmetic hover — pure local math on every machine, nothing replicates.
	UPROPERTY(EditDefaultsOnly, Category = "Loot|Motion")
	float BobAmplitude = 12.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Loot|Motion")
	float BobSpeed = 2.0f;

	/** Degrees/second. */
	UPROPERTY(EditDefaultsOnly, Category = "Loot|Motion")
	float SpinSpeed = 45.0f;

private:
	/** Hide + stop ticking when this machine's local player isn't the owner.
	 *  Clients mostly never receive foreign pickups (relevancy), but the
	 *  LISTEN HOST has every server actor locally — without this the host
	 *  would see the whole squad's drops. Collision stays on regardless: the
	 *  server needs the overlap to detect the actual owner walking in. */
	void RefreshLocalVisibility();

	UPROPERTY(ReplicatedUsing = OnRep_Loot)
	TObjectPtr<const UIBItemDefinition> Definition;

	UPROPERTY(Replicated)
	int32 Count = 1;

	/** Null = shared (see class comment). PlayerState, not controller, is the
	 *  replicated identity: it exists on every machine and survives respawn. */
	UPROPERTY(ReplicatedUsing = OnRep_OwningPlayer)
	TObjectPtr<AIBPlayerState> OwningPlayer;

	FVector BaseLocation = FVector::ZeroVector;
	float HoverTime = 0.0f;
	bool bCollected = false;
};
