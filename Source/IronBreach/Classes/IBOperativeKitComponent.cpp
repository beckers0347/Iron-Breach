#include "Classes/IBOperativeKitComponent.h"
#include "Classes/IBClassKitData.h"
#include "Skills/IBSkillComponent.h"
#include "Skills/IBSkillDecoy.h"
#include "Components/CapsuleComponent.h"
#include "Components/MeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "Classes/IBKitZone.h"
#include "Combat/DamageableInterface.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Items/IBPlayerState.h"
#include "UI/IBKitHudWidget.h"
#include "IronBreach.h"
#include "Blueprint/UserWidget.h"
#include "Components/InputComponent.h"
#include "EnhancedInputComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "Kismet/KismetSystemLibrary.h"
#include "TimerManager.h"

UIBOperativeKitComponent::UIBOperativeKitComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = 0.25f; // HUD spawn + housekeeping only; effects are event-driven
	SetIsReplicatedByDefault(true);

	KitAbilityKey = EKeys::Q;
	MovementToolKey = EKeys::V;

	// Designer-owned kits, one asset per trade; absent assets fall back to DefaultKitFor.
	KitData.Add(EIBOperativeClass::Breaker,    TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Breaker.DA_Kit_Breaker"))));
	KitData.Add(EIBOperativeClass::Picket,     TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Picket.DA_Kit_Picket"))));
	KitData.Add(EIBOperativeClass::Bellringer, TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Bellringer.DA_Kit_Bellringer"))));
	KitData.Add(EIBOperativeClass::Corpsman,   TSoftObjectPtr<UIBClassKitData>(FSoftObjectPath(TEXT("/Game/IronBreach/Classes/DA_Kit_Corpsman.DA_Kit_Corpsman"))));
}

// ---------------------------------------------------------------- defaults

FIBClassKit UIBOperativeKitComponent::DefaultKitFor(EIBOperativeClass Class)
{
    FIBClassKit Kit;
    const FIBSkillState Starter = IBSkills::StarterState(Class);
    if (const FIBSkillNode* N=IBSkills::Find(Starter.Equipped[0])) { Kit.MovementTool=N->Spec; }
    if (const FIBSkillNode* N=IBSkills::Find(Starter.Equipped[1])) { Kit.KitAbility=N->Spec; }
    return Kit;
}

// ---------------------------------------------------------------- lifecycle

void UIBOperativeKitComponent::BeginPlay()
{
	Super::BeginPlay();
	RefreshKit();
}

void UIBOperativeKitComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(GlideHandle);
		for (FTimerHandle Handle:EffectHandles) { World->GetTimerManager().ClearTimer(Handle); }
        EndGlide();
	}
	if (Hud)
	{
		Hud->RemoveFromParent();
		Hud = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}

void UIBOperativeKitComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// The PlayerState (and its operative) can land after BeginPlay on clients.
	RefreshKit();
    if (GetOwner()->HasAuthority() && bConcealed && (Now() >= CloakUntil || !CanActivate())) { NotifyAttack(); }
	EnsureHud();
}

void UIBOperativeKitComponent::RefreshKit()
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const AIBPlayerState* PS = Pawn ? Pawn->GetPlayerState<AIBPlayerState>() : nullptr;
	const bool bHasIdentity = PS && PS->HasOperative();
	const EIBOperativeClass Class = bHasIdentity ? PS->GetOperativeClass() : EIBOperativeClass::Breaker;

    const FIBSkillState Next = PS && PS->Skills && PS->Skills->IsReady()
        ? PS->Skills->GetState() : IBSkills::StarterState(Class);
    if (bKitApplied && Class==ResolvedClass && bHasIdentity==bResolvedFromIdentity && Next==AppliedSkills) { return; }
    AppliedSkills=Next;
    SlotSpecs.SetNum(4);
    for (int32 I=0; I<4; ++I)
    {
        const FIBSkillNode* N=Next.Equipped.IsValidIndex(I) ? IBSkills::Find(Next.Equipped[I]) : nullptr;
        SlotSpecs[I]=N ? N->Spec : FIBKitAbilitySpec();
    }
    ActiveKit.KitAbility=SlotSpecs[1]; ActiveKit.MovementTool=SlotSpecs[0];
    ResolvedClass=Class; bResolvedFromIdentity=bHasIdentity; bKitApplied=true;

	if (Hud)
	{
		Hud->RefreshLabels();
	}
}

