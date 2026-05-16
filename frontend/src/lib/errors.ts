import axios from "axios";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatFieldName(field: string): string {
  return field
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function valueToMessage(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map(valueToMessage).filter(Boolean).join(" ") || null;
  }

  if (isRecord(value)) {
    for (const [field, fieldValue] of Object.entries(value)) {
      const message = valueToMessage(fieldValue);

      if (message) {
        return `${formatFieldName(field)}: ${message}`;
      }
    }
  }

  return null;
}

function responseDataToMessage(data: unknown): string | null {
  if (typeof data === "string") {
    return data;
  }

  if (!isRecord(data)) {
    return null;
  }

  for (const key of ["detail", "message", "error", "non_field_errors"]) {
    const message = valueToMessage(data[key]);

    if (message) {
      return message;
    }
  }

  const nestedErrors = valueToMessage(data.errors);

  if (nestedErrors) {
    return nestedErrors;
  }

  for (const [field, fieldValue] of Object.entries(data)) {
    if (["detail", "message", "error", "errors", "status"].includes(field)) {
      continue;
    }

    const message = valueToMessage(fieldValue);

    if (message) {
      return `${formatFieldName(field)}: ${message}`;
    }
  }

  return null;
}

export function getApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return "Something went wrong. Please try again.";
  }

  if (!error.response) {
    return "Unable to reach the server. Please check your connection and try again.";
  }

  const responseMessage = responseDataToMessage(error.response.data);

  if (responseMessage) {
    return responseMessage;
  }

  if (error.response.status === 400) {
    return "Please check the form and try again.";
  }

  if (error.response.status === 401) {
    return "Invalid username or password.";
  }

  return "Something went wrong. Please try again.";
}
