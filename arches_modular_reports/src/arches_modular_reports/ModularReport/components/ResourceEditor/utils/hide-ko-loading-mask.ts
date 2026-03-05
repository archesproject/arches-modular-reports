export function hideKoLoadingMask() {
    setTimeout(() => {
        // Arches's page-view.js registers its own beforeunload handler
        // that calls viewModel.loading(true) on every navigation. When
        // navigation is cancelled, loading() is never reset. Reset it
        // via the Knockout viewModel directly if ko is available as a
        // global; fall back to a CSS override if not.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const ko = (window as any).ko;
        if (ko) {
            const vm = ko.dataFor(document.body);
            if (vm && typeof vm.loading === "function") {
                vm.loading(false);
                return;
            }
        }
        const loadingMask =
            document.querySelector<HTMLElement>(".loading-mask");
        if (loadingMask) {
            loadingMask.style.visibility = "hidden";
        }
    }, 0);
}
