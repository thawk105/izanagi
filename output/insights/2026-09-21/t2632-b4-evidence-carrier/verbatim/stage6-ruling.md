# [T-2632] 段 6 裁定 (2026-09-21 21:1x JST、親)

入力: 焦点走 f1 (`focus-f1.log`、`15633.nqsv`、12 failed / 4689 passed / 15 skipped / 167.68 s)、段 6 レビュー A `codex/s6-review-A.md` (NO-GO)、
B `codex/s6-review-B.md` (NO-GO)。いずれも check_codex_output rc=0。fix 前の統合 snapshot = `integrated-snapshot-ec6459863.patch`。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 | 放置時の成果物影響 (DW-G05) |
|---|---|---|---|---|
| A1 | 束縛 (outcome ごとの attempt 選択・refs の境界) | refuted | — | — |
| A2 | 非 B-4 走行でも `canonical_b4_proposal_sha256` を必ず計算するため、canonical 化できない proposal (例 `planner.uncertainty` に NaN) で以前は通った走行が止まる。B-5 slot では拒否 sidecar / rc=3 を経由せず漏れる | **real、must-fix** | 採用 (下記 §2.1) | 非 B-4 / B-5 の走行が消え、B-5 の失敗台帳の記録経路が変わる |
| A3 | `.corrupt.*` による停止は原本不在の時だけ | real、should-fix | 採用 (docstring を実挙動へ限定。挙動は plan §4 どおりで変えない) | 説明の過大 |
| A4 | P4 docstring の「bootstrap は再実行拒否」は WAL 履歴がある場合に限る | real、should-fix | 採用 (docstring を限定) | 説明の過大 |
| A5 | 入力隔離 (実装) | refuted | 動的証拠は fix 後の test で取る | — |
| A6 | caller | refuted | — | — |
| A7 / B6 | 新設 test 11 件が検査対象へ届く前に落ちる (`mkdir` 8、`STAGE_VERIFY_DONE` 未 import 2、admitted campaign 無し 1) | **real、must-fix** | 採用 | attempt 束縛・破損停止・入力隔離が未検証のまま「検証済み」と記録される |
| A7 / B4 | 既存 `test_p3_b4_closed_critic.py::test_launcher_positive_uses_real_factory_and_real_base_main_for_commit` の評価 stub が、commit の attempt ID と対応 start を持たない certified を返す | **real、must-fix** | 採用。**本番の attempt 検査は緩めない** (両レビュー一致)。stub の出力を実物の形 (同一 attempt の start / commit を WAL に記録) にする fixture 修正。assert は変えない | launcher → base main → checkpoint の既存回帰検証が失われる |
| B3 | hash=null 単独 test が既存 assertion と重複 | real、nit | 不採用 (成果物影響なし、fix の範囲を広げない) | 実行コストのみ |
| A8 | skip 15 件の理由が log に無い | 情報 | 次の焦点走は `-rfs` で理由を出す | — |

## 2. fix の内容 (fix 子 1 本、所有 3 file)

所有: `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_b4_closed_critic.py`。
caller 側 (実装子 B) は所見 0 のため fix しない。

1. **A2:** `main()` の hash 計算で `B4ProtocolError` が出たとき、mode を問わず `initial_proposal_sha256 = None` として走行を続ける
   (受理集合を変えない。null は「この呼出しでは canonical identity を提供できない」の既存の意味)。
   根拠: 既存で canonical hash を要求するのは B-4 bootstrap の registry 束縛 (`require_b4_proposal_registry_binding`) だけで、bootstrap はそこで
   先に拒否されるので本分岐へ届かない。B-4 continuation と非 B-4 は canonical hash を要求していないので、ここで停止させると受理集合が縮む。
   null の entry は後段の適格性判定で「出所なし」として不適格側に数えられる (安全側)。B-5 slot の rc も sidecar も変わらない。
   docstring に「canonical 化できない proposal は hash=null」と書く。
   回帰 test: 非 B-4 で `planner.uncertainty` に NaN を持つ proposal が従来どおり評価へ進み、entry の hash が null になる (実 `main` を通す)。
2. **A3 / A4:** `_load_provenance` と `_append_provenance_entry` の docstring を実挙動へ限定する (挙動は変えない)。
3. **A7 / B6:** 新設 test の fixture 不具合 3 系統を直す (既存 `reports/` を作り直さない、`STAGE_VERIFY_DONE` 等の import、入力隔離 test に
   lock と WAL を持つ admitted campaign を用意)。assert は弱めない。
