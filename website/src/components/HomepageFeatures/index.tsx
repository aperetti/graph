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
    img: '/img/ami_insights_v3.png',
    description: (
      <>
        Unlock actionable grid patterns with high-resolution meter data.
      </>
    ),
  },
  {
    title: 'Plan the Future Grid',
    img: '/img/plan_future_grid_v3.png',
    description: (
      <>
        Predict and prepare for dynamic grid evolution today.
      </>
    ),
  },
  {
    title: 'Data at Scale',
    img: '/img/data_at_scale_v3.png',
    description: (
      <>
        Analyze millions of data points in real-time.
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
