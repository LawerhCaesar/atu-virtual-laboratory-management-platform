# Signed Integration Return Contract

This contract allows an Administrator-approved demonstration resource to return structured session outputs to a Student's editable practical-submission draft. It is intended for controlled educational activity, not industrial model validation.

## 1. Administrator configuration

1. Store a long random shared secret in the deployment environment, keyed by a non-secret identifier:

   ```dotenv
   INTEGRATION_SHARED_SECRETS={"resource-key-id":"replace-with-a-long-random-shared-secret"}
   ```

2. Register the demonstration resource in the platform.
3. Select **Signed return** as its integration mode.
4. Enter `resource-key-id` as its integration key identifier and approve the resource.

The identifier is stored with the resource; the secret is read from the environment and is never stored in the database or placed in a launch URL.

## 2. Launch request

After a Student selects and saves an approved signed-return resource, the platform redirects the Student to the resource URL with these query parameters:

| Parameter | Purpose |
| --- | --- |
| `atu_session` | Opaque integration-session UUID. |
| `atu_return_url` | Platform callback URL. |
| `atu_return_token` | Signed, time-limited token bound to the integration session, submission and Student record. |
| `atu_completion_url` | Student-only platform page for checking the returned session status. |

The return token expires after `INTEGRATION_RETURN_TOKEN_MAX_AGE_SECONDS` (1,800 seconds by default).

## 3. Return request

The demonstration resource sends one HTTP `POST` request to `atu_return_url`. The body must be UTF-8 JSON and must not exceed `INTEGRATION_CALLBACK_MAX_BYTES` (1 MiB by default).

```json
{
  "session_id": "00000000-0000-0000-0000-000000000000",
  "return_token": "opaque-value-received-at-launch",
  "status": "completed",
  "outputs": {
    "run_reference": "DEMO-001",
    "summary": "Structured educational output"
  }
}
```

Required fields:

- `session_id`: the exact `atu_session` value;
- `return_token`: the exact `atu_return_token` value;
- `status`: `completed` or `failed`;
- `outputs`: a JSON object or array containing the structured output.

The sender computes an HMAC-SHA256 digest over the **exact raw request body bytes** using the shared secret and supplies the hexadecimal digest in this header:

```http
X-ATU-Signature: sha256=<hexadecimal-hmac-digest>
```

Conceptual signing example:

```python
signature = hmac.new(shared_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
header_value = f"sha256={signature}"
```

The JSON serialization used to calculate the signature must be the same bytes sent in the request. Do not parse and re-serialize the body between signing and transmission.

## 4. Responses and safeguards

| HTTP status | Meaning |
| --- | --- |
| `200` | The signed result was accepted and the submission draft was updated. |
| `400` | The JSON or required field values are invalid. |
| `403` | The HMAC, return token or token age failed verification. |
| `404` | The integration session does not exist. |
| `409` | A terminal result was already accepted for this session. |
| `413` | The callback body exceeds the configured limit. |

A successful callback records the integration status, returned payload, completion time and an audit event. A terminal callback cannot be replayed. The Student must still review the draft, attach the required evidence and explicitly confirm formal submission; the integration callback does not submit work automatically.

Production hardening rejects late callbacks after formal submission, revoked academic/resource access, and a resource selection that no longer matches the launch. These return `409` without changing the submission. The launch token contains a session UUID and random nonce, not internal Student/submission identifiers; server-side foreign keys and the stored token hash provide binding. The accepted record excludes the plaintext return token.
