#include "Online/IBWatchTypes.h"
#include "UI/IBStyleKit.h"
#include "Misc/PackageName.h"
#include "UObject/UObjectGlobals.h"
#include "Engine/Texture2D.h"

namespace IBWatchData
{
	struct FDestRow
	{
		const TCHAR* Id; const TCHAR* Name; const TCHAR* Short; const TCHAR* Codename; const TCHAR* Threat; int32 Level;
		const TCHAR* Type; const TCHAR* Brief; const TCHAR* Team; const TCHAR* Mech; const TCHAR* Map;
		EIBDestinationKind Kind; FVector2D Pos; int32 SquadMin; int32 SquadMax; bool bAvailable;
		const TCHAR* Recon = nullptr;
	};

	FIBDestination MakeDest(const FDestRow& R)
	{
		FIBDestination D;
		D.Id = FName(R.Id);
		D.SectorId = FName(TEXT("carrow"));
		D.Name = FText::FromString(R.Name);
		D.ShortName = FText::FromString(R.Short);
		D.Codename = FText::FromString(R.Codename);
		D.ThreatClass = FText::FromString(R.Threat);
		D.ThreatLevel = R.Level;
		D.MissionType = FText::FromString(R.Type);
		D.Brief = FText::FromString(R.Brief);
		D.Fireteam = FText::FromString(R.Team);
		D.MechDeployment = FText::FromString(R.Mech);
		D.MapPath = R.Map;
		D.Kind = R.Kind;
		D.BoardPosition = R.Pos;
		D.SquadMin = R.SquadMin;
		D.SquadMax = R.SquadMax;
		D.bAvailable = R.bAvailable;
		if (R.Recon) { D.ReconStill = TSoftObjectPtr<UTexture2D>(FSoftObjectPath(R.Recon)); }
		return D;
	}

	/** The floor: what ships in the build when no registry asset exists. Positions
	 *  are on the stylised Carrow sector board (land west, sea east, the harbor
	 *  scar mid-right — see UIBSectorBoardWidget's coastline). */
	TArray<FIBDestination> BuiltInDestinations()
	{
		TArray<FIBDestination> Out;
		Out.Add(MakeDest({ TEXT("watch"), TEXT("CARROW-1 · THE WATCH"), TEXT("THE WATCH"), TEXT("THE BASTION"), TEXT("SECURE"), 0,
			TEXT("COMMAND DECK"),
			TEXT("The fortress Carrowgate raised around the wound PALAWAN left in the harbor. You are on the sea wall's watch floor. Pick a breach; the squad travels together."),
			TEXT("SQUAD LINKED"), TEXT("—"),
			TEXT("/Game/FirstPerson/Lvl_MainMenu"), EIBDestinationKind::Bastion, FVector2D(0.545, 0.640), 1, 8, true }));
		Out.Add(MakeDest({ TEXT("carrow_gate"), TEXT("CARROW GATE GARRISON"), TEXT("GATE GARRISON"), TEXT("OP. LANDFALL · M1"), TEXT("CLASS A — PALAWAN"), 4,
			TEXT("KAIJU SUPPRESSION · HOLD THE GATE"),
			TEXT("PALAWAN's spawn are on the breakwater again. Crew the batteries, get the civilians behind the wall and hold the north gate until the mech pair is cleared to drop."),
			TEXT("1–8 OPERATORS"), TEXT("AUTHORIZED · 1 PAIR"),
			TEXT("/Game/LevelPrototyping/CarrowGateGarrison"), EIBDestinationKind::Operation, FVector2D(0.605, 0.505), 1, 8, true, TEXT("/Game/IronBreach/Watch/Stills/T_Recon_CarrowGate.T_Recon_CarrowGate") }));
		Out.Add(MakeDest({ TEXT("carrow_zone"), TEXT("CARROW EXCLUSION ZONE"), TEXT("EXCLUSION ZONE"), TEXT("PATROL GRID 7"), TEXT("CLASS C — ROAMING PACKS"), 2,
			TEXT("PATROL · CULL & RECOVER"),
			TEXT("Basin plains, birch stands, the abandoned village. Burrow-shoal packs come out of the culverts at dusk. Patrol, cull, recover material, mark the burrows."),
			TEXT("1–4 OPERATORS"), TEXT("NOT REQUIRED"),
			TEXT("/Game/Lvl_Plains"), EIBDestinationKind::Sector, FVector2D(0.300, 0.330), 1, 4, true, TEXT("/Game/IronBreach/Watch/Stills/T_Recon_Plains.T_Recon_Plains") }));
		Out.Add(MakeDest({ TEXT("firing_line"), TEXT("FIRING LINE"), TEXT("FIRING LINE"), TEXT("TRAINING STAND 2"), TEXT("NO THREAT — LIVE FIRE"), 0,
			TEXT("TRAINING · LIVE FIRE"),
			TEXT("The Defense Force range behind the sea wall. Zero your kit, run the drill lanes, test the new sights against dummy carapace. Nothing here counts."),
			TEXT("1–4 OPERATORS"), TEXT("TRAINING FRAME"),
			TEXT("/Game/FirstPerson/Lvl_FirstPerson"), EIBDestinationKind::Range, FVector2D(0.380, 0.790), 1, 4, true, TEXT("/Game/IronBreach/Watch/Stills/T_Recon_FiringLine.T_Recon_FiringLine") }));
		Out.Add(MakeDest({ TEXT("drowned_quarter"), TEXT("THE DROWNED QUARTER"), TEXT("DROWNED QUARTER"), TEXT("SEALED DISTRICT"), TEXT("CLASS B — UNCONFIRMED"), 3,
			TEXT("RECON · SEALED"),
			TEXT("The old harbor district the sea took when the wall went up. Something is nesting in the flooded blocks. Not cleared for deployment."),
			TEXT("—"), TEXT("NOT AUTHORIZED"),
			TEXT(""), EIBDestinationKind::Locked, FVector2D(0.630, 0.870), 2, 4, false }));
		return Out;
	}

