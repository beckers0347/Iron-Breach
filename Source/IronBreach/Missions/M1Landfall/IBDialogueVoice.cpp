// IBDialogueVoice.cpp

#include "IBDialogueVoice.h"
#include "IronBreach.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "Components/SceneComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	UWorld* ResolveWorld(UObject* Context)
	{
		return (GEngine && Context)
			? GEngine->GetWorldFromContextObject(Context, EGetWorldErrorMode::ReturnNull)
			: nullptr;
	}

	// Clips longer than this are treated as "looping / unknown" and don't extend the hold.
	constexpr float MaxSensibleVoiceSeconds = 600.0f;
}

FName IBDialogueVoice::GetSpeakerTag(EDialogueSpeaker Speaker)
{
	switch (Speaker)
	{
	case EDialogueSpeaker::Rhodes:     return FName(TEXT("VO_Rhodes"));
	case EDialogueSpeaker::Bricks:     return FName(TEXT("VO_Bricks"));
	case EDialogueSpeaker::Static:     return FName(TEXT("VO_Static"));
	case EDialogueSpeaker::Vance:      return FName(TEXT("VO_Vance"));
	case EDialogueSpeaker::Achterberg: return FName(TEXT("VO_Achterberg"));
	default:                           return NAME_None; // Player / Idris / Comms / None -> 2D
	}
}

AActor* IBDialogueVoice::FindSpeakerActor(UObject* WorldContext, EDialogueSpeaker Speaker)
{
	const FName Tag = GetSpeakerTag(Speaker);
	UWorld* World = ResolveWorld(WorldContext);
	if (Tag.IsNone() || !World)
	{
		return nullptr;
	}

	FVector Reference = FVector::ZeroVector;
	if (const APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(World, 0))
	{
		Reference = PlayerPawn->GetActorLocation();
	}

	AActor* Best = nullptr;
	double BestDistSq = TNumericLimits<double>::Max();
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Candidate = *It;
		if (!Candidate || Candidate->IsHidden() || !Candidate->ActorHasTag(Tag))
		{
			continue;
		}
		const double DistSq = FVector::DistSquared(Candidate->GetActorLocation(), Reference);
		if (DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Best = Candidate;
		}
	}
	return Best;
}

float IBDialogueVoice::PlayLine(UObject* WorldContext, const FDialogueLine& Line, const TCHAR* ActTag, int32 LineIndex)
{
	UWorld* World = ResolveWorld(WorldContext);
	if (!World)
	{
		return 0.0f;
	}

	// 1. Explicit sound on the line, 2. naming convention.
	USoundBase* Sound = Line.VoiceSound.IsNull() ? nullptr : Line.VoiceSound.LoadSynchronous();
	if (!Sound && ActTag)
	{
		const FString AssetName = FString::Printf(TEXT("%s_L%03d"), ActTag, LineIndex);
		const FString ObjectPath = FString::Printf(TEXT("/Game/IronBreach/Audio/VO/M1/%s.%s"), *AssetName, *AssetName);
		Sound = LoadObject<USoundBase>(nullptr, *ObjectPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	}

	if (!Sound)
	{
		return 0.0f;
	}

	float Duration = Sound->GetDuration();
	if (Duration < 0.0f || Duration > MaxSensibleVoiceSeconds)
	{
		Duration = 0.0f;
	}

	// A dedicated server has nobody to hear it, but still reports the duration so
	// line timing stays identical on every machine.
	if (World->GetNetMode() == NM_DedicatedServer)
	{
		return Duration;
	}

	AActor* SpeakerActor = FindSpeakerActor(WorldContext, Line.Speaker);
	if (SpeakerActor && SpeakerActor->GetRootComponent())
	{
		UGameplayStatics::SpawnSoundAttached(Sound, SpeakerActor->GetRootComponent());
		UE_LOG(LogIronBreach, Verbose, TEXT("[VO] 3D '%s' on '%s' (%.2fs) act=%s line=%d"),
			*Sound->GetName(), *SpeakerActor->GetName(), Duration, ActTag ? ActTag : TEXT("?"), LineIndex);
	}
	else
	{
		UGameplayStatics::PlaySound2D(World, Sound);
		UE_LOG(LogIronBreach, Verbose, TEXT("[VO] 2D '%s' (%.2fs) act=%s line=%d"),
			*Sound->GetName(), Duration, ActTag ? ActTag : TEXT("?"), LineIndex);
	}

	return Duration;
}
