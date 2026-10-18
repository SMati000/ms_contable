(() => {
    const minimumWheelDelta = 40;
    const navigationDelay = 180;
    const pageScrollCloseThreshold = 32;
    const outsideWheelCloseThreshold = 32;
    const accumulatedDelta = new WeakMap();
    const lastNavigation = new WeakMap();
    let activeCalendar = null;
    let activeCalendarLink = null;
    let positionFrame = 0;
    let lastPageScrollPosition = { left: 0, top: 0 };
    let accumulatedPageScroll = 0;
    let accumulatedOutsideWheelDelta = 0;
    let lastOutsideWheelDirection = 0;
    let outsideWheelResetTimer = null;
    const calendarResizeObserver = typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(scheduleCalendarPosition);

    function viewportBounds() {
        const viewport = window.visualViewport;
        return {
            left: viewport?.offsetLeft || 0,
            top: viewport?.offsetTop || 0,
            width: viewport?.width || window.innerWidth,
            height: viewport?.height || window.innerHeight,
        };
    }

    function positionCalendar(calendar, link) {
        if (!calendar || !link || getComputedStyle(calendar).display === "none") return;

        const viewport = viewportBounds();
        const padding = 8;
        const maxWidth = Math.max(1, viewport.width - padding * 2);
        const maxHeight = Math.max(1, viewport.height - padding * 2);

        calendar.classList.add("calendar-viewport-fitted");
        calendar.style.setProperty("position", "fixed", "important");
        calendar.style.setProperty("transform", "none", "important");
        calendar.style.setProperty("margin", "0", "important");
        calendar.style.setProperty("box-sizing", "border-box", "important");
        calendar.style.setProperty("max-width", `${maxWidth}px`, "important");
        calendar.style.setProperty("max-height", `${maxHeight}px`, "important");
        calendar.style.setProperty("overflow-x", "hidden", "important");
        calendar.style.setProperty("overflow-y", "auto", "important");
        calendar.style.setProperty("overscroll-behavior", "contain", "important");

        const anchor = link.getBoundingClientRect();
        const box = calendar.getBoundingClientRect();
        const minLeft = viewport.left + padding;
        const maxLeft = viewport.left + viewport.width - box.width - padding;
        const minTop = viewport.top + padding;
        const maxTop = viewport.top + viewport.height - box.height - padding;

        let left = anchor.right + padding;
        if (left > maxLeft) {
            const leftOfButton = anchor.left - box.width - padding;
            if (leftOfButton >= minLeft) left = leftOfButton;
        }
        left = Math.min(Math.max(left, minLeft), Math.max(minLeft, maxLeft));

        let top = anchor.top + (anchor.height - box.height) / 2;
        top = Math.min(Math.max(top, minTop), Math.max(minTop, maxTop));

        calendar.style.setProperty("left", `${left}px`, "important");
        calendar.style.setProperty("top", `${top}px`, "important");
    }

    function scheduleCalendarPosition() {
        if (!activeCalendar || !activeCalendarLink || positionFrame) return;
        positionFrame = requestAnimationFrame(() => {
            positionFrame = 0;
            positionCalendar(activeCalendar, activeCalendarLink);
        });
    }

    function closeActiveCalendar() {
        if (!activeCalendar) return;

        const calendar = activeCalendar;
        const calendarNumber = calendar.id.replace(/^calendarbox/, "");
        if (window.DateTimeShortcuts?.dismissCalendar) {
            window.DateTimeShortcuts.dismissCalendar(calendarNumber);
        } else {
            calendar.style.display = "none";
        }
        activeCalendar = null;
        activeCalendarLink = null;
        calendarResizeObserver?.disconnect();
        accumulatedDelta.delete(calendar);
        lastNavigation.delete(calendar);
        accumulatedOutsideWheelDelta = 0;
        lastOutsideWheelDirection = 0;
        window.clearTimeout(outsideWheelResetTimer);
        outsideWheelResetTimer = null;
    }

    function closeCalendarOnPageScroll(event) {
        if (!activeCalendar) return;
        if (event.target instanceof Node && activeCalendar.contains(event.target)) return;

        const scrollElement = document.scrollingElement;
        const currentPosition = {
            left: scrollElement?.scrollLeft ?? window.scrollX,
            top: scrollElement?.scrollTop ?? window.scrollY,
        };
        accumulatedPageScroll += Math.abs(currentPosition.left - lastPageScrollPosition.left)
            + Math.abs(currentPosition.top - lastPageScrollPosition.top);
        lastPageScrollPosition = currentPosition;

        if (accumulatedPageScroll >= pageScrollCloseThreshold) {
            closeActiveCalendar();
        }
    }

    function closeCalendarAfterOutsideWheel(event) {
        if (!activeCalendar) return;
        if (event.target instanceof Node && activeCalendar.contains(event.target)) return;

        const delta = normalizeDelta(event, activeCalendar);
        if (!delta) return;

        const direction = Math.sign(delta);
        if (lastOutsideWheelDirection && direction !== lastOutsideWheelDirection) {
            accumulatedOutsideWheelDelta = 0;
        }
        accumulatedOutsideWheelDelta += Math.abs(delta);
        lastOutsideWheelDirection = direction;

        window.clearTimeout(outsideWheelResetTimer);
        outsideWheelResetTimer = window.setTimeout(() => {
            accumulatedOutsideWheelDelta = 0;
            lastOutsideWheelDirection = 0;
            outsideWheelResetTimer = null;
        }, 220);

        if (accumulatedOutsideWheelDelta >= outsideWheelCloseThreshold) {
            closeActiveCalendar();
        }
    }

    document.addEventListener("click", (event) => {
        const target = event.target instanceof Element ? event.target : event.target?.parentElement;
        const link = target?.closest('a[id^="calendarlink"]');
        const calendarNumber = link?.id.match(/^calendarlink(\d+)$/)?.[1];
        if (!calendarNumber) return;

        const calendar = document.getElementById(`calendarbox${calendarNumber}`);
        if (!calendar) return;
        if (activeCalendar && activeCalendar !== calendar) closeActiveCalendar();

        activeCalendar = calendar;
        activeCalendarLink = link;
        const scrollElement = document.scrollingElement;
        lastPageScrollPosition = {
            left: scrollElement?.scrollLeft ?? window.scrollX,
            top: scrollElement?.scrollTop ?? window.scrollY,
        };
        accumulatedPageScroll = 0;
        calendarResizeObserver?.disconnect();
        calendarResizeObserver?.observe(calendar);
        scheduleCalendarPosition();
    }, { capture: true });

    window.addEventListener("resize", scheduleCalendarPosition, { passive: true });
    window.addEventListener("scroll", closeCalendarOnPageScroll, { capture: true, passive: true });
    document.addEventListener("scroll", closeCalendarOnPageScroll, { capture: true, passive: true });
    window.visualViewport?.addEventListener("scroll", closeCalendarOnPageScroll, { passive: true });
    document.addEventListener("wheel", closeCalendarAfterOutsideWheel, { capture: true, passive: true });
    window.visualViewport?.addEventListener("resize", scheduleCalendarPosition, { passive: true });

    function normalizeDelta(event, calendar) {
        if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
        if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * calendar.clientHeight;
        return event.deltaY;
    }

    document.addEventListener("wheel", (event) => {
        const target = event.target instanceof Element ? event.target : event.target?.parentElement;
        const calendar = target?.closest(".calendarbox");
        if (!calendar || getComputedStyle(calendar).display === "none") return;

        if (calendar.scrollHeight > calendar.clientHeight) {
            const canScrollPanel = event.deltaY < 0
                ? calendar.scrollTop > 0
                : calendar.scrollTop + calendar.clientHeight < calendar.scrollHeight;
            if (canScrollPanel) return;
        }

        event.preventDefault();
        const delta = normalizeDelta(event, calendar);
        if (!delta) return;

        const now = performance.now();
        const previousNavigation = lastNavigation.get(calendar);
        if (previousNavigation !== undefined && now - previousNavigation < navigationDelay) {
            accumulatedDelta.set(calendar, 0);
            return;
        }

        const nextDelta = (accumulatedDelta.get(calendar) || 0) + delta;
        if (Math.abs(nextDelta) < minimumWheelDelta) {
            accumulatedDelta.set(calendar, nextDelta);
            return;
        }

        accumulatedDelta.set(calendar, 0);
        lastNavigation.set(calendar, now);
        const direction = nextDelta > 0 ? "previous" : "next";
        calendar.querySelector(`.calendarnav-${direction}`)?.click();
    }, { capture: true, passive: false });
})();
