#include "World/IBMapZoneInfo.h"
#include "World/IBMapSubsystem.h"
#include "Engine/World.h"

void AIBMapZoneInfo::BeginPlay()
{
	Super::BeginPlay();

	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->RegisterZoneInfo(this);
	}
}
