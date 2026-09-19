# 段 1 brief — [T-2778 改訂] wave が作った子 worktree を段 9 で自分で撤去する恒久対策

作成: 2026-09-19 21:45 JST。wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2778-child-worktree-cleanup`
(branch `worktree-dev-wave-t2778-child-worktree-cleanup`、base = local main `2ba400087`)。

## 研究前進 (土台)

- 止めているもの: 全 wave の段 9・`/next-tasks`・`/cleanup-branches` の固定費。2026-09-19 19:59 の実測で残骸 worktree
  194 本 (1 本 ≈ 734 MB / 26k file、t2638 §4.1)、うち dirty 117 本、branch なし container・未統合 probe/fix branch を含む。
  T-2783 は起動時に 212 本の handoff を走査した。ユーザー裁定 (2026-09-19)「ワークツリーが残って next-tasks / cleanup-branches
  のたびに費用が増え続けている。恒久対策が要る」。
- 最小差分: (a) 子木作成時に job dir の manifest へ exact path を登録、(b) `tools/dev_wave_cleanup.py` に manifest 束縛の
  子木撤去 mode、(c) DW-S05-A / DW-O28 の手順、(d) D703 拡張 + D2148 項 9 (iii) supersede の決定 fragment。
- 完了判定: 本 wave 自身の author 子木 (dirty を含む) を段 9 で新 mode が撤去する (正例 1 件、t2638 §9.3 の「通る正例ゼロ」を解消)。
  負例 3 型 (manifest 外 path・占有中・未統合 author commit) が rc≠0 で止まる。

## scope

- 実装面 (Codex author、D95): `tools/dev_wave_cleanup.py` (子木 mode)、manifest の登録 CLI、`orchestrator/tests/test_dev_wave_cleanup.py`、
  `tools/check_docs.py` の `DEV_WAVE_DW_O28_SECTION_LITERAL` 更新と `orchestrator/tests/test_check_docs.py` の `_SYNTHETIC_DW_O28_SECTION`。
- docs (親): `docs/dev-wave/workers.md` DW-S05-A (作成時登録 + fix 巡の author 木再利用)、`docs/dev-wave/operations.md` DW-O28
  (子木撤去 + 回収 wave の旧 manifest)、必要なら DW-O20 (lock と登録を同所で)。spool fragment: decisions 1 (D703 拡張・D2148 項 9 (iii) supersede)、
  worklog 1。insight `output/insights/2026-09-19/t2778-child-worktree-cleanup/`。
- scope 外: 周期 sweep、stale lock の推定判定、`/cleanup-branches` の変更、既存残骸 (2026-09-19 に 194 本撤去済み・残 19 本) の処置、
  `tools/mutation_worktree.py` の自己登録、他 gate・台帳・一般化。

## 確定済みユーザー裁定

- 2026-09-19: D703 の例外を「wave が作成時に job dir の manifest へ exact path で登録した子木」まで広げ、D2148 項 9 (iii) を supersede する。
  preflight = 占有なし + author commit が main から到達可能または wave 木へ統合済み。dirty は job dir へ patch/tar 退避してから撤去。
  manifest 外 path は拒否。周期 sweep・stale lock 推定は作らない。
- 維持: D703 の `git branch -d` のみ・`-D`/force/remote/一括禁止、F26 (`git worktree remove`/`deinit` 不使用)、D2044 項 16 (起動器の終端 commit は記録のみ)、
  DW-O28 の unlock 統合、T-2777 の hardlink 修正。

## 既存被覆 (純増だけを書く)

- D2044 項 16 (実装子の作業木は終端時に branch へ記録、起動器が実装済み) は維持。項 18 (親の生存に依存しない回収経路は作らない) も
  維持 — 本 wave の (4) は人間が起動する回収 wave の手順であり、自動回収経路ではない。
- t2638 裁定パッケージ (R1〜R8) の R1 を今回のユーザー裁定が「是」とし、R2 は「C (着地証明) + 限定 B (退避)」に相当する。
  t2638 §9 の前提 7 件のうち、2 (`_assert_clean_and_head` が子に通らない) と 3 (通る正例ゼロ) と 4 (所有外差分の行き先) を本 wave で解く。
- 2026-09-19 の t2484 wave は同型の author 木撤去を script (`cleanup-author.sh`) で個別実行済み (退避 layout の先例)。
- 純増 = manifest (作成時 exact path 登録) と、それに束縛された子木 mode。

## 不変条件

1. 撤去対象は manifest に exact path (realpath 一致) で登録された子木だけ。位置 (`.codex/worktrees/` 等) や名前で子と判定しない (t2638 §9.5)。
2. 占有あり (`check_worktree_occupancy` が unoccupied 以外) は撤去しない。判定不能も拒否 (絶対規律 2 の同型: 判定不能を受理へ倒さない)。
3. 内容を失わない: committed 内容は「HEAD reflog の全 commit が参照 ref (`refs/heads/main`、任意で wave tip) から到達可能」か
   「所有 path の全 blob が参照 ref の同 path と一致」のいずれかを要求。どちらも不成立なら拒否し、不一致 path を列挙する。
   所有外 path の差分・未追跡・dirty は job dir の証拠 dir へ `tracked.patch` / `untracked.tar.gz` / `status.txt` / `head-sha.txt` /
   `branch.txt` として退避してから撤去 (2026-09-19 残置撤去と同じ layout)。証拠 dir は空でなければ拒否 (上書き禁止)。
4. 子 branch は撤去後も残す。削除は tip が `refs/heads/main` の祖先のときだけ `git branch -d` (D703 と同規則)。それ以外は残して報告。
5. wave 本体の撤去契約 (`_classify` a〜e、admin binding、hardlink 拒否) は変えない。既存テストの期待値を変えない。
6. 受入時間: 新規テストは tmp repo の fixture で数秒級。実 repo を読む test を増やさない (long-tests-must-not-hold-real-repo-read-locks)。

## (P) 親の provisional 裁定 — 攻撃対象

- (P1) 統合証明は「祖先性 ∨ 所有 path の blob 一致 (参照 ref = `refs/heads/main`、`--integration-ref <sha>` で wave tip を追加可)」。
  実測: 稼働中 author 子木 4 本は親 tip の祖先でなく、所有 path の blob は親 tip と一致、`author-result.md`/`fix-result.md` だけ不一致。
  → manifest に `owned_paths` を持たせ、所有外 path は退避扱い。purpose ∈ {author, fix} で `owned_paths` 空は登録拒否。
- (P2) manifest = `<job dir>/child-worktrees.json`、schema `izanagi-dev-wave-child-worktrees/v1`、entry = `path`(絶対・realpath)、`purpose`
  (author|fix|mutation-container|probe|scratch)、`branch`(null 可)、`base_sha`、`owned_paths`、`registered_at`。同 path の再登録は entry 置換 (fix 巡の branch 変更)。
- (P3) CLI: `tools/dev_wave_cleanup.py register-child …` / `remove-child --main-worktree <M> --manifest <F> --child-worktree <P> --evidence-dir <D> [--integration-ref <sha>]`。
  1 呼出し 1 子木。既存の 4/5 option 形 (wave 本体) は不変。rc 体系 (2/20/21/22/30) を共有。
- (P4) DW-O28 の順序: land 後、main worktree から子木を manifest 順に撤去 → 最後に wave 本体。回収 wave は旧 wave の manifest path を同段で追加実行。
- (P5) DW-O28 は L2 単節 989/1000 bytes、DW-O20 996/1000。D782 → まず既存記述を縮約して収容し、不可なら上限引き上げを報告。
- (P6) 新 D 番号は fold まで未定なので docs 本文は番号を書かず「D703 の例外を manifest 登録済み子木へ広げた裁定」と書く (living docs の実在 D 検査)。

## 変更面 (実アンカー)

| file | 現行アンカー | 変更 |
|---|---|---|
| `tools/dev_wave_cleanup.py` | `Args`(L39)、`_parse_argv`(L130、argv 長 8/10 固定)、`_assert_unoccupied`(L484)、`_assert_branch_safety`(L652)、`_classify`(L685)、`_bind_admin`(L835)、`_remove_admin`(L1012)、`_preflight`(L1065)、`_remove_verified_tree`(L1230)、`_mutate`(L1272)、`main`(L1411) | 子木 mode 追加。既存関数を再利用し、wave 本体経路の挙動は不変 |
| `orchestrator/tests/test_dev_wave_cleanup.py` | 1820 行、tmp repo fixture、`test_real_occupancy_scan_rejects_live_process_cwd` は collection contract が名指し (改名禁止) | 正例・負例の node 追加 |
| `tools/check_docs.py` | `DEV_WAVE_DW_O28_SECTION_LITERAL`(L628)、`DEV_WAVE_L2_SECTION_BYTES_MAX=1_000`(L360) | literal 追従 |
| `orchestrator/tests/test_check_docs.py` | `_SYNTHETIC_DW_O28_SECTION`(L189)、合成 decisions の `D703. placeholder`(L1311) | fixture 追従 |
| `docs/dev-wave/workers.md` | DW-S05-A (783 bytes、L1.5) | 作成時登録・fix 巡の再利用 |
| `docs/dev-wave/operations.md` | DW-O28 (989 bytes、L2 exact pin)、DW-O20 (996 bytes) | 子木撤去・回収 wave |
| `docs/spool/decisions/`, `docs/spool/worklog/` | README の形式 | fragment 各 1 |

## 実測と模擬/実の差

- 稼働 19 木の編集面重複: commit 差分 (main...branch) と dirt の両方で上記 file の hit 0 (t2484 は `mutation.md` のみ)。
- 現存子 branch 9 本の統合状態 (`integration_probe.py`): author/fix 4 本 = 祖先性 False、所有 blob 一致 (3/5, 3/5, 2/4, 2/3)、
  不一致は報告 `.md`。probe 3 本 = 一致 0。scratch/freeze 2 本 = 親 tip と全一致 (1 本は祖先)。→ (P1) の述語は実環境で到達可能。
- DW-O09 pin 閉包: `dev_wave_cleanup` の参照は `tools/check_docs.py`(DW-O28 literal)、`orchestrator/test_selection_contract.py`(path)、
  `test_pytest_collection_config.py`(node 名)、`test_branch_rescue_ledger.py`(docs 文言)、`docs/unreachable-object-ledger.md`、`docs/failures.md`。
  whole-file sha256 pin は grep で 0 件。凍結 artifact・oracle・proof chain には触れない (DW-O08/O10 不成立)。
- DW-O11 成立 (directory 削除): 既存の `_remove_verified_tree` + admin gitdir 削除を再利用、`git worktree remove`/`deinit` 不使用。
- DW-O13 成立 (受理形を増やす既存述語の改訂): 入力 field は `git worktree list --porcelain` (path/HEAD/branch/detached/locked)、
  occupancy payload (`status`/`occupants`/`issues`)、`git rev-parse <ref>:<path>` の blob id、manifest (本 wave が定義)。値域は上記実測。
- check_docs baseline rc=0 (2026-09-19 21:40 JST、wave worktree)。
- 模擬なし。dogfood: 本 wave の author 子木を manifest に登録し、段 9 で新 mode で撤去する。

## DW-G05 成果物影響

certified 選択・レポート・台帳の値・受理集合・参照は変わらない (開発運用の土台)。放置時の影響は費用 (走査・掃除の所要) のみ。

## 分割方針

軽量版ではなく全 9 段 (削除権限の拡張 = 正しさ防壁・受理集合に触る)。段 5 は Codex author 1 単位 (tool + tests + check_docs literal + fixture)。
親は docs 本文 (DW-S05-A / DW-O28 / DW-O20) と fragment。段 6 は敵対レビュー 2 本 (過剰・削除レンズ固定 1 本 + 正しさ境界 1 本)。
受入は `tools/dev_wave_wait.py acceptance --lease-optional` (Pegasus 計算ノード dispatch、runbook `docs/pegasus-runbook.md`)。
