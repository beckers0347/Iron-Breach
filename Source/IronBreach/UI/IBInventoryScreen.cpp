#include "UI/IBInventoryScreen.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "UI/IBItemTileWidget.h"
#include "UI/IBUISettings.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBMenuActionButton.h"
#include "Components/EditableTextBox.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/WidgetSwitcher.h"
#include "Components/Image.h"
#include "Player/IBOperativePreviewStage.h"
#include "Player/IBCharacterTypes.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Blueprint/WidgetTree.h"
#include "GameFramework/PlayerController.h"

UIBInventoryComponent* UIBInventoryScreen::GetInventory() const
{
	const APlayerController* PC = GetOwningPlayer();
	const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	return PS ? PS->GetInventory() : nullptr;
}

void UIBInventoryScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Never let the class run tile-less, whatever the WBP forgot.
	if (!GridTileClass) { GridTileClass = UIBItemTileWidget::StaticClass(); }

	// Bare WBP: build the Destiny layout in code.
	if (!ItemGrid && !Tile_WeaponPrimary)
	{
		BuildFallbackLayout();
	}
}

UIBItemTileWidget* UIBInventoryScreen::MakeWell(UVerticalBox* Column, EIBEquipSlot ForSlot)
{
	UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(GetOwningPlayer(), *GridTileClass);
	if (!Tile) { return nullptr; }
	UTextBlock* SlotName = IBMenuLayout::Text(WidgetTree,
		UEnum::GetDisplayValueAsText(ForSlot).ToUpper(), 9, FLinearColor(.49f,.63f,.69f), 140);
	SlotName->SetJustification(ETextJustify::Center);
	Column->AddChildToVerticalBox(SlotName)->SetPadding(FMargin(0, 0, 0, 4));
	WellLabels.Add(ForSlot, SlotName);
	Tile->SetEmptySlot(ForSlot);
	Tile->SetPresentationSize(FVector2D(140, 108));
	UVerticalBoxSlot* WellSlot = Column->AddChildToVerticalBox(Tile);
	WellSlot->SetHorizontalAlignment(HAlign_Center);
	WellSlot->SetPadding(FMargin(0, 0, 0, 14));
	return Tile;
}

