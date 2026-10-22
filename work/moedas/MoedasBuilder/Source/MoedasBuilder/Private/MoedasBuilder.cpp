#include "Modules/ModuleManager.h"
#include "Containers/Ticker.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraphUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "KismetCompilerModule.h"
#include "Kismet2/CompilerResultsLog.h"
#include "HAL/FileManager.h"
#include "UObject/SavePackage.h"

class FMoedasBuilderModule : public IModuleInterface {
    FTSTicker::FDelegateHandle Handle;
public:
    virtual void StartupModule() override {
        Handle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float) {
            const FString Dir = FPaths::ProjectDir() / TEXT("work/moedas");
            const FString Trigger = Dir / TEXT("import_graph.trigger");
            if (!FPaths::FileExists(Trigger)) return true;
            IFileManager::Get().Delete(*Trigger);
            FString Text, Result;
            UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/Moedas/BP_Moeda.BP_Moeda"));
            if (BP && FFileHelper::LoadFileToString(Text, *(Dir / TEXT("BP_Moeda_graph.txt")))) {
                UEdGraph* Graph = FBlueprintEditorUtils::FindEventGraph(BP);
                TSet<UEdGraphNode*> Imported;
                FEdGraphUtilities::ImportNodesFromText(Graph, Text, Imported);
                FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
                FCompilerResultsLog Log;
                FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::None, &Log);
                Result = FString::Printf(TEXT("Imported=%d Errors=%d Warnings=%d Status=%d\n"), Imported.Num(), Log.NumErrors, Log.NumWarnings, int32(BP->Status));
                for (const TSharedRef<FTokenizedMessage>& Message : Log.Messages) Result += Message->ToText().ToString() + TEXT("\n");
                for (UEdGraphNode* Node : Imported) {
                    Result += Node->GetName() + TEXT(" : ") + Node->GetNodeTitle(ENodeTitleType::ListView).ToString() + TEXT("\n");
                    for (UEdGraphPin* Pin : Node->Pins) {
                        Result += TEXT("  ") + Pin->PinName.ToString() + TEXT(" links=") + FString::FromInt(Pin->LinkedTo.Num()) + TEXT(" orphan=") + FString::FromInt(Pin->bOrphanedPin) + TEXT("\n");
                    }
                }
                if (!Log.NumErrors) {
                    FSavePackageArgs Args; Args.TopLevelFlags = RF_Public | RF_Standalone;
                    UPackage::SavePackage(BP->GetOutermost(), BP, *FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir() / TEXT("Moedas/BP_Moeda.uasset")), Args);
                }
            } else Result = TEXT("Missing blueprint or graph source");
            FFileHelper::SaveStringToFile(Result, *(Dir / TEXT("native_result.log")));
            return true;
        }), 1.0f);
    }
    virtual void ShutdownModule() override { FTSTicker::GetCoreTicker().RemoveTicker(Handle); }
};
IMPLEMENT_MODULE(FMoedasBuilderModule, MoedasBuilder)

