# Git repository extension for AnnabanAI KCA

`GitRepositoryExtension` is a read-only GitHub REST adapter for the Knowledge Curator Agent. It inventories a selected branch's commit and tree, hashes the canonical snapshot, and reports only simple repository-structure gaps (README and conventional test paths).

## Use

```python
from annabanos.extensions.git import GitRepositoryExtension

source = GitRepositoryExtension("owner/repository")
observation = source.observe(
    ref="main",
    jurisdiction_id="US-TX",
    visibility="internal",
)
print(observation)
```

Set `GITHUB_TOKEN` for authenticated API access when required. A token is never written to the observation. The extension uses GET requests only; it does not clone or execute repository code, create branches, open issues, commit, reward agents, or mutate schemata. Network observation happens only when `snapshot` or `observe` is called. Tests inject a fake transport and do not use live APIs.

Findings are advisory indicators, not proof that documentation or tests do not exist. Tree truncation and malformed API responses fail closed rather than returning an incomplete snapshot. Jurisdiction and visibility are required on every snapshot.
