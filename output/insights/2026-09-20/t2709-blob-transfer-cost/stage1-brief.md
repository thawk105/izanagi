# 段 1 brief — [T-2709] 受入 fixture の index 化を自己完結で「下限」へ届かせる経路の費用実測

- wave: `dev-wave-t2709-blob-transfer-cost`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2709-blob-transfer-cost`、base = local main `b7f970dfa` (乖離 0)
- 起点: 台帳 entry 1554 の T-2709 本文、D2068 (C 案は「効果の符号が未確認」で本 wave では採らない)、一次資料 `output/insights/2026-09-16/t2559-acceptance-floor-t080/`
- 日時は `date` から: 2026-09-20 07:20 JST 着手

## 研究前進 (1 行)

土台。受入全走 (D2067: 最遅 shard-0 の t080 e2e が 300 秒超) の床にある fixture base 構築の `git add -A` を、正しさ検査を 1 bit も緩めずに縮められるかの費用を、受入と同じ計算ノード local `/tmp` で対比較して確定する。全 research wave の受入往復に効く。

## scope (確定)

- 本題の費用実測だけ。fixture 本体 (`orchestrator/tests/test_s8b_oracle_driver.py`) は変えない。新 gate・台帳・一般化は足さない。
- probe は Codex `role=author` が書き、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/` へ保全し repo へは入れない (先例 T-2708: `output/insights/2026-09-17/t2708-fixture-config-h-gap/probe-source.md`)。実装差分ゼロ → 変異 matrix は免除、受入全走は免除しない。
- 計測は計算ノード generic dispatch (`tools/pegasus/dispatch_compute.py --task generic`)。login では測らない (D2068: login の外乱 28 倍)。
- 成果物: `output/insights/2026-09-20/t2709-blob-transfer-cost/` (README + 段の逐語 + probe-source + result JSON)、spool fragment (worklog、decisions)。結論は「食わない → 採用再検討の裁定パッケージ」または「食う → 不採用で閉じる」の二値。採用そのものは本 wave でしない。

## 確定済みユーザー裁定・既裁定 (逐語は `verbatim/`)

- D2068: A (whitelist) / B (alternates) は不採用 (受理集合・観測が変わる)。C (必要 blob だけ移送) は効果の符号未確認なので採らない。「効果を先に測り未確認のまま実装しない」。
- D2067: 受入短縮の対象は shard-0 の t080 e2e。D357 / D1260: 受入 wall の改善主張は同一 tip の逐次 3 走以上の中央値、10% 未満は変化なし・採用しない。D2086: fixture の proto 化 (branch `impl-dev-wave-t080-accept-speed`) は −5.7% で採用せず保存。
- production 側の不変条件 (現行コード、本 wave で触らない): `t080_freeze_migration._capture_head` は `objects/info/alternates` の存在を拒否する (M:643)。`_git_env` は `GIT_OPTIONAL_LOCKS=0` (M:565)。発行経路は `_worktree_status` = `git status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` を `_capture_draft_basis` (M:1833) と `_validate_repin_report_git` (M:2012) で走らせ、clean を要求する。

## 不変条件 (規律 2 — 緩めない)

- 移送経路は fixture の `.git` に alternates を作らない (production が拒否するので自動的に不採用)。blob だけを移送し commit / tree は移送しない (ancestry 観測 `missing-commit` を変えない、D2068 (B) の理由を回避)。
- index の stat を偽装しない: `--assume-unchanged` (CE_VALID) や `core.checkStat` 等で `git status` の変更検出を弱める変種は計測対象に入れない (fixture は破壊的変異を検出させる負例を持つ)。
- 各方式の結果は A (現行 `git add -A`) と **tree OID が byte 一致**、production 形の `git status` が空、`git fsck --connectivity-only` が alternates 無しで緑、`rev-list --objects HEAD` の件数一致、を満たしたときだけ費用を比較する。満たさない試行は失格 (数値を採らない)。

## 覆す新事実 (brief 前の一次資料照合、段 4 で再裁定)

- **T-2709 起票文の「削減分 79〜191 秒」は login 実測であり、計算ノードには当てはまらない。** D2086 の一次資料
  `output/insights/2026-09-16/accept-speed-t080-session-copy/README.md` §2-1 (bnode050、直列 1 process、cProfile) では
  base 構築 118.2 秒の内訳が「`output/` 複製 52.9 秒 (45%) / 発行 subprocess 53.3 秒 (45%) / **`_run_git` ×11 (init・config ×4・
  submodule add・checkout・add -A・commit) 9.5 秒 (8%)** / `orchestrator/` 複製 2.5 秒」。§2-2 (5 key) でも git 55 回 47.5 秒 (base あたり 9.5 秒)。
  したがって計算ノードで index 化を 0 にしても **base 1 回あたりの削減上限は 9.5 秒未満** (add -A + commit は 11 操作の一部)。
- 同資料: 実 repo (Lustre) → node の `output/` 複製 (23k file、614 MB) は copytree 37.4 秒 + stat 9.4 秒。移送経路も同じ Lustre から
  24k object を読むので、この桁 (数十秒) になれば削減上限 9.5 秒を食う。**符号は依然として未測定** (pack は圧縮済み約 165 MB・file 数は pack 21 本で、複製とは I/O の形が違う)。
