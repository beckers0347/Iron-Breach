#include "UI/IBLedgerScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBUISettings.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/ButtonSlot.h"
#include "Items/IBLedgerSubsystem.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBItemTileWidget.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/GameInstance.h"

void UIBLedgerScreen::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (!GridTileClass) { GridTileClass = UIBItemTileWidget::StaticClass(); }
    if (!ItemGrid && WidgetTree)
    {
        const auto Page = BuildHangarSection(
            NSLOCTEXT("IBLedger", "Title", "THE LEDGER"),
            NSLOCTEXT("IBLedger", "Kicker", "BREAKWATER / COLLECTION ARCHIVE"),
            NSLOCTEXT("IBLedger", "Controls", "HOVER / PREVIEW ENTRY     CLICK / KEEP RECORD OPEN     Q E / SWITCH MENU     ESC / RETURN"));
        if (!Page.Body) { return; }
        UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
        Page.Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

        UVerticalBox* Categories = WidgetTree->ConstructWidget<UVerticalBox>();
        Categories->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBLedger","Collections","COLLECTIONS"),9,IBStyle::TextLo(),200))->SetPadding(FMargin(14,2,0,12));
        const FText Labels[] = { NSLOCTEXT("IBLedger", "All", "ALL"), NSLOCTEXT("IBLedger", "Weapons", "WEAPONS"),
            NSLOCTEXT("IBLedger", "Armor", "ARMOR"), NSLOCTEXT("IBLedger", "Materials", "MATERIALS") };
        const EIBItemCategory GlyphCategories[] = { EIBItemCategory::None, EIBItemCategory::Weapon, EIBItemCategory::Armor, EIBItemCategory::KaijuMaterial };
        for (int32 Index=0; Index<4; ++Index)
        {
            UButton* Button = WidgetTree->ConstructWidget<UButton>(); IBHangar::StyleRail(Button);
            UHorizontalBox* ButtonCopy = WidgetTree->ConstructWidget<UHorizontalBox>();
            UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree,FLinearColor::Transparent); Accent->SetPadding(FMargin(1.5f,0));
            UHorizontalBoxSlot* AccentSlot = ButtonCopy->AddChildToHorizontalBox(Accent); AccentSlot->SetPadding(FMargin(0,0,10,0)); AccentSlot->SetVerticalAlignment(VAlign_Fill);
            UIBItemGlyphWidget* Glyph = CreateWidget<UIBItemGlyphWidget>(this); Glyph->SetGlyph(GlyphCategories[Index]);
            USizeBox* GlyphSize = IBMenuLayout::Width(WidgetTree,Glyph,20); GlyphSize->SetHeightOverride(20);
            UHorizontalBoxSlot* GlyphSlot = ButtonCopy->AddChildToHorizontalBox(GlyphSize); GlyphSlot->SetPadding(FMargin(0,0,10,0)); GlyphSlot->SetVerticalAlignment(VAlign_Center);
            UTextBlock* Label = IBMenuLayout::Text(WidgetTree,Labels[Index],10,IBStyle::TextLo(),60);
            UHorizontalBoxSlot* LabelSlot = ButtonCopy->AddChildToHorizontalBox(Label); LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); LabelSlot->SetVerticalAlignment(VAlign_Center);
            Button->SetContent(ButtonCopy);
            CastChecked<UButtonSlot>(ButtonCopy->Slot)->SetHorizontalAlignment(HAlign_Fill);
            Categories->AddChildToVerticalBox(Button)->SetPadding(FMargin(0,0,0,2));
            FilterButtons.Add(Button); FilterLabels.Add(Label); FilterAccents.Add(Accent);
        }
        FilterButtons[0]->OnClicked.AddDynamic(this,&UIBLedgerScreen::HandleAll);
        FilterButtons[1]->OnClicked.AddDynamic(this,&UIBLedgerScreen::HandleWeapons);
        FilterButtons[2]->OnClicked.AddDynamic(this,&UIBLedgerScreen::HandleArmor);
        FilterButtons[3]->OnClicked.AddDynamic(this,&UIBLedgerScreen::HandleMaterials);
        UHorizontalBoxSlot* CategorySlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,IBHangar::Panel(WidgetTree,Categories,FMargin(6,12,6,10)),206));
        CategorySlot->SetPadding(FMargin(0,0,14,0)); CategorySlot->SetVerticalAlignment(VAlign_Top);

        UVerticalBox* Catalog = WidgetTree->ConstructWidget<UVerticalBox>();
        UHorizontalBox* CatalogHeader = WidgetTree->ConstructWidget<UHorizontalBox>();
        CatalogHeader->AddChildToHorizontalBox(IBHangar::Label(WidgetTree,TEXT("FIELD DISCOVERIES"),13,IBStyle::TextHi()))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        CatalogHeader->AddChildToHorizontalBox(IBHangar::Label(WidgetTree,TEXT("CATEGORY / CLEARANCE"),10,IBStyle::TextLo()))->SetVerticalAlignment(VAlign_Center);
        Catalog->AddChildToVerticalBox(CatalogHeader)->SetPadding(FMargin(0,0,0,18));
        ItemGrid = WidgetTree->ConstructWidget<UUniformGridPanel>(); ItemGrid->SetSlotPadding(FMargin(3)); GridColumns = 7;
        IBMenuLayout::Scroll(WidgetTree,Catalog,ItemGrid);
        CastChecked<UScrollBoxSlot>(ItemGrid->Slot)->SetHorizontalAlignment(HAlign_Left);
        ProgressText = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextHi());
        Catalog->AddChildToVerticalBox(ProgressText)->SetPadding(FMargin(4,18,4,9));
        CollectionProgress = WidgetTree->ConstructWidget<UProgressBar>(); CollectionProgress->SetFillColorAndOpacity(IBHangar::Cyan());
        FProgressBarStyle ProgressStyle = CollectionProgress->GetWidgetStyle();
        ProgressStyle.BackgroundImage = IBStyle::RoundedBrush(FLinearColor(.025f,.06f,.065f),0);
        ProgressStyle.FillImage = IBStyle::RoundedBrush(FLinearColor::White,0); CollectionProgress->SetWidgetStyle(ProgressStyle);
        USizeBox* ProgressSize = WidgetTree->ConstructWidget<USizeBox>(); ProgressSize->SetHeightOverride(3); ProgressSize->SetContent(CollectionProgress);
        Catalog->AddChildToVerticalBox(ProgressSize)->SetPadding(FMargin(4,0,4,12));
        Catalog->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBLedger","CatalogHint","RECOVER ITEMS IN THE FIELD TO REVEAL SEALED RECORDS."),10,IBStyle::TextLo()))->SetPadding(FMargin(4,0,4,0));
        UHorizontalBoxSlot* CatalogSlot = Columns->AddChildToHorizontalBox(IBHangar::Panel(WidgetTree,Catalog,FMargin(18)));
        CatalogSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); CatalogSlot->SetPadding(FMargin(0,0,16,0));

        UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
        DetailRarity = IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBLedger","Archive","FIELD ARCHIVE"),11,IBHangar::Cyan(),140); Details->AddChildToVerticalBox(DetailRarity);
        DetailName = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),24); DetailName->SetAutoWrapText(true);
        Details->AddChildToVerticalBox(DetailName)->SetPadding(FMargin(0,6,0,0));
        DetailCategory = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo(),40); Details->AddChildToVerticalBox(DetailCategory)->SetPadding(FMargin(0,3,0,0));
        UOverlay* Preview = WidgetTree->ConstructWidget<UOverlay>();
        DetailIcon = WidgetTree->ConstructWidget<UImage>(); DetailIcon->SetVisibility(ESlateVisibility::Collapsed);
        UScaleBox* IconFit = WidgetTree->ConstructWidget<UScaleBox>(); IconFit->SetStretch(EStretch::ScaleToFit); IconFit->SetContent(DetailIcon);
        UOverlaySlot* IconSlot = Preview->AddChildToOverlay(IconFit); IconSlot->SetHorizontalAlignment(HAlign_Fill); IconSlot->SetVerticalAlignment(VAlign_Fill); IconSlot->SetPadding(FMargin(10));
        DetailGlyph = CreateWidget<UIBItemGlyphWidget>(this);
        USizeBox* GlyphSize = IBMenuLayout::Width(WidgetTree,DetailGlyph,96); GlyphSize->SetHeightOverride(96);
        UOverlaySlot* GlyphSlot = Preview->AddChildToOverlay(GlyphSize); GlyphSlot->SetHorizontalAlignment(HAlign_Center); GlyphSlot->SetVerticalAlignment(VAlign_Center);
        USizeBox* PreviewSize = WidgetTree->ConstructWidget<USizeBox>(); PreviewSize->SetHeightOverride(196); PreviewSize->SetContent(IBHangar::Inset(WidgetTree,Preview,FMargin(0)));
        Details->AddChildToVerticalBox(PreviewSize)->SetPadding(FMargin(0,14,0,14));
        UVerticalBox* RatingCopy = WidgetTree->ConstructWidget<UVerticalBox>();
        DetailRatingLabel = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),9,IBStyle::TextLo(),160);
        DetailRating = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),30);
        RatingCopy->AddChildToVerticalBox(DetailRatingLabel); RatingCopy->AddChildToVerticalBox(DetailRating);
        Details->AddChildToVerticalBox(RatingCopy);
        DetailAccent = IBStyle::MakeAccentBar(WidgetTree,IBHangar::Cyan()); DetailAccent->SetPadding(FMargin(0,.5f));
        Details->AddChildToVerticalBox(DetailAccent)->SetPadding(FMargin(0,12,0,14));
        UVerticalBox* Record = WidgetTree->ConstructWidget<UVerticalBox>();
        DetailStats = WidgetTree->ConstructWidget<UVerticalBox>(); Record->AddChildToVerticalBox(DetailStats);
        DetailInfo = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),12,IBStyle::TextLo(),10); DetailInfo->SetAutoWrapText(true); DetailInfo->SetLineHeightPercentage(1.3f);
        Record->AddChildToVerticalBox(DetailInfo)->SetPadding(FMargin(0,4,0,0));
        IBMenuLayout::Scroll(WidgetTree,Details,Record);
        DetailFooter = IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBLedger","Footer","BREAKWATER  /  COLLECTION ARCHIVE"),9,IBStyle::TextLo(),140);
        Details->AddChildToVerticalBox(DetailFooter)->SetPadding(FMargin(0,16,0,0));
        DetailFrame = IBHangar::Dossier(WidgetTree,Details,FMargin(22));
        Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,DetailFrame,380));
        ResetDetails(); RefreshFilters();
    }
}
void UIBLedgerScreen::ResetDetails()
{
	if (DetailName) { DetailName->SetText(NSLOCTEXT("IBLedger", "Idle", "BUILD THE ARCHIVE")); DetailName->SetColorAndOpacity(IBStyle::TextHi()); }
	if (DetailInfo) { DetailInfo->SetText(NSLOCTEXT("IBLedger", "IdleHint", "Every discovery becomes part of the record.\n\nHover over an entry to inspect its recovered data.")); }
	if (DetailRarity) { DetailRarity->SetText(NSLOCTEXT("IBLedger","Archive","FIELD ARCHIVE")); DetailRarity->SetColorAndOpacity(IBHangar::Cyan()); }
	if (DetailCategory) { DetailCategory->SetText(FText::GetEmpty()); }
	if (DetailRatingLabel) { DetailRatingLabel->SetText(FText::GetEmpty()); }
	if (DetailRating) { DetailRating->SetText(FText::GetEmpty()); }
	if (DetailIcon) { DetailIcon->SetVisibility(ESlateVisibility::Collapsed); }
	if (DetailGlyph) { DetailGlyph->SetGlyph(EIBItemCategory::None); DetailGlyph->SetTint(IBHangar::Fade(IBStyle::TextLo(), .45f)); DetailGlyph->SetVisibility(ESlateVisibility::HitTestInvisible); }
	if (DetailAccent) { DetailAccent->SetBrushColor(IBHangar::Cyan()); }
	if (UIBGlassBorder* Glass = Cast<UIBGlassBorder>(DetailFrame)) { Glass->SetAccentColor(IBHangar::Cyan()); }
	if (DetailFooter) { DetailFooter->SetText(NSLOCTEXT("IBLedger","Footer","BREAKWATER  /  COLLECTION ARCHIVE")); }
	if (DetailStats) { DetailStats->ClearChildren(); }
}

