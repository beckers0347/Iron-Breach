#include "Kaiju/IBCharacter_Kaiju.h"
#include "Kaiju/KaijuSpeciesData.h"
#include "IronBreach.h"
#include "Combat/HealthComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h" // Explicit include: DOREPLIFETIME macros

AIBCharacter_Kaiju::AIBCharacter_Kaiju()
{
	PrimaryActorTick.bCanEverTick = false;

	bReplicates = true; // Explicit for clarity (ACharacter defaults on) — the kaiju is server-owned truth

	HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("HealthComponent"));

	bUseControllerRotationYaw = false;
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->bOrientRotationToMovement = true;
		GetCharacterMovement()->RotationRate = FRotator(0.0f, 45.0f, 0.0f); // Ponderous turning
	}
}

void AIBCharacter_Kaiju::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	// Species never changes after spawn; ship it once with the initial bunch.
	DOREPLIFETIME_CONDITION(AIBCharacter_Kaiju, Species, COND_InitialOnly);
	DOREPLIFETIME(AIBCharacter_Kaiju, CurrentArmor);
}

void AIBCharacter_Kaiju::BeginPlay()
{
	ApplySpecies();

	if (HealthComponent)
	{
		HealthComponent->OnDeath.AddDynamic(this, &AIBCharacter_Kaiju::HandleDeath);
	}

	Super::BeginPlay();
}

void AIBCharacter_Kaiju::ApplySpecies()
{
	if (!Species)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("%s has no KaijuSpeciesData assigned"), *GetName());
		return;
	}
	if (bSpeciesApplied) return; // BeginPlay and OnRep_Species can both land here
	bSpeciesApplied = true;

	// Gameplay state is authority-only. On clients the replicated values are the truth —
	// a late joiner must NOT reset a half-broken armor pool back to full.
	if (HasAuthority())
	{
		CurrentArmor = Species->ArmorHealth;

		if (HealthComponent)
		{
			HealthComponent->SetMaxHealth(Species->MaxHealth);
		}
	}

	// Size the beast: scale the whole actor from the species height
	SetActorScale3D(FVector(Species->GetScaleFactor()));

	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		if (Species->Mesh)
		{
			MeshComp->SetSkeletalMesh(Species->Mesh);
		}
		if (Species->AnimClass)
		{
			MeshComp->SetAnimInstanceClass(Species->AnimClass);
		}
	}

	if (GetCharacterMovement())
	{
		GetCharacterMovement()->MaxWalkSpeed = Species->WalkSpeed;
	}

	UE_LOG(LogIronBreach, Log, TEXT("Kaiju %s spawned: %s, %.0fm, %d organs"),
		*GetName(), *Species->SpeciesName.ToString(), Species->HeightMeters, Species->OrganCount);
}

float AIBCharacter_Kaiju::GetArmorPercent() const
{
	const float Max = Species ? FMath::Max(Species->ArmorHealth, 1.0f) : 1.0f;
	return FMath::Clamp(CurrentArmor / Max, 0.0f, 1.0f);
}

void AIBCharacter_Kaiju::HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	// Authority rule (ADR-002): only the server mutates armor/health.
	if (!HasAuthority()) return;

	// Phase 1 (ArmorBreak): armor soaks all damage until it shatters
	if (CurrentArmor > 0.0f)
	{
		CurrentArmor = FMath::Max(CurrentArmor - DamageAmount, 0.0f);
		if (CurrentArmor <= 0.0f && !bArmorBreakAnnounced)
		{
			bArmorBreakAnnounced = true;
			UE_LOG(LogIronBreach, Log, TEXT("%s armor BROKEN"), *GetName());
			OnArmorBroken.Broadcast();
			BP_OnArmorBroken();
		}
		return;
	}

	// Armor gone: health takes damage (OrganDisable and beyond)
	if (HealthComponent)
	{
		HealthComponent->ApplyDamage(DamageAmount, HitResult, InstigatedBy, DamageCauser);
	}
}

void AIBCharacter_Kaiju::OnRep_Species()
{
	// Runtime-spawned kaiju: the species reference just arrived — size the beast locally.
	ApplySpecies();
}

void AIBCharacter_Kaiju::OnRep_CurrentArmor()
{
	// Clients mirror the armor-break moment for roars/FX/HUD.
	if (CurrentArmor <= 0.0f && !bArmorBreakAnnounced)
	{
		bArmorBreakAnnounced = true;
		OnArmorBroken.Broadcast();
		BP_OnArmorBroken();
	}
}

void AIBCharacter_Kaiju::HandleDeath(AActor* Killer)
{
	UE_LOG(LogIronBreach, Log, TEXT("Kaiju %s has fallen"), *GetName());

	if (GetCharacterMovement())
	{
		GetCharacterMovement()->StopMovementImmediately();
		GetCharacterMovement()->DisableMovement();
	}

	BP_OnDied(Killer);
}