	FIBSector MakeSector(const TCHAR* Id, const TCHAR* Name, const TCHAR* Region, const TCHAR* Status, float Lat, float Lon,
		const FLinearColor& Color, const TCHAR* Glyph, int32 Level, bool bLive, bool bHot, bool bHome, const TCHAR* Brief, const TCHAR* Lock)
	{
		FIBSector S;
		S.Id = FName(Id);
		S.Name = FText::FromString(Name);
		S.Region = FText::FromString(Region);
		S.Status = FText::FromString(Status);
		S.Latitude = Lat;
		S.Longitude = Lon;
		S.Color = Color;
		S.Glyph = Glyph;
		S.ThreatLevel = Level;
		S.bLive = bLive;
		S.bHot = bHot;
		S.bHome = bHome;
		S.Brief = FText::FromString(Brief);
		S.LockReason = FText::FromString(Lock);
		return S;
	}

	/** Seven sectors: one live (ours), six that say what the rest of the world is doing. */
	TArray<FIBSector> BuiltInSectors()
	{
		const FLinearColor Violet(0.65f, 0.42f, 1.0f);
		const FLinearColor Dust(0.31f, 0.36f, 0.41f);
		TArray<FIBSector> Out;
		Out.Add(MakeSector(TEXT("carrow"), TEXT("CARROW SECTOR"), TEXT("AURENTINE EAST COAST"), TEXT("BREACH ACTIVE · CLASS A"), 33.f, 20.f,
			IBStyle::Amber(), TEXT("A"), 4, true, true, true,
			TEXT("Carrowgate and the Bastion raised around the scar PALAWAN left. Three sites answer the relay."), TEXT("")));
		Out.Add(MakeSector(TEXT("kessandra"), TEXT("KESSANDRA REACH"), TEXT("NORTHERN KESSANDRA"), TEXT("CLASS B · RELAY DARK"), 41.f, 135.f,
			IBStyle::Amber(), TEXT("B"), 3, false, true, false,
			TEXT("A Class B breach was confirmed on day 212. Nothing from the Reach station since. The relay is dark; no drop corridor can be held."),
			TEXT("RELAY DARK — NO LINK TO THE REACH")));
		Out.Add(MakeSector(TEXT("saltgate"), TEXT("THE SALT GATE"), TEXT("EQUATORIAL ARCHIPELAGO"), TEXT("CATASTROPHE CLASS · SEALED"), 3.f, -104.f,
			IBStyle::Danger(), TEXT("X"), 5, false, true, false,
			TEXT("The archipelago the first city-killer came out of. Sealed. Nothing that went in has come back out. There is no return corridor."),
			TEXT("SEALED — NO RETURN CORRIDOR")));
		Out.Add(MakeSector(TEXT("meridian"), TEXT("MERIDIAN SHELF"), TEXT("SOUTHERN MERIDIAN"), TEXT("QUIET · NO OPEN BREACH"), -38.f, -58.f,
			IBStyle::Cyan(), TEXT("·"), 0, false, false, false,
			TEXT("The Shelf stands its own watch. No open breach, no call for help. Material convoys leave for Carrow every nine days."),
			TEXT("NO OPEN BREACH — NO CALL FOR HELP")));
		Out.Add(MakeSector(TEXT("vosk"), TEXT("VOSK PENINSULA"), TEXT("VESK SOUTHEAST"), TEXT("NO CONTACT · 41 DAYS"), -27.f, 80.f,
			Violet, TEXT("?"), 0, false, false, false,
			TEXT("Forty-one days without contact. Last word from the pier station: \"It came up under the piers.\" Reconnaissance not yet authorized."),
			TEXT("NO CONTACT — RECON NOT AUTHORIZED")));
		Out.Add(MakeSector(TEXT("haldane"), TEXT("HALDANE ICE"), TEXT("NORTHERN ICE LINE"), TEXT("DORMANT · SKELETON CREW"), 72.f, 44.f,
			Dust, TEXT("·"), 0, false, false, false,
			TEXT("The listening station above the ice line. Dormant, skeleton crew, no breach on record. Nothing to shoot."),
			TEXT("DORMANT — NO DEPLOYMENT ABOVE THE ICE LINE")));
		Out.Add(MakeSector(TEXT("orrin"), TEXT("ORRIN STRAIT"), TEXT("ORRIN ISLANDS"), TEXT("CLASS C SIGHTINGS"), -9.f, 141.f,
			IBStyle::Cyan(), TEXT("C"), 2, false, false, false,
			TEXT("Class C sightings along the strait. The patrol rotation is full for the next window; Carrow crews are not on the roster yet."),
			TEXT("PATROL ROTATION FULL — NEXT WINDOW 6 H")));
		return Out;
	}