void UIBLedgerScreen::ShowDetails(const UIBItemDefinition* Definition)
{
	if (!Definition) { ResetDetails(); return; }
	const UIBLedgerSubsystem* Ledger = GetLedger();
	const bool bDiscovered = Ledger && Ledger->IsDiscovered(Definition);
	const FLinearColor Rarity = UIBUISettings::Get()->GetRarityColor(Definition->Rarity);
	UTexture2D* Icon = bDiscovered ? Definition->Icon.LoadSynchronous() : nullptr;

	// Undiscovered entries keep the chase honest: category and silhouette only.
	if (DetailRarity)
	{
		DetailRarity->SetText(bDiscovered ? UEnum::GetDisplayValueAsText(Definition->Rarity).ToUpper() : NSLOCTEXT("IBLedger","SealedRecord","SEALED RECORD"));
		DetailRarity->SetColorAndOpacity(bDiscovered ? Rarity : IBStyle::TextLo());
	}
	if (DetailName)
	{
		DetailName->SetText(bDiscovered ? Definition->DisplayName : NSLOCTEXT("IBLedger", "Sealed", "DATA SEALED"));
		DetailName->SetColorAndOpacity(bDiscovered ? IBStyle::TextHi() : IBStyle::TextLo());
	}
	if (DetailCategory)
	{
		DetailCategory->SetText(Definition->EquipSlot != EIBEquipSlot::None
			? FText::Format(NSLOCTEXT("IBLedger","CategorySlot","{0}  ·  {1}"),UEnum::GetDisplayValueAsText(Definition->Category),UEnum::GetDisplayValueAsText(Definition->EquipSlot))
			: UEnum::GetDisplayValueAsText(Definition->Category));
	}
	if (DetailIcon)
	{
		if (Icon) { DetailIcon->SetBrushFromTexture(Icon); }
		DetailIcon->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (DetailGlyph)
	{
		DetailGlyph->SetGlyph(Definition->Category, Definition->EquipSlot);
		DetailGlyph->SetTint(bDiscovered ? Rarity : IBHangar::Fade(IBStyle::TextLo(), .35f));
		DetailGlyph->SetVisibility(Icon ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (DetailRatingLabel && DetailRating)
	{
		const bool bRated = bDiscovered && Definition->BaseClearanceRating > 0;
		DetailRatingLabel->SetText(bRated ? NSLOCTEXT("IBLedger","BaseClearance","BASE CLEARANCE") : FText::GetEmpty());
		DetailRating->SetText(bRated ? FText::AsNumber(Definition->BaseClearanceRating) : FText::GetEmpty());
	}
	if (DetailAccent) { DetailAccent->SetBrushColor(bDiscovered ? Rarity : IBHangar::Edge()); }
	if (UIBGlassBorder* Glass = Cast<UIBGlassBorder>(DetailFrame)) { Glass->SetAccentColor(bDiscovered ? Rarity : IBHangar::Cyan()); }
	if (DetailStats)
	{
		DetailStats->ClearChildren();
		if (bDiscovered) { for (const FIBItemStat& Stat : Definition->Stats) { IBHangar::Stat(WidgetTree, DetailStats, Stat.StatName, Stat.Value); } }
	}
	if (DetailInfo)
	{
		DetailInfo->SetText(bDiscovered
			? FText::FromString(Definition->Description.ToString() + (Definition->Flavor.IsEmpty() ? FString() : TEXT("\n\n") + Definition->Flavor.ToString()))
			: NSLOCTEXT("IBLedger", "SealedHint", "This entry has not been discovered. Recover the item in the field to reveal its record."));
	}
	if (DetailFooter)
	{
		DetailFooter->SetText(bDiscovered ? NSLOCTEXT("IBLedger","Recovered","BREAKWATER  /  RECOVERED RECORD") : NSLOCTEXT("IBLedger","Footer","BREAKWATER  /  COLLECTION ARCHIVE"));
	}
}

void UIBLedgerScreen::HandleTileClicked(UIBItemTileWidget* Tile)
{
	if (!Tile || !Tile->GetDefinition() || !ItemGrid) { return; }
	// Click keeps a record open; hover elsewhere previews and then returns to it.
	SelectedDefinition = Tile->GetDefinition();
	for (UWidget* Child : ItemGrid->GetAllChildren())
	{
		if (UIBItemTileWidget* Other = Cast<UIBItemTileWidget>(Child)) { Other->SetSelected(Other->GetDefinition() == SelectedDefinition); }
	}
	ShowDetails(SelectedDefinition);
}

void UIBLedgerScreen::HandleAll()
{
	bFilterAll = true;
	RebuildGrid();
}

void UIBLedgerScreen::RefreshFilters()
{
	const EIBItemCategory Categories[] = { EIBItemCategory::None, EIBItemCategory::Weapon, EIBItemCategory::Armor, EIBItemCategory::KaijuMaterial };
	for (int32 i = 0; i < FilterButtons.Num() && i < UE_ARRAY_COUNT(Categories); ++i)
	{
		const bool bActive = i == 0 ? bFilterAll : (!bFilterAll && CategoryFilter == Categories[i]);
		IBHangar::StyleRail(FilterButtons[i], bActive);
		if (FilterLabels.IsValidIndex(i) && FilterLabels[i]) { FilterLabels[i]->SetColorAndOpacity(bActive ? IBStyle::TextHi() : IBStyle::TextLo()); }
		if (FilterAccents.IsValidIndex(i) && FilterAccents[i]) { FilterAccents[i]->SetBrushColor(bActive ? IBHangar::Cyan() : FLinearColor::Transparent); }
	}
}

UIBLedgerSubsystem* UIBLedgerScreen::GetLedger() const
{
	const UGameInstance* GI = GetGameInstance();
	return GI ? GI->GetSubsystem<UIBLedgerSubsystem>() : nullptr;
}

void UIBLedgerScreen::NativeScreenOpened()
{
	if (!bDiscoveryBound)
	{
		if (UIBLedgerSubsystem* Ledger = GetLedger())
		{
			// Live update if a public-event drop lands while the book is open.
			Ledger->OnEntryDiscovered.AddDynamic(this, &UIBLedgerScreen::HandleEntryDiscovered);
			bDiscoveryBound = true;
		}
	}
	RebuildGrid();
}

void UIBLedgerScreen::SetCategoryFilter(EIBItemCategory Category)
{
	if (bFilterAll || CategoryFilter != Category)
	{
		bFilterAll = false;
		CategoryFilter = Category;
		RebuildGrid();
	}
}

void UIBLedgerScreen::HandleEntryDiscovered(const UIBItemDefinition* /*Definition*/)
{
	RebuildGrid();
}

void UIBLedgerScreen::RebuildGrid()
{
	if (!ItemGrid) { return; }
	ItemGrid->ClearChildren();
	ResetDetails();
	RefreshFilters();

	UIBLedgerSubsystem* Ledger = GetLedger();
	if (!Ledger || !GridTileClass) { return; }

	int32 CellIndex = 0;
	int32 DiscoveredInCategory = 0;
	int32 TotalInCategory = 0;
	const UIBItemDefinition* FirstDiscovered = nullptr;
	const UIBItemDefinition* FirstEntry = nullptr;
	bool bSelectionVisible = false;

	// Stable reading order: category sections, rising clearance inside each,
	// names as the tiebreak — the book always reads the same way.
	TArray<UIBItemDefinition*> Catalog = Ledger->GetFullCatalog();
	Catalog.Sort([](const UIBItemDefinition& A, const UIBItemDefinition& B)
	{
		if (A.Category != B.Category) { return A.Category < B.Category; }
		if (A.BaseClearanceRating != B.BaseClearanceRating) { return A.BaseClearanceRating < B.BaseClearanceRating; }
		return A.DisplayName.CompareTo(B.DisplayName) < 0;
	});

	for (const UIBItemDefinition* Def : Catalog)
	{
		if (!Def) { continue; }
		if (!bFilterAll && Def->Category != CategoryFilter) { continue; }
		++TotalInCategory;
		if (!FirstEntry) { FirstEntry = Def; }
		bSelectionVisible |= SelectedDefinition == Def;

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }
		Tile->SetPresentationSize(FVector2D(112,100));

		if (Ledger->IsDiscovered(Def))
		{
			++DiscoveredInCategory;
			if (!FirstDiscovered) { FirstDiscovered = Def; }
			FIBItemInstance Preview;            // definition-only display instance
			Preview.Definition = Def;
			Preview.StackCount = 1;
			Tile->SetItem(Preview);
		}
		else
		{
			Tile->SetLocked(Def);
		}

		Tile->OnTileHoverChanged.RemoveDynamic(this, &UIBLedgerScreen::HandleTileHoverChanged);
		Tile->OnTileHoverChanged.AddDynamic(this, &UIBLedgerScreen::HandleTileHoverChanged);
		Tile->OnTileClicked.AddDynamic(this, &UIBLedgerScreen::HandleTileClicked);

		UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns);
		if (GridSlot)
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
	}
	if (!bSelectionVisible) { SelectedDefinition = FirstDiscovered ? FirstDiscovered : FirstEntry; }
	for (UWidget* Child : ItemGrid->GetAllChildren())
	{
		if (UIBItemTileWidget* Tile = Cast<UIBItemTileWidget>(Child)) { Tile->SetSelected(Tile->GetDefinition() == SelectedDefinition); }
	}
	ShowDetails(SelectedDefinition);

	if (CollectionProgress) { CollectionProgress->SetPercent(TotalInCategory > 0 ? float(DiscoveredInCategory) / TotalInCategory : 0.f); }
	if (ProgressText)
	{
		ProgressText->SetText(FText::Format(
			NSLOCTEXT("IBLedger", "Progress", "{0} / {1} CATALOGUED"),
			FText::AsNumber(DiscoveredInCategory), FText::AsNumber(TotalInCategory)));
	}
}

void UIBLedgerScreen::HandleTileHoverChanged(UIBItemTileWidget* Tile, bool bHovered)
{
	if (!Tile) { return; }

	if (bHovered && Tile->GetDefinition())
	{
		const UIBItemDefinition* Def = Tile->GetDefinition();
		const bool bLocked = Tile->IsLockedEntry();
		ShowDetails(Def);
		BP_OnEntryFocused(Def, !bLocked);
	}
	else
	{
		// Back to the record the player keeps open (or the archive idle copy).
		ShowDetails(SelectedDefinition);
		BP_OnEntryUnfocused();
	}
}
