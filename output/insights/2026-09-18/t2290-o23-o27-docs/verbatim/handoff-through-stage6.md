# [T-2290][T-2291] DW-O23 (land cwd 要件 rc=22) / DW-O27 (再投入時の log・receipt 新 path) 収容 wave
- 目的: docs のみ。`docs/dev-wave/operations.md` の DW-O23 へ `tools/dev_wave_land.py` の cwd 要件 (rc=22) を、DW-O27 へ再投入時に log/receipt を新 path にする義務を、D782 / D730 の手順で予算内に収容する
- 状態: 作業中
- 最終更新: 2026-09-18 09:25 JST
- 基準コミット: e9e92f435 (local main を 09:31 JST に ff-only で取り込み。当初 base は a0ccb8ad9)、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2290-o23-o27-docs`、branch `worktree-dev-wave-t2290-o23-o27-docs`

## 完了した中間成果
- 起動: worklog 末尾 (1642) 読了、handoff dir は README のみ、DW-C00/DW-STOP/DW-S01/DW-G01〜05/DW-O20/DW-C01/skill-self-improvement 読了
- 事実: DW-O23 / DW-O27 は check_docs の exact literal pin 対象外 (pin は O18/O25/O26/O28/C01 と入口/routing)。DW-O23 は段 9 U → L1 (10,625)、DW-O27 は C のみ → L2 単節 1000
- 事実: t2498 wave は land 済み (1638)、cleanup-si-routing も land 済み (main tip fold)

## 未完の作業と次の一手
- submodule 初期化 → check_wave_startup fresh → L1 残余 実測 → 稼働 wave の operations.md 編集面照合 → 段 1 brief

## 落とし穴・気づき
- `git worktree add` で EINTR warning (.gitattributes 不在 file、実害なし、tree は clean)

## dev-wave 改善候補
- (なし)

## 段 1 brief (T-2290 / T-2291) — 09:30 JST (date 実測)
- 研究前進 (土台): land の cwd 違反 (rc=22) と受入 log の既存 file (rc=2) は wave の段 9 / 受入を 1 回ずつ空振りさせた実測 (archive 1238-1239 の wave)。手順欠落を DW-O23 / DW-O27 に収容し、CC 合成 wave の受入・land が手順で止まらないようにする。完了判定 = 2 節に義務が入り check_docs 緑、L1 footprint が base 10,622 を超えない、DW-O27 ≤ 1000。
- scope: docs のみ (`docs/dev-wave/operations.md` の DW-O23 / DW-O27 の 2 節)。実装面ゼロ → 子ゼロの軽量版 (DW-C00)、変異 matrix は実装面差分ゼロで免除。仮想リスク向け gate・検査・台帳・一般化は足さない。
- 確定裁定: D782 (D730 の手順を AI が適用し、上限引き上げ時だけ報告)、D730 (既存記述の削減 → 独立 3 例なら例外 → それでも無理なら上限引き上げ)。
- 不変条件: 規律 2 不変。`tools/dev_wave_land.py` 文字列は operations.md 全体で 1 件 (DW-O23 内、check_docs 6393 行)。DW-O23 は L1 (段 9 U) なので L1 footprint を増やさない (Δ ≤ 0 → t2447 との合流後も ≤ 10,625)。DW-O27 は L2 単節 ≤ 1000。exact pin 対象外 (O18/O25/O26/O28/C01 でない) → Codex author 不要。縮約は意味等価に限り、原資は DW-O23 / DW-O27 内の冗長語。
- 純増: (1) land 起動時の cwd = wave worktree 自身 (rc=22)。(2) acceptance の `--log-file` / `--receipt-file` は既存 file だと rc=2、再投入は新 path。既存被覆: dev-wave docs に 0 件。DW-O19 の「`--out` と `--attempt-out` を新 path にする」は変異 harness の別物。
- 一次資料: dev_wave_land.py:1353-1354 (`RC_IDENTITY = 22`、cwd inode ≠ wave fd)、dev_wave_wait.py:2475-2497 `_external_new_file_preflight` (repo 内・親 dir 不在・symlink・既存 file → rc=2)、2534-2547 log と receipt の同一 path も rc=2。
- 編集面照合 (09:35 JST 実測、全 worktree の branch tip を merge-base と比較): operations.md を変えている稼働 wave は t2447-lens-p2-p6 のみ (preamble 1 行削除、DW-O23/O27 不接触)。t2498・cleanup-si-routing は land 済み。
- (P1) 提案本文は意味等価の縮約で予算内に入る。入らなければ D730 の 3 例判定 (rc=22 = 1 例 [0903]、log rc=2 = 2 例 [0903, 0915] + insight t907-recovery)。
- 成果物: operations.md 差分、insight `output/insights/2026-09-18/t2290-o23-o27-docs/README.md` (bytes 収支・実測)、spool fragment (worklog)。分割: 親のみ。
- 実測環境: check_docs は login (worktree 内で直接)。関連 test は test_check_docs の実 repo 走査が growth hold で skip → check_docs 直接を実効 gate として実測。受入全走は land 経路 (計算ノード)。

## 段 4 裁定 (軽量版: 段 2・3 省略、所見なし) — 09:31 JST 以降
- 実装する (docs のみ、親が編集)。変異 matrix は実装面差分ゼロで免除 (DW-S04)。受入全走は免除せず land 経路で実施。
- (P1) は dry-run で成立: D730 段階 1 (既存記述の削減 = 節内の意味等価な縮約) だけで収容できる。3 例例外・上限引き上げは不要。
- DW-O23: 「cwd=wave worktree必須（rc=22）。」を 2 行目に追加。原資 = 節内の冗長語 (「の範囲」「数え直す→数える」「して→し」「foldする→fold」「返さず、→返さず」「一度→1度」「束縛した→束縛の」「再試行する→再試行」)。dry-run 1036 → 1036 bytes (Δ0)。`tools/dev_wave_land.py` は 1 件のまま。
- DW-O27: 「`--log-file`/`--receipt-file`は既存 file で rc=2。再投入は新 path にする。」を追加。原資 = 末尾段落の縮約 (義務「新節登録時に合成 fixture との整合を同じ commit で確認」は保つ) と「wave slug とは→slug と」。dry-run 981 → 998 bytes。
- t2447 (未 land、L1 10,623 実測) との合流後 = 10,623 + 0 ≤ 10,625。
- 検査: check_docs 直接、probe で L1/L2 再実測、`git diff` 目視、実 repo 走査 test (growth hold で skip を実測して記録)。

## 段 5・6 進捗 — 09:42 JST 時点 (date 実測は各行)
- 段 5: 本文を書き込み、check_docs 違反なし (rc=0)、probe 実測 L1 10,622 (不変)・DW-O27 998。commit 32db53133 (trailer role=author scope=docs、--message-file rc=0、全史監査 11,274 件新規違反なし)。
- 段 6 焦点走 1 (計算ノード 5433.nqsv、09:36-09:37): 116 failed / 739 passed / 3 skipped。赤は全部 `docs/dev-wave/operations.md: working tree が authority commit と異なる` (snapshot_authority) = 未 commit の docs 差分を launcher 系 test が拒否 → 自分起因、F225 の同型 (焦点走の test でも起きる型は未記載 → 段 8 候補: F225 再発追記)。log は insight verbatim/s6-focus-run-1-uncommitted-docs.log。
- 段 6 焦点走 2 (計算ノード 5437.nqsv、commit 後、09:41 投入): 待ち中。

## dev-wave 改善候補
- (1) F225 再発: 親の docs/dev-wave 直接編集を未 commit のまま焦点走に掛けると、codex 子だけでなく launcher を起動する test 群 (test_codex_worker_launch / test_dev_wave_launch_authority、116 node) が同じ authority 拒否で赤になる。routing 1 (既存 F へ再発追記)。DW-O18/O26 は exact pin + 予算満杯なので追記しない (D730)。
