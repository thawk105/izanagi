### §0 読了確認

全文を読んだもの:

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t664-docs-budget/s1-brief.md`
- `docs/dev-wave/core.md`
- `docs/dev-wave/workers.md`
- `docs/dev-wave/mutation.md`
- `docs/dev-wave/operations.md`
- `.claude/commands/dev-wave.md`
- `docs/skill-self-improvement.md`
- `docs/decisions.md` の D94 / D110 / D186
- `docs/ruleops.md`
- `CLAUDE.md`、`AGENTS.md`、dev-wave skill

静的に確認したもの:

- `tools/check_docs.py` の `COMMAND_LIMITS`、`REFERENCE_LIMITS`、`DEV_WAVE_*`、節外延、stage/condition dispatch、budget 検査
- `docs/worklog.md`、`docs/archive/worklog-*.md`、`docs/failures.md`、`docs/decisions.md`、`output/insights/**`、`/work/1/SFC/tanab/dev-wave-jobs/**` の意味検索 hit
- 関連 tool と test の実装・nodeid

読めなかった必須資料: なし。

本文編集・テスト実行はしていない。以下は静的検査だけであり、テストの緑は主張しない。

### §1 L2 集合の同定

dispatcher の決定的な行は次である。

> `段 2 preflight`: `DW-O01`, `DW-O02`, `DW-O03`, `DW-O05`  
> `段 3 preflight`: 上記に `DW-O13` を追加  
> `段 5` / `段 6`: 「成立した条件の」operations 節  
> `段 9`: `DW-O23`

また、core / workers / mutation は各段で個別に無条件列挙されている。operations 節が後段で条件付きでも、一度でも無条件 dispatch されれば D94 上は L1 である。

| file | 節 | 層 | 根拠 |
|---|---|---|---|
| `.claude/commands/dev-wave.md` | `入力と開始`, `読み込み契約`, `凍結境界`, `9 段状態機械`, `段 dispatch`, `条件 dispatch`, `終端` | L0 | command は常時全文読了 |
| `core.md` | `DW-C00`, `DW-STOP`, `DW-S01`, `DW-G01`, `DW-G02`, `DW-G03`, `DW-G04`, `DW-G05`, `DW-S04`, `DW-S07`, `DW-S08`, `DW-S09`, `DW-CTX` | L1 | wave 開始・段 1/4/7/8/9 で無条件指定 |
| `workers.md` | `DW-S02`, `DW-S03`, `DW-S05-A`, `DW-S05-B`, `DW-S05-C`, `DW-S06-A`, `DW-S06-B`, `DW-S06-C` | L1 | 段 2/3/5/6 で無条件指定 |
| `mutation.md` | `DW-M01`, `DW-M02`, `DW-M03`, `DW-M04`, `DW-M05`, `DW-M06`, `DW-M07`, `DW-M08` | L1 | 段 4/6 で無条件指定 |
| `operations.md` | `DW-O01`, `DW-O02`, `DW-O03`, `DW-O05`, `DW-O13`, `DW-O23` | L1 | 段 2/3 preflight または段 9 で無条件指定 |
| `operations.md` | `DW-O04`, `DW-O06`, `DW-O08`, `DW-O09`, `DW-O10`, `DW-O11`, `DW-O12`, `DW-O14`, `DW-O16`, `DW-O17`, `DW-O18`, `DW-O19`, `DW-O20` | L2 | 条件成立時だけ読む |

したがって (P-L2) は正しい。節別 raw UTF-8 bytes も提示値と一致し、L2 合計は **5,008 bytes** である。

### §2 経路 A — 削除候補の棚卸し

意味語 hit は `worklog / archive / failures / decisions / insights` の合計で、同一事例の重複を含む観測 signal である。判定には別途、代表的な直接発火を突き合わせた。

| 節 | bytes | (ii) 発火実績 (検索語と hit) | (iii) 機械代替 (path + テスト nodeid、無ければ「なし」) | 判定 | 理由 |
|---|---:|---|---|---|---|
| `DW-O04` | 200 | `commit -F`=13、`message file`=9、`heredoc`=20、合計42。commit `0e056e5` の message に `output/campaigns/...` が実在 | 部分: `hooks/guard_bash.py`; `orchestrator/tests/test_hooks.py::test_bash_opaque_with_protected_fails_closed` | 不採 | 発火済み。hook は不透明構文を拒否するが、単一行 `-m` を許し、Write＋`-F` を強制しない |
| `DW-O06` | 210 | `index lock`=9、`submodule.*偽赤`=22、`sandbox 由来`=4、合計35。`worklog-phase3-0721-0722.md:898` と `...0727-20-25.md:159` に親環境不再現例 | なし | 不採 | 発火済み。赤の環境帰属は意味判断で、完全な機械代替なし |
| `DW-O08` | 183 | `submodule update --init`=39、`未初期化`=78、合計117。F66 (`failures.md:1624`) と [T-207] で発火 | 部分: `tools/run_tests.py`, `tools/check_wave_startup.py`; `test_v15_acceptance_missing_submodule_initializes_no_fetch_with_scrubbed_env`, `test_resume_rejects_invalid_submodule_marker` | 不採 | 発火済み。初期化検知はあるが、「skip・手前の赤を破損なしと報告しない」は人間義務 |
| `DW-O09` | 935 | `FROZEN_MANIFEST`=325、`pin 閉包`=127、`durable manifest`=9、`凍結 snapshot`=20、合計481。F30 (`failures.md:574`) が直接例 | 部分: `orchestrator/tests/test_frozen_artifacts.py::test_frozen_artifacts_match_manifest`, `::test_manifest_shape_is_exact` | 不採 | 頻繁に発火。既知 manifest の bytes は検査するが、role-key pin、ledger、分類を含む閉包探索は代替しない |
| `DW-O10` | 261 | `producer.*書く全ファイル`=1、`write-path`=16、合計17。[T-419] `s4-adjudication.md:88-105` で棚卸し、同 `:215-220` で追加 sidecar 漏れを是正 | なし | 不採 | 旧調査後に明確に発火。全 producer に共通する機械入力 schema がない |
| `DW-O11` | 223 | `未 stage 削除`=31、`rc=15`=24、`削除を伴う`=3、合計58。commit `72e3800` が既存 O11 下で handoff を削除 | 部分: `tools/run_tests.py`; `test_unstaged_deletion_gate_detects_count_and_scrubs_git_env`, `test_acceptance_deletion_git_rc_failure_fails_closed` | 不採 | 発火済み。D186 が受入 receipt・landed tip 結線等の欠落を確定し、回収量 0 と裁定 |
| `DW-O12` | 195 | `実際に実行した手順`=2。`worklog-phase3-0728-38-0729-48.md:255` に「DW-O12 訂正、裁定記載手順は未実装」 | なし | 不採 | hit は少ないが直接発火あり。裁定予定と実行事実の意味比較を読む共通 field がない |
| `DW-O14` | 200 | `monkeypatch`=334、`注入 seam`=58、`current_head`=23、合計415。D94 自身が ratified memo の正規 seam 非等価確認を実発火例に指定 | なし | 不採 | 発火済み。個別 seam test はあっても、対象実装全体を読む義務の代替にはならない |
| `DW-O16` | 367 | `焦点再レビュー`=456、`対応表`=277、`closed / partial`=24、合計757。3 巡上限到達例は archive に複数 | なし | 不採 | 高頻度発火。表の存在だけで root cause closure の意味を検査できない |
| `DW-O17` | 702 | `trailer`=448、`--dry-run -F`=6、`full-history 監査`=23、合計477。F25/F37 と実 commit で発火 | 部分: `tools/check_ai_provenance.py`; `test_message_file_gate_uses_staged_paths`, `test_merge_preflight_and_history_count_all_parent_different_resolution` | 不採 | 発火済み。個別監査は機械化済みだが、commit/merge の実行順と監査実施を結ぶ receipt がない |
| `DW-O18` | 441 | `単独再走`=93、`repo root`=132、`偽赤`=157、`帰属しない`=40、合計422。F41 と多数の単独再現性確認 | 部分: `tools/run_tests.py`; `test_main_assembles_absolute_relative_target_from_other_cwd`, `test_main_absolutizes_plain_relative_target_from_other_cwd` | 不採 | 発火済み。cwd は機械化されるが、到達可能性・再現性・帰属・測定 checkout は判断義務 |
| `DW-O19` | 602 | `git checkout --`=64、`一時変異`=41、`復元 bytes`=5、合計110。archive に tracked 変異と HEAD bytes 復元例が多数 | 部分: `tools/mutation_harness.py`; `test_restore_verification_rejects_content_different_from_head`, `test_signal_arriving_during_restore_is_deferred_until_all_targets_verified` | 不採 | 発火済み。tool 外の一時編集、anchor/記録 commit の順序まで代替しない |
| `DW-O20` | 489 | `check_wave_startup`=155、`clean-tree`=36、`untracked handoff`=6、合計197。F48/F49/F50 で直接発火 | 部分: `tools/check_wave_startup.py`; `test_fresh_rejects_dirty_tree`, `test_external_handoff_also_rejects_worktree_handoff_leftover` | 不採 | 発火済み。resume の clean-tree 非検査や worktree 再利用判断など残余義務あり |

**削除候補はゼロ。** 13 節すべてで D94 条件 (ii) が偽であり、複数節では (iii) も部分代替に留まる。5,008 bytes は理論上の L2 総量であって、解放可能量ではない。

RuleOps v1 は `orchestrator/tests/test_*.py` 直下と `output/insights/**` だけが対象で、`docs/dev-wave/**` は対象外である。さらに観測 signal と mutation receipt は advisory なので、D94 の意味検索や削除安全を代替しない。

### §3 経路 B — テスト化候補の棚卸し

| # | 対象 (節・file:line) | 現在の prose 義務 | 検査の設計 (読む実成果物と field) | 赤にする具体入力 | 既存被覆との差 (純増検出力) | 移管後に削れる bytes (実測/推定) | 実装コスト | 既裁定との重複 |
|---|---|---|---|---|---|---:|---|---|
| B1 | `DW-O23`; `operations.md:121` | lock 内再照合、ff-only、同 lock 内 fold、失敗時非 landed、zero-fragment no-op、dirty/collision/no-touch | `LandRequest.main_worktree`, `wave_worktree`, `tested_main_sha`, `tested_wave_tip_sha`, `audited_commits` と、`LandResult.status`, `main_before`, `main_after`, `wave_tip`, `fold_commit_sha`。既存 `test_dev_wave_land.py` を機械正本にする | pending fragment 1 件で fold を例外終了させたのに `status="landed"` を返す実装。`test_fold_failure_rolls_back_ff_and_never_returns_landed` が赤になる | 個別検出力は既存 node に存在。新 test の純増は 0 だが、機械化済み内部手順を prose の二重正本から外せる | **449 bytes、文案実測**（1123→674） | 中 | 独立。D110 の新規 reference 化ではない |
| B2 | `DW-O10`; `operations.md:60` | producer の全書き出し種を列挙し、変更漏れを防ぐ | baseline/candidate の `final-receipt.json`: `schema_version`, `staging_manifest[].path`, `calibrator_attempt_manifest[].path` を集合比較する proposed node `test_receipt_file_set_delta_requires_inventory_entry` | candidate receipt に `published-self-comparison.json` が増えたのに登録集合が baseline のまま | collector は path/size/SHA を記録するだけで、file-set delta を検査しない。実際の [T-419] NR-04 を新たに捕捉できる | **予算解放 0**。receipt のない producer と事前棚卸し義務が残る | 中 | 独立 |
| B3 | `DW-O04`; `operations.md:27` | 防護 path を含む commit message は Write＋`git commit -F` | PreToolUse event の `tool_name` と `tool_input.command` を読み、protected path を含む `git commit` の `-m` を拒否する proposed node `test_bash_commit_with_protected_path_requires_message_file` | `git commit -m 'output/campaigns/x を参照'`。現行 fast path は許可するため、新 node はこの入力で赤にできる | 既存 test は heredoc/command substitution を塞ぐだけ。透明な `-m` 拒否が純増 | **予算解放 0**。Codex に hook が未配線で、Write 実施も hook 単独では証明不能 | 低 | 独立 |
| 既裁定 | `DW-C00 core.md:17`, `DW-O01 operations.md:9`, `DW-M05 mutation.md:35`, `DW-M08 mutation.md:49`, `DW-S06-B workers.md:52` | 待ち手3条、残留 `.done`、pgrep 自己一致、期待 node 完全一致、F112/F124 | `.done` の存在・exit code、`/proc/*/cmdline`、spec `mutations[].expected_nodes`、ledger `mutations[].failed_nodes/status`。待ち手 condition identity field は単一 launcher 実装まで不在 | stale `.done` がある再投入、待ち手自身へ一致する `pgrep -f`、expected/failed の真部分・真上位集合 | **[T-454] と同一。新規候補に数えない。** `DW-M08` exact set は既存実装・test に到達済み | 新規計上 **0** | [T-454] の既定 scope | **同一** |

B1 の縮約文案は次で実測した。太字の wave-side 禁止、caller の成功判定、再試行、所有境界は prose に残している。

```markdown
## DW-O23 — 並行 session の local main land

