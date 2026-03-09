import type { ReactNode } from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  img: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'AMI Insights',
    img: '/img/ami_insights_v2.png',
    description: (
      <>
        Empowering utilities with high-resolution AMI data to understand behavior,
        identify stress points, and optimize grid health.
      </>
    ),
  },
  {
    title: 'Plan the Future Grid',
    img: '/img/plan_future_grid_v2.png',
    description: (
      <>
        Simulate network expansions and renewable integration.
        Build a more resilient grid with predictive modeling.
      </>
    ),
  },
  {
    title: 'Data at Scale',
    img: '/img/data_at_scale_v2.png',
    description: (
      <>
        Leverage high-performance engines to process thousands of nodes and
        millions of readings in seconds.
      </>
    ),
  },
];

function Feature({ title, img, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={img} className={styles.featureSvg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
