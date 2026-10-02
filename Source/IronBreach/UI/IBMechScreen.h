#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBMechScreen.generated.h"

class AIBMech_Base;
class APawn;
enum class EIBMechStationOccupancy : uint8;
class UTextBlock;
class UProgressBar;
class UImage;
class UIBItemGlyphWidget;

/**
 * MECH — the frame sheet of the Personal ring. Reads the live AIBMech_Base in the
 * current world (the one the local player is crewing, else the first on station):
 * chassis, hull integrity, the fixed arm weapon with its ammo and recovery, the two
 * physical stations and who is in them, the Concord link, and the Watch's mech deployment
 * authorization for this location. Stations (HULL / GUNNER SEAT) are not roles (DRIVER /
 * GUNNER): a role can swap without anyone moving, and roles are only knowable where this
 * frame has authority, so they are shown only there. Nothing on this sheet is invented: no
 * hardpoints, cores or mech equipment exist in the game yet, so none are drawn.
 * Pure view — never boards, fires or swaps seats.
 */
UCLASS()
class IRONBREACH_API UIBMechScreen : public UIBMenuScreen
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeScreenOpened() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

private:
	AIBMech_Base* FindFrame() const;
	void Refresh();
	/** Who is at a station, named from that station pawn's replicated PlayerState. */
	FText StationOccupant(const APawn* StationPawn, EIBMechStationOccupancy Occupancy) const;
	/** DRIVER / GUNNER, and only where this machine can actually know it — see the .cpp. */
	FText StationRole(const AIBMech_Base* Frame, const APawn* StationPawn) const;

	UPROPERTY(Transient) TObjectPtr<UTextBlock> FrameName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FrameStatus;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HullValue;
	UPROPERTY(Transient) TObjectPtr<UProgressBar> HullBar;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> WeaponName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> WeaponMeta;
	UPROPERTY(Transient) TObjectPtr<UImage> WeaponIcon;
	UPROPERTY(Transient) TObjectPtr<UIBItemGlyphWidget> WeaponGlyph;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AmmoValue;
	UPROPERTY(Transient) TObjectPtr<UProgressBar> AmmoBar;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CooldownValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HullOccupantName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HullOccupantRole;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SeatOccupantName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SeatOccupantRole;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ConcordState;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DeployLocation;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DeployAuthorization;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DeployFireteam;
	UPROPERTY(Transient) TObjectPtr<class UWidget> FrameBody;
	UPROPERTY(Transient) TObjectPtr<class UWidget> EmptyBody;

	float RefreshClock = 0.f;
};
