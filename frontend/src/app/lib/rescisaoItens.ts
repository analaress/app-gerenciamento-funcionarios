import {
  calcularINSS,
  calcularIRRF,
  type Colaborador,
  type MotivoDesligamento,
  type ValoresRescisao,
} from "../data/mockData";
import type { ItemPayload } from "./api";

/**
 * A API recebe os itens já calculados (ela só soma). O cálculo das verbas
 * continua em calcularRescisao (mockData.ts); aqui só convertemos para itens.
 */

/** Motivos da API → motivos que o cálculo local entende. */
export function motivoParaCalculo(motivoApi: string): MotivoDesligamento {
  switch (motivoApi) {
    case "Demissão sem justa causa":
      return "Sem justa causa";
    case "Demissão por justa causa":
      return "Com justa causa";
    case "Acordo entre as partes":
      return "Acordo";
    // Pedido de demissão e término de contrato: sem aviso indenizado e sem multa de 40%
    default:
      return "Pedido de demissão";
  }
}

export function calcularDeducoes(col: Colaborador) {
  const inss = Math.round(calcularINSS(col.salario));
  const irrf = Math.max(0, Math.round(calcularIRRF(col.salario - inss)));
  return { inss, irrf, total: inss + irrf };
}

/**
 * O TRCT paga só os proventos (campo 46). A multa de 40% e o FGTS 8% são
 * informativos no documento e NÃO entram no líquido (o backend trata como INFORMATIVO).
 */
export function totalBruto(v: ValoresRescisao): number {
  return v.total - v.multaFgts;
}

/** Monta os itens pelo código da rubrica do TRCT (ver RUBRICAS no backend). */
export function montarItens(
  col: Colaborador,
  v: ValoresRescisao,
  dataDesligamento: string
): ItemPayload[] {
  const d = new Date(dataDesligamento + "T12:00:00");
  const avos = `${d.getMonth() + 1}/12 avos`;
  const { inss, irrf } = calcularDeducoes(col);

  const itens: ItemPayload[] = [
    { codigo: 29, valor: v.avisoPrevioIndenizado, referencia: "30 dias" },
    { codigo: 30, valor: v.saldoSalario, referencia: `${d.getDate()} dias` },
    { codigo: 31, valor: v.decimoTerceiroProporcional, referencia: avos },
    { codigo: 35, valor: v.feriasProporcionais, referencia: avos },
    { codigo: 36, valor: v.tercoFerias },
    { codigo: 42, valor: v.fgtsDepositado }, // informativo
    { codigo: 43, valor: v.multaFgts }, // informativo
    { codigo: 47, valor: inss },
    { codigo: 50, valor: irrf },
  ];
  return itens.filter((i) => i.valor > 0);
}

// ─── Conferência / edição manual ────────────────────────────────────────────

export type TipoRubrica = "PROVENTO" | "DESCONTO" | "INFORMATIVO";

/** Tipo de cada rubrica do TRCT (igual à tabela RUBRICAS do backend). */
export function tipoRubrica(codigo: number): TipoRubrica {
  if (codigo >= 47 && codigo <= 53) return "DESCONTO";
  if (codigo >= 41 && codigo <= 45) return "INFORMATIVO";
  return "PROVENTO";
}

export const ROTULOS: Record<number, string> = {
  29: "Aviso prévio indenizado",
  30: "Saldo de salário",
  31: "13º salário proporcional",
  32: "13º salário indenizado",
  33: "Férias vencidas",
  34: "1/3 sobre férias vencidas",
  35: "Férias proporcionais",
  36: "1/3 sobre férias proporcionais",
  37: "Outras verbas rescisórias",
  38: "1/3 sobre férias indenizadas",
  39: "Reflexo de extras / DSR",
  40: "Horas extras",
  41: "Horas faltas parcial",
  42: "FGTS 8%",
  43: "FGTS multa rescisória",
  44: "FGTS mês da rescisão / anterior",
  45: "Faltas",
  47: "Previdência (INSS)",
  48: "Previdência 13º salário",
  49: "Adiantamentos",
  50: "IRRF",
  51: "Aviso prévio (desconto)",
  52: "Faltas (desconto)",
  53: "Outros descontos",
};

/** Códigos que podem ser digitados à mão (46, 54 e 55 são totais calculados pelo backend). */
export const CODIGOS_EDITAVEIS = Object.keys(ROTULOS).map(Number);

/** Item como aparece nos campos da tela (valor em texto, para poder digitar livremente). */
export interface ItemEdicao {
  codigo: number;
  valor: string;
  referencia: string;
}

const EXTRAS_SEMPRE_VISIVEIS = [37, 53]; // "Outras verbas" e "Outros descontos"