void UIBInventoryScreen::BuildFallbackLayout()
{
    UVerticalBox* Body = BuildHangarPage(NSLOCTEXT("IBInv", "HangarControls", "LEFT / RIGHT  CHARACTER & INVENTORY     CLICK  SELECT ITEM     EQUIP  APPLY SELECTION     Q E  SWITCH MENU     ESC  RETURN"));
    InventoryPages = WidgetTree->ConstructWidget<UWidgetSwitcher>();
    Body->AddChildToVerticalBox(InventoryPages)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    // ---------------------------------------------------------------- CHARACTER
    // The live operative stands on the whole sheet; weapons hang left, armor
    // right, the loadout plinth sits at the feet. Nothing here is a framed card.
    UOverlay* Character = WidgetTree->ConstructWidget<UOverlay>();
    InventoryPages->AddChild(Character);
    CharacterImage = WidgetTree->ConstructWidget<UImage>();
    CharacterImage->SetVisibility(ESlateVisibility::HitTestInvisible);
    USizeBox* PortraitSize = IBMenuLayout::Width(WidgetTree,CharacterImage,1024); PortraitSize->SetHeightOverride(1024);
    UScaleBox* Fit = WidgetTree->ConstructWidget<UScaleBox>(); Fit->SetStretch(EStretch::ScaleToFit); Fit->SetContent(PortraitSize);
    Fit->SetRenderTransformPivot(FVector2D(.5f,1.f)); Fit->SetRenderScale(FVector2D(1.1f,1.1f));
    UOverlaySlot* PortraitSlot = Character->AddChildToOverlay(Fit);
    PortraitSlot->SetHorizontalAlignment(HAlign_Fill); PortraitSlot->SetVerticalAlignment(VAlign_Fill);
    PortraitSlot->SetPadding(FMargin(0,0,0,66));
    UHorizontalBox* Equipment = WidgetTree->ConstructWidget<UHorizontalBox>();
    UOverlaySlot* EquipmentSlot = Character->AddChildToOverlay(IBMenuLayout::Width(WidgetTree,Equipment,940));
    EquipmentSlot->SetHorizontalAlignment(HAlign_Center); EquipmentSlot->SetVerticalAlignment(VAlign_Center);
    EquipmentSlot->SetPadding(FMargin(0,0,0,70));
    UVerticalBox* Weapons = WidgetTree->ConstructWidget<UVerticalBox>();
    Tile_WeaponPrimary = MakeWell(Weapons, EIBEquipSlot::WeaponPrimary);
    Tile_WeaponSpecial = MakeWell(Weapons, EIBEquipSlot::WeaponSpecial);
    Tile_WeaponHeavy = MakeWell(Weapons, EIBEquipSlot::WeaponHeavy);
    Tile_GearAntiKaiju = MakeWell(Weapons, EIBEquipSlot::GearAntiKaiju);
    Equipment->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Weapons,150))->SetVerticalAlignment(VAlign_Center);
    Equipment->AddChildToHorizontalBox(WidgetTree->ConstructWidget<USpacer>())->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    UVerticalBox* Armor = WidgetTree->ConstructWidget<UVerticalBox>();
    Tile_ArmorHead = MakeWell(Armor,EIBEquipSlot::ArmorHead);
    Tile_ArmorChest = MakeWell(Armor,EIBEquipSlot::ArmorChest);
    Tile_ArmorArms = MakeWell(Armor,EIBEquipSlot::ArmorArms);
    Tile_ArmorLegs = MakeWell(Armor,EIBEquipSlot::ArmorLegs);
    Equipment->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Armor,150))->SetVerticalAlignment(VAlign_Center);
    for (UVerticalBox* Column : { Weapons, Armor })
        for (UWidget* Child : Column->GetAllChildren())
            CastChecked<UVerticalBoxSlot>(Child->Slot)->SetHorizontalAlignment(HAlign_Center);

    UVerticalBox* Core = WidgetTree->ConstructWidget<UVerticalBox>();
    UTextBlock* CoreTitle = IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBInv","CoreTitle","OPERATIVE LOADOUT"),10,IBHangar::Cyan(),200);
    CoreTitle->SetJustification(ETextJustify::Center); Core->AddChildToVerticalBox(CoreTitle)->SetPadding(FMargin(0,0,0,8));
    UHorizontalBox* CoreRow = WidgetTree->ConstructWidget<UHorizontalBox>(); Core->AddChildToVerticalBox(CoreRow);
    auto CoreStat = [this,CoreRow](const TCHAR* Label, EIBItemCategory GlyphCategory, bool bDivider)
    {
        UHorizontalBox* Pair = WidgetTree->ConstructWidget<UHorizontalBox>();
        UIBItemGlyphWidget* Glyph = CreateWidget<UIBItemGlyphWidget>(this); Glyph->SetGlyph(GlyphCategory); Glyph->SetTint(IBHangar::Cyan());
        USizeBox* GlyphSize = IBMenuLayout::Width(WidgetTree,Glyph,28); GlyphSize->SetHeightOverride(28);
        UHorizontalBoxSlot* GlyphSlot = Pair->AddChildToHorizontalBox(GlyphSize); GlyphSlot->SetPadding(FMargin(0,0,14,0)); GlyphSlot->SetVerticalAlignment(VAlign_Center);
        UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>();
        Copy->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,FText::FromString(Label),9,IBStyle::TextLo(),140));
        UTextBlock* Value = IBMenuLayout::Heading(WidgetTree,FText::FromString(TEXT("—")),22);
        Copy->AddChildToVerticalBox(Value)->SetPadding(FMargin(0,2,0,0)); Pair->AddChildToHorizontalBox(Copy)->SetVerticalAlignment(VAlign_Center);
        UHorizontalBoxSlot* Column = CoreRow->AddChildToHorizontalBox(Pair); Column->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); Column->SetHorizontalAlignment(HAlign_Center);
        if (bDivider)
        {
            UBorder* Divider = IBStyle::MakeAccentBar(WidgetTree,IBHangar::Edge()); Divider->SetPadding(FMargin(.5f,0));
            UHorizontalBoxSlot* DividerSlot = CoreRow->AddChildToHorizontalBox(Divider); DividerSlot->SetPadding(FMargin(0,4)); DividerSlot->SetVerticalAlignment(VAlign_Fill);
        }
        return Value;
    };
    CharacterStats = CoreStat(TEXT("CLEARANCE"),EIBItemCategory::Splice,true);
    CharacterEquipmentValue = CoreStat(TEXT("EQUIPPED"),EIBItemCategory::Armor,true);
    CharacterBackpackValue = CoreStat(TEXT("IN BACKPACK"),EIBItemCategory::None,false);
    UOverlaySlot* CoreSlot = Character->AddChildToOverlay(IBMenuLayout::Width(WidgetTree,IBHangar::Plinth(WidgetTree,Core,FMargin(52,10,52,14)),900));
    CoreSlot->SetHorizontalAlignment(HAlign_Center); CoreSlot->SetVerticalAlignment(VAlign_Bottom);

    UVerticalBox* GearDetails = WidgetTree->ConstructWidget<UVerticalBox>();
    CharacterDetailName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),20); CharacterDetailName->SetAutoWrapText(true);
    CharacterDetailInfo = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo()); CharacterDetailInfo->SetAutoWrapText(true); CharacterDetailInfo->SetLineHeightPercentage(1.25f);
    GearDetails->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("EQUIPPED GEAR"),10,IBHangar::Cyan()));
    GearDetails->AddChildToVerticalBox(CharacterDetailName)->SetPadding(FMargin(0,6,0,0)); IBHangar::Rule(WidgetTree,GearDetails,12);
    IBMenuLayout::Scroll(WidgetTree,GearDetails,CharacterDetailInfo);
    CharacterDetailPanel = IBMenuLayout::Width(WidgetTree,IBHangar::Dossier(WidgetTree,GearDetails,FMargin(20)),320);
    CharacterDetailPanel->SetHeightOverride(280);
    UOverlaySlot* Popup = Character->AddChildToOverlay(CharacterDetailPanel);
    Popup->SetHorizontalAlignment(HAlign_Left); Popup->SetVerticalAlignment(VAlign_Center); Popup->SetPadding(FMargin(0,0,0,70));
    CharacterDetailPanel->SetVisibility(ESlateVisibility::Collapsed);

    // ---------------------------------------------------------------- INVENTORY
    // Category rail | search / sort / grid | persistent inspector.
    UVerticalBox* BackpackPage = WidgetTree->ConstructWidget<UVerticalBox>(); InventoryPages->AddChild(BackpackPage);
    UHorizontalBox* PackColumns = WidgetTree->ConstructWidget<UHorizontalBox>();
    UVerticalBoxSlot* PackSlot = BackpackPage->AddChildToVerticalBox(PackColumns);
    PackSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); PackSlot->SetPadding(FMargin(0,16,0,6));
    UVerticalBox* Categories = WidgetTree->ConstructWidget<UVerticalBox>();
    Categories->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBInv","RailTitle","CATEGORIES"),9,IBStyle::TextLo(),200))->SetPadding(FMargin(14,2,0,12));
    FilterTabLabels.Reset(); FilterCategories.Reset(); FilterButtons.Reset(); FilterCounts.Reset(); FilterAccents.Reset();
    const TPair<EIBItemCategory,const TCHAR*> Filters[] = {
        {EIBItemCategory::None,TEXT("ALL ITEMS")}, {EIBItemCategory::Weapon,TEXT("WEAPONS")},
        {EIBItemCategory::Armor,TEXT("ARMOR")}, {EIBItemCategory::KaijuMaterial,TEXT("MATERIALS")},
        {EIBItemCategory::Consumable,TEXT("CONSUMABLES")}, {EIBItemCategory::Splice,TEXT("SPLICES")},
        {EIBItemCategory::Doctrine,TEXT("DOCTRINES")}, {EIBItemCategory::Collectible,TEXT("COLLECTIBLES")},
        {EIBItemCategory::Cosmetic,TEXT("COSMETICS")}};
    for (const auto& Entry : Filters)
    {
        UIBMenuActionButton* Filter = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree,FLinearColor::Transparent); Accent->SetPadding(FMargin(1.5f,0));
        UHorizontalBoxSlot* AccentSlot = Row->AddChildToHorizontalBox(Accent); AccentSlot->SetPadding(FMargin(0,0,10,0)); AccentSlot->SetVerticalAlignment(VAlign_Fill);
        UIBItemGlyphWidget* Glyph = CreateWidget<UIBItemGlyphWidget>(this); Glyph->SetGlyph(Entry.Key);
        USizeBox* GlyphSize = IBMenuLayout::Width(WidgetTree,Glyph,20); GlyphSize->SetHeightOverride(20);
        UHorizontalBoxSlot* GlyphSlot = Row->AddChildToHorizontalBox(GlyphSize); GlyphSlot->SetPadding(FMargin(0,0,10,0)); GlyphSlot->SetVerticalAlignment(VAlign_Center);
        UTextBlock* Label = IBMenuLayout::Text(WidgetTree,FText::FromString(Entry.Value),10,IBStyle::TextLo(),60);
        UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(Label); LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); LabelSlot->SetVerticalAlignment(VAlign_Center);
        UTextBlock* Count = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),10,IBStyle::TextLo());
        Row->AddChildToHorizontalBox(Count)->SetVerticalAlignment(VAlign_Center);
        Filter->SetContent(Row); IBHangar::StyleRail(Filter);
        const EIBItemCategory Category = Entry.Key;
        Filter->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Category] { if (Category == EIBItemCategory::None) { SetFilterAll(); } else { SetCategoryFilter(Category); } }));
        Categories->AddChildToVerticalBox(Filter)->SetPadding(FMargin(0,0,0,2));
        FilterTabLabels.Add(Label); FilterCategories.Add(Category); FilterButtons.Add(Filter); FilterCounts.Add(Count); FilterAccents.Add(Accent);
    }
    UHorizontalBoxSlot* CategorySlot = PackColumns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Categories,FMargin(6,12,6,10)),214));
    CategorySlot->SetPadding(FMargin(0,0,14,0)); CategorySlot->SetVerticalAlignment(VAlign_Top);

    UVerticalBox* Backpack = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* Tools = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBox* SearchRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBoxSlot* SearchMarkSlot = SearchRow->AddChildToHorizontalBox(IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Search,IBStyle::TextLo(),15.f));
    SearchMarkSlot->SetPadding(FMargin(12,0,0,0)); SearchMarkSlot->SetVerticalAlignment(VAlign_Center);
    UEditableTextBox* Search = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("InventorySearch"));
    Search->SetHintText(NSLOCTEXT("IBInv","Search","Search..."));
    FEditableTextBoxStyle SearchStyle = Search->GetWidgetStyle();
    SearchStyle.SetTextStyle(FTextBlockStyle(SearchStyle.TextStyle).SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),12)));
    SearchStyle.SetBackgroundImageNormal(IBStyle::RoundedBrush(FLinearColor::Transparent,0));
    SearchStyle.SetBackgroundImageHovered(SearchStyle.BackgroundImageNormal); SearchStyle.SetBackgroundImageFocused(SearchStyle.BackgroundImageNormal);
    SearchStyle.SetForegroundColor(IBStyle::TextHi()); SearchStyle.SetPadding(FMargin(10,8));
    Search->SetWidgetStyle(SearchStyle); Search->OnTextChanged.AddDynamic(this,&UIBInventoryScreen::HandleSearchChanged);
    SearchRow->AddChildToHorizontalBox(Search)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Tools->AddChildToHorizontalBox(IBHangar::Inset(WidgetTree,SearchRow,FMargin(0)))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UTextBlock* SortText = nullptr;
    UButton* Sort = IBHangar::Button(WidgetTree,TEXT("SORT: RARITY"),&SortText); SortLabel = SortText;
    SortText->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),11));
    FButtonStyle SortStyle = Sort->GetStyle(); SortStyle.NormalPadding = FMargin(14,8); SortStyle.PressedPadding = SortStyle.NormalPadding; Sort->SetStyle(SortStyle);
    Sort->OnClicked.AddDynamic(this,&UIBInventoryScreen::CycleSort);
    Tools->AddChildToHorizontalBox(Sort)->SetPadding(FMargin(12,0,0,0));
    Backpack->AddChildToVerticalBox(Tools)->SetPadding(FMargin(2,0,2,14));
    ItemGrid = WidgetTree->ConstructWidget<UUniformGridPanel>(); ItemGrid->SetSlotPadding(FMargin(3)); GridColumns = 6;
    IBMenuLayout::Scroll(WidgetTree,Backpack,ItemGrid);
    CastChecked<UScrollBoxSlot>(ItemGrid->Slot)->SetHorizontalAlignment(HAlign_Fill);
    IBHangar::Rule(WidgetTree,Backpack,0);
    UHorizontalBox* PackFooter = WidgetTree->ConstructWidget<UHorizontalBox>();
    PackStatus = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),11,IBStyle::TextHi(),80);
    PackFooter->AddChildToHorizontalBox(PackStatus)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    PackFooter->AddChildToHorizontalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBInv","PackFooter","FIELD LOOT  /  NO STORAGE LIMIT"),9,IBStyle::TextLo(),140))->SetVerticalAlignment(VAlign_Center);
    Backpack->AddChildToVerticalBox(PackFooter)->SetPadding(FMargin(4,12,4,0));
    UHorizontalBoxSlot* GridArea = PackColumns->AddChildToHorizontalBox(IBHangar::Panel(WidgetTree,Backpack,FMargin(16)));
    GridArea->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); GridArea->SetPadding(FMargin(0,0,14,0));

    UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailRarity = IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBInv","EquipmentInspection","EQUIPMENT INSPECTION"),11,IBHangar::Cyan(),140); Details->AddChildToVerticalBox(DetailRarity);
    Txt_DetailName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),24); Txt_DetailName->SetAutoWrapText(true);
    Details->AddChildToVerticalBox(Txt_DetailName)->SetPadding(FMargin(0,6,0,0));
    DetailCategory = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo(),40);
    Details->AddChildToVerticalBox(DetailCategory)->SetPadding(FMargin(0,3,0,0));
    UOverlay* Art = WidgetTree->ConstructWidget<UOverlay>();
    DetailIcon = WidgetTree->ConstructWidget<UImage>(); DetailIcon->SetVisibility(ESlateVisibility::Collapsed);
    UScaleBox* ArtFit = WidgetTree->ConstructWidget<UScaleBox>(); ArtFit->SetStretch(EStretch::ScaleToFit); ArtFit->SetContent(DetailIcon);
    UOverlaySlot* ArtSlot = Art->AddChildToOverlay(ArtFit); ArtSlot->SetHorizontalAlignment(HAlign_Fill); ArtSlot->SetVerticalAlignment(VAlign_Fill); ArtSlot->SetPadding(FMargin(10));
    DetailGlyph = CreateWidget<UIBItemGlyphWidget>(this);
    USizeBox* MissingArt = IBMenuLayout::Width(WidgetTree,DetailGlyph,96); MissingArt->SetHeightOverride(96);
    UOverlaySlot* MissingSlot = Art->AddChildToOverlay(MissingArt); MissingSlot->SetHorizontalAlignment(HAlign_Center); MissingSlot->SetVerticalAlignment(VAlign_Center);
    USizeBox* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetHeightOverride(196); IconSize->SetContent(IBHangar::Inset(WidgetTree,Art,FMargin(0)));
    Details->AddChildToVerticalBox(IconSize)->SetPadding(FMargin(0,14,0,14));
    UHorizontalBox* RatingRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    UVerticalBox* RatingCopy = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailRatingLabel = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),9,IBStyle::TextLo(),160);
    DetailRating = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),30);
    RatingCopy->AddChildToVerticalBox(DetailRatingLabel); RatingCopy->AddChildToVerticalBox(DetailRating);
    RatingRow->AddChildToHorizontalBox(RatingCopy)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Details->AddChildToVerticalBox(RatingRow);
    IBHangar::Rule(WidgetTree,Details,12);
    UVerticalBox* DetailContent = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailStats = WidgetTree->ConstructWidget<UVerticalBox>(); DetailContent->AddChildToVerticalBox(DetailStats);
    Txt_DetailInfo = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo(),10); Txt_DetailInfo->SetAutoWrapText(true); Txt_DetailInfo->SetLineHeightPercentage(1.3f);
    DetailContent->AddChildToVerticalBox(Txt_DetailInfo)->SetPadding(FMargin(0,4,0,0));
    IBMenuLayout::Scroll(WidgetTree,Details,DetailContent);
    UTextBlock* ActionText = nullptr; EquipButton = IBHangar::Button(WidgetTree,TEXT("EQUIP"),&ActionText); EquipLabel = ActionText;
    EquipButton->OnClicked.AddDynamic(this,&UIBInventoryScreen::EquipSelected);
    ActionText->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),11));
    IBHangar::StyleButton(EquipButton,true);
    Details->AddChildToVerticalBox(EquipButton)->SetPadding(FMargin(0,14,0,0));
    DetailFrame = IBHangar::Dossier(WidgetTree,Details,FMargin(22));
    DetailPanel = IBMenuLayout::Width(WidgetTree,DetailFrame,380);
    PackColumns->AddChildToHorizontalBox(DetailPanel);
    RefreshFilterTabs(); RefreshSubtabs(); SetDetails(nullptr);
}

