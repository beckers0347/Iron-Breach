#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Combat/IBInteractableInterface.h"
#include "IBCarryablePawn.generated.h"

class AIBCharacter_Infantry;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCarryableVoiceLineSignature, const FText&, Line);

/**
 * Ms. Idris, M1 LANDFALL's carried civilian (Docs/M1_LANDFALL_Mission_Design.md
 * §4.4). Deliberately content-light: a mesh + a line of dialogue text, not a
 * full character. "She navigates her own rescue" (LOCKED) means her voice IS
 * the waypoint system -- no marker, no compass -- so VoiceLines is the whole
 * navigation UI, played by placed trigger volumes calling PlayVoiceLine as the
 * carrier walks the route. Actual VO audio/subtitles hang off OnVoiceLine;
 * this class owns none of that presentation.
 *
 * Not an APawn -- she's never controlled, only carried (AttachToComponent in
 * AIBCharacter_Infantry::BeginCarry). A plain Actor is the honest shape.
 */
UCLASS()
class IRONBREACH_API AIBCarryablePawn : public AActor, public IIBInteractable
{
	GENERATED_BODY()

public:
	AIBCarryablePawn();

	// IIBInteractable
	virtual void Interact_Implementation(AActor* Interactor) override;
	virtual FText GetInteractPrompt_Implementation() const override;

	/** Advances to VoiceLines[Index] and broadcasts it. Wire from placed trigger
	 *  volumes along the carry route (ATriggerBox + a Blueprint event calling this) --
	 *  content/level work, not code; see the mission doc's "Left at the bakery, love"
	 *  example line. Out of range is a no-op (logs a warning) rather than a crash,
	 *  since the route length is still being blocked out. */
	UFUNCTION(BlueprintCallable, Category = "Carry")
	void PlayVoiceLine(int32 Index);

	UPROPERTY(BlueprintAssignable, Category = "Carry|Events")
	FOnCarryableVoiceLineSignature OnVoiceLine;

	/** Placeholder script -- [PROPOSAL] lines per the mission doc §4.4, final
	 *  copy/VO pending Connor/Shane sign-off (doc §13). Author the real sequence
	 *  here once VO is recorded; the LAST line should be empty/unset -- per the
	 *  doc, she stops mid-sentence, no sting, and the final ~100m plays in silence. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Carry")
	TArray<FText> VoiceLines;

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<class UStaticMeshComponent> Mesh; // swap for a skeletal mesh once her model exists

	/** Prompt shown by the interact-hint widget before she's picked up. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Carry")
	FText InteractPrompt;
};
