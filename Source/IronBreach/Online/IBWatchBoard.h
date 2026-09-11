#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "Subsystems/WorldSubsystem.h"
#include "IBWatchBoard.generated.h"

class APlayerState;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBWatchBoardChanged);

/**
 * THE WATCH — the breach board's shared state. One per world, spawned by the
 * server (UIBWatchSubsystem), always relevant, so every screen — lobby or
 * mid-mission — reads the same four facts:
 *
 *   Proposed  : what someone on the squad wants to answer, and who said so
 *   Armed     : what the host confirmed (the host proposing IS a confirm)
 *   DeployAt  : server time the squad travels (countdown; host can still cancel)
 *   Current   : the destination this world is
 *
 * Rule agreed with Connor: anyone can pick, the host confirms. Clients reach
 * the server through AIBPlayerState::WatchPropose/Confirm/Cancel (owned
 * connection -> Server RPC -> here). Server-side truth, replication informs
 * (ADR-002). The travel itself goes through UIBSessionSubsystem::IBDeployTo so
 * the session survives the map change.
 */
UCLASS(NotBlueprintable)
class IRONBREACH_API AIBWatchBoard : public AInfo
{
	GENERATED_BODY()

public:
	AIBWatchBoard();

	/** The world's board (server-spawned; clients see it once it replicates). */
	static AIBWatchBoard* Get(const UWorld* World);

	// ---- Server API (PlayerState RPC layer calls these; authority only) ----
	void ServerPropose(APlayerState* By, FName DestinationId);
	void ServerConfirm(APlayerState* By);
	void ServerCancel(APlayerState* By);

	/** Listen-server host (or the standalone player): the local controller on the authority. */
	bool IsHostPlayer(const APlayerState* PS) const;

	// ---- Read (any side) ----
	FName GetProposedId() const { return ProposedId; }
	const FString& GetProposedByName() const { return ProposedByName; }
	int32 GetProposedByPlayerId() const { return ProposedByPlayerId; }
	FName GetArmedId() const { return ArmedId; }
	FName GetCurrentId() const { return CurrentId; }
	bool IsArmed() const { return !ArmedId.IsNone(); }
	/** Seconds until the squad travels; < 0 when nothing is armed. */
	float GetSecondsToDeploy() const;

	UPROPERTY(BlueprintAssignable, Category = "Watch")
	FOnIBWatchBoardChanged OnChanged;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	UFUNCTION()
	void OnRep_Board();

	UPROPERTY(ReplicatedUsing = OnRep_Board) FName ProposedId;
	UPROPERTY(ReplicatedUsing = OnRep_Board) FString ProposedByName;
	UPROPERTY(ReplicatedUsing = OnRep_Board) int32 ProposedByPlayerId = -1;
	UPROPERTY(ReplicatedUsing = OnRep_Board) FName ArmedId;
	/** Server world time of the travel; < 0 when nothing is armed. Clients read it against GameState server time. */
	UPROPERTY(ReplicatedUsing = OnRep_Board) float DeployAtServerTime = -1.f;
	UPROPERTY(ReplicatedUsing = OnRep_Board) FName CurrentId;

private:
	void Arm(FName Id);
	void ClearAll();
	void FireDeploy();
	/** Server-side OnRep stand-in so the host's own screen updates too. */
	void Notify();

	float ServerNow() const;
	bool bDeployFired = false;
};

/**
 * Puts one AIBWatchBoard in every game world the server runs (lobby, mission,
 * standalone menu). Cheap, and it means "return to the Watch" works from
 * anywhere without a GameMode class change.
 */
UCLASS()
class IRONBREACH_API UIBWatchSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override
	{
		return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
	}
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	AIBWatchBoard* GetBoard() const { return Board.Get(); }

private:
	void OpenLobbyMenu();
	FTimerHandle LobbyMenuTimer;
	TWeakObjectPtr<AIBWatchBoard> Board;
	TWeakObjectPtr<class UIBWatchScreen> DevScreen;
};