void UIBOperativeKitComponent::EnsureHud()
{
	if (Hud || !bShowHud) { return; }
	APlayerController* PC = OwnerPC();
	if (!PC || !PC->IsLocalController()) { return; }

	Hud = CreateWidget<UIBKitHudWidget>(PC, UIBKitHudWidget::StaticClass());
	if (Hud)
	{
		Hud->InitFor(this);
		Hud->AddToViewport(7);
	}
}

// ---------------------------------------------------------------- input

void UIBOperativeKitComponent::BindInput(UInputComponent* PlayerInputComponent, UInputAction* KitAbilityAction, UInputAction* MovementToolAction)
{
	if (!PlayerInputComponent) { return; }

	// Raw floor: the kit works with zero content (same rule as 1/2/3 and F).
	if (KitAbilityKey.IsValid())
	{
		PlayerInputComponent->BindKey(KitAbilityKey, IE_Pressed, this, &UIBOperativeKitComponent::ActivateKitAbility);
	}
	if (MovementToolKey.IsValid())
	{
		PlayerInputComponent->BindKey(MovementToolKey, IE_Pressed, this, &UIBOperativeKitComponent::ActivateMovementTool);
	}

	PlayerInputComponent->BindKey(EKeys::Z, IE_Pressed, this, &UIBOperativeKitComponent::ActivateTacticalTwo);
    PlayerInputComponent->BindKey(EKeys::X, IE_Pressed, this, &UIBOperativeKitComponent::ActivateOverdrive);

    // Optional Enhanced Input route for Connor's IMC (gamepad etc.).
	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		if (KitAbilityAction)   { EIC->BindAction(KitAbilityAction,   ETriggerEvent::Started, this, &UIBOperativeKitComponent::ActivateKitAbility); }
		if (MovementToolAction) { EIC->BindAction(MovementToolAction, ETriggerEvent::Started, this, &UIBOperativeKitComponent::ActivateMovementTool); }
	}
}

