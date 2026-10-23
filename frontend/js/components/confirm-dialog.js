(() => {
    let dialog;
    let titleElement;
    let messageElement;
    let confirmButton;
    let pendingResolve;

    function getDialog() {
        if (dialog) return dialog;

        dialog = document.createElement("dialog");
        dialog.className = "confirm-dialog";
        dialog.setAttribute("aria-labelledby", "confirmDialogTitle");

        const card = document.createElement("section");
        card.className = "confirm-card";

        const icon = document.createElement("div");
        icon.className = "confirm-dialog-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" stroke-linecap="round" stroke-linejoin="round"/></svg>';

        const content = document.createElement("div");
        content.className = "confirm-dialog-content";

        titleElement = document.createElement("h2");
        titleElement.className = "confirm-dialog-title";
        titleElement.id = "confirmDialogTitle";

        messageElement = document.createElement("p");
        messageElement.className = "confirm-dialog-message";

        const actions = document.createElement("div");
        actions.className = "confirm-dialog-actions";

        confirmButton = document.createElement("button");
        confirmButton.className = "confirm-dialog-submit";
        confirmButton.type = "button";
        confirmButton.addEventListener("click", () => dialog.close("confirm"));

        const cancelButton = document.createElement("button");
        cancelButton.className = "confirm-dialog-cancel";
        cancelButton.type = "button";
        cancelButton.textContent = "Cancel";
        cancelButton.addEventListener("click", () => dialog.close("cancel"));

        content.append(titleElement, messageElement);
        actions.append(confirmButton, cancelButton);
        card.append(icon, content, actions);
        dialog.append(card);
        document.body.append(dialog);

        dialog.addEventListener("close", () => {
            if (pendingResolve) {
                pendingResolve(dialog.returnValue === "confirm");
                pendingResolve = null;
            }
        });
        dialog.addEventListener("click", (event) => {
            if (event.target === dialog) dialog.close("cancel");
        });

        return dialog;
    }

    window.showConfirmDialog = ({ title, message, confirmText = "Deactivate" }) => {
        getDialog();
        titleElement.textContent = title;
        messageElement.textContent = message;
        confirmButton.textContent = confirmText;

        return new Promise((resolve) => {
            pendingResolve = resolve;
            dialog.showModal();
            confirmButton.focus();
        });
    };
})();
