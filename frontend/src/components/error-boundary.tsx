import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error boundary:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center p-8">
          <div className="max-w-md text-center rounded-xl border border-border bg-bg-panel px-8 py-10">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-accent-amber/15 text-accent-amber">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <h2 className="text-section-title text-text-primary mb-2">This view hit a problem</h2>
            <p className="text-muted text-sm leading-relaxed mb-6">
              The page crashed while rendering. Your data is unchanged — try reloading this screen.
            </p>
            <Button
              variant="primary"
              onClick={() => {
                window.location.reload();
              }}
            >
              Reload page
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
