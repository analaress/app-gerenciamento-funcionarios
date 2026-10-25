import { Link } from "react-router";
import {
  FileText,
  FileX2,
  Clock,
  CheckCircle,
  Send,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { documentos, colaboradores } from "../data/mockData";

const statusColors: Record<string, string> = {
  Pendente: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  "Em Conferência": "bg-blue-100 text-blue-700 hover:bg-blue-100",
  Gerado: "bg-purple-100 text-purple-700 hover:bg-purple-100",
  Enviado: "bg-green-100 text-green-700 hover:bg-green-100",
  "Erro Geração": "bg-red-100 text-red-700 hover:bg-red-100",
  "Erro Envio": "bg-red-100 text-red-700 hover:bg-red-100",
};

export function Dashboard() {
  const recibos = documentos.filter((d) => d.tipo === "Recibo");
  const rescisoes = documentos.filter((d) => d.tipo === "Rescisão");

  const recibosPendentes = recibos.filter((d) => d.status === "Pendente").length;
  const recibosGerados = recibos.filter((d) => d.status === "Gerado").length;
  const recibosEnviados = recibos.filter((d) => d.status === "Enviado").length;
  const rescisoesPendentes = rescisoes.filter((d) => d.status === "Pendente").length;
  const rescisoesGeradas = rescisoes.filter((d) => d.status === "Gerado").length;
  const aguardandoEnvio = documentos.filter((d) => d.status === "Gerado").length;

  const colaboradoresAtivos = colaboradores.filter((c) => c.situacao === "Ativo").length;
  const colaboradoresDesligados = colaboradores.filter((c) => c.situacao === "Desligado").length;

  const recentes = [...documentos]
    .sort((a, b) => {
      const da = a.dataGeracao ?? a.dataEnvio ?? "0";
      const db = b.dataGeracao ?? b.dataEnvio ?? "0";
      return db.localeCompare(da);
    })
    .slice(0, 6);

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            {new Date().toLocaleDateString("pt-BR", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>
        {(recibosPendentes + rescisoesPendentes) > 0 && (
          <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-700">
              {recibosPendentes + rescisoesPendentes} documento(s) aguardando processamento
            </span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-5">
        {/* Recibos block */}
        <Card className="col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                Recibos
              </CardTitle>
              <Link to="/recibos" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
                Gerenciar <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-amber-700 font-medium">Pendentes</span>
                  <Clock className="w-4 h-4 text-amber-500" />
                </div>
                <p className="text-3xl font-bold text-amber-800">{recibosPendentes}</p>
              </div>
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-purple-700 font-medium">Gerados</span>
                  <FileText className="w-4 h-4 text-purple-500" />
                </div>
                <p className="text-3xl font-bold text-purple-800">{recibosGerados}</p>
              </div>
              <div className="bg-green-50 rounded-xl p-4 border border-green-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-green-700 font-medium">Enviados</span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <p className="text-3xl font-bold text-green-800">{recibosEnviados}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Aguardando envio */}
        <Card className="bg-blue-700 border-blue-700">
          <CardContent className="p-6 flex flex-col justify-between h-full">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs text-blue-200 font-medium uppercase tracking-wide">
                Aguardando Envio
              </span>
              <Send className="w-4 h-4 text-blue-300" />
            </div>
            <div>
              <p className="text-5xl font-bold text-white mb-1">{aguardandoEnvio}</p>
              <p className="text-sm text-blue-200">documento(s) gerados, ainda não enviados</p>
            </div>
            <Link
              to="/historico"
              className="mt-4 text-xs text-blue-200 hover:text-white flex items-center gap-1 transition-colors"
            >
              Ver todos <ArrowRight className="w-3 h-3" />
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Rescisões block */}
        <Card className="col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                Rescisões
              </CardTitle>
              <Link to="/rescisoes" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
                Gerenciar <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-red-50 rounded-xl p-4 border border-red-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-red-700 font-medium">Pendentes</span>
                  <Clock className="w-4 h-4 text-red-400" />
                </div>
                <p className="text-3xl font-bold text-red-800">{rescisoesPendentes}</p>
              </div>
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-purple-700 font-medium">Geradas</span>
                  <FileX2 className="w-4 h-4 text-purple-500" />
                </div>
                <p className="text-3xl font-bold text-purple-800">{rescisoesGeradas}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Colaboradores */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                Colaboradores
              </CardTitle>
              <Link to="/colaboradores" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
                Ver todos <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-sm text-gray-700">Ativos</span>
              </div>
              <span className="text-lg font-bold text-green-800">{colaboradoresAtivos}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full" />
                <span className="text-sm text-gray-700">Desligados</span>
              </div>
              <span className="text-lg font-bold text-gray-700">{colaboradoresDesligados}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-100">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
                <span className="text-sm text-gray-700">Total</span>
              </div>
              <span className="text-lg font-bold text-blue-800">{colaboradores.length}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent documents */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold text-gray-900">
              Atividade Recente
            </CardTitle>
            <Link to="/historico" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
              Ver histórico completo <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="text-left px-6 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Colaborador</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Empresa</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Tipo</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Referência</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentes.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors last:border-0">
                  <td className="px-6 py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{doc.colaboradorNome}</p>
                      <p className="text-xs text-gray-400">{doc.colaboradorCpf}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{doc.empresa}</td>
                  <td className="px-4 py-3">
                    <Badge
                      variant="outline"
                      className={
                        doc.tipo === "Recibo"
                          ? "bg-blue-50 text-blue-700 border-blue-200"
                          : "bg-orange-50 text-orange-700 border-orange-200"
                      }
                    >
                      {doc.tipo}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {doc.competencia ?? doc.dataDesligamento ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={statusColors[doc.status]}>{doc.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
