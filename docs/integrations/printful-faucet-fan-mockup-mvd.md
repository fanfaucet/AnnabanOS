# Faucet Fan × Printful Mock-up Integration MVD

**Status:** Specification only — not deployed or connected to a live Printful or Shopify account  
**Originator:** Jacob Wayne Kinnaird  
**Repository context:** AnnabanOS Human Authority Gate MVD, PR #12  
**Initial milestone:** Generate mock-ups for human review before any listing is published

## 1. Goal

Define a narrow, auditable integration path from ChatGPT-assisted Faucet Fan artwork to Printful mock-up generation. This milestone ends when mock-up assets are stored and presented for human review. It does not publish a product, set a live price, create a paid order, or claim a live vendor connection.

## 2. System flow

1. **Design input:** Store a print-ready artwork asset and its metadata (design ID, version, checksum, intended product, placement, and source attribution).
2. **Human Authority Gate:** Create a `PENDING` approval record. Require an authenticated operator identity and an explicit approval bound to the design version, product ID, variant IDs, placement, and intended next action.
3. **Backend validation:** Verify approval is valid, unexpired, unused, and matches the exact payload. Reject missing, revoked, duplicated, or stale approvals.
4. **Catalog resolution:** Resolve the Printful catalog product and compatible variant IDs. Confirm placement/print-file requirements and artwork aspect ratio before requesting a mock-up.
5. **Mock-up task:** Submit a task to the chosen Printful API version and persist the returned task identifier before polling.
6. **Task completion:** Poll with backoff or consume the supported `mockup_task_finished` webhook; retain polling as a recovery path. Do not assume the result is synchronous.
7. **Asset persistence:** Download the temporary mock-up URLs to controlled storage, verify successful downloads and content types, and record checksums and source task metadata.
8. **Human review:** Present persisted previews to the operator. The next state is `AWAITING_LISTING_APPROVAL`; no product is published automatically in this milestone.
9. **Future milestone:** Shopify/Printful listing creation, price control, order approval, and fulfillment tracking require separate scope, implementation, tests, and approval gates.

## 3. Printful API versioning

Use one API version per task and make the version explicit in configuration. Verify the current endpoint schemas against Printful's official documentation before implementation.

### Preferred evaluation target: Mockup Generator v2

- Create task: `POST https://api.printful.com/v2/mockup-tasks`
- Retrieve tasks/results: `GET https://api.printful.com/v2/mockup-tasks?id={task_id}`
- Subscribe to the documented `mockup_task_finished` event where webhook configuration is supported.
- The v2 request uses catalog product/variant IDs and product/placement design data. Validate required fields against the current schema.

### Alternative: v1 endpoint

- Create task: `POST https://api.printful.com/mockup-generator/create-task/{product_id}`
- Retrieve task: `GET https://api.printful.com/mockup-generator/task?task_key={task_key}`
- The v1 request uses a product ID, variant IDs, and files/placements. Do not mix v1 request fields with v2 task payloads.

### Rate limits and retries

- Do not assume that the general API allowance applies to mock-up task creation.
- Printful documentation describes mock-up creation limits of 2 requests/minute for new stores and up to 10 requests/minute for established stores, with actual limits supplied by response headers and potentially varying by account/API version.
- Read rate-limit headers and honor `Retry-After` on HTTP 429. Use a queue, bounded concurrency, exponential backoff with jitter, and a per-store task-creation throttle. Do not hard-code 120 calls/minute as the mock-up limit.
- Avoid duplicate task creation on retry: persist an internal idempotency key derived from the approved design version, product, variants, placements, and API version.

## 4. Temporary mock-up URLs

Printful documents mock-up URLs as temporary (commonly up to 72 hours). Treat them as expiring immediately for design purposes:

- Download each approved task result promptly to controlled object storage.
- Check HTTP status, file size, and allowed image content type; calculate a SHA-256 checksum.
- Store the durable asset URI, checksum, Printful task ID, product/variant IDs, design version, and retrieval timestamp.
- Do not expose bearer tokens or treat temporary Printful URLs as permanent storefront assets.
- If download or persistence fails, retain the task metadata and retry safely before the source URL expires.

## 5. Human Authority Gate contract

Proposed states:

`PENDING → APPROVED → TASK_SUBMITTED → MOCKUP_READY → AWAITING_LISTING_APPROVAL`

Failure/rejection paths:

`PENDING → REJECTED`  
`APPROVED → REVOKED` (before submission)  
`TASK_SUBMITTED → RETRYABLE_FAILURE | TERMINAL_FAILURE`

Required event fields:

- event ID and timestamp
- actor identity from an authenticated source (not a self-asserted label alone)
- action and decision
- design ID/version and checksum
- product ID, variant IDs, placements, and API version
- approval/request correlation ID and task ID
- prior-event hash and current-event hash where the current ledger implementation supports it
- result code and sanitized error summary

The current Human Authority Gate MVD is described in PR #12 as a local demonstration with in-memory storage and a hash chain, not an immutable external ledger or production authentication system. Do not represent it as production-secure without further implementation and review.

## 6. Security and operational controls

- Store Printful credentials only in backend secret storage/environment configuration; never commit tokens or expose them to browser code, logs, or generated documentation.
- Use a store-scoped token and the narrowest available permissions. Keep Shopify credentials separate from Printful credentials.
- Validate webhook signatures according to the provider's current instructions, reject invalid events, and deduplicate deliveries.
- Treat webhook payloads as untrusted input; confirm task status through the documented API when needed.
- Keep outbound requests on an allowlisted Printful API host. Validate artwork source URLs and prevent server-side request forgery.
- Record audit events without logging credentials or unnecessary customer personal data.
- Fail closed: if approval, catalog validation, or asset persistence cannot be verified, do not proceed to listing publication.
- An AnnabanOS gate only governs actions routed through this integration. It cannot guarantee control over changes made directly in Shopify or Printful dashboards unless platform permissions and operational policy prevent those bypasses.

## 7. Acceptance criteria for this milestone

- [ ] API version and request schema are pinned and documented.
- [ ] Catalog product and compatible variant IDs are validated.
- [ ] No task can be created without approval bound to the exact design/version and product configuration.
- [ ] Task ID is persisted before polling or webhook processing.
- [ ] Polling respects provider rate limits and retries safely.
- [ ] Webhook authentication and deduplication are implemented if webhooks are enabled.
- [ ] Temporary mock-up assets are downloaded to durable storage and checksummed.
- [ ] Audit trail records the approval, request, task result, and asset references.
- [ ] Unit tests cover missing approval, stale approval, duplicate submission, API errors, HTTP 429, failed asset download, invalid webhook, and successful completion.
- [ ] No Shopify listing or paid order is created by the mock-up-only milestone.
- [ ] No live account connection, vendor partnership, or successful deployment is claimed until independently verified.

## 8. Official references

- Printful API documentation: https://developers.printful.com/docs/
- Printful Mockup Generator v2 documentation: https://developers.printful.com/docs/v2-beta/
- Printful Mockup Generator v1 documentation: https://developers.printful.com/docs/

## 9. Next implementation sequence

1. Review the current repository Human Authority Gate interface and test contract.
2. Add a typed Printful API client with version-specific request/response models.
3. Add an approval-bound mock-up request service and task persistence.
4. Add durable image storage and checksums.
5. Add tests with mocked HTTP responses; never require live credentials for unit tests.
6. Only after mock-up review works, design a separate Shopify listing approval flow.