void UIBInventoryScreen::ShowCharacterTab()
{
	bBackpackSelected = false;
	RefreshSubtabs();
}

void UIBInventoryScreen::ShowBackpackTab()
{
	bBackpackSelected = true;
	RefreshSubtabs();
}

void UIBInventoryScreen::RefreshSubtabs()
{
	if (!InventoryPages) { return; }
	InventoryPages->SetActiveWidgetIndex(bBackpackSelected ? 1 : 0);
	RefreshTabBanner();
	SetDetails(SelectedTile.Get());
	if (bScreenOpen && !bBackpackSelected) { RefreshCharacterPreview(); }
	else { ReleaseCharacterPreview(); }
}

void UIBInventoryScreen::RefreshCharacterPreview()
{
	if (!bScreenOpen || bBackpackSelected || !CharacterImage) { return; }
	const APlayerController* PC = GetOwningPlayer();
	const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	const FLinearColor Accent = PS && PS->HasOperative() ? IBCharacter::ClassColor(PS->GetOperativeClass()) : IBStyle::Cyan();
	if (CharacterName) { CharacterName->SetText(PS && PS->HasOperative() ? FText::FromString(PS->GetDisplayCallsign().ToUpper()) : NSLOCTEXT("IBInv", "Operative", "OPERATIVE")); }
	if (CharacterRole)
	{
		CharacterRole->SetText(PS && PS->HasOperative() ? FText::Format(NSLOCTEXT("IBInv", "ClassLevel", "{0} / LEVEL {1}"),
			IBCharacter::ClassName(PS->GetOperativeClass()), PS->GetOperativeLevel()) : NSLOCTEXT("IBInv", "FieldOperative", "FIELD OPERATIVE"));
		CharacterRole->SetColorAndOpacity(Accent);
	}
	if (!IsValid(PreviewStage))
	{
		PreviewStage = AIBOperativePreviewStage::Spawn(GetWorld());
		// Isolate this studio's lights from any open front-end portrait stage.
		if (PreviewStage) { PreviewStage->SetActorLocation(FVector(185000, 185000, -60000)); }
	}
	if (!PreviewStage) { return; }
	PreviewStage->ShowOperative(PS ? PS->GetOperativeGender() : EIBOperativeGender::Male, Accent);
	// The live pawn's body, materials and the weapon it is actually holding; no invented gear.
	const AIBCharacter_Infantry* Infantry = PC ? Cast<AIBCharacter_Infantry>(PC->GetPawn()) : nullptr;
	PreviewStage->ConfigureForInventory(Infantry ? Infantry->GetMesh() : nullptr, Infantry ? Infantry->GetThirdPersonWeaponMesh() : nullptr);
	FSlateBrush Brush = CharacterImage->GetBrush();
	if (!PortraitMaterial)
	{
		if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/IronBreach/UI/Hangar/M_OperativePortrait.M_OperativePortrait")))
			PortraitMaterial = UMaterialInstanceDynamic::Create(Base,this);
	}
	if (PortraitMaterial)
	{
		PortraitMaterial->SetTextureParameterValue(TEXT("Portrait"),PreviewStage->GetRenderTarget());
		Brush.SetResourceObject(PortraitMaterial);
	}
	else { Brush.SetResourceObject(PreviewStage->GetRenderTarget()); }
	Brush.ImageSize = FVector2D(1024, 1024);
	CharacterImage->SetBrush(Brush);
}

