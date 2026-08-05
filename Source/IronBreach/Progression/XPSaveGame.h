#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Progression/XPTypes.h"
#include "XPSaveGame.generated.h"

/**
 * Local save file for both XP ledgers (ADR-002: this is a listen-server, self-hosted game --
 * the host machine's disk IS the shared server truth, same posture as the rest of the
 * project's netcode). Owned and written exclusively by IBXPSubsystem.
 */
UCLASS()
class IRONBREACH_API UXPSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	/** Keyed by one pilot's stable player key (see IBXPSubsystem::MakePlayerKey). */
	UPROPERTY()
	TMap<FString, FXPRecord> PilotRecords;

	/** Keyed by a sorted, joined pair of player keys (see IBXPSubsystem::MakeCrewKey) --
	 *  order-independent, so the same two humans always resolve to the same record
	 *  regardless of which seat each is in. A human paired with the AI co-pilot resolves to
	 *  a single-key "solo crew" record, distinct from that same player's record once a
	 *  second human joins them. */
	UPROPERTY()
	TMap<FString, FXPRecord> CrewRecords;

	static const TCHAR* SlotName;
	static const int32 UserIndex;
};
