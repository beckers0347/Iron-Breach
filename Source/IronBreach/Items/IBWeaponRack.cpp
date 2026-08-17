// IBWeaponRack.cpp
#include "Items/IBWeaponRack.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBWeaponRackScreen.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InputComponent.h"
#include "EnhancedInputComponent.h"
#include "InputAction.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Blueprint/UserWidget.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
#include "IronBreach.h"

AIBWeaponRack::AIBWeaponRack()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;

	RackMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RackMesh"));
	SetRootComponent(RackMesh);
	RackMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	RackMesh->SetCollisionResponseToAllChannels(ECR_Block);

	// Best-effort default so the actor isn't meshless out of the box; Shane can
	// swap it in the BP. Load failure just leaves the slot empty, not a compile issue.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> DefaultRackMesh(
		TEXT("/Game/LevelPrototyping/AIModels/SM_WeaponRack.SM_WeaponRack"));
	if (DefaultRackMesh.Succeeded())
	{
		RackMesh->SetStaticMesh(DefaultRackMesh.Object);
	}

	InteractionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("InteractionSphere"));
	InteractionSphere->SetupAttachment(RootComponent);
	InteractionSphere->InitSphereRadius(InteractionRadius);
	InteractionSphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	InteractionSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
	InteractionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void AIBWeaponRack::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBWeaponRack, StockedWeapons);
}

void AIBWeaponRack::BeginPlay()
{
	Super::BeginPlay();

	InteractionSphere->SetSphereRadius(InteractionRadius);
	InteractionSphere->OnComponentBeginOverlap.AddDynamic(this, &AIBWeaponRack::HandleBeginOverlap);
	InteractionSphere->OnComponentEndOverlap.AddDynamic(this, &AIBWeaponRack::HandleEndOverlap);
}

void AIBWeaponRack::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (FocusedPawn)
	{
		UnbindInputFor(FocusedPawn);
	}
	ClosePicker();

	Super::EndPlay(EndPlayReason);
}

void AIBWeaponRack::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	APawn* Pawn = Cast<APawn>(OtherActor);

	// Only the machine that actually controls this pawn should get a prompt /
	// bind input for it -- the server sees every pawn overlap, remote clients
	// only their own. Without this gate, a listen host would bind input for
	// every player who walks up to the rack.
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	FocusedPawn = Pawn;
	BindInputFor(Pawn);
	BP_OnFocusChanged(true);
}

void AIBWeaponRack::HandleEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!Pawn || Pawn != FocusedPawn)
	{
		return;
	}

	UnbindInputFor(Pawn);
	FocusedPawn = nullptr;
	BP_OnFocusChanged(false);
	ClosePicker();
}

void AIBWeaponRack::BindInputFor(APawn* Pawn)
{
	APlayerController* PC = Pawn->GetController<APlayerController>();
	if (!PC || !InteractAction)
	{
		// Unassigned InteractAction is a valid, logged-nowhere state on purpose --
		// same "guarded optional action" convention as MoveAction/LookAction on
		// the Character. Assign IA_Interact on the placed BP_WeaponRack to activate.
		return;
	}

	EnableInput(PC);
	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(InputComponent))
	{
		EIC->BindAction(InteractAction, ETriggerEvent::Started, this, &AIBWeaponRack::HandleInteract);
	}
	else
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("%s: [WeaponRack] EnableInput did not produce an EnhancedInputComponent -- check DefaultInputComponentClass in DefaultInput.ini."),
			*GetName());
	}
}

void AIBWeaponRack::UnbindInputFor(APawn* Pawn)
{
	if (APlayerController* PC = Pawn->GetController<APlayerController>())
	{
		DisableInput(PC);
	}
}

void AIBWeaponRack::HandleInteract()
{
	if (FocusedPawn)
	{
		OpenPickerFor(FocusedPawn);
	}
}

void AIBWeaponRack::OpenPickerFor(APawn* Pawn)
{
	if (ActivePicker)
	{
		return; // Already open for this pawn; interact is a toggle-open, not toggle-close (Escape closes it).
	}

	APlayerController* PC = Pawn->GetController<APlayerController>();
	if (!PC)
	{
		return;
	}

	const TSubclassOf<UIBWeaponRackScreen> WidgetClass =
		PickerWidgetClass ? PickerWidgetClass : TSubclassOf<UIBWeaponRackScreen>(UIBWeaponRackScreen::StaticClass());

	UIBWeaponRackScreen* Picker = CreateWidget<UIBWeaponRackScreen>(PC, WidgetClass);
	if (!Picker)
	{
		return;
	}

	Picker->InitForRack(this);
	Picker->AddToViewport();

	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(Picker->TakeWidget());
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PC->SetInputMode(InputMode);
	PC->SetShowMouseCursor(true);

	ActivePicker = Picker;
}

void AIBWeaponRack::ClosePicker()
{
	if (!ActivePicker)
	{
		return;
	}

	APawn* Pawn = FocusedPawn;
	ActivePicker->RemoveFromParent();
	ActivePicker = nullptr;

	if (Pawn)
	{
		if (APlayerController* PC = Pawn->GetController<APlayerController>())
		{
			PC->SetInputMode(FInputModeGameOnly());
			PC->SetShowMouseCursor(false);
		}
	}
}

void AIBWeaponRack::NotifyPickerClosed()
{
	ClosePicker();
}

const UIBItemDefinition* AIBWeaponRack::Server_TakeAt(int32 Index)
{
	if (!HasAuthority())
	{
		return nullptr;
	}

	if (!StockedWeapons.IsValidIndex(Index) || !StockedWeapons[Index])
	{
		return nullptr;
	}

	const UIBItemDefinition* Definition = StockedWeapons[Index];

	if (!bInfiniteStock)
	{
		StockedWeapons.RemoveAt(Index);

		// The server doesn't run its own OnRep (that's a client-only replication
		// callback) -- fire it manually so a listen host's own open picker (and
		// anything else locally bound to OnStockChanged) refreshes too.
		OnRep_StockedWeapons();
	}

	return Definition;
}

bool AIBWeaponRack::Server_DepositItem(const UIBItemDefinition* Definition)
{
	if (!HasAuthority() || !Definition)
	{
		return false;
	}

	// const_cast mirrors the inventory's own grammar: instances carry const
	// definitions, storage holds the mutable asset pointer type UHT requires.
	StockedWeapons.Add(const_cast<UIBItemDefinition*>(Definition));
	OnRep_StockedWeapons(); // manual for the listen host, same as Server_TakeAt
	return true;
}

void AIBWeaponRack::OnRep_StockedWeapons()
{
	OnStockChanged.Broadcast();
}

TArray<UIBItemDefinition*> AIBWeaponRack::GetStockedWeapons() const
{
	TArray<UIBItemDefinition*> Result;
	Result.Reserve(StockedWeapons.Num());
	for (const TObjectPtr<UIBItemDefinition>& Def : StockedWeapons)
	{
		Result.Add(Def);
	}
	return Result;
}