`tools/dev_wave_land.py`へmain/waveの絶対path、tested main/tip、監査commit列を渡す。
lock内再照合・ff-only・同lock内fold・dirty/collision/no-touch拒否・postconditionは同toolと
`orchestrator/tests/test_dev_wave_land.py`の機械契約を正本とする。**wave側でfoldしてはならない**。
成功は`landed`/`already-landed`だけ。他statusは停止する。stale/busyはfresh contextで既存branchを再利用し、
新main監査、固定SHAのwave-side merge、条件再評価・受入後に再試行する。
他session所有物、rebase、force、remote、pushで解消しない。
```

残余リスク:

- tool と test を同時に弱める変更には別の独立 oracle が必要。
- `LandResult` は full-history provenance 実施を証明しないため、`DW-O17` / `DW-S09` は削れない。
- `DW-O11` は D186 のとおり acceptance receipt と landed tip の field が存在せず、候補外。
- `DW-O18` の cwd 一文だけは機械化済みだが、解放量が数十 bytes に留まるため候補外。
- `DW-M08` pointer 化は F95 / [T-417] の正規化未実装が残り、[T-597] の棄却を維持する。

### §4 dispatcher (L0) の削減候補

| L0 対象 | 統合先 | 統合後の文面案 | 削減 bytes | 意味が変わらない根拠 |
|---|---|---|---:|---|
| `.claude/commands/dev-wave.md:39` | `DW-STOP` (`core.md:20`)＋既存 `DW-S09` | `push と remote branch 操作は行わず、停止条件をテスト弱体化、権限拡大、rebase、force、未監査差分の取り込みで迂回しない。` | command **−134**、reference **+44**、常時読量 net **−90** | `DW-STOP` は wave 開始時に読むため push/remote 禁止の時期は遅れない。local main の全条件成立・段9限定・唯一経路は既に `DW-S09:109-111` が持つ |
| `.claude/commands/dev-wave.md:42` | `DW-CTX` (`core.md:114`) | `1 wave は 1 fresh context。command は自己再帰・\`/clear\`・次 wave 開始を行わず、段 9 後に人間が`<br>`\`/clear <完了 wave 名>\` と報告された \`/dev-wave <次タスク>\` を順に実行する（D69）。` | command **−119**、reference **+24**、常時読量 net **−95** | `DW-CTX` は wave 開始と段9で無条件読了される。fresh context、自己再帰禁止、command 内 `/clear` 禁止、人間による次 wave 起動をすべて保持 |