	const UIBDestinationRegistry* Registry()
	{
		static const UIBDestinationRegistry* Asset = nullptr;
		static bool bTried = false;
		if (!bTried)
		{
			bTried = true;
			Asset = LoadObject<UIBDestinationRegistry>(nullptr, TEXT("/Game/IronBreach/Watch/DA_Destinations.DA_Destinations"));
		}
		return Asset;
	}

	const TArray<FIBDestination>& CachedDestinations()
	{
		static TArray<FIBDestination> List;
		static bool bLoaded = false;
		if (!bLoaded)
		{
			bLoaded = true;
			List = BuiltInDestinations();
			// Content override: a registry asset wins wholesale when it has rows.
			if (const UIBDestinationRegistry* Asset = Registry())
			{
				if (Asset->Destinations.Num() > 0) { List = Asset->Destinations; }
			}
		}
		return List;
	}

	const TArray<FIBSector>& CachedSectors()
	{
		static TArray<FIBSector> List;
		static bool bLoaded = false;
		if (!bLoaded)
		{
			bLoaded = true;
			List = BuiltInSectors();
			if (const UIBDestinationRegistry* Asset = Registry())
			{
				if (Asset->Sectors.Num() > 0) { List = Asset->Sectors; }
			}
		}
		return List;
	}
}

const TArray<FIBDestination>& IBWatch::Destinations()
{
	return IBWatchData::CachedDestinations();
}

const FIBDestination* IBWatch::Find(FName Id)
{
	if (Id.IsNone()) { return nullptr; }
	return IBWatchData::CachedDestinations().FindByPredicate([Id](const FIBDestination& D) { return D.Id == Id; });
}

