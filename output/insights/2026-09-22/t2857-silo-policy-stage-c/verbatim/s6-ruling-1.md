# 段 6 裁定 1 巡目 — [T-2857] (2026-09-22 20:4x JST、親 = Claude manager)

入力: 焦点走 f2 (17975.nqsv、8 failed / 4770 passed / 8 skipped、log = job dir `focus-2.log`)、
レビュー A (`codex/s6-review-A.md`、NO-GO must-fix 3)、レビュー B (`codex/s6-review-B.md`、NO-GO must-fix 2)。
統合 snapshot = `codex/snapshot-integrated-1.patch` (eef04f5a7..23acbfa60)。

## 1. 所見と赤の裁定

| # | 出所 | 内容 | 判定 | 扱い |
|---|---|---|---|---|
| F1 | f2 赤 3 件 + A1 + B1 | `silo_policy_coverage._build_variant` (348 行) の gate 呼出しが macro の loop 内にあり、既存の define / build sink 交差検査がゼロ回 loop の経路を gate 未通過と数える | real (静的受入条件との不整合。実行時の gate 迂回ではない) | fix。gate の呼出しと成功確認が sink を支配する構造へ driver を局所整理する。検査の緩和・除外登録は禁止 |
| F2 | f2 赤 3 件 (condition gate `[SILO_POLICY_VARIANT]` の configure-failed) | 試験用 fixture `orchestrator/tests/condition_gate_test_support.py` の `_OPTIONS` に `CCBENCH_SILO_POLICY_VARIANT` の cache 変数と universal definition が無い | real | fix。fixture に既存 cache 経路 macro (`SORT_VARIANT` など) と同じ形で足す |
| F3 | f2 赤 1 件 (`test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty`) | coder 本文を materialize する入口 (`render_hole` の呼び手) の閉集合 {`p3_s4_loop.quarantine`} に `silo_policy_coverage.prepare_policy` が増えた | real | fix。閉集合は広げない。`prepare_policy` は既存の `p3_s4_loop.quarantine(sub, body, marker_id=axis.MARKER_ID, source_rel=axis.SOURCE_REL, write=False)` で DiffQuarantine と描画を行い、effect gate・構文検査・単独 TU compile をすべて通った後にだけ書き込み・build する |
| F4 | f2 赤 1 件 (`test_screening_condition_requests_cover_exact_define_specs`) | `screening_driver._CONDITION_DEFAULTS` に新 macro 3 個の既定値が無い | real | fix。既存 entry と同じ形で 3 個の既定値 (0) を足す。screening の既存の挙動 (既定値を使う経路) が変わらないことを確かめる |
| F5 | A2 + B2 | prefix unlock 変異の方策が裁定 §3 の `maxwait` でなく `abort0` (親の C1 投げ文の書き違い)。上限出口の unlock 漏れを独立に検証していない | real | fix。同じ変異 patch を 2 方策で走らせる: `abort0` (lock hook が即 abort を返すので action-abort 出口だけに到達、試行 0 は上限に届かない) と `maxwait` (常に retry を返すので上限出口だけに到達)。方策の構成で出口を分けることを case 名と結果 JSON に書く。どちらも正常骨格の同方策が対照 |
| F6 | B4 | 正常対照 5 走 (3 hook + wrong-reason の対照 = `focus/focus` と同構成、no-reload の対照 = `focus/retry` と同構成) が重複 | real | fix。重複対照は同じ観測 (`focus/focus`・`focus/retry`) を参照する対応表にし、build を減らす。対照の判定式は変えない |
| F7 | B5 | smoke 入口の timeout 経路の接続試験が無い | real | fix。`test_silo_policy_smoke_entry.py` に 1 件足す |
| F8 | A4 | 成功通知の後の状態継続の観測に正の到達条件が無い (成功前の `0 == 0` の比較で満たせる) | real | fix。probe に「同じ worker で成功 commit が 1 回以上あった後の比較」の一致・不一致を別に数え、driver は `focus/focus` でその一致 > 0・不一致 0 を要求する |
| F9 | A 変異表・B3 | 段 4 裁定 §4 の「hook の実呼出しを 1 か所消すとその照合だけが赤」は誤り (符号の連動で赤は複数照合)。C2 の赤集合の完全一致判定は正しい | real (親の裁定の誤り) | 実装変更なし。insight と decisions fragment で訂正する (各 hook の赤集合は互いに異なるので、どの hook が外れたかは一意に識別できる) |
| F10 | A3 | 事前登録した変異 M-CHK-EMPTY は必須集合の一致判定を外しても後段 (`checks == derived`・到達検査の KeyError) が拒否を保つ過剰決定で、単一理由にならない | real | 変異登録から外し、冗長 gate として記録する (DW-M03)。実装変更なし |
| F11 | B「足りない」 | `patches/README.md` に新 patch の適用順・診断用途・裸 macro の説明が無い | real | 親が段 7 で書く (docs) |

## 2. fix の分割

一枚岩で 1 本の Codex fix 子に渡す。理由: F1・F3・F5・F6・F8 が同じ driver `silo_policy_coverage.py` とその test に集中し、F8 は probe patch の変更で積み重ねの厳密適用 (機構変異 patch の文脈) にも波及するため、分けると producer / consumer 契約が割れる。F2・F4・F7 は小さい。

## 3. 変異の事前登録の更新 (DW-M01、fix 前)

- 削除: M-CHK-EMPTY (F10、冗長 gate)。
- 追加:
  - M-POSTCOMMIT: `focus/focus` の判定から成功後比較の到達要件を外す → 成功後比較 0 の観測が合格になる。kill 点 = `test_silo_policy_coverage.py` の成功後比較の test (fix 子が書く、名前は `test_focus_requires_post_commit_state_observation`)。
  - M-GATE-DOM: driver の gate 呼出しを macro の loop 内へ戻す → 既存の define / build sink 交差検査 3 node が赤。
  - M-INGRESS: `prepare_policy` を `render_hole` の直呼びへ戻す → 既存の `test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty` が赤。
- 残りの 11 件 (M-LEX・M-TYPE・M-SELFINIT・M-RETURN・M-ASSIGN・M-RHSLIT・M-TU-GLOBAL・M-TU-MACRO・M-CHK-NORW・M-SMOKE-SKIP・M-API-SYNC) は段 4 のとおり。期待 KILLED node は fix 統合後の commit で login self-run か初回 dispatch probe で完全集合に固定する (DW-M08)。

## 4. 計算の残予算

- 使用済み (Elapse): 焦点走 f-a1 27 秒・f-b1 27 秒・f-c1 10 秒・f2 228 秒 = 292 秒 (0.08 node 時間)。
- F6 で coverage の build は 26 → 約 21 に減り、F5 で prefix unlock が 1 走増える。承認上限 2.4 node 時間に対し、見積り上側を超える見込みはない (段 4 §7 の上側 2.4 のうち、coverage 再走 1 回を含めても残る)。
