# iOS TODO

## Type-ahead request state

- [ ] Associate each suggestion request with a generation ID so only the newest
  request can update the `Predicting…` / `Ready` status. A cancelled older
  request must not show `Ready` while the newest request is still running.
  Verify that the suggestion pills and `Ready` state appear together for the
  latest request.
