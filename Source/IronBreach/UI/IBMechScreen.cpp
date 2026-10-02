#include "UI/IBMechScreen.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBItemTileWidget.h"
#include "Mech/IBMech_Base.h"
#include "Mech/IBGunnerSeat.h"
#include "Mech/ConcordComponent.h"
#include "Combat/WeaponVisualData.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "Online/IBWatchTypes.h"
#include "UI/IBUISettings.h"
#include "Components/ProgressBar.h"
#include "Components/Image.h"
#include "Components/WidgetSwitcher.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"

namespace IBMechSheet
{
	/** "BP_Caryatid_C" -> "CARYATID": the chassis as the content names it, nothing invented. */
	FText ChassisName(const AIBMech_Base* Frame)
	{
		FString Name = Frame ? Frame->GetClass()->GetName() : FString();
		Name.RemoveFromEnd(TEXT("_C"));
		Name.RemoveFromStart(TEXT("BP_"));
		Name.RemoveFromStart(TEXT("IB"));
		Name = Name.Replace(TEXT("_"), TEXT(" ")).ToUpper();
		return FText::FromString(Name.IsEmpty() ? TEXT("FRAME") : Name);
	}

	/** Is this player crewing this frame?
	 *
	 *  Read from the station pawns' PlayerStates, never from the frame's seat pointers. Those
	 *  are AController pointers, and a client is not sent another player's controller
	 *  (AController is only relevant to its owner) nor any AI controller at all — so on a
	 *  client they are always null, and replicating them would still hand over a reference
	 *  that cannot resolve. A pawn's PlayerState does replicate to everyone. */
	bool IsCrewedBy(const AIBMech_Base* Frame, const APlayerState* Who)
	{
		if (!Frame || !Who) { return false; }
		if (Frame->GetPlayerState() == Who) { return true; }
		return Frame->GunnerSeat && Frame->GunnerSeat->GetPlayerState() == Who;
	}

	UProgressBar* Bar(UWidgetTree* Tree, UVerticalBox* Box, FLinearColor Fill, float Height = 4.f)
	{
		UProgressBar* Result = Tree->ConstructWidget<UProgressBar>();
		FProgressBarStyle Style;
		Style.SetBackgroundImage(IBStyle::RoundedBrush(FLinearColor(.06f, .11f, .14f, .9f), 0));
		Style.SetFillImage(IBStyle::RoundedBrush(FLinearColor::White, 0));
		Result->SetWidgetStyle(Style);
		Result->SetFillColorAndOpacity(Fill);
		Result->SetPercent(0.f);
		USizeBox* Size = Tree->ConstructWidget<USizeBox>();
		Size->SetHeightOverride(Height);
		Size->SetContent(Result);
		Box->AddChildToVerticalBox(Size)->SetPadding(FMargin(0, 6, 0, 0));
		return Result;
	}
}

void UIBMechScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UVerticalBox* Body = BuildHangarPage(NSLOCTEXT("IBMech", "Controls", "LIVE FRAME READOUT     BOARD A FRAME IN THE FIELD TO CREW IT     Q E  SWITCH MENU     ESC  RETURN"));

	UHorizontalBox* PageTitle = WidgetTree->ConstructWidget<UHorizontalBox>();
	UVerticalBox* TitleCopy = WidgetTree->ConstructWidget<UVerticalBox>();
	TitleCopy->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree, NSLOCTEXT("IBMech", "Title", "MECH"), 30));
	TitleCopy->AddChildToVerticalBox(IBHangar::Label(WidgetTree, TEXT("BREAKWATER FRAME  /  CREW OF TWO"), 11, IBStyle::TextLo()))->SetPadding(FMargin(0, 4, 0, 0));
	PageTitle->AddChildToHorizontalBox(TitleCopy)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	FrameStatus = IBHangar::Label(WidgetTree, TEXT(""), 11, IBHangar::Cyan());
	PageTitle->AddChildToHorizontalBox(FrameStatus)->SetVerticalAlignment(VAlign_Bottom);
	Body->AddChildToVerticalBox(PageTitle)->SetPadding(FMargin(0, 0, 0, 18));

	UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
	Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	// ---- Frame dossier (left): live systems, or the empty-station copy ----
	UWidgetSwitcher* Pages = WidgetTree->ConstructWidget<UWidgetSwitcher>();

	UVerticalBox* Frame = WidgetTree->ConstructWidget<UVerticalBox>();
	FrameName = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 28);
	Frame->AddChildToVerticalBox(FrameName);
	IBHangar::Rule(WidgetTree, Frame, 16);

	UHorizontalBox* Systems = WidgetTree->ConstructWidget<UHorizontalBox>();
	UVerticalBox* Hull = WidgetTree->ConstructWidget<UVerticalBox>();
	Hull->AddChildToVerticalBox(IBHangar::Label(WidgetTree, TEXT("HULL INTEGRITY"), 10, IBStyle::TextLo()));
	HullValue = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 26);
	Hull->AddChildToVerticalBox(HullValue)->SetPadding(FMargin(0, 4, 0, 0));
	HullBar = IBMechSheet::Bar(WidgetTree, Hull, IBHangar::Cyan());
	Systems->AddChildToHorizontalBox(Hull)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	UVerticalBox* Concord = WidgetTree->ConstructWidget<UVerticalBox>();
	Concord->AddChildToVerticalBox(IBHangar::Label(WidgetTree, TEXT("CONCORD"), 10, IBStyle::TextLo()));
	ConcordState = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 13, IBHangar::Cyan(), 60);
	ConcordState->SetAutoWrapText(true);
	Concord->AddChildToVerticalBox(ConcordState)->SetPadding(FMargin(0, 6, 0, 0));
	UHorizontalBoxSlot* ConcordSlot = Systems->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, Concord, 260));
	ConcordSlot->SetPadding(FMargin(28, 0, 0, 0)); ConcordSlot->SetVerticalAlignment(VAlign_Top);
	Frame->AddChildToVerticalBox(Systems);

	IBHangar::SectionTitle(WidgetTree, Frame, TEXT("ARM WEAPON"), 26, 12);
	UHorizontalBox* Weapon = WidgetTree->ConstructWidget<UHorizontalBox>();
	UOverlay* Art = WidgetTree->ConstructWidget<UOverlay>();
	WeaponIcon = WidgetTree->ConstructWidget<UImage>(); WeaponIcon->SetVisibility(ESlateVisibility::Collapsed);
	UScaleBox* ArtFit = WidgetTree->ConstructWidget<UScaleBox>(); ArtFit->SetStretch(EStretch::ScaleToFit); ArtFit->SetContent(WeaponIcon);
	UOverlaySlot* ArtSlot = Art->AddChildToOverlay(ArtFit); ArtSlot->SetHorizontalAlignment(HAlign_Fill); ArtSlot->SetVerticalAlignment(VAlign_Fill); ArtSlot->SetPadding(FMargin(10));
	WeaponGlyph = CreateWidget<UIBItemGlyphWidget>(this);
	USizeBox* GlyphSize = IBMenuLayout::Width(WidgetTree, WeaponGlyph, 64); GlyphSize->SetHeightOverride(64);
	UOverlaySlot* GlyphSlot = Art->AddChildToOverlay(GlyphSize); GlyphSlot->SetHorizontalAlignment(HAlign_Center); GlyphSlot->SetVerticalAlignment(VAlign_Center);
	USizeBox* ArtSize = IBMenuLayout::Width(WidgetTree, IBHangar::Inset(WidgetTree, Art, FMargin(0)), 220); ArtSize->SetHeightOverride(124);
	Weapon->AddChildToHorizontalBox(ArtSize)->SetPadding(FMargin(0, 0, 22, 0));
	UVerticalBox* WeaponCopy = WidgetTree->ConstructWidget<UVerticalBox>();
	WeaponName = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 20); WeaponName->SetAutoWrapText(true);
	WeaponCopy->AddChildToVerticalBox(WeaponName);
	WeaponMeta = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 60);
	WeaponCopy->AddChildToVerticalBox(WeaponMeta)->SetPadding(FMargin(0, 3, 0, 0));
	UHorizontalBox* AmmoRow = WidgetTree->ConstructWidget<UHorizontalBox>();
	AmmoRow->AddChildToHorizontalBox(IBHangar::Label(WidgetTree, TEXT("AMMUNITION"), 10, IBStyle::TextLo()))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	AmmoValue = IBHangar::Label(WidgetTree, TEXT(""), 12);
	AmmoRow->AddChildToHorizontalBox(AmmoValue);
	WeaponCopy->AddChildToVerticalBox(AmmoRow)->SetPadding(FMargin(0, 16, 0, 0));
	AmmoBar = IBMechSheet::Bar(WidgetTree, WeaponCopy, IBStyle::TextHi());
	CooldownValue = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 11, IBStyle::TextLo(), 60);
	WeaponCopy->AddChildToVerticalBox(CooldownValue)->SetPadding(FMargin(0, 10, 0, 0));
	UHorizontalBoxSlot* WeaponCopySlot = Weapon->AddChildToHorizontalBox(WeaponCopy);
	WeaponCopySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); WeaponCopySlot->SetVerticalAlignment(VAlign_Center);
	Frame->AddChildToVerticalBox(Weapon);

	IBHangar::SectionTitle(WidgetTree, Frame, TEXT("CREW"), 26, 12);
	auto Seat = [this, Frame](const TCHAR* Caption, TObjectPtr<UTextBlock>& OutName, TObjectPtr<UTextBlock>& OutRole)
	{
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
		UHorizontalBoxSlot* MarkSlot = Row->AddChildToHorizontalBox(IBHangar::Glyph(WidgetTree, EIBMenuGlyph::Diamond, IBHangar::Cyan(), 16.f));
		MarkSlot->SetPadding(FMargin(2, 0, 14, 0)); MarkSlot->SetVerticalAlignment(VAlign_Center);
		Row->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, IBHangar::Label(WidgetTree, Caption, 10, IBStyle::TextLo()), 110))->SetVerticalAlignment(VAlign_Center);
		OutName = IBHangar::Label(WidgetTree, TEXT(""), 14);
		UHorizontalBoxSlot* NameSlot = Row->AddChildToHorizontalBox(OutName); NameSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); NameSlot->SetVerticalAlignment(VAlign_Center);
		OutRole = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 10, IBHangar::Cyan(), 140);
		Row->AddChildToHorizontalBox(OutRole)->SetVerticalAlignment(VAlign_Center);
		Frame->AddChildToVerticalBox(IBHangar::Inset(WidgetTree, Row, FMargin(12, 9)))->SetPadding(FMargin(0, 0, 0, 6));
	};
	// Captions name the STATION, which never moves. The role column beside them is filled
	// only where the roles are authoritatively known.
	Seat(TEXT("HULL"), HullOccupantName, HullOccupantRole);
	Seat(TEXT("GUNNER SEAT"), SeatOccupantName, SeatOccupantRole);
	Frame->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree, NSLOCTEXT("IBMech", "Fixed", "FIXED ARM WEAPON  /  NO MODULAR HARDPOINTS FIELDED"), 9, IBStyle::TextLo(), 140))->SetPadding(FMargin(0, 18, 0, 0));
	FrameBody = Frame;
	Pages->AddChild(Frame);

	UVerticalBox* Empty = WidgetTree->ConstructWidget<UVerticalBox>();
	Empty->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree, NSLOCTEXT("IBMech", "NoFrame", "NO FRAME ON STATION"), 28));
	IBHangar::Rule(WidgetTree, Empty, 16);
	UTextBlock* EmptyCopy = IBMenuLayout::Text(WidgetTree, NSLOCTEXT("IBMech", "NoFrameCopy", "Frames are crewed in the field. Board one and its hull, arm weapon, seats and Concord link read out here."), 14, IBStyle::TextLo());
	EmptyCopy->SetAutoWrapText(true); EmptyCopy->SetLineHeightPercentage(1.3f);
	Empty->AddChildToVerticalBox(EmptyCopy);
	EmptyBody = Empty;
	Pages->AddChild(Empty);

	UVerticalBox* Dossier = WidgetTree->ConstructWidget<UVerticalBox>();
	IBMenuLayout::Scroll(WidgetTree, Dossier, Pages);
	Columns->AddChildToHorizontalBox(IBHangar::Dossier(WidgetTree, Dossier, FMargin(26, 24, 26, 22)))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	// ---- Deployment (right): what the Watch says about frames at this location ----
	UVerticalBox* Deploy = WidgetTree->ConstructWidget<UVerticalBox>();
	Deploy->AddChildToVerticalBox(IBHangar::Label(WidgetTree, TEXT("MECH DEPLOYMENT"), 11, IBHangar::Cyan()));
	DeployLocation = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 20); DeployLocation->SetAutoWrapText(true);
	Deploy->AddChildToVerticalBox(DeployLocation)->SetPadding(FMargin(0, 6, 0, 0));
	IBHangar::Rule(WidgetTree, Deploy, 14);
	DeployAuthorization = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 15, IBStyle::TextHi(), 40); DeployAuthorization->SetAutoWrapText(true);
	Deploy->AddChildToVerticalBox(DeployAuthorization);
	DeployFireteam = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 12, IBStyle::TextLo(), 40); DeployFireteam->SetAutoWrapText(true);
	Deploy->AddChildToVerticalBox(DeployFireteam)->SetPadding(FMargin(0, 8, 0, 0));
	UTextBlock* DeployHint = IBMenuLayout::Text(WidgetTree, NSLOCTEXT("IBMech", "DeployHint", "Authorization comes from the destination record on the Watch; a crew of two answers for one frame."), 11, IBStyle::TextLo());
	DeployHint->SetAutoWrapText(true); DeployHint->SetLineHeightPercentage(1.3f);
	Deploy->AddChildToVerticalBox(DeployHint)->SetPadding(FMargin(0, 18, 0, 0));
	UHorizontalBoxSlot* DeploySlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, IBHangar::Panel(WidgetTree, Deploy, FMargin(22)), 380));
	DeploySlot->SetPadding(FMargin(20, 0, 0, 0)); DeploySlot->SetVerticalAlignment(VAlign_Top);

	Refresh();
}

