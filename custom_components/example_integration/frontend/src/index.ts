import { ExamplePanel } from './panel';

if (!customElements.get('example-panel')) {
  customElements.define('example-panel', ExamplePanel);
}

export { ExamplePanel };