void UIBInventoryScreen::ReleaseCharacterPreview()
{
	if (CharacterImage)
	{
		FSlateBrush Brush = CharacterImage->GetBrush();
		Brush.SetResourceObject(nullptr);
		CharacterImage->SetBrush(Brush);
	}
	if (IsValid(PreviewStage)) { PreviewStage->Destroy(); }
	PreviewStage = nullptr;
	PortraitMaterial = nullptr;
}

FReply UIBInventoryScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InventoryPages)
	{
		if (InKeyEvent.GetKey() == EKeys::Left || InKeyEvent.GetKey() == EKeys::Gamepad_DPad_Left)
		{ ShowCharacterTab(); return FReply::Handled(); }
		if (InKeyEvent.GetKey() == EKeys::Right || InKeyEvent.GetKey() == EKeys::Gamepad_DPad_Right)
		{ ShowBackpackTab(); return FReply::Handled(); }
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UIBInventoryScreen::SetDetails(const UIBItemTileWidget* Tile)
{
    const UIBItemDefinition* Def = Tile ? Tile->GetDefinition() : nullptr;
    UTexture2D* Icon = Def ? Def->Icon.LoadSynchronous() : nullptr;
    const FLinearColor Rarity = Def ? UIBUISettings::Get()->GetRarityColor(Def->Rarity) : IBHangar::Cyan();
    if (DetailStats) { DetailStats->ClearChildren(); }
    if (DetailIcon)
    {
        if (Icon) { DetailIcon->SetBrushFromTexture(Icon); }
        DetailIcon->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    }
    if (DetailGlyph)
    {
        // Real art when the definition has it; otherwise the category pictogram in the rarity color.
        DetailGlyph->SetGlyph(Def ? Def->Category : EIBItemCategory::None, Def ? Def->EquipSlot : EIBEquipSlot::None);
        DetailGlyph->SetTint(Def ? Rarity : IBHangar::Fade(IBStyle::TextLo(), .45f));
        DetailGlyph->SetVisibility(Icon ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    }
    if (EquipButton)
    {
        FIBItemInstance Selected;
        const bool bCanEquip = BoundInventory && BoundInventory->FindItem(SelectedItemId,Selected) && Selected.IsValid() && Selected.Definition->EquipSlot != EIBEquipSlot::None;
        EquipButton->SetIsEnabled(bCanEquip);
        EquipLabel->SetText(bCanEquip ? NSLOCTEXT("IBInv","EquipSelection","EQUIP SELECTED ITEM") : NSLOCTEXT("IBInv","NoEquip","NOT EQUIPPABLE"));
    }
    if (!Def)
    {
        if (Txt_DetailName) { Txt_DetailName->SetText(NSLOCTEXT("IBInv","ChooseItem","SELECT AN ITEM")); Txt_DetailName->SetColorAndOpacity(IBStyle::TextHi()); }
        if (DetailCategory) { DetailCategory->SetText(FText::GetEmpty()); }
        if (Txt_DetailInfo) { Txt_DetailInfo->SetText(NSLOCTEXT("IBInv","SelectHint","Select equipment from your backpack to inspect its stats and equip it.\n\nLoot collected in the field appears here.")); }
        if (DetailRarity) { DetailRarity->SetText(NSLOCTEXT("IBInv","EquipmentInspection","EQUIPMENT INSPECTION")); DetailRarity->SetColorAndOpacity(IBHangar::Cyan()); }
        if (DetailRatingLabel) { DetailRatingLabel->SetText(FText::GetEmpty()); }
        if (DetailRating) { DetailRating->SetText(FText::GetEmpty()); }
        if (DetailFrame) { if (UIBGlassBorder* Glass = Cast<UIBGlassBorder>(DetailFrame)) { Glass->SetAccentColor(IBHangar::Cyan()); } }
        if (CharacterDetailPanel) { CharacterDetailPanel->SetVisibility(ESlateVisibility::Collapsed); }
        return;
    }
    const FIBItemInstance& Item = Tile->GetItem();
    if (DetailRarity) { DetailRarity->SetText(UEnum::GetDisplayValueAsText(Def->Rarity).ToUpper()); DetailRarity->SetColorAndOpacity(Rarity); }
    if (Txt_DetailName) { Txt_DetailName->SetText(Def->DisplayName); Txt_DetailName->SetColorAndOpacity(IBStyle::TextHi()); }
    if (DetailCategory)
    {
        DetailCategory->SetText(Def->EquipSlot != EIBEquipSlot::None
            ? FText::Format(NSLOCTEXT("IBInv","CategorySlot","{0}  ·  {1}"),UEnum::GetDisplayValueAsText(Def->Category),UEnum::GetDisplayValueAsText(Def->EquipSlot))
            : UEnum::GetDisplayValueAsText(Def->Category));
    }
    if (DetailFrame) { if (UIBGlassBorder* Glass = Cast<UIBGlassBorder>(DetailFrame)) { Glass->SetAccentColor(Rarity); } }
    if (DetailRatingLabel && DetailRating)
    {
        if (Def->EquipSlot != EIBEquipSlot::None)
        {
            DetailRatingLabel->SetText(NSLOCTEXT("IBInv","RatingLabel","CLEARANCE"));
            DetailRating->SetText(FText::AsNumber(Item.ClearanceRating));
        }
        else if (Item.StackCount > 1)
        {
            DetailRatingLabel->SetText(NSLOCTEXT("IBInv","QuantityLabel","QUANTITY"));
            DetailRating->SetText(FText::AsNumber(Item.StackCount));
        }
        else
        {
            DetailRatingLabel->SetText(FText::GetEmpty());
            DetailRating->SetText(FText::GetEmpty());
        }
    }
    FString Info = Def->Description.ToString();
    if (!Def->Flavor.IsEmpty()) { Info += TEXT("\n\n") + Def->Flavor.ToString(); }
    if (Txt_DetailInfo) { Txt_DetailInfo->SetText(FText::FromString(Info)); }
    if (DetailStats) { for (const FIBItemStat& Stat : Def->Stats) { IBHangar::Stat(WidgetTree,DetailStats,Stat.StatName,Stat.Value); } }
    if (CharacterDetailName) { CharacterDetailName->SetText(Def->DisplayName); CharacterDetailName->SetColorAndOpacity(Rarity); }
    if (CharacterDetailInfo)
    {
        FString Gear = FString::Printf(TEXT("%s  ·  %s\n"), *UEnum::GetDisplayValueAsText(Def->Rarity).ToString().ToUpper(), *UEnum::GetDisplayValueAsText(Def->Category).ToString().ToUpper());
        if (Def->EquipSlot != EIBEquipSlot::None) { Gear += FString::Printf(TEXT("CLEARANCE  %d\n"), Item.ClearanceRating); }
        CharacterDetailInfo->SetText(FText::FromString(Gear + TEXT("\n") + Info));
    }
    const bool bInspectingGear = Tile && GetWellForSlot(Tile->GetRepresentedSlot()) == Tile;
    if (CharacterDetailPanel) { CharacterDetailPanel->SetVisibility(!bBackpackSelected && bInspectingGear ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed); }
}

void UIBInventoryScreen::HandleSearchChanged(const FText& Text)
{
    SearchText = Text.ToString().TrimStartAndEnd(); RebuildGrid();
}

void UIBInventoryScreen::CycleSort()
{
    SortMode = (SortMode + 1) % 3;
    const TCHAR* Labels[] = { TEXT("SORT: RARITY"), TEXT("SORT: NAME"), TEXT("SORT: CLEARANCE") };
    if (SortLabel) { SortLabel->SetText(FText::FromString(Labels[SortMode])); }
    RebuildGrid();
}

void UIBInventoryScreen::EquipSelected()
{
    FIBItemInstance Selected;
    if (BoundInventory && BoundInventory->FindItem(SelectedItemId,Selected) && Selected.IsValid() && Selected.Definition->EquipSlot != EIBEquipSlot::None)
    { BoundInventory->RequestEquip(SelectedItemId); }
}

void UIBInventoryScreen::NativeScreenOpened()
{
	bScreenOpen = true;
	BindInventory();
	if (APlayerController* PC = GetOwningPlayer())
	{
		PreviewIdentity = PC->GetPlayerState<AIBPlayerState>();
		if (PreviewIdentity) { PreviewIdentity->OnOperativeIdentityChanged.AddUniqueDynamic(this, &UIBInventoryScreen::RefreshCharacterPreview); }
	}
	RebuildAll();
	RefreshSubtabs();
}

void UIBInventoryScreen::NativeScreenClosed()
{
	bScreenOpen = false;
	ReleaseCharacterPreview();
	if (PreviewIdentity) { PreviewIdentity->OnOperativeIdentityChanged.RemoveDynamic(this, &UIBInventoryScreen::RefreshCharacterPreview); }
	PreviewIdentity = nullptr;
	UnbindInventory();
	BP_OnItemUnfocused();
}

void UIBInventoryScreen::NativeDestruct()
{
	bScreenOpen = false;
	ReleaseCharacterPreview();
	if (PreviewIdentity) { PreviewIdentity->OnOperativeIdentityChanged.RemoveDynamic(this, &UIBInventoryScreen::RefreshCharacterPreview); }
	PreviewIdentity = nullptr;
	UnbindInventory();
	Super::NativeDestruct();
}

void UIBInventoryScreen::BindInventory()
{
	UIBInventoryComponent* Inventory = GetInventory();
	if (Inventory == BoundInventory) { return; }
	UnbindInventory();

	BoundInventory = Inventory;
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.AddDynamic(this, &UIBInventoryScreen::HandleInventoryChanged);
		BoundInventory->OnEquipmentChanged.AddDynamic(this, &UIBInventoryScreen::HandleEquipmentChanged);
	}
	else
	{
		// Loudly, once, in the log — the #1 setup miss will be the GameMode still
		// pointing at the engine's default PlayerState.
		UE_LOG(LogIronBreach, Warning,
			TEXT("[InventoryScreen] No UIBInventoryComponent — is the GameMode's Player State Class set to IBPlayerState? (MENUS_UI_WIRING.md §3)"));
	}
}

void UIBInventoryScreen::UnbindInventory()
{
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleInventoryChanged);
		BoundInventory->OnEquipmentChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleEquipmentChanged);
		BoundInventory = nullptr;
	}
}

