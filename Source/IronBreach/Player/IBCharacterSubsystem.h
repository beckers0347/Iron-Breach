#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Player/IBCharacterTypes.h"
#include "IBCharacterSubsystem.generated.h"

class UIBCharacterSaveGame;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBRosterChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBActiveCharacterChanged, const FIBCharacterRecord&, Character);

/**
 * The operative roster: up to MaxCharacters saved characters, and which one
 * is on station for THIS run of the game.
 *
 * Persistence law: the roster (and who played last) saves to disk; the
 * ACTIVE choice is per-run only — every fresh boot walks through the select
 * screen again (Destiny law: you always choose your character at the door).
 * GameInstance lifetime means the choice survives every map travel,
 * including quit-to-menu, without re-asking.
 */
UCLASS()
class IRONBREACH_API UIBCharacterSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static constexpr int32 MaxCharacters = 3;

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	// ---- Roster ----

	UFUNCTION(BlueprintPure, Category = "Character")
	const TArray<FIBCharacterRecord>& GetRoster() const { return Roster; }

	UFUNCTION(BlueprintPure, Category = "Character")
	int32 GetMaxCharacters() const { return MaxCharacters; }

	UFUNCTION(BlueprintPure, Category = "Character")
	bool CanCreateCharacter() const { return Roster.Num() < MaxCharacters; }

	/** Who deployed last (highlight on the select screen). Invalid guid if never. */
	UFUNCTION(BlueprintPure, Category = "Character")
	FGuid GetLastActiveId() const { return LastActiveId; }

	/**
	 * Create + select in one act (creation IS your choice for this run).
	 * Callsign is sanitized here — trimmed, uppercased, [A-Z 0-9 - _ .],
	 * max 16; blank generates one. Fails only when the roster is full or the
	 * callsign is already in service (OutError narrates).
	 */
	bool CreateCharacter(const FString& Callsign, EIBOperativeClass Class, EIBOperativeGender Gender,
		FIBCharacterRecord& OutCharacter, FText& OutError);

	/** Remove an operative for good. Clears the active choice if it was them. */
	UFUNCTION(BlueprintCallable, Category = "Character")
	bool DeleteCharacter(const FGuid& CharacterId);

	/** Mirror the XP ledger's level onto the roster card (display only). */
	UFUNCTION(BlueprintCallable, Category = "Character")
	void SetCharacterLevel(const FGuid& CharacterId, int32 Level);

	// ---- Active choice (per-run) ----

	UFUNCTION(BlueprintCallable, Category = "Character")
	bool SelectCharacter(const FGuid& CharacterId);

	UFUNCTION(BlueprintPure, Category = "Character")
	bool HasActiveCharacter() const;

	UFUNCTION(BlueprintPure, Category = "Character")
	bool GetActiveCharacter(FIBCharacterRecord& OutCharacter) const;

	// ---- Events ----

	/** Roster contents changed (create/delete). */
	UPROPERTY(BlueprintAssignable, Category = "Character")
	FOnIBRosterChanged OnRosterChanged;

	/** A character was put on station for this run. */
	UPROPERTY(BlueprintAssignable, Category = "Character")
	FOnIBActiveCharacterChanged OnActiveCharacterChanged;

	/** Public so the create screen can preview what the service record will show. */
	static FString SanitizeCallsign(const FString& Raw);
	static FString GenerateCallsign();

private:
	const FIBCharacterRecord* FindRecord(const FGuid& Id) const;
	void LoadRoster();
	void SaveRoster();

	UPROPERTY(Transient)
	TArray<FIBCharacterRecord> Roster;

	/** Persisted: who played last. */
	FGuid LastActiveId;

	/** Per-run only: who is on station right now. Never loaded from disk. */
	FGuid ActiveCharacterId;
};
