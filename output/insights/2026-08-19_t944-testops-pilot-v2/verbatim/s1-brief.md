# 段 1 brief v2 — dev-wave-t944-testops-pilot

## 依頼と確定済みユーザー裁定

[T-944]。`docs/decisions.md` **D341** (2026-08-12 第 3 束裁定) が Q1〜Q3 を確定済み — もはや
裁定待ちではなく実装待ち。

- **Q1=(a):** 有界の次世代 pilot として再開。cap 到達で再凍結、rollover は自動化せず次世代開始は
  明示裁定のまま (D66 (6) の予約を維持)。
- **Q2=(a):** 記録先は **repo 外・repo の兄弟** (本機 `/work/1/SFC/tanab/izanagi-task-runs/`、
  未使用パスと実測確認済み)。改竄検出は主張しない (git 履歴 anchor を失う代償を受け入れる)。
- **Q3=(a):** 被覆は `tools/run_tests.py` 経由のみ。素の pytest・mutation local mode・別 clone は
  未被覆と明記し「全走行を記録する」と称さない。

closure 対象は `output/insights/2026-08-12_testops-observation/verbatim/` の blocker 9 件・
must-fix 11 件 (s3-lens-a.md ×2 refuted 済み A1 除く、s3-lens-b.md、集約は s4-ruling.md §1)。
本 brief では再掲せず file:line だけを渡す (下記アンカー表)。**D220 の再訪条件 (token 消費 event を
次世代 pilot の設計に含める) は本 wave の scope 外** — ユーザーの 3 制約に token 計装は無い。

## 不変条件 (緩めない)

- `run_tests.py` の 4 gate (`_is_full_suite`/`_has_no_execution_flag`/`_has_dispatch_exempt_flag`/
  `_is_acceptance_run`、L388-560 + 定数表 L74-122) を 1 bit も変えない。pytest argv に flag を足さない。
- 書く側 fail-open (child rc を絶対に置換しない) / 読む側 fail-closed。ただし fail-open は**無言**でよいとは
  もう言わない — M1 により診断可能にする (下記 (P4))。
- `KeyboardInterrupt`/`SystemExit` は記録経路のどこでも飲み込まない (D66 (3)、A11)。
- 台帳は `authority: development-observation-not-evidence` を保つ。node ID・selector・argv・repo
  file path を objective/suite_id/生成 path/log の**どこにも**書かない (A9)。schema 世代は増やさない
  (`task-run/v1` のまま)。
- 凍結済み `output/task-runs/` (tracked) には新規 start を一切させない。破損/unknown entry の検出を
  pilot 閉鎖条件 (`PilotClosedError` 予定) に混ぜない — 混ぜると破損を隠して次世代を作ってしまう
  (実測: `ledger.py:551-552` の damaged/unknown raise は L544-557 の 3 条件と別の独立 raise)。
- 新設する `repo_root` 引数は CLI から到達不能にする (`cli.py` に `--repo-root` 相当の flag を足さない)。
  A8 (caller が任意 repo の HEAD を偽装できる) への構造的対策。

## 実測で確定した現況 (旧 insight の file:line は全部ズレていたため再実測済み、詳細はアンカー表)

`start_run()`(`ledger.py:527-624`) は `repo_root` 引数を**まだ持たない**。`base_commit` は
`root` 自体を git cwd にする (`:563`) ため、root を repo 外に置くと現状は `_filesystem_repo_root()`
(`:296`) が `.git` marker 探索に失敗して即 `LedgerError` になる — 引数追加は Q2(a) を成立させる
必須変更。banned-namespace 検査 (`_assert_safe_root`, `:144-156`) には TOCTOU がある (`:156` が
resolve 前の `root` を return)。`_run_bounded_scope_and_record()` の B4 バグ (`:1549`,
`CHILD_RC` 以外は無条件 return) は現行コードに実在。`test_cap_rollover_creates_second_v1_generation`
は repo 全体で 0 件 (旧 plan の想定名のみ、未着手)。repo 兄弟 path を導出する共有 helper は repo 内に
**存在しない** (`thirdparty-cache` の解決は git-common-dir でなく祖先8階層探索、`dev-wave-jobs` は
手動環境変数) — 新規実装が要る。既存テスト 39+55 個は全て手動 ID 前提で、無手番自動経路のテンプレートには
ならない。

