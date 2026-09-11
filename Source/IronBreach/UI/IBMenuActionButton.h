#pragma once
#include "CoreMinimal.h"
#include "Components/Button.h"
#include "IBMenuActionButton.generated.h"

/** Local UI actions with payloads; handlers bind weakly to their owning screen. */
UCLASS()
class IRONBREACH_API UIBMenuActionButton : public UButton
{
    GENERATED_BODY()
public:
    void BindAction(FSimpleDelegate InAction)
    {
        Action = MoveTemp(InAction);
        OnClicked.AddUniqueDynamic(this, &UIBMenuActionButton::Invoke);
    }
private:
    UFUNCTION() void Invoke() { Action.ExecuteIfBound(); }
    FSimpleDelegate Action;
};
