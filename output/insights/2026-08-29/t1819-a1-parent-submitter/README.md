# [T-1819] A-1 投入器 — 起票前提の反証と実在欠陥 5 件の局所修正 (2026-08-29)

wave: `dev-wave-t1819-a1-parent-submitter` / branch: `worktree-dev-wave-t1819-a1-parent-submitter`
base: `d03855e92` / 統合 commit: `4b453343e` / fix commit: `097f4f35e`

## 一次資料

- `mutation-spec.json` — 変異 matrix 本走の spec (sha256 `142cc0d81f034a1ae4b5a646aab1818062de69d8bbd911e4b228fa340e5e652c`)。
- `mutation-report.json` — 本走の報告。baseline PASSED、10/10 KILLED、期待 node 完全一致。
- `mutation-probe-report.json` — 期待 node を収集するための probe (全件 SURVIVED 期待)。
  baseline PASSED、10 変異すべてが失敗 node を出した。

## 起票前提の反証 (実測)

起票 (2026-08-26) は「A-1 に親側直接 qsub と acquisition receipt の create-only 書き出しが無く、
他 job body の `tools/pegasus/submit_*.sh` に対応する部品が無い」と述べていた。着手時の実測で
次のとおり覆った。

| 起票の主張 | 実測 | 判定 |
|---|---|---|
| 親側直接 qsub が無い | `run_submit` (1080 行) と `_run_qsub` (1016 行) が main に存在 | refuted |
| create-only の receipt 書き出しが無い | `_exclusive_write` 経由で存在。`ACQUISITION_SCHEMA = SUBMISSION_SCHEMA` | refuted |
| test が無い | `test_paper_story_a1_job_contract.py` に 4 本 (1724 / 1768 / 1803 / 1839 行) | refuted |
| login 側 shell が無いので未実装 | job body 自身が「親が直接 qsub する。この file は投入器ではない」と宣言 | refuted (設計差) |
| 正式投入経路が塞がっている | durable measurement base を作る部品が無く base も実在しない | **一部 real** |

出所は同日 land した [T-2006] (worklog エントリ 1087)。D1028 が「A-1 の投入は非認証成果物型と
投入器を 1 つの変更単位で作る」と定めており、[T-1819] の実体はその変更単位に吸収されていた。

段 2 は `hooks/guard_bash.py` の `decide()` へ実 command 列を与える read-only probe を走らせ、
正式投入の command 列が機械防壁を通ることを rc=0 で実測した (正式 qsub 自体は実行していない)。

## 実装した実在欠陥 5 件

| # | 欠陥 | 成果物影響 |
|---|---|---|
| R1 | acquisition receipt の create-only 書き出しが原子的でない。compute 側 job body は receipt path の存在だけで待機を終えて即読みする | qsub と親側 receipt 作成が成功しても compute が acquisition validation で終了し、有効な A-1 raw bundle が作られない |
| R2 | qsub 前の fresh-attempt 検査が evidence 4 path のうち completion / stdout / stderr を見ない | 測定を完遂しても completion receipt を発行できず materialize 不能な bundle が残る |
| R5 | durable measurement base を作る部品が無い。policy が指す base も実在しない | 最初の正式投入が intent の `os.open` で ENOENT になり、測定が 1 件も始まらない |
| MF1 | rename 失敗時に staging file が残り cleanup が無い | 復旧操作後に staging の `O_EXCL` が qsub 後に失敗し、receipt を公開できない |
| MF2 | staging 名の衝突で、evidence 4 path が空でも拒否される (未承認の過剰拒否) | 承認外の受理集合縮小 |
| MF4 | PID suffix 付き staging basename が `NAME_MAX` を超えうる | final basename が有効な長い attempt-id が新経路でだけ書けない |

R1 の修正は新機構ではなく、**同じ module に既にある作法** (`PUBLISH_RENAME_NOREPLACE`、
`_renameat2_directory`、`_publish_staging_noreplace`) を receipt の書き出しへ当てたものである。
R5 は手本の A-2 (`paper_story_a2_certification.py` 641 行の
`base.mkdir(parents=True, exist_ok=True)`) を最小で写した。

## 変異の証拠 — 事前登録と事後登録を分ける

