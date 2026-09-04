#include "Classes/IBOperativeKitComponent.h"
#include "Classes/IBClassKitData.h"
#include "Classes/IBKitZone.h"
#include "Combat/DamageableInterface.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Items/IBPlayerState.h"
#include "UI/IBKitHudWidget.h"
#include "IronBreach.h"
#include "Blueprint/UserWidget.h"
#include "Components/InputComponent.h"
#include "EnhancedInputComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "Kismet/KismetSystemLibrary.h"
#include "TimerManager.h"

UIBOperativeKitComponent::UIBOperativeKitComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = 0.25f; // HUD spawn + housekeeping only; effects are event-driven
	SetIsReplicatedByDefault(true);

	KitAbilityKey = EKeys::Q;
	MovementToolKey = EKeys::V;

	// Designer-owned kits, one asset per trade; absent assets fall back to DefaultKitFor.
	KitData.Add(EIBOperativeClass::Breaker,    TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Breaker.DA_Kit_Breaker"))));
	KitData.Add(EIBOperativeClass::Picket,     TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Picket.DA_Kit_Picket"))));
	KitData.Add(EIBOperativeClass::Bellringer, TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Bellringer.DA_Kit_Bellringer"))));
	KitData.Add(EIBOperativeClass::Corpsman,   TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Corpsman.DA_Kit_Corpsman"))));
}

// ---------------------------------------------------------------- defaults

FIBClassKit UIBOperativeKitComponent::DefaultKitFor(EIBOperativeClass Class)
{
	FIBClassKit Kit;
	FIBKitAbilitySpec& A = Kit.KitAbility;
	FIBKitAbilitySpec& M = Kit.MovementTool;

	switch (Class)
	{
	case EIBOperativeClass::Breaker:
		A.DisplayName = NSLOCTEXT("IBKit", "RamCharge", "RAM CHARGE");
		A.Description = NSLOCTEXT("IBKit", "RamChargeDesc", "Shoulder-mounted concussive breach: a short lunge that hammers everything in front of you and opens armor seams.");
		A.Effect = EIBKitEffect::ConeStrike; A.Cooldown = 10.f; A.Duration = 0.2f; A.Strength = 1500.f; A.Range = 380.f; A.Radius = 220.f; A.Damage = 60.f;
		M.DisplayName = NSLOCTEXT("IBKit", "BulwarkDash", "BULWARK DASH");
		M.Description = NSLOCTEXT("IBKit", "BulwarkDashDesc", "Armored lunge — most incoming damage shrugs off for the length of the dash.");
		M.Effect = EIBKitEffect::Dash; M.Cooldown = 6.f; M.Duration = 0.6f; M.Strength = 1600.f; M.DamageTakenScale = 0.35f;
		break;

	case EIBOperativeClass::Picket:
		A.DisplayName = NSLOCTEXT("IBKit", "LamplightFlare", "LAMPLIGHT FLARE");
		A.Description = NSLOCTEXT("IBKit", "LamplightFlareDesc", "Thrown sensor spike: everything hostile around it is marked for the fireteam while it burns.");
		A.Effect = EIBKitEffect::DeployZone; A.Cooldown = 14.f; A.Duration = 8.f; A.Range = 2500.f; A.Radius = 900.f; A.bMarksTargets = true; A.bPlaceAtAim = true; A.SlowFactor = 1.f;
		M.DisplayName = NSLOCTEXT("IBKit", "LineBolt", "LINE BOLT");
		M.Description = NSLOCTEXT("IBKit", "LineBoltDesc", "Launchable cable runner — zip to whatever you're aiming at.");
		M.Effect = EIBKitEffect::Grapple; M.Cooldown = 5.f; M.Range = 3000.f; M.Strength = 2200.f;
		break;

	case EIBOperativeClass::Bellringer:
		A.DisplayName = NSLOCTEXT("IBKit", "DeterrentPylon", "DETERRENT PYLON");
		A.Description = NSLOCTEXT("IBKit", "DeterrentPylonDesc", "Area denial: it sings 'nothing here' — hostiles inside crawl.");
		A.Effect = EIBKitEffect::DeployZone; A.Cooldown = 16.f; A.Duration = 10.f; A.Radius = 700.f; A.SlowFactor = 0.45f;
		M.DisplayName = NSLOCTEXT("IBKit", "NullStep", "NULL STEP");
		M.Description = NSLOCTEXT("IBKit", "NullStepDesc", "Acoustic-dampened glide: hang in the air with full control for a few seconds.");
		M.Effect = EIBKitEffect::Glide; M.Cooldown = 5.f; M.Duration = 2.5f; M.Strength = 0.12f;
		break;

	case EIBOperativeClass::Corpsman:
		A.DisplayName = NSLOCTEXT("IBKit", "StimLine", "STIM LINE");
		A.Description = NSLOCTEXT("IBKit", "StimLineDesc", "Tethered field-dressing dart. (Post-launch corps — Blueprint placeholder.)");
		A.Effect = EIBKitEffect::Blueprint; A.Cooldown = 10.f;
		M.DisplayName = NSLOCTEXT("IBKit", "SurgeCarry", "SURGE CARRY");
		M.Description = NSLOCTEXT("IBKit", "SurgeCarryDesc", "A sprint that ignores carry penalties.");
		M.Effect = EIBKitEffect::Dash; M.Cooldown = 6.f; M.Duration = 0.3f; M.Strength = 1300.f;
		break;
	}
	return Kit;
}

// ---------------------------------------------------------------- lifecycle

void UIBOperativeKitComponent::BeginPlay()
{
	Super::BeginPlay();
	RefreshKit();
}

void UIBOperativeKitComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(GlideHandle);
		World->GetTimerManager().ClearTimer(StrikeHandle);
	}
	if (Hud)
	{
		Hud->RemoveFromParent();
		Hud = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}

void UIBOperativeKitComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// The PlayerState (and its operative) can land after BeginPlay on clients.
	if (!bResolvedFromIdentity)
	{
		RefreshKit();
	}
	EnsureHud();
}

void UIBOperativeKitComponent::RefreshKit()
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const AIBPlayerState* PS = Pawn ? Pawn->GetPlayerState<AIBPlayerState>() : nullptr;
	const bool bHasIdentity = PS && PS->HasOperative();
	const EIBOperativeClass Class = bHasIdentity ? PS->GetOperativeClass() : EIBOperativeClass::Breaker;

	if (bResolvedFromIdentity && Class == ResolvedClass)
	{
		return; // nothing changed
	}

	UIBClassKitData* Data = nullptr;
	if (const TSoftObjectPtr<UIBClassKitData>* Found = KitData.Find(Class))
	{
		Data = Found->LoadSynchronous();
	}
	ActiveKit = Data ? Data->Kit : DefaultKitFor(Class);
	ResolvedClass = Class;
	bResolvedFromIdentity = bHasIdentity;

	UE_LOG(LogIronBreach, Log, TEXT("Kit: %s -> %s / %s (%s)"),
		*IBCharacter::ClassName(Class).ToString(),
		*ActiveKit.KitAbility.DisplayName.ToString(), *ActiveKit.MovementTool.DisplayName.ToString(),
		Data ? TEXT("asset") : TEXT("built-in defaults"));

	if (Hud)
	{
		Hud->RefreshLabels();
	}
}

