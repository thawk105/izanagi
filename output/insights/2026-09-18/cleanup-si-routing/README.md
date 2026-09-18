# cleanup-branches 2026-09-17 実走の自己改善候補 4 件の routing — 段 9 の子 worktree unlock、rescue gate の timeout、guard の同居拒否、F26 の現行実体、自己撤去 tool の hardlink 拒否

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-cleanup-si-routing (branch `worktree-dev-wave-cleanup-si-routing`、軽量版)
- 起点: ユーザー依頼 (2026-09-17 の `/cleanup-branches` 実走が final で報告した候補 4 件を `docs/skill-self-improvement.md` の routing で処理する)。実走の job dir `~/.claude/jobs/1de496c3/tmp/` は本 wave 開始時点で消失しており (job 削除で掃除済み)、実走の件数 (locked 14 本中 10 本が stale、17 本並列 101 秒 / 10 本 161 秒、候補 17 本・27 commit 中 10 件 checker-timeout、225 秒) は依頼文が final 報告を引用したものだけが出所である。本資料では、現在の repo で再実測できた事実と、依頼文にしか無い数値を分けて書く。
- 基準: local main `d2ebef7a4` (wave 開始時、clean)

## 0. 結論

| # | 候補 | 行き先 (routing) | 状態 |
|---|---|---|---|
| 1 | locked の古い lock (land 済み wave の Codex 子・変異 container の lock が残る) | `docs/dev-wave/operations.md` `DW-O28` へ「`DW-O20` で lock した子 worktree は同段で unlock する」を等価縮約で統合 (routing 3)。**撤去の自動化は統合しない** — D703 (自動削除は自 wave の exact な worktree path と branch ref だけ) の例外外なので §3.1 の裁定パッケージへ (routing 2)。cleanup-branches 側の stale lock 判定も同じパッケージ | docs 済み (989 bytes、単節予算 1000)。`DW-O28` は `tools/check_docs.py` の exact literal に pin されているため Codex author / fix が pin を追随 (§2) |
| 2 | F26 の「1 worktree ずつ削除」は launcher で不要 | `docs/failures.md` F26 へ supersede 追記 1 行 (routing 1、新 F は作らない) | spool fragment 済み |
| 3 | rescue gate の checker-timeout と root-snapshot-moved | `docs/unreachable-object-ledger.md` 運用契約へ 2 文 (routing 4 の reference 側) | docs 済み |
| 4 | §4 の submodule 検査を `$()` と同居させると guard 拒否 | `hooks/README.md` 既知限界へ 1 項 (契約「事故のない明確化は入口でなく reference へ」に従い command §4 と pin は不変) | docs 済み |

追加で起票したもの (依頼外だが候補 1 の前提に関わる新事実、§1.3): **`tools/dev_wave_cleanup.py` は admin dir 配下の submodule object の hardlink を拒否するため、通常 preflight の snapshot に到達した自己撤去はその hardlink が残る限り rc=20 で止まる**。失敗台帳 F (新規) と次の一手 T (P1、Codex author の別 wave) で起票し、本 wave は tool を直さない。

## 1. 本 wave で再実測した事実

### 1.1 lock の残留 (候補 1 の前提) と撤去可能な子の条件

- `git worktree list`: 146 本、うち `locked` 46 本 (2026-09-18 05:50 JST、wave 開始時点)。
- `.git/worktrees/*/locked` の理由文字列: 「Codex author active」「mutation container」「codex fix running」「author child」など、land 済み wave の子 worktree・container のものが多数。理由なし (空 file) も多数。
- `tools/dev_wave_cleanup.py` の argv は `--wave-worktree` 1 本だけ (`Args`: main_worktree / wave_worktree / wave_branch / tested_wave_tip_sha / landing_wave_tip_sha)。子 worktree は射程外。
- `docs/dev-wave/` の leaf で lock を指示するのは `DW-O20` の「子を走らせる worktree は `git worktree lock`」だけで、unlock・撤去を指示する節は無かった (grep `lock|撤去|container` で `DW-O28` の本体撤去以外に hit なし)。→ 本 wave で `DW-O28` に unlock を統合。
- 同 tool を子 worktree に当てて撤去する案 (§3.1 (i)) が成立する子の条件 (段 6 レビュー A の静的読解、`tools/dev_wave_cleanup.py`): 同じ landing tip を指す branch ref が必要 (対応 branch ref のない detached container は `_classify` の state b に入らない)、branch tip が `refs/heads/main` の祖先 (`_assert_branch_safety`、親が merge しなかった fix / probe branch は拒否)、branch reflog と worktree HEAD reflog の全 commit も main 祖先性を要求 (reset 前の probe commit が残れば拒否)、`--tested-wave-tip-sha` が landing tip の祖先、unoccupied・clean。条件外は「撤去できない理由を報告」へ落ちる。したがって hardlink 拒否 (§1.3) を直しても、branch の無い container・未 merge の probe branch は自動撤去できず、`/cleanup-branches` かユーザー裁定に残る。

