#include "Kaiju/IBCharacter_Kaiju.h"
#include "Kaiju/KaijuSpeciesData.h"
#include "Kaiju/IBKaijuOrganComponent.h"
#include "IronBreach.h"
#include "Combat/HealthComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h" // Explicit include: DOREPLIFETIME macros
#include "Engine/GameInstance.h"
#include "Progression/IBXPSubsystem.h"

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
	DOREPLIFETIME(AIBCharacter_Kaiju, FightPhase);
}

void AIBCharacter_Kaiju::BeginPlay()
{
	ApplySpecies();

	// Anatomy census: every organ sphere the BP placed on this body.
	Organs.Reset();
	GetComponents(Organs);
	if (HasAuthority())
	{
		const float OrganHP = Species ? Species->OrganHealth : 4000.0f;
		for (UIBKaijuOrganComponent* Organ : Organs)
		{
			if (Organ) Organ->InitOrgan(OrganHP);
		}
		if (Species && Organs.Num() != Species->OrganCount)
		{
			UE_LOG(LogIronBreach, Warning, TEXT("%s: species says %d organs, BP has %d placed"),
				*GetName(), Species->OrganCount, Organs.Num());
		}
	}

	if (HealthComponent)
	{
		HealthComponent->OnDeath.AddDynamic(this, &AIBCharacter_Kaiju::HandleDeath);
	}

	Super::BeginPlay();
}

UIBKaijuOrganComponent* AIBCharacter_Kaiju::FindOrganAlongShot(const FHitResult& HitResult) const
{
	FVector Dir = HitResult.ImpactPoint - HitResult.TraceStart;
	if (!Dir.Normalize()) return nullptr; // Fabricated hit (melee/scripted) with no trace line — no probe

	// A chord through the widest part of the capsule bounds how deep any organ can sit.
	const float CapR = GetCapsuleComponent() ? GetCapsuleComponent()->GetScaledCapsuleRadius() : 500.0f;
	const FVector A = HitResult.ImpactPoint;
	const FVector B = A + Dir * (CapR * 2.0f);

	UIBKaijuOrganComponent* Best = nullptr;
	float BestDist = TNumericLimits<float>::Max();
	for (UIBKaijuOrganComponent* Organ : Organs)
	{
		if (!Organ || Organ->IsOrganDestroyed()) continue;
		const FVector C = Organ->GetComponentLocation();
		if (FMath::PointDistToSegment(C, A, B) > Organ->GetScaledSphereRadius()) continue;
		const float Along = static_cast<float>(FVector::DotProduct(C - A, Dir));
		if (Along < BestDist) { BestDist = Along; Best = Organ; } // First organ along the shot wins
	}
	return Best;
}

int32 AIBCharacter_Kaiju::GetLiveOrganCount() const
{
	int32 N = 0;
	for (const UIBKaijuOrganComponent* Organ : Organs)
	{
		if (Organ && !Organ->IsOrganDestroyed()) ++N;
	}
	return N;
}

void AIBCharacter_Kaiju::SetFightPhase(EKaijuFightPhase NewPhase)
{
	if (!HasAuthority()) return;
	if (FightPhase == NewPhase || FightPhase == EKaijuFightPhase::Dead) return; // Dead is terminal

	FightPhase = NewPhase;
	UE_LOG(LogIronBreach, Log, TEXT("%s fight phase -> %s"), *GetName(), *UEnum::GetValueAsString(NewPhase));

	// Server/listen-host hears it now; remote clients via OnRep_FightPhase.
	OnPhaseChanged.Broadcast(FightPhase);
	BP_OnPhaseChanged(FightPhase);
}

void AIBCharacter_Kaiju::OnRep_FightPhase()
{
	OnPhaseChanged.Broadcast(FightPhase);
	BP_OnPhaseChanged(FightPhase);
}

