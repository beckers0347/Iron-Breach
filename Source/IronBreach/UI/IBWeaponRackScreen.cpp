// IBWeaponRackScreen.cpp
#include "UI/IBWeaponRackScreen.h"
#include "UI/IBStyleKit.h"
#include "UI/IBItemTileWidget.h"
#include "Items/IBWeaponRack.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBPlayerState.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"
#include "GameFramework/PlayerController.h"

void UIBWeaponRackScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	if (!GridTileClass) { GridTileClass = UIBItemTileWidget::StaticClass(); }

	BuildFallbackLayout();

	if (CloseButton)
	{
		CloseButton->OnClicked.RemoveDynamic(this, &UIBWeaponRackScreen::HandleCloseClicked);
		CloseButton->OnClicked.AddDynamic(this, &UIBWeaponRackScreen::HandleCloseClicked);
	}
	if (StoreButton)
	{
		StoreButton->OnClicked.RemoveDynamic(this, &UIBWeaponRackScreen::HandleStoreClicked);
		StoreButton->OnClicked.AddDynamic(this, &UIBWeaponRackScreen::HandleStoreClicked);
	}
}

void UIBWeaponRackScreen::HandleStoreClicked()
{
	if (!Rack) { return; }

	APlayerController* PC = GetOwningPlayer();
	AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	UIBInventoryComponent* Inventory = PS ? PS->GetInventory() : nullptr;
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	AIBCharacter_Infantry* Infantry = Cast<AIBCharacter_Infantry>(Pawn);
	if (!Inventory || !Infantry) { return; }

	// Store whatever is in the ACTIVE well — matches what's in your hands.
	FIBItemInstance Equipped;
	if (!Inventory->GetEquippedItem(Infantry->GetActiveWeaponSlot(), Equipped) || !Equipped.IsValid())
	{
		return; // empty hands, nothing to store
	}

	Inventory->RequestStoreToRack(Rack, Equipped.InstanceId);
	RebuildGrid(); // optimistic; OnStockChanged re-confirms when the deposit replicates
}

void UIBWeaponRackScreen::BuildFallbackLayout()
{
	if (ItemGrid || !WidgetTree) { return; } // Already bound from a WBP child, or no tree yet.

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

	UHorizontalBox* HeaderRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	UTextBlock* Title = IBStyle::MakeTitle(WidgetTree, NSLOCTEXT("IBWeaponRack", "Title", "WEAPON RACK"));
	if (UHorizontalBoxSlot* TitleSlot = HeaderRow->AddChildToHorizontalBox(Title))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetPadding(FMargin(0.f, 0.f, 40.f, 0.f));
	}

	UButton* Store = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWeaponRack", "Store", "STORE EQUIPPED"), 12, /*bAccent=*/true);
	if (UHorizontalBoxSlot* StoreSlot = HeaderRow->AddChildToHorizontalBox(Store))
	{
		StoreSlot->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));
		StoreSlot->SetVerticalAlignment(VAlign_Center);
	}
	StoreButton = Store;

	UButton* Close = IBStyle::MakeButton(WidgetTree, NSLOCTEXT("IBWeaponRack", "Close", "CLOSE (ESC)"), 12);
	if (UHorizontalBoxSlot* CloseSlot = HeaderRow->AddChildToHorizontalBox(Close))
	{
		CloseSlot->SetHorizontalAlignment(HAlign_Right);
		CloseSlot->SetVerticalAlignment(VAlign_Center);
	}
	CloseButton = Close;

	if (UVerticalBoxSlot* HeaderSlot = Column->AddChildToVerticalBox(HeaderRow))
	{
		HeaderSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));
	}
	TitleText = Title;

	UUniformGridPanel* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass());
	Grid->SetSlotPadding(FMargin(4.f));
	Column->AddChildToVerticalBox(Grid);
	ItemGrid = Grid;

	UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	Hint->SetText(NSLOCTEXT("IBWeaponRack", "Hint", "CLICK A WEAPON TO TAKE IT  ·  STORE EQUIPPED RACKS THE GUN IN YOUR HANDS"));
	FSlateFontInfo HintFont = Hint->GetFont();
	HintFont.Size = 10;
	Hint->SetFont(HintFont);
	Hint->SetColorAndOpacity(FSlateColor(FLinearColor(0.5f, 0.56f, 0.68f)));
	if (UVerticalBoxSlot* HintSlot = Column->AddChildToVerticalBox(Hint))
	{
		HintSlot->SetPadding(FMargin(0.f, 10.f, 0.f, 0.f));
		HintSlot->SetHorizontalAlignment(HAlign_Center);
	}

	if (UOverlaySlot* ColumnSlot = Root->AddChildToOverlay(Column))
	{
		ColumnSlot->SetHorizontalAlignment(HAlign_Center);
		ColumnSlot->SetVerticalAlignment(VAlign_Center);
	}
}

