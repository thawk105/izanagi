# fig11 — A-6 read-heavy 正式 certification (attempt `a6-20260908b`、outer `reject`) の exact 2 cell 図: 生成器の一般化・test・着地の開発記録

これは既存測定 (attempt `a6-20260908b`、稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md`) の
**図を作る開発記録**である。新しい性能測定、certification の昇格、反復 attempt、有意差判定、B-10 との pool は行わない (D12、D1993 項 2、[T-2430])。
台帳 ID は未起票 (出所 = 論文ストーリー 2026-09-20 版 §8 第 2 (A-6) と単独稿の限定 11「図は無い」)。

## 成果物と一次資料

- 図 11: `docs/paper-story/figures/fig11_a6_certification_reject.{png,pdf,provenance.json}` (着地 SHA-256 は figures README の fig11 節が正本)。
- 生成器: `tools/plotting/plot_a2_certification.py` (fig6 と同じ file を in-place で一般化。新 file は作らない)。test: `orchestrator/tests/test_plot_a2_certification.py`
  (87 → 111 node、既存 test の期待値は不変、exact pin 2 件を A-6 を含む形へ拡張)。
- docs: `docs/paper-story/figures/README.md` (一覧 1 行 + fig11 節)、`tools/plotting/README.md` (plot_a2_certification 節へ A-6 の段落)、
  `docs/paper-story/README.md` (results 表の A-6 行「図は無い」→ 図 11、results 系列規則の後ろに「A-6 単独稿の限定 11 への追補 (2026-09-20)」段落)。
- 入力: 権威 bytes `output/insights/2026-09-08_t2411-paper-story-a6-certification/{certification.json,raw-manifest.json}` (SHA-256 `3a9505b0…` / `8d179535…`、稿 §5.1 と同値)、
  durable authority `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` の 6 file (campaign WAL・raw cell 2・campaign lock・claim・条件関門受領証、
  raw-manifest の SHA-256 で束縛。着手時に 6 file とも一致を実測)。5 標本は durable にだけあり、certification.json は median だけを持つ。
- **稿の bytes は変えない。** 稿は results 系列の凍結物 (稿冒頭・`docs/paper-story/README.md` の同系列規則) で、fig11 の provenance が稿を `caption_source` として
  SHA-256 `34a968428f867ce26479abe37320946b6eb8149007244dfe1d18a18446633850` で束縛する。依頼文の「単独稿の限定 11「図は無い」を更新」は、
  paper-story README の results 表行と追補段落で行った (同 README の T-1998 単独稿の読解上の追補・C14a 追記と同じ型。fig8b / fig10 の wave も稿を触っていない)。
- 値の出所・限定・caption・proof chain は figures README の fig11 節と稿に置き、本 README には再掲しない。

## 設計判断 (段 4 裁定 `verbatim/s4-adjudication.md`、段 6 裁定 `verbatim/s6-adjudication.md`)

- (P1) 稿 bytes 不変・README 追補で「限定 11」を更新 (上記)。レビュー A / B とも妥当と判定 (A は「稿本文を更新したとは言わない」と付記、そのとおり書いた)。
- (P2) 生成器は新 file でなく in-place 一般化: study → {表示名, caption_source} の exact 2 件の `STUDY_PROFILES`、pin 表 `CANONICAL_SHA256` に A-6 を足して 3 leaf、
  workload 数 N は embedded policy から導き、外部入力の閉包は 6 × N file、request / created_utc の一意検査は N、layout check は 2 行 × N 列。legacy profile は A-2 のみ。
  **着地済み fig5 / fig6 / fig7 の bytes・caption・artist 射影は不変** (fig6 の landed provenance を `validate_repo_closure` に通す test `test_a2_current_full_caption_is_unchanged_for_landed_fig6` が守る)。
  **再生成する current-full の provenance には top-level `study` が加わる** (着地済み provenance は key を持たず、読取側は無ければ A-2 と扱う。レビュー A-2 の書き分け)。
- (P3) A-6 caption の固定文は稿 §0 主判定文と §4 限定 1・2・3・4 (i)〜(v)・5・6・7・9 から英文化。A-2 固有の末文 (older series / sign difference) と
  「Top-row y axes are scaled independently by workload」は入れない。B-10 は「履歴的照合であって独立再現でなく pool しない」の 1 文だけ。
- 段 6 で採用した所見: B-1 (must-fix) abort 率は「5 rep のうち throughput が median に最も近い rep の 1 観測 (runner の代表 rep 規則)」で "aggregate" と書かない、
  B-2 正しさ文を 3 文に分け限定 (iii)(v) を足す、対応表の 2 点 (campaign claim recorded at <時刻>、限定 2 の外挿禁止)、A-3 / B-3 fig11 着地 test に provenance と
  tracked certification.json / raw-manifest の値の直接照合を足す (`validate_repo_closure` 本体は不変)、A-4 / B-5 README の pin 表と study 表の書き分け・図中ラベル・適合節の短縮、
  A-1 / B-4 変異 m1 / m6 の再照準 (下)。不採用: `check_figure_layout` の冗長条件の削除 (害なし・受理集合不変)、producer 迂回や fixture 一般化。
- 軽量版 (DW-C00): 段 2・3 省略。受理集合 (study) が広がる実装面なので段 6 の独立レビュー 2 本は省かない。段 5 Codex author 1 本、段 6 レビュー 2 本 + fix 1 本 + 焦点再レビュー 1 本。

## 経過 (2026-09-20 JST)

- 13:25 worktree (`worktree-dev-wave-fig11-a6-certification`、base local main `947fd160a`)。submodule 3 段とも初期化、gate rc=0。生死確認: 現行生成器 + A-6 入力 → rc=2「path is not in repository-owned pin table」、出力 0 件。
- 13:44〜13:55 段 5 author (Codex gpt-6-astra、reasoning medium、26 call、644 s、accepted): 生成器 +78/−23、test +323/−2。実データ生成 rc=0、稿との照合一致 (median 2・effect・abort 率 2・correctness)、
  fig5 / 6 / 7 の landed provenance は `validate_repo_closure` 通過。
- 13:57 焦点走 1 (request 12602): 110 passed / 1 failed (fig11 未着地の期待赤)。13:58 親が login (pegasus02、計測機の外) で fig11 生成 rc=0。README 編集後の焦点走 2 (12618): 111 passed。
  commit `90e74e909` (実装) と `ffcee706b` (図 + docs)。
- 14:12〜14:17 レビュー A (過剰・削除、NO-GO、must-fix 1 / should 2 / nit 1、12 call 248 s) と B (正しさ境界・整合、NO-GO、must-fix 1 / should 3 / nit 1、12 call 253 s)。
  両者とも SHA-256・標本・median・effect・外部 6 file の一致を一次資料から再確認。
- 14:2x local main `d4af98f15` (T-2610 docs wave) を `--no-ff --no-commit` で取り込み、figures README の衝突 2 箇所 (一覧の fig10 行 / 末尾の fig10 追補) を両側保持で解決 (`33db2ed88`)。
- 14:21〜14:27 fix1 (Codex author、11 call、300 s、accepted): A-6 caption と着地 test の直接照合、固定文 test の追随。14:2x 親が図を再生成 (PNG bytes 不変、PDF / provenance 更新)、
  README fig11 節へ所見を反映 (`readme_fix1.py`、exact 12 edit)。焦点走 3 (12690): 111 passed。commit `bdc6e8401` (fix) と `02fa41e25` (図 + README)。
- 14:36〜14:41 焦点再レビュー (11 call、208 s): closed 8 / partial 1 (A-2 の書き分けの文書化 = plotting README と worklog に未記載、順序どおり) / regressed 0、新規所見なし。
  14:42 plotting README に A-6 段落を足して閉じる (`c699d67b1`)。DW-O26 の consumer 焦点走 4 (a2 / b7 / a1 / b10 / s1_9pair / check_docs / plain_runner、request 12706): 828 passed / 3 skipped
  (skip は本 wave の test に無い既存 file 由来)。
- 14:44 local main `4726b6493` (S-1a 稿 wave) を取り込み (衝突なし、`bb3a2f590`)。check_docs 違反なし、全史 provenance 監査 新規違反なし。

## 変異の終端

固定 anchor は `bb3a2f590c86aa8f082eab27ca7e9dbd5ff98cb5` (最終 tip。02fa41e25 → 差分は docs と merge のみ、変異対象 2 file は同一 blob)、spec は `mutation-spec-v2-final.json`
(SHA-256 `b0c303d8cf341fc1bd39e287bbd16e96287c0f119c10ceacde4ea2b789f80ae3`)、11 件 (positive 1 + negative 10。段 6 で m6 を m6a = legacy が A-6 study を受理 / m6b = current-full の
受理集合から A-6 を落とす、の 2 本へ分けた)。runner は `tools/mutation_harness.py --runner-mode dispatch --detached` を主 repo の登録 worktree `.codex/worktrees/mut-fig11-a6`
(固定 commit、submodule 初期化済) に直接当て、test runner は `run_tests.py --force-dispatch orchestrator/tests/test_plot_a2_certification.py -q -rf` (計算ノード)。
期待 node は同じ経路の probe (anchor `02fa41e25`、全件 SURVIVED 登録、`mutation-probe-results.json`) で観測した赤 node の完全集合 (`mutation-expected-nodes.json`)。

単一理由性の裁定: m1 の既存 `test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs` は pin 表不在で手前の層が拒否するため検出根拠から外し、
主検出は `test_a6_pin_drift_is_rejected` (変更前 hash を保持して空白を足す) と `test_current_cli_reads_repository_owned_pin_table` (同層)。
current-full の未知 study 拒否は生成器が先・producer が背後の冗長 gate なので単独変異の証拠から外し、m6a (legacy 経路、他層なし) と m6b (A-6 正例群で殺す) に分けた。
m5 は caption の固定文削除で fixed-literal test と着地 closure test (provenance の caption と再構成の不一致 = fail-closed) の 2 本が赤になる。m2 / m6b は A-6 の正例 test 群
(15 / 16 node) が一斉に赤になる = 受理集合の縮小を検出する正例。

## 変異 final の実測

本走 (2026-09-20 14:53〜15:23 JST、`mutation-final-results.json` / `mutation-final-attempts.json`、計算ノード dispatch 13 走): **baseline PASSED (105.6 s)、m0 SURVIVED、
m1〜m9 の negative 10 件すべて KILLED、期待 node 完全集合 11/11 一致、MISMATCH / PARSE_ERROR / TIMEOUT はすべて 0**。
m1 は `test_a6_pin_drift_is_rejected` と `test_current_cli_reads_repository_owned_pin_table` の 2 本、m2 は A-6 正例 15 node、m3 は caption_source test と CLI 3 成果物 test の 2 本、
m4 は wrong-axes-count test 1 本、m5 は fixed-literal test と着地 closure test の 2 本、m6a は legacy A-6 拒否 test 1 本、m6b は A-6 正例 16 node、m7 は重複 request / 時刻 test 2 本、
m8 は着地 test の全欠落 test 1 本、m9 は fig6 landed closure test 1 本が赤になった。probe (anchor `02fa41e25`) と final (anchor `bb3a2f590`) の観測 node は同一。診断文字列だけの赤は無く、
いずれも受理集合または fail-closed 挙動の変化で殺した (m2 / m6b は正常な A-6 入力が拒否される = 受理集合の縮小、他は拒否・束縛の消失)。harness は `repo_head`・clean tree・flock を束縛し、
spec の `old` は各 1 箇所 (11/11)。

## レビュー・変異で残った限界

- `validate_repo_closure` は provenance の自己整合と hash (tracked 入力・出力の SHA-256、external_inputs の各 path が raw-manifest に同じ SHA-256 で載ること、
  cells から再構成した artist / caption の一致) を見るだけで、権威 bytes との値の再照合は fig11 の着地 test の直接照合が担う (レビュー A-3 / B-3)。durable root との再照合は
  root が読めるときだけ (`validate_external_sources`)。
- `_study_label` の「`study` key が無ければ A-2」は着地済み fig5 / 6 / 7 の互換既定で、新規生成は必ず `study` を書く。着地 provenance から `study` を落とすと A-6 の caption は
  A-2 版として再構成されて閉包が壊れる (レビュー A-3 が実測)。
- 図の上段は 1 列 (figsize 8.0 × 7.6 in) なので 2 cell の間が広い。値は直接ラベルと caption に出す。
- 稿の限定 12 件のうち caption に写したのは §4 項 1〜7・9 の趣旨と項 12 (Conditions の no perf) で、項 8 (反復しないことで失うもの)・項 10 (policy bytes の 1 key 差) は稿にだけある。項 11 は図自身が答える。

## 工数

- codex 子 5 本 (author 1 = 26 call / 644 s、review 2 = 12 call / 248 s と 12 call / 253 s、fix 1 = 11 call / 300 s、focus 1 = 11 call / 208 s。全て gpt-6-astra / medium、accepted)。
- 計算ノード job: 焦点走 4 (12602 / 12618 / 12690 / 12706)、変異 probe 13 走 + final 13 走。作図は login。
- 受入全走は本記録 commit の後に land 対象 tip へ投入する (DW-O12)。結果は job dir の receipt (`acceptance-receipt-final-<n>.json`) と land の receipt 束縛が正本で、本 README には書かない。
