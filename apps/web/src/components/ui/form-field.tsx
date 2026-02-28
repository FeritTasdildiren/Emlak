import * as React from "react"
import {
  Controller,
  ControllerProps,
  FieldValues,
  Path,
  ControllerRenderProps,
} from "react-hook-form"

type FormFieldChildrenProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends Path<TFieldValues> = Path<TFieldValues>
> = ControllerRenderProps<TFieldValues, TName> & {
  errorMessage?: string
  label?: string
  helperText?: string
}

type FormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends Path<TFieldValues> = Path<TFieldValues>
> = Omit<ControllerProps<TFieldValues, TName>, "render"> & {
  label?: string
  helperText?: string
  children:
    | React.ReactElement
    | ((props: FormFieldChildrenProps<TFieldValues, TName>) => React.ReactElement)
}

interface ChildProps {
  label?: string
  helperText?: string
  [key: string]: unknown
}

const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends Path<TFieldValues> = Path<TFieldValues>
>({
  name,
  control,
  label,
  helperText,
  children,
  ...props
}: FormFieldProps<TFieldValues, TName>) => {
  return (
    <Controller
      name={name}
      control={control}
      {...props}
      render={({ field, fieldState }) => {
        const childProps: FormFieldChildrenProps<TFieldValues, TName> = {
          ...field,
          errorMessage: fieldState.error?.message,
          label,
          helperText,
        }

        if (typeof children === "function") {
          return children(childProps)
        }

        if (React.isValidElement(children)) {
          return React.cloneElement(children as React.ReactElement<ChildProps>, {
            ...childProps,
            label: label || (children.props as ChildProps).label,
            helperText: helperText || (children.props as ChildProps).helperText,
          } as React.Attributes & ChildProps)
        }

        return <></>
      }}
    />
  )
}

export { FormField }