void AIBCharacter_Kaiju::NotifyOrganDestroyedLocal(UIBKaijuOrganComponent* Organ)
{
	const int32 Remaining = GetLiveOrganCount();
	OnOrganDestroyed.Broadcast(Organ, Remaining);
	BP_OnOrganDestroyed(Organ, Remaining);
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
	if (FightPhase == EKaijuFightPhase::Dead) return;

	// Phase 1 (Armored): the plating soaks all damage until it shatters. This bypasses
	// UHealthComponent entirely, so it needs its own XP report -- HealthComponent::
	// ApplyDamage only ever sees post-armor (health-phase) damage on a kaiju.
	if (CurrentArmor > 0.0f)
	{
		CurrentArmor = FMath::Max(CurrentArmor - DamageAmount, 0.0f);
		const bool bJustBroke = (CurrentArmor <= 0.0f && !bArmorBreakAnnounced);

		if (UGameInstance* GI = GetGameInstance())
		{
			if (UIBXPSubsystem* XP = GI->GetSubsystem<UIBXPSubsystem>())
			{
				XP->ReportKaijuArmorDamage(DamageAmount, InstigatedBy, DamageCauser, bJustBroke);
			}
		}

		if (bJustBroke)
		{
			bArmorBreakAnnounced = true;
			UE_LOG(LogIronBreach, Log, TEXT("%s armor BROKEN"), *GetName());
			OnArmorBroken.Broadcast();
			BP_OnArmorBroken();
			SetFightPhase(GetLiveOrganCount() > 0 ? EKaijuFightPhase::OrganPhase : EKaijuFightPhase::Exposed);
		}
		return; // The breaking hit is spent on the plate
	}

	// Zero-armor species (or none assigned) never get a breaking hit — advance on first contact.
	if (FightPhase == EKaijuFightPhase::Armored)
	{
		SetFightPhase(GetLiveOrganCount() > 0 ? EKaijuFightPhase::OrganPhase : EKaijuFightPhase::Exposed);
	}

	if (!HealthComponent) return;

	// Phase 2 (OrganPhase): pop the weak points; the body is hardened meanwhile.
	if (FightPhase == EKaijuFightPhase::OrganPhase)
	{
		UIBKaijuOrganComponent* Organ = Cast<UIBKaijuOrganComponent>(HitResult.GetComponent());
		if (!Organ || !Organs.Contains(Organ) || Organ->IsOrganDestroyed())
		{
			Organ = FindOrganAlongShot(HitResult); // capsule may have caught a shot aimed at a buried organ
		}
		if (Organ)
		{
			if (Organ->ApplyOrganDamage(DamageAmount))
			{
				// The pop: kaiju-level beat + a real chunk off the boss's health bar.
				NotifyOrganDestroyedLocal(Organ);
				if (Species && Species->OrganBreakDamagePercent > 0.0f)
				{
					HealthComponent->ApplyDamage(Species->MaxHealth * Species->OrganBreakDamagePercent, HitResult, InstigatedBy, DamageCauser);
				}
				// Chunk damage can be lethal — only advance if the fight is still on.
				if (FightPhase == EKaijuFightPhase::OrganPhase && GetLiveOrganCount() == 0)
				{
					SetFightPhase(EKaijuFightPhase::Exposed);
				}
			}
			return;
		}

		const float HardMult = Species ? Species->HardenedBodyMultiplier : 1.0f;
		HealthComponent->ApplyDamage(DamageAmount * HardMult, HitResult, InstigatedBy, DamageCauser);
		return;
	}

	// Phase 3 (Exposed): the execute window — everything hits harder until it dies.
	const float ExpMult = Species ? Species->ExposedDamageMultiplier : 1.0f;
	HealthComponent->ApplyDamage(DamageAmount * ExpMult, HitResult, InstigatedBy, DamageCauser);
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

	// Terminal phase; clients hear it through the OnRep.
	SetFightPhase(EKaijuFightPhase::Dead);

	// Cosmetic, runs on every machine.
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->StopMovementImmediately();
		GetCharacterMovement()->DisableMovement();
	}

	// The corpse stops eating bullets and stops blocking the player.
	if (GetCapsuleComponent())
	{
		GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	BP_OnDied(Killer);

	// Authority schedules removal; actor destruction replicates to clients on its own.
	if (HasAuthority())
	{
		SetLifeSpan(FMath::Max(CorpseLifetime, 0.1f));
	}
}
