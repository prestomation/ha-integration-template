import { CARD_DESCRIPTION, CARD_NAME, ExampleCard, ExampleCardEditor } from './card';

if (!customElements.get('example-card')) {
  customElements.define('example-card', ExampleCard);
}
if (!customElements.get('example-card-editor')) {
  customElements.define('example-card-editor', ExampleCardEditor);
}

// Advertise the card in the dashboard "Add card" picker.
interface CustomCard {
  type: string;
  name: string;
  description: string;
  preview?: boolean;
  documentationURL?: string;
}
const w = window as unknown as { customCards?: CustomCard[] };
w.customCards = w.customCards || [];
if (!w.customCards.some((c) => c.type === 'example-card')) {
  w.customCards.push({
    type: 'example-card',
    name: CARD_NAME,
    description: CARD_DESCRIPTION,
    preview: true,
    documentationURL: 'https://github.com/prestomation/ha-integration-template',
  });
}

export { ExampleCard, ExampleCardEditor };
