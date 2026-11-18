import type { UseFormRegisterReturn } from "react-hook-form";

type TextFieldProps = {
  id: string;
  label: string;
  registration: UseFormRegisterReturn;
  error?: string;
  type?: string;
  placeholder?: string;
  autoComplete?: string;
};

export function TextField({
  id,
  label,
  registration,
  error,
  type = "text",
  placeholder,
  autoComplete,
}: TextFieldProps) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1 block text-xs font-semibold text-slate-600"
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${id}-error` : undefined}
        className="ui-input h-11"
        {...registration}
      />
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-1 text-xs font-medium text-destructive">{error}</p>
      ) : null}
    </div>
  );
}
