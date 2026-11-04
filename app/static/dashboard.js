const table = document.querySelector("#records-table");

if (table) {
    const body = table.tBodies[0];
    const search = document.querySelector("#record-search");
    const count = document.querySelector("#record-count");
    const emptyRow = document.querySelector("#no-records-match");
    const sortableHeaders = [...table.tHead.querySelectorAll("[data-sort-column]")];
    const collator = new Intl.Collator("pt-BR", {
        numeric: true,
        sensitivity: "base",
    });
    let sortColumn = -1;
    let sortDirection = 1;

    const dataRows = () =>
        [...body.rows].filter((row) => row !== emptyRow);

    const updateRows = () => {
        const query = search.value.trim().toLocaleLowerCase("pt-BR");
        let visibleCount = 0;

        for (const row of dataRows()) {
            const searchableText = [...row.cells]
                .slice(0, -1)
                .map((cell) => cell.textContent)
                .join(" ")
                .toLocaleLowerCase("pt-BR");
            row.hidden = !searchableText.includes(query);
            if (!row.hidden) visibleCount += 1;
        }

        emptyRow.hidden = visibleCount > 0;
        count.textContent = `${visibleCount} de ${dataRows().length} registro(s)`;
    };

    search.addEventListener("input", updateRows);

    sortableHeaders.forEach((button, index) => {
        button.addEventListener("click", () => {
            const header = button.closest("th");
            if (sortColumn === index) {
                sortDirection *= -1;
            } else {
                sortColumn = index;
                sortDirection = 1;
            }

            for (const otherHeader of sortableHeaders) {
                otherHeader.closest("th").setAttribute("aria-sort", "none");
            }
            header.setAttribute(
                "aria-sort",
                sortDirection === 1 ? "ascending" : "descending",
            );

            const rows = dataRows().sort((left, right) => {
                const leftText = left.cells[index].textContent.trim();
                const rightText = right.cells[index].textContent.trim();
                return sortDirection * collator.compare(leftText, rightText);
            });

            for (const row of rows) body.append(row);
            body.append(emptyRow);
            updateRows();
        });
    });

    updateRows();
}
