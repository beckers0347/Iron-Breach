#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "IBInteractableInterface.generated.h"

/**
 * Generic world-interaction contract -- the coffee pot / log / dry-fire rig in
 * M1's QUIET beat, and Ms. Idris in the AFTERMATH carry, all implement this
 * rather than each inventing their own overlap-and-keypress plumbing. See
 * AIBCharacter_Infantry::Interact() for the caller side (a short trace from
 * the first-person camera, ETriggerEvent::Started on InteractAction).
 *
 * Deliberately NOT restricted to weapon/item pickups -- IBLootPickup predates
 * this interface and keeps its own overlap-based flow; retrofitting it is a
 * separate pass, not required for M1.
 */
UINTERFACE(BlueprintType)
class IRONBREACH_API UIBInteractable : public UInterface
{
	GENERATED_BODY()
};

class IRONBREACH_API IIBInteractable
{
	GENERATED_BODY()

public:
	/** Called on the trace-hit actor when the interactor presses Interact. */
	UFUNCTION(BlueprintNativeEvent, Category = "Interact")
	void Interact(AActor* Interactor);

	/** Prompt text for the interact-hint widget ("Pour coffee", "Carry"). Empty = not currently interactable. */
	UFUNCTION(BlueprintNativeEvent, Category = "Interact")
	FText GetInteractPrompt() const;
};
