import { Component, type ReactNode } from 'react';

interface State {
  failed: boolean;
  attempt: number;
}

/**
 * Keeps a map crash (WebGL context loss, deck.gl/maplibre exception) from unmounting the
 * whole app, which otherwise leaves a blank page. Offers a retry that remounts the map.
 */
export class MapErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { failed: false, attempt: 0 };

  static getDerivedStateFromError(): Partial<State> {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    console.error('Map crashed; showing fallback.', error);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="map-fallback" role="alert">
          <p>The map stopped working. Your field and choices are kept.</p>
          <button
            type="button"
            className="btn-cta"
            onClick={() => this.setState((s) => ({ failed: false, attempt: s.attempt + 1 }))}
          >
            Reload map
          </button>
        </div>
      );
    }
    return (
      <div key={this.state.attempt} className="map-boundary">
        {this.props.children}
      </div>
    );
  }
}