void UIBOperativeKitComponent::ActivateKitAbility() { ActivateSlot(EIBSkillSlot::TacticalOne); }
void UIBOperativeKitComponent::ActivateMovementTool() { ActivateSlot(EIBSkillSlot::Signature); }
double UIBOperativeKitComponent::Now() const { return GetWorld() ? GetWorld()->GetTimeSeconds() : 0; }
const FIBKitAbilitySpec& UIBOperativeKitComponent::GetSlotSpec(EIBSkillSlot Slot) const
{
    static const FIBKitAbilitySpec Empty;
    return SlotSpecs.IsValidIndex(static_cast<int32>(Slot)) ? SlotSpecs[static_cast<int32>(Slot)] : Empty;
}
FKey UIBOperativeKitComponent::GetSlotKey(EIBSkillSlot Slot) const
{
    switch (Slot) { case EIBSkillSlot::Signature:return MovementToolKey; case EIBSkillSlot::TacticalOne:return KitAbilityKey;
    case EIBSkillSlot::TacticalTwo:return EKeys::Z; default:return EKeys::X; }
}
float UIBOperativeKitComponent::GetSlotCooldown(EIBSkillSlot Slot) const
{
    const int32 I=static_cast<int32>(Slot); if (I<0 || I>=4) { return 0; }
    const FName Root=AppliedSkills.Equipped.IsValidIndex(I) ? IBSkills::RootAbility(AppliedSkills.Equipped[I]) : NAME_None;
    const double* AbilityReady=AbilityReadyTime.Find(Root);
    return FMath::Max(0.f,static_cast<float>(FMath::Max(SlotReadyTime[I],AbilityReady ? *AbilityReady : 0.0)-Now()));
}
float UIBOperativeKitComponent::GetCooldownRemaining(bool bMovementTool) const
{ return GetSlotCooldown(bMovementTool ? EIBSkillSlot::Signature : EIBSkillSlot::TacticalOne); }
float UIBOperativeKitComponent::GetCooldownFraction(bool bMovementTool) const
{ return FMath::Clamp(GetCooldownRemaining(bMovementTool)/FMath::Max(.01f,SpecFor(bMovementTool).Cooldown),0.f,1.f); }
float UIBOperativeKitComponent::GetDamageTakenScale() const
{
    float Scale=Now()<DefenseUntil ? DefenseScale : 1.f;
    if (Now()<GuardUntil) { Scale=FMath::Min(Scale,GuardScale); }
    if (Now()<WardUntil) { Scale=FMath::Min(Scale,WardScale); }
    return Scale;
}
void UIBOperativeKitComponent::ApplyWardDefense(float Scale,float Duration)
{
    if (!GetOwner()->HasAuthority()) { return; }
    if (Now()>=WardUntil || Scale<=WardScale) { WardScale=FMath::Clamp(Scale,0.f,1.f); WardUntil=Now()+Duration; }
}
void UIBOperativeKitComponent::RecordGuardedDamage(float IncomingDamage)
{
    if (GetOwner()->HasAuthority() && Now()<GuardUntil && FMath::IsFinite(IncomingDamage))
    { GuardEnergy=FMath::Clamp(GuardEnergy+FMath::Max(0.f,IncomingDamage)*(1.f-GuardScale),0.f,100.f); }
}
bool UIBOperativeKitComponent::CanActivate() const
{
    const AIBCharacter_Infantry* Infantry=Cast<AIBCharacter_Infantry>(GetOwner());
    return Infantry && !Infantry->IsDead() && Infantry->GetController();
}
void UIBOperativeKitComponent::ActivateSlot(EIBSkillSlot Slot)
{
    if (CanActivate()) { Server_Activate(Slot); }
}
void UIBOperativeKitComponent::Server_Activate_Implementation(EIBSkillSlot Slot)
{
    const int32 I=static_cast<int32>(Slot);
    if (I<0 || I>=4 || !CanActivate()) { return; }
    RefreshKit();
    const FIBKitAbilitySpec& Spec=GetSlotSpec(Slot);
    if (!Spec.IsUsable()) { return; }
    if (Spec.Effect==EIBKitEffect::ReturnDash && Now()<ReturnUntil && TryReturn()) { return; }
    const FName Root=IBSkills::RootAbility(AppliedSkills.Equipped[I]);
    if (GetSlotCooldown(Slot)>0)
    { Client_Cooldown(Slot,Root,GetSlotCooldown(Slot)); return; }
    SlotReadyTime[I]=Now()+Spec.Cooldown; AbilityReadyTime.Add(Root,SlotReadyTime[I]);
    Client_Cooldown(Slot,Root,Spec.Cooldown);
    ExecuteEffect(Slot);
}
void UIBOperativeKitComponent::Client_Cooldown_Implementation(EIBSkillSlot Slot,FName Ability,float Remaining)
{
    const int32 I=static_cast<int32>(Slot); if (I<0 || I>=4 || GetOwner()->HasAuthority()) { return; }
    SlotReadyTime[I]=Now()+Remaining; AbilityReadyTime.Add(Ability,SlotReadyTime[I]);
}
void UIBOperativeKitComponent::Multicast_Activated_Implementation(EIBSkillSlot Slot,const FIBKitAbilitySpec& Spec)
{ BP_OnKitActivated(Slot==EIBSkillSlot::Signature,Spec); }
void UIBOperativeKitComponent::ExecuteEffect(EIBSkillSlot Slot)
{
    const FIBKitAbilitySpec Spec=GetSlotSpec(Slot);
    if (Spec.Damage>0) { NotifyAttack(); }
    auto Later=[&](float Delay,TFunction<void()> Action)
    {
        FTimerHandle& Handle=EffectHandles.AddDefaulted_GetRef();
        GetWorld()->GetTimerManager().SetTimer(Handle,FTimerDelegate::CreateWeakLambda(this,[this,Action]()
        { if (CanActivate()) { Action(); } }),Delay,false);
    };
    switch(Spec.Effect)
    {
    case EIBKitEffect::ReturnDash:
        ReturnAnchor=GetOwner()->GetActorLocation(); ReturnUntil=Now()+3; Client_ReturnWindow(3);
        DoDash(Spec); break;
    case EIBKitEffect::Dash:
        DoDash(Spec); OpenDefenseWindow(Spec);
        if (Spec.bLeaveWard) { Later(.6f,[this,Spec]() { FIBKitAbilitySpec Ward=Spec; Ward.Duration=5; DoDeployZone(Ward); }); }
        break;
    case EIBKitEffect::Grapple: DoGrapple(Spec); break;
    case EIBKitEffect::Glide: DoGlide(Spec); break;
    case EIBKitEffect::ConeStrike:
        DoDash(Spec); OpenDefenseWindow(Spec);
        Later(FMath::Max(.05f,Spec.Duration),[this,Spec]() { DoConeStrikeDamage(Spec); }); break;
    case EIBKitEffect::RadialStrike:
        OpenDefenseWindow(Spec); DoStrikeDamage(Spec,true); break;
    case EIBKitEffect::Guard:
        GuardUntil=Now()+Spec.Duration; GuardScale=Spec.DamageTakenScale; break;
    case EIBKitEffect::DeployZone: DoDeployZone(Spec); break;
    case EIBKitEffect::Cloak:
        bConcealed=true; CloakUntil=Now()+Spec.Duration; OnRep_Concealed();
        if (Spec.Strength>0) { DoDash(Spec); }
        if (Spec.bMarksTargets || Spec.SlowFactor<1) { DoDeployZone(Spec); }
        break;
    case EIBKitEffect::Decoy: AIBSkillDecoy::Project(OwnerCharacter(),Spec); break;
    default: break;
    }
    GetOwner()->ForceNetUpdate(); Multicast_Activated(Slot,Spec);
}
bool UIBOperativeKitComponent::TryReturn()
{
    ACharacter* C=OwnerCharacter(); if (!C || Now()>=ReturnUntil) { return false; }
    UCapsuleComponent* Capsule=C->GetCapsuleComponent();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(IBReturnVector),false,C);
    const FCollisionShape Shape=FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(),Capsule->GetScaledCapsuleHalfHeight());
    FHitResult Hit;
    if (GetWorld()->SweepSingleByChannel(Hit,C->GetActorLocation(),ReturnAnchor,FQuat::Identity,ECC_Pawn,Shape,Params)
        || GetWorld()->OverlapBlockingTestByChannel(ReturnAnchor,FQuat::Identity,ECC_Pawn,Shape,Params)) { return false; }
    C->GetCharacterMovement()->StopMovementImmediately();
    if (!C->TeleportTo(ReturnAnchor,C->GetActorRotation(),false,true)) { return false; }
    ReturnUntil=0; Client_ReturnWindow(0); return true;
}
void UIBOperativeKitComponent::NotifyAttack()
{
    if (!GetOwner()->HasAuthority() || !bConcealed) { return; }
    bConcealed=false; CloakUntil=0; OnRep_Concealed(); GetOwner()->ForceNetUpdate();
}
void UIBOperativeKitComponent::OnRep_Concealed()
{
    if (bConcealed)
    {
        TArray<UMeshComponent*> Meshes; GetOwner()->GetComponents(Meshes);
        for (UMeshComponent* Mesh:Meshes) if (Mesh->IsVisible()) { ConcealedMeshes.AddUnique(Mesh); Mesh->SetVisibility(false); }
    }
    else
    {
        for (auto Weak:ConcealedMeshes) if (UMeshComponent* Mesh=Weak.Get()) { Mesh->SetVisibility(true); }
        ConcealedMeshes.Empty();
    }
}
void UIBOperativeKitComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UIBOperativeKitComponent,bConcealed);
    DOREPLIFETIME_CONDITION(UIBOperativeKitComponent,GuardEnergy,COND_OwnerOnly);
}

