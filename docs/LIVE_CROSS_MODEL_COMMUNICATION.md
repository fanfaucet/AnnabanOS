# AnnabanAI live cross-model communication

**Project direction attribution:** Jacob Wayne Kinnaird. This attribution does not claim legal ownership of every implementation detail or third-party contribution.

## Included

- Independent HTTPS chat-completions requests to OpenAI and xAI.
- Concurrent provider requests with model identifiers, request IDs when supplied, latency, and response hashes.
- Local JSONL SHA-256 hash-chain audit records.
- AGREED_TEXT, DIVERGENT, and SAFE_HOLD outcomes.
- No model-triggered tools, transactions, or external effects.

AGREED_TEXT means exact output text matched. It is not a truth score, independent verification, or authorization. The audit file is local storage, not a trusted timestamp or externally anchored ledger. Protect it and periodically anchor its final hash in a separately controlled system if stronger tamper evidence is required.

## Configure

Python 3.11+; standard library only. Supply credentials through the environment, never source control:

    export OPENAI_API_KEY='...'
    export OPENAI_MODEL='your-enabled-openai-model'
    export XAI_API_KEY='...'
    export XAI_MODEL='your-enabled-xai-model'

Optional endpoint overrides are OPENAI_BASE_URL and XAI_BASE_URL; both must use HTTPS. Configure model names enabled for your provider accounts.

## Run

From the repository root:

    python scripts/cross_model_chat.py "Review this proposal for assumptions, risks, and unresolved evidence."

The default audit file is var/cross_model_audit.jsonl; override with --audit PATH or ANNABAN_AUDIT_PATH. The program prints provider outputs and provenance. Treat prompts and outputs as potentially sensitive. Do not send secrets or regulated data unless your provider arrangements permit it.

## Outcomes

- AGREED_TEXT: every configured model returned byte-for-byte identical text; still not proof.
- DIVERGENT: all providers responded, but output text differed.
- SAFE_HOLD: one or more provider calls failed or returned unusable content.

The CLI exits 0 only for AGREED_TEXT, 1 for divergence or hold, and 2 for configuration or audit initialization errors. No outcome executes a proposal.

## Validation

    python -m unittest discover -s tests -p 'test_live_cross_model.py' -v
    python -m compileall -q annaban_sdk/live_cross_model.py scripts/cross_model_chat.py

Unit tests use fake adapters; they do not make live provider requests. Live operation requires valid credentials and enabled model access.