合計は command **−253 bytes**、reference **+68 bytes**、常時読量 net **−185 bytes**。

ただし現行 reference aggregate の空きは16 bytesしかないため、この2件は単独では採用できない。B1 と同一変更単位なら aggregate は `25,184 − 449 + 68 = 24,803`、command は `9,457 − 253 = 9,204` となる。

次は候補外である。

- 読み込み契約、凍結境界、状態機械、stage/condition dispatch は dispatch 自体を成立させる命令。
- D94 却下案 (c) の入口冒頭2行→`DW-CTX` 移管は、外部 supervisor と manager で読者主体が異なるため復活させない。
- 新規 reference file は D94 却下案 (a) どおり提案しない。

### §5 既裁定との関係

| 既裁定 | 関係 | 本棚卸しとの関係 |
|---|---|---|
| [T-127] | 部分重複 | 上限据置き、微小な言い換えを成果にしない、機械化優先を継承 |
| [T-313] | 部分重複 | 実装後は L2 剪定の「予算解放」価値が消える。B1の `DW-O23` はL1、§4はL0なので価値を維持 |
| [T-328] | 部分重複 | 条件付き reference という方向は共有するが、新規 file・節移動は提案しない。B1は既存節から実行 tool/test への移管 |
| [T-412] | 部分重複（§2は同一） | L2棚卸しを現 anchor まで更新。旧唯一薄弱候補 O10 も [T-419] 発火で不適格になった |
| [T-454] | 部分重複 | 固定 scope は同一として非計上。B1/B2/B3はその外側の独立候補 |
| D94 | 部分重複（経路Aは同一） | 層定義、意味検索、削除3条件、ユーザー裁定境界をそのまま適用 |
| D110 | 独立 | provenance の外出し先例として参照するだけ。dev-wave の file split へ転用しない |
| D186 | 部分重複 | `DW-O11` の機械化不足・解放0 bytesを再確認。B1/B2/B3には独立 |