const fmtValor = (n: number) => (Number.isFinite(n) ? n.toFixed(2).replace(".", ",") : "0,00");

/** Aceita "1234.56", "1234,56" e "1.234,56". Retorna NaN se não for número. */
export function parseValor(texto: string): number {
  const t = texto.trim();
  if (t === "") return 0;
  const normal = t.includes(",") ? t.replace(/\./g, "").replace(",", ".") : t;
  return /^\d+(\.\d+)?$/.test(normal) ? Number(normal) : NaN;
}

export function itensParaEdicao(
  itens: { codigo: number; valor: number | string; referencia?: string | null }[]
): ItemEdicao[] {
  const lista: ItemEdicao[] = itens
    .filter((i) => ROTULOS[i.codigo] !== undefined)
    .map((i) => ({
      codigo: i.codigo,
      valor: fmtValor(Number(i.valor)),
      referencia: i.referencia ?? "",
    }));
  for (const codigo of EXTRAS_SEMPRE_VISIVEIS) {
    if (!lista.some((i) => i.codigo === codigo)) lista.push({ codigo, valor: "0,00", referencia: "" });
  }
  return lista.sort((a, b) => a.codigo - b.codigo);
}

export function temValorInvalido(itens: ItemEdicao[]): boolean {
  return itens.some((i) => Number.isNaN(parseValor(i.valor)));
}

/** Converte o que está na tela para o que a API espera (ignora linhas zeradas). */
export function edicaoParaPayload(itens: ItemEdicao[]): ItemPayload[] {
  return itens
    .map((i) => ({
      codigo: i.codigo,
      valor: parseValor(i.valor),
      referencia: i.referencia.trim() || undefined,
    }))
    .filter((i) => i.valor > 0);
}

/** Mesma conta do backend: informativos (41–45) não entram no líquido. */
export function totaisEdicao(itens: ItemEdicao[]) {
  let proventos = 0;
  let descontos = 0;
  for (const i of itens) {
    const v = parseValor(i.valor);
    if (!(v > 0)) continue;
    const tipo = tipoRubrica(i.codigo);
    if (tipo === "PROVENTO") proventos += v;
    else if (tipo === "DESCONTO") descontos += v;
  }
  return { proventos, descontos, liquido: proventos - descontos };
}

// ─── Recálculo a partir da "referência" (dias / avos) ───────────────────────

const RUBRICAS_POR_DIAS = new Set([29, 30, 52]); // aviso prévio, saldo de salário, faltas
const RUBRICAS_POR_AVOS = new Set([31, 32, 33, 35]); // 13º, férias
const TERCO_DE: Record<number, number> = { 35: 36, 33: 34 }; // férias -> 1/3 de férias

function lerReferencia(codigo: number, texto: string): number | null {
  const t = texto.trim().toLowerCase();
  if (RUBRICAS_POR_DIAS.has(codigo)) {
    const m = t.match(/^(\d+(?:[.,]\d+)?)\s*(?:dias?)?$/);
    return m ? Number(m[1].replace(",", ".")) : null;
  }
  if (RUBRICAS_POR_AVOS.has(codigo)) {
    const m = t.match(/^(\d+)\s*(?:\/\s*12)?\s*(?:avos?)?$/);
    return m ? Number(m[1]) : null;
  }
  return null;
}

/**
 * Atualiza a referência de uma linha e, quando ela é "N dias" ou "N/12 avos",
 * recalcula o valor: dias = salário ÷ 30 × N; avos = salário ÷ 12 × N.
 * Férias (33/35) também atualizam o 1/3 (34/36).
 */
export function aplicarReferencia(
  itens: ItemEdicao[],
  codigo: number,
  texto: string,
  salario: number
): ItemEdicao[] {
  let lista = itens.map((i) => (i.codigo === codigo ? { ...i, referencia: texto } : i));
  const n = lerReferencia(codigo, texto);
  if (n === null || !(salario > 0)) return lista;

  const base = RUBRICAS_POR_DIAS.has(codigo) ? (salario / 30) * n : (salario / 12) * n;
  const valor = Math.round(base * 100) / 100;
  lista = lista.map((i) => (i.codigo === codigo ? { ...i, valor: fmtValor(valor) } : i));

  const terco = TERCO_DE[codigo];
  if (terco !== undefined) {
    const valorTerco = fmtValor(Math.round((valor / 3) * 100) / 100);
    lista = lista.some((i) => i.codigo === terco)
      ? lista.map((i) => (i.codigo === terco ? { ...i, valor: valorTerco } : i))
      : [...lista, { codigo: terco, valor: valorTerco, referencia: "" }].sort((a, b) => a.codigo - b.codigo);
  }
  return lista;
}
