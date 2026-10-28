async function carregarLista(url, alvo, renderizar) {
    const elemento = document.getElementById(alvo);
    if (!elemento) return;
    try {
        const resposta = await fetch(url);
        if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
        const dados = await resposta.json();
        elemento.innerHTML = dados.length
            ? dados.map(renderizar).join("")
            : "<p>Nenhum registro encontrado.</p>";
    } catch (erro) {
        elemento.innerHTML = `<p>Não foi possível carregar: ${erro.message}</p>`;
    }
}

function carregarColaboradores() {
    return carregarLista("/colaboradores/", "lista-colaboradores", (item) =>
        `<p><strong>${item.nome}</strong> — ${item.cargo || "Sem cargo"} — ${item.email}</p>`
    );
}

function carregarRescisoes() {
    return carregarLista("/rescisoes", "lista-rescisoes", (item) =>
        `<p><strong>Rescisão #${item.id}</strong> — ${item.causa_afastamento} — ${item.status}</p>`
    );
}

function carregarHistorico() {
    return carregarLista("/historico", "lista-historico", (item) =>
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

        // Quando entrar na página Empresa,
        // atualiza a lista de empresas
        if (pageId === "empresa") {
            carregarEmpresas();
        }
        if (pageId === "colaboradores") carregarColaboradores();
        if (pageId === "rescisao") carregarRescisoes();
        if (pageId === "historico") carregarHistorico();

    });

});

carregarColaboradores();


// ================================
// CADASTRO DE EMPRESA
// ================================

const empresaForm = document.getElementById("empresa-form");

empresaForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const dadosEmpresa = {

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


    try {

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


        const empresaCadastrada =
            await resposta.json();


        console.log(
            "Empresa cadastrada:",
            empresaCadastrada
        );


        alert(
            "Empresa cadastrada com sucesso!"
        );


        empresaForm.reset();


        // Atualiza a lista depois do cadastro
        carregarEmpresas();


    } catch (erro) {

        console.error(
            "Erro ao cadastrar empresa:",
            erro
        );


        alert(
            "Erro ao cadastrar a empresa. " +
            "Verifique se o backend está funcionando."
        );

    }

});


// ================================
// LISTAGEM DE EMPRESAS
// ================================

const listaEmpresas =
    document.getElementById("lista-empresas");


async function carregarEmpresas() {

    try {

        const resposta = await fetch(
            "/empresas"
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar as empresas."
            );

        }


        const empresas =
            await resposta.json();


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


            empresaCard.classList.add(
                "empresa-item"
            );


            empresaCard.innerHTML = `

                <div>

                    <h3>
                        ${empresa.razao_social}
                    </h3>

                    <p>
                        <strong>Nome Fantasia:</strong>
                        ${empresa.nome_fantasia}
                    </p>

                    <p>
                        <strong>CNPJ:</strong>
                        ${empresa.cnpj}
                    </p>

                    <p>
                        <strong>E-mail:</strong>
                        ${empresa.email}
                    </p>

                    <p>
                        <strong>Telefone:</strong>
                        ${empresa.telefone}
                    </p>

                    <p>
                        <strong>Cidade:</strong>
                        ${empresa.cidade ?? "-"}
                    </p>

                    <p>
                        <strong>Estado:</strong>
                        ${empresa.estado ?? "-"}
                    </p>

                    <div class="empresa-acoes">

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


            listaEmpresas.appendChild(
                empresaCard
            );

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
// EXCLUIR EMPRESA
// ================================

async function excluirEmpresa(empresaId) {

    const confirmar = confirm(
        "Tem certeza que deseja excluir esta empresa?"
    );


    // Se clicar em Cancelar, não exclui
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


        // Atualiza a lista depois da exclusão
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
