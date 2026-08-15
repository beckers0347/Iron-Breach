#include "UI/IBObjectiveWidget.h"
#include "IronBreach.h"
#include "Components/TextBlock.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "TimerManager.h"

void UIBObjectiveWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// Bare widget: build the single centered line ourselves.
	if (!Txt_Objective && WidgetTree)
	{
		UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
		if (!WidgetTree->RootWidget)
		{
			Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
			WidgetTree->RootWidget = Root;
		}
		if (Root)
		{
			UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
			FSlateFontInfo Font = Text->GetFont();
			Font.Size = 20;
			Text->SetFont(Font);
			Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 0.95f, 1.0f)));
			Text->SetShadowOffset(FVector2D(1.5f, 1.5f));
			Text->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.8f));
			if (UOverlaySlot* TextSlot = Root->AddChildToOverlay(Text))
			{
				TextSlot->SetHorizontalAlignment(HAlign_Center);
				TextSlot->SetVerticalAlignment(VAlign_Top);
				TextSlot->SetPadding(FMargin(0.f, 48.f, 0.f, 0.f));
			}
			Txt_Objective = Text;
		}
	}

	TryBindDirector();
}

void UIBObjectiveWidget::NativeDestruct()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(FindDirectorTimer);
	}
	if (Director.IsValid())
	{
		Director->OnMissionPhaseChanged.RemoveDynamic(this, &UIBObjectiveWidget::HandleMissionPhase);
	}
	Super::NativeDestruct();
}

void UIBObjectiveWidget::TryBindDirector()
{
	UWorld* World = GetWorld();
	if (!World) { return; }

	for (TActorIterator<AIBMissionDirector> It(World); It; ++It)
	{
		Director = *It;
		Director->OnMissionPhaseChanged.AddDynamic(this, &UIBObjectiveWidget::HandleMissionPhase);
		RefreshText();
		return;
	}

	// No director yet (client replication lag, or a mission-less world).
	// Stay hidden and look again shortly; give up quietly in menu worlds.
	SetVisibility(ESlateVisibility::Hidden);
	World->GetTimerManager().SetTimer(FindDirectorTimer, this, &UIBObjectiveWidget::TryBindDirector, 0.5f, false);
}

void UIBObjectiveWidget::HandleMissionPhase(EIBMissionPhase NewPhase)
{
	RefreshText();
	BP_OnObjectiveChanged(NewPhase);
}

void UIBObjectiveWidget::RefreshText()
{
	if (!Director.IsValid()) { return; }

	SetVisibility(ESlateVisibility::HitTestInvisible);
	if (Txt_Objective)
	{
		Txt_Objective->SetText(Director->GetObjectiveText());

		// Phase color: warning amber for emergence, victory green for secured.
		switch (Director->GetMissionPhase())
		{
		case EIBMissionPhase::Emergence:
			Txt_Objective->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.55f, 0.15f))); break;
		case EIBMissionPhase::Secured:
			Txt_Objective->SetColorAndOpacity(FSlateColor(FLinearColor(0.4f, 1.0f, 0.5f))); break;
		default:
			Txt_Objective->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 0.95f, 1.0f))); break;
		}
	}
}
