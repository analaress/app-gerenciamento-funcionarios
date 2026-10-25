import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { Plus, Download, Send, FileX2, ChevronRight, Check, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { SendEmailFlow } from "./SendEmailFlow";
import { ConferenciaEditor } from "./ConferenciaEditor";
import { RescisaoPreview } from "./RescisaoPreview";
import { calcularRescisao, Colaborador } from "../data/mockData";
import {
  ApiError,
  ApiRescisao,
  RescisaoDoc,
  corrigirRescisao,
  criarRescisao,
  enviarRescisao,
  gerarRescisao,
  getColaboradores,
  getMotivos,
  listarRescisoes,
  obterRescisao,
  pdfUrl,
  toRescisaoDoc,
} from "../lib/api";
import {
  ItemEdicao,
  edicaoParaPayload,
  itensParaEdicao,
  montarItens,
  motivoParaCalculo,
  temValorInvalido,
  totalBruto,
} from "../lib/rescisaoItens";

const statusColors: Record<string, string> = {
  Pendente: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  "Em Conferência": "bg-blue-100 text-blue-700 hover:bg-blue-100",
  Gerado: "bg-purple-100 text-purple-700 hover:bg-purple-100",
  Enviado: "bg-green-100 text-green-700 hover:bg-green-100",
  "Erro Geração": "bg-red-100 text-red-700 hover:bg-red-100",
  "Erro Envio": "bg-red-100 text-red-700 hover:bg-red-100",
};

const steps = ["Selecionar Colaborador", "Revisar Valores", "Conferência", "Concluído"];

interface WizardState {
  step: 1 | 2 | 3 | 4;
  colaboradorId: string;
  dataDesligamento: string;
  motivo: string;
  generating: boolean;
  /** id da rescisão já criada na API (permite corrigir/gerar de novo sem duplicar) */
  rescisaoId?: number;
  /** rescisão como foi salva e gerada pela API (alimenta o documento exibido) */
  resultado?: ApiRescisao;
  error?: string;
  sendPhase: boolean;
  /** valores da conferência (editáveis); vazio = ainda vale o cálculo automático */
  itens?: ItemEdicao[];
  observacoes?: string;
}

// ─── Wizard step indicator ───────────────────────────────────────────────────

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
                    ? "bg-red-600 text-white"
                    : active
                    ? "bg-red-700 text-white ring-4 ring-red-100"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {done ? <Check className="w-3.5 h-3.5" /> : num}
              </div>
              <span
                className={`text-xs mt-1.5 font-medium whitespace-nowrap ${
                  active ? "text-red-700" : done ? "text-gray-500" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`flex-1 h-0.5 mt-[-14px] mx-1 ${done ? "bg-red-600" : "bg-gray-200"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Wizard panel ────────────────────────────────────────────────────────────

function WizardPanel({
  wizard,
  setWizard,
  colaboradores,
  motivos,
  onComplete,
  onRefresh,
  onEnviar,
}: {
  wizard: WizardState;
  setWizard: (w: WizardState | null) => void;
  colaboradores: Colaborador[];
  motivos: string[];
  onComplete: (doc: RescisaoDoc) => void;
  onRefresh: () => void;
  onEnviar: (id: number, email: string) => Promise<void>;
}) {
  const col = colaboradores.find((c) => c.id === wizard.colaboradorId);
  const valores =
    col && wizard.dataDesligamento && wizard.motivo
      ? calcularRescisao(col, wizard.dataDesligamento, motivoParaCalculo(wizard.motivo))
      : null;

  /** Valores da conferência: os editados à mão ou, se ninguém mexeu, o cálculo automático. */
  const calculados = () =>
    col && valores ? itensParaEdicao(montarItens(col, valores, wizard.dataDesligamento)) : [];
  const itensConferencia = wizard.itens ?? calculados();

  const montarPayload = () => ({
    colaborador_id: Number(col!.id),
    data_desligamento: wizard.dataDesligamento,
    causa_afastamento: wizard.motivo,
    observacoes: wizard.observacoes?.trim() || null,
    itens: edicaoParaPayload(itensConferencia),
  });

  const [salvando, setSalvando] = useState(false);
  const [avisoSalvar, setAvisoSalvar] = useState<{ ok: boolean; texto: string } | null>(null);

  /** Guarda as edições na API sem gerar o PDF (a rescisão fica "Em Conferência" e pode ser reaberta). */
  const handleSalvar = async () => {
    if (!col) return;
    setSalvando(true);
    setAvisoSalvar(null);
    try {
      const payload = montarPayload();
      const salva = wizard.rescisaoId
        ? await corrigirRescisao(wizard.rescisaoId, payload)
        : await criarRescisao(payload);
      setWizard({ ...wizard, rescisaoId: salva.id });
      onComplete(toRescisaoDoc(salva, colaboradores));
      setAvisoSalvar({ ok: true, texto: "Edições salvas. Você pode gerar o PDF agora ou continuar depois." });
    } catch (e) {
      setAvisoSalvar({
        ok: false,
        texto: e instanceof ApiError ? e.message : "Não foi possível salvar as edições.",
      });
    } finally {
      setSalvando(false);
    }
  };

  /** Cria (ou corrige) a rescisão na API e pede para o backend gerar o PDF. */
  const handleGenerate = async (apenasGerar = false) => {
    if (!col || !valores) return;
    setWizard({ ...wizard, step: 4, generating: true, sendPhase: false, error: undefined });

    let rescisaoId = wizard.rescisaoId;
    try {
      const payload = montarPayload();
      // "apenasGerar": repetir só a geração do PDF (dados já salvos na API)
      if (!(apenasGerar && rescisaoId)) {
        const salva = rescisaoId
          ? await corrigirRescisao(rescisaoId, payload)
          : await criarRescisao(payload);
        rescisaoId = salva.id;
      }

      const final = await gerarRescisao(rescisaoId!);

      onComplete(toRescisaoDoc(final, colaboradores));
      setWizard({ ...wizard, step: 4, generating: false, rescisaoId, resultado: final, sendPhase: false });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Erro inesperado ao gerar a rescisão.";
      setWizard({ ...wizard, step: 4, generating: false, rescisaoId, error: msg, sendPhase: false });
      onRefresh();
    }
  };

  const ativosColaboradores = colaboradores.filter((c) => c.situacao === "Ativo");

  return (
    <div className="p-8">
      <StepIndicator current={wizard.step} />

      {/* Step 1 — Select colaborador */}
      {wizard.step === 1 && (
        <div className="max-w-lg space-y-5">
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-800">Atenção</p>
              <p className="text-sm text-red-600 mt-0.5">
                Apenas colaboradores com situação <strong>Ativo</strong> podem ter rescisão iniciada.
              </p>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Colaborador</label>
            <Select
              value={wizard.colaboradorId}
              onValueChange={(v) => setWizard({ ...wizard, colaboradorId: v })}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Selecione o colaborador ativo..." />
              </SelectTrigger>
              <SelectContent>
                {ativosColaboradores.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.nome} — {c.empresa}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Data de Desligamento</label>
            <Input
              type="date"
              value={wizard.dataDesligamento}
              onChange={(e) => setWizard({ ...wizard, dataDesligamento: e.target.value })}
              className="h-10"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Motivo do Desligamento</label>
            <Select
              value={wizard.motivo}
              onValueChange={(v) => setWizard({ ...wizard, motivo: v })}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Selecione o motivo..." />
              </SelectTrigger>
              <SelectContent>
                {motivos.map((m) => (
                  <SelectItem key={m} value={m}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {col && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-gray-900">{col.nome}</p>
              <p className="text-xs text-gray-500">{col.cargo} · {col.empresa}</p>
              <p className="text-xs text-gray-500 mt-1">
                Admissão: {new Date(col.dataAdmissao + "T12:00:00").toLocaleDateString("pt-BR")}
              </p>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={() => setWizard(null)} className="flex-1">
              Cancelar
            </Button>
            <Button
              className="flex-1 bg-red-700 hover:bg-red-800"
              disabled={!wizard.colaboradorId || !wizard.dataDesligamento || !wizard.motivo}
              onClick={() => setWizard({ ...wizard, step: 2, itens: undefined })}
            >
              Próximo <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2 — Revisar Valores */}
      {wizard.step === 2 && col && valores && (
        <div className="max-w-lg space-y-5">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="bg-gray-800 px-5 py-3">
              <p className="text-white text-sm font-semibold">Valores Calculados — {wizard.motivo}</p>
              <p className="text-gray-400 text-xs mt-0.5">
                Desligamento: {new Date(wizard.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}
              </p>
            </div>
            <div className="p-5 space-y-1.5">
              {[
                { label: "Saldo de Salário", value: valores.saldoSalario },
                { label: "Férias Proporcionais", value: valores.feriasProporcionais },
                { label: "1/3 de Férias", value: valores.tercoFerias },
                { label: "13º Proporcional", value: valores.decimoTerceiroProporcional },
                ...(valores.avisoPrevioIndenizado > 0
                  ? [{ label: "Aviso Prévio Indenizado", value: valores.avisoPrevioIndenizado }]
                  : []),
                ...(valores.multaFgts > 0
                  ? [{ label: "Multa FGTS 40% (informativo)", value: valores.multaFgts }]
                  : []),
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className="text-sm font-medium text-gray-900">
                    R$ {value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between pt-3 border-t-2 border-gray-200">
                <span className="text-base font-bold text-gray-900">Total Bruto</span>
                <span className="text-lg font-bold text-red-700">
                  R$ {totalBruto(valores).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
            <p className="font-medium mb-1">FGTS depositado (referência)</p>
            <p className="text-amber-700">
              R$ {valores.fgtsDepositado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })} —
              sujeito à confirmação junto à Caixa Econômica Federal.
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setWizard({ ...wizard, step: 1 })} className="flex-1">
              Voltar
            </Button>
            <Button
              className="flex-1 bg-red-700 hover:bg-red-800"
              onClick={() => setWizard({ ...wizard, step: 3, itens: wizard.itens ?? calculados() })}
            >
              Conferir <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3 — Conferência (valores editáveis) */}
      {wizard.step === 3 && col && valores && (
        <div className="max-w-xl space-y-5">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="bg-red-700 px-6 py-5">
              <p className="text-white font-semibold text-lg">Conferência da Rescisão</p>
              <p className="text-red-200 text-sm mt-0.5">
                {wizard.motivo} · confira e corrija os valores se necessário
              </p>
            </div>
            <div className="p-6 space-y-5">
              <div className="pb-4 border-b border-gray-100">
                <p className="text-sm font-semibold text-gray-900">{col.nome}</p>
                <p className="text-xs text-gray-500">{col.cargo} · CPF {col.cpf}</p>
                <p className="text-xs text-gray-500">{col.empresa}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Admissão: {new Date(col.dataAdmissao + "T12:00:00").toLocaleDateString("pt-BR")} ·
                  Desligamento: {new Date(wizard.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}
                </p>
              </div>
              <ConferenciaEditor
                itens={itensConferencia}
                onChange={(itens) => setWizard({ ...wizard, itens })}
                observacoes={wizard.observacoes ?? ""}
                onObservacoes={(observacoes) => setWizard({ ...wizard, observacoes })}
                onRestaurar={() => setWizard({ ...wizard, itens: calculados() })}
                salario={col.salario}
              />
              {temValorInvalido(itensConferencia) && (
                <p className="text-xs text-red-600">
                  Há valores inválidos (destacados em vermelho). Use números, como 1234,56.
                </p>
              )}
            </div>
          </div>
          {avisoSalvar && (
            <div
              className={`flex items-start gap-2 rounded-lg border px-4 py-2.5 text-sm ${
                avisoSalvar.ok
                  ? "bg-green-50 border-green-200 text-green-700"
                  : "bg-red-50 border-red-200 text-red-700"
              }`}
            >
              {avisoSalvar.ok ? <Check className="w-4 h-4 mt-0.5 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
              <span>{avisoSalvar.texto}</span>
            </div>
          )}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => setWizard({ ...wizard, step: 2 })} className="flex-1">
              Voltar
            </Button>
            <Button
              variant="outline"
              className="flex-1 gap-2"
              disabled={salvando || temValorInvalido(itensConferencia) || edicaoParaPayload(itensConferencia).length === 0}
              onClick={handleSalvar}
            >
              {salvando && <Loader2 className="w-4 h-4 animate-spin" />}
              Salvar edições
            </Button>
            <Button
              className="w-full bg-red-700 hover:bg-red-800"
              disabled={temValorInvalido(itensConferencia) || edicaoParaPayload(itensConferencia).length === 0}
              onClick={() => handleGenerate()}
            >
              Gerar PDF
            </Button>
          </div>
        </div>
      )}

      {/* Step 4 — PDF preview / send flow */}
      {wizard.step === 4 && (
        <div className={wizard.sendPhase ? "max-w-md" : "max-w-3xl"}>
          {wizard.generating ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500">
              <Loader2 className="w-10 h-10 animate-spin text-red-600 mb-4" />
              <p className="font-medium text-gray-700">Gerando PDF...</p>
              <p className="text-sm text-gray-400 mt-1">Aguarde enquanto o documento é montado</p>
            </div>
          ) : wizard.error ? (
            <div className="max-w-lg">
              <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-red-800">Não foi possível gerar a rescisão</p>
                  <p className="text-sm text-red-600 mt-0.5">{wizard.error}</p>
                </div>
              </div>
              <div className="flex gap-3 mt-5">
                <Button variant="outline" className="flex-1" onClick={() => setWizard({ ...wizard, step: 3, error: undefined })}>
                  Voltar
                </Button>
                <Button className="flex-1 bg-red-700 hover:bg-red-800" onClick={() => handleGenerate(true)}>
                  Tentar novamente
                </Button>
              </div>
            </div>
          ) : wizard.sendPhase ? (
            col && (
              <SendEmailFlow
                email={col.email}
                docLabel={`Rescisão — ${new Date(wizard.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}`}
                collaboratorName={col.nome}
                pdfHref={wizard.rescisaoId ? pdfUrl(wizard.rescisaoId) : undefined}
                onSend={(email) => onEnviar(wizard.rescisaoId!, email)}
                onBack={() => setWizard({ ...wizard, sendPhase: false })}
                onDone={() => setWizard(null)}
              />
            )
          ) : (
            col && wizard.resultado && (
              <div>
                <div className="flex items-center gap-2 mb-5 bg-green-50 border border-green-200 rounded-lg px-4 py-2.5">
                  <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm font-medium text-green-700">
                    Rescisão gerada com sucesso — visualize abaixo antes de baixar
                  </span>
                </div>

                <RescisaoPreview rescisao={wizard.resultado!} col={col} />

                <div className="flex gap-3 mt-5">
                  <Button asChild className="flex-1 gap-2 bg-red-700 hover:bg-red-800">
                    <a href={pdfUrl(wizard.rescisaoId!)} target="_blank" rel="noreferrer">
                      <Download className="w-4 h-4" />
                      Baixar PDF
                    </a>
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
                <Button
                  variant="outline"
                  className="w-full mt-3"
                  onClick={() => setWizard({ ...wizard, step: 3, sendPhase: false })}
                >
                  Corrigir dados
                </Button>
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

// ─── Main page ───────────────────────────────────────────────────────────────

export function Rescisoes() {
  const [docs, setDocs] = useState<RescisaoDoc[]>([]);
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [motivos, setMotivos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [wizard, setWizard] = useState<WizardState | null>(null);
  const [detailSend, setDetailSend] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setLoadError(null);
      const [cols, mots] = await Promise.all([getColaboradores(), getMotivos()]);
      const rescisoes = await listarRescisoes();
      setColaboradores(cols);
      setMotivos(mots);
      setDocs(rescisoes.map((r) => toRescisaoDoc(r, cols)));
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Erro ao carregar dados da API.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // Vindo da tela de Colaboradores ("Iniciar Rescisão"): abre o assistente com a pessoa já selecionada
  const location = useLocation();
  const navigate = useNavigate();
  const preselecionado = useRef(false);
  useEffect(() => {
    const id = (location.state as { colaboradorId?: string } | null)?.colaboradorId;
    if (!id || loading || preselecionado.current) return;
    preselecionado.current = true;
    if (colaboradores.some((c) => c.id === id && c.situacao === "Ativo")) {
      setSelectedId(null);
      setWizard({
        step: 1,
        colaboradorId: id,
        dataDesligamento: "",
        motivo: "",
        generating: false,
        sendPhase: false,
      });
    }
    navigate(location.pathname, { replace: true, state: null }); // limpa, para não reabrir ao atualizar
  }, [loading, colaboradores, location, navigate]);

  const handleDocStatusUpdate = (docId: number, status: "Enviado" | "Erro Envio") => {
    setDocs((prev) => prev.map((d) => (d.id === docId ? { ...d, status } : d)));
  };

  /** Envia o PDF por e-mail pela API e já registra o resultado (Enviado / Erro Envio) na lista. */
  const handleEnviar = async (id: number, email: string) => {
    try {
      await enviarRescisao(id, email);
      handleDocStatusUpdate(id, "Enviado");
    } catch (e) {
      handleDocStatusUpdate(id, "Erro Envio");
      throw e;
    }
  };

  /** Reabre uma rescisão já gerada na conferência, com os valores salvos, para corrigir à mão. */
  const handleCorrigir = async (doc: RescisaoDoc) => {
    try {
      const r = await obterRescisao(doc.id);
      setSelectedId(null);
      setDetailSend(false);
      setWizard({
        step: 3,
        colaboradorId: doc.colaboradorId,
        dataDesligamento: doc.dataDesligamento,
        motivo: doc.motivoDesligamento,
        rescisaoId: doc.id,
        generating: false,
        sendPhase: false,
        itens: itensParaEdicao(r.itens),
        observacoes: r.observacoes ?? "",
      });
    } catch (e) {
      window.alert(e instanceof ApiError ? e.message : "Não foi possível abrir a rescisão para correção.");
    }
  };

  const handleNew = () => {
    setSelectedId(null);
    setDetailSend(false);
    setWizard({
      step: 1,
      colaboradorId: "",
      dataDesligamento: "",
      motivo: "",
      generating: false,
      sendPhase: false,
    });
  };

  const handleProcessar = (doc: RescisaoDoc) => {
    setSelectedId(null);
    setDetailSend(false);
    setWizard({
      step: 2,
      colaboradorId: doc.colaboradorId,
      dataDesligamento: doc.dataDesligamento,
      motivo: doc.motivoDesligamento,
      rescisaoId: doc.id,
      generating: false,
      sendPhase: false,
    });
  };

  const handleComplete = (doc: RescisaoDoc) => {
    setDocs((prev) => [doc, ...prev.filter((d) => d.id !== doc.id)]);
    setSelectedId(doc.id);
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
            <h1 className="text-lg font-semibold text-gray-900">Rescisões</h1>
            <Button size="sm" className="bg-red-700 hover:bg-red-800 gap-1.5" onClick={handleNew} disabled={loading || !!loadError}>
              <Plus className="w-3.5 h-3.5" />
              Nova
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-10 text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          )}
          {loadError && (
            <div className="m-4 bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-red-800">Falha ao carregar</p>
              <p className="text-xs text-red-600 mt-1">{loadError}</p>
              <Button size="sm" variant="outline" className="mt-3 gap-1.5" onClick={() => { setLoading(true); carregar(); }}>
                <RefreshCw className="w-3.5 h-3.5" /> Tentar de novo
              </Button>
            </div>
          )}
          {!loading && !loadError && docs.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-10">Nenhuma rescisão ainda.</p>
          )}
          {docs.map((doc) => (
            <button
              key={doc.id}
              onClick={() => { setSelectedId(doc.id); setWizard(null); setDetailSend(false); }}
              className={`w-full text-left px-5 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                selectedId === doc.id && !wizard ? "bg-red-50 border-l-2 border-l-red-600" : ""
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
              {doc.motivoDesligamento && (
                <p className="text-xs text-gray-500 mt-1">{doc.motivoDesligamento}</p>
              )}
              {doc.dataDesligamento && (
                <p className="text-xs text-gray-400">
                  {new Date(doc.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}
                </p>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {showWizard && (
          <WizardPanel
            wizard={wizard!}
            setWizard={setWizard}
            colaboradores={colaboradores}
            motivos={motivos}
            onComplete={handleComplete}
            onRefresh={carregar}
            onEnviar={handleEnviar}
          />
        )}

        {showDetailSend && selectedDoc && selectedCol && (
          <div className="p-8">
            <SendEmailFlow
              email={selectedCol.email}
              docLabel={`Rescisão — ${selectedDoc.dataDesligamento
                ? new Date(selectedDoc.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")
                : ""}`}
              collaboratorName={selectedDoc.colaboradorNome}
              pdfHref={pdfUrl(selectedDoc.id)}
              onSend={(email) => handleEnviar(selectedDoc.id, email)}
              onBack={() => setDetailSend(false)}
              onDone={() => setDetailSend(false)}
            />
          </div>
        )}

        {showDetail && selectedDoc && (
          <div className="p-8 max-w-lg">
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden mb-5">
              <div className="bg-red-700 px-6 py-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-white font-semibold text-lg">{selectedDoc.colaboradorNome}</p>
                    <p className="text-red-200 text-sm mt-0.5">{selectedDoc.empresa}</p>
                  </div>
                  <Badge className="bg-white/20 text-white hover:bg-white/20 border-0">
                    Rescisão
                  </Badge>
                </div>
              </div>
              <div className="p-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">CPF</span>
                  <span className="font-medium text-gray-800">{selectedDoc.colaboradorCpf}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Motivo</span>
                  <span className="font-medium text-gray-800">{selectedDoc.motivoDesligamento || "—"}</span>
                </div>
                {selectedDoc.dataDesligamento && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Data de desligamento</span>
                    <span className="font-medium text-gray-800">
                      {new Date(selectedDoc.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                )}
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
              </div>
            </div>
            {(() => {
              const temPdf = ["Gerado", "Enviado", "Erro Envio"].includes(selectedDoc.status);
              return (
                <div className="flex flex-wrap gap-3">
                  {temPdf ? (
                    <Button asChild className="flex-1 gap-2 bg-red-700 hover:bg-red-800">
                      <a href={pdfUrl(selectedDoc.id)} target="_blank" rel="noreferrer">
                        <Download className="w-4 h-4" />
                        Baixar PDF
                      </a>
                    </Button>
                  ) : (
                    <Button className="flex-1 bg-red-700 hover:bg-red-800" onClick={() => handleProcessar(selectedDoc)}>
                      Processar Rescisão
                    </Button>
                  )}
                  {temPdf && (
                    <Button variant="outline" className="flex-1 gap-2" onClick={() => setDetailSend(true)}>
                      <Send className="w-4 h-4" />
                      {selectedDoc.status === "Gerado" ? "Enviar" : "Reenviar"}
                    </Button>
                  )}
                  {temPdf && (
                    <Button variant="outline" className="w-full" onClick={() => handleCorrigir(selectedDoc)}>
                      Corrigir dados
                    </Button>
                  )}
                </div>
              );
            })()}
          </div>
        )}
        {showEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <FileX2 className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm mb-4">Selecione uma rescisão ou inicie uma nova</p>
            <Button onClick={handleNew} className="gap-2 bg-red-700 hover:bg-red-800">
              <Plus className="w-4 h-4" />
              Nova Rescisão
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
