import { useState } from "react";
import { Mail, Check, X, Loader2, RefreshCw, Download, ArrowLeft } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

type FlowStep = "confirm" | "sending" | "success" | "failed";

interface Props {
  email: string;
  docLabel: string;
  collaboratorName: string;
  onBack: () => void;
  onDone: () => void;
  onSendSuccess?: () => void;
  /** Envio real: se informado, é chamado ao confirmar (deve lançar erro se falhar). Sem ele, o envio é simulado. */
  onSend?: (email: string) => Promise<void>;
  /** Endereço do PDF, para o botão "Baixar PDF". */
  pdfHref?: string;
}

export function SendEmailFlow({
  email: initialEmail,
  docLabel,
  collaboratorName,
  onBack,
  onDone,
  onSendSuccess,
  onSend,
  pdfHref,
}: Props) {
  const [step, setStep] = useState<FlowStep>("confirm");
  const [email, setEmail] = useState(initialEmail);
  const [erro, setErro] = useState<string | null>(null);

  const handleSend = async () => {
    setStep("sending");
    setErro(null);
    if (onSend) {
      try {
        await onSend(email.trim());
        setStep("success");
      } catch (e) {
        setErro(e instanceof Error ? e.message : "Não foi possível enviar o e-mail.");
        setStep("failed");
      }
      return;
    }
    setTimeout(() => {
      const ok = Math.random() > 0.3;
      setStep(ok ? "success" : "failed");
    }, 2500);
  };

  const handleConcluir = () => {
    if (step === "success") onSendSuccess?.();
    onDone();
  };

  if (step === "confirm") {
    return (
      <div className="space-y-6 max-w-md">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Enviar por E-mail</h3>
          <p className="text-sm text-gray-500">Confirme o endereço antes de enviar o documento.</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Documento</p>
            <p className="text-sm font-semibold text-gray-800">{docLabel}</p>
            <p className="text-xs text-gray-500 mt-0.5">{collaboratorName}</p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">
              E-mail do destinatário
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-9 h-10"
              />
            </div>
            <p className="text-xs text-gray-400 mt-1.5">
              E-mail cadastrado do colaborador. Edite se necessário.
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={onBack} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Button>
          <Button
            className="flex-1 bg-blue-700 hover:bg-blue-800 gap-2"
            disabled={!email.trim()}
            onClick={handleSend}
          >
            <Mail className="w-4 h-4" />
            Confirmar Envio
          </Button>
        </div>
      </div>
    );
  }

  if (step === "sending") {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="relative w-20 h-20 mb-6">
          <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center">
            <Mail className="w-8 h-8 text-blue-300" />
          </div>
          <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md border border-gray-100">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          </div>
        </div>
        <p className="font-semibold text-gray-800 text-lg">Enviando documento...</p>
        <p className="text-sm text-gray-400 mt-1 text-center">
          Aguarde enquanto o e-mail é enviado para
        </p>
        <p className="text-sm font-medium text-gray-600 mt-0.5">{email}</p>
      </div>
    );
  }

  if (step === "success") {
    return (
      <div className="flex flex-col items-center py-10 max-w-sm mx-auto">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-5">
          <Check className="w-10 h-10 text-green-600" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-1">Enviado com Sucesso!</h3>
        <p className="text-sm text-gray-500 text-center mb-5">{docLabel}</p>

        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3 mb-8 w-full">
          <div className="w-9 h-9 bg-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Mail className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-gray-400">Enviado para</p>
            <p className="text-sm font-medium text-gray-800 truncate">{email}</p>
          </div>
          <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
        </div>

        <div className="flex gap-3 w-full">
          {pdfHref ? (
            <Button asChild variant="outline" className="flex-1 gap-2">
              <a href={pdfHref} target="_blank" rel="noreferrer">
                <Download className="w-4 h-4" />
                Baixar PDF
              </a>
            </Button>
          ) : (
            <Button variant="outline" className="flex-1 gap-2">
              <Download className="w-4 h-4" />
              Baixar PDF
            </Button>
          )}
          <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleConcluir}>
            Concluir
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center py-10 max-w-sm mx-auto">
      <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-5">
        <X className="w-10 h-10 text-red-500" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-1">Envio Falhou</h3>
      <p className="text-sm text-gray-500 text-center mb-2">
        Não foi possível entregar o documento.
      </p>

      <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-2 w-full">
        <div className="w-9 h-9 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <Mail className="w-4 h-4 text-red-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-gray-400">Tentativa para</p>
          <p className="text-sm font-medium text-gray-800 truncate">{email}</p>
        </div>
        <X className="w-4 h-4 text-red-500 flex-shrink-0" />
      </div>

      {erro && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3 w-full break-words">
          {erro}
        </p>
      )}
      <p className="text-xs text-gray-400 mb-8 text-center">
        Verifique se o endereço está correto e tente novamente.
      </p>

      <div className="flex gap-3 w-full">
        {pdfHref ? (
          <Button asChild variant="outline" className="flex-1 gap-2">
            <a href={pdfHref} target="_blank" rel="noreferrer">
              <Download className="w-4 h-4" />
              Baixar PDF
            </a>
          </Button>
        ) : (
          <Button variant="outline" className="flex-1 gap-2">
            <Download className="w-4 h-4" />
            Baixar PDF
          </Button>
        )}
        <Button
          className="flex-1 gap-2 bg-blue-700 hover:bg-blue-800"
          onClick={() => setStep("confirm")}
        >
          <RefreshCw className="w-4 h-4" />
          Tentar Novamente
        </Button>
      </div>
      <button
        className="mt-4 text-sm text-gray-400 hover:text-gray-600"
        onClick={handleConcluir}
      >
        Fechar
      </button>
    </div>
  );
}