void UIBWeaponRackScreen::InitForRack(AIBWeaponRack* InRack)
{
	Rack = InRack;

	if (Rack && !bStockBound)
	{
		Rack->OnStockChanged.AddDynamic(this, &UIBWeaponRackScreen::HandleStockChanged);
		bStockBound = true;
	}

	RebuildGrid();
	BP_OnOpened();
}

void UIBWeaponRackScreen::NativeDestruct()
{
	if (Rack && bStockBound)
	{
		Rack->OnStockChanged.RemoveDynamic(this, &UIBWeaponRackScreen::HandleStockChanged);
		bStockBound = false;
	}
	Super::NativeDestruct();
}

FReply UIBWeaponRackScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		RequestClose();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UIBWeaponRackScreen::HandleCloseClicked()
{
	RequestClose();
}

void UIBWeaponRackScreen::RequestClose()
{
	BP_OnClosed();

	// The rack owns opening/closing bookkeeping (ActivePicker pointer, restoring
	// game input mode) — same reasoning as why AIBLootPickup's collection logic
	// lives on the pickup, not scattered into whatever widget/pawn touches it.
	if (Rack)
	{
		Rack->NotifyPickerClosed();
	}
	else
	{
		RemoveFromParent();
	}
}

void UIBWeaponRackScreen::HandleStockChanged()
{
	RebuildGrid();
}

void UIBWeaponRackScreen::RebuildGrid()
{
	if (!ItemGrid || !Rack || !GridTileClass) { return; }

	ItemGrid->ClearChildren();

	int32 CellIndex = 0;
	for (UIBItemDefinition* Def : Rack->GetStockedWeapons())
	{
		if (!Def) { continue; }

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }

		// Definition-only preview instance — there's no owned FIBItemInstance yet,
		// the item is still sitting on the rack (same trick the Ledger screen uses
		// for its "discovered but not owned" tiles).
		FIBItemInstance Preview;
		Preview.Definition = Def;
		Preview.StackCount = 1;
		Tile->SetItem(Preview);

		Tile->OnTileClicked.RemoveDynamic(this, &UIBWeaponRackScreen::HandleTileClicked);
		Tile->OnTileClicked.AddDynamic(this, &UIBWeaponRackScreen::HandleTileClicked);

		if (UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns))
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
	}
}

void UIBWeaponRackScreen::HandleTileClicked(UIBItemTileWidget* Tile)
{
	if (!Tile || !Rack) { return; }

	const UIBItemDefinition* Clicked = Tile->GetDefinition();
	if (!Clicked) { return; }

	const int32 Index = Rack->GetStockedWeapons().IndexOfByKey(Clicked);
	if (Index == INDEX_NONE) { return; }

	APlayerController* PC = GetOwningPlayer();
	AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	UIBInventoryComponent* Inventory = PS ? PS->GetInventory() : nullptr;
	if (!Inventory) { return; }

	Inventory->RequestTakeFromRack(Rack, Index);

	// Optimistic local refresh for the infinite-stock case (nothing actually
	// changed to replicate); the non-infinite case gets a real refresh from
	// OnStockChanged once the server's removal replicates back.
	RebuildGrid();
}