void UIBOperativeKitComponent::EnsureHud()
{
	if (Hud || !bShowHud) { return; }
	APlayerController* PC = OwnerPC();
	if (!PC || !PC->IsLocalController()) { return; }

	Hud = CreateWidget<UIBKitHudWidget>(PC, UIBKitHudWidget::StaticClass());
	if (Hud)
	{
		Hud->InitFor(this);
		Hud->AddToViewport(7);
	}
}

// ---------------------------------------------------------------- input

void UIBOperativeKitComponent::BindInput(UInputComponent* PlayerInputComponent, UInputAction* KitAbilityAction, UInputAction* MovementToolAction)
{
	if (!PlayerInputComponent) { return; }

	// Raw floor: the kit works with zero content (same rule as 1/2/3 and F).
	if (KitAbilityKey.IsValid())
	{
		PlayerInputComponent->BindKey(KitAbilityKey, IE_Pressed, this, &UIBOperativeKitComponent::ActivateKitAbility);
	}
	if (MovementToolKey.IsValid())
	{
		PlayerInputComponent->BindKey(MovementToolKey, IE_Pressed, this, &UIBOperativeKitComponent::ActivateMovementTool);
	}

	// Optional Enhanced Input route for Connor's IMC (gamepad etc.).
	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		if (KitAbilityAction)   { EIC->BindAction(KitAbilityAction,   ETriggerEvent::Started, this, &UIBOperativeKitComponent::ActivateKitAbility); }
		if (MovementToolAction) { EIC->BindAction(MovementToolAction, ETriggerEvent::Started, this, &UIBOperativeKitComponent::ActivateMovementTool); }
	}
}

