import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium ring-offset-background transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-gradient-primary text-primary-foreground shadow-medium hover:shadow-strong hover:scale-105",
        destructive:
          "bg-destructive text-destructive-foreground shadow-medium hover:bg-destructive/90 hover:shadow-strong hover:scale-105",
        outline:
          "border-2 border-border bg-background hover:bg-primary-light hover:border-primary/50 hover:scale-105 shadow-subtle hover:shadow-medium",
        secondary:
          "bg-secondary text-secondary-foreground shadow-subtle hover:bg-secondary/80 hover:shadow-medium hover:scale-105",
        ghost: "hover:bg-primary-light hover:text-primary hover:scale-105",
        link: "text-primary underline-offset-4 hover:underline hover:scale-105",
        premium: "bg-gradient-accent text-accent-foreground shadow-elegant hover:shadow-strong hover:scale-110 border border-accent/20",
        glass: "glass text-foreground hover:bg-primary-light hover:scale-105",
      },
      size: {
        default: "h-11 px-6 py-3",
        sm: "h-9 rounded-full px-4 text-xs",
        lg: "h-14 rounded-full px-8 text-base",
        icon: "h-11 w-11",
        fab: "h-14 w-14 rounded-full shadow-strong hover:shadow-elegant",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
