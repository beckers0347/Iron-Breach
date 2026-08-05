#include "Kaiju/IBKaijuOrganComponent.h"
#include "Kaiju/IBCharacter_Kaiju.h"
#include "Net/UnrealNetwork.h" // Explicit include: DOREPLIFETIME macros

UIBKaijuOrganComponent::UIBKaijuOrganComponent()
{
	SetIsReplicatedByDefault(true);

	// Query-only: weapon traces can hit it, nothing bounces off it physically.
	// ECC_Pawn matches UHitscanWeaponComponent's trace channel (see its line 147
	// comment) — block that, ignore the rest so we never eat camera/vis traces.
	SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SetCollisionObjectType(ECC_WorldDynamic);
	SetCollisionResponseToAllChannels(ECR_Ignore);
	SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);

	SphereRadius = 80.0f; // Chunky default target; scale per-organ in the BP
}

void UIBKaijuOrganComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UIBKaijuOrganComponent, bDestroyed);
	DOREPLIFETIME(UIBKaijuOrganComponent, CurrentOrganHealth);
	DOREPLIFETIME(UIBKaijuOrganComponent, MaxOrganHealth);
}

void UIBKaijuOrganComponent::InitOrgan(float SpeciesOrganHealth)
{
	MaxOrganHealth = (OrganHealthOverride > 0.0f) ? OrganHealthOverride : SpeciesOrganHealth;
	CurrentOrganHealth = MaxOrganHealth;
}

bool UIBKaijuOrganComponent::ApplyOrganDamage(float Amount)
{
	if (bDestroyed || Amount <= 0.0f) return false;

	CurrentOrganHealth = FMath::Max(CurrentOrganHealth - Amount, 0.0f);
	if (CurrentOrganHealth > 0.0f) return false;

	bDestroyed = true;

	// Server-side listeners (and the listen-server host's FX) hear it now;
	// remote clients hear the identical broadcast from OnRep_Destroyed.
	OnOrganStateChanged.Broadcast(true);

	// Traces should now pass through the wound to the body behind it.
	SetCollisionEnabled(ECollisionEnabled::NoCollision);
	return true;
}

void UIBKaijuOrganComponent::OnRep_Destroyed()
{
	if (!bDestroyed) return;

	OnOrganStateChanged.Broadcast(true);
	SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// Client-side mirror of the kaiju-level hook (stagger FX, HUD pips).
	if (AIBCharacter_Kaiju* Kaiju = Cast<AIBCharacter_Kaiju>(GetOwner()))
	{
		Kaiju->NotifyOrganDestroyedLocal(this);
	}
}
