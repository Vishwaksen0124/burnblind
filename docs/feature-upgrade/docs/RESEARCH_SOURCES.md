# Research Sources

- WeMakeDevs Environmental Hacks: https://www.wemakedevs.org/aws/env
- Rules: https://www.wemakedevs.org/aws/env/rules
- Environmental Hacks announcement: https://www.wemakedevs.org/blogs/announcing-environmental-hacks
- GK2A Punjab/Haryana dataset: https://zenodo.org/records/20084790
- NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/active_fire/
- GK2A AWS Open Data: https://registry.opendata.aws/noaa-gk2a-pds/
- Open-Meteo historical weather: https://open-meteo.com/en/docs/historical-weather-api
- WorldPop India population: https://hub.worldpop.org/
- NOAA HYSPLIT: https://www.arl.noaa.gov/hysplit/
- Strands Agents: https://strandsagents.com/
- Strands evaluations: https://strandsagents.com/docs/user-guide/evals-sdk/evaluators/
- CloudWatch AI agent telemetry: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/omni-send-ai-agent-telemetry.html

Research conclusions:
1. BurnBlind should focus on turning environmental measurements into decisions.
2. Blind spots are a differentiator, but must not be described as calibrated missed-fire probabilities.
3. Cross-sensor disagreement is useful investigation evidence, not proof of a missed event.
4. Exposure should be transparent and labelled as an estimate unless a validated dispersion model is used.
5. HYSPLIT is a strong advanced option but should not block the MVP.
6. Strands is suitable for the Investigation Agent; deterministic scoring remains outside the LLM.
7. Agent evaluation should include trajectory/tool/grounding/failure tests.
