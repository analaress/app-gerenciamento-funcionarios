async function carregarLista(url, alvo, renderizar) {
    const elemento = document.getElementById(alvo);

    if (!elemento) return;

    try {
        const resposta = await fetch(url);

        if (!resposta.ok) {
            throw new Error(`HTTP ${resposta.status}`);
        }

        const dados = await resposta.json();

        elemento.innerHTML = dados.length
            ? dados.map(renderizar).join("")
            : "<p>Nenhum registro encontrado.</p>";

    } catch (erro) {
        elemento.innerHTML =
            `<p>Não foi possível carregar: ${erro.message}</p>`;
    }
}


function carregarColaboradores() {
    return carregarLista(
        "/colaboradores/",
        "lista-colaboradores",
        (item) =>
            `<p><strong>${item.nome}</strong> — ${item.cargo || "Sem cargo"} — ${item.email}</p>`
    );
}


function carregarRescisoes() {
    return carregarLista(
        "/rescisoes",
        "lista-rescisoes",
        (item) =>
            `<p><strong>Rescisão #${item.id}</strong> — ${item.causa_afastamento} — ${item.status}</p>`
    );
}


function carregarHistorico() {
    return carregarLista(
        "/historico",
        "lista-historico",
        (item) =>
            `<p><strong>${item.tipo || "Documento"}</strong> — ${item.status || "Sem status"}</p>`
    );
}


// ================================
// NAVEGAÇÃO DO MENU
// ================================

const menuItems = document.querySelectorAll(".menu-item");
const pages = document.querySelectorAll(".page");

menuItems.forEach((item) => {

    item.addEventListener("click", () => {

        const pageId = item.dataset.page;

        menuItems.forEach((menuItem) => {
            menuItem.classList.remove("active");
        });

        item.classList.add("active");

        pages.forEach((page) => {
            page.classList.remove("active-page");
        });

        const selectedPage = document.getElementById(pageId);

        if (selectedPage) {
            selectedPage.classList.add("active-page");
        }

        if (pageId === "empresa") {
            carregarEmpresas();
        }

        if (pageId === "colaboradores") {
            carregarColaboradores();
        }

        if (pageId === "rescisao") {
            carregarRescisoes();
        }

        if (pageId === "historico") {
            carregarHistorico();
        }

    });

});


carregarColaboradores();


// ================================
// ELEMENTOS DA EMPRESA
// ================================

const empresaForm = document.getElementById("empresa-form");

const btnEmpresaSubmit =
    document.getElementById("btn-empresa-submit");

const btnCancelarEdicao =
    document.getElementById("btn-cancelar-edicao");

const listaEmpresas =
    document.getElementById("lista-empresas");


let empresaEditandoId = null;


// ================================
// PEGAR DADOS DO FORMULÁRIO
// ================================

function pegarDadosEmpresa() {

    return {

        razao_social:
            empresaForm.elements["razao_social"].value,

        nome_fantasia:
            empresaForm.elements["nome_fantasia"].value,

        cnpj:
            empresaForm.elements["cnpj"].value,

        email:
            empresaForm.elements["email"].value,

        telefone:
            empresaForm.elements["telefone"].value,

        cep:
            empresaForm.elements["cep"].value,

        logradouro:
            empresaForm.elements["logradouro"].value,

        numero:
            empresaForm.elements["numero"].value,

        complemento:
            empresaForm.elements["complemento"].value,

        bairro:
            empresaForm.elements["bairro"].value,

        cidade:
            empresaForm.elements["cidade"].value,

        estado:
            empresaForm.elements["estado"].value,

        representante_legal:
            empresaForm.elements["representante_legal"].value

    };

}


// ================================
// CADASTRAR / EDITAR EMPRESA
// ================================

empresaForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const dadosEmpresa = pegarDadosEmpresa();

    try {

        if (empresaEditandoId !== null) {

            const resposta = await fetch(
                `/empresas/${empresaEditandoId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(dadosEmpresa)
                }
            );

            if (!resposta.ok) {
                throw new Error(
                    "Não foi possível atualizar a empresa."
                );
            }

            alert("Empresa atualizada com sucesso!");

        } else {

            const resposta = await fetch(
                "/empresas",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(dadosEmpresa)
                }
            );

            if (!resposta.ok) {
                throw new Error(
                    "Não foi possível cadastrar a empresa."
                );
            }

            alert("Empresa cadastrada com sucesso!");
        }


        empresaForm.reset();

        sairDoModoEdicao();

        carregarEmpresas();


    } catch (erro) {

        console.error(
            "Erro ao salvar empresa:",
            erro
        );

        alert(
            "Erro ao salvar a empresa. " +
            "Verifique se o backend está funcionando."
        );
    }

});


// ================================
// LISTAGEM DE EMPRESAS
// ================================

async function carregarEmpresas() {

    try {

        const resposta = await fetch("/empresas");

        if (!resposta.ok) {
            throw new Error(
                "Não foi possível carregar as empresas."
            );
        }

        const empresas = await resposta.json();

        listaEmpresas.innerHTML = "";


        if (empresas.length === 0) {

            listaEmpresas.innerHTML = `
                <p>Nenhuma empresa cadastrada.</p>
            `;

            return;
        }


        empresas.forEach((empresa) => {

            const empresaCard =
                document.createElement("div");

            empresaCard.classList.add("empresa-item");


            empresaCard.innerHTML = `

                <div class="empresa-resumo">

                    <div class="empresa-info-principal">

                        <h3>
                            ${empresa.razao_social}
                        </h3>

                        <p>
                            ${empresa.nome_fantasia}
                        </p>

                        <p>
                            <strong>CNPJ:</strong>
                            ${empresa.cnpj}
                        </p>

                    </div>


                    <div class="empresa-contatos">

                        <p>
                            <strong>E-mail:</strong>
                            ${empresa.email}
                        </p>

                        <p>
                            <strong>Telefone:</strong>
                            ${empresa.telefone}
                        </p>

                    </div>

                </div>


                <button
                    type="button"
                    class="btn-detalhes"
                    onclick="mostrarDetalhesEmpresa(${empresa.id}, this)"
                >
                    Ver detalhes
                </button>


                <div
                    class="empresa-detalhes"
                    id="detalhes-empresa-${empresa.id}"
                    style="display: none;"
                >

                    <div class="detalhes-secao">

                        <h4>Dados da empresa</h4>

                        <div class="detalhes-grid">

                            <p>
                                <strong>Razão Social:</strong><br>
                                ${empresa.razao_social || "-"}
                            </p>

                            <p>
                                <strong>Nome Fantasia:</strong><br>
                                ${empresa.nome_fantasia || "-"}
                            </p>

                            <p>
                                <strong>CNPJ:</strong><br>
                                ${empresa.cnpj || "-"}
                            </p>

                            <p>
                                <strong>E-mail:</strong><br>
                                ${empresa.email || "-"}
                            </p>

                            <p>
                                <strong>Telefone:</strong><br>
                                ${empresa.telefone || "-"}
                            </p>

                        </div>

                    </div>


                    <div class="detalhes-secao">

                        <h4>Endereço</h4>

                        <div class="detalhes-grid">

                            <p>
                                <strong>CEP:</strong><br>
                                ${empresa.cep || "-"}
                            </p>

                            <p>
                                <strong>Logradouro:</strong><br>
                                ${empresa.logradouro || "-"}
                            </p>

                            <p>
                                <strong>Número:</strong><br>
                                ${empresa.numero || "-"}
                            </p>

                            <p>
                                <strong>Complemento:</strong><br>
                                ${empresa.complemento || "-"}
                            </p>

                            <p>
                                <strong>Bairro:</strong><br>
                                ${empresa.bairro || "-"}
                            </p>

                            <p>
                                <strong>Cidade:</strong><br>
                                ${empresa.cidade || "-"}
                            </p>

                            <p>
                                <strong>Estado:</strong><br>
                                ${empresa.estado || "-"}
                            </p>

                        </div>

                    </div>


                    <div class="detalhes-secao">

                        <h4>Representante Legal</h4>

                        <p>
                            ${empresa.representante_legal || "-"}
                        </p>

                    </div>


                    <div class="empresa-acoes">

                        <button
                            type="button"
                            class="btn-primary"
                            onclick="editarEmpresa(${empresa.id})"
                        >
                            Editar
                        </button>

                        <button
                            type="button"
                            class="btn-excluir"
                            onclick="excluirEmpresa(${empresa.id})"
                        >
                            Excluir
                        </button>

                    </div>

                </div>

            `;


            listaEmpresas.appendChild(empresaCard);

        });


    } catch (erro) {

        console.error(
            "Erro ao carregar empresas:",
            erro
        );

        listaEmpresas.innerHTML = `
            <p>
                Erro ao carregar as empresas.
            </p>
        `;
    }

}


// ================================
// MOSTRAR / ESCONDER DETALHES
// ================================

function mostrarDetalhesEmpresa(empresaId, botao) {

    const detalhes =
        document.getElementById(
            `detalhes-empresa-${empresaId}`
        );


    if (!detalhes) {
        return;
    }


    if (detalhes.style.display === "none") {

        detalhes.style.display = "block";

        botao.textContent = "Ocultar detalhes";

    } else {

        detalhes.style.display = "none";

        botao.textContent = "Ver detalhes";
    }

}


// ================================
// EDITAR EMPRESA
// ================================

async function editarEmpresa(empresaId) {

    try {

        const resposta = await fetch(
            `/empresas/${empresaId}`
        );

        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar os dados da empresa."
            );
        }


        const empresa =
            await resposta.json();


        empresaEditandoId = empresa.id;


        empresaForm.elements["razao_social"].value =
            empresa.razao_social ?? "";

        empresaForm.elements["nome_fantasia"].value =
            empresa.nome_fantasia ?? "";

        empresaForm.elements["cnpj"].value =
            empresa.cnpj ?? "";

        empresaForm.elements["email"].value =
            empresa.email ?? "";

        empresaForm.elements["telefone"].value =
            empresa.telefone ?? "";

        empresaForm.elements["cep"].value =
            empresa.cep ?? "";

        empresaForm.elements["logradouro"].value =
            empresa.logradouro ?? "";

        empresaForm.elements["numero"].value =
            empresa.numero ?? "";

        empresaForm.elements["complemento"].value =
            empresa.complemento ?? "";

        empresaForm.elements["bairro"].value =
            empresa.bairro ?? "";

        empresaForm.elements["cidade"].value =
            empresa.cidade ?? "";

        empresaForm.elements["estado"].value =
            empresa.estado ?? "";

        empresaForm.elements["representante_legal"].value =
            empresa.representante_legal ?? "";


        btnEmpresaSubmit.textContent =
            "Salvar Alterações";


        btnCancelarEdicao.style.display =
            "inline-block";


        empresaForm.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (erro) {

        console.error(
            "Erro ao editar empresa:",
            erro
        );

        alert(
            "Erro ao carregar os dados da empresa."
        );
    }

}


// ================================
// CANCELAR EDIÇÃO
// ================================

btnCancelarEdicao.addEventListener(
    "click",
    () => {

        empresaForm.reset();

        sairDoModoEdicao();

    }
);


function sairDoModoEdicao() {

    empresaEditandoId = null;

    btnEmpresaSubmit.textContent =
        "Cadastrar Empresa";

    btnCancelarEdicao.style.display =
        "none";

}


// ================================
// EXCLUIR EMPRESA
// ================================

async function excluirEmpresa(empresaId) {

    const confirmar = confirm(
        "Tem certeza que deseja excluir esta empresa?"
    );


    if (!confirmar) {
        return;
    }


    try {

        const resposta = await fetch(
            `/empresas/${empresaId}`,
            {
                method: "DELETE"
            }
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível excluir a empresa."
            );
        }


        alert(
            "Empresa excluída com sucesso!"
        );


        carregarEmpresas();


    } catch (erro) {

        console.error(
            "Erro ao excluir empresa:",
            erro
        );


        alert(
            "Erro ao excluir a empresa."
        );
    }

}