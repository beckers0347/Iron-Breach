#include "Combat/HitscanWeaponComponent.h"
#include "IronBreach.h"
#include "Combat/DamageableInterface.h"
#include "Combat/WeaponDataAsset.h"
#include "Components/InputComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/HitResult.h"
#include "TimerManager.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "DrawDebugHelpers.h" // Prototype tracer fallback when no MFXTracer asset is set
#include "Combat/WeaponRigComponent.h"

UHitscanWeaponComponent::UHitscanWeaponComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true); // Required so Server_Fire routes through the owner's channel
}

void UHitscanWeaponComponent::BeginPlay()
{
	Super::BeginPlay();

	if (bAutoBindLegacyInput)
	{
		TryBindInput();
	}
}

void UHitscanWeaponComponent::TryBindInput()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (Pawn && Pawn->InputComponent)
	{
		Pawn->InputComponent->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &UHitscanWeaponComponent::Fire);
		UE_LOG(LogIronBreach, Log, TEXT("%s: hitscan weapon bound to left mouse"), *GetNameSafe(GetOwner()));
		return;
	}

	// Input component may not exist yet at BeginPlay (possession order) — retry shortly.
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(BindRetryHandle, this, &UHitscanWeaponComponent::TryBindInput, 0.25f, false);
	}
}

bool UHitscanWeaponComponent::GetOwnerViewPoint(FVector& OutLocation, FRotator& OutRotation) const
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn) return false;

	if (AController* Controller = Pawn->GetController())
	{
		Controller->GetPlayerViewPoint(OutLocation, OutRotation);
	}
	else
	{
		Pawn->GetActorEyesViewPoint(OutLocation, OutRotation);
	}
	return true;
}

void UHitscanWeaponComponent::Fire()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	UWorld* World = GetWorld();
	if (!Pawn || !World) return;

	// Client-side spam guard (UX only — the server enforces the real cooldown).
	const float UseInterval = WeaponData ? WeaponData->FireRate : FireInterval;
	const float Now = World->GetTimeSeconds();
	if (Now - LastFireTime < FMath::Max(UseInterval, 0.05f)) return;
	LastFireTime = Now;

	// Aim from the local viewpoint — the client's camera is the truth about intent.
	FVector ViewLocation;
	FRotator ViewRotation;
	if (!GetOwnerViewPoint(ViewLocation, ViewRotation)) return;

	// The shooter hears/sees their shot immediately, no round-trip (cosmetic-first).
	// Predicted end point; the server's Multicast_FireFX covers everyone else.
	const float CosmeticRange = WeaponData ? WeaponData->MaxRange : Range;
	PlayFireCosmeticsAt(ViewLocation, ViewLocation + ViewRotation.Vector() * CosmeticRange);

	if (Pawn->HasAuthority())
	{
		// Listen host or standalone: we ARE the server.
		PerformFire(ViewLocation, ViewRotation.Vector());
	}
	else
	{
		Server_Fire(ViewLocation, ViewRotation.Vector());
	}
}

bool UHitscanWeaponComponent::Server_Fire_Validate(FVector_NetQuantize ViewLocation, FVector_NetQuantizeNormal ViewDirection)
{
	// Reject garbage; fine-grained cheat checks (view-location sanity vs pawn) come later.
	return !ViewLocation.ContainsNaN() && !ViewDirection.ContainsNaN() && !ViewDirection.IsNearlyZero();
}

void UHitscanWeaponComponent::Server_Fire_Implementation(FVector_NetQuantize ViewLocation, FVector_NetQuantizeNormal ViewDirection)
{
	PerformFire(ViewLocation, ViewDirection);
}

void UHitscanWeaponComponent::PerformFire(const FVector& ViewLocation, const FVector& ViewDirection)
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	UWorld* World = GetWorld();
	if (!Pawn || !World) return;

	// Authoritative cooldown — a hacked client spamming Server_Fire gains nothing.
	const float UseInterval = WeaponData ? WeaponData->FireRate : FireInterval;
	const float Now = World->GetTimeSeconds();
	if (Now - LastServerFireTime < FMath::Max(UseInterval, 0.05f)) return;
	LastServerFireTime = Now;

	const float UseDamage = WeaponData ? WeaponData->BaseDamage : Damage;
	const float UseRange = WeaponData ? WeaponData->MaxRange : Range;

	// Apply the owner's current spread cone (hip = loose, ADS = tight). Read from
	// the weapon rig if present; no rig -> pinpoint (preserves prior behavior).
	FVector FireDir = ViewDirection.GetSafeNormal();
	if (AActor* Owner = GetOwner())
	{
		if (const UWeaponRigComponent* Rig = Owner->FindComponentByClass<UWeaponRigComponent>())
		{
			const float HalfAngle = Rig->GetCurrentSpreadDegrees();
			if (HalfAngle > KINDA_SMALL_NUMBER)
			{
				FireDir = FMath::VRandCone(FireDir, FMath::DegreesToRadians(HalfAngle));
			}
		}
	}

	const FVector TraceEnd = ViewLocation + FireDir * UseRange;

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(Pawn);

	// ECC_Pawn: pawn capsules ignore ECC_Visibility (see enemy FireAt)
	const bool bHit = World->LineTraceSingleByChannel(HitResult, ViewLocation, TraceEnd, ECC_Pawn, QueryParams);

	UE_LOG(LogIronBreach, Verbose, TEXT("%s fired [auth] (hit: %s)"), *GetNameSafe(Pawn), bHit ? *GetNameSafe(HitResult.GetActor()) : TEXT("none"));

	// Everyone else gets the show (the shooter is skipped inside the multicast).
	Multicast_FireFX(ViewLocation, bHit ? FVector(HitResult.ImpactPoint) : TraceEnd);

	if (bHit && HitResult.GetActor())
	{
		if (HitResult.GetActor()->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass()))
		{
			IDamageableInterface::Execute_HandleTakeDamage(HitResult.GetActor(), UseDamage, HitResult, Pawn->GetController(), Pawn);
		}
		else
		{
			UGameplayStatics::ApplyDamage(HitResult.GetActor(), UseDamage, Pawn->GetController(), Pawn, nullptr);
		}
	}
}

void UHitscanWeaponComponent::Multicast_FireFX_Implementation(FVector_NetQuantize TraceStart, FVector_NetQuantize TraceEnd)
{
	// The shooter already played these cosmetics locally in Fire() — don't double up.
	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (Pawn && Pawn->IsLocallyControlled()) return;

	PlayFireCosmeticsAt(TraceStart, TraceEnd);
}

void UHitscanWeaponComponent::PlayFireCosmeticsAt(const FVector& TraceStart, const FVector& TraceEnd) const
{
	if (!WeaponData) return;

	if (WeaponData->FireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, WeaponData->FireSound, TraceStart);
	}

	if (WeaponData->MFXTracer)
	{
		UNiagaraComponent* Tracer = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
			this, WeaponData->MFXTracer, TraceStart, (TraceEnd - TraceStart).Rotation());
		if (Tracer)
		{
			// Harmless no-op if the Niagara system has no such user parameter.
			Tracer->SetVectorParameter(TEXT("BeamEnd"), TraceEnd);
		}
	}
	else if (UWorld* World = GetWorld())
	{
		// No Niagara asset assigned yet: draw a prototype tracer (Development builds).
		// Assigning WeaponData->MFXTracer later takes over automatically.
		DrawDebugLine(World, TraceStart, TraceEnd, FColor(120, 200, 255), false, 0.06f, 0, 1.0f);
	}
	// TODO: impact FX at TraceEnd once an asset exists in WeaponData.
}
