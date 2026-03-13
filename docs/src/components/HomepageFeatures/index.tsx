import type { ReactNode } from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

import AmiInsightsAnimation from './AmiInsightsAnimation';
import FutureGridAnimation from './FutureGridAnimation';
import ScrollingNumbersAnimation from './ScrollingNumbersAnimation';

type FeatureItem = {
  title: string;
  img?: string;
  Animation?: React.FC;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'AMI Insights',
    Animation: AmiInsightsAnimation,
    description: (
      <>
        Unlock actionable grid patterns with high-resolution meter data.
      </>
    ),
  },
  {
    title: 'Plan the Future Grid',
    Animation: FutureGridAnimation,
    description: (
      <>
        Predict and prepare for dynamic grid evolution today.
      </>
    ),
  },
  {
    title: 'Data at Scale',
    Animation: ScrollingNumbersAnimation,
    description: (
      <>
        Analyze millions of data points in real-time.
      </>
    ),
  },
];

function Feature({ title, img, Animation, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        {Animation ? (
          <div className={styles.animationContainer}>
            <Animation />
          </div>
        ) : (
          <img src={img} className={styles.featureSvg} alt={title} />
        )}
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
