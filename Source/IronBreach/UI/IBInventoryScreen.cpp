#include "UI/IBInventoryScreen.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "UI/IBItemTileWidget.h"
#include "UI/IBUISettings.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/TextBlock.h"
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

static UTextBlock* IBMakeLabel(UWidgetTree* Tree, const FText& Text, int32 FontSize, FLinearColor Color)
{
	UTextBlock* Label = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	Label->SetText(Text);
	FSlateFontInfo Font = Label->GetFont();
	Font.Size = FontSize;
	Label->SetFont(Font);
	Label->SetColorAndOpacity(FSlateColor(Color));
	Label->SetShadowOffset(FVector2D(1.f, 1.f));
	Label->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.7f));
	return Label;
}

UIBItemTileWidget* UIBInventoryScreen::MakeWell(UVerticalBox* Column, EIBEquipSlot ForSlot)
{
	UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(GetOwningPlayer(), *GridTileClass);
	if (!Tile) { return nullptr; }
	Tile->SetEmptySlot(ForSlot);
	if (UVerticalBoxSlot* WellSlot = Column->AddChildToVerticalBox(Tile))
	{
		WellSlot->SetPadding(FMargin(0.f, 5.f));
		WellSlot->SetHorizontalAlignment(HAlign_Center);
	}
	return Tile;
}

void UIBInventoryScreen::BuildFallbackLayout()
{
	if (!WidgetTree) { return; }

	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!WidgetTree->RootWidget)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	if (!Root) { return; }

	// Menu, not blackout: the world stays faintly alive behind the screen.
	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Dim->SetBrushColor(FLinearColor(0.01f, 0.015f, 0.03f, 0.78f));
	if (UOverlaySlot* DimSlot = Root->AddChildToOverlay(Dim))
	{
		DimSlot->SetHorizontalAlignment(HAlign_Fill);
		DimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// Header: title left, Clearance Rating right (the POWER number).
	UTextBlock* Title = IBMakeLabel(WidgetTree, NSLOCTEXT("IBInv", "Title", "CHARACTER"), 26, FLinearColor(0.85f, 0.9f, 1.f));
	if (UOverlaySlot* TitleSlot = Root->AddChildToOverlay(Title))
	{
		TitleSlot->SetHorizontalAlignment(HAlign_Left);
		TitleSlot->SetVerticalAlignment(VAlign_Top);
		TitleSlot->SetPadding(FMargin(90.f, 50.f, 0.f, 0.f));
	}

	UVerticalBox* ClearanceBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UTextBlock* ClearanceLabel = IBMakeLabel(WidgetTree, NSLOCTEXT("IBInv", "Clearance", "CLEARANCE"), 12, FLinearColor(0.6f, 0.68f, 0.8f));
	UTextBlock* ClearanceNum = IBMakeLabel(WidgetTree, FText::AsNumber(0), 44, FLinearColor(0.85f, 0.62f, 0.18f)); // Relic amber
	ClearanceBox->AddChildToVerticalBox(ClearanceLabel);
	ClearanceBox->AddChildToVerticalBox(ClearanceNum);
	if (UOverlaySlot* ClearSlot = Root->AddChildToOverlay(ClearanceBox))
	{
		ClearSlot->SetHorizontalAlignment(HAlign_Right);
		ClearSlot->SetVerticalAlignment(VAlign_Top);
		ClearSlot->SetPadding(FMargin(0.f, 44.f, 100.f, 0.f));
	}
	ClearanceText = ClearanceNum;

	// Left column: the three weapon wells.
	UVerticalBox* Weapons = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Weapons->AddChildToVerticalBox(IBMakeLabel(WidgetTree, NSLOCTEXT("IBInv", "Weapons", "WEAPONS"), 13, FLinearColor(0.6f, 0.68f, 0.8f)));
	Tile_WeaponPrimary = MakeWell(Weapons, EIBEquipSlot::WeaponPrimary);
	Tile_WeaponSpecial = MakeWell(Weapons, EIBEquipSlot::WeaponSpecial);
	Tile_WeaponHeavy   = MakeWell(Weapons, EIBEquipSlot::WeaponHeavy);
	if (UOverlaySlot* WeaponSlot = Root->AddChildToOverlay(Weapons))
	{
		WeaponSlot->SetHorizontalAlignment(HAlign_Left);
		WeaponSlot->SetVerticalAlignment(VAlign_Center);
		WeaponSlot->SetPadding(FMargin(120.f, 0.f, 0.f, 60.f));
	}

	// Right column: armor + anti-kaiju gear.
	UVerticalBox* Armor = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Armor->AddChildToVerticalBox(IBMakeLabel(WidgetTree, NSLOCTEXT("IBInv", "Armor", "ARMOR"), 13, FLinearColor(0.6f, 0.68f, 0.8f)));
	Tile_ArmorHead     = MakeWell(Armor, EIBEquipSlot::ArmorHead);
	Tile_ArmorChest    = MakeWell(Armor, EIBEquipSlot::ArmorChest);
	Tile_ArmorArms     = MakeWell(Armor, EIBEquipSlot::ArmorArms);
	Tile_ArmorLegs     = MakeWell(Armor, EIBEquipSlot::ArmorLegs);
	Tile_GearAntiKaiju = MakeWell(Armor, EIBEquipSlot::GearAntiKaiju);
	if (UOverlaySlot* ArmorSlot = Root->AddChildToOverlay(Armor))
	{
		ArmorSlot->SetHorizontalAlignment(HAlign_Right);
		ArmorSlot->SetVerticalAlignment(VAlign_Center);
		ArmorSlot->SetPadding(FMargin(0.f, 0.f, 120.f, 60.f));
	}

	// Bottom center: the backpack grid.
	UVerticalBox* GridBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	GridBox->AddChildToVerticalBox(IBMakeLabel(WidgetTree, NSLOCTEXT("IBInv", "Backpack", "BACKPACK"), 13, FLinearColor(0.6f, 0.68f, 0.8f)));
	UUniformGridPanel* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass());
	Grid->SetSlotPadding(FMargin(4.f));
	GridBox->AddChildToVerticalBox(Grid);
	if (UOverlaySlot* GridSlot = Root->AddChildToOverlay(GridBox))
	{
		GridSlot->SetHorizontalAlignment(HAlign_Center);
		GridSlot->SetVerticalAlignment(VAlign_Bottom);
		GridSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 60.f));
	}
	ItemGrid = Grid;

	// Details pane: bottom-left card, filled on hover.
	UBorder* DetailCard = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	DetailCard->SetBrushColor(FLinearColor(0.02f, 0.03f, 0.05f, 0.9f));
	DetailCard->SetPadding(FMargin(14.f));
	UVerticalBox* DetailBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	DetailCard->SetContent(DetailBox);
	Txt_DetailName = IBMakeLabel(WidgetTree, FText::GetEmpty(), 18, FLinearColor::White);
	Txt_DetailInfo = IBMakeLabel(WidgetTree, FText::GetEmpty(), 11, FLinearColor(0.75f, 0.8f, 0.9f));
	Txt_DetailInfo->SetAutoWrapText(true);
	DetailBox->AddChildToVerticalBox(Txt_DetailName);
	DetailBox->AddChildToVerticalBox(Txt_DetailInfo);
	USizeBox* DetailSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	DetailSize->SetWidthOverride(340.f);
	DetailSize->AddChild(DetailCard);
	if (UOverlaySlot* DetailSlot = Root->AddChildToOverlay(DetailSize))
	{
		DetailSlot->SetHorizontalAlignment(HAlign_Left);
		DetailSlot->SetVerticalAlignment(VAlign_Bottom);
		DetailSlot->SetPadding(FMargin(90.f, 0.f, 0.f, 60.f));
	}
	DetailSize->SetVisibility(ESlateVisibility::Hidden);
	DetailPanel = DetailSize;
}

