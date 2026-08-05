#include "UI/IBLedgerScreen.h"
#include "Items/IBLedgerSubsystem.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBItemTileWidget.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
#include "Engine/GameInstance.h"

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
	if (CategoryFilter != Category)
	{
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

	for (const UIBItemDefinition* Def : Ledger->GetFullCatalog())
	{
		if (!Def || Def->Category != CategoryFilter) { continue; }
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
