#include "UI/IBMissionsScreen.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBMenuActionButton.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBWatchScreen.h"
#include "UI/IBPaintKit.h"
#include "Online/IBWatchTypes.h"
#include "Missions/IBMissionDirector.h"
#include "Components/Image.h"
#include "Components/ButtonSlot.h"
#include "Components/BorderSlot.h"
#include "Widgets/Layout/SBorder.h"
#include "Components/ScrollBox.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

namespace IBMissionsPresentation
{
    class SImageShade final : public SBorder
    {
    public:
        virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
            FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const override
        {
            const FVector2f Size(Geo.GetLocalSize());
            const FLinearColor Tint = Style.GetColorAndOpacityTint();
            IBPaint::Gradient(Out, LayerId, Geo, FVector2f::ZeroVector, Size,
                FLinearColor(.003f,.012f,.020f,.98f)*Tint, FLinearColor(.003f,.012f,.020f,.10f)*Tint, false);
            return SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId+1, Style, bParentEnabled);
        }
    };

    void Fill(UOverlaySlot* OverlaySlot)
    {
        OverlaySlot->SetHorizontalAlignment(HAlign_Fill);
        OverlaySlot->SetVerticalAlignment(VAlign_Fill);
    }

    /** Recon rows: hairline at rest, lit cyan frame when selected; the still fills the button. */
    void StyleRow(UButton* Row, bool bSelected)
    {
        if (!Row) { return; }
        FButtonStyle Style = Row->GetStyle();
        Style.Normal  = IBStyle::RoundedBrush(FLinearColor::Transparent, 0.f, bSelected ? IBHangar::Cyan() : IBHangar::Edge(), bSelected ? 1.5f : 1.f);
        Style.Hovered = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.08f), 0.f, IBHangar::Cyan(), 1.5f);
        Style.Pressed = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.16f), 0.f, IBHangar::Cyan(), 1.5f);
        Style.SetNormalPadding(FMargin(2)); Style.SetPressedPadding(FMargin(2));
        Row->SetStyle(Style);
    }
}

TSharedRef<SWidget> UIBMissionImageShade::RebuildWidget()
{
    MyBorder = SNew(IBMissionsPresentation::SImageShade);
    if (GetChildrenCount() > 0) { CastChecked<UBorderSlot>(GetContentSlot())->BuildSlot(MyBorder.ToSharedRef()); }
    return MyBorder.ToSharedRef();
}