- base→test 複製 (`copytree`、`.git` 込み) は test 1 本 2.85〜3.0 秒 (§2-1、§2-2)。(P6) の副次量に対応する。
- 親の再裁定案: 計測は予定どおり行う (author 1 + 計算ノード job 1 本、安価)。ただし裁定パッケージでは「削減分」を計算ノード A の実測値
  (上限 9.5 秒) で述べ、D1260 の 10% wall 基準 (≈33 秒) に対する写像は模型として別記する。login の 79〜191 秒は判断に使わない。

## 親の provisional 裁定 (攻撃対象)

- (P1) **stat 無しの index は production で毎回再ハッシュされる。** `update-index --index-info` で作った index は stat が空。production は `GIT_OPTIONAL_LOCKS=0` なので `git status` が index を書き戻さず、発行経路の 2 回 + テスト側の全 `status` が 24k file / 614 MB を再ハッシュする。したがって自己完結経路は明示 `git update-index --refresh` (= 1 回のハッシュ走査) を含めて初めて production 等価であり、D2068 の「0.61 秒」はこの費用を含まない。**自己完結の真の下限 = blob 移送 + 1 回のハッシュ走査** で、それより下に届く経路は無い (親の主張、反証歓迎)。
- (P2) **実用候補は C1 = 移送 + `git add -A`。** object が pack に既在なら `add` は圧縮・loose 書込を飛ばし (`write_object_file` の freshen)、ハッシュ走査と stat 記録だけ行う。ignore 規則も現行と同じ経路を通るので tree は A と byte 一致 (config.h の 1 件ずれも同じ)。fixture 側 object 集合 = A と同一 (loose でなく pack にあるだけ)。C2 = 移送 + index-info + write-tree + commit-tree + 明示 refresh は「下限の再現」であり、production 設計としては path→OID の信頼問題が残る (本 wave は費用だけ測る)。
- (P3) **削減分の基準は login の 79〜191 秒ではなく、計算ノード local `/tmp` での A の実測。** 受入は TMPDIR 未設定 → 計算ノードの xfs `/tmp` に base を組む (conftest.py 冒頭、`_t080_stub_free_e2e_repo` は `tempfile.gettempdir()`)。login の値は判断に使わない。
- (P4) **移送の費用は「実 repo (Lustre 上の共有 object store: pack 21 本 480 MB + loose 5,914) から 24k blob を読む」費用が支配的**で、cold (初回) と warm で違う。受入では shard ごと (別 node) に cold で始まる可能性が高いので、初回試行を別に報告する。
- (P5) **判定規則 (事前登録)。** 主指標は base 1 回あたりの「index 化〜commit〜最初の production 形 status」までの合計 (A: add + commit + status1、C1: 移送 + add + commit + status1、C2: 移送 + index-info + write-tree + commit-tree + refresh + status1)。5 round の A/C1/C2 交互試行で、**C1 の中央値 < A の中央値 かつ 5 round 中 4 round 以上で C1 < A** なら「食わない」→ 裁定パッケージ。それ以外は「食う (または符号未確定)」→ 不採用で閉じる。cold 初回の C1 が cold 初回の A を上回る場合はその事実を裁定パッケージに明記する (採用の再検討条件に含める)。10% 基準 (D357/D1260) は受入 wall の話なので本 wave の per-base 比較には適用せず、裁定パッケージで wall への写像を「模型」として別に書く (主張しない)。
- (P6) **副次量**: 各方式の `.git` を `shutil.copytree(symlinks=True)` する所要と `du` (テストごとの base→test 複製が `.git` を含む: `_t080_stub_free_e2e_repo` の copytree)。loose 24k file と pack 1 本で差が出うる。主判定には使わない。

## 計測設計 (probe の仕様、author への射影元)

