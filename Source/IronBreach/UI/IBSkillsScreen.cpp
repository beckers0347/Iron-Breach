#include "UI/IBSkillsScreen.h"
#include "UI/IBSkillConstellation.h"
#include "UI/IBHangarStyle.h"
#include "Skills/IBSkillComponent.h"
#include "Items/IBPlayerState.h"
#include "Player/IBOperativePreviewStage.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Components/Image.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/PlayerController.h"

UIBSkillComponent* UIBSkillsScreen::Skills() const
{
    const AIBPlayerState* PS=GetOwningPlayer() ? GetOwningPlayer()->GetPlayerState<AIBPlayerState>() : nullptr;
    return PS ? PS->Skills : nullptr;
}
void UIBSkillsScreen::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    UVerticalBox* Body=BuildHangarPage(NSLOCTEXT("IBSkills","Controls","HOVER / INSPECT     ARROWS / NAVIGATE     Q E / SWITCH MENU     K OR ESC / RETURN"));
    UHorizontalBox* Heading=WidgetTree->ConstructWidget<UHorizontalBox>();
    ClassTitle=IBHangar::Label(WidgetTree,TEXT("SKILLS"),34);
    Heading->AddChildToHorizontalBox(ClassTitle)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Points=IBHangar::Label(WidgetTree,TEXT(""),22,IBHangar::Cyan()); Heading->AddChildToHorizontalBox(Points);
    Body->AddChildToVerticalBox(Heading)->SetPadding(FMargin(0,8,0,20));
    UHorizontalBox* Strip=WidgetTree->ConstructWidget<UHorizontalBox>();
    const TCHAR* Keys[]={TEXT("V"),TEXT("Q"),TEXT("Z"),TEXT("X")};
    for (int32 I=0; I<4; ++I)
    {
        UVerticalBox* Chip=WidgetTree->ConstructWidget<UVerticalBox>();
        Chip->AddChildToVerticalBox(IBHangar::Label(WidgetTree,FString::Printf(TEXT("[%s]  %s"),Keys[I],*IBSkills::SlotName(static_cast<EIBSkillSlot>(I)).ToString()),11,IBHangar::Cyan()));
        UTextBlock* Name=IBHangar::Label(WidgetTree,TEXT(""),16); Name->SetAutoWrapText(true);
        Chip->AddChildToVerticalBox(Name)->SetPadding(FMargin(0,8,0,0)); StripNames.Add(Name);
        UButton* Button=WidgetTree->ConstructWidget<UButton>(); Button->SetContent(Chip); IBHangar::StyleButton(Button);
        StripButtons.Add(Button);
        UHorizontalBoxSlot* SkillSlot=Strip->AddChildToHorizontalBox(Button); SkillSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); SkillSlot->SetPadding(FMargin(0,0,I==3 ? 0 : 12,0));
    }
    StripButtons[0]->OnClicked.AddDynamic(this,&UIBSkillsScreen::PickSignature);
    StripButtons[1]->OnClicked.AddDynamic(this,&UIBSkillsScreen::PickTacticalOne);
    StripButtons[2]->OnClicked.AddDynamic(this,&UIBSkillsScreen::PickTacticalTwo);
    StripButtons[3]->OnClicked.AddDynamic(this,&UIBSkillsScreen::PickOverdrive);
    Body->AddChildToVerticalBox(Strip)->SetPadding(FMargin(0,0,0,18));

    UHorizontalBox* Columns=WidgetTree->ConstructWidget<UHorizontalBox>();
    Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UVerticalBox* Left=WidgetTree->ConstructWidget<UVerticalBox>();
    UOverlay* Field=WidgetTree->ConstructWidget<UOverlay>();
    UBorder* FieldShade=WidgetTree->ConstructWidget<UBorder>(); FieldShade->SetBrushColor(FLinearColor(.003f,.015f,.023f,.6f)); FieldShade->SetVisibility(ESlateVisibility::HitTestInvisible);
    UOverlaySlot* ShadeSlot=Field->AddChildToOverlay(FieldShade); ShadeSlot->SetHorizontalAlignment(HAlign_Fill); ShadeSlot->SetVerticalAlignment(VAlign_Fill);
    Portrait=WidgetTree->ConstructWidget<UImage>(); Portrait->SetVisibility(ESlateVisibility::HitTestInvisible);
    Portrait->SetColorAndOpacity(FLinearColor(.12f,.8f,1.f,.36f));
    USizeBox* PortraitSize=IBMenuLayout::Width(WidgetTree,Portrait,560); PortraitSize->SetHeightOverride(560);
    UScaleBox* PortraitFit=WidgetTree->ConstructWidget<UScaleBox>(); PortraitFit->SetStretch(EStretch::ScaleToFit); PortraitFit->SetContent(PortraitSize); PortraitFit->SetVisibility(ESlateVisibility::HitTestInvisible);
    UOverlaySlot* PortraitSlot=Field->AddChildToOverlay(PortraitFit); PortraitSlot->SetHorizontalAlignment(HAlign_Fill); PortraitSlot->SetVerticalAlignment(VAlign_Fill);
    Constellation=CreateWidget<UIBSkillConstellation>(GetOwningPlayer());
    UOverlaySlot* CanvasSlot=Field->AddChildToOverlay(Constellation); CanvasSlot->SetHorizontalAlignment(HAlign_Fill); CanvasSlot->SetVerticalAlignment(VAlign_Fill);
    Constellation->OnPicked.AddUObject(this,&UIBSkillsScreen::SelectNode);
    Left->AddChildToVerticalBox(Field)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Left->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("SOLID / UNLOCKED     DIAMOND / EQUIPPED     DASHED / LOCKED"),10,IBStyle::TextLo()))->SetPadding(FMargin(0,14,0,8));
    UHorizontalBoxSlot* LeftSlot=Columns->AddChildToHorizontalBox(Left); LeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); LeftSlot->SetPadding(FMargin(0,0,24,0));

    UVerticalBox* Details=WidgetTree->ConstructWidget<UVerticalBox>();
    DetailKind=IBHangar::Label(WidgetTree,TEXT(""),11,IBHangar::Cyan()); Details->AddChildToVerticalBox(DetailKind);
    DetailName=IBHangar::Label(WidgetTree,TEXT(""),27); DetailName->SetAutoWrapText(true); Details->AddChildToVerticalBox(DetailName)->SetPadding(FMargin(0,12,0,0));
    IBHangar::Rule(WidgetTree,Details);
    UVerticalBox* Scroll=WidgetTree->ConstructWidget<UVerticalBox>();
    DetailDescription=IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),14,IBStyle::TextHi(),0); DetailDescription->SetAutoWrapText(true); Scroll->AddChildToVerticalBox(DetailDescription);
    DetailStats=IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo(),0); DetailStats->SetAutoWrapText(true); Scroll->AddChildToVerticalBox(DetailStats)->SetPadding(FMargin(0,18,0,0));
    IBMenuLayout::Scroll(WidgetTree,Details,Scroll);
    DetailState=IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBHangar::Cyan(),0); DetailState->SetAutoWrapText(true); Details->AddChildToVerticalBox(DetailState)->SetPadding(FMargin(0,12,0,12));
    UTextBlock* UnlockText=nullptr; UnlockButton=IBHangar::Button(WidgetTree,TEXT("UNLOCK"),&UnlockText); UnlockLabel=UnlockText; UnlockButton->OnClicked.AddDynamic(this,&UIBSkillsScreen::Unlock); Details->AddChildToVerticalBox(UnlockButton);
    const TCHAR* EquipNames[]={TEXT("EQUIP SIGNATURE  [V]"),TEXT("EQUIP TACTICAL 1  [Q]"),TEXT("EQUIP TACTICAL 2  [Z]"),TEXT("EQUIP OVERDRIVE  [X]")};
    for (const TCHAR* Label:EquipNames) { UButton* B=IBHangar::Button(WidgetTree,Label); Details->AddChildToVerticalBox(B)->SetPadding(FMargin(0,6,0,0)); EquipButtons.Add(B); }
    EquipButtons[0]->OnClicked.AddDynamic(this,&UIBSkillsScreen::EquipSignature);
    EquipButtons[1]->OnClicked.AddDynamic(this,&UIBSkillsScreen::EquipTacticalOne);
    EquipButtons[2]->OnClicked.AddDynamic(this,&UIBSkillsScreen::EquipTacticalTwo);
    EquipButtons[3]->OnClicked.AddDynamic(this,&UIBSkillsScreen::EquipOverdrive);
    Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Details),370));

    UHorizontalBox* Bottom=WidgetTree->ConstructWidget<UHorizontalBox>();
    Status=IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBSkills","Intro","One signature. Two tacticals. One overdrive. Choose one variant per ability."),12,IBStyle::TextLo(),0); Status->SetAutoWrapText(true);
    Bottom->AddChildToHorizontalBox(Status)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UTextBlock* RefundText=nullptr; RefundButton=IBHangar::Button(WidgetTree,TEXT("REFUND SKILLS"),&RefundText); RefundLabel=RefundText; RefundButton->OnClicked.AddDynamic(this,&UIBSkillsScreen::Refund);
    Bottom->AddChildToHorizontalBox(RefundButton)->SetPadding(FMargin(20,0,0,0));
    Body->AddChildToVerticalBox(Bottom)->SetPadding(FMargin(0,18,0,0));
}
void UIBSkillsScreen::SelectNode(FName Id)
{
    if (const FIBSkillNode* N=IBSkills::Find(Id); N && N->Class==Constellation->Class)
    { Selected=Id; Constellation->Selected=Id; Refresh(); }
}
void UIBSkillsScreen::SelectEquipped(int32 SkillSlot)
{ if (UIBSkillComponent* C=Skills(); C && C->GetState().Equipped.IsValidIndex(SkillSlot)) { SelectNode(C->GetState().Equipped[SkillSlot]); } }
void UIBSkillsScreen::Refresh()
{
    UIBSkillComponent* C=Skills();
    const AIBPlayerState* PS=GetOwningPlayer() ? GetOwningPlayer()->GetPlayerState<AIBPlayerState>() : nullptr;
    if (!C || !PS || !C->IsReady()) { Points->SetText(NSLOCTEXT("IBSkills","Loading","SYNCING SKILLS")); UnlockButton->SetIsEnabled(false); RefundButton->SetIsEnabled(false); for (UButton* B:EquipButtons) { B->SetIsEnabled(false); } return; }
    Constellation->Class=PS->GetOperativeClass(); Constellation->State=C->GetState();
    const FIBSkillNode* N=IBSkills::Find(Selected);
    if (!N || N->Class!=PS->GetOperativeClass()) { Selected=C->GetState().Equipped[0]; N=IBSkills::Find(Selected); }
    if (!N) { return; } Constellation->Selected=Selected;
    ClassTitle->SetText(FText::Format(NSLOCTEXT("IBSkills","ClassTitle","{0} / SKILLS"),IBCharacter::ClassName(PS->GetOperativeClass())));
    Points->SetText(FText::Format(NSLOCTEXT("IBSkills","PointCount","{0} POINTS AVAILABLE"),C->PointsAvailable()));
    for (int32 I=0; I<4; ++I)
    {
        const FIBSkillNode* Equipped=IBSkills::Find(C->GetState().Equipped[I]);
        StripNames[I]->SetText(Equipped ? Equipped->Name : NSLOCTEXT("IBSkills","EmptyDrive","NO OVERDRIVE EQUIPPED"));
        IBHangar::StyleButton(StripButtons[I],Equipped && Equipped->Id==Selected);
    }
    const bool Owned=IBSkills::IsUnlocked(C->GetState(),Selected), Equipped=C->GetState().Equipped.Contains(Selected);
    DetailName->SetText(N->Name); DetailDescription->SetText(N->Description);
    const FString Kind=N->Kind==EIBSkillKind::Signature ? TEXT("SIGNATURE") : N->Kind==EIBSkillKind::Tactical ? TEXT("TACTICAL") : TEXT("OVERDRIVE");
    DetailKind->SetText(FText::FromString(Kind+(N->Parent.IsNone() ? TEXT(" / ABILITY") : TEXT(" / VARIANT"))));
    FString Stats=FString::Printf(TEXT("RECOVERY   %.0f s"),N->Spec.Cooldown);
    if (!N->Parent.IsNone()) { Stats+=TEXT("\nPARENT   ")+IBSkills::Find(N->Parent)->Name.ToString(); }
    if (N->Spec.Duration>.3f) { Stats+=FString::Printf(TEXT("\nDURATION   %.1f s"),N->Spec.Duration); }
    if (N->Spec.Damage>0) { Stats+=FString::Printf(TEXT("\nDAMAGE   %.0f"),N->Spec.Damage); }
    if (N->Spec.bUsesGuardEnergy) { Stats+=TEXT(" + up to 100 stored energy"); }
    if (N->Spec.Effect==EIBKitEffect::Grapple || N->Spec.bPlaceAtAim) { Stats+=FString::Printf(TEXT("\nREACH   %.0f m"),N->Spec.Range/100); }
    if (N->Spec.Effect==EIBKitEffect::DeployZone || N->Spec.Effect==EIBKitEffect::RadialStrike) { Stats+=FString::Printf(TEXT("\nRADIUS   %.1f m"),N->Spec.Radius/100); }
    if (N->Spec.DamageTakenScale<1) { Stats+=FString::Printf(TEXT("\nDAMAGE REDUCTION   %.0f%%"),(1-N->Spec.DamageTakenScale)*100); }
    if (N->Spec.SlowFactor<1) { Stats+=FString::Printf(TEXT("\nHOSTILE SLOW   %.0f%%"),(1-N->Spec.SlowFactor)*100); }
    Stats+=FString::Printf(TEXT("\n\nUNLOCK   LEVEL %d / %d POINTS"),N->Level,N->Cost);
    DetailStats->SetText(FText::FromString(Stats));
    FIBSkillState Trial=C->GetState(); FText Error;
    const bool CanUnlock=IBSkills::Unlock(Trial,PS->GetOperativeClass(),PS->GetOperativeLevel(),Selected,Error);
    DetailState->SetText(Equipped ? NSLOCTEXT("IBSkills","StateEquipped","EQUIPPED") : Owned ? NSLOCTEXT("IBSkills","StateOwned","UNLOCKED / READY TO EQUIP") : CanUnlock ? NSLOCTEXT("IBSkills","Available","AVAILABLE TO UNLOCK") : Error);
    UnlockButton->SetVisibility(Owned ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    UnlockButton->SetIsEnabled(CanUnlock); UnlockLabel->SetText(FText::FromString(FString::Printf(TEXT("UNLOCK / %d POINTS"),N->Cost)));
    for (int32 I=0; I<4; ++I)
    {
        const bool Compatible=IBSkills::CanEquip(*N,static_cast<EIBSkillSlot>(I));
        EquipButtons[I]->SetVisibility(Owned && Compatible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        Trial=C->GetState(); EquipButtons[I]->SetIsEnabled(IBSkills::Equip(Trial,PS->GetOperativeClass(),Selected,static_cast<EIBSkillSlot>(I),Error));
    }
    RefundButton->SetIsEnabled(C->CanRefund());
    RefundLabel->SetText(FText::FromString(!C->CanRefund() ? TEXT("REFUND AT THE BASTION") : bRefundArmed ? TEXT("CONFIRM FREE REFUND") : TEXT("REFUND SKILLS / FREE")));
    if (!C->GetStatus().IsEmpty()) { Status->SetText(C->GetStatus()); }
}
void UIBSkillsScreen::Unlock() { if (UIBSkillComponent* C=Skills()) { C->RequestUnlock(Selected); Refresh(); } }
void UIBSkillsScreen::Equip(EIBSkillSlot SkillSlot) { if (UIBSkillComponent* C=Skills()) { C->RequestEquip(Selected,SkillSlot); Refresh(); } }
void UIBSkillsScreen::Refund()
{
    if (!bRefundArmed) { bRefundArmed=true; Refresh(); return; }
    bRefundArmed=false; if (UIBSkillComponent* C=Skills()) { C->RequestRefund(); Refresh(); }
}
void UIBSkillsScreen::NativeScreenOpened()
{
    bOpen=true; bRefundArmed=false; Refresh();
    const AIBPlayerState* PS=GetOwningPlayer()->GetPlayerState<AIBPlayerState>();
    Stage=AIBOperativePreviewStage::Spawn(GetWorld()); if (!Stage) { return; }
    Stage->SetActorLocation(FVector(195000,195000,-60000));
    Stage->ShowOperative(PS ? PS->GetOperativeGender() : EIBOperativeGender::Male,IBStyle::Cyan());
    const AIBCharacter_Infantry* Pawn=Cast<AIBCharacter_Infantry>(GetOwningPlayer()->GetPawn()); Stage->ConfigureForInventory(Pawn ? Pawn->GetMesh() : nullptr);
    if (UMaterialInterface* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/IronBreach/UI/Hangar/M_OperativePortrait.M_OperativePortrait")))
    {
        PortraitMaterial=UMaterialInstanceDynamic::Create(Base,this); PortraitMaterial->SetTextureParameterValue(TEXT("Portrait"),Stage->GetRenderTarget());
        FSlateBrush Brush; Brush.SetResourceObject(PortraitMaterial); Brush.ImageSize=FVector2D(1024,1024); Portrait->SetBrush(Brush);
    }
}
void UIBSkillsScreen::ReleasePortrait()
{
    if (Portrait) { Portrait->SetBrush(FSlateBrush()); }
    if (IsValid(Stage)) { Stage->Destroy(); } Stage=nullptr; PortraitMaterial=nullptr;
}
void UIBSkillsScreen::NativeScreenClosed() { bOpen=false; bRefundArmed=false; ReleasePortrait(); }
void UIBSkillsScreen::NativeDestruct() { ReleasePortrait(); Super::NativeDestruct(); }
void UIBSkillsScreen::NativeTick(const FGeometry& Geo,float Delta)
{
    Super::NativeTick(Geo,Delta); RefreshClock+=Delta;
    if (bOpen && RefreshClock>=.25f) { RefreshClock=0; Refresh(); }
}
FReply UIBSkillsScreen::NativeOnKeyDown(const FGeometry& Geo,const FKeyEvent& Event)
{
    const FKey K=Event.GetKey(); FVector2D Direction;
    if (K==EKeys::Left || K==EKeys::Gamepad_DPad_Left) { Direction=FVector2D(-1,0); }
    else if (K==EKeys::Right || K==EKeys::Gamepad_DPad_Right) { Direction=FVector2D(1,0); }
    else if (K==EKeys::Up || K==EKeys::Gamepad_DPad_Up) { Direction=FVector2D(0,-1); }
    else if (K==EKeys::Down || K==EKeys::Gamepad_DPad_Down) { Direction=FVector2D(0,1); }
    else { return Super::NativeOnKeyDown(Geo,Event); }
    Constellation->Navigate(Direction); return FReply::Handled();
}
