import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

type Feature = {
  title: string;
  description: string;
};

const FEATURES: Feature[] = [
  {
    title: 'Sidebar panel',
    description:
      'Create, edit and delete items in a panel in the Home Assistant sidebar. Each page has its own URL.',
  },
  {
    title: 'Native entities and a card',
    description:
      'Each item has a sensor entity, and a dashboard card lists the items with their values.',
  },
  {
    title: 'Services and events',
    description:
      'Each data action is a service, and each change fires a bus event that automations can use.',
  },
  {
    title: 'Translations',
    description:
      'The panel, the card and the service text follow the Home Assistant language.',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className={styles.heroTitle}>
          {siteConfig.title}
        </Heading>
        <p className={styles.heroTagline}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link className="button button--secondary button--lg" to="/docs/intro">
            User Guide
          </Link>
          <Link
            className="button button--outline button--secondary button--lg"
            to="/developer/integrating">
            Developer Guide
          </Link>
        </div>
      </div>
    </header>
  );
}

function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FEATURES.map((feature) => (
            <div key={feature.title} className={clsx('col col--6', styles.feature)}>
              <Heading as="h3">{feature.title}</Heading>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
