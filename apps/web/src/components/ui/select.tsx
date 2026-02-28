import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const selectVariants = cva(
  "flex h-10 w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-input focus-visible:ring-ring",
        error: "border-red-500 focus-visible:ring-red-500",
        disabled: "cursor-not-allowed opacity-50 bg-muted",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size">,
    VariantProps<typeof selectVariants> {
  label?: string
  options: SelectOption[]
  placeholder?: string
  helperText?: string
  errorMessage?: string
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, variant, options, label, placeholder, helperText, errorMessage, disabled, ...props }, ref) => {
    const selectVariant = errorMessage ? "error" : disabled ? "disabled" : variant

    return (
      <div className="w-full space-y-2">
        {label && (
          <label
            className={cn(
              "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
              errorMessage && "text-red-500"
            )}
          >
            {label}
          </label>
        )}
        <select
          className={cn(selectVariants({ variant: selectVariant, className }))}
          ref={ref}
          disabled={disabled}
          defaultValue=""
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {helperText && !errorMessage && (
          <p className="text-sm text-muted-foreground">{helperText}</p>
        )}
        {errorMessage && (
          <p className="text-sm text-red-500">{errorMessage}</p>
        )}
      </div>
    )
  }
)
Select.displayName = "Select"

export { Select, selectVariants }
