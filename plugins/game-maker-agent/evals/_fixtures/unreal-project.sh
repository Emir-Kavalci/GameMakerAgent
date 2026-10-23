#!/usr/bin/env bash
# Builds a small fake Unreal Engine 5.7 C++ project ("Skyhop") in the current
# folder for the eval cases. It has no real engine files; it only has to look
# like a project to the agents.
# Usage: bash unreal-project.sh [--bare]
#   --bare  only the .uproject and Source/ (no CLAUDE.md, Docs/ or Content/),
#           like a project that never ran gma-init
set -e

mkdir -p Source/Skyhop

cat > Skyhop.uproject <<'JSON'
{
	"FileVersion": 3,
	"EngineAssociation": "5.7",
	"Category": "",
	"Description": "",
	"Modules": [
		{
			"Name": "Skyhop",
			"Type": "Runtime",
			"LoadingPhase": "Default",
			"AdditionalDependencies": [ "Engine" ]
		}
	],
	"Plugins": [
		{ "Name": "ModelingToolsEditorMode", "Enabled": true, "TargetAllowList": [ "Editor" ] }
	]
}
JSON

cat > Source/Skyhop.Target.cs <<'CS'
using UnrealBuildTool;

public class SkyhopTarget : TargetRules
{
	public SkyhopTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
		ExtraModuleNames.Add("Skyhop");
	}
}
CS

cat > Source/SkyhopEditor.Target.cs <<'CS'
using UnrealBuildTool;

public class SkyhopEditorTarget : TargetRules
{
	public SkyhopEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
		ExtraModuleNames.Add("Skyhop");
	}
}
CS

cat > Source/Skyhop/Skyhop.Build.cs <<'CS'
using UnrealBuildTool;

public class Skyhop : ModuleRules
{
	public Skyhop(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput" });
	}
}
CS

cat > Source/Skyhop/Skyhop.h <<'CPP'
#pragma once

#include "CoreMinimal.h"
CPP

cat > Source/Skyhop/Skyhop.cpp <<'CPP'
#include "Skyhop.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, Skyhop, "Skyhop");
CPP

cat > Source/Skyhop/SkyhopCharacter.h <<'CPP'
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SkyhopCharacter.generated.h"

class UInputAction;

UCLASS()
class SKYHOP_API ASkyhopCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ASkyhopCharacter();

	/** Number of coins the player has collected. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Coins")
	int32 CoinCount = 0;

	UFUNCTION(BlueprintCallable, Category = "Coins")
	void AddCoins(int32 Amount);

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> JumpAction;
};
CPP

cat > Source/Skyhop/SkyhopCharacter.cpp <<'CPP'
#include "SkyhopCharacter.h"
#include "EnhancedInputComponent.h"

ASkyhopCharacter::ASkyhopCharacter()
{
	PrimaryActorTick.bCanEverTick = false;
	JumpMaxCount = 2; // double jump
}

void ASkyhopCharacter::AddCoins(int32 Amount)
{
	CoinCount += FMath::Max(0, Amount);
}

void ASkyhopCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		Input->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
		Input->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
	}
}
CPP

if [ "$1" = "--bare" ]; then
  exit 0
fi

mkdir -p Docs/Features Content/Blueprints Content/Meshes Content/Materials Content/Maps

cat > CLAUDE.md <<'MD'
# Skyhop

## About the game
A cozy single-player 3D platformer: a small cloud hops between floating islands and collects coins.
Design: Docs/GDD.md. Feature specs: Docs/Features/. Tasks: Docs/Tasks.md.

## Project facts
- Engine: Unreal Engine 5.7
- Project type: C++
- Main module: Skyhop (export macro SKYHOP_API)
- Platform: Windows
- Editor connection (GameMakerAgent): off

## Conventions
- Follow Unreal Engine naming conventions (A/U/F/E/I prefixes, b for booleans).
- Put new C++ classes in Source/Skyhop/ following the existing flat layout.
- Expose tunable values to the editor with UPROPERTY(EditAnywhere).
- Do not edit .uasset or .umap files as files; change them through the editor connection when it is on, otherwise describe editor steps.

## Build
Close the Unreal Editor first, then run:
"C:/Program Files/Epic Games/UE_5.7/Engine/Build/BatchFiles/Build.bat" SkyhopEditor Win64 Development -Project="<this folder>/Skyhop.uproject" -WaitMutex
MD

cat > Docs/GDD.md <<'MD'
# Skyhop: Game Design Document

## Pitch
A cozy single-player 3D platformer. You are Puff, a small cloud who hops between floating islands to collect lost coins.

## Platform and scope
- PC (Windows), Steam. Single-player only; there is no multiplayer or online mode.
- Target length: 3 levels, about 1 hour.

## Core loop
Explore an island, collect coins, reach the wind gate to the next island.

## Features (current state)
| Feature | State |
|---|---|
| Movement and double jump | Done |
| Coins and coin counter | Done (C++ only, no UI yet) |
| Checkpoints | Not started |
| Speed pads | In progress |
| Level 1: Meadow Isle | Blockout |
| Levels 2 and 3 | Not started |
| Main menu, pause menu | Not started |

## Art and audio
Soft pastel colors, low-poly shapes. Calm acoustic music. Not decided in detail yet.
MD

cat > Docs/Tasks.md <<'MD'
# Tasks

## Now

## Next

## Later

## Done
- [x] Movement and double jump (programmer)
- [x] Coins and coin counter in C++ (programmer)
MD

echo "One spec per feature, written by the game-designer agent." > Docs/Features/README.md

# Placeholder assets. Real ones are binary; these only need the right names.
# Some names break Unreal conventions on purpose, for the naming audit case.
for f in Blueprints/BP_Coin Blueprints/BP_WindGate Blueprints/coinPickup_old \
         Meshes/SM_Island_Small Meshes/gem_mesh Meshes/Rock01 \
         Materials/M_Grass Materials/Material_Ground Materials/MI_Grass_Dark \
         Maps/L_Meadow; do
  ext=uasset
  case "$f" in Maps/*) ext=umap ;; esac
  printf 'FAKE-UNREAL-ASSET %s\n' "$f" > "Content/$f.$ext"
done
