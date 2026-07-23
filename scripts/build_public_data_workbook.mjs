import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicDir = path.join(root, "data", "public");
const qaDir = path.join(root, "tmp", "public_data_workbook_qa");

const worldBankCsv = await fs.readFile(path.join(publicDir, "world_bank_fao_china_fisheries_2014_2023.csv"), "utf8");
const moaCsv = await fs.readFile(path.join(publicDir, "moa_national_fishery_statistics.csv"), "utf8");
const catalogCsv = await fs.readFile(path.join(publicDir, "source_catalog.csv"), "utf8");

const workbook = await Workbook.fromCSV(worldBankCsv, { sheetName: "World Bank FAO" });
await workbook.fromCSV(moaCsv, { sheetName: "MOA Annual" });
await workbook.fromCSV(catalogCsv, { sheetName: "Source Catalog" });

const worldBankSheet = workbook.worksheets.getItem("World Bank FAO");
worldBankSheet.getRange("C2:C31").values = worldBankSheet.getRange("C2:C31").values.map(([value]) => [Number(value)]);
worldBankSheet.getRange("F2:F31").values = worldBankSheet.getRange("F2:F31").values.map(([value]) => [Number(value)]);
worldBankSheet.getRange("C2:C31").format.numberFormat = "0";
worldBankSheet.getRange("F2:F31").format.numberFormat = "#,##0.000";

const moaSheet = workbook.worksheets.getItem("MOA Annual");
moaSheet.getRange("A2:A71").values = moaSheet.getRange("A2:A71").values.map(([value]) => [Number(value)]);
moaSheet.getRange("C2:C71").values = moaSheet.getRange("C2:C71").values.map(([value]) => [value === "" ? null : Number(value)]);
moaSheet.getRange("A2:A71").format.numberFormat = "0";
moaSheet.getRange("C2:C71").format.numberFormat = "#,##0.00";
const notes = workbook.worksheets.add("Notes");
notes.getRange("A1:B9").values = [
  ["Public fishery data package", "Review workbook for the GitHub reproduction repository"],
  ["Retrieved", "2026-07-23"],
  ["World Bank / FAO", "Three China national production indicators, 2014-2023, CC BY 4.0"],
  ["Ministry annual data", "Accessible official HTML communiqués for 2015, 2016 and 2019-2023"],
  ["Province-level data", "NBS indicator A0407 documented, but the automated endpoint returned HTTP 403"],
  ["Important", "World Bank/FAO and Ministry totals have different definitions; do not merge them as one series"],
  ["Missing values", "not_found means the field was not located in that official HTML page; no interpolation"],
  ["Article reconstruction", "Figures 2-10 remain calibrated reconstructions, not author run logs"],
  ["Repository", "https://github.com/niqundaye/Frontiers-in-Marine-Science"],
];

const sheetConfigs = [
  ["World Bank FAO", "A1:M31", [12, 14, 10, 18, 34, 16, 16, 34, 58, 18, 14, 14, 44], 40, false],
  ["MOA Annual", "A1:I71", [10, 30, 16, 18, 38, 58, 14, 16, 42], 40, false],
  ["Source Catalog", "A1:I13", [25, 30, 36, 28, 62, 38, 34, 48, 15], 46, true],
  ["Notes", "A1:B9", [24, 90], 34, true],
];

for (const [sheetName, rangeAddress, widths, bodyHeight, wrapBody] of sheetConfigs) {
  const sheet = workbook.worksheets.getItem(sheetName);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const used = sheet.getRange(rangeAddress);
  used.format.font = { name: "Aptos", size: 10, color: "#172033" };
  used.format.wrapText = wrapBody;
  used.format.verticalAlignment = "center";
  const header = used.getRow(0);
  header.format.wrapText = true;
  header.format.fill = "#0F766E";
  header.format.font = { name: "Aptos Display", size: 10, bold: true, color: "#FFFFFF" };
  header.format.rowHeight = 30;
  used.offset(1, 0).resize(used.rowCount - 1, used.columnCount).format.rowHeight = bodyHeight;
  widths.forEach((width, index) => {
    used.getColumn(index).format.columnWidth = width;
  });
}

worldBankSheet.getRange("H2:I31").format.wrapText = true;
worldBankSheet.getRange("M2:M31").format.wrapText = true;
moaSheet.getRange("E2:F71").format.wrapText = true;
moaSheet.getRange("I2:I71").format.wrapText = true;

notes.getRange("A1:B1").format.fill = "#164E63";
notes.getRange("A1:B1").format.font = { name: "Aptos Display", size: 12, bold: true, color: "#FFFFFF" };
notes.getRange("A1:B1").format.rowHeight = 38;
notes.getRange("A6:B6").format.fill = "#FEF3C7";
notes.getRange("A6:B6").format.font = { name: "Aptos", size: 10, bold: true, color: "#92400E" };
notes.getRange("A6:B6").format.rowHeight = 44;

await fs.mkdir(qaDir, { recursive: true });
for (const [sheetName] of sheetConfigs) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(qaDir, `${sheetName.replaceAll(" ", "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const check = await workbook.inspect({
  kind: "table",
  range: "World Bank FAO!A1:M8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 13,
});
console.log(check.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(publicDir, "public_data_catalog.xlsx");
await output.save(outputPath);
console.log(outputPath);
process.exitCode = 0;
