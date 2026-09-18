# [T-2290][T-2291] DW-O23 / DW-O27 収容 wave — 一次資料 (2026-09-18)

- wave: branch `worktree-dev-wave-t2290-o23-o27-docs`、worktree `.claude/worktrees/dev-wave-t2290-o23-o27-docs`
- 起点 main: a0ccb8ad9 (09:18 JST の local main)。09:31 JST に e9e92f435 を ff-only で取り込み (dev-wave docs に差分なし)
- 種別: docs のみ (`docs/dev-wave/operations.md` の DW-O23 / DW-O27)。子ゼロの軽量版 (`DW-C00`)。変異 matrix は
  実装面差分ゼロで免除 (`DW-S04`)
- 裁定の出所: D782 (D730 の手順を AI が適用し、上限引き上げ時だけ報告)、D730 (既存記述の削減 → 独立 3 例なら例外 →
  それでも無理なら上限引き上げ)

## §1 着手前実測 (段 1)

| 項目 | 実測 | 出所 |
|---|---|---|
| L1 unique footprint (常時読む節の合計) | 10,622 / 10,625 bytes (残り 3) | `tools/check_docs.py` の `_check_dev_wave_layer_budget` を予算 0 で呼ぶ probe (`verbatim/` には置かず job dir、値は本表) |
| DW-O27 (L2 単節) | 981 / 1000 bytes | 同上 |
| DW-O23 の層 | 段 9 の無条件節 → L1 (`DEV_WAVE_L1_STAGE_KEYS` に「段 9」) | `tools/check_docs.py` 899 行付近 |
| exact literal pin | DW-O23 / DW-O27 は対象外 (pin は O18 / O25 / O26 / O28 / C01 と入口・routing) | `DEV_WAVE_EXACT_VISIBLE_SECTIONS` |
| land helper 文字列 | `tools/dev_wave_land.py` は operations.md 全体で exact 1 件かつ DW-O23 内 | `tools/check_docs.py` 6393 行付近 |
| rc=22 の現物 | `RC_IDENTITY = 22`、cwd の inode が wave worktree の fd と一致しないと `cwd must be the exact wave worktree` | `tools/dev_wave_land.py` 53 行・1353-1354 行 |
| log/receipt の現物 | `_external_new_file_preflight`: repo 内・親 dir 不在・symlink・**既存 file** で `RC_USAGE = 2`。log と receipt が同一 path でも rc=2 | `tools/dev_wave_wait.py` 2475-2547 行 |
| 既存被覆 | dev-wave docs (入口 + 4 leaf) に `rc=22` / `cwd must be` / `log-file` の記述なし (DW-O19 の `--out` / `--attempt-out` は変異 harness の別物) | grep |
| 実測例 (D730 例外の材料、使わなかった) | rc=22 cwd: archive 0903 (T-2290 原文) 1 例。log rc=2: archive 0903・0915 の 2 例 + insight t907-recovery | grep |

編集面照合 (09:35 JST、job dir の overlap_scan.py で 190 worktree の branch tip を merge-base と `git diff --quiet` 比較):
operations.md を base から変えている稼働 wave は `worktree-dev-wave-t2447-lens-p2-p6` のみ (冒頭 1 行「該当節を操作直前に
読み、停止条件を迂回しない。」の削除、DW-O23 / DW-O27 に不接触、同 worktree での L1 実測 10,623)。依頼文の t2498
(entry 1638) と cleanup-si-routing (entry 1641) は land 済み。

不変条件: 本 wave は L1 を 1 byte も増やさない (Δ0)。合流後 = 10,623 + 0 ≤ 10,625。

## §2 裁定 (段 4、軽量版で段 2・3 は省略)

- (P1)「意味等価の縮約で予算内に入る」は dry-run で成立 → D730 段階 1 で終了。3 例例外・上限引き上げに進まない。
- 縮約の原資は自分の節内の冗長語だけ。安全義務は 1 つも削らない (DW-O27 末尾段落の「新節登録時に合成 fixture との
  整合を同じ commit で確認する」義務は本文を短くして保持)。

## §3 変更 (段 5、親編集、commit 32db53133)

