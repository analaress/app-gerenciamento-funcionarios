import { useState } from "react";
import { Plus, Download, Send, FileText, ChevronRight, Check, Loader2 } from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { SendEmailFlow } from "./SendEmailFlow";
import {
  colaboradores,
  documentos as mockDocs,
  calcularINSS,
  calcularIRRF,
  Colaborador,
  Documento,
} from "../data/mockData";

const statusColors: Record<string, string> = {
  Pendente: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  "Em Conferência": "bg-blue-100 text-blue-700 hover:bg-blue-100",
  Gerado: "bg-purple-100 text-purple-700 hover:bg-purple-100",
  Enviado: "bg-green-100 text-green-700 hover:bg-green-100",
  "Erro Geração": "bg-red-100 text-red-700 hover:bg-red-100",
  "Erro Envio": "bg-orange-100 text-orange-700 hover:bg-orange-100",
};

const competencias = ["Setembro/2026", "Agosto/2026", "Julho/2026", "Junho/2026"];
const steps = ["Selecionar Colaborador", "Revisar Dados", "Conferência", "Concluído"];

interface WizardState {
  step: 1 | 2 | 3 | 4;
  colaboradorId: string;
  competencia: string;
  horasExtras: number;
  adiantamento: number;
  generating: boolean;
  generatedId?: string;
  sendPhase: boolean;
}

// ─── Holerite preview ─────────────────────────────────────────────────────────

function PreviewRecibo({
  col,
  competencia,
  horasExtras,
  adiantamento,
}: {
  col: Colaborador;
  competencia: string;
  horasExtras: number;
  adiantamento: number;
}) {
  const inss = Math.round(calcularINSS(col.salario));
  const baseIRRF = col.salario - inss;
  const irrf = Math.max(0, Math.round(calcularIRRF(baseIRRF)));
  const totalProventos = col.salario + horasExtras;
  const totalDescontos = inss + irrf + adiantamento;
  const liquido = Math.max(0, totalProventos - totalDescontos);
  const fmt = (v: number) => v.toLocaleString("pt-BR", { minimumFractionDigits: 2 });

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden text-[11px] leading-tight shadow-sm">
      {/* Header */}
      <div className="bg-blue-700 text-white px-5 py-3 flex items-center justify-between">
        <p className="font-bold text-sm tracking-wide uppercase">Holerite de Pagamento</p>
        <p className="text-blue-200">{competencia}</p>
      </div>

      {/* Employee info row 1 */}
      <div className="grid grid-cols-3 border-b border-gray-300">
        <div className="px-3 py-2 border-r border-gray-300">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Colaborador</p>
          <p className="font-semibold text-gray-800 text-xs">{col.nome}</p>
        </div>
        <div className="px-3 py-2 border-r border-gray-300">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">CPF</p>
          <p className="font-semibold text-gray-800">{col.cpf}</p>
        </div>
        <div className="px-3 py-2">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Função / Cargo</p>
          <p className="font-semibold text-gray-800">{col.cargo}</p>
        </div>
      </div>

      {/* Employee info row 2 */}
      <div className="grid grid-cols-3 border-b border-gray-300">
        <div className="px-3 py-2 border-r border-gray-300">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Empresa</p>
          <p className="font-semibold text-gray-800">{col.empresa}</p>
        </div>
        <div className="px-3 py-2 border-r border-gray-300">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Admissão</p>
          <p className="font-semibold text-gray-800">
            {new Date(col.dataAdmissao + "T12:00:00").toLocaleDateString("pt-BR")}
          </p>
        </div>
        <div className="px-3 py-2">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Referência</p>
          <p className="font-semibold text-gray-800">{competencia}</p>
        </div>
      </div>

      {/* Main table */}
      <div className="grid grid-cols-2">
        {/* Proventos */}
        <div className="border-r border-gray-300 flex flex-col">
          <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-300 flex justify-between">
            <span className="font-semibold text-gray-600 text-[10px] uppercase tracking-wide">Proventos</span>
            <span className="font-semibold text-gray-600 text-[10px] uppercase tracking-wide">Valor</span>
          </div>
          <div className="px-3 py-1.5 flex justify-between border-b border-gray-200">
            <span className="text-gray-700">Salário Base</span>
            <span className="font-medium text-gray-900 tabular-nums">{fmt(col.salario)}</span>
          </div>
          {horasExtras > 0 && (
            <div className="px-3 py-1.5 flex justify-between border-b border-gray-200">
              <span className="text-gray-700">Horas Extras / Adicionais</span>
              <span className="font-medium text-gray-900 tabular-nums">{fmt(horasExtras)}</span>
            </div>
          )}
          <div className="mt-auto px-3 py-2 bg-gray-50 border-t border-gray-300 flex justify-between items-center">
            <span className="font-bold text-gray-800">Total Proventos</span>
            <span className="font-bold text-gray-900 tabular-nums">{fmt(totalProventos)}</span>
          </div>
        </div>

        {/* Deduções */}
        <div className="flex flex-col">
          <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-300 flex justify-between">
            <span className="font-semibold text-gray-600 text-[10px] uppercase tracking-wide">Deduções</span>
            <span className="font-semibold text-gray-600 text-[10px] uppercase tracking-wide">Valor</span>
          </div>
          <div className="px-3 py-1.5 flex justify-between border-b border-gray-200">
            <span className="text-gray-700">INSS</span>
            <span className="font-medium text-red-600 tabular-nums">{fmt(inss)}</span>
          </div>
          <div className="px-3 py-1.5 flex justify-between border-b border-gray-200">
            <span className="text-gray-700">IRRF</span>
            <span className={`font-medium tabular-nums ${irrf > 0 ? "text-red-600" : "text-gray-300"}`}>
              {irrf > 0 ? fmt(irrf) : "—"}
            </span>
          </div>
          {adiantamento > 0 && (
            <div className="px-3 py-1.5 flex justify-between border-b border-gray-200">
              <span className="text-gray-700">Adiantamento / Descontos</span>
              <span className="font-medium text-red-600 tabular-nums">{fmt(adiantamento)}</span>
            </div>
          )}
          <div className="mt-auto px-3 py-2 bg-red-50 border-t border-gray-300 flex justify-between items-center">
            <span className="font-bold text-gray-700">Total Deduções</span>
            <span className="font-bold text-red-700 tabular-nums">{fmt(totalDescontos)}</span>
          </div>
        </div>
      </div>

      {/* Líquido footer */}
      <div className="bg-blue-700 px-5 py-3 flex justify-between items-center">
        <span className="font-bold text-white text-xs uppercase tracking-wide">Líquido a Receber</span>
        <span className="font-bold text-white text-base tabular-nums">R$ {fmt(liquido)}</span>
      </div>
    </div>
  );
}

