(() => {
    const normalize = (value) => value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase();

    function getSearchableText(item) {
        const copy = item.cloneNode(true);
        copy.querySelectorAll("button, [data-search-ignore], .row-actions").forEach((element) => element.remove());
        return normalize(copy.textContent || "");
    }

    function attachSearch(input) {
        const target = document.querySelector(input.dataset.recordSearch);
        const wrapper = input.closest(".record-search");
        const emptyMessage = wrapper?.querySelector(".record-search-empty");
        if (!target || !emptyMessage) return;

        const controls = document.createElement("div");
        controls.className = "search-controls";
        input.insertAdjacentElement("afterend", controls);
        controls.append(input);

        const searchButton = document.createElement("button");
        searchButton.type = "button";
        searchButton.className = "button button-primary";
        searchButton.textContent = "Search";
        controls.append(searchButton);

        const clearButton = document.createElement("button");
        clearButton.type = "button";
        clearButton.className = "button button-secondary";
        clearButton.textContent = "Clear";
        controls.append(clearButton);

        function filterRecords() {
            const query = normalize(input.value.trim());
            const entries = [...target.children];
            let visibleCount = 0;

            for (const entry of entries) {
                const isEmptyRow = entry.matches("tr") && entry.querySelector("td[colspan]");
                const matches = !query || (!isEmptyRow && getSearchableText(entry).includes(query));
                entry.classList.toggle("record-search-filtered", !matches);
                if (matches && !isEmptyRow) visibleCount += 1;
            }

            emptyMessage.hidden = !query || visibleCount > 0;
        }

        input.addEventListener("input", filterRecords);
        searchButton.addEventListener("click", filterRecords);
        clearButton.addEventListener("click", () => {
            input.value = "";
            filterRecords();
            input.focus();
        });
        new MutationObserver(filterRecords).observe(target, { childList: true, subtree: false });
        filterRecords();
    }

    document.querySelectorAll("[data-record-search]").forEach(attachSearch);
})();
