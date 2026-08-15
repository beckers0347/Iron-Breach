#include "UI/IBLootToastWidget.h"
#include "IronBreach.h"
#include "Items/IBInventoryComponent.h"
#include "Items/IBItemDefinition.h"
#include "Items/IBPlayerState.h"
#include "UI/IBUISettings.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

void UIBLootToastWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (WidgetTree && !ToastBox)
	{
		UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
		if (!WidgetTree->RootWidget)
		{
			Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
			WidgetTree->RootWidget = Root;
		}
		if (Root)
		{
			ToastBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
			if (UOverlaySlot* BoxSlot = Root->AddChildToOverlay(ToastBox))
			{
				BoxSlot->SetHorizontalAlignment(HAlign_Right);
				BoxSlot->SetVerticalAlignment(VAlign_Bottom);
				BoxSlot->SetPadding(FMargin(0.f, 0.f, 48.f, 120.f));
			}
		}
	}

	SetVisibility(ESlateVisibility::HitTestInvisible);
	TryBindInventory();
}

void UIBLootToastWidget::NativeDestruct()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(FindInventoryTimer);
	}
	if (BoundInventory.IsValid())
	{
		BoundInventory->OnItemGranted.RemoveDynamic(this, &UIBLootToastWidget::HandleItemGranted);
	}
	Super::NativeDestruct();
}

void UIBLootToastWidget::TryBindInventory()
{
	APlayerController* PC = GetOwningPlayer();
	const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	UIBInventoryComponent* Inventory = PS ? PS->GetInventory() : nullptr;

	if (!Inventory)
	{
		// PlayerState replication can lag the widget — retry until it lands.
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(FindInventoryTimer, this, &UIBLootToastWidget::TryBindInventory, 0.5f, false);
		}
		return;
	}

	BoundInventory = Inventory;
	Inventory->OnItemGranted.AddDynamic(this, &UIBLootToastWidget::HandleItemGranted);
}

void UIBLootToastWidget::HandleItemGranted(const FIBItemInstance& Item)
{
	if (!ToastBox || !WidgetTree || !Item.Definition) { return; }

	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	const FString Line = (Item.StackCount > 1)
		? FString::Printf(TEXT("+ %s  x%d"), *Item.Definition->DisplayName.ToString(), Item.StackCount)
		: FString::Printf(TEXT("+ %s"), *Item.Definition->DisplayName.ToString());
	Text->SetText(FText::FromString(Line));

	FSlateFontInfo Font = Text->GetFont();
	Font.Size = 16;
	Text->SetFont(Font);
	Text->SetShadowOffset(FVector2D(1.f, 1.f));
	Text->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.8f));
	Text->SetColorAndOpacity(FSlateColor(UIBUISettings::Get()->GetRarityColor(Item.Definition->Rarity)));

	if (UVerticalBoxSlot* LineSlot = ToastBox->AddChildToVerticalBox(Text))
	{
		LineSlot->SetPadding(FMargin(0.f, 2.f));
		LineSlot->SetHorizontalAlignment(HAlign_Right);
	}

	FToastLine Entry; Entry.Text = Text;
	Lines.Add(Entry);
}

void UIBLootToastWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	for (int32 i = Lines.Num() - 1; i >= 0; --i)
	{
		FToastLine& Line = Lines[i];
		Line.Age += InDeltaTime;

		UTextBlock* Text = Line.Text.Get();
		if (!Text) { Lines.RemoveAt(i); continue; }

		if (Line.Age >= ToastLifetime)
		{
			Text->RemoveFromParent();
			Lines.RemoveAt(i);
		}
		else if (Line.Age > ToastLifetime - ToastFadeTime)
		{
			Text->SetRenderOpacity((ToastLifetime - Line.Age) / ToastFadeTime);
		}
	}
}
