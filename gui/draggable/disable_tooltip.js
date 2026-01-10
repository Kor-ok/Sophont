(() => {
    try {
        const el = getHtmlElement({self.id});
        if (el) {
            el.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, cancelable: true }));
            el.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, cancelable: true }));
        }

        // Safety net: ensure any currently-visible Quasar tooltips are hidden.
        // This avoids stale tooltips lingering when a drag starts mid-hover.
        document.querySelectorAll('.q-tooltip').forEach((tip) => {
            try {
                tip.style.display = 'none';
            } catch (_) {
                // ignore
            }
        });
    } catch (_) {
        // ignore
    }
})();