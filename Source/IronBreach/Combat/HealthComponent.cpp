#include "HealthComponent.h"
#include "IronBreach.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h" // Explicit include: DOREPLIFETIME macros

UHealthComponent::UHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // Optimized: No polling on Tick
	SetIsReplicatedByDefault(true);            // Health state flows server -> clients
	CurrentHealth = MaxHealth;
}

void UHealthComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UHealthComponent, MaxHealth);
	DOREPLIFETIME(UHealthComponent, CurrentHealth);
}

void UHealthComponent::BeginPlay()
{
	Super::BeginPlay();

	// Only the authority initializes and accepts damage; clients receive state via replication.
	if (GetOwnerRole() == ROLE_Authority)
	{
		CurrentHealth = MaxHealth;

		// Any actor carrying this component also accepts damage from the generic engine
		// pipeline (e.g. UGameplayStatics::ApplyDamage called from Blueprints/projectiles).
		if (AActor* Owner = GetOwner())
		{
			Owner->OnTakeAnyDamage.AddDynamic(this, &UHealthComponent::HandleAnyDamage);
		}
	}
}

void UHealthComponent::HandleAnyDamage(AActor* DamagedActor, float Damage, const UDamageType* DamageType, AController* InstigatedBy, AActor* DamageCauser)
{
	ApplyDamage(Damage, FHitResult(), InstigatedBy, DamageCauser);
}

void UHealthComponent::ApplyDamage(float Amount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	// Authority rule (ADR-002): clients request, the server decides, replication informs.
	if (GetOwnerRole() != ROLE_Authority) return;
	if (CurrentHealth <= 0.0f || Amount <= 0.0f) return;

	CurrentHealth = FMath::Clamp(CurrentHealth - Amount, 0.0f, MaxHealth);

	// Broadcast to listeners (UI, Post-processing, etc.) on the server/host.
	// Remote clients get the equivalent broadcast from OnRep_CurrentHealth.
	OnHealthChanged.Broadcast(CurrentHealth, MaxHealth, HitResult);

	if (CurrentHealth <= 0.0f && !bDeathHandled)
	{
		bDeathHandled = true;
		OnDeath.Broadcast(DamageCauser);

		if (bRestartLevelOnDeath)
		{
			// Level-restart is a single-player prototype convenience only. In a networked
			// session, reloading the map out from under connected clients is chaos —
			// the open-zone respawn flow (u1-08) owns death there.
			if (GetNetMode() == NM_Standalone)
			{
				UE_LOG(LogIronBreach, Log, TEXT("%s died - restarting level"), *GetNameSafe(GetOwner()));
				UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
			}
			else
			{
				UE_LOG(LogIronBreach, Warning, TEXT("%s died - bRestartLevelOnDeath ignored in networked play (respawn flow TBD, u1-08)"), *GetNameSafe(GetOwner()));
			}
		}
	}
}

void UHealthComponent::OnRep_CurrentHealth(float OldHealth)
{
	// Client-side mirror of the server broadcast so UI/FX listeners work everywhere.
	// No HitResult available on this path — cosmetic hit reactions that need impact data
	// should key off weapon-side effects instead.
	OnHealthChanged.Broadcast(CurrentHealth, MaxHealth, FHitResult());

	if (CurrentHealth <= 0.0f && OldHealth > 0.0f && !bDeathHandled)
	{
		bDeathHandled = true;
		OnDeath.Broadcast(nullptr); // Killer identity is server knowledge (see header note)
	}
}
