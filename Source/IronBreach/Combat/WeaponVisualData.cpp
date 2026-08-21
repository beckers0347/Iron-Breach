#include "WeaponVisualData.h"

#if WITH_EDITOR
void UWeaponVisualData::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	// Live-tune seam: lets AIBCharacter_Infantry re-apply this weapon's scale/
	// alignment/mesh to a running PIE session the instant you edit the asset,
	// instead of needing to exit and re-enter PIE to see the change.
	OnVisualDataChanged.Broadcast();
}
#endif