### 1.2 guard の同居拒否 (候補 4)

- `git submodule status external/ccbench` 単独: 通過 (`511c9538…` を表示)。
- 同じ command を `$( … )` で包み pin と比較する形: `hooks/guard_bash.py` が「防護ツリーのパス … と不透明構文 ($()/…) の同居は分類不能 = fails-closed」で拒否 (本 wave で再現)。発火条件は `_TREE_LITERAL_RE` の `external/ccbench` 字面 × `_OPAQUE_RE` の `$(` であり、`hooks/README.md` の既知限界には `git commit -m "$(...)"` の同型が既に載っていた。
- 到達経路 (段 6 レビュー B が確認): Codex 側は `.agents/skills/cleanup-branches/SKILL.md` の入口読込と「hook の配線と限界は `hooks/README.md` が正本」の指定から到達し、共通側は `CLAUDE.md` の hooks 節の正本指定から到達する。command §4 自体は `$()` 同居を命じていない。

### 1.3 自己撤去 tool の hardlink 拒否 (新事実)

- land 済み worktree の admin dir `.git/worktrees/dev-wave-t2756-pin-evidence/modules/external/ccbench/objects/**` に `st_nlink > 1` の regular file が **31 件** (`find -type f -links +1`)。段 6 で `.git/worktrees/` 配下 172 本を走査すると、`modules/` を持つ 171 本すべてに `st_nlink > 1` の regular file が少なくとも 1 件あった (各 admin dir で最初の 1 件で打ち切り。焦点再レビュー後の再走は 184 本中 183/183。script は wave job dir `count_hardlinks.py`、stdout 逐語は本 dir の `count-hardlinks.txt`)。出所は `tools/dev_wave_submodule_init.py` → `git submodule update --init --recursive --no-fetch` が local URL から clone する際に git が object を hardlink で共有する標準挙動。
- `tools/dev_wave_cleanup.py` の `_read_admin_file` は `metadata.st_nlink != 1` を `admin entry is not a single regular file` で拒否し、`_admin_snapshot` は admin dir を `modules/` まで再帰する (`allow_locked` は `locked` marker の例外で hardlink には関係しない)。→ 通常 preflight の snapshot (`_bind_admin`) に到達した時点で、hardlink が残る限り ValueError → RC_REJECTED (20)。state d / e の早期 return など snapshot に到達しない経路は別。
- 「初期化済み worktree で必ず rc=20」「146 本の蓄積はこの拒否の帰結」は段 6 レビュー A1 / B2 が過大と指摘し、上記の条件付きへ限定した。蓄積のうちどれだけが本拒否の帰結かは、過去 wave の段 9 の rc が記録されていないため未確認。本 wave の段 9 で自分の worktree に同 tool を当て、rc を一次観測して最終報告に載せる (`DW-O28`)。
- 起票: failures fragment の新規 F (`{{F:cleanup-tool-rejects-hardlinked-admin}}`) と worklog fragment の新規 T (P1)。修正は実装面なので Codex author の別 wave。

### 1.4 rescue gate の timeout (候補 3)

