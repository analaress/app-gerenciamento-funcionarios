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
