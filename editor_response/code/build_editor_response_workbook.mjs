import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const packageRoot = path.join(root, "editor_response");
const payload = JSON.parse(await fs.readFile(path.join(packageRoot, "workbook_payload.json"), "utf8"));
const qaDir = path.join(root, "tmp", "editor_response_workbook_qa");
await fs.mkdir(qaDir, { recursive: true });

const workbook = Workbook.create();
const navy = "#17365D";
const blue = "#D9EAF7";
const pale = "#F3F6F9";
const amber = "#FFF2CC";
const red = "#FCE8E6";
const green = "#E2F0D9";

function matrixFromRecords(records) {
  if (!records.length) return { headers: ["No records"], values: [["No records"]] };
  const headers = Object.keys(records[0]);
  return { headers, values: records.map((record) => headers.map((header) => record[header] ?? null)) };
}

function applyBase(sheet) {
  sheet.showGridLines = false;
  sheet.getUsedRange().format.font = { name: "Aptos", size: 10, color: "#202124" };
}

function addDataSheet(name, records, options = {}) {
  const sheet = workbook.worksheets.add(name);
  const { headers, values } = matrixFromRecords(records);
  const all = [headers, ...values];
  const range = sheet.getRangeByIndexes(0, 0, all.length, headers.length);
  range.values = all;
  applyBase(sheet);
  sheet.getRangeByIndexes(0, 0, 1, headers.length).format = {
    fill: navy,
    font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  range.format.borders = { preset: "insideHorizontal", style: "thin", color: "#D9E1E8" };
  range.format.autofitColumns();
  range.format.autofitRows();
  sheet.freezePanes.freezeRows(1);
  if (options.freezeColumns) sheet.freezePanes.freezeColumns(options.freezeColumns);
  if (all.length > 1 && headers.length > 1) {
    const table = sheet.tables.add(range, true, `${name.replace(/[^A-Za-z0-9]/g, "")}Table`);
    table.style = "TableStyleMedium2";
    table.showBandedRows = true;
  }
  for (const [columnIndex, width] of Object.entries(options.widths ?? {})) {
    sheet.getRangeByIndexes(0, Number(columnIndex), all.length, 1).format.columnWidth = width;
  }
  sheet.getRangeByIndexes(0, 0, 1, headers.length).format.rowHeight = 42;
  for (const columnIndex of options.wrapColumns ?? []) {
    const column = sheet.getRangeByIndexes(1, columnIndex, Math.max(values.length, 1), 1);
    column.format.wrapText = true;
    column.format.autofitRows();
  }
  if (options.dataRowHeight && values.length) {
    sheet.getRangeByIndexes(1, 0, values.length, headers.length).format.rowHeight = options.dataRowHeight;
  }
  for (const columnIndex of options.percentColumns ?? []) {
    sheet.getRangeByIndexes(1, columnIndex, Math.max(values.length, 1), 1).format.numberFormat = "0.0000";
  }
  for (const columnIndex of options.integerColumns ?? []) {
    sheet.getRangeByIndexes(1, columnIndex, Math.max(values.length, 1), 1).format.numberFormat = "#,##0";
  }
  return sheet;
}

const readme = workbook.worksheets.add("README");
readme.showGridLines = false;
readme.getRange("A1:F1").merge();
readme.getRange("A1").values = [["31-Province Input Matrix: Evidence and Reconstruction Workbook"]];
readme.getRange("A1:F1").format = { fill: navy, font: { name: "Aptos Display", size: 18, bold: true, color: "#FFFFFF" }, rowHeight: 34, verticalAlignment: "center" };
readme.getRange("A3:F5").merge();
readme.getRange("A3").values = [["ESSENTIAL DISCLOSURE\nThis workbook is a calibrated, deterministic replacement constructed from the public surrogate model and retained article/public data. It is not the original 31-province workbook used for the reported results. The historical matrix, original row order, EWM inputs/weights, province TACs and original preprocessing files were not present in the retained archive."]];
readme.getRange("A3:F5").format = { fill: amber, font: { name: "Aptos", size: 11, bold: true, color: "#7F6000" }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "medium", color: "#BF9000" } };
readme.getRange("A7:B14").values = [
  ["Field", "Value"],
  ["Prepared on", payload.metadata.prepared_on],
  ["Paper DOI", payload.metadata.paper_doi],
  ["Data status", payload.metadata.package_disclosure],
  ["Province mapping", "NBS standard 31-province order assigned for reconstruction; original r-index order unavailable"],
  ["Decision dimensions", "31 regions x 4 sectors x 2 modes = 248 variables"],
  ["NBS A0407 retrieval", payload.metadata.nbs_a0407_check],
  ["Primary code", "src/fishery_repro/model.py and scripts/build_editor_response_data.py"],
];
readme.getRange("A7:B7").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } };
readme.getRange("A7:B14").format.borders = { preset: "all", style: "thin", color: "#D9E1E8" };
readme.getRange("A7:A14").format.font = { bold: true };
readme.getRange("A7:B14").format.wrapText = true;
readme.getRange("A16:F16").merge();
readme.getRange("A16").values = [["Interpretation: yellow = essential limitation; blue headers = structured tables; every proxy column and row is labelled so that it cannot be confused with a historical original."]];
readme.getRange("A16:F16").format = { fill: pale, font: { italic: true, color: "#44546A" }, wrapText: true };
readme.getRange("A1:F20").format.font.name = "Aptos";
readme.getRange("A1:A20").format.columnWidth = 28;
readme.getRange("B1:F20").format.columnWidth = 24;