| 節 | 追加した文 | 縮約した原資 | bytes |
|---|---|---|---|
| DW-O23 | `cwd=wave worktree必須（rc=22）。` (2 行目) | 「監査列の範囲は…で固定」→「監査列は…に固定」、「数え直すと」→「数えると」、「再照合して…ff-onlyし、…foldする」→「再照合し…ff-only、…fold」、「一度だけ」→「1度だけ」、「返さず、0件」→「返さず0件」、「双方向束縛した」→「双方向束縛の」、「再試行する」→「再試行」 | 1,036 → 1,036 (Δ0) |
| DW-O27 | `` `--log-file`/`--receipt-file`は既存 file で rc=2。再投入は新 path にする。 `` | 「codex の wave slug とは別でよい」→「codex の slug と別でよい」、末尾段落「整合性を同じ commit で確認する（`DW-O26` の精神を checker 変更にも適用。怠ると多数のテストが連鎖的に失敗する — T-1458 実測、320 件）」→「整合を同じ commit で確認する（`DW-O26` の精神。怠ると test が連鎖的に赤 — T-1458、320 件）」 | 981 → 998 |

編集後の実測: L1 10,622 (不変)、L1.5 9,696 (不変)、DW-O27 998、`python3 tools/check_docs.py` 違反なし (rc=0)、
`tools/dev_wave_land.py` 文字列 1 件。

## §4 検査 (段 6)

- 焦点走の対象 = operations.md を参照する consumer test 3 file (`test_check_docs.py`、`test_codex_worker_launch.py`、
  `test_dev_wave_launch_authority.py`、`DW-O26` の参照関係で列挙。3 file とも suite を再帰起動しない)。
- **焦点走 1** (計算ノード 5433.nqsv、09:36-09:37 JST、未 commit の docs 差分のまま投入): 116 failed / 739 passed /
  3 skipped、rc=1。赤は全件 `tools.dev_waves.launch_authority.AuthorityError: docs/dev-wave/operations.md: working tree が
  authority commit と異なる` (`snapshot_authority`、launcher を subprocess 起動する test 群)。**自分起因**
  (未 commit の docs 差分)。F225 の同型で、焦点走にも効く点を再発として記録。log: `verbatim/s6-focus-run-1-uncommitted-docs.log`。
- **焦点走 2** (計算ノード 5437.nqsv、commit 32db53133、09:41 投入・09:48 JST 終端): **855 passed / 3 skipped、rc=0**。
  skipped 3 は growth hold (`docs_bytes` 軸: `test_dev_wave_model_pins_accept_current_docs_contract`、
  `test_normative_exact_section_pins_accept_real_repo`、`test_real_repo_clean`) で、hold 下の検査は走っていない
  (緑と読まない)。同じ検査は `python3 tools/check_docs.py` 直接 (rc=0、commit 前後で各 1 回) を実効 gate として実測した。
  log: `verbatim/s6-focus-run-2-committed.log`。
- 全史 provenance 監査 (`python3 tools/check_ai_provenance.py`、commit 32db53133 後): 11,274 件、新規違反なし、rc=0。
- 受入全走: land 経路で最終 tip に対して 1 走 (結果は land の受領証と job dir)。本 README には実測前なので書かない。

## §5 変異 matrix

免除 (実装面差分ゼロ、`DW-S04`)。docs 側の drift は `tools/check_docs.py` の L1 / L2 予算・land helper 文字列の
exact 1 件検査が直接捕まえる (§3 の実測値)。

## §6 限界・次の一手候補

- DW-O27 は 998 / 1000 で満杯に戻った。次に同節へ足す wave は再び縮約か D730 の例外判定が要る。
- t2447 が先に land すると L1 は 10,623 になる (本 wave の Δ0 は保つ)。後続で L1 に足す wave の残余は 2 bytes。
- 段 8 候補: F225 再発追記 (焦点走の launcher 系 test も authority 拒否で赤になる)。DW-O18 / DW-O26 への「docs/dev-wave
  編集は焦点走前に commit」の追記は、両節が exact pin かつ予算満杯・実測 1 例のため D730 で実施しない。

## §7 工数

- codex 子 0 本 (docs-only、`DW-C00` の既定軽量版)。
- 親の実測: 層予算 probe 3 回 (起点 / 取り込み後 / 編集後、t2447 木で 1 回)、pin と tool 現物の grep、編集面照合 (190
  worktree)、check_docs 直接 2 回、焦点走 2 本 (計算ノード)、全史 provenance 監査 1 回。
- 段 9 の受入・land・自己撤去は最終報告と次 wave の worklog へ。

## verbatim

- `verbatim/handoff-through-stage6.md` — 段 6 までの専用 handoff (段 1 brief・段 4 裁定を含む)
- `verbatim/s6-focus-run-1-uncommitted-docs.log` — 焦点走 1 (赤 116、自分起因)
- `verbatim/s6-focus-run-2-committed.log` — 焦点走 2 (緑)
