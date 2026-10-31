# Shared demo sign in

The login page gains **Log in to demo account**. The user chose editable demo documents and AI checks/chat, with team management and rule activation blocked. The existing fictional Northstar account and prepared documents are reused. Demo visitors share edits and conversation history; disclose this before sign in and throughout the workspace. No private uploads should be suggested.

Credentials stay server side. Use AWS SSM Parameter Store SecureString containing email, password and org_id. The host fetches it with its instance role into a mode 0600 private file at deployment/startup; the API verifies the account password and active membership before issuing an HttpOnly session. Never send credentials to JavaScript or log the decrypted parameter. Missing/invalid credentials disable demo entry with a generic error, without affecting normal login.

Restricted demo sessions are recorded separately from normal sessions and expire in one hour. The backend limits reads to the configured organisation and allows only document editing, comments, review/rewrite/chat operations. It denies team changes, invitations, other organisations, settings/consent changes, guideline changes and human approval. Effective role is creator even though the original account is an owner. Normal account sessions retain their existing permissions.

Approaches considered: browser credential autofill would expose the secret and grant owner access; direct AWS SDK access inside the container would widen cloud access and require new runtime dependencies. Host-side SSM loading reuses the deployment instance role and keeps cloud credentials out of the app container. Reload on deployment/startup rather than a network call for each visitor.

Validation covers missing/bad configuration, wrong password, disabled membership, secure cookies, expiry/logout, rate limits/CSRF, other-tenant denial, blocked administration/approval and allowed document/AI routes. Browser validation covers one-click dashboard entry, shared-demo disclosure, logout and normal login.
