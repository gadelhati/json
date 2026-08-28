/**
 * Editor de registros JSON.
 *
 * Responsável por:
 * - Exibir os registros em um DataTable;
 * - Editar registros existentes;
 * - Criar novos registros;
 * - Excluir registros;
 * - Limpar o formulário;
 * - Gerar o download do JSON atualizado.
 *
 * O array jsonData é fornecido pelo template editor.html.
 *
 * editingIndex:
 *     null -> modo novo registro
 *     >= 0 -> índice do registro que está sendo editado
 */

let table;
let editingIndex = null;


/**
 * Coloca o formulário no modo "Novo registro".
 */
function newRecord() {

    editingIndex = null;

    document.getElementById("index").value = "";
    document.getElementById("id").value = "";
    document.getElementById("nome").value = "";
    document.getElementById("data").value = "";
    document.getElementById("tipo").value = "";

    document.getElementById("formTitle").textContent =
        "Novo registro";

    document.getElementById("saveButton").textContent =
        "Adicionar";
}


/**
 * Carrega um registro existente no formulário.
 *
 * @param {number} index Índice do registro no array jsonData.
 */
function editRecord(index) {

    editingIndex = index;

    const item = jsonData[index];

    document.getElementById("index").value = index;

    document.getElementById("id").value =
        item.id ?? "";

    document.getElementById("nome").value =
        item.nome ?? "";

    document.getElementById("data").value =
        item.data ?? "";

    document.getElementById("tipo").value =
        item.tipo ?? "";

    document.getElementById("formTitle").textContent =
        "Editar registro";

    document.getElementById("saveButton").textContent =
        "Salvar alteração";
}


/**
 * Obtém os dados atualmente preenchidos no formulário.
 *
 * @returns {Object} Registro preenchido.
 */
function getFormData() {

    return {

        id: Number(
            document
                .getElementById("id")
                .value
        ),

        nome:
            document
                .getElementById("nome")
                .value
                .trim(),

        data:
            document
                .getElementById("data")
                .value
                .trim(),

        tipo:
            document
                .getElementById("tipo")
                .value
                .trim()
    };
}


/**
 * Atualiza uma linha existente do DataTable.
 *
 * @param {number} index Índice do registro.
 */
function updateTableRow(index) {

    const item = jsonData[index];

    table
        .row(index)
        .data([
            item.id,
            item.nome,
            item.data,
            item.tipo,
            `
                <button
                    type="button"
                    class="btn btn-sm btn-primary edit-button"
                    data-index="${index}"
                >
                    Editar
                </button>

                <button
                    type="button"
                    class="btn btn-sm btn-danger delete-button"
                    data-index="${index}"
                >
                    Excluir
                </button>
            `
        ])
        .draw(false);
}


/**
 * Adiciona uma nova linha ao DataTable.
 *
 * @param {number} index Índice do novo registro.
 */
function addTableRow(index) {

    const item = jsonData[index];

    table
        .row
        .add([
            item.id,
            item.nome,
            item.data,
            item.tipo,
            `
                <button
                    type="button"
                    class="btn btn-sm btn-primary edit-button"
                    data-index="${index}"
                >
                    Editar
                </button>

                <button
                    type="button"
                    class="btn btn-sm btn-danger delete-button"
                    data-index="${index}"
                >
                    Excluir
                </button>
            `
        ])
        .draw(false);
}


/**
 * Salva o registro atual.
 *
 * Se editingIndex for null:
 *     cria um novo registro.
 *
 * Caso contrário:
 *     atualiza o registro existente.
 */
function saveRecord() {

    const item = getFormData();

    /*
     * Validação básica.
     */
    if (
        !item.nome ||
        !item.data ||
        !item.tipo
    ) {

        alert(
            "Preencha todos os campos."
        );

        return;
    }


    /*
     * Novo registro.
     */
    if (editingIndex === null) {

        jsonData.push(item);

        const newIndex =
            jsonData.length - 1;

        addTableRow(newIndex);

        alert(
            "Registro adicionado com sucesso."
        );
    }


    /*
     * Registro existente.
     */
    else {

        jsonData[editingIndex] = item;

        updateTableRow(editingIndex);

        alert(
            "Registro atualizado com sucesso."
        );
    }


    /*
     * Após salvar, volta ao modo
     * "Novo registro".
     */
    newRecord();
}