- `tools/check_branch_rescue.py`: `DEFAULT_ASSESSMENT_TIMEOUT_SECONDS = 8.0` (`--assessment-timeout-seconds`、`_bounded_float(1, 60)`)、`DEFAULT_TIMEOUT_SECONDS = 300.0` (`--timeout-seconds`、上限 900)。landed checker の子 process は `timeout=min(timeout, overall_remaining)` で走り、`TimeoutExpired` は `checker-timeout` → `indeterminate` → rc 2。
- `root-snapshot-moved` は start / end の root inventory digest が不一致のとき `technical_incomplete` → rc 2。走行中に別 wave が worktree・branch を作れば digest が変わりうる (途中の全イベントを監視する実装ではない)。
- 依頼文の実測 (候補 17 本・27 commit で 10 件 checker-timeout、225 秒) は本 wave では再現していない (掃除対象が既に消えている)。

## 2. 変更面

| file | 変更 | 種別 |
|---|---|---|
| `docs/dev-wave/operations.md` `DW-O28` | 子 worktree の unlock 義務を統合、撤去は D703 の例外外と明記、983 → 989 bytes (L2 単節予算 1000)。段 6 前の版 (子の撤去を含む 998 bytes) は B1 で撤回 | docs |
| `docs/unreachable-object-ledger.md` 運用契約 | timeout 2 option と root 移動の 2 文 | docs |
| `hooks/README.md` 既知限界 | `git submodule status external/ccbench` × `$(...)` の 1 項 | docs |
| `docs/spool/failures/2026-09-18-dev-wave-cleanup-si-routing-1.md` | F26 supersede 1 行 + 新規 F (§1.3) | fragment |
| `docs/spool/worklog/2026-09-18-dev-wave-cleanup-si-routing-1.md` | 本 wave の entry + 新規 T 2 件 | fragment |
| `tools/check_docs.py` `DEV_WAVE_DW_O28_SECTION_LITERAL` | 新本文へ追随 (author: 998、fix: 989) | 実装面 (Codex author / fix) |
| `orchestrator/tests/test_check_docs.py` `_SYNTHETIC_DW_O28_SECTION` と byte 数 assert 2 箇所 | 同上 (983 → 998 → 989) | 実装面 (Codex author / fix) |

`.claude/commands/cleanup-branches.md` (6181 / 6204 bytes、whole-file SHA-256 pin) と `.agents/skills/cleanup-branches/` は 1 byte も変えていない。cleanup の安全条件・判定機構 (F51 の locked 禁止、D703 の削除範囲) も変えていない。exact pin の受理集合は旧本文から新本文へ移った (他の本文を拒否する機構は不変)。

## 3. 裁定パッケージ (ユーザーへ返す、本 wave は実装しない)

### 3.1 land 済み wave の子 worktree・container の撤去と stale lock

- 問題: `/cleanup-branches` §2 / §3 は locked を報告のみ (F51) とするため、land 済み wave の子 worktree・container に残る lock (§1.1) を掃除できず、2026-09-17 はユーザー裁定で越えた。本 wave で `DW-O28` に unlock を統合したので、今後の wave の子は unlock された状態で `/cleanup-branches` の通常経路 (main 取込済み・clean・unoccupied なら削除) に乗る。残るのは (a) 過去の残留分と (b) 撤去の自動化の要否。
- (i) 段 9 で子 worktree・container も同 tool で撤去する: D703 は自動削除を「同一 invocation の exact な wave worktree path と wave branch ref だけ」に限定しているので、例外の拡張裁定が要る。撤去可能な子の条件は §1.1 (branch 必須、tip と reflog の main 祖先性)。条件外の container・probe branch は依然として残る。
- (ii) `/cleanup-branches` に stale lock 判定 (lock 理由の pid が不在、または lock 理由の wave branch が不在なら unlock 可) を足す: F51 の「locked は触らない」(§2 の locked 除外と §3 の unlock 禁止の両方) の変更が要り、pid 再利用・理由なし lock の扱い・command の byte 予算 (残 23 bytes) と SHA pin 更新も要る。判定を `tools/check_worktree_occupancy.py` 側へ寄せる派生案も、command の locked 禁止条項を変えない限り機能しない (段 6 レビュー B3)。
- (iii) 現行どおり報告のみとし、残留分 (2026-09-18 時点で locked 46 本のうち land 済み wave の子) を 1 回だけユーザー裁定で unlock する。
- 親の推奨: (iii) + `DW-O28` の unlock 統合 (本 wave) + §3.2 の tool 修正。主経路 (CC 自動合成) との距離: 遠い (開発運用の土台)。

