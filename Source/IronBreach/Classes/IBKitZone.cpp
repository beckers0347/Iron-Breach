#include "Classes/IBKitZone.h"
#include "IronBreach.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AIBKitZone::AIBKitZone()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	SetReplicatingMovement(false);

	ZoneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ZoneRoot"));
	RootComponent = ZoneRoot;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	// Unlit glow (Scripts/ib_create_kit_materials.py), resolved lazily in ApplyLook so a
	// checkout without the asset boots clean; missing -> the engine's lit grey shapes, tinted.
	ZoneMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/M_IBKitZone.M_IBKitZone")));

	Disc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Disc"));
	Disc->SetupAttachment(ZoneRoot);
	Disc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Disc->SetCastShadow(false);
	if (CylinderMesh.Succeeded()) { Disc->SetStaticMesh(CylinderMesh.Object); }

	Post = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Post"));
	Post->SetupAttachment(ZoneRoot);
	Post->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Post->SetCastShadow(false);
	Post->SetRelativeScale3D(FVector(0.14f, 0.14f, 1.7f));
	Post->SetRelativeLocation(FVector(0.f, 0.f, 85.f));
	if (CylinderMesh.Succeeded()) { Post->SetStaticMesh(CylinderMesh.Object); }

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(ZoneRoot);
	Light->SetRelativeLocation(FVector(0.f, 0.f, 180.f));
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetIntensity(400.f);
	Light->SetAttenuationRadius(1200.f);
	Light->SetCastShadows(false);
}

void AIBKitZone::InitZone(const FIBKitAbilitySpec& Spec, const FLinearColor& InAccent, AActor* InOwnerPawn)
{
	Radius = FMath::Max(50.f, Spec.Radius);
	Accent = InAccent;
	SlowFactor = FMath::Clamp(Spec.SlowFactor, 0.05f, 1.f);
	bMarksTargets = Spec.bMarksTargets;
	Lifetime = FMath::Max(0.5f, Spec.Duration);
	OwnerPawn = InOwnerPawn;
	ApplyLook();

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(PulseHandle, this, &AIBKitZone::Pulse, 0.25f, true, 0.05f);
		World->GetTimerManager().SetTimer(ExpireHandle, FTimerDelegate::CreateWeakLambda(this, [this]()
		{
			ReleaseAll();
			Destroy();
		}), Lifetime, false);
	}
}

void AIBKitZone::BeginPlay()
{
	Super::BeginPlay();
	ApplyLook();

	// Clients pulse too — marks are cosmetic and must show on every machine.
	if (!HasAuthority())
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(PulseHandle, this, &AIBKitZone::Pulse, 0.25f, true, 0.1f);
		}
	}
}

void AIBKitZone::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	ReleaseAll();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(PulseHandle);
		World->GetTimerManager().ClearTimer(ExpireHandle);
	}
	Super::EndPlay(EndPlayReason);
}

void AIBKitZone::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBKitZone, Radius);
	DOREPLIFETIME(AIBKitZone, Accent);
	DOREPLIFETIME(AIBKitZone, SlowFactor);
	DOREPLIFETIME(AIBKitZone, bMarksTargets);
}

void AIBKitZone::OnRep_Look()
{
	ApplyLook();
}

UMaterialInterface* AIBKitZone::ResolveZoneMaterial()
{
	if (!bZoneMaterialResolved)
	{
		bZoneMaterialResolved = true;
		if (!ZoneMaterial.IsNull())
		{
			// Quiet: a missing asset is a content gap, not an error worth a log line per zone.
			ResolvedZoneMaterial = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
				*ZoneMaterial.ToSoftObjectPath().ToString(), nullptr, LOAD_NoWarn | LOAD_Quiet));
		}
	}
	return ResolvedZoneMaterial;
}