void UIBOperativeKitComponent::ActivateKitAbility()   { TryActivate(false); }
void UIBOperativeKitComponent::ActivateMovementTool() { TryActivate(true); }

double UIBOperativeKitComponent::Now() const
{
	const UWorld* World = GetWorld();
	return World ? World->GetTimeSeconds() : 0.0;
}

float UIBOperativeKitComponent::GetCooldownRemaining(bool bMovementTool) const
{
	const double Ready = bMovementTool ? MoveReadyTime : KitReadyTime;
	return FMath::Max(0.f, static_cast<float>(Ready - Now()));
}

float UIBOperativeKitComponent::GetCooldownFraction(bool bMovementTool) const
{
	const float Cooldown = SpecFor(bMovementTool).Cooldown;
	if (Cooldown <= KINDA_SMALL_NUMBER) { return 0.f; }
	return FMath::Clamp(GetCooldownRemaining(bMovementTool) / Cooldown, 0.f, 1.f);
}

float UIBOperativeKitComponent::GetDamageTakenScale() const
{
	return (Now() < DefenseUntil) ? DefenseScale : 1.f;
}

void UIBOperativeKitComponent::TryActivate(bool bMovementTool)
{
	if (!bResolvedFromIdentity) { RefreshKit(); }

	ACharacter* Character = OwnerCharacter();
	const FIBKitAbilitySpec& Spec = SpecFor(bMovementTool);
	if (!Character || !Spec.IsUsable()) { return; }

	double& Ready = bMovementTool ? MoveReadyTime : KitReadyTime;
	if (Now() < Ready) { return; }
	Ready = Now() + Spec.Cooldown; // predicted; the server keeps its own clock

	if (Character->HasAuthority())
	{
		ExecuteEffect(bMovementTool, /*bAuthority=*/true, /*bLocal=*/Character->IsLocallyControlled());
	}
	else
	{
		ExecuteEffect(bMovementTool, /*bAuthority=*/false, /*bLocal=*/true);
		Server_Activate(bMovementTool);
	}
}

void UIBOperativeKitComponent::Server_Activate_Implementation(bool bMovementTool)
{
	if (!bResolvedFromIdentity) { RefreshKit(); }

	const FIBKitAbilitySpec& Spec = SpecFor(bMovementTool);
	if (!Spec.IsUsable()) { return; }

	double& Ready = bMovementTool ? MoveReadyTime : KitReadyTime;
	if (Now() < Ready - 0.15) { return; } // a little slack for latency
	Ready = Now() + Spec.Cooldown;

	ExecuteEffect(bMovementTool, /*bAuthority=*/true, /*bLocal=*/false);
}

void UIBOperativeKitComponent::Multicast_Activated_Implementation(bool bMovementTool)
{
	BP_OnKitActivated(bMovementTool, SpecFor(bMovementTool));
}

// ---------------------------------------------------------------- effects

void UIBOperativeKitComponent::ExecuteEffect(bool bMovementTool, bool bAuthority, bool bLocal)
{
	const FIBKitAbilitySpec& Spec = SpecFor(bMovementTool);

	switch (Spec.Effect)
	{
	case EIBKitEffect::Dash:
		DoDash(Spec);                         // both the owning client and the server move the body
		OpenDefenseWindow(Spec);
		break;

	case EIBKitEffect::Grapple:
		DoGrapple(Spec);
		break;

	case EIBKitEffect::Glide:
		DoGlide(Spec);
		break;

	case EIBKitEffect::ConeStrike:
		DoDash(Spec);
		OpenDefenseWindow(Spec);
		if (bAuthority)
		{
			// Let the lunge land first, then hit what's in front.
			if (UWorld* World = GetWorld())
			{
				const FIBKitAbilitySpec SpecCopy = Spec;
				World->GetTimerManager().SetTimer(StrikeHandle, FTimerDelegate::CreateWeakLambda(this, [this, SpecCopy]()
				{
					DoConeStrikeDamage(SpecCopy);
				}), FMath::Max(0.05f, Spec.Duration), false);
			}
		}
		break;

	case EIBKitEffect::DeployZone:
		if (bAuthority) { DoDeployZone(Spec); }
		break;

	case EIBKitEffect::Blueprint:
	case EIBKitEffect::None:
	default:
		break;
	}

	if (bAuthority)
	{
		Multicast_Activated(bMovementTool); // FX on every machine
	}
	UE_LOG(LogIronBreach, Verbose, TEXT("Kit: %s activated (%s%s)"), *Spec.DisplayName.ToString(),
		bAuthority ? TEXT("authority") : TEXT("client"), bLocal ? TEXT(", local") : TEXT(""));
}