### 3.2 `tools/dev_wave_cleanup.py` の hardlink 拒否 (§1.3)

- 問題: 段 9 の自己撤去が、admin dir の submodule object に hardlink が残る worktree で rc=20 になる。
- 案 A (推奨): `_read_admin_file` の `st_nlink != 1` 拒否を `modules/` 配下の object file (submodule の hardlink pack / loose object) に限り許容し、admin の registry file (`gitdir` / `commondir` / `HEAD` / `locked` 等) は現行どおり nlink==1 を要求する。「検査の意味 (admin file の同一性) を保つ」は実装時の検証事項であり確定事実ではない。
- 案 B: `_admin_snapshot` が `modules/` を再帰しない。撤去対象の identity 束縛が弱くなる。
- いずれも Codex author の実装 + 正例 (hardlink 入り admin dir の fixture で撤去成功) + 負例 (registry file の hardlink は拒否) の変異が要る。D2104 項 32 / D2113 (並列撤去 launcher) とは別の tool であり直接の矛盾はない。

## 4. 検査

- `python3 tools/check_docs.py`: docs commit 時点で赤 1 件 (`DW-O28` の exact 契約不一致、期待どおり) → Codex author / fix の pin 追随後に「違反なし」。
- 焦点走 1 (author 後の tip bcf017c74、`test_check_docs.py` + `test_dev_wave_land.py` + `test_dev_waves_checker.py` + `test_spool_fold.py` + `test_check_ai_provenance.py`、計算ノード request 4937.nqsv): rc=0、1581 passed / 4 skipped (growth hold 3 = `test_dev_wave_model_pins_accept_current_docs_contract` / `test_normative_exact_section_pins_accept_real_repo` / `test_real_repo_clean`、flaky hold 1)。skipped は緑と読まない。
- 焦点走 2 (fix 1 巡目後の tip 5fc1d8971、上記 5 file + `test_branch_rescue_ledger.py` + `test_hooks.py`、request 4998.nqsv): **rc=1、336 failed / 1754 passed / 5 skipped**。失敗は全て `test_check_docs.py` で、赤理由は合成 fixture 上の `docs/dev-wave/operations.md: 実在しない D 参照: 'D703' (decisions.md に見出しなし)` が 1 件余分に出ること (合成 fixture の `docs/decisions.md` は pin 節が参照する D を placeholder 見出しで供給する設計で、D703 が無かった)。焦点再レビューの must-fix 1。
- 焦点走 3 (fix 2 巡目後の最終 tip 675ba9e5a、同 7 file、request 5044.nqsv): **rc=0、2090 passed / 5 skipped** (growth hold 3 + flaky hold 1 + 1)。
- 受入全走: land 経路 (`tools/dev_wave_wait.py acceptance`) で実施、結果は land の受領証と job dir。

## 5. 変異 matrix と実走結果

事前登録 (段 4、handoff → `parent-brief.md`): runner `tools/run_tests.py orchestrator/tests/test_check_docs.py -q -rf --force-dispatch`、container `.codex/worktrees/cleanup-si-mutcontainer`、M0 comment 対照 (positive / SURVIVED)、M1 `check_docs.py` literal drift (negative / KILLED)、M2 doc drift (negative / KILLED 予測)。

### 5.1 erratum — 段 6 前の本文 (v2、子の撤去を含む 998 bytes、tip bcf017c74) に対する走行

