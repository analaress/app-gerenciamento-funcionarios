export interface Colaborador {
  id: string;
  nome: string;
  cpf: string;
  email: string;
  telefone: string;
  empresa: string;
  cargo: string;
  salario: number;
  dataAdmissao: string;
  situacao: "Ativo" | "Desligado";
  dataDesligamento?: string;
}

export type DocumentoStatus =
  | "Pendente"
  | "Em Conferência"
  | "Gerado"
  | "Enviado"
  | "Erro Geração"
  | "Erro Envio";

export type DocumentoTipo = "Recibo" | "Rescisão";

export type MotivoDesligamento =
  | "Sem justa causa"
  | "Com justa causa"
  | "Pedido de demissão"
  | "Acordo";

export interface Documento {
  id: string;
  colaboradorId: string;
  colaboradorNome: string;
  colaboradorCpf: string;
  empresa: string;
  tipo: DocumentoTipo;
  status: DocumentoStatus;
  competencia?: string;
  motivoDesligamento?: MotivoDesligamento;
  dataDesligamento?: string;
  dataGeracao?: string;
  dataEnvio?: string;
  usuarioResponsavel: string;
}

export const colaboradores: Colaborador[] = [
  {
    id: "1",
    nome: "Ana Paula Ferreira",
    cpf: "123.456.789-00",
    email: "ana.ferreira@techsolutions.com.br",
    telefone: "(11) 98765-4321",
    empresa: "Tech Solutions Ltda",
    cargo: "Analista de Sistemas",
    salario: 5500,
    dataAdmissao: "2022-03-15",
    situacao: "Ativo",
  },
  {
    id: "2",
    nome: "Carlos Eduardo Santos",
    cpf: "987.654.321-00",
    email: "carlos.santos@comerciobrasil.com.br",
    telefone: "(11) 97654-3210",
    empresa: "Comércio Brasil S.A.",
    cargo: "Supervisor de Vendas",
    salario: 4200,
    dataAdmissao: "2021-07-01",
    situacao: "Ativo",
  },
  {
    id: "3",
    nome: "Mariana Costa Oliveira",
    cpf: "456.123.789-00",
    email: "mariana.oliveira@inovetech.com.br",
    telefone: "(11) 96543-2109",
    empresa: "Inove Tech Ltda",
    cargo: "Designer de Produto",
    salario: 4800,
    dataAdmissao: "2023-01-10",
    situacao: "Ativo",
  },
  {
    id: "4",
    nome: "Roberto Alves Lima",
    cpf: "789.321.654-00",
    email: "roberto.lima@construpress.com.br",
    telefone: "(11) 95432-1098",
    empresa: "Construpress Engenharia",
    cargo: "Engenheiro Civil",
    salario: 9200,
    dataAdmissao: "2020-05-20",
    situacao: "Ativo",
  },
  {
    id: "5",
    nome: "Juliana Mendes Rocha",
    cpf: "321.654.987-00",
    email: "juliana.rocha@foodexpress.com.br",
    telefone: "(11) 94321-0987",
    empresa: "Food Express Ltda",
    cargo: "Gerente Operacional",
    salario: 6800,
    dataAdmissao: "2019-11-08",
    situacao: "Desligado",
    dataDesligamento: "2026-08-31",
  },
  {
    id: "6",
    nome: "Fernando Souza Castro",
    cpf: "654.987.321-00",
    email: "fernando.castro@comerciobrasil.com.br",
    telefone: "(11) 93210-9876",
    empresa: "Comércio Brasil S.A.",
    cargo: "Vendedor",
    salario: 2800,
    dataAdmissao: "2021-02-14",
    situacao: "Ativo",
  },
  {
    id: "7",
    nome: "Patrícia Lima Nascimento",
    cpf: "111.222.333-44",
    email: "patricia.nascimento@alphalogistica.com.br",
    telefone: "(11) 92109-8765",
    empresa: "Alpha Logística Ltda",
    cargo: "Coordenadora de Logística",
    salario: 5900,
    dataAdmissao: "2020-08-03",
    situacao: "Ativo",
  },
  {
    id: "8",
    nome: "Thiago Melo Barbosa",
    cpf: "555.666.777-88",
    email: "thiago.barbosa@inovetech.com.br",
    telefone: "(11) 91098-7654",
    empresa: "Inove Tech Ltda",
    cargo: "Desenvolvedor Backend",
    salario: 7400,
    dataAdmissao: "2022-09-19",
    situacao: "Desligado",
    dataDesligamento: "2026-09-01",
  },
];

