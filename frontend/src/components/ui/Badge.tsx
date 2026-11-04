import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

export const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground shadow',
        secondary: 'border-transparent bg-secondary text-secondary-foreground',
        destructive: 'border-transparent bg-destructive text-destructive-foreground shadow',
        outline: 'text-foreground border border-border',
        solicitado: 'border border-amber-200 dark:border-amber-800/60 bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300',
        confirmado: 'border border-emerald-200 dark:border-emerald-800/60 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300',
        anulado: 'border border-rose-200 dark:border-rose-800/60 bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300',
        cancelado: 'border border-rose-200 dark:border-rose-800/60 bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300',
        presente: 'border border-blue-200 dark:border-blue-800/60 bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300',
        ausente: 'border border-slate-300 dark:border-neutral-700 bg-slate-200 dark:bg-neutral-800 text-slate-700 dark:text-neutral-300',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps): React.JSX.Element {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export default Badge;
