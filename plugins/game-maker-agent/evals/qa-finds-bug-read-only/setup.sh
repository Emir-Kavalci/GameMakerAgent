bash "$(dirname "$0")/../_fixtures/unreal-project.sh"
cat > Docs/Features/SpeedPads.md <<'MD'
# Speed Pads

## Goal
A pad on the ground that gives the player a short burst of speed.

## Acceptance criteria
1. When the player character steps on a speed pad, its max walk speed rises from 600 to 1200.
2. After 2 seconds the speed returns to 600.
3. The boost amount and duration can be changed per pad in the editor.
4. Other actors (for example a rolling rock) stepping on the pad cause no error.
MD
cat > Source/Skyhop/SpeedPad.h <<'CPP'
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SpeedPad.generated.h"

class UBoxComponent;

UCLASS()
class SKYHOP_API ASpeedPad : public AActor
{
	GENERATED_BODY()

public:
	ASpeedPad();

	virtual void Tick(float DeltaTime) override;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UBoxComponent> Trigger;

	UFUNCTION()
	void OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	void ResetSpeed();

	ACharacter* BoostedCharacter;
	FTimerHandle ResetTimer;
};
CPP
cat > Source/Skyhop/SpeedPad.cpp <<'CPP'
#include "SpeedPad.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

ASpeedPad::ASpeedPad()
{
	PrimaryActorTick.bCanEverTick = true;

	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	RootComponent = Trigger;
}

void ASpeedPad::BeginPlay()
{
	Super::BeginPlay();
	Trigger->OnComponentBeginOverlap.AddDynamic(this, &ASpeedPad::OnOverlap);
}

void ASpeedPad::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

void ASpeedPad::OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	ACharacter* Character = Cast<ACharacter>(OtherActor);
	Character->GetCharacterMovement()->MaxWalkSpeed = 1200.f;
	BoostedCharacter = Character;
	GetWorldTimerManager().SetTimer(ResetTimer, this, &ASpeedPad::ResetSpeed, 2.0f, false);
}

void ASpeedPad::ResetSpeed()
{
	if (BoostedCharacter)
	{
		BoostedCharacter->GetCharacterMovement()->MaxWalkSpeed = 600.f;
	}
}
CPP
