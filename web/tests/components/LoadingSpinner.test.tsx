import { render, screen } from '@testing-library/react';
import LoadingSpinner from '@/components/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders loading spinner with default props', () => {
    render(<LoadingSpinner />);
    
    const spinnerDiv = document.querySelector('.animate-spin');
    expect(spinnerDiv).toBeInTheDocument();
    expect(spinnerDiv).toHaveClass('animate-spin');
    expect(spinnerDiv).toHaveClass('rounded-full');
  });

  it('renders loading spinner with custom size', () => {
    render(<LoadingSpinner size="lg" />);
    
    const spinnerDiv = document.querySelector('.animate-spin');
    expect(spinnerDiv).toBeInTheDocument();
    expect(spinnerDiv).toHaveClass('h-8');
    expect(spinnerDiv).toHaveClass('w-8');
  });

  it('renders loading spinner with custom message', () => {
    const message = 'Loading content...';
    render(<LoadingSpinner text={message} />);
    
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  it('renders inline spinner correctly', () => {
    render(<LoadingSpinner inline={true} text="Processing..." />);
    
    const wrapper = document.querySelector('.inline-flex');
    expect(wrapper).toBeInTheDocument();
    expect(wrapper).toHaveClass('inline-flex');
    expect(wrapper).toHaveClass('items-center');
  });
});
