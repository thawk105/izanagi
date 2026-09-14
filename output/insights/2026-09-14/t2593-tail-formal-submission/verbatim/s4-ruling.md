# 段 4 裁定 — [T-2593] 静的 tail 本走の投入経路

親が段 3 の全所見を real / refuted、採用 / 不採用、scope 内 / 外で裁定する。
各採用項には放置時の成果物影響を 1 行で付す。

## 0. wave 開始後の更新の取り込み

local main が `3b80b5a96` → `af3762d62` へ進んだ。編集面 (2 script、driver、事前登録、
関係する 2 test file) への差分はゼロであることを実測した。新規裁定 16 項のうち
本 wave を止めるものは無い。ただし次の 2 つは本 wave の設計に効く。

- **項 7 (T-2267)**: 「対象を限った測定の入り口は今は作らない」「実測が無いまま class を動かさない」
- **項 8 (T-2518)**: 「依存物をつなぐ最小の入り口は新設しない」

## 1. 集団入口の形 — P1-a を撤回し、plan 案を採る (luna-6 は real だが不採用)

**裁定: 新しい `tools/pegasus/*.sh` を作らない。** 集団入口は
新規文書 `docs/b10-backoff-static-tail-submission.md` の操作手順とし、
その argv が driver の CLI から乖離しないことをテストで固定する。

- luna-6 の指摘 (「文書だけでは終了コード伝播が検証対象にならない」) は **real**。
  しかし新規 `.sh` を `tools/pegasus/` へ置くと `admission_registry.json` へ class を宣言する
  必要が生じる (`test_hooks.py` の inventory 集合一致、親が現物で確認済み)。
  本 wave には集団 report を実際に走らせる campaign が存在しないので、
  `local-ok` を主張する実測を持てない。これは項 7 (ii) が禁じる形にあたる。
  置き場所をずらして inventory 検査を避けるのは不正直なので採らない。
- 3 走を 1 集団として束ねる仕組み自体は**既に 2 箇所に在る**。
  (a) 投入 receipt の `group_id` と workload ごとの `output_root`、
  (b) driver の `report` が 3 つの campaign lock 間で cohort identity を突き合わせる経路。
  欠けていたのは (a) から (b) への、乖離しない手順である。それを足す。
- 終了コード契約は、文書の argv を driver の `main()` へ通すテストで固定する
  (3 本必須・invalid で rc=1)。**shell wrapper を作らない以上、wrapper の rc 伝播は検査対象に
  ならない** — この限界は insight に明記する。
- **成果物影響:** 放置すると 3 campaign を束ねる手順が人の記憶に残り、
  cohort report の入力取り違えが検出されない。

## 2. 採用する must-fix

### (a) sol-1 — 「1 bit 不変」の比較契約を定義する [real / 採用]

親 brief の不変条件 1 は文字どおりには達成不能である。`JOB_SCRIPT_SHA256` は
今回編集する job script の bytes から計算されるので、旧系列の qsub argv にも必ず現れる。

**契約:** 旧系列の不変性テストは argv の bytes 一致ではなく次を固定する。
- 可変値 (job script SHA / group id / nonce / 日時 / PID) は**値を消さず、
  その場で正しさを検証する**: SHA は現行 job script の実 bytes の sha256 と一致すること、
  nonce は 3 job と manifest 事象で同一であること、group id は固定部と workload suffix に分かれること。
- それ以外の環境変数名・値・順序、workload 3 本の fan-out、出力 path の組み立ては完全一致。
- **成果物影響:** 放置すると誤った script SHA を渡す編集が「argv 不変」の緑をすり抜け、
  旧系列の job が実行前に拒否される。

### (b) sol-2 — 投入 receipt そのものを観測する [real / 採用]

qsub argv だけでは、manifest の `schema_version` を変える編集を検出できない。
submit テストは既に script を実起動するので、生成された receipt の
schema・event 種別・run_kind・argv との対応も観測する。新しい台帳は作らない。
- **成果物影響:** 放置すると旧 3 系列の投入台帳の schema が黙って変わり、既存 consumer の参照が切れる。

### (c) sol-3 — 「8 commit + execution 実在」の十分性を組合せで検査する [real / 採用]

この 2 条件は単独では成功の十分条件でない。現行は sweep の非ゼロ終了を job script が
先に止めるので finalizer に到達しない。**その組合せをテストで固定する**:
「8 commit と execution が在るが driver が rc≠0 / timeout」で `completion.json` が出ないこと。
新しい gate は足さない。
- **成果物影響:** 放置すると失敗終了の握り潰しを入れる編集が、不完全な走行に完了印を発行させる。

### (d) luna-4 — job テストの断片間の到達性を検査する [real / 採用]

断片ごとの性質検査だけでは、入力検査 → driver 起動 → 完了処理の接続を壊す編集を見逃す。
少なくとも 1 本は、入力検査の位置 (scratch 作成より前) と driver argv を**同じ走行で**観測する。
finalizer は heredoc の開始 (`:618` 付近の argv 行) から終端までを連続して抜く。
既存の `_shell_function()` はトップレベル heredoc に流用できない (luna が読解で指摘、親も現物で確認)。
- **成果物影響:** 放置すると新系列が job 内で拒否される配線が緑のまま land する。

### (e) luna-5 — submit 負例の観測点を増やす [real / 採用]

