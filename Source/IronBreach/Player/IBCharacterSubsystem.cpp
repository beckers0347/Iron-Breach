#include "Player/IBCharacterSubsystem.h"
#include "Player/IBCharacterSaveGame.h"
#include "IronBreach.h"
#include "Kismet/GameplayStatics.h"

void UIBCharacterSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	LoadRoster();
}

void UIBCharacterSubsystem::LoadRoster()
{
	Roster.Reset();
	LastActiveId.Invalidate();
	ActiveCharacterId.Invalidate(); // per-run choice NEVER comes from disk

	if (UGameplayStatics::DoesSaveGameExist(UIBCharacterSaveGame::SlotName, UIBCharacterSaveGame::UserIndex))
	{
		if (UIBCharacterSaveGame* Save = Cast<UIBCharacterSaveGame>(
			UGameplayStatics::LoadGameFromSlot(UIBCharacterSaveGame::SlotName, UIBCharacterSaveGame::UserIndex)))
		{
			Roster = Save->Characters;
			LastActiveId = Save->LastActiveId;

			// Belt and braces: a corrupt or hand-edited save never overfills the billets.
			if (Roster.Num() > MaxCharacters)
			{
				Roster.SetNum(MaxCharacters);
			}
		}
	}

	UE_LOG(LogIronBreach, Log, TEXT("CharacterSubsystem: %d operative(s) on file"), Roster.Num());
}

void UIBCharacterSubsystem::SaveRoster()
{
	UIBCharacterSaveGame* Save = Cast<UIBCharacterSaveGame>(
		UGameplayStatics::CreateSaveGameObject(UIBCharacterSaveGame::StaticClass()));
	if (!Save)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("CharacterSubsystem: could not create save object"));
		return;
	}

	Save->Characters = Roster;
	Save->LastActiveId = LastActiveId;

	if (!UGameplayStatics::SaveGameToSlot(Save, UIBCharacterSaveGame::SlotName, UIBCharacterSaveGame::UserIndex))
	{
		UE_LOG(LogIronBreach, Warning, TEXT("CharacterSubsystem: save to slot '%s' FAILED"), UIBCharacterSaveGame::SlotName);
	}
}

FString UIBCharacterSubsystem::SanitizeCallsign(const FString& Raw)
{
	FString Clean;
	Clean.Reserve(Raw.Len());

	for (const TCHAR C : Raw.ToUpper())
	{
		const bool bOk = (C >= TEXT('A') && C <= TEXT('Z'))
			|| (C >= TEXT('0') && C <= TEXT('9'))
			|| C == TEXT(' ') || C == TEXT('-') || C == TEXT('_') || C == TEXT('.');
		if (bOk)
		{
			// No double spaces — callsigns read like stencils, not sentences.
			if (C == TEXT(' ') && Clean.EndsWith(TEXT(" ")))
			{
				continue;
			}
			Clean.AppendChar(C);
		}
	}

	Clean.TrimStartAndEndInline();
	if (Clean.Len() > 16)
	{
		Clean.LeftInline(16);
		Clean.TrimStartAndEndInline();
	}
	return Clean;
}

FString UIBCharacterSubsystem::GenerateCallsign()
{
	// Service-issue placeholder: OPERATIVE-#### (players can decommission and redo).
	return FString::Printf(TEXT("OPERATIVE-%04d"), FMath::RandRange(0, 9999));
}