void UIBMissionsScreen::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    UVerticalBox* Body = BuildHangarPage(NSLOCTEXT("IBMissions","Controls","CLICK  SELECT BRIEFING     VIEW ON WATCH  OPEN DESTINATION     Q E  SWITCH MENU     ESC  RETURN"));
    UHorizontalBox* PageTitle = WidgetTree->ConstructWidget<UHorizontalBox>();
    UVerticalBox* TitleCopy = WidgetTree->ConstructWidget<UVerticalBox>();
    TitleCopy->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree,NSLOCTEXT("IBMissions","Title","MISSIONS"),30));
    TitleCopy->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("ORDERS TODAY. A STRONGER TOMORROW."),11,IBStyle::TextLo()))->SetPadding(FMargin(0,4,0,0));
    PageTitle->AddChildToHorizontalBox(TitleCopy)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    MissionCount = IBHangar::Label(WidgetTree,TEXT(""),11,IBHangar::Cyan());
    PageTitle->AddChildToHorizontalBox(MissionCount)->SetVerticalAlignment(VAlign_Bottom);
    Body->AddChildToVerticalBox(PageTitle)->SetPadding(FMargin(0,0,0,18));
    UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
    Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    UVerticalBox* Left = WidgetTree->ConstructWidget<UVerticalBox>();
    // ACTIVE: the one objective that is real right now — the mission director of the current
    // map, replicated to every machine. Nothing here is a quest log entry we invented.
    UIBMenuActionButton* Active = WidgetTree->ConstructWidget<UIBMenuActionButton>();
    UHorizontalBox* ActiveRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBoxSlot* ActiveMarkSlot = ActiveRow->AddChildToHorizontalBox(IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Target,IBHangar::Cyan(),26.f));
    ActiveMarkSlot->SetPadding(FMargin(4,0,14,0)); ActiveMarkSlot->SetVerticalAlignment(VAlign_Center);
    UVerticalBox* ActiveCopy = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* ActiveHead = WidgetTree->ConstructWidget<UHorizontalBox>();
    ActiveHead->AddChildToHorizontalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBMissions","ActiveKicker","ACTIVE OPERATION"),9,IBHangar::Cyan(),200))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ActiveLocation = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),9,IBStyle::TextLo(),120);
    ActiveHead->AddChildToHorizontalBox(ActiveLocation);
    ActiveCopy->AddChildToVerticalBox(ActiveHead);
    ActiveObjective = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),14,IBStyle::TextHi()); ActiveObjective->SetAutoWrapText(true);
    ActiveCopy->AddChildToVerticalBox(ActiveObjective)->SetPadding(FMargin(0,5,0,0));
    UHorizontalBoxSlot* ActiveCopySlot = ActiveRow->AddChildToHorizontalBox(ActiveCopy); ActiveCopySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); ActiveCopySlot->SetVerticalAlignment(VAlign_Center);
    Active->SetContent(IBHangar::Glass(WidgetTree,ActiveRow,FMargin(12,10),FIBGlassStyle::Inset(),IBHangar::Lit()));
    CastChecked<UButtonSlot>(Active->GetContent()->Slot)->SetHorizontalAlignment(HAlign_Fill);
    FButtonStyle ActiveStyle = Active->GetStyle();
    ActiveStyle.Normal = IBStyle::RoundedBrush(FLinearColor::Transparent,0); ActiveStyle.Hovered = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.10f),0); ActiveStyle.Pressed = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.18f),0);
    ActiveStyle.SetNormalPadding(FMargin(0)); ActiveStyle.SetPressedPadding(FMargin(0)); Active->SetStyle(ActiveStyle);
    Active->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this]
    {
        const FName Current = IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true));
        // Same eligibility rule the briefing list and the auto-selection use: the Bastion is
        // where you stand between operations, not a briefing you can select.
        const FIBDestination* Target = IBWatch::Find(Current);
        if (Target && Target->Kind != EIBDestinationKind::Bastion) { FilterIndex = 0; SelectDestination(Current); }
    }));
    ActiveStrip = Active;
    Left->AddChildToVerticalBox(Active)->SetPadding(FMargin(0,0,0,12));
    Active->SetVisibility(ESlateVisibility::Collapsed);
    UHorizontalBox* FilterRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    const TCHAR* Names[] = {TEXT("ALL"),TEXT("OPERATIONS"),TEXT("PATROLS"),TEXT("TRAINING")};
    for (int32 Index=0; Index<4; ++Index)
    {
        UIBMenuActionButton* Button = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        Button->SetContent(IBMenuLayout::Text(WidgetTree,FText::FromString(Names[Index]),11,IBStyle::TextLo(),100)); IBHangar::StyleTab(Button);
        Button->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Index] { FilterIndex=Index; RebuildList(); }));
        UHorizontalBoxSlot* FilterSlot = FilterRow->AddChildToHorizontalBox(Button);
        FilterSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); FilterSlot->SetPadding(FMargin(0,0,2,0));
        Filters.Add(Button);
    }
    Left->AddChildToVerticalBox(FilterRow)->SetPadding(FMargin(0,0,0,12));
    MissionList = WidgetTree->ConstructWidget<UVerticalBox>();
    IBMenuLayout::Scroll(WidgetTree,Left,MissionList);
    Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Left,FMargin(10)),490))->SetPadding(FMargin(0,0,20,0));

    UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* Dossier = WidgetTree->ConstructWidget<UHorizontalBox>();
    Details->AddChildToVerticalBox(Dossier)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UVerticalBox* BriefingColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    MissionType = IBHangar::Label(WidgetTree,TEXT(""),12,IBHangar::Cyan());
    BriefingColumn->AddChildToVerticalBox(MissionType);
    MissionName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),28); MissionName->SetAutoWrapText(true);
    BriefingColumn->AddChildToVerticalBox(MissionName)->SetPadding(FMargin(0,6,0,16));
    UVerticalBox* Briefing = WidgetTree->ConstructWidget<UVerticalBox>();
    Brief = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),15,IBStyle::TextLo()); Brief->SetAutoWrapText(true); Brief->SetLineHeightPercentage(1.25f);
    Briefing->AddChildToVerticalBox(Brief);
    Briefing->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("OBJECTIVES"),15,IBHangar::Cyan()))->SetPadding(FMargin(0,28,0,0));
    IBHangar::Rule(WidgetTree,Briefing,14);
    UHorizontalBox* ObjectiveRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBoxSlot* ObjectiveMarkSlot = ObjectiveRow->AddChildToHorizontalBox(IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Target,IBHangar::Cyan(),26.f));
    ObjectiveMarkSlot->SetPadding(FMargin(0,0,14,0)); ObjectiveMarkSlot->SetVerticalAlignment(VAlign_Top);
    UVerticalBox* ObjectiveCopy = WidgetTree->ConstructWidget<UVerticalBox>();
    ObjectiveSource = IBHangar::Label(WidgetTree,TEXT("MISSION BRIEFING"),10,IBHangar::Cyan());
    ObjectiveCopy->AddChildToVerticalBox(ObjectiveSource)->SetPadding(FMargin(0,0,0,7));
    Objective = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),17,IBStyle::TextHi()); Objective->SetAutoWrapText(true); Objective->SetLineHeightPercentage(1.2f);
    ObjectiveCopy->AddChildToVerticalBox(Objective);
    ObjectiveRow->AddChildToHorizontalBox(ObjectiveCopy)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Briefing->AddChildToVerticalBox(ObjectiveRow);
    IBMenuLayout::Scroll(WidgetTree,BriefingColumn,Briefing);
    UHorizontalBoxSlot* BriefingSlot = Dossier->AddChildToHorizontalBox(BriefingColumn);
    BriefingSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); BriefingSlot->SetPadding(FMargin(0,0,26,0));

    UVerticalBox* IntelColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    UOverlay* ReconFrame = WidgetTree->ConstructWidget<UOverlay>();
    ReconFrame->SetClipping(EWidgetClipping::ClipToBounds);
    UBorder* ReconBase = IBStyle::MakePanel(WidgetTree,FLinearColor(.018f,.043f,.056f),0);
    IBMissionsPresentation::Fill(ReconFrame->AddChildToOverlay(ReconBase));
    Recon = WidgetTree->ConstructWidget<UImage>(); Recon->SetVisibility(ESlateVisibility::HitTestInvisible);
    UScaleBox* ReconFit = WidgetTree->ConstructWidget<UScaleBox>(); ReconFit->SetStretch(EStretch::ScaleToFill); ReconFit->SetContent(Recon);
    IBMissionsPresentation::Fill(ReconFrame->AddChildToOverlay(ReconFit));
    ReconFallback = IBHangar::Label(WidgetTree,TEXT("RECON IMAGE UNAVAILABLE"),11,IBStyle::TextLo());
    UOverlaySlot* FallbackSlot = ReconFrame->AddChildToOverlay(ReconFallback); FallbackSlot->SetHorizontalAlignment(HAlign_Center); FallbackSlot->SetVerticalAlignment(VAlign_Center);
    ReconCaption = IBHangar::Label(WidgetTree,TEXT(""),13,IBStyle::TextHi()); ReconCaption->SetAutoWrapText(true);
    UBorder* ReconCaptionShade = IBStyle::MakePanel(WidgetTree,FLinearColor(.002f,.009f,.015f,.86f),0); ReconCaptionShade->SetPadding(FMargin(14,12)); ReconCaptionShade->SetContent(ReconCaption);
    UOverlaySlot* CaptionSlot = ReconFrame->AddChildToOverlay(ReconCaptionShade); CaptionSlot->SetHorizontalAlignment(HAlign_Fill); CaptionSlot->SetVerticalAlignment(VAlign_Bottom);
    USizeBox* StillSize = IBMenuLayout::Width(WidgetTree,ReconFrame,416); StillSize->SetHeightOverride(244);
    IntelColumn->AddChildToVerticalBox(IBHangar::Inset(WidgetTree,StillSize,FMargin(1)));
    IntelColumn->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("DEPLOYMENT INTEL"),15,IBHangar::Cyan()))->SetPadding(FMargin(0,24,0,0));
    IBHangar::Rule(WidgetTree,IntelColumn,14);
    Intel = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),15,IBStyle::TextLo()); Intel->SetAutoWrapText(true); Intel->SetLineHeightPercentage(1.4f);
    IBMenuLayout::Scroll(WidgetTree,IntelColumn,Intel);
    UHorizontalBoxSlot* IntelSlot = Dossier->AddChildToHorizontalBox(IntelColumn); IntelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    IBHangar::Rule(WidgetTree,Details,14);
    UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>();
    Status = IBHangar::Label(WidgetTree,TEXT(""),11,IBHangar::Cyan()); Status->SetAutoWrapText(true);
    UHorizontalBoxSlot* StatusSlot = Footer->AddChildToHorizontalBox(Status); StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); StatusSlot->SetVerticalAlignment(VAlign_Center);
    WatchButton = IBHangar::Button(WidgetTree,TEXT("VIEW ON WATCH  >")); IBHangar::StyleButton(WatchButton,true);
    WatchButton->OnClicked.AddDynamic(this,&UIBMissionsScreen::ViewOnWatch);
    Footer->AddChildToHorizontalBox(WatchButton)->SetPadding(FMargin(20,0,0,0)); Details->AddChildToVerticalBox(Footer);
    Columns->AddChildToHorizontalBox(IBHangar::Dossier(WidgetTree,Details,FMargin(26,24,26,22)))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
}
void UIBMissionsScreen::NativeScreenOpened()
{
    if (SelectedId.IsNone())
    {
        const FName Current = IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true));
        if (const FIBDestination* Destination = IBWatch::Find(Current); Destination && Destination->Kind != EIBDestinationKind::Bastion) { SelectedId = Current; }
    }
    RebuildList();
}