[T-313] 実装時に予算上の価値を失うもの:

- 経路 A 全体。L2 5,008 bytes は常時読量 gate の対象外になる。
- L2である B2 (`DW-O10`) と B3 (`DW-O04`) はもともと予算解放0で、検出力の価値だけが残る。

価値を失わないもの:

- B1 `DW-O23` はL1。
- §4 の dispatcher はL0。
- [T-454] の C00/O01/M05/M08/S06-B はL1であり、安全・検出力上の価値も残る。

## 総括

- 経路 A: **悲観 0 / 楽観 0 bytes**。L2 13節、5,008 bytes のどれもD94削除gateを通らない。
- 経路 Bの新規候補: **悲観 0 / 楽観 449 bytes**。予算を実際に空け得るのは `DW-O23` の機械契約移管だけ。
- L0は別枠で、B1と同時なら command **253 bytes**、常時読量 net **185 bytes**を追加で減らせる。

最も推奨する3手:

1. B1の `DW-O23` 449-byte移管をユーザー裁定へ送る。L1削減なので [T-313] 後も有効。
2. B1と同一変更単位で、dispatcher 39行・42行を既存 `DW-STOP` / `DW-S09` / `DW-CTX` へ統合する。
3. [T-454] は設計を作り直さず、確定済み scope のまま起票する。新規候補・新規 bytes として二重計上しない。

この棚卸しで空かないと判明したものは、L2剪定全部、`DW-O11`、file再編、新規reference、F95/[T-417]未了の `DW-M08` pointer化、RuleOps v1、`DW-O04` hook強化、`DW-O10` receipt差分検査、数十bytesの助詞・一文削り、および `DW-S07` の安全義務である。