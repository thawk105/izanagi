# 段 1 brief — [T-503] 変異復元耐久化 第一 slice (使い捨て専有 worktree 方式)

- wave branch: `worktree-dev-wave-t503-disposable-worktree` (起点 main = 5a322447)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree`
- job artifact: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t503-disposable-worktree/`

## 確定済みユーザー裁定

正本 = `output/insights/2026-08-06_t503-restore-durability-implementation-ruling/README.md` の
V-1〜V-6 (worklog (269) で裁定、(270) の委任一括裁定で維持)。

- **V-1 (b)** 設計 §7.1 の注記どおり「使い捨て専有 worktree 方式」を第一 slice にし、
  族一般化と consumer 契約そのものを回避する
- **V-2** V-1 に従属 (canonical state root / incarnation nonce の発行者を作らない)
- **V-3 (b)** 全 child を包含する exclusive lease / **V-4 (a)** `clean` は production verifier だけが
  発行できる sealed capability / **V-5 (a)** 未知 metadata は arm 前に拒否 / **V-6 (b)** 抽出は leaf-only
- D205 (プロトタイプ基準)。防御的堅牢化は既定で見送る。**規律 1〜6 は不変**

## 段 1 で実測した前提 (probe 4 本、逐語 = job dir の `probe_*.sh` と本節)

1. **provision コスト** — `git worktree add --detach` **10.10 s** + `submodule update --init
   external/ccbench` **1.45 s**、**134 MB**。
2. **clean 性** — 使い捨て木の `git status --porcelain=v1 --untracked-files=all
   --ignore-submodules=none` = **0 行**。harness の `_assert_clean_tracked` を通る。
3. **テストが通る** — 使い捨て木で `tools/run_tests.py orchestrator/tests/test_mutation_harness.py
   -rf` = **64 passed** (dispatch、request 893594.nqsv、26.92 s)。計算ノードから使い捨て木の path が
   解決し、submodule も見える。
4. **破棄が安全** — `rm -rf` **4.90 s** + `git worktree prune` で admin dir (`modules/external/ccbench`
   を含む) が回収される。**共有 checkout と wave worktree の submodule status・porcelain は無傷**。
   `git worktree remove` と `submodule deinit` は使わない。
5. **seam が既存** — `mutation_harness.py --repo <使い捨て木> --plan-only` が **rc=0**。
   `--repo` は既に第一級の注入 seam であり、**harness を 1 byte も変えずに** 本方式が成立する
   → U-10 (a) の「no-touch を明示解除する」は本 slice では**不要**。

## scope

- **作る**: `tools/mutation_worktree.py` — 使い捨て専有 worktree を commit から provision し、
  その中で `tools/mutation_harness.py` を走らせ、終了時に必ず破棄する wrapper。
  併せて `orchestrator/tests/test_mutation_worktree.py`。
- **作らない** (V-1 (b) の帰結として第一 slice に発火面が無い): write-ahead journal、fsync 順序契約、
  再開時修復、原子的 target 置換、canonical state root、incarnation nonce、consumer lease、
  `campaign/wal.py` primitive の抽出。
- **触らない**: `tools/mutation_harness.py` (前提 5)。
- **docs**: `DW-M05` に変異本走の実行形を書く。`docs/mutation-restore-durability-design.md` §9.2 に
  第一 slice の着手と射程を記録。`docs/README.md` の tools 地図。

## 不変条件

- 規律 2/3 を緩めない。harness の既存 gate (固定 HEAD 束縛・起動/復元時の内容比較・`flock` 単一走行・
  逐次 flush・HEAD/spec 束縛の `--resume`・signal 復元) を 1 つも外さない・迂回しない。
- 使い捨て木は **commit からのみ** 作る。未 commit 差分は測定対象にならない (`DW-M07` の anchor
  再検証と整合し、汚染入力を構造的に排除する)。
- **L-B (物理ノード死後の永続性) は `UNKNOWN` のまま。** 本 slice が主張するのは
  「変異本走が共有 checkout の bytes を触らない」だけであり、永続性・耐障害性を主張しない。
  test 名・docstring・完了記述にこの限定を残す。
- **V-3 / V-4 / V-5 は第一 slice に発火面が無い** (arm・`clean`・in-place 復元が存在しないため)。
  放棄ではなく、in-place 復元経路を作る後続 slice で復活する。この事実を design doc に明記する。

## 成果物影響 (`DW-G05`)

実装しない場合、変異本走は wave worktree の tracked bytes を in-place で書き換え続け、次の 2 経路が
残る。(a) SIGKILL・ノード死で `finally` を通らないと変異 bytes が残り、`_assert_clean_tracked` が
阻止的なので**人間が手で掃除するまで変異 campaign が止まる**。(b) 走行中に並行 consumer
(受入全走・別 session・docs 書込) が同じ木を測り、**偽の赤/緑が worklog と変異台帳
(`mutation-ledger.json` の `status` / 失敗 node) へ載る** (先例: worklog (210) の 79 failed)。
実装すると変異台帳の測定対象が使い捨て木に閉じ、両経路が消える。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** scratch root は `--scratch-root` 必須引数とし、repo 外・非 symlink・既存 directory を
  検査する。U-3 の split-brain 懸念は journal と `active` locator が存在しないため発火しない。
- **(P2)** 破棄は wrapper の `finally` + signal handler で行う。SIGKILL 時の残骸は「共有木の外のごみ」
  として起動時 stale 掃除に委ねる。生存 child が `rm -rf` と競合しても共有木は無傷。
- **(P3)** `DW-M05` は使い捨て木経由を**必須**とし、推奨に留めない。機械 gate (harness 側で
  使い捨て木以外を拒否) は本 slice では作らない (D205 プロトタイプ基準)。
- **(P4)** 本 wave の**変異 matrix は従来経路** (harness を wave worktree で直接) で走らせる。
  器具が被試験物のときの自己適用を避けるため。wrapper の健全性は専用テストに加え、
  **同じ spec を wrapper 経由でも 1 回走らせ、台帳の kill/survive が一致すること**で示す (対照走行)。

## 成果物の形

`tools/mutation_worktree.py`、`orchestrator/tests/test_mutation_worktree.py`、docs 3 箇所、
変異 matrix (従来経路) + 対照走行 (wrapper 経路)、受入全走、worklog/decisions fragment。

## 分割方針

実装子 1 本 (wrapper と test は同一所有面。分割すると contract がずれる)。レビューは 2 レンズ並列。
本 wave は変異契約 `DW-M05` を変えるため `DW-C00` の軽量版に該当せず、段 2・3 と段 6 レビュー 2 本を行う。

## 受入・実測環境

Pegasus。テストは `tools/run_tests.py` (dispatch で計算ノードへ)。受入全走は wave worktree で行う。
変異本走・対照走行は detached 経路から起動する。
