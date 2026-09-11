#pragma once

#include "CoreMinimal.h"
#include "Components/Button.h"
#include "IBMenuNavButton.generated.h"

class UIBMenuSubsystem;

/** Mouse navigation through the same registry used by Q/E. */
UCLASS()
class IRONBREACH_API UIBMenuNavButton : public UButton
{
	GENERATED_BODY()
public:
	void Init(UIBMenuSubsystem* InMenu, FName InScreenId);
private:
	UFUNCTION() void OpenDestination();
	UPROPERTY(Transient) TWeakObjectPtr<UIBMenuSubsystem> Menu;
	FName Destination;
};
