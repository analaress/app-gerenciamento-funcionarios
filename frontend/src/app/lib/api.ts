import type { Colaborador, DocumentoStatus } from "../data/mockData";

/**
 * Endereço da API FastAPI.
 * - Em desenvolvimento usa "/api", que o Vite redireciona para http://127.0.0.1:8000 (ver vite.config.ts).
 * - Em produção defina VITE_API_URL (ex.: https://minha-api.com) e libere o CORS no FastAPI.
 */
export const API_BASE: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      "Não foi possível conectar à API. Verifique se o servidor FastAPI está rodando.",
      0
    );
  }

  if (!res.ok) {
    let msg = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
      else if (Array.isArray(body.detail))
        msg = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      /* corpo sem JSON */
    }
    throw new ApiError(msg, res.status);
  }
  return res.json() as Promise<T>;
}

// ─── Tipos do contrato da API ───────────────────────────────────────────────

interface ApiColaborador {
  id: number;
  nome: string;
  cpf: string;
  email: string;
  empresa_id: number;
  cargo: string;
  salario: number | string;
  data_admissao: string;
  situacao: string; // "ATIVO" | "DESLIGADO"
  empresa: { id: number; razao_social: string; cnpj: string } | null;
}

export type TipoItem = "PROVENTO" | "DESCONTO" | "INFORMATIVO";

/** Item enviado à API: o código é a rubrica do TRCT (29–53). Descrição e tipo vêm do backend. */
export interface ItemPayload {
  codigo: number;
  valor: number;
  referencia?: string;
}

export interface RescisaoPayload {
  colaborador_id: number;
  data_desligamento: string;
  causa_afastamento: string;
  data_aviso_previo?: string | null;
  codigo_afastamento?: string | null;
  observacoes?: string | null;
  itens: ItemPayload[];
}

export interface ApiRescisao {
  id: number;
  colaborador_id: number;
  empresa_id: number;
  data_desligamento: string;
  causa_afastamento: string;
  codigo_afastamento?: string | null;
  pensao_alimenticia?: number | string | null;
  categoria_trabalhador?: string;
  observacoes: string | null;
  total_proventos: number | string;
  total_descontos: number | string;
  total_liquido: number | string;
  status: string;
  criado_em: string;
  itens: {
    id: number;
    codigo: number;
    descricao: string;
    tipo: TipoItem;
    valor: number | string;
    referencia: string | null;
  }[];
}

// ─── Colaboradores / motivos ────────────────────────────────────────────────

export async function getColaboradores(): Promise<Colaborador[]> {
  const lista = await request<ApiColaborador[]>("/colaboradores/");
  return lista.map((c) => ({
    id: String(c.id),
    nome: c.nome,
    cpf: c.cpf,
    email: c.email,
    telefone: "",
    empresa: c.empresa?.razao_social ?? `Empresa #${c.empresa_id}`,
    cargo: c.cargo,
    salario: Number(c.salario),
    dataAdmissao: c.data_admissao,
    situacao: c.situacao.toUpperCase() === "ATIVO" ? "Ativo" : "Desligado",
  }));
}

export const getMotivos = () => request<string[]>("/rescisoes/motivos");

// ─── Rescisões ──────────────────────────────────────────────────────────────

export const listarRescisoes = () => request<ApiRescisao[]>("/rescisoes/");

export const obterRescisao = (id: number) => request<ApiRescisao>(`/rescisoes/${id}`);

export const criarRescisao = (payload: RescisaoPayload) =>
  request<ApiRescisao>("/rescisoes/", { method: "POST", body: JSON.stringify(payload) });

export const corrigirRescisao = (id: number, payload: RescisaoPayload) =>
  request<ApiRescisao>(`/rescisoes/${id}`, { method: "PUT", body: JSON.stringify(payload) });

/** Dispara a geração do PDF no backend. */
export const gerarRescisao = (id: number) =>
  request<ApiRescisao>(`/rescisoes/${id}/gerar`, { method: "POST" });

/** URL do PDF gerado (abre/baixa direto no navegador). */
export const pdfUrl = (id: number) => `${API_BASE}/rescisoes/${id}/pdf`;

// ─── Conversão API → modelo da tela ─────────────────────────────────────────

const STATUS_LABEL: Record<string, DocumentoStatus> = {
  PENDENTE: "Pendente",
  EM_CONFERENCIA: "Em Conferência",
  GERADO: "Gerado",
  ENVIADO: "Enviado",
  ERRO_GERACAO: "Erro Geração",
  ERRO_ENVIO: "Erro Envio",
};

export interface RescisaoDoc {
  id: number;
  colaboradorId: string;
  colaboradorNome: string;
  colaboradorCpf: string;
  empresa: string;
  status: DocumentoStatus;
  motivoDesligamento: string;
  dataDesligamento: string;
  dataGeracao: string;
  totalLiquido: number;
}

export function toRescisaoDoc(r: ApiRescisao, colaboradores: Colaborador[]): RescisaoDoc {
  const col = colaboradores.find((c) => c.id === String(r.colaborador_id));
  return {
    id: r.id,
    colaboradorId: String(r.colaborador_id),
    colaboradorNome: col?.nome ?? `Colaborador #${r.colaborador_id}`,
    colaboradorCpf: col?.cpf ?? "",
    empresa: col?.empresa ?? "",
    status: STATUS_LABEL[r.status] ?? "Pendente",
    motivoDesligamento: r.causa_afastamento,
    dataDesligamento: r.data_desligamento,
    dataGeracao: r.criado_em.slice(0, 10),
    totalLiquido: Number(r.total_liquido),
  };
}

// ─── Envio por e-mail ───────────────────────────────────────────────────────

/** Pede ao backend para enviar o PDF por e-mail. Se falhar, lança ApiError com o motivo. */
export const enviarRescisao = (id: number, destinatario: string) =>
  request<ApiRescisao>(`/rescisoes/${id}/enviar`, {
    method: "POST",
    body: JSON.stringify({ destinatario }),
  });