bool UIBCharacterSubsystem::CreateCharacter(const FString& Callsign, EIBOperativeClass Class,
	EIBOperativeGender Gender, FIBCharacterRecord& OutCharacter, FText& OutError)
{
	if (!CanCreateCharacter())
	{
		OutError = NSLOCTEXT("IBCharacter", "ErrFull", "ALL BILLETS FILLED — DECOMMISSION AN OPERATIVE FIRST");
		return false;
	}

	if (!IBCharacter::ClassAvailable(Class))
	{
		OutError = NSLOCTEXT("IBCharacter", "ErrClassLocked", "THAT CORPS IS NOT YET OPEN");
		return false;
	}

	FString Clean = SanitizeCallsign(Callsign);
	if (Clean.IsEmpty())
	{
		Clean = GenerateCallsign();
	}

	for (const FIBCharacterRecord& Existing : Roster)
	{
		if (Existing.Callsign.Equals(Clean, ESearchCase::IgnoreCase))
		{
			OutError = NSLOCTEXT("IBCharacter", "ErrDupName", "CALLSIGN ALREADY IN SERVICE");
			return false;
		}
	}

	FIBCharacterRecord Record;
	Record.CharacterId = FGuid::NewGuid();
	Record.Callsign = Clean;
	Record.Class = Class;
	Record.Gender = Gender;
	Record.Level = 1;
	Record.CreatedUtc = FDateTime::UtcNow();
	Record.LastPlayedUtc = FDateTime(0);

	Roster.Add(Record);
	OutCharacter = Record;

	UE_LOG(LogIronBreach, Log, TEXT("CharacterSubsystem: enlisted '%s' (%s / %s)"),
		*Record.Callsign,
		*IBCharacter::ClassName(Record.Class).ToString(),
		*IBCharacter::GenderName(Record.Gender).ToString());

	SaveRoster();
	OnRosterChanged.Broadcast();

	// Creation IS the choice for this run.
	SelectCharacter(Record.CharacterId);
	return true;
}

bool UIBCharacterSubsystem::DeleteCharacter(const FGuid& CharacterId)
{
	const int32 Removed = Roster.RemoveAll([&CharacterId](const FIBCharacterRecord& R)
	{
		return R.CharacterId == CharacterId;
	});

	if (Removed == 0)
	{
		return false;
	}

	if (ActiveCharacterId == CharacterId)
	{
		ActiveCharacterId.Invalidate();
	}
	if (LastActiveId == CharacterId)
	{
		LastActiveId.Invalidate();
	}

	UE_LOG(LogIronBreach, Log, TEXT("CharacterSubsystem: decommissioned %s"), *CharacterId.ToString());

	SaveRoster();
	OnRosterChanged.Broadcast();
	return true;
}

void UIBCharacterSubsystem::SetCharacterLevel(const FGuid& CharacterId, int32 Level)
{
	for (FIBCharacterRecord& R : Roster)
	{
		if (R.CharacterId == CharacterId)
		{
			if (R.Level != Level)
			{
				R.Level = FMath::Max(1, Level);
				SaveRoster();
				OnRosterChanged.Broadcast();
			}
			return;
		}
	}
}

bool UIBCharacterSubsystem::SelectCharacter(const FGuid& CharacterId)
{
	FIBCharacterRecord* Found = nullptr;
	for (FIBCharacterRecord& R : Roster)
	{
		if (R.CharacterId == CharacterId)
		{
			Found = &R;
			break;
		}
	}

	if (!Found)
	{
		return false;
	}

	ActiveCharacterId = CharacterId;
	LastActiveId = CharacterId;
	Found->LastPlayedUtc = FDateTime::UtcNow();

	SaveRoster();
	OnActiveCharacterChanged.Broadcast(*Found);

	UE_LOG(LogIronBreach, Log, TEXT("CharacterSubsystem: '%s' on station"), *Found->Callsign);
	return true;
}

bool UIBCharacterSubsystem::HasActiveCharacter() const
{
	return FindRecord(ActiveCharacterId) != nullptr;
}

bool UIBCharacterSubsystem::GetActiveCharacter(FIBCharacterRecord& OutCharacter) const
{
	if (const FIBCharacterRecord* Found = FindRecord(ActiveCharacterId))
	{
		OutCharacter = *Found;
		return true;
	}
	return false;
}

const FIBCharacterRecord* UIBCharacterSubsystem::FindRecord(const FGuid& Id) const
{
	if (!Id.IsValid())
	{
		return nullptr;
	}
	for (const FIBCharacterRecord& R : Roster)
	{
		if (R.CharacterId == Id)
		{
			return &R;
		}
	}
	return nullptr;
}
