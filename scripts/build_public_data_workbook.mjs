import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicDir = path.join(root, "data", "public");
const qaDir = path.join(root, "tmp", "public_data_workbook_qa");

const csvSheets = [
  ["world_bank_fao_china_fisheries_2014_2023.csv", "World Bank FAO"],
  ["moa_national_fishery_statistics.csv", "MOA Annual"],
  ["moa_2024_detailed_fishery_statistics.csv", "MOA 2024 Detail"],
  ["moa_fishery_environment_2024.csv", "Environment 2024"],
  ["official_latest_aquatic_products_2025.csv", "Latest Official"],
  ["source_catalog.csv", "Source Catalog"],
];

const [firstCsv, firstSheetName] = csvSheets[0];
const workbook = await Workbook.fromCSV(
  await fs.readFile(path.join(publicDir, firstCsv), "utf8"),
  { sheetName: firstSheetName },
);
for (const [filename, sheetName] of csvSheets.slice(1)) {
  await workbook.fromCSV(await fs.readFile(path.join(publicDir, filename), "utf8"), { sheetName });
}

function typeNumericColumns(sheetName, numericHeaders) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange();
  const values = used.values;
  const headers = values[0].map((value) => String(value));
  for (const header of numericHeaders) {
    const columnIndex = headers.indexOf(header);
    if (columnIndex < 0) {
      throw new Error(`Numeric field ${header} not found on ${sheetName}`);
    }
    const typed = values.slice(1).map((row) => {
      const value = row[columnIndex];
      return [value === "" || value === null ? null : Number(value)];
    });
    sheet.getRangeByIndexes(1, columnIndex, typed.length, 1).values = typed;
  }
}

typeNumericColumns("World Bank FAO", ["year", "value"]);
typeNumericColumns("MOA Annual", ["year", "value"]);
typeNumericColumns("MOA 2024 Detail", [
  "year",
  "reported_value",
  "normalization_multiplier",
  "value",
  "yoy_pct",
  "share_pct",
]);
typeNumericColumns("Environment 2024", [
  "year",
  "comparison_year",
  "reported_value",
  "normalization_multiplier",
  "value",
]);
typeNumericColumns("Latest Official", [
  "year",
  "reported_value",
  "normalization_multiplier",
  "value",
  "yoy_pct",
]);

const notes = workbook.worksheets.add("Notes");
notes.getRange("A1:B14").values = [
  ["Public fishery data package", "Review workbook for the GitHub reproduction repository"],
  ["Retrieved", "2026-07-23"],
  ["Data label", "经过处理的数据（公开来源） / processed data from public sources"],
  ["World Bank / FAO", "Three China national production indicators, 2014-2023, CC BY 4.0"],
  ["Ministry annual data", "Accessible official HTML communiqués for 2015, 2016 and 2019-2024"],
  ["MOA 2024 detail", "99 records: economy, species/water-body production, area, fleet, population, processing, trade and disasters"],
  ["Fishery environment", "12 records: monitoring network and reported exceedance-area change magnitudes"],
  ["Latest official", "2025 national total/aquaculture/capture and Zhejiang total/marine/freshwater production"],
  ["Reported vs normalized", "Reported value/unit are retained; normalized value = reported value × normalization multiplier"],
  ["Source integrity", "Detailed rows contain the SHA-256 of the official HTML used by the parser"],
  ["Province-level data", "NBS indicator A0407 is documented, but its automated endpoint returned HTTP 403"],
  ["Important", "World Bank/FAO, Ministry and NBS totals can use different definitions; do not merge without checking scope"],
  ["Missing values", "not_found means the field was not located in that official HTML page; no interpolation"],
  ["Repository", "https://github.com/niqundaye/Frontiers-in-Marine-Science"],
];

