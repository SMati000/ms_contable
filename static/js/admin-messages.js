(() => {
    const messages = document.querySelectorAll(".messagelist > li:not(.error)");

    for (const message of messages) {
        window.setTimeout(() => {
            message.classList.add("message-dismissed");
            window.setTimeout(() => message.remove(), 250);
        }, 5000);
    }
})();