void UIBMechScreen::NativeScreenOpened()
{
	RefreshClock = 0.f;
	Refresh();
}

void UIBMechScreen::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
	Super::NativeTick(Geometry, DeltaTime);
	RefreshClock += DeltaTime;
	if (RefreshClock >= 0.5f) { RefreshClock = 0.f; Refresh(); }
}

AIBMech_Base* UIBMechScreen::FindFrame() const
{
	UWorld* World = GetWorld();
	if (!World) { return nullptr; }
	// "The frame you are crewing" has to be decided from something a client receives, so it is
	// decided from the station pawns' PlayerStates rather than the frame's seat pointers.
	const APlayerState* Mine = GetOwningPlayerState();
	AIBMech_Base* First = nullptr;
	for (TActorIterator<AIBMech_Base> It(World); It; ++It)
	{
		AIBMech_Base* Candidate = *It;
		if (IBMechSheet::IsCrewedBy(Candidate, Mine)) { return Candidate; } // the frame you are crewing wins
		if (!First) { First = Candidate; }
	}
	return First;
}

FText UIBMechScreen::StationOccupant(const APawn* StationPawn, EIBMechStationOccupancy Occupancy) const
{
	// Occupancy says WHETHER someone is there (it is replicated because controllers are not);
	// the station pawn's PlayerState says WHO, and it reaches every machine.
	if (Occupancy == EIBMechStationOccupancy::Copilot) { return NSLOCTEXT("IBMech", "AICopilot", "AI CO-PILOT"); }
	if (Occupancy == EIBMechStationOccupancy::Vacant) { return NSLOCTEXT("IBMech", "EmptySeat", "EMPTY"); }
	const APlayerState* Occupant = StationPawn ? StationPawn->GetPlayerState() : nullptr;
	if (const AIBPlayerState* Operative = Cast<AIBPlayerState>(Occupant)) { return FText::FromString(Operative->GetDisplayCallsign().ToUpper()); }
	if (Occupant) { return FText::FromString(Occupant->GetPlayerName().ToUpper()); }
	return NSLOCTEXT("IBMech", "Operative", "OPERATIVE"); // aboard; their identity has not landed yet
}