`DW-M01` は変異を実装前に登録することを求める。本 wave の 10 件は 2 群に分かれ、
証拠としての重みが違うので**合算した件数を成果として書かない**。

### 事前登録 7 件 (実装前に登録。証拠として数える)

| id | 結果 | 失敗 node 数 |
|---|---|---|
| `t1819.m1.staging-is-final` | KILLED | 15 |
| `t1819.m2.rename-replaces` | KILLED | 2 |
| `t1819.m3.drop-completion-check` | KILLED | 1 |
| `t1819.m4.drop-stdout-check` | KILLED | 1 |
| `t1819.m5.drop-stderr-check` | KILLED | 1 |
| `t1819.m6.over-reject-stderr-check` | KILLED | 11 |
| `t1819.m7.drop-base-mkdir` | KILLED | 1 |

M6 は `DW-M01` が受理集合を縮める wave に要求する過剰拒否の正例、M7 は R5 の正例である。

### 事後登録 3 件 (fix 実装後に追加。事前登録と同じ重みでは数えない)

| id | 結果 | 失敗 node 数 |
|---|---|---|
| `t1819.m8.drop-staging-collision-check` | KILLED | 1 |
| `t1819.m9.blind-staging-cleanup` | KILLED | 1 |
| `t1819.m10.unbounded-staging-name` | KILLED | 1 |

段 6 のレビュー所見に対する fix の変異を fix 子の起動前に登録する規則が `DW-M01` に無いことが
原因である。失敗台帳へ起票した。

### 過剰決定の申告 (DW-M03)

M1 (15 node) と M6 (11 node) は**過剰決定**である。M1 は staging を final path と同一にすると
publish 全体が壊れるため、「完成前に final path が見えない」という性質だけを分離できていない。
M6 は無条件拒否なのであらゆる正常経路を壊す。したがって両者を**冗長 gate と明記し、
単独変異の帰属証拠から外す**。publish 経路の帰属は M2 (2 node)・M8・M9・M10 (各 1 node) が担う。

## 親が実測したテスト (子は実走できなかった)

段 5 実装子と段 6 fix 子はいずれも計算ノード混雑で runner の admission が通らず child 未起動
(rc=16、`child_started=false`) となり、正直に「未実走」と報告した。テストは親が実測した。

| 走 | 結果 |
|---|---|
| 変更 test file 単独走 (`test_paper_story_a1_job_contract.py`) | 126 passed、rc=0 |
| consumer 焦点走 8 file (参照関係で引いた) | 1083 passed / 4 skipped、rc=0 |
| 変異 matrix 本走 | baseline PASSED、10/10 KILLED、rc=0 |

consumer 焦点走の対象は、変更した production module 名で `orchestrator/tests/` を grep して
引いた `test_ccbench_spawn_sites.py` / `test_hooks.py` / `test_official_perf_closure.py` /
`test_p3_build_authority_cli.py` / `test_p3_exploration_namespace.py` /
`test_paper_story_a1_headline.py` / `test_paper_story_a1_paired.py` / `test_campaign.py`。

段 3 と段 6 が「exact 述語は AST node 数を数えており追随不要」と判定した
`test_ccbench_spawn_sites.py` と `test_p3_exploration_namespace.py` は、この実走で緑を確認した。

## 実装しなかったもの

- CCBench の strict clean gate。段 3 の 2 本ともそのままの実装に反対した。裁定パッケージで返す。
- login 側 shell 投入器、汎用の投入 framework、新しい署名・nonce・schema。
- `check_quota` / `qstat -Q` の queue 状態検査 / 既存 request の重複検査 — いずれも成果物の値・
  受理集合への影響を書けない liveness 差なので `DW-G05` により nit / backlog とした。
- 正式 qsub と A-1 の実測投入。

## 運用で踏んだこと

- 変異 wrapper は `--source-repo` と main 共有木の観測 bytes 不変を要求する。並行 wave が
  main checkout を絶えず動かしているため 1 度 rc=125 になり、独立 clone を渡して回避した。
- 変異 spec の `category` に取れる値は `negative` / `positive` / `both-layers` だけである。
- 親が別 worktree へ `cd` すると、隔離 session の bash guard が以後の全 command を拒否する。
  同じ path で worktree へ入り直すと復帰する。
