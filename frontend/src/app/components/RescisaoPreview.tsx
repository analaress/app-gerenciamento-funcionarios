import type { ReactNode } from "react";
import type { Colaborador } from "../data/mockData";
import type { ApiRescisao } from "../lib/api";

interface Linha {
  num: number;
  label: string;
  sub?: string;
}

// Rubricas do TRCT (mesmos códigos do backend)
const PROVENTOS_A: Linha[] = [
  { num: 29, label: "Aviso Prévio Indenizado", sub: "dias" },
  { num: 30, label: "Saldo Salário", sub: "dias" },
  { num: 31, label: "13º Salário", sub: "/12 avos" },
  { num: 32, label: "13º Salário Inden.", sub: "/12 avos" },
  { num: 33, label: "Férias Vencidas", sub: "/12 avos" },
  { num: 34, label: "1/3 sobre férias vencidas" },
  { num: 35, label: "Férias proporc.", sub: "/12 avos" },
  { num: 36, label: "1/3 sob férias proporc." },
  { num: 37, label: "Outras verbas rescisórias" },
];

const PROVENTOS_B: Linha[] = [
  { num: 38, label: "1/3 sob férias indenizadas" },
  { num: 39, label: "Reflexo Extras DSR" },
  { num: 40, label: "Horas extras", sub: "/horas" },
  { num: 41, label: "Horas Faltas Parcial", sub: "/horas" },
  { num: 42, label: "FGTS 8%", sub: "meses" },
  { num: 43, label: "FGTS Multa Rescis." },
  { num: 44, label: "FGTS Mês rescisão/ant." },
  { num: 45, label: "Faltas" },
];

const DEDUCOES: Linha[] = [
  { num: 47, label: "Previdência" },
  { num: 48, label: "Previdência 13º Sal." },
  { num: 49, label: "Adiantamentos" },
  { num: 50, label: "IRRF" },
  { num: 51, label: "Aviso Prévio" },
  { num: 52, label: "Faltas" },
  { num: 53, label: "Outros descontos" },
];

const brl = (v: number) =>
  v > 0 ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2 }) : "-";

const dataBr = (d: string) => new Date(d + "T12:00:00").toLocaleDateString("pt-BR");

function Campo({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div className="px-3 py-2">
      <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">{rotulo}</p>
      <p className="font-semibold text-gray-800">{children}</p>
    </div>
  );
}

