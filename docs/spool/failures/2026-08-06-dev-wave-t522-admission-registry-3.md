---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t522-admission-registry
seq: 3
---

## 再発

### F57

- **再発: 2026-08-06 ([T-522] 受入全走)。** 6,606 件の全走 (48 worker、request `892018`) で
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が 1 件落ちた。原因は assert 不一致ではなく
  `git -c core.useReplaceRefs=false cat-file --batch-check` の 15 秒 timeout (`returncode -9`) で、
  同 file 単独の再走は 8 passed / 29.23 秒で再現しない。**[T-327] が 2026-08-05 に
  同型 (全走 6,034 件で `git add -A` が 30 秒 timeout) を session fixture 化 + timeout 180 秒で
  塞いだ直後の再発**であり、対策された呼び出しではなく `_batch_oids` 側の別の git 呼び出しで出た。
  本 wave の差分 (admission registry) は当該コードへ到達しない。恒久対応は
  {{T:s8c-git-timeout-under-load}} として起票する。
