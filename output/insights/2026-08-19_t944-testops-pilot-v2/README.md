# 有界 task-run 観測 pilot v2 の実装 — 段1〜段6 記録 (2026-08-19)

authority: none
default_effect: production-change

wave = `dev-wave-t944-testops-pilot` / branch `worktree-t944-testops-pilot`
base = main `40a833ed`
commits = `9e81501f` (主実装), `bc59f873` (m03 変異テストfix), `201005ce` (dispatch walltime override)

## 何をしたか

`docs/decisions.md` D341 (2026-08-12 第3束裁定、Q1〜Q3=(a)(a)(a) 確定) の制約下で、
`output/insights/2026-08-12_testops-observation/` が凍結した blocker 9 件・must-fix 11 件
(A1 は refuted 済みで対象外の計20項目) を閉じる実装を行った。9 段の dev-wave 状態機械を
全段実行 (段2 codex plan → 段3 敵対相談2本 → 段4 親裁定 → 段5 実装 (Unit A/B 分割) →
段6 敵対レビュー2本 + fix 3巡 (DW-O16 上限) + 変異事前登録)。

## 主要な設計判断

- **記録先**: `git rev-parse --git-common-dir` の realpath から導出する repo 兄弟
  (本機 `/work/1/SFC/tanab/izanagi-task-runs/`)。digest 方式は不採用 — 兄弟パスは親ディレクトリ内で
  既に一意なため。
- **R-B4SCOPE (最重要の裁定)**: task-run/v1 schema を変更しない制約のため、bounded scope の
  非 CHILD_RC outcome (CAP_OOM・timeout・dispatch infra 失敗) は task_run event を作らず、
  固定 diagnostic のみにする scope 縮小を行った。
- **explicit-only な次世代生成**: 自動 rollover を実装せず、次世代作成は明示 API のみ。
  Python の呼出し規約だけに頼らず call-graph meta-test で機械的に pin した。
- **sidecar は専用 0700 lease directory + 固定 basename** (`pytest-stats.json`)。当初の
  hash ベース命名は既存 `pytest_stats.py` の契約と非互換で、段5〜6 で発見・是正した
  (詳細は下記「主な発見」)。

## 主な発見 (段5〜6 の実測)

1. **cap 判定の迂回 (最重要のバグ、段6 両レンズが独立に検出):** `RootReport.published_run_count`
   が `published` のみを数え `incomplete`/`damaged` を除外していたため、task marker 作成前に
   crash する走行を繰り返すことで cap (10件) を実質無制限に超えられた。cap 分母を
   published+incomplete+damaged の合計へ修正した。
2. **sidecar 統合バグ (段5、親が実測して発見):** `generation.py` の sidecar lease 命名
   (`sidecar-<hash>.json`) が、既存 `pytest_stats.py` の `_create_sidecar()` が要求する
   固定 basename 契約 (`pytest-stats.json`、`O_EXCL` 前提) と非互換で、automatic 経路の
   counts/digest が常に欠測していた。専用 0700 lease directory + 固定 basename の形へ是正した。
3. **`renameat2(RENAME_NOREPLACE)` は `/work` で使えない** (`docs/pegasus-runbook.md:296-298`
   既実測、`docs/failures.md` F22 既存記録)。generation 作成は `os.mkdir` 排他予約 + `os.rename`
   (calibrator precedent) を使う。
4. **段4裁定文の曖昧さによる fix1→fix2→fix3 の往復:** damaged/unknown な root への
   `start_run()` を拒否すべきか否かで3回の fix 往復が発生した。最終的に、pre-existing v1 の
   `test_validate_root_classifies_damaged_and_unknown` が「damaged があっても start は成功する」
   ことを明示的に要求している事実を発見し、これに合わせて確定させた
   (cap 分母修正で実害は既に閉じているため、diagnostic の追加要求は不採用)。