// ─── Step indicator ───────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {steps.map((label, i) => {
        const num = i + 1;
        const done = num < current;
        const active = num === current;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                  done
                    ? "bg-blue-600 text-white"
                    : active
                    ? "bg-blue-700 text-white ring-4 ring-blue-100"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {done ? <Check className="w-3.5 h-3.5" /> : num}
              </div>
              <span
                className={`text-xs mt-1.5 font-medium whitespace-nowrap ${
                  active ? "text-blue-700" : done ? "text-gray-500" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mt-[-14px] mx-1 ${done ? "bg-blue-600" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Wizard panel ─────────────────────────────────────────────────────────────

function WizardPanel({
  wizard,
  setWizard,
  onComplete,
}: {
  wizard: WizardState;
  setWizard: (w: WizardState | null) => void;
  onComplete: (doc: Documento) => void;
}) {
  const col = colaboradores.find((c) => c.id === wizard.colaboradorId);

  const inss = col ? Math.round(calcularINSS(col.salario)) : 0;
  const baseIRRF = col ? col.salario - inss : 0;
  const irrf = Math.round(calcularIRRF(baseIRRF));
  const liquido = col ? col.salario + wizard.horasExtras - inss - irrf - wizard.adiantamento : 0;

  const handleGenerate = () => {
    setWizard({ ...wizard, step: 4, generating: true, sendPhase: false });
    setTimeout(() => {
      const newDoc: Documento = {
        id: `D${Date.now()}`,
        colaboradorId: wizard.colaboradorId,
        colaboradorNome: col?.nome ?? "",
        colaboradorCpf: col?.cpf ?? "",
        empresa: col?.empresa ?? "",
        tipo: "Recibo",
        status: "Gerado",
        competencia: wizard.competencia,
        dataGeracao: new Date().toISOString().split("T")[0],
        usuarioResponsavel: "RH Operacional",
      };
      onComplete(newDoc);
      setWizard({ ...wizard, step: 4, generating: false, generatedId: newDoc.id, sendPhase: false });
    }, 2000);
  };

  return (
    <div className="p-8">
      <StepIndicator current={wizard.step} />

      {/* Step 1 */}
      {wizard.step === 1 && (
        <div className="max-w-lg space-y-5">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Colaborador</label>
            <Select
              value={wizard.colaboradorId}
              onValueChange={(v) => setWizard({ ...wizard, colaboradorId: v })}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Selecione o colaborador..." />
              </SelectTrigger>
              <SelectContent>
                {colaboradores.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.nome} — {c.empresa}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Competência</label>
            <Select
              value={wizard.competencia}
              onValueChange={(v) => setWizard({ ...wizard, competencia: v })}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Selecione a competência..." />
              </SelectTrigger>
              <SelectContent>
                {competencias.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {col && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                {col.nome.split(" ").slice(0, 2).map((n) => n[0]).join("")}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{col.nome}</p>
                <p className="text-xs text-gray-500">{col.cargo} · {col.empresa}</p>
              </div>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={() => setWizard(null)} className="flex-1">
              Cancelar
            </Button>
            <Button
              className="flex-1 bg-blue-700 hover:bg-blue-800"
              disabled={!wizard.colaboradorId || !wizard.competencia}
              onClick={() => setWizard({ ...wizard, step: 2 })}
            >
              Próximo <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2 */}
      {wizard.step === 2 && col && (
        <div className="max-w-lg space-y-5">
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
              Dados preenchidos automaticamente
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-gray-400">Colaborador</p>
                <p className="font-medium text-gray-800">{col.nome}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Competência</p>
                <p className="font-medium text-gray-800">{wizard.competencia}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Salário Bruto</p>
                <p className="font-medium text-gray-800">
                  R$ {col.salario.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Empresa</p>
                <p className="font-medium text-gray-800">{col.empresa}</p>
              </div>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">
              Horas extras / adicionais (R$)
            </label>
            <Input
              type="number"
              min={0}
              value={wizard.horasExtras || ""}
              onChange={(e) => setWizard({ ...wizard, horasExtras: parseFloat(e.target.value) || 0 })}
              placeholder="0,00"
              className="h-10"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">
              Adiantamento / descontos (R$)
            </label>
            <Input
              type="number"
              min={0}
              value={wizard.adiantamento || ""}
              onChange={(e) => setWizard({ ...wizard, adiantamento: parseFloat(e.target.value) || 0 })}
              placeholder="0,00"
              className="h-10"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={() => setWizard({ ...wizard, step: 1 })} className="flex-1">
              Voltar
            </Button>
            <Button
              className="flex-1 bg-blue-700 hover:bg-blue-800"
              onClick={() => setWizard({ ...wizard, step: 3 })}
            >
              Revisar <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3 */}
      {wizard.step === 3 && col && (
        <div className="max-w-lg space-y-5">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="bg-blue-700 px-5 py-4">
              <p className="text-white font-semibold">Recibo de Pagamento</p>
              <p className="text-blue-200 text-sm">{wizard.competencia}</p>
            </div>
            <div className="p-5 space-y-1">
              <div className="pb-3 mb-3 border-b border-gray-100">
                <p className="text-sm font-semibold text-gray-900">{col.nome}</p>
                <p className="text-xs text-gray-500">{col.cargo} · CPF {col.cpf}</p>
                <p className="text-xs text-gray-500">{col.empresa}</p>
              </div>
              {[
                { label: "Salário Bruto", value: col.salario, type: "credit" },
                ...(wizard.horasExtras > 0
                  ? [{ label: "Horas Extras / Adicionais", value: wizard.horasExtras, type: "credit" }]
                  : []),
                { label: "INSS", value: -inss, type: "debit" },
                { label: "IRRF", value: -irrf, type: "debit" },
                ...(wizard.adiantamento > 0
                  ? [{ label: "Adiantamento / Descontos", value: -wizard.adiantamento, type: "debit" }]
                  : []),
              ].map(({ label, value, type }) => (
                <div key={label} className="flex items-center justify-between py-1.5">
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className={`text-sm font-medium ${type === "credit" ? "text-gray-900" : "text-red-600"}`}>
                    {type === "debit" ? "- " : ""}R${" "}
                    {Math.abs(value).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between pt-3 mt-2 border-t-2 border-gray-200">
                <span className="text-base font-bold text-gray-900">Salário Líquido</span>
                <span className="text-lg font-bold text-blue-700">
                  R$ {liquido.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setWizard({ ...wizard, step: 2 })} className="flex-1">
              Voltar
            </Button>
            <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleGenerate}>
              Gerar PDF
            </Button>
          </div>
        </div>
      )}

      {/* Step 4 */}
      {wizard.step === 4 && (
        <div className={wizard.sendPhase ? "max-w-md" : "max-w-2xl"}>
          {wizard.generating ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
              <p className="font-medium text-gray-700">Gerando PDF...</p>
              <p className="text-sm text-gray-400 mt-1">Aguarde enquanto o documento é montado</p>
            </div>
          ) : wizard.sendPhase ? (
            col && (
              <SendEmailFlow
                email={col.email}
                docLabel={`Recibo — ${wizard.competencia}`}
                collaboratorName={col.nome}
                onBack={() => setWizard({ ...wizard, sendPhase: false })}
                onDone={() => setWizard(null)}
              />
            )
          ) : (
            col && (
              <div>
                <div className="flex items-center gap-2 mb-5 bg-green-50 border border-green-200 rounded-lg px-4 py-2.5">
                  <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm font-medium text-green-700">
                    Recibo gerado com sucesso — visualize abaixo antes de baixar
                  </span>
                </div>

                <PreviewRecibo
                  col={col}
                  competencia={wizard.competencia}
                  horasExtras={wizard.horasExtras}
                  adiantamento={wizard.adiantamento}
                />

                <div className="flex gap-3 mt-5">
                  <Button className="flex-1 gap-2 bg-blue-700 hover:bg-blue-800">
                    <Download className="w-4 h-4" />
                    Baixar PDF
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1 gap-2"
                    onClick={() => setWizard({ ...wizard, sendPhase: true })}
                  >
                    <Send className="w-4 h-4" />
                    Enviar por E-mail
                  </Button>
                </div>
                <button
                  className="mt-4 text-sm text-gray-400 hover:text-gray-600 block mx-auto"
                  onClick={() => setWizard(null)}
                >
                  Fechar
                </button>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Recibos() {
  const [docs, setDocs] = useState<Documento[]>(mockDocs.filter((d) => d.tipo === "Recibo"));
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [wizard, setWizard] = useState<WizardState | null>(null);
  const [detailSend, setDetailSend] = useState(false);

  const handleNewRecibo = () => {
    setSelectedId(null);
    setDetailSend(false);
    setWizard({
      step: 1,
      colaboradorId: "",
      competencia: "",
      horasExtras: 0,
      adiantamento: 0,
      generating: false,
      sendPhase: false,
    });
  };

  const handleComplete = (doc: Documento) => {
    setDocs((prev) => [doc, ...prev]);
  };

  const handleDocStatusUpdate = (docId: string, status: "Enviado" | "Erro Envio") => {
    setDocs((prev) =>
      prev.map((d) =>
        d.id === docId
          ? {
              ...d,
              status,
              ...(status === "Enviado"
                ? { dataEnvio: new Date().toISOString().split("T")[0] }
                : {}),
            }
          : d
      )
    );
  };

  const selectedDoc = docs.find((d) => d.id === selectedId);
  const selectedCol = selectedDoc
    ? colaboradores.find((c) => c.id === selectedDoc.colaboradorId)
    : null;

  const showWizard = wizard !== null;
  const showDetailSend = !showWizard && detailSend && !!selectedDoc;
  const showDetail = !showWizard && !detailSend && !!selectedDoc;
  const showEmpty = !showWizard && !detailSend && !selectedDoc;

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-900">Recibos</h1>
            <Button size="sm" className="bg-blue-700 hover:bg-blue-800 gap-1.5" onClick={handleNewRecibo}>
              <Plus className="w-3.5 h-3.5" />
              Novo
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {docs.map((doc) => (
            <button
              key={doc.id}
              onClick={() => {
                setSelectedId(doc.id);
                setWizard(null);
                setDetailSend(false);
              }}
              className={`w-full text-left px-5 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                selectedId === doc.id && !wizard ? "bg-blue-50 border-l-2 border-l-blue-600" : ""
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <p className="text-sm font-semibold text-gray-900 truncate flex-1">
                  {doc.colaboradorNome}
                </p>
                <Badge className={`text-xs ml-2 flex-shrink-0 ${statusColors[doc.status]}`}>
                  {doc.status}
                </Badge>
              </div>
              <p className="text-xs text-gray-400">{doc.empresa}</p>
              {doc.competencia && (
                <p className="text-xs text-gray-500 mt-1">{doc.competencia}</p>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {showWizard && (
          <WizardPanel wizard={wizard!} setWizard={setWizard} onComplete={handleComplete} />
        )}

        {showDetailSend && selectedDoc && selectedCol && (
          <div className="p-8">
            <SendEmailFlow
              email={selectedCol.email}
              docLabel={`Recibo — ${selectedDoc.competencia}`}
              collaboratorName={selectedDoc.colaboradorNome}
              onBack={() => setDetailSend(false)}
              onDone={() => setDetailSend(false)}
              onSendSuccess={() => handleDocStatusUpdate(selectedDoc.id, "Enviado")}
            />
          </div>
        )}

        {showDetail && selectedDoc && (
          <div className="p-8 max-w-lg">
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden mb-5">
              <div className="bg-blue-700 px-6 py-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-white font-semibold text-lg">{selectedDoc.colaboradorNome}</p>
                    <p className="text-blue-200 text-sm mt-0.5">{selectedDoc.empresa}</p>
                  </div>
                  <Badge className="bg-white/20 text-white hover:bg-white/20 border-0">
                    {selectedDoc.competencia}
                  </Badge>
                </div>
              </div>
              <div className="p-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">CPF</span>
                  <span className="font-medium text-gray-800">{selectedDoc.colaboradorCpf}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Status</span>
                  <Badge className={statusColors[selectedDoc.status]}>{selectedDoc.status}</Badge>
                </div>
                {selectedDoc.dataGeracao && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Gerado em</span>
                    <span className="font-medium text-gray-800">
                      {new Date(selectedDoc.dataGeracao + "T12:00:00").toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                )}
                {selectedDoc.dataEnvio && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Enviado em</span>
                    <span className="font-medium text-gray-800">
                      {new Date(selectedDoc.dataEnvio + "T12:00:00").toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Responsável</span>
                  <span className="font-medium text-gray-800">{selectedDoc.usuarioResponsavel}</span>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <Button className="flex-1 gap-2 bg-blue-700 hover:bg-blue-800">
                <Download className="w-4 h-4" />
                Baixar PDF
              </Button>
              {(selectedDoc.status === "Gerado" || selectedDoc.status === "Erro Envio") && (
                <Button
                  variant="outline"
                  className="flex-1 gap-2"
                  onClick={() => setDetailSend(true)}
                >
                  <Send className="w-4 h-4" />
                  {selectedDoc.status === "Erro Envio" ? "Reenviar" : "Enviar"}
                </Button>
              )}
            </div>
          </div>
        )}

        {showEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <FileText className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm mb-4">Selecione um recibo ou crie um novo</p>
            <Button onClick={handleNewRecibo} className="gap-2 bg-blue-700 hover:bg-blue-800">
              <Plus className="w-4 h-4" />
              Novo Recibo
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