4. **A7 / B4:** 既存 launcher positive test の評価 stub が返す certified の `records` に、同一 attempt の `build_start` と `commit` を WAL に書いた上で
   その attempt ID を載せる (実物の certified と同じ形)。**test の assert・期待 rc・期待される commit 内容は変えない。**

## 3. 変異の追加登録 (DW-M01、fix 前)

| ID | 対象 | 一行変異 | 期待 kill | 向き |
|---|---|---|---|---|
| S15 | main の hash 計算 | `B4ProtocolError` を捕えず再送出する (§2.1 の分岐を外す) | 非 B-4 NaN proposal の回帰 test | 正 (過剰拒否) |

## 4. erratum (2026-09-21 21:2x JST、焦点走 f2 の後)

焦点走 f2 (`15636.nqsv`、commit `eee7e4ba3`): 1 failed / 4701 passed / 15 skipped / 166.08 s。skip 15 件は理由を `-rfs` で確認し、
既存の growth hold・template patch 未適用の条件付き未実走・実機 build 環境の未設定・Python 3.11 要件で、本 wave と無関係。
赤 1 件 = `test_base_provenance_duplicate_reuses_selected_attempt`: fixture が採用 commit の**後**に同 variant の別 attempt (start + abort) を足しており、
既存の `_resolve_duplicate` (本 wave で不変) は最後の終端が abort の variant を certified 重複と見なさず `aborted` を返す。
つまり「採用 commit より後に同 variant の start がある」状態は duplicate 経路で実在せず、段 4 の S4 (最新 start へ置換) は実在状態で等価になる。

- **S4 の再照準 (DW-M01):** 「commit 由来 ID を同 variant の**最初の** start の ID に置換」へ変える。期待 kill は同じ test。
- **fixture の修正 (fix 子 A2、test のみ):** 失敗した先行 attempt (start + abort) を採用された certified attempt の**前**に置き、
  entry の `build_attempt_id` が採用 commit の ID で、`wal_refs` が先行 attempt の record を含まないことを assert する。assert は弱めない。

### 4.1 §4 の診断の訂正 (2026-09-21 21:3x JST、焦点走 f3 の後)

焦点走 f3 (`15639.nqsv`、commit `f5049bf6d`、test_p3_s4_loop.py 単独): 1 failed / 654 passed。先行 attempt を前に置いた fixture でも
`_resolve_duplicate` は `aborted` を返した。**§4 の「採用 commit の後の abort が原因」という診断は誤り。** 実際の原因は、helper
`_base_selected_commit` が書く `verify_done` の payload に `anomalies` が無く、`artifact_admission.require_persisted_certified_commit` が
「persisted COMMIT verify anomalies must be exact int zero」で certified 認定を拒否したことである (f2 の赤も同じ原因)。
「採用 commit の後に同 variant の start がある状態が duplicate 経路で実在しない」は検証していない主張として撤回する。
S4 の再照準 (同 variant の最初の start へ置換、先行の失敗 attempt を前に置く fixture) は、成功の前に再試行が入る実在の形を覆うので維持する。
fix 子 A3 (test のみ) が helper の `verify_done` payload に `"anomalies": 0` を足す。

### 4.2 残る拒否理由の特定 (2026-09-21 21:3x JST、焦点走 f4 の後)

焦点走 f4 (commit `3bfbecfca`): 同じ 1 件がなお `aborted`。`_resolve_duplicate` は拒否理由を握りつぶすので、親の読み取り probe
(`probe_duplicate_reject.py`、job dir) で同じ fixture を組み直接呼んだ: `ArtifactAdmissionError: persisted COMMIT receipt evidence does not match WAL verifies`。
helper は `verify_done` を tag `legacy` / `s2` の 2 件書くが、`commit_receipt_support.log_receipted_commit` を既定の `tags=("legacy",)` で呼んでいた。
修正案を当てた probe (`probe_duplicate_fixed.py`) で certified 認定が通り、`_resolve_duplicate` = `duplicate`、選ばれた attempt = 採用 commit、
refs 4 件 (先行 attempt の 2 件を含まない) を確認した。fix 子 A4 (test のみ) が helper の呼出しに `tags=("legacy", "s2")` を足す。

## 5. 変異の実行方法の登録 (2026-09-21 21:3x JST、走行前)

