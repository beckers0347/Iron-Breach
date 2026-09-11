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
	Column->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
		UEnum::GetDisplayValueAsText(ForSlot).ToUpper(), 10, IBStyle::TextLo(), 60))->SetPadding(FMargin(0, 0, 0, 4));
	Tile->SetEmptySlot(ForSlot);
	Tile->SetPresentationSize(FVector2D(110, 110));
	UVerticalBoxSlot* WellSlot = Column->AddChildToVerticalBox(Tile);
	WellSlot->SetHorizontalAlignment(HAlign_Left);
	WellSlot->SetPadding(FMargin(0, 0, 0, 10));
	return Tile;
}

void UIBInventoryScreen::BuildFallbackLayout()
{
    UVerticalBox* Body = BuildHangarPage(NSLOCTEXT("IBInv", "HangarControls", "LEFT / RIGHT  CHARACTER & INVENTORY     CLICK  SELECT ITEM     EQUIP  APPLY SELECTION     Q E  SWITCH MENU     ESC  RETURN"));
    InventoryPages = WidgetTree->ConstructWidget<UWidgetSwitcher>();
    Body->AddChildToVerticalBox(InventoryPages)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    UOverlay* Character = WidgetTree->ConstructWidget<UOverlay>();
    InventoryPages->AddChild(Character);
    UHorizontalBox* Equipment = WidgetTree->ConstructWidget<UHorizontalBox>();
    Character->AddChildToOverlay(Equipment);
    UVerticalBox* Weapons = WidgetTree->ConstructWidget<UVerticalBox>();
    Weapons->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("WEAPONS / FIELD GEAR"),12,IBHangar::Cyan()))->SetPadding(FMargin(0,0,0,16));
    Tile_WeaponPrimary = MakeWell(Weapons, EIBEquipSlot::WeaponPrimary);
    Tile_WeaponSpecial = MakeWell(Weapons, EIBEquipSlot::WeaponSpecial);
    Tile_WeaponHeavy = MakeWell(Weapons, EIBEquipSlot::WeaponHeavy);
    Tile_GearAntiKaiju = MakeWell(Weapons, EIBEquipSlot::GearAntiKaiju);
    auto* Left = Equipment->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Weapons,200));
    Left->SetPadding(FMargin(170,0,0,0)); Left->SetVerticalAlignment(VAlign_Center);

    UVerticalBox* Portrait = WidgetTree->ConstructWidget<UVerticalBox>();
    CharacterName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),28);
    CharacterName->SetJustification(ETextJustify::Center);
    CharacterName->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
    Portrait->AddChildToVerticalBox(CharacterName);
    CharacterRole = IBHangar::Label(WidgetTree,TEXT(""),12,IBHangar::Cyan());
    CharacterRole->SetJustification(ETextJustify::Center);
    Portrait->AddChildToVerticalBox(CharacterRole)->SetPadding(FMargin(0,4,0,0));
    CharacterImage = WidgetTree->ConstructWidget<UImage>();
    CharacterImage->SetVisibility(ESlateVisibility::HitTestInvisible);
    USizeBox* PortraitSize = IBMenuLayout::Width(WidgetTree,CharacterImage,1024); PortraitSize->SetHeightOverride(1024);
    UScaleBox* Fit = WidgetTree->ConstructWidget<UScaleBox>(); Fit->SetStretch(EStretch::ScaleToFit); Fit->SetContent(PortraitSize);
    Portrait->AddChildToVerticalBox(Fit)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CharacterStats = IBHangar::Label(WidgetTree,TEXT(""),14,IBHangar::Cyan());
    CharacterStats->SetJustification(ETextJustify::Center);
    Portrait->AddChildToVerticalBox(IBHangar::Panel(WidgetTree,CharacterStats,FMargin(18,14)));
    Equipment->AddChildToHorizontalBox(Portrait)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    UVerticalBox* Armor = WidgetTree->ConstructWidget<UVerticalBox>();
    Armor->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("ARMOR"),12,IBHangar::Cyan()))->SetPadding(FMargin(0,0,0,16));
    Tile_ArmorHead = MakeWell(Armor,EIBEquipSlot::ArmorHead);
    Tile_ArmorChest = MakeWell(Armor,EIBEquipSlot::ArmorChest);
    Tile_ArmorArms = MakeWell(Armor,EIBEquipSlot::ArmorArms);
    Tile_ArmorLegs = MakeWell(Armor,EIBEquipSlot::ArmorLegs);
    auto* Right = Equipment->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Armor,200));
    Right->SetPadding(FMargin(0,0,170,0)); Right->SetVerticalAlignment(VAlign_Center);
    for (UVerticalBox* Column : { Weapons, Armor })
        for (UWidget* Child : Column->GetAllChildren())
            CastChecked<UVerticalBoxSlot>(Child->Slot)->SetHorizontalAlignment(HAlign_Center);

    UVerticalBox* GearDetails = WidgetTree->ConstructWidget<UVerticalBox>();
    CharacterDetailName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),22); CharacterDetailName->SetAutoWrapText(true);
    CharacterDetailInfo = IBHangar::Label(WidgetTree,TEXT(""),13); CharacterDetailInfo->SetAutoWrapText(true);
    GearDetails->AddChildToVerticalBox(CharacterDetailName); IBHangar::Rule(WidgetTree,GearDetails);
    IBMenuLayout::Scroll(WidgetTree,GearDetails,CharacterDetailInfo);
    CharacterDetailPanel = IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,GearDetails),300);
    CharacterDetailPanel->SetHeightOverride(260);
    auto* Popup = Character->AddChildToOverlay(CharacterDetailPanel);
    Popup->SetHorizontalAlignment(HAlign_Left); Popup->SetVerticalAlignment(VAlign_Bottom);
    CharacterDetailPanel->SetVisibility(ESlateVisibility::Collapsed);

    UVerticalBox* BackpackPage = WidgetTree->ConstructWidget<UVerticalBox>(); InventoryPages->AddChild(BackpackPage);
    BackpackPage->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree,NSLOCTEXT("IBInv","PackTitle","INVENTORY"),36))->SetPadding(FMargin(0,0,0,20));
    UHorizontalBox* PackColumns = WidgetTree->ConstructWidget<UHorizontalBox>();
    BackpackPage->AddChildToVerticalBox(PackColumns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UVerticalBox* Categories = WidgetTree->ConstructWidget<UVerticalBox>();
    Categories->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("CATEGORIES"),11,IBHangar::Cyan()))->SetPadding(FMargin(4,0,0,20));
    FilterTabLabels.Reset(); FilterCategories.Reset();
    const TPair<EIBItemCategory,const TCHAR*> Filters[] = {
        {EIBItemCategory::None,TEXT("ALL ITEMS")}, {EIBItemCategory::Weapon,TEXT("WEAPONS")},
        {EIBItemCategory::Armor,TEXT("ARMOR")}, {EIBItemCategory::KaijuMaterial,TEXT("MATERIALS")},
        {EIBItemCategory::Consumable,TEXT("CONSUMABLES")}, {EIBItemCategory::Splice,TEXT("SPLICES")},
        {EIBItemCategory::Doctrine,TEXT("DOCTRINES")}, {EIBItemCategory::Collectible,TEXT("COLLECTIBLES")},
        {EIBItemCategory::Cosmetic,TEXT("COSMETICS")}};
    for (const auto& Entry : Filters)
    {
        UIBMenuActionButton* Filter = WidgetTree->ConstructWidget<UIBMenuActionButton>();
        UTextBlock* Label = IBHangar::Label(WidgetTree,Entry.Value,12);
        Filter->SetContent(Label); IBHangar::StyleButton(Filter);
        const EIBItemCategory Category = Entry.Key;
        Filter->BindAction(FSimpleDelegate::CreateWeakLambda(this,[this,Category] { if (Category == EIBItemCategory::None) { SetFilterAll(); } else { SetCategoryFilter(Category); } }));
        Categories->AddChildToVerticalBox(Filter)->SetPadding(FMargin(0,0,0,7));
        FilterTabLabels.Add(Label); FilterCategories.Add(Category);
    }
    PackColumns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Categories,FMargin(14,20)),200))->SetPadding(FMargin(0,0,18,0));

    UVerticalBox* Backpack = WidgetTree->ConstructWidget<UVerticalBox>();
    UHorizontalBox* Tools = WidgetTree->ConstructWidget<UHorizontalBox>();
    UEditableTextBox* Search = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("InventorySearch"));
    Search->SetHintText(NSLOCTEXT("IBInv","Search","Search inventory..."));
    FEditableTextBoxStyle SearchStyle = Search->GetWidgetStyle();
    SearchStyle.SetBackgroundImageNormal(IBStyle::RoundedBrush(IBHangar::Ink(),0,IBHangar::Cyan(),1));
    SearchStyle.SetBackgroundImageHovered(SearchStyle.BackgroundImageNormal); SearchStyle.SetBackgroundImageFocused(SearchStyle.BackgroundImageNormal);
    SearchStyle.SetForegroundColor(IBStyle::TextHi()); SearchStyle.SetPadding(FMargin(14,10));
    Search->SetWidgetStyle(SearchStyle); Search->OnTextChanged.AddDynamic(this,&UIBInventoryScreen::HandleSearchChanged);
    Tools->AddChildToHorizontalBox(Search)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UTextBlock* SortText = nullptr;
    UButton* Sort = IBHangar::Button(WidgetTree,TEXT("SORT: RARITY"),&SortText); SortLabel = SortText;
    Sort->OnClicked.AddDynamic(this,&UIBInventoryScreen::CycleSort);
    Tools->AddChildToHorizontalBox(Sort)->SetPadding(FMargin(12,0,0,0));
    Backpack->AddChildToVerticalBox(Tools)->SetPadding(FMargin(0,0,0,16));
    ItemGrid = WidgetTree->ConstructWidget<UUniformGridPanel>(); ItemGrid->SetSlotPadding(FMargin(5)); GridColumns = 6;
    IBMenuLayout::Scroll(WidgetTree,Backpack,ItemGrid);
    CastChecked<UScrollBoxSlot>(ItemGrid->Slot)->SetHorizontalAlignment(HAlign_Left);
    PackStatus = IBHangar::Label(WidgetTree,TEXT(""),12);
    Backpack->AddChildToVerticalBox(PackStatus)->SetPadding(FMargin(4,14,0,0));
    auto* GridArea = PackColumns->AddChildToHorizontalBox(IBHangar::Panel(WidgetTree,Backpack,FMargin(16)));
    GridArea->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); GridArea->SetPadding(FMargin(0,0,18,0));

    UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailRarity = IBHangar::Label(WidgetTree,TEXT("EQUIPMENT INSPECTION"),11,IBHangar::Cyan()); Details->AddChildToVerticalBox(DetailRarity);
    Txt_DetailName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),28); Txt_DetailName->SetAutoWrapText(true);
    Details->AddChildToVerticalBox(Txt_DetailName)->SetPadding(FMargin(0,8,0,0));
    IBHangar::Rule(WidgetTree,Details,10);
    DetailIcon = WidgetTree->ConstructWidget<UImage>();
    USizeBox* IconSize = IBMenuLayout::Width(WidgetTree,DetailIcon,200); IconSize->SetHeightOverride(164);
    UScaleBox* IconFit = WidgetTree->ConstructWidget<UScaleBox>(); IconFit->SetStretch(EStretch::ScaleToFit); IconFit->SetContent(IconSize);
    Details->AddChildToVerticalBox(IconFit)->SetHorizontalAlignment(HAlign_Center);
    UVerticalBox* DetailContent = WidgetTree->ConstructWidget<UVerticalBox>();
    Txt_DetailInfo = IBHangar::Label(WidgetTree,TEXT(""),14); Txt_DetailInfo->SetAutoWrapText(true);
    DetailContent->AddChildToVerticalBox(Txt_DetailInfo)->SetPadding(FMargin(0,14,0,18));
    DetailStats = WidgetTree->ConstructWidget<UVerticalBox>(); DetailContent->AddChildToVerticalBox(DetailStats);
    IBMenuLayout::Scroll(WidgetTree,Details,DetailContent);
    UTextBlock* ActionText = nullptr; EquipButton = IBHangar::Button(WidgetTree,TEXT("EQUIP"),&ActionText); EquipLabel = ActionText;
    EquipButton->OnClicked.AddDynamic(this,&UIBInventoryScreen::EquipSelected);
    Details->AddChildToVerticalBox(EquipButton)->SetPadding(FMargin(0,16,0,0));
    DetailPanel = IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Details,FMargin(24)),390);
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
	const AIBCharacter_Infantry* Infantry = PC ? Cast<AIBCharacter_Infantry>(PC->GetPawn()) : nullptr;
	PreviewStage->ConfigureForInventory(Infantry ? Infantry->GetMesh() : nullptr);
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
    if (DetailStats) { DetailStats->ClearChildren(); }
    if (DetailIcon) { DetailIcon->SetBrushFromTexture(Def ? Def->Icon.LoadSynchronous() : nullptr); DetailIcon->SetVisibility(Def && !Def->Icon.IsNull() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed); }
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
        if (Txt_DetailInfo) { Txt_DetailInfo->SetText(NSLOCTEXT("IBInv","SelectHint","Select equipment from your backpack to inspect its stats and equip it.\n\nLoot collected in the field appears here.")); }
        if (DetailRarity) { DetailRarity->SetText(NSLOCTEXT("IBInv","EquipmentInspection","EQUIPMENT INSPECTION")); }
        if (CharacterDetailPanel) { CharacterDetailPanel->SetVisibility(ESlateVisibility::Collapsed); }
        return;
    }
    const FLinearColor Rarity = UIBUISettings::Get()->GetRarityColor(Def->Rarity);
    if (DetailRarity) { DetailRarity->SetText(FText::Format(NSLOCTEXT("IBInv","TypeRarity","{0}  /  {1}"),UEnum::GetDisplayValueAsText(Def->Rarity).ToUpper(),UEnum::GetDisplayValueAsText(Def->Category).ToUpper())); DetailRarity->SetColorAndOpacity(Rarity); }
    if (Txt_DetailName) { Txt_DetailName->SetText(Def->DisplayName); Txt_DetailName->SetColorAndOpacity(Rarity); }
    FString Info = Def->EquipSlot != EIBEquipSlot::None ? FString::Printf(TEXT("CLEARANCE  %d\n\n"), Tile->GetItem().ClearanceRating) : FString();
    if (Tile->GetItem().StackCount > 1) { Info += FString::Printf(TEXT("QUANTITY  %d\n\n"),Tile->GetItem().StackCount); }
    Info += Def->Description.ToString();
    if (!Def->Flavor.IsEmpty()) { Info += TEXT("\n\n") + Def->Flavor.ToString(); }
    if (Txt_DetailInfo) { Txt_DetailInfo->SetText(FText::FromString(Info)); }
    if (DetailStats) { for (const FIBItemStat& Stat : Def->Stats) { IBHangar::Stat(WidgetTree,DetailStats,Stat.StatName,Stat.Value); } }
    if (CharacterDetailName) { CharacterDetailName->SetText(Def->DisplayName); CharacterDetailName->SetColorAndOpacity(Rarity); }
    if (CharacterDetailInfo) { CharacterDetailInfo->SetText(FText::FromString(Info)); }
    if (CharacterDetailPanel) { CharacterDetailPanel->SetVisibility(!bBackpackSelected ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed); }
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
        IBHangar::StyleButton(Cast<UButton>(Label->GetParent()),bActive);
        Label->SetColorAndOpacity(bActive ? IBHangar::Cyan() : IBStyle::TextLo());
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
			UBorder* Empty = IBHangar::Panel(WidgetTree,nullptr,FMargin(0));
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
		if (BoundInventory && BoundInventory->GetEquippedItem(EquipSlot, Equipped))
		{
			Well->SetItem(Equipped);
		}
		else
		{
			Well->SetEmptySlot(EquipSlot);
		}
	}
	if (CharacterStats && BoundInventory)
	{
		int32 EquippedCount = 0;
		for (uint8 Index=1; Index<static_cast<uint8>(EIBEquipSlot::Count); ++Index)
		{ FIBItemInstance Item; if (BoundInventory->GetEquippedItem(static_cast<EIBEquipSlot>(Index),Item)) { ++EquippedCount; } }
		CharacterStats->SetText(FText::Format(NSLOCTEXT("IBInv","EquipmentSummary","CLEARANCE  {0}     /     EQUIPPED  {1} / 8"),BoundInventory->GetTotalClearanceRating(),EquippedCount));
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
