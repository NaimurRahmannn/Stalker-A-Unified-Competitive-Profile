/** Convert an API instant into the browser's local wall-clock input value. */
export function toLocalDateTimeInput(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/** Convert an explicitly edited local wall-clock value back to an API instant. */
export function fromLocalDateTimeInput(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new Error("Enter a valid submission date and time.");
  return date.toISOString();
}