/** Documento da rescisão (layout do Figma) montado com os dados salvos na API. */
export function RescisaoPreview({
  rescisao,
  col,
}: {
  rescisao: ApiRescisao;
  col?: Colaborador;
}) {
  const itens = new Map(rescisao.itens.map((i) => [i.codigo, i]));
  const valor = (cod: number) => Number(itens.get(cod)?.valor ?? 0);
  const referencia = (l: Linha) => itens.get(l.num)?.referencia || l.sub;

  const totalBruto = Number(rescisao.total_proventos);
  const totalDeducoes = Number(rescisao.total_descontos);
  const liquido = Number(rescisao.total_liquido);

  const renderProventos = (linhas: Linha[]) =>
    linhas.map((l, i) => {
      const v = valor(l.num);
      const sub = referencia(l);
      return (
        <div
          key={l.num}
          className={`px-3 py-1.5 flex justify-between items-start gap-1 ${
            i < linhas.length - 1 ? "border-b border-gray-200" : ""
          }`}
        >
          <div className="flex-1 min-w-0">
            <span className="text-gray-400">{l.num}-</span>
            <span className="text-gray-700">{l.label}</span>
            {sub && <p className="text-gray-400 text-[9px] pl-3">{sub}</p>}
          </div>
          <span
            className={`flex-shrink-0 font-medium tabular-nums ${
              v > 0 ? "text-gray-900" : "text-gray-300"
            }`}
          >
            {brl(v)}
          </span>
        </div>
      );
    });

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden text-[11px] leading-tight shadow-sm">
      <div className="bg-gray-800 text-white px-5 py-3">
        <p className="text-center font-bold text-sm tracking-wide">
          RESCISÃO DE CONTRATO DE TRABALHO
        </p>
      </div>

      {/* Dados do trabalhador */}
      <div className="grid grid-cols-3 border-b border-gray-300 [&>div+div]:border-l [&>div+div]:border-gray-300">
        <Campo rotulo="Nome do Empregado">
          {col?.nome ?? `Colaborador #${rescisao.colaborador_id}`}
        </Campo>
        <Campo rotulo="CPF">{col?.cpf ?? "—"}</Campo>
        <Campo rotulo="Função / Cargo">{col?.cargo ?? "—"}</Campo>
      </div>
      <div className="grid grid-cols-3 border-b border-gray-300 [&>div+div]:border-l [&>div+div]:border-gray-300">
        <Campo rotulo="Empresa">{col?.empresa ?? "—"}</Campo>
        <Campo rotulo="Data Admissão">{col ? dataBr(col.dataAdmissao) : "—"}</Campo>
        <Campo rotulo="Data Desligamento">{dataBr(rescisao.data_desligamento)}</Campo>
      </div>

      {/* Afastamento */}
      <div className="grid grid-cols-4 border-b border-gray-300 bg-gray-50 [&>div+div]:border-l [&>div+div]:border-gray-300">
        <div className="px-3 py-2">
          <p className="text-gray-500 text-[9px]">25-Causa do Afastamento</p>
          <p className="text-gray-700 mt-0.5">{rescisao.causa_afastamento}</p>
        </div>
        <div className="px-3 py-2">
          <p className="text-gray-500 text-[9px]">26-Código de Afastam.</p>
          <p className="text-gray-700 mt-0.5">{rescisao.codigo_afastamento || "—"}</p>
        </div>
        <div className="px-3 py-2">
          <p className="text-gray-500 text-[9px]">27-Pensão Aliment. %</p>
          <p className="text-gray-700 mt-0.5">
            {rescisao.pensao_alimenticia != null ? `${rescisao.pensao_alimenticia}%` : "—"}
          </p>
        </div>
        <div className="px-3 py-2">
          <p className="text-gray-500 text-[9px]">28-Cat. Do Trabalhador</p>
          <p className="text-gray-700 mt-0.5">{rescisao.categoria_trabalhador || "—"}</p>
        </div>
      </div>

      {/* Tabela de rubricas */}
      <div className="grid grid-cols-3">
        <div className="border-r border-gray-300 flex flex-col">
          <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-300 text-center">
            <span className="text-gray-600 font-semibold text-[10px] uppercase tracking-wide">Valor</span>
          </div>
          {renderProventos(PROVENTOS_A)}
        </div>

        <div className="border-r border-gray-300 flex flex-col">
          <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-300 text-center">
            <span className="text-gray-600 font-semibold text-[10px] uppercase tracking-wide">Valor</span>
          </div>
          {renderProventos(PROVENTOS_B)}
          <div className="mt-auto px-3 py-2 bg-gray-100 border-t border-gray-300 flex justify-between items-center">
            <span className="font-bold text-gray-800">46-TOTAL BRUTO</span>
            <span className="font-bold text-gray-900 tabular-nums">{brl(totalBruto)}</span>
          </div>
        </div>

        <div className="flex flex-col">
          <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-300 text-center">
            <span className="text-gray-600 font-semibold text-[10px] uppercase tracking-wide">Deduções</span>
          </div>
          {DEDUCOES.map((d) => {
            const v = valor(d.num);
            return (
              <div
                key={d.num}
                className="px-3 py-1.5 flex justify-between items-start gap-1 border-b border-gray-200"
              >
                <div className="flex-1 min-w-0">
                  <span className="text-gray-400">{d.num}-</span>
                  <span className="text-gray-700">{d.label}</span>
                </div>
                <span
                  className={`flex-shrink-0 font-medium tabular-nums ${
                    v > 0 ? "text-red-600" : "text-gray-300"
                  }`}
                >
                  {brl(v)}
                </span>
              </div>
            );
          })}
          <div className="px-3 py-1.5 border-b border-gray-300 bg-red-50 flex justify-between items-center">
            <span className="font-bold text-gray-700 text-[10px]">54-TOTAL DAS DEDUÇÕES</span>
            <span className="font-bold text-red-700 tabular-nums">{brl(totalDeducoes)}</span>
          </div>
          <div className="mt-auto px-3 py-2 bg-green-700 flex justify-between items-center">
            <span className="font-bold text-white text-[10px] uppercase tracking-wide">
              55-Líquido a Receber
            </span>
            <span className="font-bold text-white text-sm tabular-nums">
              R$ {liquido.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      {rescisao.observacoes && (
        <div className="px-3 py-2 border-t border-gray-300">
          <p className="text-gray-400 text-[9px] uppercase tracking-wide mb-0.5">Observações</p>
          <p className="text-gray-700">{rescisao.observacoes}</p>
        </div>
      )}
    </div>
  );
}
