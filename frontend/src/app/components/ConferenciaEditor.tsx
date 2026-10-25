import { Plus, RotateCcw } from "lucide-react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import {
  CODIGOS_EDITAVEIS,
  aplicarReferencia,
  ROTULOS,
  parseValor,
  tipoRubrica,
  totaisEdicao,
  type ItemEdicao,
  type TipoRubrica,
} from "../lib/rescisaoItens";

const brl = (v: number) => v.toLocaleString("pt-BR", { minimumFractionDigits: 2 });

const GRUPOS: { tipo: TipoRubrica; titulo: string; dica?: string }[] = [
  { tipo: "PROVENTO", titulo: "Proventos" },
  { tipo: "INFORMATIVO", titulo: "Informativos (FGTS)", dica: "Não entram no líquido a receber." },
  { tipo: "DESCONTO", titulo: "Deduções" },
];

interface Props {
  itens: ItemEdicao[];
  onChange: (itens: ItemEdicao[]) => void;
  observacoes: string;
  onObservacoes: (texto: string) => void;
  /** Volta aos valores calculados automaticamente (descarta as edições). */
  onRestaurar?: () => void;
  /** Salário do colaborador: usado para recalcular o valor quando a referência (dias/avos) muda. */
  salario?: number;
}

/** Tabela de conferência: todos os valores podem ser corrigidos à mão antes de gerar o PDF. */
export function ConferenciaEditor({ itens, onChange, observacoes, onObservacoes, onRestaurar, salario = 0 }: Props) {
  const totais = totaisEdicao(itens);
  const disponiveis = CODIGOS_EDITAVEIS.filter((c) => !itens.some((i) => i.codigo === c));

  const alterar = (codigo: number, campo: "valor" | "referencia", texto: string) =>
    onChange(itens.map((i) => (i.codigo === codigo ? { ...i, [campo]: texto } : i)));

  const adicionar = (codigo: number) =>
    onChange([...itens, { codigo, valor: "0,00", referencia: "" }].sort((a, b) => a.codigo - b.codigo));

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
        Digite o valor no campo <strong>R$</strong> e os totais se atualizam na hora. Em saldo de salário, aviso
        prévio, faltas, 13º e férias, o campo menor (referência) também recalcula o valor: escreva
        <strong> 5 dias</strong> ou <strong>10/12 avos</strong>.
      </p>
      {GRUPOS.map(({ tipo, titulo, dica }) => {
        const linhas = itens.filter((i) => tipoRubrica(i.codigo) === tipo);
        if (linhas.length === 0) return null;
        return (
          <div key={tipo}>
            <div className="flex items-baseline justify-between mb-1.5">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{titulo}</p>
              {dica && <p className="text-[11px] text-gray-400">{dica}</p>}
            </div>
            <div className="space-y-1.5">
              {linhas.map((i) => {
                const invalido = Number.isNaN(parseValor(i.valor));
                return (
                  <div key={i.codigo} className="flex items-center gap-2">
                    <label className="flex-1 min-w-0 text-sm text-gray-700 truncate">
                      <span className="text-gray-400">{i.codigo}- </span>
                      {ROTULOS[i.codigo]}
                    </label>
                    <Input
                      value={i.referencia}
                      onChange={(e) =>
                        onChange(aplicarReferencia(itens, i.codigo, e.target.value, salario))
                      }
                      placeholder="ref."
                      aria-label={`Referência de ${ROTULOS[i.codigo]}`}
                      className="h-8 w-24 text-xs"
                    />
                    <div className="relative">
                      <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
                      <Input
                        value={i.valor}
                        inputMode="decimal"
                        onChange={(e) => alterar(i.codigo, "valor", e.target.value)}
                        aria-label={`Valor de ${ROTULOS[i.codigo]}`}
                        aria-invalid={invalido}
                        className={`h-8 w-32 pl-7 text-right text-sm ${
                          invalido ? "border-red-400 focus-visible:ring-red-300" : ""
                        }`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="flex items-center gap-2 pt-1">
        {disponiveis.length > 0 && (
          <div className="relative flex-1">
            <Plus className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
            <select
              value=""
              onChange={(e) => e.target.value && adicionar(Number(e.target.value))}
              className="w-full h-8 pl-8 pr-2 text-xs rounded-md border border-gray-200 bg-white text-gray-600"
              aria-label="Adicionar verba"
            >
              <option value="">Adicionar outra verba…</option>
              {disponiveis.map((c) => (
                <option key={c} value={c}>
                  {c}- {ROTULOS[c]}
                </option>
              ))}
            </select>
          </div>
        )}
        {onRestaurar && (
          <Button type="button" variant="outline" size="sm" className="gap-1.5 h-8 text-xs" onClick={onRestaurar}>
            <RotateCcw className="w-3.5 h-3.5" />
            Restaurar cálculo
          </Button>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 overflow-hidden text-sm">
        <div className="flex justify-between px-4 py-2 bg-gray-50">
          <span className="text-gray-600">46- Total bruto</span>
          <span className="font-semibold text-gray-900">R$ {brl(totais.proventos)}</span>
        </div>
        <div className="flex justify-between px-4 py-2 border-t border-gray-100">
          <span className="text-gray-600">54- Total das deduções</span>
          <span className="font-semibold text-red-600">R$ {brl(totais.descontos)}</span>
        </div>
        <div className="flex justify-between px-4 py-2.5 bg-green-700">
          <span className="font-semibold text-white">55- Líquido a receber</span>
          <span className="font-bold text-white">R$ {brl(totais.liquido)}</span>
        </div>
      </div>

      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">
          Observações
        </label>
        <textarea
          value={observacoes}
          onChange={(e) => onObservacoes(e.target.value)}
          rows={3}
          maxLength={500}
          placeholder="Opcional — aparece no documento."
          className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-200"
        />
      </div>
    </div>
  );
}