**drift probe の実測:** 独立 clone (`mutation-source`、commit `eee7e4ba3`) で E1 (等価) を `mutation_worktree.py` の注入で走らせ、
対象 `test_p3_s4_loop.py` + `test_p3_b4_closed_critic.py` (既知赤 1 件を `--deselect`) で baseline PASSED・E1 は **150 node が落ちた** (MISMATCH)。
内訳 = test_p3_s4_loop.py 103 / test_p3_b4_closed_critic.py 47、うち本 wave の新設 test 22 node (drive / main を通す test)。
一覧 = `drift-nodes-e1.txt`。これらは変異の内容と無関係に落ちるので KILL の根拠にしない。

**割り振り:**

| 群 | 変異 | 方法 | 対象 |
|---|---|---|---|
| 注入群 L | S3・S4・S5・S6・S7・S8・S9・S13・E1 | `mutation_worktree.py` (dispatch)、`test_p3_s4_loop.py -k` で drift を受けない新設 test だけを選ぶ | 期待 node は drift 一覧と交わらない |
| 注入群 C | C1〜C5 | 同上、`test_p3_b4_prerun_caller.py` 全体 (caller は closure 外で drift なし) | |
| commit 群 | S1・S2・S10・S11・S12・S14・S15 | `run-commit-group.sh` (下記)、`test_p3_s4_loop.py -k "provenance"` | 検出 test が drift 群にしかない変異 |

注入群 L の E1 は、選択した test 集合の中で drift が無いことの対照を兼ねる (SURVIVED を期待)。

**commit 群の harness (DW-M05 の同等検査の登録):** `run-commit-group.sh` + `apply_mutant.py` (job dir、repo に入れない)。
- 固定 base: 引数の base commit に detach し、clean (`git status --porcelain --untracked-files=no` 空) でなければ中止。
- 注入: spec の replacements を累積適用し、各 old が累積後に exactly 1 回だけ現れることを assert (DW-M04)。変更 file 集合が spec の file 集合と
  一致しなければ中止。変異 1 件を 1 commit (独立 clone 内だけ、main へは入らない) にしてから dispatch する。
- 単一走行: 変異を 1 件ずつ直列に走らせる (同一 clone の dispatch は直列、pid file)。最初に baseline (無変異) を走らせ、赤なら中止。
- 記録: 変異ごとに rc・log・`IZANAGI_FAILURE` 行から抽出した失敗 node を保存。
- 復元: 毎回 base へ detach し直し、終了時に clean を確かめる。主 tree と wave 木には触れない。
- 期待 node: 初回を probe (期待 node 空) として観測し、完全集合を登録 (erratum) した後に final を走らせ、完全一致だけを KILLED とする (DW-M08)。

### 5.1 焦点再レビューを受けた割り振りの訂正 (2026-09-21 21:4x JST)

焦点再レビュー (`codex/s6-focus.md`、受理 rc=0): 段 6 の real 所見 5 件 (A2・A3・A4・A7/B6・A7/B4) はすべて closed。NO-GO の理由は変異設計の 1 件。

- **F1 (real、must-fix、採用):** S13 (評価前検証の削除) と S8 (破損で `{}` を返す) は、drive を通す `test_base_provenance_corrupt_report_stops` の入口停止を外し、
  評価 stub より前の `ident.ensure_campaign_identity` の live binding 照合へ到達させる。E1 で drift が出なかった node でも、この 2 変異の時だけ drift に届く。
  → **S13 を commit 群へ移す。S8 は注入群 L に残し、L の選択から `corrupt_report_stops` を外して、`_load_provenance` を直接呼ぶ
  `test_base_provenance_invalid_entry_is_quarantined` で検出させる。**
- **F2 (real、nit、採用):** `make_mutation_spec.py` の S4 の comment に撤回済みの説明 (§4) が残る → §4.2 の根拠へ直す。

L の probe (`mutation-linjprobe`) は訂正前の選択 (`corrupt_report_stops` を含む) で走行中で、途中停止は孤児 job の危険があるので完走させる。
L の final の選択は `corrupt_report_stops` を除いた集合とし、期待 node は probe の観測を final の選択へ制限したものを登録する (erratum として記録)。
final で完全一致しなければ、その変異は KILL と数えず原因を調べる。S13 は commit 群で単独の probe を走らせてから commit 群の final に含める。
