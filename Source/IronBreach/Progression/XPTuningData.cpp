#include "Progression/XPTuningData.h"

int32 UXPTuningData::LevelForXP(int32 TotalXP, const TArray<int32>& Thresholds)
{
	int32 Level = 1;
	for (int32 Index = 0; Index < Thresholds.Num(); ++Index)
	{
		if (TotalXP >= Thresholds[Index])
		{
			Level = Index + 1;
		}
		else
		{
			break;
		}
	}
	return Level;
}