rc=2 と qsub 未呼出しだけでは「副作用より前に拒否」を証明しない。
負例は **queue 照会 stub の未呼出しと receipt file の不在**も観測する。
既存の位置検査は `SystemExit(文字列)` で rc=1 になるので、
新 explore 検査は rc=2 に揃える (既存検査の rc は変えない)。
- **成果物影響:** 放置すると拒否された投入でも receipt が残り、集団の参照に不要な記録が混じる。

### (f) luna-2 — 実行環境の成立条件を手順へ書く [real / 採用、ただし gate は足さない]

親が現物で確認した事実:
- job script の必須 command 一覧 (`:218-222`) に `git` が既に入っている。新 driver の
  `load_preregistration()` が使う `git rev-parse` / `merge-base --is-ancestor` / `git show` は動く。
- `REPO_ROOT` は `PBS_O_WORKDIR` 由来 (`:239`) であり、qsub は作業 dir を指定しない (`:190-192`)。
  **投入は repo root から行う必要がある** — これは旧 3 系列でも同じ既存条件である。
- 新系列に固有の前提は、指定 commit が job checkout の HEAD の祖先であること、
  および作業ツリーの事前登録 bytes が その commit の blob と一致することである
  (`load_preregistration()` が両方を要求する)。

**裁定:** これらは新しい gate を足さず、`docs/b10-backoff-static-tail-submission.md` の
前提条件として書く。job script 側に commit 解決の先回り検査を足さない (仮想リスク向けの gate に当たる)。
- **成果物影響:** 放置すると前提を満たさない投入が計算ノードで停止し、campaign が生成されない。

### (g) sol-4 — 期待 literal は事前登録の現物から取る [real / 採用、nit]

テストの期待 literal (`t2500-tail-formal`、`t2500-backoff-static-tail-formal`) は
事前登録 §8.2 の逐語から固定し、検査対象の shell から逆算しない。逆算すると二重定義の
片側だけを変える編集に追随して緑になる。

### (h) sol-6 — `--help` の順序を負例で固定する [real / 採用、nit]

新 flag を認識するようにすると、`--run-kind extended --explore-campaign /x --help` の
終了コードが 2 から 0 へ変わる。これは「旧系列の受理集合を狭める」向きではないが、
親の不変条件から外れる挙動変化なので、**偶発でなく意図として負例テストで固定する。**
P1-c の拒否は既存の run-kind `case` 検証と同じ位置 (引数 loop の後) で行う。

## 3. 採用しない所見

- **sol-5 (explore campaign の identity を追加固定する gate)** — scope 外。
  親も読解で確認した: `--explore-campaign` は correctness mode の比較基準を供給するだけで、
  検査命令・反復数・閾値は spec 側から来る。正しさを緩める向きの経路ではない。規律 2 に抵触しない。
- **luna-3 (既存 `OUTPUT_PARENT` の正規化前しか検査しない穴)** — real だが scope 外。
  既存 3 系列の受理集合を変える修正になる。insight へ記録し、起票は段 7 で判断する。
- **luna-7 (新入口を実起動して argv と rc を観測せよ)** — 1 の裁定で新入口を作らないので
  対象が消える。文書 argv を driver の `main()` へ通すテストで置き換える。

## 4. plan v2 — 実装する変更面

| # | file | 変更 |
|---|---|---|
| 1 | `tools/pegasus/submit_b10_backoff_grid.sh` | usage・引数 loop・`case`・`QSUB_ENV` に新系列と新 2 入力 |
| 2 | `tools/pegasus/b10_backoff_grid.sh` | `case`・入力検査・stage 名・新 driver 起動・finalizer の新系列分岐 |
| 3 | `docs/b10-backoff-static-tail-submission.md` (新規) | 投入手順・前提条件・集団 report の argv |
| 4 | `orchestrator/tests/test_b10_backoff_grid_submit.py` (新規) | submit 側のテスト |
| 5 | `orchestrator/tests/test_b10_backoff_grid_job.py` (新規) | job 側のテスト |
| 6 | `orchestrator/tests/test_backoff_extended_sweep.py` | 回数 pin (`:1705` `:1842`) の追従のみ |

**触らないもの:** 事前登録、driver 本体、`admission_registry.json`、`hooks/`、
既存 3 系列の受理集合・成果物名・report schema、`EXTENDED_SWEEP_US` を pin するテスト。

## 5. 変異事前登録 (DW-M01、段 4 分)

実装後に、各変異の赤理由が一つに絞れることを確認してから本登録する。

| # | 位置 | 変異 | 期待 kill |
|---|---|---|---|
| M1 | job の新系列 driver path | 新 driver → `backoff_extended_sweep.py` | job argv 完全一致テスト |
| M2 | job finalizer 新系列 | `!= 8` → `!= 5` | 8 commit テスト |
| M3 | job finalizer 新系列 | 要求 stem を旧 stem へ | stem テスト |
| M4 | submit の `QSUB_ENV` | `B10_EXPLORE_CAMPAIGN` を落とす | 転送テスト |
| M5 | submit の commit 検査 | 正規表現を緩める | 負例テスト |
| M6 | submit の P1-c 拒否 | 旧種別 + 新 flag を受理へ | 負例テスト |
| M7 | job の新系列 argv | `--run-kind` を足す | 新 driver argv テスト |
| M8 | job の extended 分岐条件 | 新系列も extended 経路へ流す | 旧系列不変テスト |
| M9 (正例) | — | 妥当な commit + explore + 新種別 | qsub へ到達すること (過剰拒否の検出) |
| M10 | job の入力検査位置 | scratch 作成の後ろへ移す | (d) の到達性テスト |
| M11 | submit の receipt schema | `v1` → `v2` | (b) の receipt 観測テスト |
