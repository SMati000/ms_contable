function showHelpDialog(dialog) {
    if (dialog.open || typeof dialog.showModal !== "function") {
        return;
    }

    dialog.showModal();
}

function containDialogScrollEvents(event) {
    const dialog = document.querySelector("dialog.help-dialog[open]");
    if (!dialog) {
        return;
    }

    const content = dialog.querySelector(".help-dialog__content");
    const target = event.target instanceof Element ? event.target : null;

    if (!content?.contains(target)) {
        event.preventDefault();
    }

    event.stopPropagation();
}

document.addEventListener("wheel", containDialogScrollEvents, {
    capture: true,
    passive: false,
});
document.addEventListener("touchmove", containDialogScrollEvents, {
    capture: true,
    passive: false,
});
document.addEventListener("keydown", function (event) {
    const dialog = document.querySelector("dialog.help-dialog[open]");
    const pageScrollKeys = ["ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp"];

    if (dialog && pageScrollKeys.includes(event.key)) {
        const content = dialog.querySelector(".help-dialog__content");
        if (!content?.contains(event.target)) {
            event.preventDefault();
        }
    }
}, true);

document.addEventListener("click", function (event) {
    if (!(event.target instanceof Element)) {
        return;
    }

    const trigger = event.target.closest("[data-help-target]");
    if (trigger) {
        const dialog = document.getElementById(trigger.dataset.helpTarget);
        if (dialog) {
            showHelpDialog(dialog);
        }
        return;
    }

    const closeButton = event.target.closest("[data-help-close]");
    if (closeButton) {
        closeButton.closest("dialog")?.close();
        return;
    }

    const dialog = event.target.closest("dialog.help-dialog");
    if (dialog && event.target === dialog) {
        const bounds = dialog.getBoundingClientRect();
        const clickedOutside =
            event.clientX < bounds.left ||
            event.clientX > bounds.right ||
            event.clientY < bounds.top ||
            event.clientY > bounds.bottom;

        if (clickedOutside) {
            dialog.close();
        }
    }
});
