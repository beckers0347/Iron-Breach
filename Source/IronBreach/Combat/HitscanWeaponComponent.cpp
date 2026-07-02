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

UHitscanWeaponComponent::UHitscanWeaponComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UHitscanWeaponComponent::BeginPlay()
{
	Super::BeginPlay();
	TryBindInput();
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

void UHitscanWeaponComponent::Fire()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	UWorld* World = GetWorld();
	if (!Pawn || !World) return;

	const float UseDamage = WeaponData ? WeaponData->BaseDamage : Damage;
	const float UseRange = WeaponData ? WeaponData->MaxRange : Range;
	const float UseInterval = WeaponData ? WeaponData->FireRate : FireInterval;

	const float Now = World->GetTimeSeconds();
	if (Now - LastFireTime < FMath::Max(UseInterval, 0.05f)) return;
	LastFireTime = Now;

	if (WeaponData && WeaponData->FireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, WeaponData->FireSound, Pawn->GetActorLocation());
	}

	// Aim from the player camera
	FVector ViewLocation;
	FRotator ViewRotation;
	if (AController* Controller = Pawn->GetController())
	{
		Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
	}
	else
	{
		Pawn->GetActorEyesViewPoint(ViewLocation, ViewRotation);
	}

	const FVector TraceEnd = ViewLocation + ViewRotation.Vector() * UseRange;

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(Pawn);

	// ECC_Pawn: pawn capsules ignore ECC_Visibility (see enemy FireAt)
	const bool bHit = World->LineTraceSingleByChannel(HitResult, ViewLocation, TraceEnd, ECC_Pawn, QueryParams);

	UE_LOG(LogIronBreach, Verbose, TEXT("%s player fired (hit: %s)"), *GetNameSafe(Pawn), bHit ? *GetNameSafe(HitResult.GetActor()) : TEXT("none"));

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