addDataSheet("Province Inputs", payload.province_inputs, {
  freezeColumns: 4,
  widths: { 0: 10, 1: 12, 2: 18, 3: 12, 4: 15, 5: 15, 6: 18, 7: 18, 8: 18, 9: 44, 10: 34 },
  wrapColumns: [9, 10],
  dataRowHeight: 30,
  percentColumns: [4, 5],
  integerColumns: [6, 7, 8],
});
addDataSheet("Coefficient Matrix", payload.coefficient_matrix_248_rows, {
  freezeColumns: 4,
  widths: { 0: 18, 1: 10, 2: 12, 3: 18, 4: 12, 6: 18, 8: 10, 9: 18, 11: 18, 22: 36 },
  wrapColumns: [22],
  dataRowHeight: 28,
  percentColumns: [12, 13, 17, 18, 19, 20, 21],
  integerColumns: [11, 14, 15, 16],
});
addDataSheet("Sector-Mode Coeff", payload.sector_mode_coefficients, {
  widths: { 0: 10, 1: 20, 2: 14, 3: 10, 4: 18, 5: 12, 6: 17, 7: 20, 8: 20, 9: 17, 10: 17, 11: 34 },
  wrapColumns: [11],
  dataRowHeight: 28,
  percentColumns: [6, 7, 8, 9, 10],
});
addDataSheet("National Constraints", payload.national_constraints, {
  widths: { 0: 22, 1: 18, 2: 18, 3: 30, 4: 34, 5: 34 },
  wrapColumns: [3, 4, 5],
  dataRowHeight: 34,
});
addDataSheet("Variable Dictionary", payload.variable_dictionary, {
  widths: { 0: 28, 1: 50, 2: 20, 3: 18, 4: 55 },
  wrapColumns: [1, 4],
  dataRowHeight: 34,
});
addDataSheet("Availability", payload.availability, {
  widths: { 0: 12, 1: 52, 2: 28, 3: 62, 4: 48, 5: 18 },
  wrapColumns: [1, 3, 4],
  dataRowHeight: 42,
});
addDataSheet("Source Map", payload.source_map, {
  widths: { 0: 25, 1: 32, 2: 38, 3: 36, 4: 62, 5: 42, 6: 30, 7: 48, 8: 16, 9: 55 },
  wrapColumns: [2, 3, 5, 6, 7, 9],
  dataRowHeight: 46,
});

