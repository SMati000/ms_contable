document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.id !== "login-form") return;

    event.preventDefault();
    form.setAttribute("aria-busy", "true");
    const submitButton = form.querySelector('input[type="submit"]');
    if (submitButton) submitButton.disabled = true;

    try {
        const response = await fetch(form.action, {
            method: form.method,
            body: new FormData(form),
            credentials: "same-origin",
        });

        if (response.redirected) {
            window.location.assign(response.url);
            return;
        }

        const responseDocument = new DOMParser().parseFromString(await response.text(), "text/html");
        const updatedForm = responseDocument.querySelector("#login-form");
        const updatedError = responseDocument.querySelector("#content .errornote");
        const content = document.querySelector("#content");
        const contentMain = content?.querySelector("#content-main");
        const currentForm = document.querySelector("#login-form");

        if (!updatedForm || !updatedError || !content || !contentMain || !currentForm) {
            window.location.assign(response.url);
            return;
        }

        content.querySelectorAll(".errornote").forEach((error) => error.remove());
        const errorNote = document.importNode(updatedError, true);
        errorNote.setAttribute("role", "alert");
        content.insertBefore(errorNote, contentMain);
        currentForm.replaceWith(document.importNode(updatedForm, true));
        document.title = responseDocument.title;
        errorNote.focus();
    } catch {
        const content = document.querySelector("#content");
        const contentMain = content?.querySelector("#content-main");
        if (content && contentMain) {
            const errorNote = document.createElement("p");
            errorNote.className = "errornote";
            errorNote.setAttribute("role", "alert");
            errorNote.textContent = "No se pudo conectar. Intentá de nuevo.";
            content.querySelectorAll(".errornote").forEach((error) => error.remove());
            content.insertBefore(errorNote, contentMain);
        }
    } finally {
        const currentForm = document.querySelector("#login-form");
        currentForm?.removeAttribute("aria-busy");
        const currentSubmitButton = currentForm?.querySelector('input[type="submit"]');
        if (currentSubmitButton) currentSubmitButton.disabled = false;
    }
});