FVector UIBOperativeKitComponent::LookDirection(bool bFlatten) const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn) { return FVector::ForwardVector; }
	FVector Dir = Pawn->GetControlRotation().Vector();
	if (bFlatten)
	{
		Dir.Z = 0.f;
	}
	return Dir.GetSafeNormal().IsNearlyZero() ? Pawn->GetActorForwardVector() : Dir.GetSafeNormal();
}

void UIBOperativeKitComponent::DoDash(const FIBKitAbilitySpec& Spec)
{
	if (ACharacter* Character = OwnerCharacter())
	{
		if (Spec.Strength<=0) { return; }
        FVector Dir=LookDirection(true);
        if (Spec.Effect==EIBKitEffect::Dash || Spec.Effect==EIBKitEffect::ReturnDash || Spec.Effect==EIBKitEffect::Cloak)
        {
            FVector Input=Character->GetLastMovementInputVector(); Input.Z=0;
            if (Input.IsNearlyZero()) { Input=Character->GetCharacterMovement()->GetCurrentAcceleration(); Input.Z=0; }
            if (!Input.IsNearlyZero()) { Dir=Input.GetSafeNormal(); }
        }
        Character->LaunchCharacter(Dir * Spec.Strength + FVector(0.f, 0.f, Spec.Strength * 0.12f), true, true);
	}
}

