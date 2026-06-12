// =====================================================
// PDF & ZIP Tool Actions
// =====================================================

function isSelectedPdf() {
    return PF.selectedType === "pdf";
}

function isSelectedZip() {
    return PF.selectedType === "zip";
}

async function doResize() {
    if (PF.isRunning) return;
    const folder = PF.currentPath;
    if (!folder) return alert(t("alert.selectDir"));

    const scope = getSegmentedValue("resizeScope");
    if (scope === "selected" && !isSelectedPdf()) return alert(t("alert.selectPdf"));

    const data = {
        folder,
        scope,
        width: numberValue("resizeWidth"),
        height: numberValue("resizeHeight"),
        strip: boolValue("resizeStrip"),
    };

    if (scope === "selected") {
        data.file = PF.selectedPath;
    }

    await runToolAction({
        start: "开始页面缩放",
        success: "缩放完成",
        failure: "缩放失败",
        endpoint: "resize",
        payload: data,
        after: () => navigateTo(PF.currentPath),
    });
}

async function doDelete() {
    if (PF.isRunning) return;
    const folder = PF.currentPath;
    if (!folder) return alert(t("alert.selectDir"));

    const scope = getSegmentedValue("deleteScope");
    if (scope === "selected" && !isSelectedPdf()) return alert(t("alert.selectPdf"));

    const mode = getSegmentedValue("deleteMode");
    const data = { folder, scope };

    if (mode === "single") {
        const count = intValue("deleteCount");
        if (!count || count < 1) return alert(t("alert.validPage"));
        data.single = count;
        data.back = getSegmentedValue("deleteBack") === "back";
    } else if (mode === "range") {
        const count = intValue("deleteCount");
        if (!count || count < 1) return alert(t("alert.validCount"));
        data.range = count;
        data.back = getSegmentedValue("deleteBack") === "back";
    } else if (mode === "range-se") {
        const start = intValue("deleteStart");
        const end = intValue("deleteEnd");
        if (!start || !end || start < 1 || end < start) return alert(t("alert.validRange"));
        data.range_start = start;
        data.range_end = end;
    }

    if (scope === "selected") {
        data.file = PF.selectedPath;
    }

    await runToolAction({
        start: "开始页面删除",
        success: "删除完成",
        failure: "删除失败",
        endpoint: "delete",
        payload: data,
        after: () => navigateTo(PF.currentPath),
    });
}

async function doExtract() {
    if (PF.isRunning) return;
    const folder = PF.currentPath;
    if (!folder) return alert(t("alert.selectDir"));

    const scope = getSegmentedValue("extractScope");
    if (scope === "selected" && !isSelectedPdf()) return alert(t("alert.selectPdf"));

    const mode = getSegmentedValue("extractMode");
    const payload = mode === "png"
        ? { folder, scope, page: intValue("extractPage"), dpi_mode: getSegmentedValue("extractDpi") }
        : { folder, scope, start: intValue("extractStart"), end: intValue("extractEnd") };

    if (scope === "selected") {
        payload.file = PF.selectedPath;
    }

    await runToolAction({
        start: "开始页面提取",
        success: "提取完成",
        failure: "提取失败",
        endpoint: mode === "png" ? "extract-png" : "extract-pdf",
        payload,
        after: () => navigateTo(PF.currentPath),
    });
}

async function doZip2pdf() {
    if (PF.isRunning) return;
    const folder = PF.currentPath;
    if (!folder) return alert(t("alert.selectDir"));

    const scope = getSegmentedValue("zip2pdfScope");
    if (scope === "selected" && !isSelectedZip()) return alert(t("alert.selectZip"));

    const data = {
        folder,
        scope,
        dpi_mode: getSegmentedValue("zipDpi"),
    };

    if (scope === "selected") {
        data.file = PF.selectedPath;
    }

    await runToolAction({
        start: "开始 ZIP 转 PDF",
        success: "转换完成",
        failure: "转换失败",
        endpoint: "zip2pdf",
        payload: data,
        after: () => navigateTo(PF.currentPath),
    });
}

async function doCleanType(cleanType) {
    if (PF.isRunning) return;
    const folder = PF.currentPath;
    if (!folder) return alert(t("alert.selectDir"));
    if (!cleanType) return;
    if (!confirm(t("alert.confirmClean"))) return;

    await runToolAction({
        start: "开始清理",
        success: "清理完成",
        failure: "清理失败",
        endpoint: "clean",
        payload: { folder, type: cleanType },
        after: () => navigateTo(PF.currentPath),
    });
}