UButton* UIBInventoryScreen::MakeFilterTab(UHorizontalBox* Row, const FText& Label)
{
	if (!WidgetTree || !Row) { return nullptr; }

	UTextBlock* TabLabel = nullptr;
	UButton* Tab = IBMenuLayout::Button(WidgetTree, Label, &TabLabel);
	FSlateFontInfo TabFont = TabLabel->GetFont(); TabFont.Size = 13; TabLabel->SetFont(TabFont);
	TabLabel->SetColorAndOpacity(FSlateColor(IBStyle::TextLo()));
	if (UHorizontalBoxSlot* TabSlot = Row->AddChildToHorizontalBox(Tab))
	{
		TabSlot->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
	}
	FilterTabLabels.Add(TabLabel);
	return Tab;
}

void UIBInventoryScreen::RefreshFilterTabs()
{
    for (int32 Index=0; Index<FilterTabLabels.Num() && Index<FilterCategories.Num(); ++Index)
    {
        const bool bActive = FilterCategories[Index] == EIBItemCategory::None ? bFilterAll : (!bFilterAll && CategoryFilter == FilterCategories[Index]);
        UTextBlock* Label = FilterTabLabels[Index];
        if (FilterButtons.IsValidIndex(Index) && FilterButtons[Index]) { IBHangar::StyleRail(FilterButtons[Index],bActive); }
        else { IBHangar::StyleButton(Cast<UButton>(Label->GetParent()),bActive); }
        Label->SetColorAndOpacity(bActive ? IBStyle::TextHi() : IBStyle::TextLo());
        if (FilterCounts.IsValidIndex(Index) && FilterCounts[Index]) { FilterCounts[Index]->SetColorAndOpacity(bActive ? IBHangar::Cyan() : IBStyle::TextLo()); }
        if (FilterAccents.IsValidIndex(Index) && FilterAccents[Index]) { FilterAccents[Index]->SetBrushColor(bActive ? IBHangar::Cyan() : FLinearColor::Transparent); }
    }
}

