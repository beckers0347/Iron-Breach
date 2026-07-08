#include "Enemy/IBCharacter_Enemy.h"
#include "Enemy/IBEnemyAIController.h"
#include "IronBreach.h"
#include "Combat/HealthComponent.h"
#include "Combat/WeaponDataAsset.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/HitResult.h"
#include "DrawDebugHelpers.h" // Prototype tracer via DrawDebugLine (dev builds)

AIBCharacter_Enemy::AIBCharacter_Enemy()
{
	PrimaryActorTick.bCanEverTick = false;

	HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("HealthComponent"));

	// AI possession
	AIControllerClass = AIBEnemyAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// Face movement direction while patrolling/chasing
	bUseControllerRotationYaw = false;
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->bOrientRotationToMovement = true;
		GetCharacterMovement()->RotationRate = FRotator(0.0f, 400.0f, 0.0f);
	}
}

void AIBCharacter_Enemy::BeginPlay()
{
	if (HealthComponent)
	{
		HealthComponent->SetMaxHealth(EnemyMaxHealth);
		HealthComponent->OnDeath.AddDynamic(this, &AIBCharacter_Enemy::HandleDeath);
	}

	Super::BeginPlay(); // HealthComponent's BeginPlay copies MaxHealth into CurrentHealth
}

void AIBCharacter_Enemy::FireAt(AActor* Target)
{
	if (bDead || !Target || !CurrentWeaponData) return;

	UWorld* World = GetWorld();
	if (!World) return;

	// Respect the weapon's fire rate
	const float Now = World->GetTimeSeconds();
	if (Now - LastFireTime < FMath::Max(CurrentWeaponData->FireRate, 0.05f)) return;
	LastFireTime = Now;

	UE_LOG(LogIronBreach, Verbose, TEXT("%s fires at %s"), *GetName(), *GetNameSafe(Target));

	// Aim from our eyes at the target's center, with a bit of spread
	FVector EyeLocation;
	FRotator EyeRotation;
	GetActorEyesViewPoint(EyeLocation, EyeRotation);

	const FVector TargetPoint = Target->GetActorLocation();
	const FVector AimDir = FMath::VRandCone((TargetPoint - EyeLocation).GetSafeNormal(), FMath::DegreesToRadians(AimSpreadDegrees));
	const FVector TraceEnd = EyeLocation + AimDir * CurrentWeaponData->MaxRange;

	// FireAt only runs on the server (AI controllers don't exist on clients) — the
	// multicast makes the shot audible/visible on every machine, including this one.
	Multicast_FireFX(TraceEnd);

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this);

	// ECC_Pawn: pawn capsules ignore ECC_Visibility, so a visibility trace flies straight through characters.
	const bool bHit = World->LineTraceSingleByChannel(HitResult, EyeLocation, TraceEnd, ECC_Pawn, QueryParams);

	if (bHit && HitResult.GetActor())
	{
		if (HitResult.GetActor()->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass()))
		{
			IDamageableInterface::Execute_HandleTakeDamage(HitResult.GetActor(), CurrentWeaponData->BaseDamage, HitResult, GetController(), this);
		}
		else
		{
			// Fallback: generic engine damage so non-interface actors (e.g. the template player BP) still get hurt
			UGameplayStatics::ApplyDamage(HitResult.GetActor(), CurrentWeaponData->BaseDamage, GetController(), this, nullptr);
		}
	}
}

void AIBCharacter_Enemy::Multicast_FireFX_Implementation(FVector_NetQuantize TraceEnd)
{
	if (!CurrentWeaponData) return;

	if (CurrentWeaponData->FireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, CurrentWeaponData->FireSound, GetActorLocation());
	}

	// Visible tracer. Start = this enemy's muzzle/eye (pawn position replicates, so this is
	// accurate on every client). Prototype line for now; swap to a Niagara beam later by
	// spawning CurrentWeaponData->MFXTracer here instead. DrawDebugLine renders in
	// Development builds (compiled out of Shipping — fine for playtesting).
	if (UWorld* World = GetWorld())
	{
		FVector EyeLocation;
		FRotator EyeRotation;
		GetActorEyesViewPoint(EyeLocation, EyeRotation);
		DrawDebugLine(World, EyeLocation, TraceEnd, FColor(255, 150, 40), false, 0.08f, 0, 1.5f);
	}
}

void AIBCharacter_Enemy::HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	if (bDead) return;

	if (HealthComponent)
	{
		HealthComponent->ApplyDamage(DamageAmount, HitResult, InstigatedBy, DamageCauser);
	}

	BP_OnDamaged(HitResult, DamageCauser);

	// Getting shot reveals the attacker
	if (AIBEnemyAIController* EnemyController = Cast<AIBEnemyAIController>(GetController()))
	{
		EnemyController->NotifyDamagedBy(InstigatedBy, DamageCauser);
	}
}

void AIBCharacter_Enemy::HandleDeath(AActor* Killer)
{
	if (bDead) return;
	bDead = true;

	UE_LOG(LogIronBreach, Log, TEXT("%s died (killer: %s)"), *GetName(), Killer ? *Killer->GetName() : TEXT("none"));

	// Stop the brain
	DetachFromControllerPendingDestroy();

	// Stop moving, drop collision on the capsule
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->StopMovementImmediately();
		GetCharacterMovement()->DisableMovement();
	}
	if (GetCapsuleComponent())
	{
		GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	// Ragdoll
	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		MeshComp->SetCollisionProfileName(TEXT("Ragdoll"));
		MeshComp->SetSimulatePhysics(true);
	}

	BP_OnDied(Killer);

	SetLifeSpan(15.0f); // Clean up the corpse
}