const TArray<FIBSector>& IBWatch::Sectors()
{
	return IBWatchData::CachedSectors();
}

const FIBSector* IBWatch::FindSector(FName Id)
{
	if (Id.IsNone()) { return nullptr; }
	return IBWatchData::CachedSectors().FindByPredicate([Id](const FIBSector& S) { return S.Id == Id; });
}

FName IBWatch::HomeSectorId()
{
	for (const FIBSector& S : IBWatchData::CachedSectors()) { if (S.bHome) { return S.Id; } }
	for (const FIBSector& S : IBWatchData::CachedSectors()) { if (S.bLive) { return S.Id; } }
	return NAME_None;
}

FName IBWatch::DestinationForMap(const FString& MapNameOrPath)
{
	// "/Game/FirstPerson/Lvl_MainMenu", "Lvl_MainMenu", "UEDPIE_0_Lvl_MainMenu" all resolve.
	FString Short = FPackageName::GetShortName(MapNameOrPath);
	int32 Dot = INDEX_NONE;
	if (Short.FindChar(TEXT('.'), Dot)) { Short.LeftInline(Dot); }
	int32 Query = INDEX_NONE;
	if (Short.FindChar(TEXT('?'), Query)) { Short.LeftInline(Query); }
	if (Short.StartsWith(TEXT("UEDPIE_")))
	{
		// UEDPIE_<n>_Name
		int32 SecondUnderscore = Short.Find(TEXT("_"), ESearchCase::CaseSensitive, ESearchDir::FromStart, 7);
		if (SecondUnderscore != INDEX_NONE) { Short.RightChopInline(SecondUnderscore + 1); }
	}
	for (const FIBDestination& D : IBWatchData::CachedDestinations())
	{
		if (!D.MapPath.IsEmpty() && FPackageName::GetShortName(D.MapPath).Equals(Short, ESearchCase::IgnoreCase))
		{
			return D.Id;
		}
	}
	return NAME_None;
}

FName IBWatch::WatchId()
{
	static const FName Id(TEXT("watch"));
	return Id;
}

FLinearColor IBWatch::KindColor(EIBDestinationKind Kind)
{
	switch (Kind)
	{
	case EIBDestinationKind::Operation: return IBStyle::Amber();
	case EIBDestinationKind::Sector:    return IBStyle::Cyan();
	case EIBDestinationKind::Range:     return FLinearColor(0.44f, 0.82f, 0.56f);
	case EIBDestinationKind::Bastion:   return IBStyle::TextHi();
	case EIBDestinationKind::Locked:
	default:                            return FLinearColor(0.30f, 0.34f, 0.42f);
	}
}

FText IBWatch::KindLabel(EIBDestinationKind Kind)
{
	switch (Kind)
	{
	case EIBDestinationKind::Operation: return NSLOCTEXT("IBWatch", "KindOperation", "OPERATION");
	case EIBDestinationKind::Sector:    return NSLOCTEXT("IBWatch", "KindSector", "SECTOR");
	case EIBDestinationKind::Range:     return NSLOCTEXT("IBWatch", "KindRange", "RANGE");
	case EIBDestinationKind::Bastion:   return NSLOCTEXT("IBWatch", "KindBastion", "BASTION");
	case EIBDestinationKind::Locked:
	default:                            return NSLOCTEXT("IBWatch", "KindLocked", "NOT CLEARED");
	}
}

FText IBWatch::ThreatLevelLabel(int32 Level)
{
	switch (Level)
	{
	case 1: return NSLOCTEXT("IBWatch", "ClassD", "CLASS D");
	case 2: return NSLOCTEXT("IBWatch", "ClassC", "CLASS C");
	case 3: return NSLOCTEXT("IBWatch", "ClassB", "CLASS B");
	case 4: return NSLOCTEXT("IBWatch", "ClassA", "CLASS A");
	case 5: return NSLOCTEXT("IBWatch", "Catastrophe", "CATASTROPHE");
	default: return NSLOCTEXT("IBWatch", "NoThreat", "NO THREAT");
	}
}
