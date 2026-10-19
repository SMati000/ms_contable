(() => {
    const notice = document.getElementById("version-update-notice");
    const versionLabel = notice?.querySelector("[data-latest-version]");
    const releaseLink = notice?.querySelector("[data-release-link]");

    if (!notice || !versionLabel || !releaseLink) return;

    const checkInterval = Number(notice.dataset.intervalMs);
    if (!Number.isFinite(checkInterval) || checkInterval <= 0) return;

    let checking = false;

    const checkForUpdate = async () => {
        if (checking) return;
        checking = true;

        try {
            const response = await fetch(notice.dataset.checkUrl, {
                headers: { Accept: "application/json" },
                cache: "no-store",
                credentials: "same-origin",
            });
            if (!response.ok) return;

            const update = await response.json();
            if (!update.update_available) {
                notice.hidden = true;
                return;
            }

            versionLabel.textContent = `v${update.latest_version}`;
            releaseLink.href = update.release_url;
            notice.hidden = false;
        } catch {
            return;
        } finally {
            checking = false;
        }
    };

    checkForUpdate();
    window.setInterval(checkForUpdate, checkInterval);
})();
