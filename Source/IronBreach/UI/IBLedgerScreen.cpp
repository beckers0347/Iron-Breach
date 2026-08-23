#include "UI/IBLedgerScreen.h"
#include "UI/IBStyleKit.h"
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

	// Bare WBP: dim sheet, title, progress line, catalog grid — the chase board.
	if (!ItemGrid && WidgetTree)
	{
		UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
		if (!WidgetTree->RootWidget)
		{
			Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
			WidgetTree->RootWidget = Root;
		}
		if (!Root) { return; }

		UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Dim->SetBrushColor(FLinearColor(0.01f, 0.015f, 0.03f, 0.78f));
		if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
		{
			DimSlot->SetHorizontalAlignment(HAlign_Fill);
			DimSlot->SetVerticalAlignment(VAlign_Fill);
		}

		UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());

		UTextBlock* Title = IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBLedger", "Title", "THE LEDGER"));
		Column->AddChildToVerticalBox(Title);

		UBorder* Accent = IBStyle::MakeAccentBar(WidgetTree, IBStyle::Amber());
		Accent->SetPadding(FMargin(0.f, 1.5f));
		if (UVerticalBoxSlot* AccentSlot = Column->AddChildToVerticalBox(Accent))
		{
			AccentSlot->SetPadding(FMargin(0.f, 6.f, 200.f, 0.f));
		}

		UTextBlock* Progress = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 12, IBStyle::TextLo(), 300);
		if (UVerticalBoxSlot* ProgSlot = Column->AddChildToVerticalBox(Progress))
		{
			ProgSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 14.f));
		}
		ProgressText = Progress;

		UUniformGridPanel* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass());
		Grid->SetSlotPadding(FMargin(4.f));
		Column->AddChildToVerticalBox(Grid);
		ItemGrid = Grid;

		if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Column))
		{
			ColumnSlot->SetHorizontalAlignment(HAlign_Center);
			ColumnSlot->SetVerticalAlignment(VAlign_Center);
		}
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
		BP_OnEntryFocused(Tile->GetDefinition(), !Tile->IsLockedEntry());
	}
	else
	{
		BP_OnEntryUnfocused();
	}
}