1. **土台 1 回**: 先例 T-2708 の `hold_session` 形で held module から `_build_t080_stub_free_e2e_repo(work/"base", issue_receipt=False)` を 1 回呼ぶ (計算ノードで 163.8 秒の先例値)。work-root は **計算ノードの local `/tmp` 配下** (job 内で `mkdtemp(dir="/tmp")`)、結果 JSON だけ job dir (Lustre) へ書く。login (hostname `pegasus0*`) では本走を拒否。
2. **参照**: builder が作った `.git` を `.git-ref` へ退避 (mv)。参照 tree OID = `.git-ref` の HEAD tree。参照 index 一覧 = `git ls-files -s` (mode / OID / path、gitlink 160000 を含む)。移送する OID 集合 = 参照 index の blob OID (gitlink 除く) を実 repo (`--source-root` の worktree、`git cat-file --batch-check`) で実在確認したもの。実在しない OID (期待: `.gitmodules` など fixture 固有 bytes) の件数と path を記録する。
3. **試行ごとの再初期化 (timed 外)**: `rm -rf .git` → `git init -q` → `gc.auto=0` / user.name / user.email (builder と同じ) → `.git/modules` を `.git-ref/modules` への symlink にする (submodule の gitfile `external/ccbench/.git` が `../../.git/modules/external/ccbench` を指すため)。`.gitmodules` は worktree の通常 file として残っている。
4. **方式 (timed 区間は各 subprocess の wall、`perf_counter_ns`)**:
   - A: `git add -A` → `git commit -q -m "T080 migration basis" -m "AI-Agent: none"` → status1 (production 形、`GIT_OPTIONAL_LOCKS=0`、harden `-c` 3 つ) → status2。
   - C1: 移送 (`git -C <source> pack-objects --stdout [設定] < oids | git index-pack --stdin` を fixture 内で、pack を `.git/objects/pack/` へ) → `git add -A` → commit → status1 → status2。
   - C2: 移送 → `git update-index --index-info` (参照 index 一覧を逐語投入、gitlink 含む) → `git write-tree` → `git commit-tree` → `git update-ref HEAD` → `git update-index --refresh` (明示、timed) → status1 → status2。**C2 の index-info の入力は参照 index 一覧を使う** (production の path→OID 写像の設計は scope 外、C2 は下限の再現)。
   - 各試行後 (timed 外): tree OID = 参照と一致、`git status` (production 形) が空、`git count-objects -v`、`git rev-list --objects HEAD | wc -l` が参照と一致、`git fsck --connectivity-only` 緑、`objects/info/alternates` 不在、`du -s .git/objects`、(P6) の copytree 所要。
5. **移送設定の事前実験 (main 試行の前、timed)**: `pack-objects` の既定 (delta 探索あり、`--threads` 既定) と `--window=0 --depth=0` (delta 探索なし、既存圧縮 bytes の再利用のみ) を交互に 3 回ずつ。**main 試行の C1/C2 は中央値が小さい方の設定を使う** (事前登録の規則、結果を見て変えない)。pack size も記録。
6. **順序と回数**: round r = 1..5 で A → C1 → C2 の順 (round ごとに巡回: r1 A C1 C2、r2 C1 C2 A、r3 C2 A C1、…) で位置効果を散らす。合計 15 試行。初回 (cold) は別報告。
7. **ハッシュ走査の参照値 (timed、1 round に 1 回)**: `git hash-object --stdin-paths` (書込なし) を参照 index の path 全件に対して走らせた所要 — (P1) の「1 回のハッシュ走査」の実費。
8. **出力**: JSON 1 本 (`--out`) に環境 (hostname、`git --version`、fstype of work-root、`nproc`、loadavg)、設定、全試行の生値、failures、limitations。集計 (中央値・min/max) も含めるが生値を必ず残す。`--selftest` (login 可、小さい合成 repo で A/C1/C2 の tree 一致と失格判定の正負例) と `--hold-session-only` を持つ。
9. **書かないこと**: source-root (worktree) へ 1 byte も書かない。`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定しない。`GIT_*` を継承しない。

## 実アンカー表 (読む場所)

| 項目 | path:line |
|---|---|
| base 構築 (現行 `add -A` + commit) | `orchestrator/tests/test_s8b_oracle_driver.py:1417-1536` (`_build_t080_stub_free_e2e_repo`)、`:1527-1528` が `add -A` / commit、`:369-386` が test 側の git env (`GIT_OPTIONAL_LOCKS=0`、production と同形) |
| output 複製 | 同 `:827-880` (`_copy_git_visible_output`) |
| shared base と base→test copytree | 同 `:900-1023` (`_T080SharedBases.get`、`_t080_stub_free_e2e_repo` の `shutil.copytree(base_root, root, symlinks=True)`) |
| production の git env / harden / alternates 拒否 / status | `orchestrator/campaign/t080_freeze_migration.py:559-574`、`:636-650`、`:1790-1793`、`:1833`、`:2012` |
| held module の import 制約 | 同 test file 末尾 `enforce_held_functions(...)`、先例 probe の `hold_session` |
| dispatch generic の clean env / read-only submission mount | `tools/pegasus/dispatch_compute.py:155-160`、`:354`、`:1309-1315` |
| TMPDIR 方針 | `orchestrator/tests/conftest.py:1-30` |

## 並列分割

- 段 3: consult 1 本 (2 レンズ、read-only)。段 2 plan は省く (軽量版、DW-C00)。
- 段 5: author 1 本 (probe 1 file)。親が login で `--selftest` と `--hold-session-only` を実走 → 計算ノードへ generic dispatch 1 本 (walltime 01:00:00)。
- 段 6: 実装差分ゼロなので fix は probe の欠陥時のみ。review 1 本 (read-only、probe と結果 JSON と README 草稿)。

## 模擬/実の差

- 本 wave の「実 repo」= wave worktree (`--source-root`) であり、その object store は共有 `/work/1/SFC/tanab/izanagi/.git`。受入でも各 wave の worktree から複製するので同一構造。
- cold cache は作れない (drop_caches 不可)。初回試行を cold の代理として報告するに留める。
- 5 key の base を worker が並列に組む受入との写像 (per-base → wall) は模型であり、本 wave は wall を測らない。