void UIBInventoryScreen::SetCategoryFilter(EIBItemCategory Category)
{
	if (bFilterAll || CategoryFilter != Category)
	{
		bFilterAll = false;
		CategoryFilter = Category;
		RefreshFilterTabs();
		RebuildGrid();
	}
}

void UIBInventoryScreen::SetFilterAll()
{
	if (!bFilterAll)
	{
		bFilterAll = true;
		RefreshFilterTabs();
		RebuildGrid();
	}
}

void UIBInventoryScreen::HandleInventoryChanged()
{
	RebuildGrid();
	RefreshEquipmentWells(); // stack counts/removals can touch equipped items too
}

void UIBInventoryScreen::HandleEquipmentChanged(EIBEquipSlot /*ChangedSlot*/, const FIBItemInstance& /*ChangedItem*/)
{
	RebuildGrid();
	RefreshEquipmentWells();
}

void UIBInventoryScreen::RebuildAll()
{
	RebuildGrid();
	RefreshEquipmentWells();
}

void UIBInventoryScreen::RebuildGrid()
{
	if (!ItemGrid) { return; }
	SelectedTile.Reset();
	ItemGrid->ClearChildren();
	SetDetails(nullptr);
	if (PackStatus) { PackStatus->SetText(NSLOCTEXT("IBInv", "PackUnavailable", "EQUIPMENT DATA UNAVAILABLE")); }

	if (!BoundInventory || !GridTileClass) { return; }

	// Equipped instances stay out of the backpack grid (they live in the wells).
	TSet<FGuid> EquippedIds;
	for (uint8 SlotIndex = 1; SlotIndex < static_cast<uint8>(EIBEquipSlot::Count); ++SlotIndex)
	{
		FIBItemInstance Equipped;
		if (BoundInventory->GetEquippedItem(static_cast<EIBEquipSlot>(SlotIndex), Equipped))
		{
			EquippedIds.Add(Equipped.InstanceId);
		}
	}

	// Rail counters: backpack contents per category, independent of the search box.
	{
		TMap<EIBItemCategory, int32> Counts;
		int32 Total = 0;
		for (const FIBItemInstance& Item : BoundInventory->GetAllItems())
		{
			if (!Item.IsValid() || EquippedIds.Contains(Item.InstanceId)) { continue; }
			++Counts.FindOrAdd(Item.Definition->Category);
			++Total;
		}
		for (int32 Index = 0; Index < FilterCounts.Num() && Index < FilterCategories.Num(); ++Index)
		{
			if (!FilterCounts[Index]) { continue; }
			const int32 Count = FilterCategories[Index] == EIBItemCategory::None ? Total : Counts.FindRef(FilterCategories[Index]);
			FilterCounts[Index]->SetText(Count > 0 ? FText::AsNumber(Count) : FText::GetEmpty());
		}
	}

	int32 CellIndex = 0;
	TArray<FIBItemInstance> Items = bFilterAll
		? BoundInventory->GetAllItems()
		: BoundInventory->GetItemsByCategory(CategoryFilter);
	Items.RemoveAll([&](const FIBItemInstance& Item)
	{
		return !Item.IsValid() || EquippedIds.Contains(Item.InstanceId) || (!SearchText.IsEmpty() && !Item.Definition->DisplayName.ToString().Contains(SearchText,ESearchCase::IgnoreCase));
	});
	Items.StableSort([this](const FIBItemInstance& A, const FIBItemInstance& B)
	{
		if (SortMode == 0 && A.Definition->Rarity != B.Definition->Rarity) { return A.Definition->Rarity > B.Definition->Rarity; }
		if (SortMode == 2 && A.ClearanceRating != B.ClearanceRating) { return A.ClearanceRating > B.ClearanceRating; }
		return A.Definition->DisplayName.CompareTo(B.Definition->DisplayName) < 0;
	});
	for (const FIBItemInstance& Item : Items)
	{
		if (EquippedIds.Contains(Item.InstanceId)) { continue; }

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }
		Tile->SetItem(Item); Tile->SetPresentationSize(FVector2D(108,108));
		WireTile(Tile);
		if (Item.InstanceId == SelectedItemId) { SelectedTile = Tile; }

		UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns);
		if (GridSlot)
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
	}
	if (!SelectedTile.IsValid() && ItemGrid->GetChildrenCount() > 0)
	{
		SelectedTile = Cast<UIBItemTileWidget>(ItemGrid->GetChildAt(0));
		if (SelectedTile.IsValid()) { SelectedItemId = SelectedTile->GetItem().InstanceId; }
	}
	if (!SelectedTile.IsValid()) { SelectedItemId.Invalidate(); }
	if (SelectedTile.IsValid()) { SelectedTile->SetSelected(true); }
	SetDetails(SelectedTile.Get());
	// Decorative empty cells describe the grid, not an invented capacity limit.
	if (bHangarLayout)
	{
		for (int32 Index=CellIndex; Index<FMath::Max(24, FMath::DivideAndRoundUp(CellIndex,GridColumns)*GridColumns); ++Index)
		{
			UBorder* Empty = IBHangar::Inset(WidgetTree,nullptr,FMargin(0));
			Empty->SetVisibility(ESlateVisibility::HitTestInvisible);
			USizeBox* Cell = IBMenuLayout::Width(WidgetTree,Empty,108); Cell->SetHeightOverride(108);
			ItemGrid->AddChildToUniformGrid(Cell,Index/GridColumns,Index%GridColumns);
		}
	}
	if (PackStatus)
	{
		PackStatus->SetText(CellIndex > 0 ? FText::Format(NSLOCTEXT("IBInv", "PackCountPlural", "{0} {0}|plural(one=ITEM,other=ITEMS) / IN BACKPACK"), CellIndex)
			: NSLOCTEXT("IBInv", "PackEmpty", "NO ITEMS IN THIS VIEW"));
	}
}