5. **段6所見のうち2件がUnit A/Bどちらの編集権限にも無い (`aggregate.py`・`pytest_stats.py`) ため
   partial にとどまった。** 焦点レビューが「s4-rulingの受入契約はUnit境界より上位」と指摘し、
   Unit A の権限を拡張して3巡目のfixで解消した。
6. **検証実行自体が実運用のrepo兄弟ディレクトリを汚染する** (git-common-dir共有のため、
   どのworktreeでの `run_tests.py` 実行も実 pilot へ記録される)。着地前に発見しクリーンな状態へ
   リセットした。この特性は D66 原設計でも既に観測済みの挙動 (初回pilotが実質1日でcapに到達) で
   あり新規の懸念ではない。
7. **`run_tests.py --force-dispatch` はdispatch walltimeを一切上書きできなかった**
   (`dispatch_compute.dispatch()`自体は`walltime` kwargを公開しているが、呼び出し側が
   到達手段を持たなかった)。hang_risk変異の検証コストをユーザーが指摘したことを契機に発見し、
   `IZANAGI_DISPATCH_WALLTIME_OVERRIDE`環境変数で上書き可能にする最小差分を追加した
   (commit `201005ce`)。テスト・運用専用の逃げ道であり、未設定時の挙動は変えない。

## 変異事前登録

`s4-ruling.md` §5 の方針に基づき、段6のcodex planが18項目を精査し15項目・16変異を登録
(3項目は DW-M01 の単一理由性を確認できず見送り、理由付き)。expected_nodes 22件を実 collection と
突合せ検証し、登録時点では全件一致した。

**m03 (banned-namespace-check) の変異実走で SURVIVED が判明:** 既存テストの2つ目の
parametrize シナリオが `_check_banned_components` を単独で検証しておらず、無関係な
「中間ディレクトリ不在」の別チェックにマスクされていた (DW-M03 の単一理由性違反)。
専用 worktree で Codex にテストのみの fix (`test_external_banned_namespace_is_rejected_with_existing_intermediates`
を新設) を依頼し、`mutation-spec.json` の expected_nodes も追随させて是正した。これは
node 名の表記ミスではなく、テストが意図した不変条件を実際には踏んでいなかったという
テスト被覆の欠落であり、変異検査 (DW-M02) が無ければ気づかなかった。

**m07/m08/m09/m12 の変異実走で MISMATCH が判明 (登録時 expected_nodes が過小、DW-M08違反):**
コード自体は正しく動作しているが、実際の破壊範囲が登録した1〜2件より広かった
(m07: `return`欠落によるfall-throughで非CHILD_RC系5テストが連鎖破壊、m08: `child_started`
強制Trueで関連3テスト破壊、m09: 共有allowlist定数の削除で allowlist 完全性テストも道連れ
[2→3件]、m12: 3ファイル共有の `_SIDECAR_BASENAME` 定数変更で lifecycle/orphan-reclaim/
digest/privacy-sentinel/xdist-attestation の計7件が破壊 [2→7件])。baseline (無変異
dispatch実行、415 passed/1 skipped) で環境要因を排除したうえで、実測失敗集合へ
expected_nodesを補正し独立な再走で再現性を確認して確定させた。

**m16 (repo-head-toctou) は SURVIVED のまま確定 (冗長gate、DW-M03の過剰決定):**
`_git_output()` 自体が呼出し前後で同じ `_verify_directory_binding` を二重に行っており
(`tools/task_runs/ledger.py:474,489`)、削除対象の `start_run()` 側チェックは三重目の
冗長防御と判明した。実害なく、単独変異の証拠から除外した。

**m04 (series-lock-timeout、hang_risk) は matrix から除外:** 3回の実dispatch観測
(各30分以上ノータイムアウト、うち2回はPBS壁時間まで完走) で被験対象の性質
(保護を外すと無限にblockする) 自体は実証済みだが、PBS強制終了されたjobは
`dispatch_compute.py`が期待する正常完了マーカーを残せず、walltime値に関わらず
毎回 orphan-hold に落ちる構造的非互換があった。harness/dispatch tooling側の限界であり、
実装コードの問題ではない。

