## 赤 5 件の原因

1. `test_originless_default...`  
   決定性の欠陥ではありません。`attempt_registry_prefix_sha256` は origin 投影ではなく、時刻、PID、monotonic starttime、`time_ns` 由来 UUID、report/journal digest を含む attempt registry の exact prefix を束縛します。別走行で値が変わるのが仕様です。baseline の hash 更新でもなく、推移的な揮発 leaf の分類漏れでした。

2. `test_originless_harness_rebuild...`  
   1 と同じ原因です。同一 path で再構築しても registry 内の実行証拠が変わるため、prefix hash は変わります。receipt verifier が exact prefix を再検証する性質は維持しました。

3. `test_frozen_paths...`  
   段 4 裁定どおり追加された必須引数 `prereg_generation: int` が literal signature pin に反映されていませんでした。

4. `test_attempt_event_hash...`  
   旧期待値は v2 row の vector でした。generation 束縛は v3 capability digest に入り、この縮約 vector では `schema_version` の v2→v3 が直接の変更 byte です。旧 v2 vector が従来値のままであることも同じテストに固定しました。

5. `test_attempt_registry_v2_reader...`  
   production の v1/v2/v3 明示 map は正しく、テスト helper が誤りでした。genesis を v2 に変更した後、helper が current v3 だけを rechain 対象にしたため、v3 時点の `event_sha256` が残っていました。

## 直した内容

- [test_reflux_originless_compatibility.py:205](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix1/orchestrator/tests/test_reflux_originless_compatibility.py:205) — attempt prefix hash の推移的揮発性を根拠付きで宣言し、揮発 leaf 集合へ追加。
- [test_attempt_registry_core_equivalence.py:710](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix1/orchestrator/tests/test_attempt_registry_core_equivalence.py:710) — signature pin に必須 `prereg_generation: int` を追加。pin は緩めていません。
- [test_trial_registry.py:5977](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix1/orchestrator/tests/test_trial_registry.py:5977) — rechain helper を v2/v3 の明示対象へ修正。
- [test_trial_registry.py:7043](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix1/orchestrator/tests/test_trial_registry.py:7043) — v2 の旧 vector と v3 の新 vectorを並べ、変更理由を記載。

## 実走したテスト

実装済み・未実走です。

指定の 4 ファイル走と、軽量 3 nodeid への分割走を `tools/run_tests.py` 経由で試みましたが、いずれも Pegasus の `qstat -Q` preflight が rc=1 となり、runner は rc=16、`child_started=false` で終了しました。したがって赤 5 nodeid は一件も実行されておらず、緑とは報告しません。

読取専用診断では、AST parse、公開署名、v2 hash `c87db9...`、v3 hash `b71bbd...`、`git diff --check` を確認済みです。

## 受理・拒否挙動の変化

production code は変更しておらず、受理集合・拒否集合に変化はありません。prefix hash は receipt verifier で引き続き exact 検証されます。v1/v2/v3 reader mapや既存拒否分岐も変更していません。

## 所有外への波及

tracked 差分は上記 3 テストファイルだけです。docs、`CLAUDE.md`、`AGENTS.md`、g1〜g13 condition-freeze、production module は未変更です。テスト削除、skip、xfail、fixture hash の焼き込みもありません。commit と push は実施していません。

## 総括

- 赤 1・2 は実装の非決定性ではなく、exact evidence digest の揮発分類漏れです。
- 赤 3・4 は意図した v3 契約変更に対する厳密 pin を更新しました。
- 赤 5 は production reader ではなく test rechain helper を修正しました。
- 受理・拒否挙動は不変です。
- Pegasus 障害により実装済み・未実走として引き渡します。