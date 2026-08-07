#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Combat/DamageableInterface.h"
#include "IBCharacter_Kaiju.generated.h"

class UHealthComponent;
class UKaijuSpeciesData;
class UIBKaijuOrganComponent;

/** The shape of the boss fight, in order. Server-authoritative, replicated. */
UENUM(BlueprintType)
enum class EKaijuFightPhase : uint8
{
	Armored		UMETA(DisplayName = "Armored (chew the plating)"),
	OrganPhase	UMETA(DisplayName = "Organ Phase (pop the weak points)"),
	Exposed		UMETA(DisplayName = "Exposed (execute window)"),
	Dead		UMETA(DisplayName = "Dead")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnArmorBrokenSignature);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnKaijuPhaseChangedSignature, EKaijuFightPhase, NewPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnOrganDestroyedSignature, UIBKaijuOrganComponent*, Organ, int32, OrgansRemaining);

/**
 * Raid boss kaiju. All species stats come from a UKaijuSpeciesData asset.
 * Damage first chews through armor (ArmorBreak raid phase) before health.
 */
UCLASS()
class IRONBREACH_API AIBCharacter_Kaiju : public ACharacter, public IDamageableInterface
{
	GENERATED_BODY()

public:
	class UKaijuSpeciesData* GetSpecies() const { return Species; }

	AIBCharacter_Kaiju();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	virtual void HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser) override;

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	bool IsArmorBroken() const { return CurrentArmor <= 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	float GetArmorPercent() const;

	UPROPERTY(BlueprintAssignable, Category = "Kaiju|Events")
	FOnArmorBrokenSignature OnArmorBroken;

	UPROPERTY(BlueprintAssignable, Category = "Kaiju|Events")
	FOnKaijuPhaseChangedSignature OnPhaseChanged;

	UPROPERTY(BlueprintAssignable, Category = "Kaiju|Events")
	FOnOrganDestroyedSignature OnOrganDestroyed;

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	EKaijuFightPhase GetFightPhase() const { return FightPhase; }

	UFUNCTION(BlueprintPure, Category = "Kaiju")
	int32 GetLiveOrganCount() const;

	/** Called by organ OnReps so clients mirror the destroyed beat; server calls it directly. */
	void NotifyOrganDestroyedLocal(UIBKaijuOrganComponent* Organ);

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

	/** The fight's spine. Replicated with an OnRep so every machine plays the beat. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_FightPhase, Category = "Kaiju")
	EKaijuFightPhase FightPhase = EKaijuFightPhase::Armored;

	/** Organs found on this actor at BeginPlay (BP-placed UIBKaijuOrganComponent spheres). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UIBKaijuOrganComponent>> Organs;

	UFUNCTION()
	void OnRep_FightPhase();

	/** Server-only: advance the fight. Broadcasts locally; clients mirror via OnRep. */
	void SetFightPhase(EKaijuFightPhase NewPhase);

	/** BP hooks for roars, FX, phase transitions. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju")
	void BP_OnArmorBroken();

	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju", meta = (DisplayName = "On Phase Changed"))
	void BP_OnPhaseChanged(EKaijuFightPhase NewPhase);

	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju", meta = (DisplayName = "On Organ Destroyed"))
	void BP_OnOrganDestroyed(UIBKaijuOrganComponent* Organ, int32 OrgansRemaining);

	UFUNCTION(BlueprintImplementableEvent, Category = "Kaiju")
	void BP_OnDied(AActor* Killer);

	UFUNCTION()
	void HandleDeath(AActor* Killer);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kaiju", meta = (ClampMin = "0.0"))
	float CorpseLifetime = 8.0f;

private:
	void ApplySpecies();

	/** The character capsule blocks the same trace channel the weapons use, so a
	 *  torso organ INSIDE the capsule never gets hit directly. This extends the
	 *  shot line past the impact point and returns the first live organ whose
	 *  sphere the line passes through — aim at the sac, hit the sac, even when
	 *  the capsule technically caught the trace. Pure math, no second physics query. */
	UIBKaijuOrganComponent* FindOrganAlongShot(const FHitResult& HitResult) const;

	bool bSpeciesApplied = false;      // ApplySpecies may be reached from BeginPlay AND OnRep
	bool bArmorBreakAnnounced = false; // One armor-break broadcast per machine
};
