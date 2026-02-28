import * as React from "react"
import { Minus, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { inputVariants } from "@/components/ui/input"

export interface NumberInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "defaultValue"> {
  value?: number
  defaultValue?: number
  onChange?: (value: number | undefined) => void
  min?: number
  max?: number
  step?: number
  suffix?: string
  label?: string
  helperText?: string
  errorMessage?: string
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 20 }).format(num)
}

const parseNumber = (str: string) => {
  // Remove thousands separators (dots) and replace decimal separator (comma) with dot
  const cleaned = str.replace(/\./g, "").replace(",", ".")
  const parsed = parseFloat(cleaned)
  return isNaN(parsed) ? undefined : parsed
}

const NumberInput = React.forwardRef<HTMLInputElement, NumberInputProps>(
  (
    {
      className,
      value,
      defaultValue,
      onChange,
      min,
      max,
      step = 1,
      suffix,
      label,
      helperText,
      errorMessage,
      disabled,
      ...props
    },
    ref
  ) => {
    // Internal state to handle the input string
    const [inputValue, setInputValue] = React.useState<string>("")
    
    // Initialize input value from value or defaultValue
    React.useEffect(() => {
      if (value !== undefined) {
        setInputValue(formatNumber(value))
      } else if (defaultValue !== undefined) {
        setInputValue(formatNumber(defaultValue))
      }
    }, [value, defaultValue])

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValueStr = e.target.value
      // Allow only digits, dot, comma, minus, or empty
      if (newValueStr !== "" && !/^[\d.,-]+$/.test(newValueStr)) return

      setInputValue(newValueStr)

      const parsed = parseNumber(newValueStr)
      if (onChange) {
        onChange(parsed)
      }
    }

    const handleBlur = () => {
      const parsed = parseNumber(inputValue)
      if (parsed !== undefined && !isNaN(parsed)) {
        let finalValue = parsed
        if (min !== undefined && finalValue < min) finalValue = min
        if (max !== undefined && finalValue > max) finalValue = max
        
        setInputValue(formatNumber(finalValue))
        if (onChange && finalValue !== parsed) {
          onChange(finalValue)
        }
      } else {
        setInputValue("")
        if (onChange) onChange(undefined)
      }
    }

    const increment = () => {
      const current = parseNumber(inputValue) ?? 0
      const newValue = current + step
      if (max !== undefined && newValue > max) return
      setInputValue(formatNumber(newValue))
      if (onChange) onChange(newValue)
    }

    const decrement = () => {
      const current = parseNumber(inputValue) ?? 0
      const newValue = current - step
      if (min !== undefined && newValue < min) return
      setInputValue(formatNumber(newValue))
      if (onChange) onChange(newValue)
    }

    const inputVariant = errorMessage ? "error" : disabled ? "disabled" : "default"

    return (
      <div className={cn("space-y-2", className)}>
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
        <div className="relative flex items-center">
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="rounded-r-none border-r-0 z-10 h-10 w-10 shrink-0"
            onClick={decrement}
            disabled={disabled}
            tabIndex={-1}
          >
            <Minus className="h-4 w-4" />
          </Button>
          
          <div className="relative flex-1">
             <input
              type="text"
              className={cn(
                inputVariants({ variant: inputVariant }),
                "rounded-none text-center px-2 z-0 relative", 
                errorMessage && "border-red-500 focus-visible:ring-red-500",
                className
              )}
              value={inputValue}
              onChange={handleInputChange}
              onBlur={handleBlur}
              disabled={disabled}
              ref={ref}
              {...props}
            />
            {suffix && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-sm text-muted-foreground">
                {suffix}
              </div>
            )}
          </div>

          <Button
            type="button"
            variant="outline"
            size="icon"
            className="rounded-l-none border-l-0 z-10 h-10 w-10 shrink-0"
            onClick={increment}
            disabled={disabled}
            tabIndex={-1}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
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

NumberInput.displayName = "NumberInput"

export { NumberInput }