#include "World/IBMapPOIComponent.h"
#include "World/IBMapSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

void UIBMapPOIComponent::BeginPlay()
{
	Super::BeginPlay();
	bDiscovered = bStartDiscovered;

	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->RegisterPOI(this);
	}
}

void UIBMapPOIComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->UnregisterPOI(this);
	}
	Super::EndPlay(EndPlayReason);
}

void UIBMapPOIComponent::SetDiscovered(bool bNewDiscovered)
{
	if (bDiscovered == bNewDiscovered) { return; }
	bDiscovered = bNewDiscovered;

	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->NotifyMapDataChanged();
	}
}

FVector UIBMapPOIComponent::GetPOIWorldLocation() const
{
	const AActor* Owner = GetOwner();
	return Owner ? Owner->GetActorLocation() : FVector::ZeroVector;
}
