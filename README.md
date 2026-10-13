# AnnabanOS

AnnabanOS includes advisory/governance scaffolds, a prototype community-provider registry, and the Annaban solo demonstration provider.

## Solo Annaban demo

A local, deterministic Annaban demonstration provider is available without API keys. It is explicitly selected with `"provider_ids": ["annaban-demo"]` on `POST /stream/business`. Selecting it runs Annaban alone and does not call other configured providers.

Developer attribution: Jacob Wayne Kinnaird. The demo is a rules-based template, not a trained generative model. It is simulation-only and advisory-only; it does not execute actions or mutate external state.

## Swappable participants

Actor contracts separate stable role slots from concrete provider identities and human-facing DBA labels. Input records freeze `actor_snapshot` at write time, while role bindings can be changed for future resolution without rewriting thread history.

See [the actor/provider binding guide](docs/actor-provider-bindings.md), [Annaban solo demo guide](docs/annaban-solo-demo.md), and [community model-provider onboarding](docs/community-model-providers.md).
