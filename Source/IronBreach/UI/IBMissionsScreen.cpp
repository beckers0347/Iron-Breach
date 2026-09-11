#include "UI/IBMissionsScreen.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBMenuActionButton.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBWatchScreen.h"
#include "Online/IBWatchTypes.h"
#include "Missions/IBMissionDirector.h"
#include "Components/Image.h"
#include "Components/ScrollBox.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

void UIBMissionsScreen::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    UVerticalBox* Body = BuildHangarPage(NSLOCTEXT("IBMissions","Controls","CLICK  SELECT BRIEFING     VIEW ON WATCH  OPEN DESTINATION     Q E  SWITCH MENU     ESC  RETURN"));
    Body->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree,NSLOCTEXT("IBMissions","Title","MISSIONS"),36))->SetPadding(FMargin(0,0,0,20));
    UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
    Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UVerticalBox* Left = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* FilterRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    const TCHAR* Names[] = {TEXT("ALL"),TEXT("OPERATIONS"),TEXT("PATROLS"),TEXT("TRAINING")};
    for (int32 Index=0; Index<4; ++Index)
    {
        UIBMenuActionButton* Button = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        Button->SetContent(IBHangar::Label(WidgetTree,Names[Index],11)); IBHangar::StyleButton(Button);
        Button->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Index] { FilterIndex=Index; RebuildList(); }));
        FilterRow->AddChildToHorizontalBox(Button)->SetPadding(FMargin(0,0,5,0)); Filters.Add(Button);
    }
    Left->AddChildToVerticalBox(FilterRow)->SetPadding(FMargin(0,0,0,20));
    MissionList = WidgetTree->ConstructWidget<UVerticalBox>();
    IBMenuLayout::Scroll(WidgetTree,Left,MissionList);
    Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Left,FMargin(20)),540))->SetPadding(FMargin(0,0,20,0));

    UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
    MissionType = IBHangar::Label(WidgetTree,TEXT(""),12,IBHangar::Cyan()); Details->AddChildToVerticalBox(MissionType);
    MissionName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),32); MissionName->SetAutoWrapText(true);
    Details->AddChildToVerticalBox(MissionName)->SetPadding(FMargin(0,8,0,0));
    IBHangar::Rule(WidgetTree,Details);
    UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* Top = WidgetTree->ConstructWidget<UHorizontalBox>();
    Brief = IBHangar::Label(WidgetTree,TEXT(""),17); Brief->SetAutoWrapText(true);
    auto* BriefSlot = Top->AddChildToHorizontalBox(Brief); BriefSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); BriefSlot->SetPadding(FMargin(0,0,24,0));
    Recon = WidgetTree->ConstructWidget<UImage>();
    USizeBox* StillSize = IBMenuLayout::Width(WidgetTree,Recon,340); StillSize->SetHeightOverride(190);
    Top->AddChildToHorizontalBox(IBHangar::Panel(WidgetTree,StillSize,FMargin(2)));
    Content->AddChildToVerticalBox(Top);
    Content->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("OBJECTIVE"),13,IBHangar::Cyan()))->SetPadding(FMargin(0,26,0,12));
    Objective = IBHangar::Label(WidgetTree,TEXT(""),18); Objective->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(IBHangar::Panel(WidgetTree,Objective,FMargin(18)));
    Content->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("DEPLOYMENT INTEL"),13,IBHangar::Cyan()))->SetPadding(FMargin(0,26,0,14));
    Intel = IBHangar::Label(WidgetTree,TEXT(""),15); Intel->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(Intel);
    IBMenuLayout::Scroll(WidgetTree,Details,Content);
    IBHangar::Rule(WidgetTree,Details,12);
    UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>();
    Status = IBHangar::Label(WidgetTree,TEXT(""),12,IBHangar::Cyan()); Status->SetAutoWrapText(true);
    auto* StatusSlot = Footer->AddChildToHorizontalBox(Status); StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); StatusSlot->SetVerticalAlignment(VAlign_Center);
    WatchButton = IBHangar::Button(WidgetTree,TEXT("VIEW ON WATCH  >")); IBHangar::StyleButton(WatchButton,true);
    WatchButton->OnClicked.AddDynamic(this,&UIBMissionsScreen::ViewOnWatch);
    Footer->AddChildToHorizontalBox(WatchButton)->SetPadding(FMargin(20,0,0,0)); Details->AddChildToVerticalBox(Footer);
    Columns->AddChildToHorizontalBox(IBHangar::Panel(WidgetTree,Details,FMargin(28)))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
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
    for (int32 Index=0; Index<Filters.Num(); ++Index) { IBHangar::StyleButton(Filters[Index],Index==FilterIndex); }
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
    for (const FIBDestination* D : Entries)
    {
        UIBMenuActionButton* Row = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        IBHangar::StyleButton(Row,D->Id==SelectedId);
        FButtonStyle RowStyle = Row->GetStyle(); RowStyle.SetNormalPadding(FMargin(12)); RowStyle.SetPressedPadding(FMargin(12)); Row->SetStyle(RowStyle);
        const FName Id = D->Id; Row->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Id] { SelectDestination(Id); }));
        UHorizontalBox* Content = WidgetTree->ConstructWidget<UHorizontalBox>();
        UImage* Thumb = WidgetTree->ConstructWidget<UImage>();
        UTexture2D* Texture = D->ReconStill.LoadSynchronous();
        Thumb->SetBrushFromTexture(Texture); Thumb->SetColorAndOpacity(Texture ? FLinearColor::White : FLinearColor(.05f,.16f,.20f));
        USizeBox* ThumbSize = IBMenuLayout::Width(WidgetTree,Thumb,112); ThumbSize->SetHeightOverride(80);
        Content->AddChildToHorizontalBox(ThumbSize)->SetPadding(FMargin(0,0,16,0));
        UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>();
        UTextBlock* Name = IBMenuLayout::Heading(WidgetTree,D->ShortName,22); Name->SetAutoWrapText(true);
        Copy->AddChildToVerticalBox(Name);
        Copy->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,D->Codename,11,IBHangar::Cyan()))->SetPadding(FMargin(0,6,0,8));
        const FName Current = IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true));
        Copy->AddChildToVerticalBox(IBHangar::Label(WidgetTree,D->Id==Current ? TEXT("CURRENT LOCATION") : (D->CanDeploy() ? TEXT("AVAILABLE") : TEXT("DEPLOYMENT LOCKED")),11));
        Content->AddChildToHorizontalBox(Copy)->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); Row->SetContent(Content);
        if (!D->CanDeploy()) { Row->SetRenderOpacity(.5f); }
        MissionList->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,0,0,12));
    }
    if (Entries.IsEmpty()) { MissionList->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("NO BRIEFINGS IN THIS CATEGORY"),13)); }
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
    MissionType->SetText(D ? D->Codename : FText::GetEmpty()); Brief->SetText(D ? D->Brief : FText::GetEmpty());
    Recon->SetBrushFromTexture(D ? D->ReconStill.LoadSynchronous() : nullptr);
    Recon->SetVisibility(D && !D->ReconStill.IsNull() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
    Intel->SetText(D ? FText::Format(NSLOCTEXT("IBMissions","Intel","THREAT     {0}\n\nFIRETEAM     {1}\n\nMECH DEPLOYMENT     {2}"),D->ThreatClass,D->Fireteam,D->MechDeployment) : FText::GetEmpty());
    Status->SetText(D ? (D->CanDeploy() ? NSLOCTEXT("IBMissions","Ready","DEPLOYMENT AVAILABLE\nSelect and confirm on the Watch") : NSLOCTEXT("IBMissions","Locked","DEPLOYMENT LOCKED\nRecon briefing only")) : FText::GetEmpty());
    RefreshObjective();
}

void UIBMissionsScreen::RefreshObjective()
{
    const FIBDestination* D=IBWatch::Find(SelectedId);
    FText Text=D ? D->MissionType : FText::GetEmpty();
    if (D && D->Id==IBWatch::DestinationForMap(UGameplayStatics::GetCurrentLevelName(this,true)))
    {
        // Actor iteration also works on clients, where the server-spawned director replicates.
        for (TActorIterator<AIBMissionDirector> It(GetWorld()); It; ++It) { Text=It->GetObjectiveText(); break; }
    }
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