const dictionary = workbook.worksheets.add("Field Dictionary");
dictionary.getRange("A1:D19").values = [
  ["Field", "Applies to", "Meaning", "Audit rule"],
  ["year", "all data sheets", "Reference year of the statistic", "Integer year"],
  ["section", "MOA 2024 Detail", "Communique topic group", "Machine-readable text"],
  ["indicator", "detailed/latest sheets", "Stable machine-readable indicator name", "Do not translate in code"],
  ["indicator_zh", "detailed/latest sheets", "Chinese label matching the official source concept", "Human-readable"],
  ["category", "MOA 2024 Detail", "Total/marine/freshwater or operational subgroup", "Controls valid aggregation"],
  ["reported_value", "detailed/latest sheets", "Numeric value as displayed on the official page", "Never overwrite"],
  ["reported_unit", "detailed/latest sheets", "Unit as displayed on the official page", "Never overwrite"],
  ["normalization_multiplier", "detailed/latest sheets", "Exact multiplier used for unit conversion", "value = reported_value × multiplier"],
  ["value", "all data sheets", "Machine-readable normalized numeric value", "Typed number"],
  ["unit", "all data sheets", "Normalized unit", "One unit per row"],
  ["yoy_pct", "MOA detail/latest", "Signed year-on-year percent; declines are negative", "Blank if source does not report"],
  ["share_pct", "MOA 2024 Detail", "Share reported in source table", "Blank unless explicitly reported"],
  ["comparison_year", "Environment 2024", "Baseline year for a change indicator", "Do not treat changes as levels"],
  ["change_direction", "Environment 2024", "level/increase/decrease classification", "Interpret with comparison_year"],
  ["category_basis", "Latest Official", "Production method or water-body basis", "Do not combine unlike bases"],
  ["source_url", "all data sheets", "Official page or API URL", "Plain-text auditable URL"],
  ["source_sha256", "detailed/latest sheets", "SHA-256 of downloaded official HTML", "64 lowercase hexadecimal characters"],
  ["data_label", "detailed/latest sheets", "经过处理的数据（公开来源）", "Never call author raw data"],
];

function findRow(sheetName, criteria) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const matrix = sheet.getUsedRange().values;
  const headers = matrix[0].map((value) => String(value));
  const rowIndex = matrix.findIndex((row, index) => {
    if (index === 0) return false;
    return Object.entries(criteria).every(([key, value]) => String(row[headers.indexOf(key)]) === value);
  });
  if (rowIndex < 1) {
    throw new Error(`QC lookup failed on ${sheetName}: ${JSON.stringify(criteria)}`);
  }
  return rowIndex + 1;
}

function valueCell(sheetName, criteria, valueColumn = "value") {
  const sheet = workbook.worksheets.getItem(sheetName);
  const headers = sheet.getUsedRange().values[0].map((value) => String(value));
  const columnIndex = headers.indexOf(valueColumn);
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  if (columnIndex < 0 || columnIndex >= letters.length) {
    throw new Error(`QC value column failed on ${sheetName}: ${valueColumn}`);
  }
  return `'${sheetName}'!${letters[columnIndex]}${findRow(sheetName, criteria)}`;
}

const qc = workbook.worksheets.add("QC Checks");
qc.getRange("A1:E10").values = [
  ["Check", "Relationship", "Difference", "Tolerance", "Status"],
  ["MOA detailed row count", "99 parsed records", null, 0, null],
  ["2024 economic output", "total - fishery - industry/construction - circulation/services", null, 0.000001, null],
  ["2024 aquatic production", "total - aquaculture - capture", null, 0.000001, null],
  ["2024 capture composition", "capture - domestic capture - distant-water capture", null, 0.000001, null],
  ["2024 water-body composition", "total - marine - freshwater", null, 0.000001, null],
  ["Motorized fleet tonnage", "motorized - production - auxiliary (rounding allowed)", null, 100, null],
  ["Processed products", "total - marine - freshwater (rounding allowed)", null, 100, null],
  ["2025 China production", "total - aquaculture - capture", null, 0.000001, null],
  ["2025 Zhejiang production", "total - marine - freshwater", null, 0.000001, null],
];

const moaValue = (indicator, category = "total") =>
  valueCell("MOA 2024 Detail", { indicator, category });
const latestValue = (geographyCode, indicator) =>
  valueCell("Latest Official", { geography_code: geographyCode, indicator });

qc.getRange("C2:C10").formulas = [
  ["=COUNTA('MOA 2024 Detail'!A2:A100)-99"],
  [`=${moaValue("total_fishery_economic_output")}-${moaValue("fishery_output")}-${moaValue("fishery_industry_construction_output")}-${moaValue("fishery_circulation_services_output")}`],
  [`=${moaValue("total_aquatic_products")}-${moaValue("aquaculture_production")}-${moaValue("capture_production")}`],
  [`=${moaValue("capture_production")}-${moaValue("domestic_capture_production")}-${moaValue("distant_water_capture", "distant_water")}`],
  [`=${moaValue("total_aquatic_products")}-${moaValue("marine_products", "marine")}-${moaValue("freshwater_products", "freshwater")}`],
  [`=${moaValue("vessel_tonnage", "motorized")}-${moaValue("vessel_tonnage", "production")}-${moaValue("vessel_tonnage", "auxiliary")}`],
  [`=${moaValue("processed_products")}-${moaValue("processed_products", "marine")}-${moaValue("processed_products", "freshwater")}`],
  [`=${latestValue("CHN", "total_aquatic_products")}-${latestValue("CHN", "aquaculture_production")}-${latestValue("CHN", "capture_production")}`],
  [`=${latestValue("CN-ZJ", "total_aquatic_products")}-${latestValue("CN-ZJ", "marine_products")}-${latestValue("CN-ZJ", "freshwater_products")}`],
];
qc.getRange("E2").formulas = [["=IF(ABS(C2)<=D2,\"PASS\",\"FAIL\")"]];
qc.getRange("E2:E10").fillDown();