void UIBOperativeKitComponent::OpenDefenseWindow(const FIBKitAbilitySpec& Spec)
{
	if (Spec.DamageTakenScale < 1.f && Spec.Duration > 0.f)
	{
		DefenseScale = Spec.DamageTakenScale;
		DefenseUntil = Now() + Spec.Duration;
	}
}

void UIBOperativeKitComponent::DoGrapple(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UWorld* World = GetWorld();
	if (!Character || !World) { return; }

	const FVector Start = Character->GetPawnViewLocation();
	const FVector Dir = LookDirection(/*bFlatten=*/false);
	const FVector End = Start + Dir * Spec.Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(IBLineBolt), /*bTraceComplex=*/false, Character);
	FHitResult Hit;
	if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
	{
		return; // nothing to anchor to — no cooldown refund on purpose (it's a commit)
	}

	const FVector From = Character->GetActorLocation();
	const FVector To = Hit.ImpactPoint;
	const float Dist = FVector::Dist(From, To);
	const FVector Flat = (To - From).GetSafeNormal();

	// Fast horizontal pull plus enough lift to clear the ledge you're aiming at.
	FVector Velocity = Flat * Spec.Strength;
	Velocity.Z = FMath::Clamp(300.f + Dist * 0.25f + FMath::Max(0.f, To.Z - From.Z) * 1.2f, 300.f, 1400.f);
	Character->LaunchCharacter(Velocity, true, true);
}

void UIBOperativeKitComponent::DoGlide(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UCharacterMovementComponent* Move = Character ? Character->GetCharacterMovement() : nullptr;
	UWorld* World = GetWorld();
	if (!Move || !World) { return; }

	if (!bGliding)
	{
		SavedGravityScale = Move->GravityScale;
		SavedAirControl = Move->AirControl;
		bGliding = true;
	}
	Move->GravityScale = FMath::Clamp(Spec.Strength, 0.f, 1.f);
	Move->AirControl = 1.f;

	// Kill the fall so the glide reads immediately, even mid-drop.
	FVector Vel = Move->Velocity;
	Vel.Z = FMath::Max(Vel.Z, 0.f);
	Move->Velocity = Vel;

	World->GetTimerManager().SetTimer(GlideHandle, this, &UIBOperativeKitComponent::EndGlide, FMath::Max(0.2f, Spec.Duration), false);
}

void UIBOperativeKitComponent::EndGlide()
{
	if (!bGliding) { return; }
	bGliding = false;
	if (ACharacter* Character = OwnerCharacter())
	{
		if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
		{
			Move->GravityScale = SavedGravityScale;
			Move->AirControl = SavedAirControl;
		}
	}
}

