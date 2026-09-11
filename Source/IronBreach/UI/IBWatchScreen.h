#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "Components/Border.h"
#include "IBWatchScreen.generated.h"

class UTextBlock;
class UButton;
class UBorder;
class UImage;
class UOverlay;
class UHorizontalBox;
class UVerticalBox;
class UCanvasPanel;
class UCanvasPanelSlot;
class UIBPlanetWidget;
class UIBSectorBoardWidget;
class AIBWatchBoard;
class AIBPlayerState;
class UIBSessionSubsystem;
struct FIBDestination;
struct FIBSector;

/** Presentation-only chamfered frame. Keeps the card's padding and child layout in UBorder. */
UCLASS()
class IRONBREACH_API UIBWatchCardBorder : public UBorder
{
	GENERATED_BODY()
protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
};

/**
 * THE WATCH — the command deck. The planet turns outside the glass
 * (UIBPlanetWidget), every sector of the world is pinned on it, and the card
 * on the right reads the pick: recon still, threat class, mission type,
 * objective, fireteam, mech deployment, DEPLOY. Anyone proposes, the host
 * confirms; DEPLOY is not a countdown any more — it is the drop: the camera
 * aims at the breach and falls, the deck fades, white-out, and the squad
 * travels together on the black frame (AIBWatchBoard::DeployAtServerTime is
 * the shared clock, IBWatch::DeployDropSeconds the length).
 *
 * Two views on one screen:
 *   orbit  — the globe; drag turns it, wheel zooms, click a pin, double-click
 *            (or VIEW MISSION) opens the sector's breach board
 *   board  — UIBSectorBoardWidget over the zoomed-in terrain, with every site
 *            of the sector pinned; BACK TO ORBIT / Esc returns
 *
 * Two lives, one widget (unchanged from v1):
 *   lobby  — UIBMainMenuWidget adds it to the viewport in the ?listen menu world
 *   in-game — registered menu screen "Watch" (B key / System → THE WATCH)
 *
 * State lives on AIBWatchBoard (replicated); this widget only reads it and
 * calls AIBPlayerState::WatchPropose / WatchConfirm / WatchCancel.
 */
UCLASS()
class IRONBREACH_API UIBWatchScreen : public UIBMenuScreen
{
	GENERATED_BODY()

public:
	/** Browse a briefing without proposing or confirming a deployment. */
	void FocusDestination(FName DestinationId);
	FName GetFocusedDestinationId() const { return SelectedId; }
	/** Dev hooks for the -IBWatchShots tour (UIBWatchSubsystem). */
	void DevOpenBoard() { GoBoard(); }
	void DevOpenOrbit() { GoOrbit(); }
	void DevDeploy() { HandlePrimary(); }

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual void NativeDestruct() override;
	virtual void NativeScreenOpened() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UFUNCTION() void HandlePicked(FName DestinationId);
	UFUNCTION() void HandleSectorPicked(FName SectorId);
	UFUNCTION() void HandleSectorOpened(FName SectorId);
	UFUNCTION() void HandleBoardChanged();
	UFUNCTION() void HandlePrimary();
	UFUNCTION() void HandleSecondary();
	UFUNCTION() void HandleView();
	UFUNCTION() void HandleInvite();
	UFUNCTION() void HandleLeave();
	UFUNCTION() void HandleSite0();
	UFUNCTION() void HandleSite1();
	UFUNCTION() void HandleSite2();
	UFUNCTION() void HandleSite3();
	UFUNCTION() void HandleSite4();
	UFUNCTION() void HandleSite5();

private:
	void StartVisualTour();
	void BuildLayout();
	void BuildHeader(UOverlay* Root);
	void BuildRoster(UOverlay* Root);
	void BuildCard(UOverlay* Root);
	void BuildFooter(UOverlay* Root);

	void EnsureBoard();
	void GoBoard();
	void GoOrbit();
	void PickSite(int32 Index);

	void RefreshAll();
	void RefreshHeader();
	void RefreshRoster();
	void RefreshCard();
	void RefreshSites();
	void RefreshThumb(const FIBDestination* D, const FIBSector* S);
	void RefreshNarrator();
	void RefreshButtons();
	void RefreshCallout();
	void TickViews(const FVector2D& ScreenSize, float DeltaTime);

	bool IsHost() const;
	bool IsOffline() const;
	int32 LocalPlayerId() const;
	AIBPlayerState* LocalPlayerState() const;
	UIBSessionSubsystem* GetSessions() const;
	FName DefaultSelection() const;
	FName SectorOf(FName DestinationId) const;
	const FIBSector* CurrentSector() const;

	// ---- the deck ----
	UPROPERTY(Transient) TObjectPtr<UIBPlanetWidget> Planet;
	UPROPERTY(Transient) TObjectPtr<UCanvasPanel> BoardCanvas;
	UPROPERTY(Transient) TObjectPtr<UCanvasPanelSlot> BoardSlot;
	UPROPERTY(Transient) TObjectPtr<UIBSectorBoardWidget> Board;
	UPROPERTY(Transient) TObjectPtr<UBorder> BoardFrame;
	UPROPERTY(Transient) TObjectPtr<UBorder> Shade;
	UPROPERTY(Transient) TObjectPtr<UOverlay> Hud;
	UPROPERTY(Transient) TObjectPtr<UBorder> Flash;
	UPROPERTY(Transient) TObjectPtr<AIBWatchBoard> BoardState;

	// ---- header / roster / footer ----
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HeaderSubText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HeaderSubHi;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> Crumbs;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NetText;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> RosterRow;
	UPROPERTY(Transient) TObjectPtr<UButton> InviteButton;
	UPROPERTY(Transient) TObjectPtr<UButton> LeaveButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LeaveLabel;

	// ---- card ----
	UPROPERTY(Transient) TObjectPtr<UBorder> CardPanel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubText;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> SitesRow;
	UPROPERTY(Transient) TArray<TObjectPtr<UButton>> SiteButtons;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SiteLabels;
	TArray<FName> SiteIds;
	UPROPERTY(Transient) TObjectPtr<UBorder> ThumbFallback;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ThumbFallbackText;
	UPROPERTY(Transient) TObjectPtr<UImage> ThumbImage;
	UPROPERTY(Transient) TObjectPtr<UBorder> ThumbTagFrame;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ThumbTag;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ThumbCaption;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ThreatLabel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ThreatValue;
	UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> MeterBars;
	UPROPERTY(Transient) TObjectPtr<UBorder> TypeBullet;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TypeValue;
	UPROPERTY(Transient) TObjectPtr<UBorder> ObjBullet;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ObjValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TeamValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MechValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NarratorText;
	UPROPERTY(Transient) TObjectPtr<UButton> PrimaryButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PrimaryLabel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PrimaryChevron;
	UPROPERTY(Transient) TObjectPtr<UButton> SecondaryButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SecondaryLabel;
	UPROPERTY(Transient) TObjectPtr<UButton> ViewButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ViewLabel;

	// ---- state ----
	FName SelectedSector;
	FName SelectedId;
	bool bBoardView = false;
	float DiveT = 0.f;          // 0 orbit .. 1 board, linear; eased on the way out
	float RefreshAccumulator = 0.f;
	float RosterAccumulator = 0.f;
	bool bDropping = false;
	FVector2D LastScreenSize = FVector2D(1600.0, 900.0);
};
