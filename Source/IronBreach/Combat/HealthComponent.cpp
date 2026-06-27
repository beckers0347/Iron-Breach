#include "HealthComponent.h"

UHealthComponent::UHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // Optimized: No polling on Tick
	CurrentHealth = MaxHealth;
}

void UHealthComponent::BeginPlay()
{
	Super::BeginPlay();
	CurrentHealth = MaxHealth;
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
	}
}