- probe (spec sha `1d792f6e…`、全件 SURVIVED 登録): baseline PASSED、M0 SURVIVED (赤 0 = drift 核なし)、M1 観測 337 node (全て `test_check_docs.py`、ASCII)、M2 観測 0。
- 本走 (spec sha `661bf29b…`、M1 KILLED 337 node 登録、M2 SURVIVED 登録): baseline PASSED、**M1 KILLED 337/337 完全一致、M0 SURVIVED、M2 SURVIVED、MISMATCH 0** (`mutation-final.json`)。
- M2 の再照準: 予測した検出 node (`test_normative_exact_section_pins_accept_real_repo` / `test_real_repo_clean`) は growth hold (2026-08-12 裁定、ユーザー明示解除のみ) で skip され、合成 fixture は test 側の独立 literal を描画するため実 docs だけの変異を検出しない (段 6 レビュー B4)。実効 gate は `python3 tools/check_docs.py` の直接実行 (`tools/dev_wave_land.py` も fold 後・commit 前に直接起動して非 0 を拒否する)。container で doc を一時変異 (`m2-direct-diff.patch`、1 file 1 行) して直接実行すると `可視 H2 節 'DW-O28 — land 後の自己撤去' の節全体が exact 契約と不一致` で rc=1、`git checkout --` 復元後の porcelain は空 (`m2-direct-*.txt`)。無変異の同 tree は本走 baseline が緑。この直接検査は pytest 層の KILLED に読み替えず、別枠の実効 gate 証拠として扱う (DW-M08)。
- この走行は B1 (子の撤去は D703 の例外外) で本文を v3 へ改めたため、最終 tip の証拠ではない。

### 5.2 最終 tip (v3 本文 989 bytes) に対する走行

anchor は v3 の語へ再照準 (M1: `check_docs.py` literal の「は同段で unlock する（撤去は D703 の例外外）。」→「は同段で unlock する。」、M2: doc 側で同じ置換、M0 は同じ comment)。spec `mutation-spec-probe-v3.json` (sha `7569d114…`)、各 anchor は file 内で一意。

- probe v3 (tip 5fc1d8971、fix 1 巡目後): **baseline FAILED (336 node、焦点走 2 と同じ D703 理由) で harness が production write を開始せず中止** (rc=2、木は clean)。erratum。
- probe v3b (最終 tip 675ba9e5a、`mutation-probe-v3b.json`): baseline PASSED、M0 SURVIVED (赤 0)、M1 観測 337 node (全て `test_check_docs.py`、ASCII、v2 と同数)、M2 観測 0。
- M2 の直接検査 (最終 tip、container、`run-m2-direct.sh v3`): 変異前 `python3 tools/check_docs.py` rc=0 (違反なし) → doc を 1 行変異 (`m2-direct-v3-diff.patch`) して rc=1 (`可視 H2 節 'DW-O28 — land 後の自己撤去' の節全体が exact 契約と不一致`) → `git checkout --` 復元後 rc=0、porcelain 空 (`m2-direct-v3-*.txt` / `.log`)。同一 checker の緑→赤→緑。
- 本走 v3 (spec `mutation-spec-final-v3.json`、sha `d3c60a0f…`、M1 KILLED 337 node 登録、M2 SURVIVED 登録、`mutation-final-v3.json`、2026-09-18 08:10 JST 完了): **baseline PASSED、M1 KILLED 337/337 完全一致、M0 SURVIVED、M2 SURVIVED、MISMATCH 0 / TIMEOUT 0** (registered 3 / recorded 3 / matching 3)。

| ID | 変異 | 種別 | 観測 node (完全集合) |
|---|---|---|---|
| M0 | `check_docs.py` の comment 1 行 (等価対照) | positive / SURVIVED | 0 (drift 核なし = harness の SURVIVED 検出の正例) |
| M1 | `DEV_WAVE_DW_O28_SECTION_LITERAL` の「（撤去は D703 の例外外）」を落とす (pin ≠ docs/synthetic) | **gate kill** | 337 node、全て `test_check_docs.py` (等式 meta-test `test_normative_exact_section_contract_is_handwritten_and_complete`、`test_dw_o28_exact_section_pin_accepts_synthetic_fixture`、合成 fixture を実 checker に掛ける正例 test 群が一斉に赤) |
| M2 | `docs/dev-wave/operations.md` 側で同じ語を落とす | pytest 層 SURVIVED (growth hold) + 直接 checker 緑→赤→緑 | 0 (pytest)、直接 checker rc 0→1→0 |
