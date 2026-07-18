#include "InfantryAnimInstance.h"
#include "Infantry/IBCharacter_Infantry.h" // Pulls in your specific character class

void UInfantryAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);

    // Get the character that owns this animation model and cast it to your specific class
    AIBCharacter_Infantry* MyCharacter = Cast<AIBCharacter_Infantry>(TryGetPawnOwner());

    // If the character is valid, grab their weapon variable
    if (MyCharacter)
    {
        // IMPORTANT: Change "bIsArmed" if your variable in IBCharacter_Infantry is named something else!
        bIsHoldingGun = MyCharacter->bIsArmed;

        MovementSpeed = MyCharacter->GetVelocity().Size2D();
    }
}