#include "IBCharacter_Mech.h"
#include "../Combat/HealthComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AIBCharacter_Mech::AIBCharacter_Mech()
{
	PrimaryActorTick.bCanEverTick = true;

	// Attach Modular Health
	HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("HealthComponent"));
	HealthComponent->SetMaxHealth(5000.0f); // Mechs are inherently tankier

	// Make the movement heavy and deliberate
	if (GetCharacterMovement())
	{
		GetCharacterMovement()->MaxWalkSpeed = 300.0f;
		GetCharacterMovement()->Mass = 10000.0f;
		GetCharacterMovement()->bUseControllerDesiredRotation = true;
	}

	CurrentSyncLevel = 0.0f;
}

void AIBCharacter_Mech::BeginPlay()
{
	Super::BeginPlay();
}

void AIBCharacter_Mech::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Input will be dynamically routed based on Pilot Role (Navigator vs Gunner)
}

// Interface Implementation handling incoming damage
void AIBCharacter_Mech::HandleTakeDamage_Implementation(float DamageAmount, const FHitResult& HitResult, AController* InstigatedBy, AActor* DamageCauser)
{
	if (HealthComponent)
	{
		// Apply armor reduction math here before passing to HealthComponent if needed
		HealthComponent->ApplyDamage(DamageAmount, HitResult, InstigatedBy, DamageCauser);
	}
}