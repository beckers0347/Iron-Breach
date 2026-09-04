#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Player/IBCharacterTypes.h"
#include "IBCharacterSaveGame.generated.h"

/**
 * Local save file for the operative roster (max 3 characters). Same posture
 * as XPSaveGame / ADR-002: this machine's disk is the truth for its own
 * account. Owned and written exclusively by UIBCharacterSubsystem.
 */
UCLASS()
class IRONBREACH_API UIBCharacterSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY()
	int32 SaveVersion = 1;

	/** Creation order; index is NOT identity — CharacterId is. */
	UPROPERTY()
	TArray<FIBCharacterRecord> Characters;

	/** Who deployed last — select screen highlights them next boot. */
	UPROPERTY()
	FGuid LastActiveId;

	static const TCHAR* SlotName;
	static const int32 UserIndex;
};