## 規模見積り (実測ベース、着手前提示。D205/D220 に触れうるとのユーザー認識どおり P4 は撤回)

旧 plan v1 の 142 行目標は M5 (敵対相談) が「安全要件と両立しない」と判定済み。人為的な行数上限は
置かない。現行ファイル実測 (ledger.py 987行/schema.py 620行/cli.py 254行/run_tests.py 1920行) と
20 項目の要求から積み上げた production 差分の見積り (下記見積り表): **概算 320〜505 行**
(D220 が過大として不採用にした 645〜816 行の別機能より小さいが、旧 142 行目標より確実に大きい)。
test 差分は旧 plan (新規 2 file・19 test 案) より確実に増える (TOCTOU・series lock 例外安全性・
crash recovery・cap race・B4・privacy sentinel・SIGINT 4 点等のシナリオが増えるため) — 段 2 の
file:line plan で確定させ、段 5 実装後に `git diff --stat` で実測値に置き換える。

## 成果物の形

`tools/task_runs/generation.py` (新規、series/generation manager) + `ledger.py`/`schema.py`/
`cli.py` の最小追加 + `run_tests.py` の記録配線変更 + `orchestrator/tests/` の新規・更新テスト +
`output/task-runs/README.md` の世代契約更新。

## (P1) 並列分割方針 — 攻撃対象

**Unit A (ledger-core, 先行):** `tools/task_runs/{ledger,generation,schema,cli}.py` +
`orchestrator/tests/test_task_run_ledger.py` + 新規 `test_task_run_generation.py`。
A3/A4/A5/A7/A8/A9/B1/B2/M2/M4 を閉じる。M1 の診断は generation.py の公開関数が
`(result, diagnostic: str|None)` 型で返す契約にし、Unit B が消費できるようにする (未定なら
段 2 で codex が具体案を出す)。
**Unit B (run_tests 統合, 後続):** `tools/run_tests.py` + `orchestrator/tests/test_run_tests_task_run.py` +
新規 `test_run_tests_testops_observation.py` + `output/task-runs/README.md`。A2/A6/A11/B3/B4/M1(残)/M3
を閉じる。Unit A 完了後、その所有パス限定 patch を適用してから投入する (`DW-S05-A`)。

## (P2) repo 兄弟 path 導出 — 攻撃対象

`git rev-parse --git-common-dir` の realpath の親を repo root とし、`<親>/<repo名>-task-runs/` を
既定 base にする (実測: 本 worktree でも `/work/1/SFC/tanab/izanagi/.git` に解決、linked worktree
全体で共有される)。plan v1 の digest 方式は**不要と判断** — repo 兄弟は親ディレクトリ内で既に一意
(別 clone は親が違うので自然に分離、共有拡大の心配がない)。命名 precedent 5 件
(`izanagi-{exploration,home-archive,jobs,thirdparty-cache,thirdparty-deps}`) と整合。

## (P3) M3 (trigger 無手番化) は簡素側に倒す — 攻撃対象

新しい trigger 分類軸を発明せず、自動記録は `trigger=unspecified` のまま README に既知の限界として
明記する。理由: 呼び出し経路 (direct/dispatch/scope) は別 field で既に区別可能になる予定であり、
trigger 独自の再設計は D205 の最小主義に反する疑いがある。

## wave 形

`run_tests.py` の記録配線 (全 wave が経由する共通経路) に触れ、記録先の設計択一もあるため
`DW-C00` の軽量版に該当しない。段 2・3 の敵対子、段 6 の review 2 本を省かない。

## 成果物影響 (DW-G05)

実装しない場合: task-run 観測はゼロのまま (現状維持)。certified 選択・レポート・3 台帳・受理集合は
**変わらない** (D13/D66 により証拠から構造的に分離済み)。変わるのは開発運用の可観測性のみ。
個別 20 項目の「直さない場合」は s3-lens-a.md/s3-lens-b.md の各 (d) 欄が権威。

## アンカー表 (段 2 codex が file:line 起草に使う実測済み現況)

