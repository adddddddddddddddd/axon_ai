# Axon, the EEG Preprocessing AI Agent

The main goal of this project is to limit the time spent on the EEG preprocessing pipeline to let experts focus on the actual analysis of the results.

We are also implementing an ui to make interact with Axon easier. MCP could also be a thing.

A huge thanks for the work behind mne sdk. This is actually what powers the models capabilities and it is a wonderful package.

## Why Magistral Small 2509 ?

Axon is based on Magistral Small (2509 for the moment), which is a proprietary model from Mistral. Axon architecture leverages both vision and reasoning of the model and works very well on openneuro ds004504 cleaning. To be fair, Mistral's API has a generous free API plan.
Making it available through free, self-hosted models is a thing we could aim for.