/**
 * Exclui um registro.
 *
 * @param {number} index Índice do registro.
 */
function deleteRecord(index) {

    const item = jsonData[index];

    if (!item) {
        return;
    }

    const confirmed = confirm(
        `Deseja realmente excluir o registro "${item.nome}"?`
    );

    if (!confirmed) {
        return;
    }


    /*
     * Remove o registro do array.
     */
    jsonData.splice(index, 1);


    /*
     * Reconstrói o DataTable.
     *
     * Isso é importante porque os índices dos registros
     * posteriores mudam após o splice().
     */
    table.clear();

    jsonData.forEach((item, i) => {

        table.row.add([
            item.id,
            item.nome,
            item.data,
            item.tipo,
            `
                <button
                    type="button"
                    class="btn btn-sm btn-primary edit-button"
                    data-index="${i}"
                >
                    Editar
                </button>

                <button
                    type="button"
                    class="btn btn-sm btn-danger delete-button"
                    data-index="${i}"
                >
                    Excluir
                </button>
            `
        ]);

    });

    table.draw();


    /*
     * Garante que o formulário não continue
     * apontando para o registro excluído.
     */
    newRecord();

    alert(
        "Registro excluído com sucesso."
    );
}


/**
 * Configura os eventos dos botões Editar e Excluir.
 *
 * Utilizamos event delegation para que os botões
 * criados dinamicamente pelo DataTable também funcionem.
 */
function configureTableEvents() {

    document
        .getElementById("jsonTable")
        .addEventListener(
            "click",
            function (event) {

                /*
                 * Botão Editar.
                 */
                const editButton =
                    event.target.closest(".edit-button");

                if (editButton) {

                    const index =
                        Number(
                            editButton.dataset.index
                        );

                    editRecord(index);

                    return;
                }


                /*
                 * Botão Excluir.
                 */
                const deleteButton =
                    event.target.closest(".delete-button");

                if (deleteButton) {

                    const index =
                        Number(
                            deleteButton.dataset.index
                        );

                    deleteRecord(index);
                }

            }
        );
}


/**
 * Inicialização da página.
 */
document.addEventListener(
    "DOMContentLoaded",
    function () {

        /*
         * Inicializa o DataTable.
         */
        table = new DataTable(
            "#jsonTable",
            {
                language: {
                    url:
                        "https://cdn.datatables.net/plug-ins/2.3.2/i18n/pt-BR.json"
                }
            }
        );


        /*
         * Botão Novo registro.
         */
        document
            .getElementById("newButton")
            .addEventListener(
                "click",
                function () {

                    newRecord();

                    document
                        .getElementById("id")
                        .focus();

                }
            );


        /*
         * Botão Limpar.
         */
        document
            .getElementById("cancelButton")
            .addEventListener(
                "click",
                function () {

                    newRecord();

                }
            );


        /*
         * Botão Adicionar/Salvar.
         */
        document
            .getElementById("saveButton")
            .addEventListener(
                "click",
                function () {

                    saveRecord();

                }
            );


        /*
         * Eventos da tabela.
         */
        configureTableEvents();


        /*
         * Botão Download.
         */
        document
            .getElementById("downloadButton")
            .addEventListener(
                "click",
                async function () {

                    try {

                        const response =
                            await fetch(
                                "/download",
                                {
                                    method: "POST",

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body:
                                        JSON.stringify(
                                            jsonData
                                        )
                                }
                            );


                        if (!response.ok) {

                            alert(
                                "Erro ao gerar o arquivo."
                            );

                            return;
                        }


                        const blob =
                            await response.blob();


                        const url =
                            window.URL
                                .createObjectURL(blob);


                        const link =
                            document
                                .createElement("a");


                        link.href = url;

                        link.download =
                            "dados.json";


                        document
                            .body
                            .appendChild(link);

                        link.click();

                        link.remove();


                        window.URL
                            .revokeObjectURL(url);

                    }

                    catch (error) {

                        console.error(error);

                        alert(
                            "Erro ao realizar o download."
                        );

                    }

                }
            );


        /*
         * Estado inicial do formulário.
         */
        newRecord();

    }
);