FVector UIBOperativeKitComponent::LookDirection(bool bFlatten) const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn) { return FVector::ForwardVector; }
	FVector Dir = Pawn->GetControlRotation().Vector();
	if (bFlatten)
	{
		Dir.Z = 0.f;
	}
	return Dir.GetSafeNormal().IsNearlyZero() ? Pawn->GetActorForwardVector() : Dir.GetSafeNormal();
}

void UIBOperativeKitComponent::DoDash(const FIBKitAbilitySpec& Spec)
{
	if (ACharacter* Character = OwnerCharacter())
	{
		const FVector Dir = LookDirection(/*bFlatten=*/true);
		Character->LaunchCharacter(Dir * Spec.Strength + FVector(0.f, 0.f, Spec.Strength * 0.12f), true, true);
	}
}

void UIBOperativeKitComponent::OpenDefenseWindow(const FIBKitAbilitySpec& Spec)
{
	if (Spec.DamageTakenScale < 1.f && Spec.Duration > 0.f)
	{
		DefenseScale = Spec.DamageTakenScale;
		DefenseUntil = Now() + Spec.Duration;
	}
}

void UIBOperativeKitComponent::DoGrapple(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UWorld* World = GetWorld();
	if (!Character || !World) { return; }

	const FVector Start = Character->GetPawnViewLocation();
	const FVector Dir = LookDirection(/*bFlatten=*/false);
	const FVector End = Start + Dir * Spec.Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(IBLineBolt), /*bTraceComplex=*/false, Character);
	FHitResult Hit;
	if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
	{
		return; // nothing to anchor to — no cooldown refund on purpose (it's a commit)
	}

	const FVector From = Character->GetActorLocation();
	const FVector To = Hit.ImpactPoint;
	const float Dist = FVector::Dist(From, To);
	const FVector Flat = (To - From).GetSafeNormal();

	// Fast horizontal pull plus enough lift to clear the ledge you're aiming at.
	FVector Velocity = Flat * Spec.Strength;
	Velocity.Z = FMath::Clamp(300.f + Dist * 0.25f + FMath::Max(0.f, To.Z - From.Z) * 1.2f, 300.f, 1400.f);
	Character->LaunchCharacter(Velocity, true, true);
}

void UIBOperativeKitComponent::DoGlide(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UCharacterMovementComponent* Move = Character ? Character->GetCharacterMovement() : nullptr;
	UWorld* World = GetWorld();
	if (!Move || !World) { return; }

	if (!bGliding)
	{
		SavedGravityScale = Move->GravityScale;
		SavedAirControl = Move->AirControl;
		bGliding = true;
	}
	Move->GravityScale = FMath::Clamp(Spec.Strength, 0.f, 1.f);
	Move->AirControl = 1.f;

	// Kill the fall so the glide reads immediately, even mid-drop.
	FVector Vel = Move->Velocity;
	Vel.Z = FMath::Max(Vel.Z, 0.f);
	Move->Velocity = Vel;

	World->GetTimerManager().SetTimer(GlideHandle, this, &UIBOperativeKitComponent::EndGlide, FMath::Max(0.2f, Spec.Duration), false);
}

void UIBOperativeKitComponent::EndGlide()
{
	if (!bGliding) { return; }
	bGliding = false;
	if (ACharacter* Character = OwnerCharacter())
	{
		if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
		{
			Move->GravityScale = SavedGravityScale;
			Move->AirControl = SavedAirControl;
		}
	}
}