void UIBInventoryScreen::RefreshEquipmentWells()
{
	if (ClearanceText && BoundInventory)
	{
		ClearanceText->SetText(FText::AsNumber(BoundInventory->GetTotalClearanceRating()));
	}

	for (uint8 SlotIndex = 1; SlotIndex < static_cast<uint8>(EIBEquipSlot::Count); ++SlotIndex)
	{
		const EIBEquipSlot EquipSlot = static_cast<EIBEquipSlot>(SlotIndex);
		UIBItemTileWidget* Well = GetWellForSlot(EquipSlot);
		if (!Well) { continue; }

		WireTile(Well);

		FIBItemInstance Equipped;
		const bool bFilled = BoundInventory && BoundInventory->GetEquippedItem(EquipSlot, Equipped);
		if (bFilled)
		{
			Well->SetItem(Equipped);
		}
		else
		{
			Well->SetEmptySlot(EquipSlot);
		}
		// Equipped gear reads its own slot; only an empty well needs the caption (Hidden keeps the column steady).
		if (const TObjectPtr<UTextBlock>* Caption = WellLabels.Find(EquipSlot))
		{
			if (*Caption) { (*Caption)->SetVisibility(bFilled ? ESlateVisibility::Hidden : ESlateVisibility::HitTestInvisible); }
		}
	}
	// Loadout plinth: three real numbers from the bound inventory, nothing invented.
	if (BoundInventory)
	{
		int32 EquippedCount = 0;
		TSet<FGuid> EquippedIds;
		for (uint8 Index=1; Index<static_cast<uint8>(EIBEquipSlot::Count); ++Index)
		{
			FIBItemInstance Item;
			if (BoundInventory->GetEquippedItem(static_cast<EIBEquipSlot>(Index),Item)) { ++EquippedCount; EquippedIds.Add(Item.InstanceId); }
		}
		int32 BackpackCount = 0;
		for (const FIBItemInstance& Item : BoundInventory->GetAllItems())
		{
			if (Item.IsValid() && !EquippedIds.Contains(Item.InstanceId)) { ++BackpackCount; }
		}
		if (CharacterStats) { CharacterStats->SetText(FText::AsNumber(BoundInventory->GetTotalClearanceRating())); }
		if (CharacterEquipmentValue) { CharacterEquipmentValue->SetText(FText::Format(NSLOCTEXT("IBInv","EquippedOf","{0} / {1}"),EquippedCount,static_cast<int32>(EIBEquipSlot::Count) - 1)); }
		if (CharacterBackpackValue) { CharacterBackpackValue->SetText(FText::AsNumber(BackpackCount)); }
	}
	else
	{
		const FText Dash = FText::FromString(TEXT("—"));
		if (CharacterStats) { CharacterStats->SetText(Dash); }
		if (CharacterEquipmentValue) { CharacterEquipmentValue->SetText(Dash); }
		if (CharacterBackpackValue) { CharacterBackpackValue->SetText(Dash); }
	}
	RefreshTabBanner();
	RefreshCharacterPreview();
}

