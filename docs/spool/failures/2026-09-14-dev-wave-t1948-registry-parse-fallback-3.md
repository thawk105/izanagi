---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1948-registry-parse-fallback
seq: 3
---

## 新規

### {{F:unreadable-registry-counted-as-zero-candidates}}. 読めなかった registry を候補 0 件と同一視し、件数による排他を素通りさせた [恒真ゲート]

- 事象: 床値 campaign の再試行認可は、旧 `valid=False` 経路と registry の検証済み recovery の
  **排他的二択**であり、排他は候補 evidence の件数で判定すると定めてある (D880)。ところが
  registry の読取が例外になったとき、旧経路の候補が 1 件あれば正常復帰する fallback が 2 箇所に
  あった。候補件数を数えられていないのに件数による排他を通していたので、
  「registry 側にも候補があった履歴」と区別できないまま retry が 1 本認可された。
  さらに reader 自身にも 3 箇所目があり、`lstat()` と `read_bytes()` の
  `FileNotFoundError` を同じ節で受けていたため、存在しない対象への symlink が
  「不在 = 候補 0 件」へ化けていた。
- 根本原因: **判定できなかった事実を、判定できた値へ変換した。** 「不在」は候補 0 件という
  結果であり、「読めない」は結果が無いことである。両者を同じ except 節で受けると、
  後者が前者の顔をして下流の件数検査を通過する。件数で排他する gate は、件数が確定した
  ときにだけ意味を持つ。
- 恒久対応: {{D:registry-read-failure-not-legacy-authorization}}。実体は
  `orchestrator/campaign/s8b_holdout_admission.py` の
  `_assert_retry_start_authorized_locked` / `floor_retry_trigger_for_round` から救済 catch を
  除去し、`_read_floor_registry_candidate_rows` の不在判定を `lstat()` に限定した変更
  (commit `335e582b1`)。
- 再発検知: `orchestrator/tests/test_s8b_holdout_admission.py` の負例 3 件
  (`test_malformed_registry_rejects_existing_failed_session_retry_query` /
  `..._consumption` / `..._inspection`)、
  `test_dangling_registry_symlink_is_not_treated_as_absent`、および過剰拒否の正例
  `test_missing_registry_preserves_existing_failed_session_retry`。
  変異 `MUT-T1948-QUERY-PARSE-FALLBACK` / `MUT-T1948-SHARED-PARSE-FALLBACK` /
  `MUT-T1948-READ-ENOENT-AS-ABSENT` / `MUT-T1948-ABSENT-AS-UNREADABLE` が全 KILLED
  (`output/insights/2026-09-14/t1948-registry-parse-fallback/`)。
- 検出経路: 起票は別 wave の段 6 レビューで、本 wave はその carry を実装した。
  reader の 3 箇所目は本 wave の段 2 プランが、親 brief の「既に分離できている」という前提を
  現物で崩して見つけた。
