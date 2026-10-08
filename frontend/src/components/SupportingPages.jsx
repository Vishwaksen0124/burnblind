import { PageHeading, StateMessage } from './shared.jsx';

const PIPELINE = [
  ['01', 'Observe', 'Collect satellite and environmental observations with source and time metadata.'],
  ['02', 'Find monitoring gaps', 'Identify periods and places where observation coverage is incomplete or uncertain.'],
  ['03', 'Detect', 'Group potential thermal observations into candidate events. A detection is not ground truth.'],
  ['04', 'Assess impact', 'Estimate potential downwind exposure when weather and population inputs are available.'],
  ['05', 'Prioritize', 'Combine validated evidence, monitoring blindness, and impact to rank events.'],
  ['06', 'Investigate', 'Cross-check important or uncertain events and present evidence for human review.'],
];

export function HowItWorksPage() {
  return <>
    <PageHeading eyebrow="SYSTEM OVERVIEW" title="How BurnBlind works">A transparent workflow for finding potential events that deserve a closer look.</PageHeading>
    <section className="pipeline" aria-label="BurnBlind monitoring pipeline">{PIPELINE.map(([number, title, copy]) => <article className="pipeline-step" key={number}><span className="pipeline-number">{number}</span><div><h2>{title}</h2><p>{copy}</p></div><span className="pipeline-arrow" aria-hidden="true">↘</span></article>)}</section>
    <p className="science-note"><strong>Scientific boundary</strong> BurnBlind identifies potential monitoring gaps and cross-source differences. It does not claim a confirmed fire without independent ground truth.</p>
  </>;
}

export const SOURCES = [
  { name: 'GK2A AMI', url: 'https://zenodo.org/records/20084790', type: 'Historical replay source', provides: 'Thermal hotspot detections used to build the current Punjab and Haryana replay sample.', limit: 'A satellite detection is a candidate observation, not a verified incident. Current UI sample covers Oct–Nov 2025.' },
  { name: 'NASA FIRMS / VIIRS', url: 'https://firms.modaps.eosdis.nasa.gov/active_fire/', type: 'Planned comparison source', provides: 'Independent active-fire observations for cross-sensor comparison.', limit: 'No matched comparison records are currently exposed by the application API.' },
  { name: 'Weather / reanalysis', url: 'https://open-meteo.com/en/docs/historical-weather-api', type: 'Planned environmental source', provides: 'Wind context for estimating a potential downwind screening corridor.', limit: 'Weather evidence is not yet connected to the dashboard API.' },
  { name: 'WorldPop', url: 'https://www.worldpop.org/', type: 'Planned exposure source', provides: 'Population estimates that may support potential exposure screening.', limit: 'No population exposure estimate is currently available in the replay API.' },
];

export function DataPage() {
  return <>
    <PageHeading eyebrow="TRANSPARENCY" title="Data & methodology">Understand what the current replay can show, what it cannot, and how future assessments will be grounded.</PageHeading>
    <section className="source-grid" aria-label="Data sources">{SOURCES.map((source) => <article className="source-card panel" key={source.name}><span className="source-type">{source.type}</span><h2><a href={source.url} target="_blank" rel="noreferrer">{source.name}<span aria-hidden="true"> ↗</span></a></h2><p>{source.provides}</p><div className="source-limit"><strong>LIMITATION</strong><p>{source.limit}</p></div></article>)}</section>
    <section className="terms-panel panel"><p className="eyebrow">TERMINOLOGY</p><dl>
      <div><dt>Monitoring blind spot</dt><dd>A gap or limitation in observation coverage; it does not prove an event occurred.</dd></div>
      <div><dt>Cross-sensor disagreement</dt><dd>Different sensors report different observations or coverage. This is evidence to investigate, not proof that a sensor missed a fire.</dd></div>
      <div><dt>Potential fire event</dt><dd>A candidate grouped from source detections. Confirmation requires independent ground truth.</dd></div>
      <div><dt>Estimated exposure</dt><dd>A modeled estimate that depends on population and environmental inputs; it is not a measured impact.</dd></div>
    </dl></section>
  </>;
}

export function InvestigationsPage() {
  return <>
    <PageHeading eyebrow="EVIDENCE REVIEW" title="Investigations">Investigation reports will appear here when the event trigger and evidence pipeline are available.</PageHeading>
    <StateMessage title="Investigation data unavailable">This historical replay has no scored events or completed agent investigations. Candidate detections are not sent for autonomous response.</StateMessage>
    <section className="investigation-readiness panel"><p className="eyebrow">CURRENT REPLAY CAPABILITIES</p><ul><li>Candidate detections can be reviewed by location, time, and source.</li><li>Blindness scores, fire likelihood, and exposure estimates are not available.</li><li>No investigation has been queued or completed for this sample.</li></ul></section>
  </>;
}
