using UnrealBuildTool;
public class MoedasBuilder : ModuleRules {
    public MoedasBuilder(ReadOnlyTargetRules Target) : base(Target) {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "UnrealEd", "BlueprintGraph", "Kismet", "KismetCompiler" });
    }
}