**最終結果: 14/16 登録変異が KILLED (期待一致)、2件除外 (理由付き、上記参照)。**
段4/6で事前登録した原spec (16変異) は `mutation/mutation-spec-registered.json`、
初回実走 (MISMATCH/SURVIVED発見時) は `mutation/mutation-out-first-full-run.json`、
expected_nodes補正 + m04/m16除外後の最終specは `mutation/mutation-spec-final.json`、
最終確定結果 (14/14 KILLED) は `mutation/mutation-out-final.json`。

## 段8: 自己改善候補 (記録のみ、未実装)

`docs/skill-self-improvement.md` の routing に従い判定。3件とも dev-wave 固有の手順で
`docs/dev-wave/mutation.md` (leaf 節) が行き先だが、同ファイル群は 3層とも予算に余裕が
乏しい既往記録があり、実測に裏付けられた短い追記でも赤になりうる。予算検証を伴わない
実装はせず、記録のみに留めてユーザー裁定へ返す。

1. **「変異harness実行中は対象repoへの一切の書込み (docs下書き含む) を避ける、
   untracked検出で即座に中止する」を DW-M05 近傍へ追記。** 段6 mutation matrix 準備中、
   insights下書きをrepoへ書いてharnessがrc=2で中断した実測に基づく (詳細は decisions
   fragment 未閉鎖残件、および memory `no-tree-writes-during-mutation-run`)。
2. **「harness本体プロセスがdispatch jobより先に死ぬorphan-holdの場合、手動qdelせず
   qstat出力内容で終端を待つ」を DW-M07 近傍へ追記。** 段6 で複数回実測 (詳細は memory
   `mutation-harness-orphan-hold-recovery`)。
3. **`tools/pegasus/dispatch_compute.py` 自体の改修候補 (docs でなく共有 tool 本体):**
   PBS 強制終了された job が正常完了マーカーを残せないケースで、cancel gate の
   `denied()` が理由 (`request-absent` 含む) を問わず `job_may_remain=True` を返す。
   hang_risk 変異を dispatch mode で検証する限り再現する構造的な問題であり、
   本 wave の scope 外 (共有 tool)。次に hang_risk 変異を使う wave で再発した場合に
   優先実装すべき。

## 逐語

- `verbatim/s1-brief.md` — 段1 親brief (実測ベース、規模見積り含む)
- `verbatim/s2-plan.md` — 段2 codex plan v2
- `verbatim/s3-lens-a.md` — 段3 敵対相談 レンズA (正しさ境界)
- `verbatim/s3-lens-b.md` — 段3 敵対相談 レンズB (実効性・全層被覆)
- `verbatim/s4-ruling.md` — 段4 親裁定 (20所見の real/refuted・scope縮小・変異事前登録方針)
- `verbatim/s6-review-a.md` — 段6 初回敵対レビューA (実装正しさ・防壁)
- `verbatim/s6-review-b.md` — 段6 初回敵対レビューB (実効性・見落とし・整合性)
- `verbatim/s6-focus.md` — 段6 統合後焦点再レビュー (fix後の closed/partial 対応表)

## scope外 (裁定パッケージへ送らず、s4-ruling.mdで親が確定させた事項)

- D220 の再訪条件 (token 消費 event を次世代 pilot の設計に含める) — ユーザーの3制約に token計装は
  無いため対象外。
- CLI の一般エラー表示規約 (task-run 以外の既存コマンド) — task-run が新設する経路にだけ privacy
  強化を適用し、既存の一般エラー表示は変更しない。
- dispatch の汎用 request/receipt format の既存 argv/repo_root 保持 — 本 wave が新設した漏洩では
  ないため是正しない。
