---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t316-copyout-t840
seq: 1
---

## 新規

### {{F:flaky-anchor-contaminates-mutation-attribution}}. フレークする anchor が無関係な変異の失敗集合へ紛れ込み帰属を汚染した [テスト代表性] [計測汚染]

- 事象: 新設した `test_copyout_destination_swap_after_hash_is_rejected_on_same_fd` が、単独走行では
  3 回連続で緑 (各 `2 passed` / rc=0) だが、ファイル全体の並列 (xdist) 走行で間欠的に落ちた。
  変異走行で 2 度観測した。無関係な変異 M11 (別 file のみを変異) の失敗集合に 1 件として現れ、
  変異 M2b の失敗集合には本来の 2 件に加えて 3 件目として混入した。
  **静的レビュー 5 本 (段 3 の敵対レンズ 2 本、段 6 の敵対レビュー 2 本、焦点再レビュー 1 本) は
  いずれも検出できなかった。** 並列走行でしか出ないため原理的に見えない。
- 根本原因: テストが差し替えた `full_sha256()` の**内側**で destination entry を rename していた。
  その呼び出しは `_full_sha256_fd()` の 2 度の `fstat` の間にあり、rename は held inode の
  `ctime` を更新する。実装側の `_stable_file_identity()` は `ctime_ns` を比較するため、
  timestamp tick が同一に収まるかで拒否理由が 2 通りに分岐していた
  (`binary が sha256 中に変化した` の早期拒否 / 本来の `destination entry` 不一致)。
  親の初期推定 (`next(rglob(...))` の非決定性) は**外れ**で、fix worker が変異ログに両方の結果が
  残っていることから真因を特定した。
- 恒久対応: 観測を `_full_sha256_fd()` 完了後の swap へ移し、対象を `/proc/self/fd/<fd>` から
  一意に取得し、fsync も mode 推定でなく hash に使った exact fd だけを記録する
  (`orchestrator/tests/test_buildcache_v2.py`、commit `a469863d`)。
  測っている 4 性質 (destination entry 不一致による拒否 / nm・sha256・fsync が同一 inode /
  `.publish-*` が残らない / `ycsb_silo.exe` が残らない) はすべて維持した。
- 再発検知: 変異本走の期待 node 完全一致検査 (`DW-M08`)。フレークが混入すると
  `matches_expectation=False` になり、`MISMATCH` として停止する。本 wave では実際にそこで止まった。

### {{F:equivalent-mutation-recorded-as-unkillable}}. 等価変異を「殺せない変異」と読み違えた [恒真ゲート] [テスト代表性]

- 事象: 変異 M11 (`_low_level_allowlist_violations()` の `path == relative_path` を
  `path.startswith(relative_path)` へ緩める) が SURVIVED した。注入は実在した
  (`anchor_counts=1`、injection diff あり) ため `DW-M04` の注入実在検査は通っている。
  当初は「検査が弱い」と読みかけたが、実際は**変異が何も変えていない**。
  既存 decoy が許可 path より長い suffix / nested path だけだったため `startswith` が常に偽で、
  exact match と意味が同じだった。
- 根本原因: decoy の設計。**許可 path の真の前方一致**を 1 件も持たない decoy 集合に対しては、
  前方一致への緩和が観測不能である。「集合に文字列が無いこと」を assert するだけで、
  実 matcher へ decoy source を渡していなかった前段の恒真性 (焦点再レビューが指摘) と同根。
- 恒久対応: 許可 path `.../smoke_driver.py` の真の前方一致 `.../smoke_driver` を synthetic path として
  **実 matcher へ渡す** decoy を追加した (`orchestrator/tests/test_p3_build_authority_cli.py`、
  commit `a469863d`)。再走で単一 node `test_low_level_issuer_allowlist_rejects_prefix_and_nested_paths`
  により KILLED を実測した。
- 再発検知: 変異本走で SURVIVED が出たら、まず `DW-M02` に従って他層 mask と**等価性**の両方を疑い、
  注入 diff を読んで「意味が変わっているか」を確認してから結論する。
