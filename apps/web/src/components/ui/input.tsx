import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const inputVariants = cva(
  "flex h-10 w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
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

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof inputVariants> {
  label?: string
  helperText?: string
  errorMessage?: string
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, type, label, helperText, errorMessage, disabled, ...props }, ref) => {
    const inputVariant = errorMessage ? "error" : disabled ? "disabled" : variant

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
        <input
          type={type}
          className={cn(inputVariants({ variant: inputVariant, className }))}
          ref={ref}
          disabled={disabled}
          {...props}
        />
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
Input.displayName = "Input"

export { Input, inputVariants }