void UIBOperativeKitComponent::DoConeStrikeDamage(const FIBKitAbilitySpec& Spec) { DoStrikeDamage(Spec,false); }
void UIBOperativeKitComponent::DoStrikeDamage(FIBKitAbilitySpec Spec,bool bRadial)
{
    ACharacter* C=OwnerCharacter(); if (!C || !C->HasAuthority() || !CanActivate()) { return; }
    if (Spec.bUsesGuardEnergy) { Spec.Damage+=GuardEnergy; GuardEnergy=0; }
    const FVector Origin=C->GetActorLocation(), Dir=LookDirection(true);
    TArray<TEnumAsByte<EObjectTypeQuery>> Types; Types.Add(UEngineTypes::ConvertToObjectType(ECC_Pawn));
    TArray<AActor*> Ignore {C}, Targets;
    UKismetSystemLibrary::SphereOverlapActors(this,Origin,bRadial ? Spec.Radius : Spec.Range+Spec.Radius,Types,AActor::StaticClass(),Ignore,Targets);
    for (AActor* Target:Targets)
    {
        if (!Target || Target->IsA<AIBCharacter_Infantry>() || Target->IsA<AIBSkillDecoy>()
            || !Target->GetClass()->ImplementsInterface(UDamageableInterface::StaticClass())) { continue; }
        const FVector To=Target->GetActorLocation()-Origin;
        if (!bRadial)
        {
            const float Along=FVector::DotProduct(To,Dir);
            if (Along<0 || Along>Spec.Range || (To-Dir*Along).Size()>Spec.Radius) { continue; }
        }
        // No strikes through walls; use the hit component/bone for the existing armor pipeline.
        FCollisionQueryParams Params(SCENE_QUERY_STAT(IBSkillStrike),true,C);
        FHitResult Hit;
        const bool bHit=GetWorld()->LineTraceSingleByChannel(Hit,Origin,Target->GetActorLocation(),ECC_Pawn,Params);
        if (bHit && Hit.GetActor()!=Target) { continue; }
        if (!bHit) { Hit=FHitResult(Target,Cast<UPrimitiveComponent>(Target->GetRootComponent()),Target->GetActorLocation(),-To.GetSafeNormal()); }
        IDamageableInterface::Execute_HandleTakeDamage(Target,Spec.Damage,Hit,C->GetController(),C);
        if (ACharacter* Other=Cast<ACharacter>(Target); Other && Spec.Strength>0)
        { Other->LaunchCharacter(To.GetSafeNormal2D()*Spec.Strength+FVector(0,0,200),true,true); }
    }
}

void UIBOperativeKitComponent::DoDeployZone(const FIBKitAbilitySpec& Spec)
{
	ACharacter* Character = OwnerCharacter();
	UWorld* World = GetWorld();
	if (!Character || !World || !Character->HasAuthority()) { return; }

	FVector Location = Character->GetActorLocation() - FVector(0.f, 0.f, Character->GetDefaultHalfHeight());
	if (Spec.bPlaceAtAim)
	{
		const FVector Start = Character->GetPawnViewLocation();
		const FVector End = Start + LookDirection(false) * Spec.Range;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IBDeployZone), false, Character);
		FHitResult Hit;
		FVector Anchor = End; // nothing in reach: it lands at max range
		if (World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
		{
			// Back off the surface so a wall hit lands at the wall's foot, not inside it.
			Anchor = Hit.ImpactPoint + Hit.ImpactNormal * 40.f;
			if (AActor* HitActor = Hit.GetActor(); HitActor && HitActor->IsA<APawn>())
			{
				Params.AddIgnoredActor(HitActor); // hit a Kaiju: drop to the ground under it, not onto its shin
			}
		}

		// It's thrown, not pinned: fall to whatever floor is under the anchor.
		FHitResult Ground;
		if (World->LineTraceSingleByChannel(Ground, Anchor + FVector(0.f, 0.f, 120.f), Anchor - FVector(0.f, 0.f, 6000.f), ECC_Visibility, Params))
		{
			Location = Ground.ImpactPoint;
		}
		else
		{
			Location = Anchor;
		}
	}

	UClass* ZoneClass = Spec.ZoneClass ? *Spec.ZoneClass : AIBKitZone::StaticClass();
	FActorSpawnParameters Params;
	Params.Owner = Character;
	Params.Instigator = Character;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (AIBKitZone* Zone = World->SpawnActor<AIBKitZone>(ZoneClass, Location, FRotator::ZeroRotator, Params))
	{
		Zone->InitZone(Spec, IBCharacter::ClassColor(ResolvedClass), Character);
	}
}

// ---------------------------------------------------------------- helpers

ACharacter* UIBOperativeKitComponent::OwnerCharacter() const
{
	return Cast<ACharacter>(GetOwner());
}

APlayerController* UIBOperativeKitComponent::OwnerPC() const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	return Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
}

void UIBOperativeKitComponent::Client_ReturnWindow_Implementation(float Seconds)
{ if (!GetOwner()->HasAuthority()) { ReturnUntil=Now()+Seconds; } }

bool UIBOperativeKitComponent::IsGuardActive() const
{
    if (GetOwner()->HasAuthority()) { return Now()<GuardUntil; }
    const FIBKitAbilitySpec& Spec=GetSlotSpec(EIBSkillSlot::Signature);
    return Spec.Effect==EIBKitEffect::Guard && GetSlotCooldown(EIBSkillSlot::Signature)>Spec.Cooldown-Spec.Duration;
}
