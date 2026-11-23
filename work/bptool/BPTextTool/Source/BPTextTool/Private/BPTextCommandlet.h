#pragma once
// Commandlet de edicao de Blueprints por texto (T3D, o mesmo formato do copiar/colar do editor).
// Uso: UnrealEditor-Cmd.exe Projeto.uproject -run=BPText -script=C:/caminho/ops.json -log=C:/caminho/result.log
// ops.json: [ { "op": "...", "bp": "/Game/Asset", ... }, ... ]
//   export   { out, graph? }                -> grava todos os nos do grafo em texto
//   list     { graph? }                     -> lista nos e pinos (com ligacoes) no log
//   delete   { nodes: [nome, ...], graph? }
//   import   { file, graph? }               -> cola nos a partir de um arquivo de texto
//   duplicate { node, name, x, y, graph? }  -> clona um no existente, sem ligacoes
//   link     { from: "No.Pino", to: "No.Pino", graph? }
//   unlink   { from: "No.Pino", to?: "No.Pino", graph? }  (sem "to": quebra todas as ligacoes do pino)
//   setdefault { pin: "No.Pino", value, graph? }
//   compile  {}                              -> compila e registra erros/avisos
//   save     {}                              -> compila e salva se nao houver erros
// "graph" e o nome do grafo (padrao: EventGraph).
#include "Modules/ModuleManager.h"
#include "Commandlets/Commandlet.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "EdGraphUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"
#include "UObject/SavePackage.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "BPTextCommandlet.generated.h"

UCLASS()
class UBPTextCommandlet : public UCommandlet
{
	GENERATED_BODY()
public:
	UBPTextCommandlet() { IsClient = false; IsEditor = true; IsServer = false; LogToConsole = true; }

	FString Out;
	int32 Failures = 0;

	void Log(const FString& S) { Out += S + TEXT("\n"); UE_LOG(LogTemp, Display, TEXT("%s"), *S); }
	void Fail(const FString& S) { ++Failures; Log(TEXT("ERRO: ") + S); }

	static UEdGraph* FindGraph(UBlueprint* BP, const FString& Name)
	{
		TArray<UEdGraph*> Graphs;
		BP->GetAllGraphs(Graphs);
		for (UEdGraph* G : Graphs) if (G && G->GetName() == Name) return G;
		return nullptr;
	}

	static UEdGraphNode* FindNode(UEdGraph* G, const FString& Name)
	{
		for (UEdGraphNode* N : G->Nodes) if (N && N->GetName() == Name) return N;
		return nullptr;
	}

	UEdGraphPin* FindPin(UEdGraph* G, const FString& Ref)
	{
		FString NodeName, PinName;
		if (!Ref.Split(TEXT("."), &NodeName, &PinName)) { Fail(TEXT("referencia invalida: ") + Ref); return nullptr; }
		UEdGraphNode* N = FindNode(G, NodeName);
		if (!N) { Fail(TEXT("no nao encontrado: ") + NodeName); return nullptr; }
		for (UEdGraphPin* P : N->Pins) if (P && P->PinName.ToString() == PinName) return P;
		FString Names;
		for (UEdGraphPin* P : N->Pins) Names += P->PinName.ToString() + TEXT(", ");
		Fail(FString::Printf(TEXT("pino '%s' nao existe em %s (pinos: %s)"), *PinName, *NodeName, *Names));
		return nullptr;
	}

	void ListGraph(UEdGraph* G)
	{
		for (UEdGraphNode* N : G->Nodes)
		{
			if (!N) continue;
			Log(FString::Printf(TEXT("NODE %s [%s] \"%s\" %s"), *N->GetName(), *N->GetClass()->GetName(),
				*N->GetNodeTitle(ENodeTitleType::ListView).ToString().Replace(TEXT("\n"), TEXT(" | ")), *N->NodeComment.Replace(TEXT("\n"), TEXT(" "))));
			for (UEdGraphPin* P : N->Pins)
			{
				if (!P || P->bHidden) continue;
				FString Links;
				for (UEdGraphPin* L : P->LinkedTo) Links += L->GetOwningNode()->GetName() + TEXT(".") + L->PinName.ToString() + TEXT(" ");
				Log(FString::Printf(TEXT("   %s %s (%s) def='%s' -> %s"), P->Direction == EGPD_Input ? TEXT("in ") : TEXT("out"),
					*P->PinName.ToString(), *P->PinType.PinCategory.ToString(), *P->GetDefaultAsString(), *Links));
			}
		}
	}

