(() => {
    const errorMessages = document.querySelectorAll(".messagelist > li.error");
    const errorDialog = document.getElementById("admin-error-dialog");
    const errorDetails = errorDialog?.querySelector("[data-error-details]");

    if (errorMessages.length && errorDialog && errorDetails && typeof errorDialog.showModal === "function") {
        for (const message of errorMessages) {
            const text = message.innerText.trim();
            if (text) {
                for (const detail of text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)) {
                    const item = document.createElement("li");
                    item.textContent = detail;
                    errorDetails.append(item);
                }
            }
            message.remove();
        }

        errorDialog.showModal();
    }

    const messages = document.querySelectorAll(".messagelist > li:not(.error)");

    for (const message of messages) {
        window.setTimeout(() => {
            message.classList.add("message-dismissed");
            window.setTimeout(() => message.remove(), 250);
        }, 5000);
    }
})();
