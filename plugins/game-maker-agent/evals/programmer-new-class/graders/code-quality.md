---
type: llm
focus: { source: file, path: Source/Skyhop/Checkpoint.h }
---

This is an Unreal Engine 5 C++ header for a checkpoint actor.
PASS if it declares a UCLASS ACheckpoint deriving from AActor, stores UObject pointers (such as components) in UPROPERTY members, and has an overlap component or overlap handler.
FAIL if it is not a valid-looking Unreal header, stores raw UObject pointers without UPROPERTY, or has no way to detect overlap.