void UIBOperativeKitComponent::DoConeStrikeDamage(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	if (!Character || !Character->HasAuthority()) { return; }

	const FVector Origin = Character->GetActorLocation();
	const FVector Dir = LookDirection(/*bFlatten=*/true);
	const FVector Center = Origin + Dir * (Spec.Range * 0.5f);

	TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
	ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_Pawn));
	TArray<AActor*> Ignore;
	Ignore.Add(Character);
	TArray<AActor*> Overlaps;
	UKismetSystemLibrary::SphereOverlapActors(this, Center, FMath::Max(Spec.Range * 0.5f, Spec.Radius), ObjectTypes, AActor::StaticClass(), Ignore, Overlaps);

	AController* Instigator = Character->GetController();
	int32 Hits = 0;
	for (AActor* Target : Overlaps)
	{
		if (!Target || Target->IsA<AIBCharacter_Infantry>()) { continue; } // never the fireteam
		if (!Target->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass())) { continue; }

		// In front of us, within the cone's half-width at its far end.
		const FVector ToTarget = Target->GetActorLocation() - Origin;
		const float Along = FVector::DotProduct(ToTarget, Dir);
		if (Along < 0.f || Along > Spec.Range + Spec.Radius) { continue; }
		const float Across = (ToTarget - Dir * Along).Size();
		if (Across > Spec.Radius) { continue; }

		FHitResult Hit;
		Hit.ImpactPoint = Target->GetActorLocation();
		Hit.Location = Hit.ImpactPoint;
		Hit.ImpactNormal = -Dir;
		Hit.Normal = -Dir;
		Hit.HitObjectHandle = FActorInstanceHandle(Target);
		IDamageableInterface::Execute_HandleTakeDamage(Target, Spec.Damage, Hit, Instigator, Character);

		if (ACharacter* TargetCharacter = Cast<ACharacter>(Target))
		{
			TargetCharacter->LaunchCharacter(Dir * Spec.Strength * 0.6f + FVector(0.f, 0.f, 260.f), true, true);
		}
		++Hits;
	}
	UE_LOG(LogIronBreach, Log, TEXT("Kit: %s hit %d target(s)"), *Spec.DisplayName.ToString(), Hits);
}

void UIBOperativeKitComponent::DoDeployZone(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UWorld* World = GetWorld();
	if (!Character || !World || !Character->HasAuthority()) { return; }

	FVector Location = Character->GetActorLocation() - FVector(0.f, 0.f, Character->GetDefaultHalfHeight());
	if (Spec.bPlaceAtAim)
	{
		const FVector Start = Character->GetPawnViewLocation();
		const FVector End = Start + LookDirection(false) * Spec.Range;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IBDeployZone), false, Character);
		FHitResult Hit;
		FVector Anchor = End; // nothing in reach: it lands at max range
		if (World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
		{
			// Back off the surface so a wall hit lands at the wall's foot, not inside it.
			Anchor = Hit.ImpactPoint + Hit.ImpactNormal * 40.f;
			if (AActor* HitActor = Hit.GetActor(); HitActor && HitActor->IsA<APawn>())
			{
				Params.AddIgnoredActor(HitActor); // hit a Kaiju: drop to the ground under it, not onto its shin
			}
		}

		// It's thrown, not pinned: fall to whatever floor is under the anchor.
		FHitResult Ground;
		if (World->LineTraceSingleByChannel(Ground, Anchor + FVector(0.f, 0.f, 120.f), Anchor - FVector(0.f, 0.f, 6000.f), ECC_Visibility, Params))
		{
			Location = Ground.ImpactPoint;
		}
		else
		{
			Location = Anchor;
		}
	}

	UClass* ZoneClass = Spec.ZoneClass ? *Spec.ZoneClass : AIBKitZone::StaticClass();
	FActorSpawnParameters Params;
	Params.Owner = Character;
	Params.Instigator = Character;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (AIBKitZone* Zone = World->SpawnActor<AIBKitZone>(ZoneClass, Location, FRotator::ZeroRotator, Params))
	{
		Zone->InitZone(Spec, IBCharacter::ClassColor(ResolvedClass), Character);
	}
}

// ---------------------------------------------------------------- helpers

ACharacter* UIBOperativeKitComponent::OwnerCharacter() const
{
	return Cast<ACharacter>(GetOwner());
}

APlayerController* UIBOperativeKitComponent::OwnerPC() const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	return Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
}
