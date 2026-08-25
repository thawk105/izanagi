---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1354-off-arm-noninterference
seq: 1
---

## 新規

### {{F:rejected-artifact-adopted-by-content-check}}. 不採用の子成果物を内容検査の緑を理由に採用へ回した [防壁の射程誤認] [手順漏れ]

- 事象: 8 子中 6 子が `evidence_status=invalid` / `accepted=false` / `launcher_rc=1` になった。
  親は保全した `attempt-0001.output.md` を `-o` の path へ複製し、
  `tools/check_codex_output.py` が rc=0 を返したことを根拠に段 2・段 3・段 6 の
  成果物として採用した。F540 が明示的に禁じている操作である。
- 根本原因: 親が 2 つの検査を同じものと見なした。`check_codex_output.py` は成果物の
  **内容**が形式を満たすかだけを見る。launcher の `accepted` は成果物を生んだ
  **実行そのものの証跡**が健全かを見る。前者の緑は後者の赤を打ち消さない。
  F540 は「内容検査が緑でも launcher の赤を迂回することになる」と 1 行で書いているが、
  親は F540 を読む前に採用を済ませていた。段 7 で F217 系を調べる過程で初めて気づいた。
- 恒久対応: {{D:offarm-noninterference-claim-scope}} と同じ規律 — 検査の届く範囲より広い
  結論を出さない。手順としては F540 の回避 (別 `--job-id` での 1 回再投入) を先に行い、
  再投入が通らない子の成果物は「保全して読むが唯一の根拠にしない」に留める。
  本 wave では気づいた時点で段 6 の関門 3 子を再投入し、2 子が受理された。
- 再発検知: 待ち手が rc=70 を返したら、成果物を複製する前に receipt の
  `attempts[].accepted` を読む。`false` なら F540 の再投入を先に実行する。
  `check_codex_output.py` の rc=0 を採用の根拠にしない。

### {{F:resubmitted-prompt-goes-stale-after-tree-advances}}. F540 の再投入で、prompt が指す一次資料が現行 bytes と食い違った [ドリフト]

- 事象: F540 の回避に従い段 6 の敵対レンズを別 `--job-id` で再投入したところ、受理はされたが
  NO-GO の理由が「レビュー入力として指定された差分 bundle が現行 commit と一致せず、
  現行 nodeid と検出力修正が欠落している」になった。実装の semantics に新しい blocker は
  無かったのに、段 6 の署名対象を確定できないという判定が返った。
- 根本原因: F540 は「**同じ prompt を**別の job-id で 1 回だけ再投入する」と定める。
  しかし本 wave では初回投入から再投入までの間に fix が入り commit も済んでいた。
  prompt が絶対 path で指す integration patch は初回時点の bytes のままで、
  同じ prompt が指す source file は現行 tip になっていた。子は両者の食い違いを正しく検出した。
- 恒久対応: 再投入の直前に、prompt が指す一次資料 (patch・差分 bundle・前段成果物) を
  現行 tip から作り直す。prompt 本文が変わらなくても、指し先の bytes は更新する。
  {{D:offarm-noninterference-claim-scope}} と同じく、検査に渡す入力が主張の対象と
  一致していることを先に確かめる。
- 再発検知: 再投入した子が「入力が現行と一致しない」型の NO-GO を返したら本エントリ。
  再投入前に `git diff` の出力を patch file へ取り直したか確認する。

### {{F:fresh-worktree-first-acceptance-is-deterministically-red}}. 新規 worktree の初回受入全走は `_real_output_snapshot` 系が決定的に赤になる [テスト代表性] [計測汚染]

