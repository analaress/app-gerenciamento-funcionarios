import { useEffect, useState } from "react";
import {
  Search, Plus, Mail, Phone, Building2, UserCheck,
  FileText, FileX2, Edit2, X, Check, AlertCircle,
} from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Colaborador } from "../data/mockData";
import { ApiError, getColaboradores } from "../lib/api";
import { Link } from "react-router";

const situacaoStyle: Record<string, string> = {
  Ativo: "bg-green-100 text-green-700 hover:bg-green-100",
  Desligado: "bg-gray-100 text-gray-600 hover:bg-gray-100",
};

function initials(nome: string) {
  return nome
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

function avatarColor(id: string) {
  const colors = [
    "from-blue-500 to-blue-700",
    "from-purple-500 to-purple-700",
    "from-green-500 to-green-700",
    "from-amber-500 to-amber-700",
    "from-rose-500 to-rose-700",
    "from-teal-500 to-teal-700",
    "from-indigo-500 to-indigo-700",
    "from-cyan-500 to-cyan-700",
  ];
  return colors[parseInt(id) % colors.length];
}

// ─── Form ─────────────────────────────────────────────────────────────────────

interface ColFormData {
  nome: string;
  cpf: string;
  cargo: string;
  empresa: string;
  email: string;
  telefone: string;
  dataAdmissao: string;
  salario: string;
  situacao: "Ativo" | "Desligado";
}

const emptyForm: ColFormData = {
  nome: "", cpf: "", cargo: "", empresa: "",
  email: "", telefone: "", dataAdmissao: "", salario: "", situacao: "Ativo",
};

const required: (keyof ColFormData)[] = ["nome", "cpf", "cargo", "empresa", "email", "dataAdmissao", "salario"];

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return (
    <p className="flex items-center gap-1 text-xs text-red-600 mt-1">
      <AlertCircle className="w-3 h-3" />
      {msg}
    </p>
  );
}

function ColaboradorForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: Colaborador;
  onSave: (d: ColFormData) => void;
  onCancel: () => void;
}) {
  const [fd, setFd] = useState<ColFormData>(
    initial
      ? {
          nome: initial.nome,
          cpf: initial.cpf,
          cargo: initial.cargo,
          empresa: initial.empresa,
          email: initial.email,
          telefone: initial.telefone,
          dataAdmissao: initial.dataAdmissao,
          salario: initial.salario.toString(),
          situacao: initial.situacao,
        }
      : { ...emptyForm }
  );
  const [errors, setErrors] = useState<Partial<Record<keyof ColFormData, string>>>({});
  const [tried, setTried] = useState(false);

  const set = (k: keyof ColFormData) => (v: string) => {
    setFd((p) => ({ ...p, [k]: v }));
    if (tried) setErrors((e) => ({ ...e, [k]: validate({ ...fd, [k]: v })[k] }));
  };

  const validate = (d: ColFormData) => {
    const errs: Partial<Record<keyof ColFormData, string>> = {};
    required.forEach((k) => {
      if (!d[k]?.toString().trim()) errs[k] = "Campo obrigatório";
    });
    if (d.salario && isNaN(parseFloat(d.salario.replace(",", "."))))
      errs.salario = "Valor inválido";
    return errs;
  };

  const handleSave = () => {
    setTried(true);
    const errs = validate(fd);
    setErrors(errs);
    if (Object.keys(errs).length === 0) onSave(fd);
  };

  const field = (
    label: string,
    key: keyof ColFormData,
    extra?: { type?: string; placeholder?: string }
  ) => (
    <div>
      <label className="text-sm font-medium text-gray-700 mb-1.5 block">
        {label}
        {required.includes(key) && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <Input
        type={extra?.type ?? "text"}
        placeholder={extra?.placeholder}
        value={fd[key] as string}
        onChange={(e) => set(key)(e.target.value)}
        className={`h-10 ${errors[key] ? "border-red-400 focus-visible:ring-red-400" : ""}`}
      />
      <FieldError msg={errors[key]} />
    </div>
  );

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {initial ? "Editar Colaborador" : "Novo Colaborador"}
        </h2>
        <p className="text-sm text-gray-400 mt-0.5">
          {initial ? "Atualize os dados do cadastro." : "Preencha os dados para cadastrar um novo colaborador."}
        </p>
      </div>

      <div className="space-y-4">
        {/* Nome — full width */}
        {field("Nome completo", "nome", { placeholder: "Ex: Maria da Silva Santos" })}

        {/* CPF + Cargo */}
        <div className="grid grid-cols-2 gap-4">
          {field("CPF", "cpf", { placeholder: "000.000.000-00" })}
          {field("Cargo", "cargo", { placeholder: "Ex: Analista de Sistemas" })}
        </div>

        {/* Empresa — full width */}
        {field("Empresa", "empresa", { placeholder: "Ex: Tech Solutions Ltda" })}

        {/* E-mail + Telefone */}
        <div className="grid grid-cols-2 gap-4">
          {field("E-mail", "email", { type: "email", placeholder: "nome@empresa.com.br" })}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">Telefone</label>
            <Input
              type="tel"
              placeholder="(11) 99999-9999"
              value={fd.telefone}
              onChange={(e) => set("telefone")(e.target.value)}
              className="h-10"
            />
          </div>
        </div>

        {/* Admissão + Salário */}
        <div className="grid grid-cols-2 gap-4">
          {field("Data de admissão", "dataAdmissao", { type: "date" })}
          {field("Salário (R$)", "salario", { type: "number", placeholder: "0,00" })}
        </div>

        {/* Status */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-2 block">Status</label>
          <div className="flex gap-2">
            {(["Ativo", "Desligado"] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setFd((p) => ({ ...p, situacao: s }))}
                className={`flex-1 py-2.5 text-sm font-medium rounded-lg border transition-colors flex items-center justify-center gap-2 ${
                  fd.situacao === s
                    ? s === "Ativo"
                      ? "bg-green-600 border-green-600 text-white"
                      : "bg-gray-600 border-gray-600 text-white"
                    : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
                }`}
              >
                {fd.situacao === s && <Check className="w-3.5 h-3.5" />}
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {tried && Object.keys(errors).length > 0 && (
        <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">
            Preencha os campos obrigatórios antes de salvar.
          </p>
        </div>
      )}

      <div className="flex gap-3 mt-6">
        <Button variant="outline" onClick={onCancel} className="flex-1">
          Cancelar
        </Button>
        <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleSave}>
          Salvar colaborador
        </Button>
      </div>
    </div>
  );
}

// ─── Reuse info section ───────────────────────────────────────────────────────

function ReuseInfo({ col }: { col: Colaborador }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Dados reaproveitados nos processos
      </p>
      <div className="space-y-2.5">
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-1.5 w-20 flex-shrink-0 pt-0.5">
            <FileText className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs font-semibold text-blue-700">Recibo</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {["Nome", "CPF", "Cargo", "Empresa", "Salário"].map((f) => (
              <span
                key={f}
                className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-100"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
        {col.situacao === "Ativo" && (
          <div className="flex items-start gap-3">
            <div className="flex items-center gap-1.5 w-20 flex-shrink-0 pt-0.5">
              <FileX2 className="w-3.5 h-3.5 text-red-500" />
              <span className="text-xs font-semibold text-red-700">Rescisão</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {["Nome", "CPF", "Cargo", "Empresa", "Admissão", "Salário"].map((f) => (
                <span
                  key={f}
                  className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full border border red-100 border-red-100"
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Detail panel ─────────────────────────────────────────────────────────────

function DetailPanel({ col, onEdit }: { col: Colaborador; onEdit: () => void }) {
  const meses = Math.floor(
    (new Date().getTime() - new Date(col.dataAdmissao).getTime()) /
      (1000 * 60 * 60 * 24 * 30.44)
  );
  const anos = Math.floor(meses / 12);
  const mesesRestantes = meses % 12;

  return (
    <div className="p-8 max-w-2xl space-y-5">
      {/* Header card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-start gap-5">
          <div
            className={`w-16 h-16 bg-gradient-to-br ${avatarColor(col.id)} rounded-2xl flex items-center justify-center text-white text-xl font-bold flex-shrink-0`}
          >
            {initials(col.nome)}
          </div>
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{col.nome}</h2>
                <p className="text-gray-500 mt-0.5">{col.cargo}</p>
              </div>
              <div className="flex items-center gap-2 ml-3">
                <Badge className={situacaoStyle[col.situacao]}>{col.situacao}</Badge>
                <button
                  onClick={onEdit}
                  className="p-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-400 hover:text-gray-700 transition-colors"
                  title="Editar colaborador"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Building2 className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-sm text-gray-600">{col.empresa}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-5 space-y-3">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Dados Pessoais
            </p>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-400">CPF</p>
                <p className="text-sm font-medium text-gray-800">{col.cpf}</p>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <Mail className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <p className="text-sm text-gray-700 truncate">{col.email}</p>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <p className="text-sm text-gray-700">{col.telefone}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 space-y-3">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Vínculo
            </p>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-400">Admissão</p>
                <p className="text-sm font-medium text-gray-800">
                  {new Date(col.dataAdmissao + "T12:00:00").toLocaleDateString("pt-BR")}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Tempo de empresa</p>
                <p className="text-sm font-medium text-gray-800">
                  {anos > 0 ? `${anos} ano${anos !== 1 ? "s" : ""}` : ""}{" "}
                  {mesesRestantes > 0
                    ? `${mesesRestantes} mês${mesesRestantes !== 1 ? "es" : ""}`
                    : ""}
                  {anos === 0 && mesesRestantes === 0 ? "Menos de 1 mês" : ""}
                </p>
              </div>
              {col.dataDesligamento && (
                <div>
                  <p className="text-xs text-gray-400">Desligamento</p>
                  <p className="text-sm font-medium text-red-700">
                    {new Date(col.dataDesligamento + "T12:00:00").toLocaleDateString("pt-BR")}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs text-gray-400">Salário</p>
                <p className="text-sm font-semibold text-gray-900">
                  R$ {col.salario.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <Link to="/recibos" className="flex-1">
          <Button variant="outline" className="w-full gap-2">
            <FileText className="w-4 h-4" />
            Gerar Recibo
          </Button>
        </Link>
        {col.situacao === "Ativo" && (
          <Link to="/rescisoes" state={{ colaboradorId: col.id }} className="flex-1">
            <Button
              variant="outline"
              className="w-full gap-2 border-red-200 text-red-700 hover:bg-red-50"
            >
              <FileX2 className="w-4 h-4" />
              Iniciar Rescisão
            </Button>
          </Link>
        )}
      </div>

      {/* Reuse info */}
      <ReuseInfo col={col} />
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

type RightMode = "detail" | "new" | "edit";

export function Colaboradores() {
  const [cols, setCols] = useState<Colaborador[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Mesma fonte de dados da tela de Rescisões: a API
  useEffect(() => {
    getColaboradores()
      .then(setCols)
      .catch((e) =>
        setLoadError(e instanceof ApiError ? e.message : "Erro ao carregar colaboradores.")
      )
      .finally(() => setLoading(false));
  }, []);
  const [search, setSearch] = useState("");
  const [situacaoFilter, setSituacaoFilter] = useState<"Todos" | "Ativo" | "Desligado">("Todos");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<RightMode>("detail");

  const filtered = cols.filter((c) => {
    const matchSearch =
      c.nome.toLowerCase().includes(search.toLowerCase()) ||
      c.cpf.includes(search) ||
      c.empresa.toLowerCase().includes(search.toLowerCase());
    const matchSituacao = situacaoFilter === "Todos" || c.situacao === situacaoFilter;
    return matchSearch && matchSituacao;
  });

  const selected = cols.find((c) => c.id === selectedId);

  const handleSave = (fd: ColFormData) => {
    if (mode === "new") {
      const newCol: Colaborador = {
        id: `C${Date.now()}`,
        nome: fd.nome.trim(),
        cpf: fd.cpf.trim(),
        cargo: fd.cargo.trim(),
        empresa: fd.empresa.trim(),
        email: fd.email.trim(),
        telefone: fd.telefone.trim(),
        dataAdmissao: fd.dataAdmissao,
        salario: parseFloat(fd.salario.replace(",", ".")),
        situacao: fd.situacao,
      };
      setCols((prev) => [newCol, ...prev]);
      setSelectedId(newCol.id);
    } else if (mode === "edit" && selected) {
      setCols((prev) =>
        prev.map((c) =>
          c.id === selected.id
            ? {
                ...c,
                nome: fd.nome.trim(),
                cpf: fd.cpf.trim(),
                cargo: fd.cargo.trim(),
                empresa: fd.empresa.trim(),
                email: fd.email.trim(),
                telefone: fd.telefone.trim(),
                dataAdmissao: fd.dataAdmissao,
                salario: parseFloat(fd.salario.replace(",", ".")),
                situacao: fd.situacao,
              }
            : c
        )
      );
    }
    setMode("detail");
  };

  const handleCancel = () => setMode("detail");

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="px-5 py-5 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-lg font-semibold text-gray-900">Colaboradores</h1>
            <Button
              size="sm"
              className="bg-blue-700 hover:bg-blue-800 gap-1.5"
              onClick={() => { setSelectedId(null); setMode("new"); }}
            >
              <Plus className="w-3.5 h-3.5" />
              Novo
            </Button>
          </div>

          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Nome, CPF ou empresa..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-8 h-9 text-sm bg-gray-50"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Limpar busca"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Filter buttons */}
          <div className="flex gap-1.5">
            {(["Todos", "Ativo", "Desligado"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSituacaoFilter(s)}
                className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  situacaoFilter === s
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-14">Carregando…</p>
          ) : loadError ? (
            <div className="m-4 bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-red-800">Falha ao carregar</p>
              <p className="text-xs text-red-600 mt-1">{loadError}</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-14 px-5 text-center text-gray-400">
              <Search className="w-8 h-8 mb-3 opacity-30" />
              <p className="text-sm font-medium text-gray-500 mb-1">
                Nenhum colaborador encontrado
              </p>
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="text-xs text-blue-600 hover:text-blue-700 underline underline-offset-2 mt-1"
                >
                  Limpar busca
                </button>
              )}
            </div>
          ) : (
            filtered.map((col) => (
              <button
                key={col.id}
                onClick={() => {
                  setSelectedId(col.id);
                  setMode("detail");
                }}
                className={`w-full text-left px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  selectedId === col.id && mode === "detail"
                    ? "bg-blue-50 border-l-2 border-l-blue-600"
                    : ""
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 bg-gradient-to-br ${avatarColor(col.id)} rounded-xl flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}
                  >
                    {initials(col.nome)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900 truncate">{col.nome}</p>
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ml-2 ${
                          col.situacao === "Ativo" ? "bg-green-500" : "bg-gray-400"
                        }`}
                      />
                    </div>
                    <p className="text-xs text-gray-400 truncate">{col.cargo}</p>
                    <p className="text-xs text-gray-400 truncate">{col.empresa}</p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer count */}
        <div className="px-5 py-2.5 border-t border-gray-100 bg-gray-50">
          <p className="text-xs text-gray-400">
            {filtered.length} de {cols.length} colaboradores
          </p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {mode === "new" ? (
          <ColaboradorForm onSave={handleSave} onCancel={handleCancel} />
        ) : mode === "edit" && selected ? (
          <ColaboradorForm
            initial={selected}
            onSave={handleSave}
            onCancel={handleCancel}
          />
        ) : selected ? (
          <DetailPanel col={selected} onEdit={() => setMode("edit")} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <UserCheck className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm text-gray-500">
                Selecione um colaborador para visualizar os dados.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
