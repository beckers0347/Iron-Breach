#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "IBLootTableAsset.generated.h"

class UIBItemDefinition;

/** One line in a loot table. */
USTRUCT(BlueprintType)
struct FIBLootTableEntry
{
	GENERATED_BODY()

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot")
	TObjectPtr<UIBItemDefinition> Definition = nullptr;

	/** Relative weight against the other rollable entries. Higher = more
	 *  common. Ignored for guaranteed entries. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "0.0", EditCondition = "!bGuaranteed"))
	float Weight = 1.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "1"))
	int32 MinCount = 1;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "1"))
	int32 MaxCount = 1;

	/** Always drops (in addition to the weighted rolls). The genre staple:
	 *  chitin ALWAYS comes off the kaiju; the Doctrine is the roll. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot")
	bool bGuaranteed = false;
};

/** One resolved drop, ready to grant or spawn. */
USTRUCT(BlueprintType)
struct FIBLootRoll
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Loot")
	TObjectPtr<UIBItemDefinition> Definition = nullptr;

	UPROPERTY(BlueprintReadOnly, Category = "Loot")
	int32 Count = 1;
};

/**
 * DA_Loot_* — a reusable drop list. One per enemy family, not per enemy:
 * every Class-D shares a table; the Palawan gets its own. Rolling is
 * server-side only (the loot component calls it on authority).
 *
 * Deliberately simple for M2: weighted pick + guaranteed lines. Rarity-tier
 * weighting and stat variance are the drop *generator* (roadmap §3.3) and
 * will layer on top of this asset, not replace it.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UIBLootTableAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot")
	TArray<FIBLootTableEntry> Entries;

	/** Chance that the weighted rolls happen at all (guaranteed entries
	 *  ignore this — they always drop). 1 = every kill pays out. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float DropChance = 1.0f;

	/** How many weighted picks per payout. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "0"))
	int32 MinRolls = 1;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Loot", meta = (ClampMin = "0"))
	int32 MaxRolls = 1;

	/** Server-side roll. Same entry can win twice — that's fine, grants stack. */
	TArray<FIBLootRoll> Roll() const
	{
		TArray<FIBLootRoll> Out;

		float TotalWeight = 0.0f;
		for (const FIBLootTableEntry& Entry : Entries)
		{
			if (Entry.bGuaranteed && Entry.Definition)
			{
				Out.Add({ Entry.Definition, FMath::RandRange(Entry.MinCount, FMath::Max(Entry.MinCount, Entry.MaxCount)) });
			}
			else if (Entry.Definition && Entry.Weight > 0.0f)
			{
				TotalWeight += Entry.Weight;
			}
		}

		if (TotalWeight <= 0.0f || FMath::FRand() > DropChance)
		{
			return Out; // guaranteed lines only
		}

		const int32 NumRolls = FMath::RandRange(MinRolls, FMath::Max(MinRolls, MaxRolls));
		for (int32 RollIndex = 0; RollIndex < NumRolls; ++RollIndex)
		{
			float Pick = FMath::FRandRange(0.0f, TotalWeight);
			for (const FIBLootTableEntry& Entry : Entries)
			{
				if (Entry.bGuaranteed || !Entry.Definition || Entry.Weight <= 0.0f) { continue; }
				Pick -= Entry.Weight;
				if (Pick <= 0.0f)
				{
					Out.Add({ Entry.Definition, FMath::RandRange(Entry.MinCount, FMath::Max(Entry.MinCount, Entry.MaxCount)) });
					break;
				}
			}
		}
		return Out;
	}
};