void UIBInventoryScreen::WireTile(UIBItemTileWidget* Tile)
{
	// Idempotent: Remove+Add so cached/rebuilt tiles never double-fire.
	Tile->OnTileClicked.RemoveDynamic(this, &UIBInventoryScreen::HandleTileClicked);
	Tile->OnTileClicked.AddDynamic(this, &UIBInventoryScreen::HandleTileClicked);
	Tile->OnTileHoverChanged.RemoveDynamic(this, &UIBInventoryScreen::HandleTileHoverChanged);
	Tile->OnTileHoverChanged.AddDynamic(this, &UIBInventoryScreen::HandleTileHoverChanged);
}

UIBItemTileWidget* UIBInventoryScreen::GetWellForSlot(EIBEquipSlot InSlot) const
{
	switch (InSlot)
	{
	case EIBEquipSlot::WeaponPrimary: return Tile_WeaponPrimary;
	case EIBEquipSlot::WeaponSpecial: return Tile_WeaponSpecial;
	case EIBEquipSlot::WeaponHeavy:   return Tile_WeaponHeavy;
	case EIBEquipSlot::ArmorHead:     return Tile_ArmorHead;
	case EIBEquipSlot::ArmorChest:    return Tile_ArmorChest;
	case EIBEquipSlot::ArmorArms:     return Tile_ArmorArms;
	case EIBEquipSlot::ArmorLegs:     return Tile_ArmorLegs;
	case EIBEquipSlot::GearAntiKaiju: return Tile_GearAntiKaiju;
	default:                          return nullptr;
	}
}

void UIBInventoryScreen::HandleTileClicked(UIBItemTileWidget* Tile)
{
	if (!Tile || !BoundInventory) { return; }

	// Equipment well with something in it → unequip. Backpack tile that can be
	// worn → equip. Server decides; the redraw comes back through the signals.
	const bool bIsWell = (GetWellForSlot(Tile->GetRepresentedSlot()) == Tile);
	const FIBItemInstance& Item = Tile->GetItem();

	if (bHangarLayout && !bIsWell && Item.IsValid())
	{
		if (SelectedTile.IsValid()) { SelectedTile->SetSelected(false); }
		SelectedItemId = Item.InstanceId; SelectedTile = Tile; Tile->SetSelected(true); SetDetails(Tile); return;
	}

	if (bIsWell && Item.IsValid())
	{
		BoundInventory->RequestUnequip(Tile->GetRepresentedSlot());
	}
	else if (!bIsWell && Item.IsValid() && Item.Definition && Item.Definition->EquipSlot != EIBEquipSlot::None)
	{
		BoundInventory->RequestEquip(Item.InstanceId);
	}
}

void UIBInventoryScreen::HandleTileHoverChanged(UIBItemTileWidget* Tile, bool bHovered)
{
	if (!Tile) { return; }

	if (bHovered && Tile->GetItem().IsValid())
	{
		const bool bIsWell = (GetWellForSlot(Tile->GetRepresentedSlot()) == Tile);
		if (!bHangarLayout || !bBackpackSelected) { SetDetails(Tile); }
		BP_OnItemFocused(Tile->GetItem(), bIsWell);
	}
	else
	{
		SetDetails(bBackpackSelected ? SelectedTile.Get() : nullptr);
		BP_OnItemUnfocused();
	}
}