void UIBInventoryScreen::SetDetails(const UIBItemTileWidget* Tile)
{
	const UIBItemDefinition* Def = Tile ? Tile->GetDefinition() : nullptr;

	if (!Def || !Txt_DetailName || !Txt_DetailInfo)
	{
		if (Txt_DetailName) { Txt_DetailName->SetText(FText::GetEmpty()); }
		if (Txt_DetailInfo) { Txt_DetailInfo->SetText(FText::GetEmpty()); }
		if (DetailPanel)    { DetailPanel->SetVisibility(ESlateVisibility::Hidden); }
		return;
	}

	Txt_DetailName->SetText(Def->DisplayName);
	Txt_DetailName->SetColorAndOpacity(FSlateColor(UIBUISettings::Get()->GetRarityColor(Def->Rarity)));

	FString Info = FString::Printf(TEXT("%s  ·  Clearance %d"),
		*UEnum::GetDisplayValueAsText(Def->Category).ToString(),
		Def->BaseClearanceRating);
	if (!Def->Description.IsEmpty())
	{
		Info += TEXT("\n\n") + Def->Description.ToString();
	}
	Txt_DetailInfo->SetText(FText::FromString(Info));

	if (DetailPanel) { DetailPanel->SetVisibility(ESlateVisibility::HitTestInvisible); }
}

void UIBInventoryScreen::NativeScreenOpened()
{
	BindInventory();
	RebuildAll();
}

void UIBInventoryScreen::NativeScreenClosed()
{
	UnbindInventory();
	BP_OnItemUnfocused();
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

void UIBInventoryScreen::SetCategoryFilter(EIBItemCategory Category)
{
	if (CategoryFilter != Category)
	{
		CategoryFilter = Category;
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
	ItemGrid->ClearChildren();

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
	for (const FIBItemInstance& Item : BoundInventory->GetItemsByCategory(CategoryFilter))
	{
		if (EquippedIds.Contains(Item.InstanceId)) { continue; }

		UIBItemTileWidget* Tile = CreateWidget<UIBItemTileWidget>(this, GridTileClass);
		if (!Tile) { continue; }
		Tile->SetItem(Item);
		WireTile(Tile);

		UUniformGridSlot* GridSlot = ItemGrid->AddChildToUniformGrid(Tile, CellIndex / GridColumns, CellIndex % GridColumns);
		if (GridSlot)
		{
			GridSlot->SetHorizontalAlignment(HAlign_Fill);
			GridSlot->SetVerticalAlignment(VAlign_Fill);
		}
		++CellIndex;
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
		SetDetails(Tile); // native details card (fallback layout / Txt_Detail binds)
		BP_OnItemFocused(Tile->GetItem(), bIsWell);
	}
	else
	{
		SetDetails(nullptr);
		BP_OnItemUnfocused();
	}
}
