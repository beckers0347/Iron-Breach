#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "IBCharacter_Kaiju.generated.h"

class UHealthComponent;
class UKaijuSpeciesData;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnArmorBrokenSignature);

/**
 * Raid boss kaiju. All species stats come from a UKaijuSpeciesData asset.
 * Damage first chews through armor (ArmorBreak raid phase) before health.
 */
UCLASS()
class IRONBREACH_API AIBCharacter_Kaiju : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	AIBCharacter_Kaiju();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	bool IsArmorBroken() const { return CurrentArmor <= 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	float GetArmorPercent() const;

	UPROPERTY(BlueprintAssignable, Category = "Kaiju|Events")
	FOnArmorBrokenSignature OnArmorBroken;

protected:
	virtual void BeginPlay() override;

	/** Which species this instance is. Assign a DA_Kaiju_* asset.
	 *  Replicated (initial-only) so runtime-spawned kaiju scale correctly on clients
	 *  and join-in-progress players never meet a 1.8m Palawan. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_Species, Category = "Kaiju")
	TObjectPtr<UKaijuSpeciesData> Species;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UHealthComponent> HealthComponent;

	/** Server-authoritative; clients mirror armor-break FX through the OnRep. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_CurrentArmor, Category = "Kaiju")
	float CurrentArmor = 0.0f;

	UFUNCTION()
	void OnRep_Species();

	UFUNCTION()
	void OnRep_CurrentArmor();

	/** BP hooks for roars, FX, phase transitions. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju")
	void BP_OnArmorBroken();

	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju")
	void BP_OnDied(AActor* Killer);

	UFUNCTION()
	void HandleDeath(AActor* Killer);

private:
	void ApplySpecies();

	bool bSpeciesApplied = false;      // ApplySpecies may be reached from BeginPlay AND OnRep
	bool bArmorBreakAnnounced = false; // One armor-break broadcast per machine
};
