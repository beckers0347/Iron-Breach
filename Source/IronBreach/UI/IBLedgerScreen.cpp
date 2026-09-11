#include "UI/IBLedgerScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBUISettings.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBoxSlot.h"
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
		const auto Page = IBMenuLayout::Begin(WidgetTree,
			NSLOCTEXT("IBLedger", "Title", "THE LEDGER"),
			NSLOCTEXT("IBLedger", "Kicker", "BREAKWATER / COLLECTION ARCHIVE"),
			NSLOCTEXT("IBLedger", "Controls", "HOVER / INSPECT ENTRY     Q E / SWITCH MENU     ESC / RETURN"));
		if (!Page.Body) { return; }
		ProgressText = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 20);
		Page.HeaderRight->AddChildToVerticalBox(ProgressText);
		CollectionProgress = WidgetTree->ConstructWidget<UProgressBar>();
		CollectionProgress->SetFillColorAndOpacity(IBStyle::Amber());
		FProgressBarStyle ProgressStyle = CollectionProgress->GetWidgetStyle();
		ProgressStyle.BackgroundImage = IBStyle::RoundedBrush(FLinearColor(.025f, .06f, .065f), 0);
		ProgressStyle.FillImage = IBStyle::RoundedBrush(FLinearColor::White, 0);
		CollectionProgress->SetWidgetStyle(ProgressStyle);
		USizeBox* ProgressSize = IBMenuLayout::Width(WidgetTree, CollectionProgress, 260);
		ProgressSize->SetHeightOverride(4);
		Page.HeaderRight->AddChildToVerticalBox(ProgressSize)->SetPadding(FMargin(0, 10, 0, 0));
		UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
		Page.Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		UVerticalBox* Catalog = WidgetTree->ConstructWidget<UVerticalBox>();
		IBMenuLayout::Section(WidgetTree, Catalog, NSLOCTEXT("IBLedger", "Catalog", "01 / FIELD DISCOVERIES"));
		UHorizontalBox* Filters = WidgetTree->ConstructWidget<UHorizontalBox>();
		const FText Labels[] = { NSLOCTEXT("IBLedger", "All", "ALL"), NSLOCTEXT("IBLedger", "Weapons", "WEAPONS"),
			NSLOCTEXT("IBLedger", "Armor", "ARMOR"), NSLOCTEXT("IBLedger", "Materials", "MATERIALS") };
		for (const FText& Label : Labels)
		{
			UButton* Button = IBMenuLayout::Button(WidgetTree, Label);
			Filters->AddChildToHorizontalBox(Button)->SetPadding(FMargin(0, 0, 8, 0));
			FilterButtons.Add(Button);
		}
		FilterButtons[0]->OnClicked.AddDynamic(this, &UIBLedgerScreen::HandleAll);
		FilterButtons[1]->OnClicked.AddDynamic(this, &UIBLedgerScreen::HandleWeapons);
		FilterButtons[2]->OnClicked.AddDynamic(this, &UIBLedgerScreen::HandleArmor);
		FilterButtons[3]->OnClicked.AddDynamic(this, &UIBLedgerScreen::HandleMaterials);
		Catalog->AddChildToVerticalBox(Filters)->SetPadding(FMargin(0, 0, 0, 18));
		ItemGrid = WidgetTree->ConstructWidget<UUniformGridPanel>();
		ItemGrid->SetSlotPadding(FMargin(4));
		GridColumns = 8;
		IBMenuLayout::Scroll(WidgetTree, Catalog, ItemGrid);
		CastChecked<UScrollBoxSlot>(ItemGrid->Slot)->SetHorizontalAlignment(HAlign_Left);
		Catalog->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
			NSLOCTEXT("IBLedger", "CatalogHint", "SEALED ENTRIES ARE REVEALED THROUGH DISCOVERY."), 11))->SetPadding(FMargin(0, 14, 0, 0));
		UHorizontalBoxSlot* CatalogSlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, Catalog));
		CatalogSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		CatalogSlot->SetPadding(FMargin(0, 0, 16, 0));
		UVerticalBox* Details = WidgetTree->ConstructWidget<UVerticalBox>();
		IBMenuLayout::Section(WidgetTree, Details, NSLOCTEXT("IBLedger", "Record", "02 / ARCHIVE RECORD"));
		DetailName = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 25);
		DetailName->SetAutoWrapText(true);
		Details->AddChildToVerticalBox(DetailName)->SetPadding(FMargin(0, 8, 0, 18));
		DetailInfo = IBMenuLayout::Text(WidgetTree, FText::GetEmpty(), 14);
		DetailInfo->SetAutoWrapText(true);
		IBMenuLayout::Scroll(WidgetTree, Details, DetailInfo);
		Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, IBMenuLayout::Card(WidgetTree, Details), 350));
		ResetDetails();
		RefreshFilters();
	}
}

void UIBLedgerScreen::ResetDetails()
{
	if (DetailName) { DetailName->SetText(NSLOCTEXT("IBLedger", "Idle", "BUILD THE ARCHIVE")); DetailName->SetColorAndOpacity(IBStyle::TextHi()); }
	if (DetailInfo) { DetailInfo->SetText(NSLOCTEXT("IBLedger", "IdleHint", "Every discovery becomes part of the record.\n\nHover over an entry to inspect its recovered data.")); }
}

void UIBLedgerScreen::HandleAll()
{
	bFilterAll = true;
	RebuildGrid();
}

void UIBLedgerScreen::RefreshFilters()
{
	const EIBItemCategory Categories[] = { EIBItemCategory::None, EIBItemCategory::Weapon, EIBItemCategory::Armor, EIBItemCategory::KaijuMaterial };
	for (int32 i = 0; i < FilterButtons.Num(); ++i)
		IBMenuLayout::StyleButton(FilterButtons[i], i == 0 ? bFilterAll : (!bFilterAll && CategoryFilter == Categories[i]));
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

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }

		if (Ledger->IsDiscovered(Def))
		{
			++DiscoveredInCategory;
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

		UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns);
		if (GridSlot)
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
	}

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
		if (DetailName)
		{
			DetailName->SetText(bLocked ? NSLOCTEXT("IBLedger", "Sealed", "DATA SEALED") : Def->DisplayName);
			DetailName->SetColorAndOpacity(bLocked ? IBStyle::TextLo() : UIBUISettings::Get()->GetRarityColor(Def->Rarity));
		}
		if (DetailInfo)
		{
			DetailInfo->SetText(bLocked ? NSLOCTEXT("IBLedger", "SealedHint", "This entry has not been discovered. Recover the item in the field to reveal its record.")
				: FText::FromString(UEnum::GetDisplayValueAsText(Def->Category).ToString() + TEXT("\n\n") + Def->Description.ToString()
					+ (Def->Flavor.IsEmpty() ? FString() : TEXT("\n\n") + Def->Flavor.ToString())));
		}
		BP_OnEntryFocused(Def, !bLocked);
	}
	else
	{
		ResetDetails();
		BP_OnEntryUnfocused();
	}
}