void UIBMissionsScreen::RebuildList()
{
    MissionList->ClearChildren();
    for (int32 Index=0; Index<Filters.Num(); ++Index)
    {
        IBHangar::StyleTab(Filters[Index],Index==FilterIndex);
        if (UTextBlock* FilterLabel = Cast<UTextBlock>(Filters[Index]->GetContent())) { FilterLabel->SetColorAndOpacity(Index==FilterIndex ? IBStyle::TextHi() : IBStyle::TextLo()); }
    }
    TArray<const FIBDestination*> Entries;
    for (const FIBDestination& D : IBWatch::Destinations())
    {
        if (D.Kind==EIBDestinationKind::Bastion) { continue; }
        if (FilterIndex==1 && D.Kind!=EIBDestinationKind::Operation) { continue; }
        if (FilterIndex==2 && D.Kind!=EIBDestinationKind::Sector) { continue; }
        if (FilterIndex==3 && D.Kind!=EIBDestinationKind::Range) { continue; }
        Entries.Add(&D);
    }
    if (!Entries.ContainsByPredicate([this](const FIBDestination* D) { return D->Id==SelectedId; })) { SelectedId=Entries.IsEmpty() ? NAME_None : Entries[0]->Id; }
    const FName Current = IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true));
    if (MissionCount) { MissionCount->SetText(FText::Format(NSLOCTEXT("IBMissions","Count","{0} BRIEFINGS  /  BREAKWATER COMMAND"),FText::AsNumber(Entries.Num()))); }
    for (const FIBDestination* D : Entries)
    {
        UIBMenuActionButton* Row = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        IBMissionsPresentation::StyleRow(Row,D->Id==SelectedId);
        const FName Id = D->Id; Row->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Id] { SelectDestination(Id); }));
        UOverlay* Art = WidgetTree->ConstructWidget<UOverlay>(); Art->SetClipping(EWidgetClipping::ClipToBounds);
        UImage* Thumb = WidgetTree->ConstructWidget<UImage>();
        UTexture2D* Texture = D->ReconStill.LoadSynchronous();
        Thumb->SetBrushFromTexture(Texture); Thumb->SetColorAndOpacity(Texture ? FLinearColor(.75f,.85f,.92f) : FLinearColor(.05f,.16f,.20f));
        Thumb->SetVisibility(ESlateVisibility::HitTestInvisible);
        UScaleBox* ArtFit = WidgetTree->ConstructWidget<UScaleBox>(); ArtFit->SetStretch(EStretch::ScaleToFill); ArtFit->SetContent(Thumb);
        IBMissionsPresentation::Fill(Art->AddChildToOverlay(ArtFit));
        UIBMissionImageShade* Shade = WidgetTree->ConstructWidget<UIBMissionImageShade>(); Shade->SetVisibility(ESlateVisibility::HitTestInvisible);
        IBMissionsPresentation::Fill(Art->AddChildToOverlay(Shade));
        UHorizontalBox* Content = WidgetTree->ConstructWidget<UHorizontalBox>();
        const FLinearColor KindColor = IBWatch::KindColor(D->Kind);
        UIBMenuGlyph* Mark = IBHangar::Glyph(WidgetTree,D->CanDeploy() ? EIBMenuGlyph::Diamond : EIBMenuGlyph::Lock,KindColor,34.f);
        UHorizontalBoxSlot* MarkSlot = Content->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Mark,42)); MarkSlot->SetPadding(FMargin(0,0,14,0)); MarkSlot->SetVerticalAlignment(VAlign_Center);
        UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>();
        Copy->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,IBWatch::KindLabel(D->Kind).ToUpper(),10,KindColor));
        UTextBlock* Name = IBMenuLayout::Heading(WidgetTree,D->ShortName.IsEmpty() ? D->Name : D->ShortName,19);
        Name->SetWrapTextAt(338); Name->SetAutoWrapText(false);
        Copy->AddChildToVerticalBox(Name)->SetPadding(FMargin(0,3,0,5));
        Copy->AddChildToVerticalBox(IBHangar::Label(WidgetTree,D->Id==Current ? TEXT("CURRENT LOCATION") : (D->CanDeploy() ? D->Codename.ToString() : TEXT("DEPLOYMENT LOCKED")),10,IBStyle::TextLo()));
        UHorizontalBoxSlot* CopySlot = Content->AddChildToHorizontalBox(Copy); CopySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); CopySlot->SetVerticalAlignment(VAlign_Center);
        UOverlaySlot* CopyOverlay = Art->AddChildToOverlay(Content); IBMissionsPresentation::Fill(CopyOverlay); CopyOverlay->SetPadding(FMargin(14,10));
        USizeBox* RowSize = WidgetTree->ConstructWidget<USizeBox>(); RowSize->SetHeightOverride(98); RowSize->SetContent(Art);
        Row->SetContent(RowSize); CastChecked<UButtonSlot>(RowSize->Slot)->SetHorizontalAlignment(HAlign_Fill);
        if (!D->CanDeploy()) { Row->SetRenderOpacity(.62f); }
        MissionList->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,0,0,9));
    }    if (Entries.IsEmpty()) { MissionList->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("NO BRIEFINGS IN THIS CATEGORY"),13)); }
    RefreshDetails();
}

