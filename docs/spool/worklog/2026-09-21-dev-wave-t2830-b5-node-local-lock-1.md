---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2830-b5-node-local-lock
seq: 1
title: [T-2830] B-5 本走前の実装 — B-5 mode の bench lock を driver 直前の 1 行で job 固有 scratch に移し、試走 launcher を arm ごとの submit-tree (env と qsub の cwd の両方) に対応させた。既存 3 経路は argv・環境とも不変 (コード + テスト + docs、branch worktree-dev-wave-t2830-b5-node-local-lock、変異 KILLED 8 / 過剰決定 2 は登録外)
---

## 本文

- 一次資料 = `output/insights/2026-09-21/t2830-b5-node-local-lock/README.md`。設計判断は {{D:b5-node-local-lock-and-per-job-trees}}。
- **着手条件の待ち:** 依頼の着手条件 ([T-2795] 修復 wave の land) を 08:20〜13:35 JST 待った (待ち手 4 本、修復 wave は受入と land の再試行中)。
  land を含む local main `d99c556df` から fresh worktree を作り、先行の D2205 (認可 session・結合検査) を壊さない範囲で実装した。
- **wave 開始後のユーザー裁定の取り込み:** 第 28 回裁定 D2200 項 1 (09:10 land) が T-2830 の範囲を「job body の node-local lock と job ごとの submit-tree」と
  定め、(6) で job ごとの submit-tree を確定していた。段 4 直前の裁定 inbox 再走査で拾い、brief の provisional (P2) を確定裁定へ差し替えた。
  同項の他の AI 手番 (本走用 launcher、全 arm 同一 walltime、Tier0、LLM arm の親運用、事前登録 §12 の発効束) は本 wave の外。
- **棄却した提案・所見:** 段 2 plan の `validate_submit_tree` への重複・common repo 比較、argv の NUL bytes 記録、継承値専用 test、lock 行の静的 pin は、
  段 3 の過剰・削除レンズと依頼 (検査の追加は scope 外) で不採用。brief の (P2) の根拠「lock を node-local にすると build の同時性が上がる」は誤り
  (build は bench lock の外) と段 3 で判明し、根拠を「共有 cache の claim が待機・retry なしで失敗する機序」と D2200 項 1 に差し替えた。
  段 6 レビュー 2 本は must-fix 0。test の重複 2 点と型注釈の nit は記録のみ (fix 巡 0)。
- **変異:** 事前登録 M1〜M9 + 段 6 の差し替え M10。final (dispatch) は KILLED 8 (M1〜M6・M9・M10) / MISMATCH 2 (M7・M8)。M7・M8 は静的 pin と
  メタ test にも掛かる過剰決定で、投入前に単一理由の証拠から外すと決めていた。MISMATCH の原因は親の self-run probe の node 抽出
  (ANSI 色と空白入り parametrize id) で、F71 の再発として本 wave の failures fragment に記録した。
- **セッション異常:** 変異用の独立 clone に短縮 SHA から推測した完全 SHA を渡し `nonexistent object` で拒否された (rev-parse の値で作り直し、実害なし)。
- **受入:** 段 6 の中間受入は child-green (26,964 passed / 69 skipped、赤 0、tested main `a8ae5f5d6` / tip `fa767882b`)。land 対象の最終受入は
  本記録を含む tip に対して投入する (land は tested tip の後に main の前進 merge しか置けない)。
- **非帰属赤の判定 (DW-O18):** 段 7・8 の記録 commit 後の最終受入 1 走目 (tag final2、16:24〜16:50 JST、tested tip `3a3c2c54c` = post-claim merge、
  session `91dffbeb…`) は shard-1 の `test_codex_worker_launch.py::test_t2620_orphan_mixed_is_rejected` 1 件が赤
  (`residual_observation.final_unknown_source=proc_stat_read_error`、`process_group_residual=None`; 26,964 件中 1 件)。本文は harness の `/proc` 走査が
  無関係 process の消滅と競走する既知の型で、entry 1777 が同日 02:59 に同じ test・同じ本文を非帰属と判定している (本件が同日 2 例目)。
  中間受入 tip からの差分は docs と他 wave の insight だけで、本 wave の実装差分 (job body・launcher とその test) からも到達不能。
  同一 tip で当該 node を単独再走 (dispatch 15384.nqsv) → 1 passed (5.45 秒) で非再現。負荷は 16:51 に load 3.47、受入待ち手 3 本・run_tests 8 本・codex 16 本。
  lease を release して受入を再走する (本追記の commit を含む tip)。hold 登録簿には登録しない。
- **工数:** Codex 子 7 本 (plan 1・consult 2・author 2・review 2、fix 0)、焦点走 2 本 (12 file 2,074 passed / 変更 test 単独 223 passed)、変異 final 1 本 (dispatch 11 run)。
- B-5 本走は未認可のまま。本 wave は計算ノードへ実験 job を投入していない (焦点走・変異・受入のテスト job のみ)。

## 次の一手差分

### 完了

- [T-2830] B-5 mode の node-local bench lock (driver 直前 1 行) と、試走 launcher の job ごとの submit-tree (env と qsub の cwd の両方) を実装し、既存 3 経路の driver argv と環境が変わらないことを実 shell test と変異 (M9・M10) で固定した。効果 (lock 待ちの消失・総 wall) の実測は次の試走か本走の台帳で見る。
  remaining: none
  base: d833959e086e2a203489620c8004111035bc30f71880bdc4c19ba2874221baf7
