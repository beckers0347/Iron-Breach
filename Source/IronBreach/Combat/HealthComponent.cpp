#include "HealthComponent.h"
#include "IronBreach.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"

UHealthComponent::UHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // Optimized: No polling on Tick
	CurrentHealth = MaxHealth;
}

void UHealthComponent::BeginPlay()
{
	Super::BeginPlay();
	CurrentHealth = MaxHealth;

	// Any actor carrying this component also accepts damage from the generic engine
	// pipeline (e.g. UGameplayStatics::ApplyDamage called from Blueprints/projectiles).
	if (AActor* Owner = GetOwner())
	{
		Owner->OnTakeAnyDamage.AddDynamic(this, &UHealthComponent::HandleAnyDamage);
	}
}

void UHealthComponent::HandleAnyDamage(AActor* DamagedActor, float Damage, const UDamageType* DamageType, AController* InstigatedBy, AActor* DamageCauser)
{
	ApplyDamage(Damage, FHitResult(), InstigatedBy, DamageCauser);
}

void UHealthComponent::ApplyDamage(float Amount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	if (CurrentHealth <= 0.0f || Amount <= 0.0f) return;

	CurrentHealth = FMath::Clamp(CurrentHealth - Amount, 0.0f, MaxHealth);

	// Broadcast to listeners (UI, Post-processing, etc.)
	OnHealthChanged.Broadcast(CurrentHealth, MaxHealth, HitResult);

	if (CurrentHealth <= 0.0f)
	{
		OnDeath.Broadcast(DamageCauser);

		if (bRestartLevelOnDeath)
		{
			UE_LOG(LogIronBreach, Log, TEXT("%s died - restarting level"), *GetNameSafe(GetOwner()));
			UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
		}
	}
}