	bool Compile(UBlueprint* BP)
	{
		FCompilerResultsLog CLog;
		FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::None, &CLog);
		Log(FString::Printf(TEXT("COMPILE %s errors=%d warnings=%d status=%d"), *BP->GetPathName(), CLog.NumErrors, CLog.NumWarnings, int32(BP->Status)));
		for (const TSharedRef<FTokenizedMessage>& M : CLog.Messages) Log(TEXT("   ") + M->ToText().ToString());
		return CLog.NumErrors == 0 && BP->Status != BS_Error;
	}

	virtual int32 Main(const FString& Params) override
	{
		FString ScriptPath, ResultLogPath;
		FParse::Value(*Params, TEXT("script="), ScriptPath);
		FParse::Value(*Params, TEXT("log="), ResultLogPath);
		FString Json;
		if (!FFileHelper::LoadFileToString(Json, *ScriptPath)) { UE_LOG(LogTemp, Error, TEXT("script nao encontrado: %s"), *ScriptPath); return 1; }
		TArray<TSharedPtr<FJsonValue>> Ops;
		if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Ops)) { UE_LOG(LogTemp, Error, TEXT("JSON invalido")); return 1; }

		for (const TSharedPtr<FJsonValue>& V : Ops)
		{
			const TSharedPtr<FJsonObject> O = V->AsObject();
			const FString Op = O->GetStringField(TEXT("op"));
			const FString BPPath = O->GetStringField(TEXT("bp"));
			FString GraphName = TEXT("EventGraph");
			O->TryGetStringField(TEXT("graph"), GraphName);
			Log(FString::Printf(TEXT("== %s %s"), *Op, *BPPath));

			UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *BPPath);
			if (!BP) { Fail(TEXT("blueprint nao encontrado")); continue; }
			UEdGraph* G = FindGraph(BP, GraphName);
			if (!G && Op != TEXT("compile") && Op != TEXT("save")) { Fail(TEXT("grafo nao encontrado: ") + GraphName); continue; }

			if (Op == TEXT("export"))
			{
				TSet<UObject*> Nodes;
				for (UEdGraphNode* N : G->Nodes) if (N) Nodes.Add(N);
				FString Text;
				FEdGraphUtilities::ExportNodesToText(Nodes, Text);
				FFileHelper::SaveStringToFile(Text, *O->GetStringField(TEXT("out")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
				Log(FString::Printf(TEXT("exportados %d nos"), Nodes.Num()));
			}
			else if (Op == TEXT("list")) ListGraph(G);
			else if (Op == TEXT("delete"))
			{
				for (const TSharedPtr<FJsonValue>& NV : O->GetArrayField(TEXT("nodes")))
				{
					UEdGraphNode* N = FindNode(G, NV->AsString());
					if (!N) { Fail(TEXT("no nao encontrado: ") + NV->AsString()); continue; }
					FBlueprintEditorUtils::RemoveNode(BP, N, true);
					Log(TEXT("removido ") + NV->AsString());
				}
				FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			}
			else if (Op == TEXT("import"))
			{
				FString Text;
				if (!FFileHelper::LoadFileToString(Text, *O->GetStringField(TEXT("file")))) { Fail(TEXT("arquivo de nos nao encontrado")); continue; }
				if (!FEdGraphUtilities::CanImportNodesFromText(G, Text)) { Fail(TEXT("texto nao pode ser importado neste grafo")); continue; }
				TSet<UEdGraphNode*> Imported;
				FEdGraphUtilities::ImportNodesFromText(G, Text, Imported);
				for (UEdGraphNode* N : Imported)
				{
					N->CreateNewGuid();
					N->PostPasteNode();
					N->ReconstructNode();
					Log(FString::Printf(TEXT("importado %s \"%s\""), *N->GetName(), *N->GetNodeTitle(ENodeTitleType::ListView).ToString()));
				}
				FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			}
			else if (Op == TEXT("duplicate"))
			{
				// Clona um no existente (sem ligacoes). Util para nos que o editor recusa colar.
				UEdGraphNode* Src = FindNode(G, O->GetStringField(TEXT("node")));
				const FString NewName = O->GetStringField(TEXT("name"));
				if (!Src) { Fail(TEXT("no nao encontrado: ") + O->GetStringField(TEXT("node"))); continue; }
				if (FindNode(G, NewName)) { Fail(TEXT("ja existe no com nome ") + NewName); continue; }
				G->Modify();
				UEdGraphNode* N = DuplicateObject<UEdGraphNode>(Src, G, FName(*NewName));
				for (UEdGraphPin* P : N->Pins) { P->LinkedTo.Empty(); P->PinId = FGuid::NewGuid(); }
				N->CreateNewGuid();
				N->NodePosX = int32(O->GetNumberField(TEXT("x")));
				N->NodePosY = int32(O->GetNumberField(TEXT("y")));
				G->AddNode(N, false, false);
				Log(FString::Printf(TEXT("duplicado %s -> %s"), *Src->GetName(), *N->GetName()));
				FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			}
			else if (Op == TEXT("link") || Op == TEXT("unlink"))
			{
				UEdGraphPin* A = FindPin(G, O->GetStringField(TEXT("from")));
				FString ToRef;
				const bool bHasTo = O->TryGetStringField(TEXT("to"), ToRef);
				UEdGraphPin* B = bHasTo ? FindPin(G, ToRef) : nullptr;
				if (!A || (bHasTo && !B)) continue;
				const UEdGraphSchema* S = G->GetSchema();
				if (Op == TEXT("link"))
				{
					if (S->TryCreateConnection(A, B)) Log(TEXT("ligado ") + O->GetStringField(TEXT("from")) + TEXT(" -> ") + ToRef);
					else Fail(TEXT("nao foi possivel ligar ") + O->GetStringField(TEXT("from")) + TEXT(" -> ") + ToRef + TEXT(": ") + S->CanCreateConnection(A, B).Message.ToString());
				}
				else
				{
					if (B) S->BreakSinglePinLink(A, B); else S->BreakPinLinks(*A, true);
					Log(TEXT("desligado ") + O->GetStringField(TEXT("from")));
				}
				FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
			}
			else if (Op == TEXT("setdefault"))
			{
				UEdGraphPin* P = FindPin(G, O->GetStringField(TEXT("pin")));
				if (!P) continue;
				G->GetSchema()->TrySetDefaultValue(*P, O->GetStringField(TEXT("value")));
				Log(TEXT("default ") + O->GetStringField(TEXT("pin")) + TEXT(" = ") + P->GetDefaultAsString());
				FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
			}
			else if (Op == TEXT("compile")) { if (!Compile(BP)) ++Failures; }
			else if (Op == TEXT("save"))
			{
				if (!Compile(BP)) { Fail(TEXT("nao salvo: erros de compilacao")); continue; }
				UPackage* Pkg = BP->GetOutermost();
				const FString File = FPackageName::LongPackageNameToFilename(Pkg->GetName(), FPackageName::GetAssetPackageExtension());
				FSavePackageArgs Args;
				Args.TopLevelFlags = RF_Public | RF_Standalone;
				if (UPackage::SavePackage(Pkg, BP, *FPaths::ConvertRelativePathToFull(File), Args)) Log(TEXT("salvo ") + File);
				else Fail(TEXT("falha ao salvar ") + File);
			}
			else Fail(TEXT("operacao desconhecida: ") + Op);
		}
		Log(FString::Printf(TEXT("FIM falhas=%d"), Failures));
		if (!ResultLogPath.IsEmpty()) FFileHelper::SaveStringToFile(Out, *ResultLogPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		return Failures ? 1 : 0;
	}
};

