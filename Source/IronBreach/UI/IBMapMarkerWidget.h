#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "World/IBMapTypes.h"
#include "IBMapMarkerWidget.generated.h"

class UImage;
class UTextBlock;
class UIBMapPOIComponent;
class UIBMapMarkerWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMapMarkerClicked, UIBMapMarkerWidget*, Marker);

/**
 * One pin on the map. C++ fills icon/label from the POI (with a per-type icon
 * table Shane fills in the WBP defaults); BP_OnMarkerUpdated is the styling
 * hook for per-type color/pulse (KaijuAlert wants to throb).
 */
UCLASS()
class IRONBREACH_API UIBMapMarkerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Marker")
	FOnMapMarkerClicked OnMarkerClicked;

	void InitFromPOI(UIBMapPOIComponent* InPOI);

	UFUNCTION(BlueprintPure, Category = "Marker")
	UIBMapPOIComponent* GetPOI() const { return POI.Get(); }

	UFUNCTION(BlueprintCallable, Category = "Marker")
	void SetSelected(bool bNewSelected);

	UFUNCTION(BlueprintPure, Category = "Marker")
	bool IsSelected() const { return bSelected; }

protected:
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Marker", meta = (DisplayName = "On Marker Updated"))
	void BP_OnMarkerUpdated();

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Marker")
	TObjectPtr<UImage> IconImage;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Marker")
	TObjectPtr<UTextBlock> Label;

	/** Fallback icons by POI type — fill in WBP_MapMarker class defaults. A POI's
	 *  IconOverride wins when set. */
	UPROPERTY(EditDefaultsOnly, Category = "Marker")
	TMap<EIBMapPOIType, TSoftObjectPtr<UTexture2D>> TypeIcons;

private:
	TWeakObjectPtr<UIBMapPOIComponent> POI;
	bool bSelected = false;
};
