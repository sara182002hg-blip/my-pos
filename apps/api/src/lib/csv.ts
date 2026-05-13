type CsvCell = string | number | boolean | null | undefined;
type CsvRow = Record<string, CsvCell>;

function escapeCell(value: CsvCell) {
  if (value === null || value === undefined) {
    return "";
  }

  const stringValue = String(value);

  if (/[",\r\n]/.test(stringValue)) {
    return `"${stringValue.replace(/"/g, "\"\"")}"`;
  }

  return stringValue;
}

export function toCsv(rows: CsvRow[]) {
  if (!rows.length) {
    return "";
  }

  const headers = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const lines = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => escapeCell(row[header])).join(","))
  ];

  return lines.join("\n");
}

export function asDownloadFilename(prefix: string) {
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  return `${prefix}-${stamp}.csv`;
}