export const documentos: Documento[] = [
  {
    id: "D001",
    colaboradorId: "1",
    colaboradorNome: "Ana Paula Ferreira",
    colaboradorCpf: "123.456.789-00",
    empresa: "Tech Solutions Ltda",
    tipo: "Recibo",
    status: "Enviado",
    competencia: "Agosto/2026",
    dataGeracao: "2026-09-05",
    dataEnvio: "2026-09-05",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D002",
    colaboradorId: "2",
    colaboradorNome: "Carlos Eduardo Santos",
    colaboradorCpf: "987.654.321-00",
    empresa: "Comércio Brasil S.A.",
    tipo: "Recibo",
    status: "Gerado",
    competencia: "Agosto/2026",
    dataGeracao: "2026-09-05",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D003",
    colaboradorId: "5",
    colaboradorNome: "Juliana Mendes Rocha",
    colaboradorCpf: "321.654.987-00",
    empresa: "Food Express Ltda",
    tipo: "Rescisão",
    status: "Pendente",
    motivoDesligamento: "Sem justa causa",
    dataDesligamento: "2026-08-31",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D004",
    colaboradorId: "3",
    colaboradorNome: "Mariana Costa Oliveira",
    colaboradorCpf: "456.123.789-00",
    empresa: "Inove Tech Ltda",
    tipo: "Recibo",
    status: "Enviado",
    competencia: "Agosto/2026",
    dataGeracao: "2026-09-03",
    dataEnvio: "2026-09-03",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D005",
    colaboradorId: "4",
    colaboradorNome: "Roberto Alves Lima",
    colaboradorCpf: "789.321.654-00",
    empresa: "Construpress Engenharia",
    tipo: "Recibo",
    status: "Enviado",
    competencia: "Julho/2026",
    dataGeracao: "2026-08-05",
    dataEnvio: "2026-08-06",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D006",
    colaboradorId: "8",
    colaboradorNome: "Thiago Melo Barbosa",
    colaboradorCpf: "555.666.777-88",
    empresa: "Inove Tech Ltda",
    tipo: "Rescisão",
    status: "Pendente",
    motivoDesligamento: "Pedido de demissão",
    dataDesligamento: "2026-09-01",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D007",
    colaboradorId: "7",
    colaboradorNome: "Patrícia Lima Nascimento",
    colaboradorCpf: "111.222.333-44",
    empresa: "Alpha Logística Ltda",
    tipo: "Recibo",
    status: "Enviado",
    competencia: "Agosto/2026",
    dataGeracao: "2026-09-04",
    dataEnvio: "2026-09-04",
    usuarioResponsavel: "RH Operacional",
  },
  {
    id: "D008",
    colaboradorId: "6",
    colaboradorNome: "Fernando Souza Castro",
    colaboradorCpf: "654.987.321-00",
    empresa: "Comércio Brasil S.A.",
    tipo: "Recibo",
    status: "Erro Envio",
    competencia: "Agosto/2026",
    dataGeracao: "2026-09-05",
    usuarioResponsavel: "RH Operacional",
  },
];

export function calcularINSS(salario: number): number {
  if (salario <= 1412) return salario * 0.075;
  if (salario <= 2666.68) return salario * 0.09;
  if (salario <= 4000.03) return salario * 0.12;
  if (salario <= 7786.02) return salario * 0.14;
  return Math.round(7786.02 * 0.14);
}

export function calcularIRRF(baseCalculo: number): number {
  if (baseCalculo <= 2259.2) return 0;
  if (baseCalculo <= 2826.65) return baseCalculo * 0.075 - 169.44;
  if (baseCalculo <= 3751.05) return baseCalculo * 0.15 - 381.44;
  if (baseCalculo <= 4664.68) return baseCalculo * 0.225 - 662.77;
  return baseCalculo * 0.275 - 896.0;
}

export interface ValoresRescisao {
  saldoSalario: number;
  feriasProporcionais: number;
  tercoFerias: number;
  decimoTerceiroProporcional: number;
  avisoPrevioIndenizado: number;
  multaFgts: number;
  fgtsDepositado: number;
  total: number;
}

export function calcularRescisao(
  colaborador: Colaborador,
  dataDesligamento: string,
  motivo: MotivoDesligamento
): ValoresRescisao {
  const salario = colaborador.salario;
  const admissao = new Date(colaborador.dataAdmissao);
  const desligamento = new Date(dataDesligamento + "T12:00:00");

  const diasNoMes = desligamento.getDate();
  const saldoSalario = Math.round((salario / 30) * diasNoMes);

  const mesesNoAno = desligamento.getMonth() + 1;
  const feriasProporcionais = Math.round((salario / 12) * mesesNoAno);
  const tercoFerias = Math.round(feriasProporcionais / 3);
  const decimoTerceiroProporcional = Math.round((salario / 12) * mesesNoAno);

  const avisoPrevioIndenizado =
    motivo === "Sem justa causa" || motivo === "Acordo" ? salario : 0;

  const mesesTrabalhados = Math.max(
    1,
    Math.floor(
      (desligamento.getTime() - admissao.getTime()) / (1000 * 60 * 60 * 24 * 30.44)
    )
  );
  const fgtsDepositado = Math.round(salario * 0.08 * mesesTrabalhados);
  const multaFgts =
    motivo === "Sem justa causa" || motivo === "Acordo"
      ? Math.round(fgtsDepositado * 0.4)
      : 0;

  const total =
    saldoSalario +
    feriasProporcionais +
    tercoFerias +
    decimoTerceiroProporcional +
    avisoPrevioIndenizado +
    multaFgts;

  return {
    saldoSalario,
    feriasProporcionais,
    tercoFerias,
    decimoTerceiroProporcional,
    avisoPrevioIndenizado,
    multaFgts,
    fgtsDepositado,
    total,
  };
}