const styles = {
  "World Bank FAO": [12, 14, 10, 18, 34, 16, 16, 34, 58, 18, 14, 14, 44],
  "MOA Annual": [10, 30, 16, 18, 38, 58, 14, 16, 42],
  "MOA 2024 Detail": [9, 28, 34, 24, 16, 16, 14, 18, 18, 18, 12, 12, 42, 62, 66, 14, 30, 46],
  "Environment 2024": [9, 14, 44, 28, 16, 14, 18, 18, 42, 18, 52, 62, 66, 14, 30, 46],
  "Latest Official": [9, 16, 18, 30, 24, 16, 14, 18, 18, 16, 12, 20, 46, 62, 66, 14, 30, 46],
  "Source Catalog": [25, 30, 40, 38, 62, 42, 38, 48, 15, 70],
  "Field Dictionary": [28, 24, 62, 52],
  "QC Checks": [28, 72, 18, 16, 14],
  Notes: [25, 96],
};

for (const [sheetName, widths] of Object.entries(styles)) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange();
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  used.format.font = { name: "Aptos", size: 10, color: "#172033" };
  used.format.verticalAlignment = "center";
  used.format.wrapText = ["Source Catalog", "Field Dictionary", "QC Checks", "Notes"].includes(sheetName);
  const header = used.getRow(0);
  header.format.wrapText = true;
  header.format.fill = "#0F766E";
  header.format.font = { name: "Aptos Display", size: 10, bold: true, color: "#FFFFFF" };
  header.format.rowHeight = 34;
  if (used.rowCount > 1) {
    used.offset(1, 0).resize(used.rowCount - 1, used.columnCount).format.rowHeight =
      ["Source Catalog", "Field Dictionary", "QC Checks", "Notes"].includes(sheetName) ? 42 : 26;
  }
  widths.forEach((width, index) => {
    if (index < used.columnCount) used.getColumn(index).format.columnWidth = width;
  });
}

workbook.worksheets.getItem("World Bank FAO").getRange("C2:C31").format.numberFormat = "0";
workbook.worksheets.getItem("World Bank FAO").getRange("F2:F31").format.numberFormat = "#,##0.000";
workbook.worksheets.getItem("MOA Annual").getRange("A2:A81").format.numberFormat = "0";
workbook.worksheets.getItem("MOA Annual").getRange("C2:C81").format.numberFormat = "#,##0.00";
workbook.worksheets.getItem("MOA 2024 Detail").getRange("F2:L100").format.numberFormat = "#,##0.00";
workbook.worksheets.getItem("Environment 2024").getRange("E2:I13").format.numberFormat = "#,##0.00";
workbook.worksheets.getItem("Latest Official").getRange("F2:K7").format.numberFormat = "#,##0.00";
qc.getRange("C2:D10").format.numberFormat = "#,##0.000000";
qc.getRange("E2:E10").conditionalFormats.add("containsText", {
  text: "PASS",
  format: { fill: "#DCFCE7", font: { bold: true, color: "#166534" } },
});
qc.getRange("E2:E10").conditionalFormats.add("containsText", {
  text: "FAIL",
  format: { fill: "#FEE2E2", font: { bold: true, color: "#991B1B" } },
});

notes.getRange("A1:B1").format.fill = "#164E63";
notes.getRange("A1:B1").format.font = { name: "Aptos Display", size: 12, bold: true, color: "#FFFFFF" };
notes.getRange("A1:B1").format.rowHeight = 38;
notes.getRange("A12:B12").format.fill = "#FEF3C7";
notes.getRange("A12:B12").format.font = { name: "Aptos", size: 10, bold: true, color: "#92400E" };

await fs.mkdir(qaDir, { recursive: true });
for (const sheetName of Object.keys(styles)) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(
    path.join(qaDir, `${sheetName.replaceAll(" ", "_")}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const check = await workbook.inspect({
  kind: "table",
  range: "QC Checks!A1:E10",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 5,
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
