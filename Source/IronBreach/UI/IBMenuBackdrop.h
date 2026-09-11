#pragma once

#include "CoreMinimal.h"
#include "Components/Widget.h"
#include "IBMenuBackdrop.generated.h"

/** Decorative, non-interactive background for native menu layouts. */
UCLASS()
class IRONBREACH_API UIBMenuBackdrop : public UWidget
{
	GENERATED_BODY()
protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
};
