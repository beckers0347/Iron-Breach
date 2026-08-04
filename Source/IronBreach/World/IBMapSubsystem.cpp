#include "World/IBMapSubsystem.h"
#include "IronBreach.h"
#include "World/IBMapPOIComponent.h"
#include "World/IBMapZoneInfo.h"

void UIBMapSubsystem::RegisterPOI(UIBMapPOIComponent* POI)
{
	if (!POI) { return; }
	RegisteredPOIs.AddUnique(POI);
	NotifyMapDataChanged();
}

void UIBMapSubsystem::UnregisterPOI(UIBMapPOIComponent* POI)
{
	if (!POI) { return; }
	RegisteredPOIs.Remove(POI);
	NotifyMapDataChanged();
}

void UIBMapSubsystem::RegisterZoneInfo(AIBMapZoneInfo* ZoneInfo)
{
	if (ActiveZoneInfo.IsValid() && ActiveZoneInfo.Get() != ZoneInfo)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[Map] Multiple IBMapZoneInfo actors in this world — using the newest (%s). One per zone, please."),
			*GetNameSafe(ZoneInfo));
	}
	ActiveZoneInfo = ZoneInfo;
	NotifyMapDataChanged();
}

void UIBMapSubsystem::NotifyMapDataChanged()
{
	OnMapDataChanged.Broadcast();
}

TArray<UIBMapPOIComponent*> UIBMapSubsystem::GetVisiblePOIs() const
{
	TArray<UIBMapPOIComponent*> Out;
	Out.Reserve(RegisteredPOIs.Num());
	for (const TWeakObjectPtr<UIBMapPOIComponent>& Weak : RegisteredPOIs)
	{
		UIBMapPOIComponent* POI = Weak.Get();
		if (POI && POI->IsDiscovered())
		{
			Out.Add(POI);
		}
	}
	return Out;
}

UIBMapZoneData* UIBMapSubsystem::GetZoneData() const
{
	const AIBMapZoneInfo* ZoneInfo = ActiveZoneInfo.Get();
	return ZoneInfo ? ZoneInfo->ZoneData : nullptr;
}

UIBMapPOIComponent* UIBMapSubsystem::FindPOIById(FName POIId) const
{
	if (POIId.IsNone()) { return nullptr; }
	for (const TWeakObjectPtr<UIBMapPOIComponent>& Weak : RegisteredPOIs)
	{
		UIBMapPOIComponent* POI = Weak.Get();
		if (POI && POI->POIId == POIId)
		{
			return POI;
		}
	}
	return nullptr;
}

void UIBMapSubsystem::RequestPOIActivation(UIBMapPOIComponent* POI)
{
	if (!POI) { return; }
	UE_LOG(LogIronBreach, Log, TEXT("[Map] POI activated: %s"), *POI->DisplayName.ToString());
	OnPOIActivated.Broadcast(POI);
}
