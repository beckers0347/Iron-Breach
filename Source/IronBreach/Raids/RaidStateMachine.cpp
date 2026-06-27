#include "Raids/RaidStateMachine.h"

URaidStateMachine::URaidStateMachine()
{
	PrimaryComponentTick.bCanEverTick = false; // Event driven, no ticking needed
	CurrentPhase = ERaidPhase::ArmorBreak;
}

void URaidStateMachine::BeginPlay()
{
	Super::BeginPlay();
	CurrentPhase = ERaidPhase::ArmorBreak;
}

void URaidStateMachine::AdvanceRaidPhase()
{
	if (CurrentPhase == ERaidPhase::Completed) return;

	// Advance to the next enum state by incrementing the uint8 value
	CurrentPhase = static_cast<ERaidPhase>(static_cast<uint8>(CurrentPhase) + 1);

	// Broadcast the phase change to UI, Music Managers, and Spawners
	OnPhaseChanged.Broadcast(CurrentPhase);
}