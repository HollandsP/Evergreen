import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
  inline?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text,
  className,
  inline = false,
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const Wrapper = inline ? 'span' : 'div';
  const wrapperClasses = inline 
    ? 'inline-flex items-center space-x-2' 
    : 'flex items-center justify-center space-x-2';

  return (
    <Wrapper className={cn(wrapperClasses, className)}>
      <div
        className={cn(
          'animate-spin rounded-full border-b-2 border-primary-600',
          sizeClasses[size],
        )}
      />
      {text && (
        <span className={cn('text-gray-600', textSizeClasses[size])}>
          {text}
        </span>
      )}
    </Wrapper>
  );
};

export default LoadingSpinner;