void UIBMissionsScreen::SelectDestination(FName Id)
{
    if (!IBWatch::Find(Id)) { return; }
    SelectedId=Id; RebuildList();
}

void UIBMissionsScreen::RefreshDetails()
{
    const FIBDestination* D=IBWatch::Find(SelectedId);
    WatchButton->SetIsEnabled(D!=nullptr);
    MissionName->SetText(D ? D->Name : NSLOCTEXT("IBMissions","NoSelection","NO MISSION SELECTED"));
    MissionType->SetText(D ? IBWatch::KindLabel(D->Kind).ToUpper() : FText::GetEmpty()); Brief->SetText(D ? D->Brief : FText::GetEmpty());
    UTexture2D* Texture = D ? D->ReconStill.LoadSynchronous() : nullptr;
    Recon->SetBrushFromTexture(Texture);
    Recon->SetVisibility(Texture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
    ReconFallback->SetVisibility(Texture ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    ReconCaption->SetText(D ? FText::Format(NSLOCTEXT("IBMissions","ReconCaption","{0}\n{1}"),D->Name,D->Codename) : FText::GetEmpty());
    Intel->SetText(D ? FText::Format(NSLOCTEXT("IBMissions","IntelDossier","THREAT CLASS\n{0}\n\nFIRETEAM\n{1}\n\nMECH DEPLOYMENT\n{2}"),D->ThreatClass,D->Fireteam,D->MechDeployment) : FText::GetEmpty());
    Status->SetText(D ? (D->CanDeploy() ? NSLOCTEXT("IBMissions","Ready","DEPLOYMENT AVAILABLE\nSelect and confirm on the Watch") : NSLOCTEXT("IBMissions","Locked","DEPLOYMENT LOCKED\nRecon briefing only")) : FText::GetEmpty());
    RefreshObjective();
}

void UIBMissionsScreen::RefreshObjective()
{
    const FName CurrentMap = IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true));
    // Actor iteration also works on clients, where the server-spawned director replicates.
    const AIBMissionDirector* Director = nullptr;
    for (TActorIterator<AIBMissionDirector> It(GetWorld()); It; ++It) { Director = *It; break; }

    // The ACTIVE strip: live objective of the map we stand in, or nothing at all.
    if (ActiveStrip)
    {
        const FIBDestination* Here = IBWatch::Find(CurrentMap);
        // Excludes the Bastion for the same reason RebuildList and NativeScreenOpened do: the
        // Watch is not an operation, so it must never advertise itself as the active one.
        const bool bLive = Director != nullptr && Here != nullptr && Here->Kind != EIBDestinationKind::Bastion;
        ActiveStrip->SetVisibility(bLive ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (bLive)
        {
            const FText Live = Director->GetObjectiveText();
            if (ActiveObjective && !Live.EqualTo(LastActiveObjective)) { ActiveObjective->SetText(Live); LastActiveObjective = Live; }
            if (ActiveLocation) { ActiveLocation->SetText((Here->ShortName.IsEmpty() ? Here->Name : Here->ShortName).ToUpper()); }
        }
    }

    const FIBDestination* D=IBWatch::Find(SelectedId);
    FText Text=D ? D->MissionType : FText::GetEmpty();
    bool bLiveObjective = false;
    if (D && Director && D->Id==CurrentMap) { Text=Director->GetObjectiveText(); bLiveObjective=true; }
    if (ObjectiveSource) { ObjectiveSource->SetText(bLiveObjective ? NSLOCTEXT("IBMissions","LiveObjective","LIVE FIELD OBJECTIVE") : NSLOCTEXT("IBMissions","BriefingObjective","MISSION BRIEFING")); }
    if (!Objective->GetText().EqualTo(Text)) { Objective->SetText(Text); }
}

void UIBMissionsScreen::NativeTick(const FGeometry& Geometry,float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime); RefreshElapsed+=DeltaTime;
    if (RefreshElapsed>=.5f) { RefreshElapsed=0; RefreshObjective(); }
}

void UIBMissionsScreen::ViewOnWatch()
{
    UIBMenuSubsystem* Menu=GetMenuSubsystem();
    const FName Destination=SelectedId;
    if (!Menu || !IBWatch::Find(Destination)) { return; }
    Menu->OpenScreen(TEXT("Watch"));
    if (UIBWatchScreen* Watch=Cast<UIBWatchScreen>(Menu->GetActiveScreen())) { Watch->FocusDestination(Destination); }
}
