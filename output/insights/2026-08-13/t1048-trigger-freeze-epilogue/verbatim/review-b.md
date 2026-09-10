must-fix は変異台帳の期待集合 1 件です。登録済み 3 変異に、生存しそうなものは静的にはありません。

### 所見 1 — MUT-1 / MUT-2 の期待失敗 node 集合が事前登録と一致しない

**主張:** MUT-1 は 3 node、MUT-2 は少なくとも `test_build_admission.py` 内だけで 37 node を赤にする。裁定表の単数形の期待では `DW-M08` の完全集合一致を満たさず、MUT-2 は `KILLED` でなく `MISMATCH` になる。

**根拠:** 裁定は MUT-1 と MUT-2 を各 1 テスト相当として記述している（[ruling.md](/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t1048-trigger-freeze-epilogue/ruling.md:121)）。しかし helper は全正例に既定の後続 bytes を付ける（[test_build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:123)）。したがって `raw[start:] == E` を要求する MUT-2 は、32 mask、pristine 1、post-epilogue 2、read-once 1、runtime-recheck 1 の計 37 node を少なくとも落とす（同ファイル [293](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:293)、[303](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:303)、[312](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:312)、[547](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:547)、[566](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:566)）。MUT-1 では `deleted`、`modified`、`gap-before` の 3 parameter node が赤になる（同ファイル [337](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:337)）。

**影響:** 変異の検出力自体はあるが、期待集合が違うため mutation ledger は MUT-1/MUT-2 を `KILLED` と記録できない。

**成果物影響:** 放置すると変異台帳の状態が `KILLED` から `MISMATCH` に変わり、レポートが参照する「3/3 KILLED」と gate 完了証拠が成立しない。

**推奨:** **must-fix。** runner を専用 test function に狭めて parameter node を完全列挙するか、実際の runner 全体で失敗 node の完全集合を probe 後に再登録する。MUT-3 は patch 整合 node を runner へ必ず含めること。他の意味論テストは変更後の定数から入力も生成するため、そこを外すと MUT-3 は生存する。

### 所見 2 — call の束縛を差し替える未記録の意味論攻撃が残る

**主張:** block と epilogue を逐語一致させたまま、prologue で `Backoff` または `FLAGS_clocks_per_us` の名前解決を差し替えれば gated call を無効化できる。これは R4 の gate 変数再宣言、R5 の非到達化、R6 の dangling `else` のいずれでもない。

具体例は、宣言と BEGIN の間にローカルな `FLAGS_clocks_per_us = 0` を置く差分である。

```cpp
#if BACKOFF_TRIGGER_GATING
  bool izanagi_gate_pass = true;
#endif
+ const uint64_t FLAGS_clocks_per_us = 0;
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
  ...
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
```

**根拠:** admission が比較するのは BEGIN..END と固定 epilogue の bytes だけである（[build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:199)）。epilogue は外部名をそのまま参照する（[axis_trigger_gating.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/axis_trigger_gating.py:51)）。`backoff(0)` は待機 threshold が 0 になり、通常は最初の反復で終了する（[backoff.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/external/ccbench/include/backoff.hh:94)、[util.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/external/ccbench/include/util.hh:88)）。

**影響:** admission は mask M を持つ gate として受理するが、実バイナリの backoff は実質無効になり、性能値と report の意味論が食い違う。

**推奨:** **scope 外。** 新しい残存限界として「call target／引数の名前解決差し替え」を記録し、prologue と呼出依存を凍結する後続タスクへ送る。現裁定の「END 後の直接再代入だけを閉じる」という限定主張自体は、この攻撃で偽にはならない。

### 所見 3 — `FileNotFoundError` と ABA の組合せは実効迂回になる

**主張:** 不正 epilogue を含む source の `SourceEvidence` を先に取得し、admission 検査時だけ対象ファイルを消し、最後の runtime gate 後に同じ不正 bytes を復元すれば検査を迂回できる。

**根拠:** `FileNotFoundError` は無条件 return する一方、他の `OSError` は拒否する（[build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:181)）。`resolve_evidence` は source digest を作れるが、この epilogue gate 自体は呼ばない（[source_digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/source_digest.py:875)）。build gateway は runtime gate の後に request metadata を確認し（[buildcache.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/buildcache.py:1273)）、source 全体の再照合は build 後である（同ファイル [1445](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/buildcache.py:1445)）。復元 bytes が最初の evidence と同じなら出口照合も通る。

**影響:** 不正 epilogue の binary と、それを正当に束縛したように見える admission receipt／cache manifest が生成されうる。

**推奨:** **scope 外。** 裁定済み B-3 と R3 の複合として起票を維持する。`ENOENT` 以外に新検査を fail-open にする `OSError` 分岐は見つからなかった。

### 境界・順序の確認結果

- `\r\n` は先頭の選択肢で 2 bytes として消費され、単独 `\r` も 1 byte消費される。`\Z` で END が EOF に達した場合、epilogue slice は短くなり必ず不一致になる（[build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:63)）。
- marker が 2 個以上なら epilogue 検査前に拒否される（同ファイル [196](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:196)）。
- 大文字小文字違い、先頭 tab は regex では marker と認識されるが、後段の逐語 block 比較で拒否される（同ファイル [204](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:204)）。
- marker が一意に存在する経路では、marker 件数検査から epilogue 検査までに受理 return はない。順序による別分岐の先行受理は確認できなかった。
- pytest は実走していない。

## 総括

最も重い問題は MUT-2 の失敗 node 集合である。  
変異は生存しないが、現記述のままでは完全集合不一致により `MISMATCH` となる。  
MUT-1 も実際には 3 parameter node が失敗するため、台帳には完全列挙が必要である。  
bytes 境界計算、CRLF、EOF、複数 marker、case、tab に受理穴は見つからなかった。  
ただし call の名前解決差し替えは R4/R5/R6 外の新しい意味論攻撃として残る。  
`FileNotFoundError` は既知の R3 と組み合わせれば実効的な admission 迂回になる。  
したがって実装の限定主張は維持できるが、変異台帳を直すまで段 6 完了とは扱えない。