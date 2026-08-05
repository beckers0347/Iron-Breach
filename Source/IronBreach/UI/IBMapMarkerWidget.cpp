#include "UI/IBMapMarkerWidget.h"
#include "World/IBMapPOIComponent.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

void UIBMapMarkerWidget::InitFromPOI(UIBMapPOIComponent* InPOI)
{
	POI = InPOI;
	if (!InPOI) { return; }

	if (Label)
	{
		Label->SetText(InPOI->DisplayName);
	}

	if (IconImage)
	{
		TSoftObjectPtr<UTexture2D> IconRef = InPOI->IconOverride;
		if (IconRef.IsNull())
		{
			if (const TSoftObjectPtr<UTexture2D>* TypeIcon = TypeIcons.Find(InPOI->POIType))
			{
				IconRef = *TypeIcon;
			}
		}
		if (UTexture2D* IconTexture = IconRef.LoadSynchronous())
		{
			IconImage->SetBrushFromTexture(IconTexture);
		}
	}

	BP_OnMarkerUpdated();
}

void UIBMapMarkerWidget::SetSelected(bool bNewSelected)
{
	if (bSelected != bNewSelected)
	{
		bSelected = bNewSelected;
		BP_OnMarkerUpdated();
	}
}

FReply UIBMapMarkerWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		OnMarkerClicked.Broadcast(this);
		return FReply::Handled(); // eats the click so the map doesn't also start a pan
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}
