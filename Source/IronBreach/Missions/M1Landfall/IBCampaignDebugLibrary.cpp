// IBCampaignDebugLibrary.cpp

#include "IBCampaignDebugLibrary.h"
#include "HAL/IConsoleManager.h"
#include "IBCampaignEditorSettings.h"

static TAutoConsoleVariable<bool> CVarIBDisableCampaign(
	TEXT("IronBreach.DisableCampaign"),
	false,
	TEXT("If true, M1's scripted act directors (Barracks/Escalation/Contact/DeepWater/Retreat) ")
	TEXT("and the generic AIBMissionDirector auto-spawn stay dormant on their next BeginPlay -- ")
	TEXT("lets you PIE-test other systems in a mission level without the campaign auto-playing. ")
	TEXT("Toggle live: `IronBreach.DisableCampaign 1` / `0` in the in-game console (~)."),
	ECVF_Cheat);

bool UIBCampaignDebugLibrary::IsCampaignDisabled()
{
	if (CVarIBDisableCampaign.GetValueOnGameThread())
	{
		return true;
	}
#if WITH_EDITOR
	// Editor Preferences > Iron Breach > Campaign > "Run Campaign In PIE". GIsEditor is only true in the
	// editor process, so this covers PIE/Simulate and never a packaged or standalone game.
	if (GIsEditor && !GetDefault<UIBCampaignEditorSettings>()->bRunCampaignInPIE)
	{
		return true;
	}
#endif
	return false;
}

void UIBCampaignDebugLibrary::SetCampaignDisabled(bool bDisabled)
{
	CVarIBDisableCampaign->Set(bDisabled ? 1 : 0, ECVF_SetByCode);
}