FText UIBMechScreen::StationRole(const AIBMech_Base* Frame, const APawn* StationPawn) const
{
	// Roles are keyed by controller, and controllers do not reach other machines — so a role
	// is printed only where this frame has authority. Everywhere else the station caption is
	// the whole of what can honestly be said, and the column stays empty.
	if (!Frame || !StationPawn || !Frame->HasAuthority()) { return FText::GetEmpty(); }
	const AController* Seated = StationPawn->GetController();
	if (!Seated) { return FText::GetEmpty(); }
	if (Seated == Frame->CurrentDriver) { return NSLOCTEXT("IBMech", "Driver", "DRIVER"); }
	if (Seated == Frame->CurrentGunner) { return NSLOCTEXT("IBMech", "Gunner", "GUNNER"); }
	return NSLOCTEXT("IBMech", "Seated", "SEATED");
}

void UIBMechScreen::Refresh()
{
	const AIBMech_Base* Frame = FindFrame();
	if (UWidgetSwitcher* Pages = FrameBody ? Cast<UWidgetSwitcher>(FrameBody->GetParent()) : nullptr)
	{
		Pages->SetActiveWidget(Frame ? FrameBody.Get() : EmptyBody.Get());
	}
	if (FrameStatus)
	{
		const bool bCrewing = IBMechSheet::IsCrewedBy(Frame, GetOwningPlayerState());
		FrameStatus->SetText(!Frame ? NSLOCTEXT("IBMech", "StatusNone", "NO FRAME ON STATION")
			: bCrewing ? NSLOCTEXT("IBMech", "StatusCrewing", "CREWING  /  LIVE READOUT") : NSLOCTEXT("IBMech", "StatusStation", "FRAME ON STATION  /  LIVE READOUT"));
	}

	// Deployment record for the map we stand in — the same registry the Watch reads.
	const FIBDestination* Here = IBWatch::Find(IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this, true)));
	if (DeployLocation) { DeployLocation->SetText(Here ? Here->Name.ToUpper() : NSLOCTEXT("IBMech", "NoRecord", "NO DESTINATION RECORD")); }
	if (DeployAuthorization)
	{
		DeployAuthorization->SetText(Here && !Here->MechDeployment.IsEmpty() ? Here->MechDeployment.ToUpper() : NSLOCTEXT("IBMech", "NoAuth", "NO MECH AUTHORIZATION LISTED FOR THIS LOCATION"));
		DeployAuthorization->SetColorAndOpacity(Here && !Here->MechDeployment.IsEmpty() ? IBStyle::TextHi() : IBStyle::TextLo());
	}
	if (DeployFireteam)
	{
		DeployFireteam->SetText(Here ? (Here->Fireteam.IsEmpty()
			? FText::FromString(FString::Printf(TEXT("FIRETEAM  %d–%d OPERATORS"), Here->SquadMin, Here->SquadMax))
			: FText::Format(NSLOCTEXT("IBMech", "Fireteam", "FIRETEAM  {0}"), Here->Fireteam.ToUpper())) : FText::GetEmpty());
	}

	if (!Frame) { return; }

	if (FrameName) { FrameName->SetText(IBMechSheet::ChassisName(Frame)); }
	if (HullValue)
	{
		HullValue->SetText(FText::Format(NSLOCTEXT("IBMech", "Hull", "{0} / {1}"), FText::AsNumber(FMath::RoundToInt(Frame->CurrentHealth)), FText::AsNumber(FMath::RoundToInt(Frame->MaxHealth))));
		const float Ratio = Frame->MaxHealth > 0.f ? FMath::Clamp(Frame->CurrentHealth / Frame->MaxHealth, 0.f, 1.f) : 0.f;
		HullValue->SetColorAndOpacity(Ratio < 0.3f ? IBStyle::Danger() : Ratio < 0.6f ? IBStyle::Amber() : IBStyle::TextHi());
		if (HullBar) { HullBar->SetPercent(Ratio); HullBar->SetFillColorAndOpacity(Ratio < 0.3f ? IBStyle::Danger() : Ratio < 0.6f ? IBStyle::Amber() : IBHangar::Cyan()); }
	}
	if (ConcordState)
	{
		// AreWeaponsSafetyLocked() is false both when the link is healthy and when there is no
		// link to speak of, so it cannot carry this line on its own. Say which it is.
		const UConcordComponent* Link = Frame->Concord;
		if (!Link)
		{
			ConcordState->SetText(NSLOCTEXT("IBMech", "ConcordNone", "NO CONCORD LINK FITTED ON THIS FRAME"));
			ConcordState->SetColorAndOpacity(IBStyle::TextLo());
		}
		else if (!Link->IsTuned())
		{
			ConcordState->SetText(NSLOCTEXT("IBMech", "ConcordUntuned", "CONCORD UNCONFIGURED  /  NO SYNC PROFILE, NO SAFETY LOCK"));
			ConcordState->SetColorAndOpacity(IBStyle::TextLo());
		}
		else if (Frame->AreWeaponsSafetyLocked())
		{
			ConcordState->SetText(NSLOCTEXT("IBMech", "ConcordLocked", "DESYNC  /  HEAVY WEAPONS HELD BY THE SAFETY LOCK"));
			ConcordState->SetColorAndOpacity(IBStyle::Amber());
		}
		else if (Link->IsDesynced())
		{
			ConcordState->SetText(NSLOCTEXT("IBMech", "ConcordDesync", "DESYNC  /  HEAVY WEAPONS STILL CLEAR"));
			ConcordState->SetColorAndOpacity(IBStyle::Amber());
		}
		else
		{
			ConcordState->SetText(NSLOCTEXT("IBMech", "ConcordClear", "LINKED  /  HEAVY WEAPONS CLEAR"));
			ConcordState->SetColorAndOpacity(IBHangar::Cyan());
		}
	}

	const UWeaponVisualData* Arm = Frame->CurrentVisualData;
	UTexture2D* Icon = Arm ? Arm->Icon.LoadSynchronous() : nullptr;
	if (WeaponName) { WeaponName->SetText(Arm && !Arm->DisplayName.IsEmpty() ? Arm->DisplayName : NSLOCTEXT("IBMech", "NoArm", "NO ARM WEAPON FITTED")); WeaponName->SetColorAndOpacity(Arm ? UIBUISettings::Get()->GetRarityColor(Arm->Rarity) : IBStyle::TextLo()); }
	if (WeaponMeta) { WeaponMeta->SetText(Arm ? FText::Format(NSLOCTEXT("IBMech", "ArmMeta", "{0}  /  ARM-MOUNTED"), UEnum::GetDisplayValueAsText(Arm->Rarity).ToUpper()) : FText::GetEmpty()); }
	if (WeaponIcon)
	{
		if (Icon) { WeaponIcon->SetBrushFromTexture(Icon); }
		WeaponIcon->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (WeaponGlyph)
	{
		WeaponGlyph->SetGlyph(EIBItemCategory::Weapon, EIBEquipSlot::WeaponHeavy);
		WeaponGlyph->SetTint(Arm ? UIBUISettings::Get()->GetRarityColor(Arm->Rarity) : IBHangar::Fade(IBStyle::TextLo(), .45f));
		WeaponGlyph->SetVisibility(Icon ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (AmmoValue) { AmmoValue->SetText(FText::Format(NSLOCTEXT("IBMech", "Ammo", "{0} / {1}"), FText::AsNumber(Frame->CurrentAmmo), FText::AsNumber(Frame->MaxAmmo))); }
	if (AmmoBar) { AmmoBar->SetPercent(Frame->MaxAmmo > 0 ? FMath::Clamp(static_cast<float>(Frame->CurrentAmmo) / static_cast<float>(Frame->MaxAmmo), 0.f, 1.f) : 0.f); }
	if (CooldownValue)
	{
		CooldownValue->SetText(Frame->WeaponCooldownRemaining > 0.05f
			? FText::Format(NSLOCTEXT("IBMech", "Recovering", "RECOVERY  {0} s"), FText::AsNumber(FMath::RoundToInt(Frame->WeaponCooldownRemaining)))
			: NSLOCTEXT("IBMech", "Ready", "READY TO FIRE"));
	}
	// Stations, read the way every machine can read them: the hull pawn is the left station,
	// the gunner-seat pawn the right one.
	const APawn* HullStation = Frame;
	const APawn* SeatStation = Frame->GunnerSeat;
	if (HullOccupantName)
	{
		HullOccupantName->SetText(StationOccupant(HullStation, Frame->HullOccupancy));
		HullOccupantName->SetColorAndOpacity(Frame->HullOccupancy == EIBMechStationOccupancy::Vacant ? IBStyle::TextLo() : IBStyle::TextHi());
	}
	if (HullOccupantRole) { HullOccupantRole->SetText(StationRole(Frame, HullStation)); }
	if (SeatOccupantName)
	{
		SeatOccupantName->SetText(StationOccupant(SeatStation, Frame->SeatOccupancy));
		SeatOccupantName->SetColorAndOpacity(Frame->SeatOccupancy == EIBMechStationOccupancy::Vacant ? IBStyle::TextLo() : IBStyle::TextHi());
	}
	if (SeatOccupantRole) { SeatOccupantRole->SetText(StationRole(Frame, SeatStation)); }
}