- 事象: 受入全走が 2 回連続で `12 failed / 15,922 passed / 60 skipped` と**完全に同一**の結果に
  なった。赤は `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系 11 件と
  `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`
  の計 12 件で、junit の差分は `('dir', 'runs/pytest-launcher-failures')` の entry 増加と
  `output/runs` の mtime 変化だった。F136 の既知形と署名は一致するが、
  **既知形が定める「単独再走と受入再投入の両方で消える」に当てはまらなかった。**
- 根本原因: `orchestrator/tests/test_codex_worker_launch.py` の
  `_FAILURE_ARTIFACT_ROOT = <repo>/output/runs/pytest-launcher-failures` は、
  launcher テストが**全件緑でも**全走中に作られる (本 wave の実測では launcher テスト 227 件が
  失敗 0 件で、それでも root が新規作成された)。長命な checkout ではこの dir が過去の走行から
  既に存在するため entry 集合も mtime も変わらない。**新規に作った worktree だけが
  「走行中に新規作成される」条件を満たす。** main の checkout と別 wave の worktree を実測して、
  どちらも当該 dir を既に持つことを確認した。
- **既存記録の訂正**: F136 の既存例が再投入で消えたのは、1 回目の走行が作った dir が残って
  2 回目の前提が変わったからである。本 wave の親は 1 回目のあとに当該 dir を「汚染源」と見なして
  除去し、**2 回目の前提を自分で作り直してしまった**。1 回目の是正が逆効果だった。
- 恒久対応: 未実施。新規 worktree で初回の受入全走を投入する前に
  `mkdir -p output/runs/pytest-launcher-failures` で定常状態へ揃える。
  これは追跡外の scratch directory であり、検査の期待値を一切変えない。
  機械化するなら `DW-O20` の worktree 作成手順か `tools/check_wave_startup.py` へ置くのが筋だが、
  受入基盤の所有 wave の判断に委ねる ({{T:fresh-worktree-acceptance-scratch-dirs}})。
- **是正を実測で確認した。** `mkdir -p output/runs/pytest-launcher-failures` を行ってから
  投入した回で、当該 12 件は**すべて消えた** (12 failed → 0 failed、`15,937 passed`)。
  仮説ではなく実測で確定した是正である。
- 再発検知: 受入の赤が `_real_output_snapshot` 系だけで、junit 差分が
  `runs/pytest-launcher-failures` を指し、**再投入で消えない**なら本エントリである。
  worktree の作成時刻と当該 dir の有無を確かめる。既存 dir を削除してはならない。

## 再発

### F136

- **再発: 2026-08-25 (同日 5 例目)** — 既知形と署名は一致するが**再投入で消えない**変種を
  {{F:fresh-worktree-first-acceptance-is-deterministically-red}} に分離した。
  既存の再発検知条件「単独再走と受入再投入の両方で消える」は、
  **走行が作った dir が残ることを暗黙の前提にしている**。その dir を除去すると条件が崩れる。

### F540

- **再発: 2026-08-25** — 1 wave で 8 子中 **6 子**が `evidence_status=invalid` になった
  (段 2 plan、段 3 レンズ A、段 6 レビュー 2 本、fix、焦点再レビュー)。
  受理されたのは段 5 実装子と段 3 レンズ B の 2 子だけである。
  **F540 の再発検知手順どおり既知 2 原因を実測で否定した。** F217 (web 検索イベントの重複キー) —
  8 子すべての `attempt-0001.events.jsonl` を重複キー拒否 parser で全行 parse し、
  失敗 0 行。文字列 `web_search` は受理された子の events にも現れるため指標にならず、
  不採用の焦点子には 1 件も現れなかった。F223 (非 NFC) — 8 子すべての成果物が NFC 正規。
  launcher-diagnostics にも `conditions_met` は空で、限界超過ではない。
  **F540 の回避 (別 job-id での再投入) は 3 子中 2 子で成功し、1 子は 2 回目も不採用**だった。
  再投入が成功した 2 子は初回と同じ結論を返した (F540 の「同じ結論を返さない」は本 wave では
  再現せず、代わりに {{F:resubmitted-prompt-goes-stale-after-tree-advances}} の型が出た)。

### F106

- **再発: 2026-08-25** — **4 度目**。変異 matrix の本走中に、親が段 7 の spool fragment 2 本を
  worktree へ書いて untracked file を増やした。`tools/mutation_harness.py` の preflight が
  `runner/test 実行前に untracked file を検出` で `rc=2` 停止し、防壁は正しく働いた。
  実害は fragment を repo 外へ退避して `--resume` で続きから走らせる一手間である。
  親は本 wave の handoff に同じ注意を書いていない状態で踏んだ。過去 3 回と同じく
  「dispatch するから worktree を触ってよい」ではなく「投入から結果取得までは worktree を
  触らない」が正しい読み方である。今回の再発は `--resume` が既存の `--attempt-out` を
  要求する点も併せて実測した (新 path を渡すと `--resume + --attempt-out には既存の
  symlink でない通常 file が必要` で停止する)。

- **再発: 2026-08-25 (同日 5 度目)** — 今度は**受入全走の走行中**に、親が段 7 の fragment 2 本を
  worktree で編集した。受入は preflight の `prerun-clean` で `rc=70` 停止し、
  テストを 1 件も走らせずに 1 回分を丸ごと失った。親は 1 分以内に気づいて編集を repo 外へ
  退避し木を戻したが、既に投入済みの走行には間に合わなかった。
  **変異本走と受入全走のどちらでも同じ規律が要る**という読み方を、同日 2 度踏んで確かめた。

### F480

- **再発: 2026-08-25** — 同じ nodeid
  (`test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`)
  が別 wave の受入でも 1 件だけ赤になった (`1 failed / 15,937 passed / 60 skipped`)。
  台帳の再発検知手順どおり同 file の単独走で確かめ、**233 passed / 16.54 秒 / rc=0 で緑**だった。
  本 wave の差分 (projected provider とその consumer test) から当該 file への到達経路は無い。
  再投入で消えた。同日 2 例目であり、`Thread.join(<秒>)` の上界が高並列下で破れる族が
  引き続き受入 1 回分を消費している。

### F277

- **再発: 2026-08-25** — 段 4 で事前登録した変異 8 件のうち 5 件が、実装前の静的検討では
  帰属可能に見えたのに、段 6 の敵対レンズが「import 時 assert・既存 guard・既存テストに
  mask される」と静的に反証した。さらに実測すると、集合だけを変える変異は
  **MISMATCH ですらなく pytest の collection error** になり、失敗 node が 1 つも出ずに
  `PARSE_ERROR` で harness が止まった。両層変異へ組み直して初めて node が観測できた。
  **単層変異の「帰属できるはず」は、実効 gate の判定順を追わない限り信用できない。**