void AIBKitZone::ApplyLook()
{
	UMaterialInterface* Glow = ResolveZoneMaterial();
	if (Disc)
	{
		if (Glow) { Disc->SetMaterial(0, Glow); }
		// The engine cylinder is 100 cm across: scale to the radius, squash flat.
		const float Scale = Radius / 50.f;
		Disc->SetRelativeScale3D(FVector(Scale, Scale, 0.04f));
		Disc->SetRelativeLocation(FVector(0.f, 0.f, 2.f));

		// M_IBKitZone: Color * Glow -> emissive, Opacity. BasicShapeMaterial only knows Color and stays lit grey.
		if (UMaterialInstanceDynamic* Mid = Disc->CreateAndSetMaterialInstanceDynamic(0))
		{
			Mid->SetVectorParameterValue(TEXT("Color"), Glow ? Accent : Accent * 0.6f);
			Mid->SetScalarParameterValue(TEXT("Glow"), 1.5f);
			Mid->SetScalarParameterValue(TEXT("Opacity"), 0.35f);
		}
	}
	if (Post)
	{
		if (Glow) { Post->SetMaterial(0, Glow); }
		if (UMaterialInstanceDynamic* Mid = Post->CreateAndSetMaterialInstanceDynamic(0))
		{
			Mid->SetVectorParameterValue(TEXT("Color"), Accent);
			Mid->SetScalarParameterValue(TEXT("Glow"), 4.f);
			Mid->SetScalarParameterValue(TEXT("Opacity"), 0.95f);
		}
	}
	if (Light)
	{
		FLinearColor LightColor = Accent;
		LightColor.A = 1.f;
		Light->SetLightColor(LightColor);
		Light->SetAttenuationRadius(FMath::Max(600.f, Radius * 1.6f));
	}
}

bool AIBKitZone::IsHostile(const ACharacter* Character) const
{
	if (!Character || Character == OwnerPawn.Get()) { return false; }
	// Infantry are the fireteam — never slowed, never marked. Everything else that walks is a target.
	return !Character->IsA<AIBCharacter_Infantry>();
}

void AIBKitZone::Pulse()
{
	UWorld* World = GetWorld();
	if (!World) { return; }

	TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
	ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_Pawn));
	TArray<AActor*> Ignore;
	if (OwnerPawn.IsValid()) { Ignore.Add(OwnerPawn.Get()); }
	TArray<AActor*> Overlaps;
	UKismetSystemLibrary::SphereOverlapActors(this, GetActorLocation(), Radius, ObjectTypes, ACharacter::StaticClass(), Ignore, Overlaps);

	TSet<ACharacter*> Inside;
	for (AActor* Actor : Overlaps)
	{
		ACharacter* Character = Cast<ACharacter>(Actor);
		if (!IsHostile(Character)) { continue; }
		Inside.Add(Character);

		if (HasAuthority() && SlowFactor < 1.f && !SlowedOriginalSpeeds.Contains(Character))
		{
			if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
			{
				SlowedOriginalSpeeds.Add(Character, Move->MaxWalkSpeed);
				Move->MaxWalkSpeed *= SlowFactor;
			}
		}

		if (bMarksTargets)
		{
			if (USkeletalMeshComponent* Mesh = Character->GetMesh())
			{
				if (!Mesh->bRenderCustomDepth)
				{
					Mesh->SetRenderCustomDepth(true);
					Mesh->SetCustomDepthStencilValue(1);
					MarkedComponents.Add(Mesh);
				}
			}
		}
	}

	// Anyone who walked out gets their speed back (marks fade with the zone).
	for (auto It = SlowedOriginalSpeeds.CreateIterator(); It; ++It)
	{
		ACharacter* Character = It.Key().Get();
		if (!Character || !Inside.Contains(Character))
		{
			if (Character)
			{
				if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
				{
					Move->MaxWalkSpeed = It.Value();
				}
			}
			It.RemoveCurrent();
		}
	}
}

void AIBKitZone::ReleaseAll()
{
	for (auto& Pair : SlowedOriginalSpeeds)
	{
		if (ACharacter* Character = Pair.Key.Get())
		{
			if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
			{
				Move->MaxWalkSpeed = Pair.Value;
			}
		}
	}
	SlowedOriginalSpeeds.Empty();

	for (const TWeakObjectPtr<UPrimitiveComponent>& Weak : MarkedComponents)
	{
		if (UPrimitiveComponent* Prim = Weak.Get())
		{
			Prim->SetRenderCustomDepth(false);
		}
	}
	MarkedComponents.Empty();
}