const qc = workbook.worksheets.add("QC");
qc.showGridLines = false;
qc.getRange("A1:D1").merge();
qc.getRange("A1").values = [["Workbook integrity and disclosure checks"]];
qc.getRange("A1:D1").format = { fill: navy, font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
qc.getRange("A3:D3").values = [["Check", "Expected", "Actual", "Result"]];
qc.getRange("A4:B9").values = [
  ["Province rows", 31],
  ["Decision/coefficient rows", 248],
  ["Sector-mode rows", 8],
  ["Region shares sum", 1],
  ["All matrix rows labelled non-original", 248],
  ["Unavailable items allowed to be described as original", 0],
];
qc.getRange("C4:C9").formulas = [
  ["=COUNTA('Province Inputs'!$A$2:$A$32)"],
  ["=COUNTA('Coefficient Matrix'!$A$2:$A$249)"],
  ["=COUNTA('Sector-Mode Coeff'!$A$2:$A$9)"],
  ["=SUM('Province Inputs'!$E$2:$E$32)"],
  ["=COUNTIF('Coefficient Matrix'!$W$2:$W$249,\"calibrated reconstruction; not historical author input\")"],
  ["=COUNTIF('Availability'!$F$2:$F$200,\"yes\")"],
];
qc.getRange("D4:D9").formulas = [
  ["=IF(ABS(B4-C4)<0.0000001,\"PASS\",\"FAIL\")"],
  ["=IF(ABS(B5-C5)<0.0000001,\"PASS\",\"FAIL\")"],
  ["=IF(ABS(B6-C6)<0.0000001,\"PASS\",\"FAIL\")"],
  ["=IF(ABS(B7-C7)<0.0000001,\"PASS\",\"FAIL\")"],
  ["=IF(ABS(B8-C8)<0.0000001,\"PASS\",\"FAIL\")"],
  ["=IF(ABS(B9-C9)<0.0000001,\"PASS\",\"FAIL\")"],
];
qc.getRange("A3:D3").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } };
qc.getRange("A3:D9").format.borders = { preset: "all", style: "thin", color: "#D9E1E8" };
qc.getRange("A3:D9").format.wrapText = true;
qc.getRange("A1:A12").format.columnWidth = 45;
qc.getRange("B1:C12").format.columnWidth = 18;
qc.getRange("D1:D12").format.columnWidth = 14;
qc.getRange("C7").format.numberFormat = "0.000000";
qc.getRange("D4:D9").conditionalFormats.add("containsText", { text: "PASS", format: { fill: green, font: { bold: true, color: "#375623" } } });
qc.getRange("D4:D9").conditionalFormats.add("containsText", { text: "FAIL", format: { fill: red, font: { bold: true, color: "#9C0006" } } });

const inspection = await workbook.inspect({ kind: "sheet,formula", maxChars: 6000, tableMaxRows: 8, tableMaxCols: 8 });
console.log(inspection.ndjson);
const qcInspection = await workbook.inspect({ kind: "table", range: "QC!A1:D9", include: "values,formulas", tableMaxRows: 12, tableMaxCols: 6, maxChars: 5000 });
console.log(qcInspection.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 200 }, summary: "final formula error scan" });
console.log(errors.ndjson);

const previews = [
  ["README", "A1:F18"],
  ["Province Inputs", "A1:K18"],
  ["Coefficient Matrix", "A1:W18"],
  ["Sector-Mode Coeff", "A1:L9"],
  ["National Constraints", "A1:F11"],
  ["Variable Dictionary", "A1:E12"],
  ["Availability", "A1:F12"],
  ["Source Map", "A1:J12"],
  ["QC", "A1:D10"],
];
if (process.argv.includes("--render-qa")) {
  for (const [sheetName, range] of previews) {
    const preview = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
    await fs.writeFile(path.join(qaDir, `${sheetName.replace(/[^A-Za-z0-9]/g, "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(packageRoot, "03_Reconstructed_31_Province_Inputs.xlsx"));
console.log(JSON.stringify({ output: path.join(packageRoot, "03_Reconstructed_31_Province_Inputs.xlsx"), qaDir, sheets: previews.length }));
process.exit(0);
