import { useCallback, useEffect, useState } from "react";
import { Search, Download, FileX2, Loader2, RefreshCw, Send } from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { RescisaoPreview } from "./RescisaoPreview";
import { SendEmailFlow } from "./SendEmailFlow";
import type { Colaborador } from "../data/mockData";
import {
  ApiError,
  ApiRescisao,
  enviarRescisao,
  getColaboradores,
  listarRescisoes,
  pdfUrl,
  toRescisaoDoc,
} from "../lib/api";

const statusColors: Record<string, string> = {
  Gerado: "bg-purple-100 text-purple-700 hover:bg-purple-100",
  Enviado: "bg-green-100 text-green-700 hover:bg-green-100",
  "Erro Envio": "bg-red-100 text-red-700 hover:bg-red-100",
};

const dataBr = (d: string) => new Date(d + "T12:00:00").toLocaleDateString("pt-BR");

/** Histórico: apenas as rescisões já geradas, para consultar o documento e baixar o PDF. */
export function Historico() {
  const [rescisoes, setRescisoes] = useState<ApiRescisao[]>([]);
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [busca, setBusca] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [enviando, setEnviando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setErro(null);
      const [cols, lista] = await Promise.all([getColaboradores(), listarRescisoes()]);
      setColaboradores(cols);
      // só as já geradas (PDF disponível), incluindo as que tiveram falha no envio
      setRescisoes(
        lista.filter((r) => ["GERADO", "ENVIADO", "ERRO_ENVIO"].includes(r.status))
      );
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Erro ao carregar o histórico.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const docs = rescisoes.map((r) => toRescisaoDoc(r, colaboradores));
  const filtrados = docs.filter((d) => {
    const q = busca.toLowerCase();
    return (
      d.colaboradorNome.toLowerCase().includes(q) ||
      d.colaboradorCpf.includes(busca) ||
      d.empresa.toLowerCase().includes(q)
    );
  });

  const selecionada = rescisoes.find((r) => r.id === selectedId);
  const selecionadaDoc = docs.find((d) => d.id === selectedId);
  const selecionadaCol = selecionada
    ? colaboradores.find((c) => c.id === String(selecionada.colaborador_id))
    : undefined;

  return (
    <div className="flex h-full">
      {/* Lista */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900">Histórico</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            {rescisoes.length} {rescisoes.length === 1 ? "rescisão gerada" : "rescisões geradas"}
          </p>
          <div className="relative mt-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nome, CPF ou empresa…"
              className="pl-9 h-9 text-sm"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-10 text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          )}
          {erro && (
            <div className="m-4 bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-red-800">Falha ao carregar</p>
              <p className="text-xs text-red-600 mt-1">{erro}</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 gap-1.5"
                onClick={() => {
                  setLoading(true);
                  carregar();
                }}
              >
                <RefreshCw className="w-3.5 h-3.5" /> Tentar de novo
              </Button>
            </div>
          )}
          {!loading && !erro && filtrados.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-10 px-5">
              {rescisoes.length === 0
                ? "Nenhuma rescisão gerada ainda."
                : "Nenhuma rescisão encontrada para essa busca."}
            </p>
          )}
          {filtrados.map((doc) => (
            <button
              key={doc.id}
              onClick={() => {
                setSelectedId(doc.id);
                setEnviando(false);
              }}
              className={`w-full text-left px-5 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                selectedId === doc.id ? "bg-red-50 border-l-2 border-l-red-600" : ""
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <p className="text-sm font-semibold text-gray-900 truncate flex-1">
                  {doc.colaboradorNome}
                </p>
                <Badge className={`text-xs ml-2 flex-shrink-0 ${statusColors[doc.status] ?? ""}`}>
                  {doc.status}
                </Badge>
              </div>
              <p className="text-xs text-gray-400">{doc.empresa}</p>
              <p className="text-xs text-gray-500 mt-1">{doc.motivoDesligamento}</p>
              <p className="text-xs text-gray-400">{dataBr(doc.dataDesligamento)}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Documento */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {selecionada && selecionadaDoc ? (
          enviando ? (
            <div className="p-8">
              <SendEmailFlow
                email={selecionadaCol?.email ?? ""}
                docLabel={`Rescisão — ${dataBr(selecionada.data_desligamento)}`}
                collaboratorName={selecionadaDoc.colaboradorNome}
                pdfHref={pdfUrl(selecionada.id)}
                onSend={async (email) => {
                  try {
                    await enviarRescisao(selecionada.id, email);
                  } finally {
                    carregar(); // atualiza o status (Enviado / Erro Envio) na lista
                  }
                }}
                onBack={() => setEnviando(false)}
                onDone={() => setEnviando(false)}
              />
            </div>
          ) : (
            <div className="p-8 max-w-3xl">
              <RescisaoPreview rescisao={selecionada} col={selecionadaCol} />
              <div className="flex gap-3 mt-5">
                <Button asChild className="flex-1 gap-2 bg-red-700 hover:bg-red-800">
                  <a href={pdfUrl(selecionada.id)} target="_blank" rel="noreferrer">
                    <Download className="w-4 h-4" />
                    Baixar PDF
                  </a>
                </Button>
                <Button variant="outline" className="flex-1 gap-2" onClick={() => setEnviando(true)}>
                  <Send className="w-4 h-4" />
                  {selecionada.status === "GERADO" ? "Enviar por E-mail" : "Reenviar por E-mail"}
                </Button>
              </div>
            </div>
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <FileX2 className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm">Selecione uma rescisão para ver o documento</p>
          </div>
        )}
      </div>
    </div>
  );
}