### tools/task_runs/ledger.py (987行)
- `:49-51` `_BANNED_OUTPUT_NAMESPACES` / `:144-156` `_assert_safe_root()` (TOCTOU: `:156` が
  resolve前rootをreturn) / `:159-172` `_ensure_root()` / `:296` `_filesystem_repo_root()` /
  `:307,:326` `_git_run()`/`_git_output()` (GIT_* 除去済み安全パターン、repo_root 実装で再利用可) /
  `:362` `init_pilot()` / `:527-624` `start_run()` (`:538` `_ensure_root` 呼出、`:544-548` final
  marker raise、`:551-552` damaged/unknown raise (別条件)、`:553-554` max_task_runs、`:556-557`
  max_days、`:563` `base_commit = _git_head(root)`)

### tools/task_runs/schema.py (620行)
- `:25` `SAFE_SLUG_RE` / `:287-289` objective 検査 (長さ・改行・`://` のみ、`/` 未禁止) /
  `:249-497` `validate_pilot()`〜`validate_documents()`

### tools/task_runs/cli.py (254行)
- `:26` `_DEFAULT_ROOT` / `:29-33` `_root(args)` / `:45` `--root` help / `:49-125` サブパーサ群

### tools/run_tests.py (1920行)
- `:65-67` 定数 / `:74-122` 4gate定数表 / `:388-560` 4gate本体 / `:836-864` `_record_task_run()`
  (既に Exception 二重捕捉、頑健) / `:867-927` `_call_and_record()` / `:930-937`
  `_dispatch_environment()` (AUTO_RECORD 相当 marker 未実装) / `:973-1025` `_dispatch_and_record()` /
  `:1521-1574` `_run_bounded_scope_and_record()` (`:1549` B4 バグ実在: `CHILD_RC` 以外は無条件
  return、記録未到達) / `:1678-1689` `_dispatch_result()` (ID無し早期return) / `:1913-1916`
  `main()` 末尾 (ID無し早期return)

### 既存テスト (テンプレート、全て手動ID前提)
- `orchestrator/tests/test_run_tests_task_run.py` (1029行/39関数): `:54` opt-out契約、`:177`
  login parent、`:216` force-dispatch、`:363` cap-oom-fallback (B4根拠)、`:396` scope-child不能、
  `:522` SIGINT非握り潰し (A11、手動経路のみ要拡張確認)
- `orchestrator/tests/test_task_run_ledger.py` (1075行/55関数): `:885` 11走目cap拒否、`:898`
  age-cap、`:915,:920` evidence-namespace拒否 (既存)
- `test_cap_rollover_creates_second_v1_generation`: repo全体 0件 (未着手、旧名のみ)
- `orchestrator/tests/conftest.py`: `:674,:697,:780` 3 hook、`:692,:713,:726,:734,:744,:802`
  `except Exception: pass` (A1 refuted の根拠、現存)

### repo 兄弟 precedent
- `orchestrator/campaign/sort_swo_oracle.py:1140-1145` (thirdparty-cache、祖先8階層探索、
  git-common-dir 不使用 — 命名規約のみ precedent)
- `docs/pegasus-runbook.md:288` (`IZANAGI_PEGASUS_THIRDPARTY_CACHE` 命名実例)、`:781`
  (`IZANAGI_DEV_WAVE_JOBS_DIR` 手動環境変数)
- `docs/decisions.md:15116-15161` (D341 全文、`:15122` 裁定確定文、`:15151-15155` home汚染却下案)

## 見積り表 (production 差分、テスト・docs 除く)

| 対象 | 見積り行数 | 主な要求 |
|---|---|---|
| `generation.py` (新規) | 180-260 | base解決・banned namespace再検査(TOCTOU安全)・
`.generation.lock`(例外安全/timeout/O_NOFOLLOW)・世代発見/明示専用作成・series fail-closed reader・
M1診断返却 |
| `ledger.py` | 25-45 | `repo_root`引数(CLI非到達)・`PilotClosedError`分離・TOCTOU修正 |
| `schema.py` | 20-35 | objective の `/` 禁止等 privacy 強化 |
| `run_tests.py` | 90-150 | 3経路 lazy session・全子envへAUTO_RECORD marker・B4修正・SIGINT 4点監査 |
| `cli.py` | 5-15 | help文言 |
| 小計 | **320-505** | |
