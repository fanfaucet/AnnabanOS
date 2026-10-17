# Printful Mock-up Client Prototype

This standard-library-only prototype is part of the Faucet Fan / AnnabanOS Printful mock-up MVD. It is a local testable scaffold, not a live account integration.

## Run the tests

From the repository root:

```bash
python -m unittest tests.test_printful_mockup_client -v
```

The tests use a fake transport and do not contact Printful. The client requires an explicit `MockupApproval` with status `APPROVED`, operator `Jacob Wayne Kinnaird`, and matching design/version/product/variant fields before sending a mock-up task request.

## Configuration

Copy `.env.example` into a local `.env` file only if your application has a dotenv loader configured. This prototype does not load dotenv automatically; set `PRINTFUL_STORE_TOKEN` in the process environment or pass a token directly during local testing. Never commit real tokens. `SHOPIFY_ACCESS_TOKEN` is reserved for a separate future listing integration and is not read by this client.

## Important limits

- The v2 task request payload must be checked against the current Printful API schema before live use.
- The prototype does not publish Shopify listings, set prices, or submit orders.
- The operator string check is not authentication. Production use requires a trusted identity provider, durable approval store, replay protection, secret management, and security review.
- The URL downloader allows HTTPS hosts ending in `.printful.com` or `.printful.me`; production deployments must harden redirects and outbound network policy.
