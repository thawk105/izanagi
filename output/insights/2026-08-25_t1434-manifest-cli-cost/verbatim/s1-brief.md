# 段 1 brief — [T-1434] task manifest の CLI 入力口と費用の正規化計算

- base: main `c83b5b2c` (command 引数の `003c0499` から main が前進済み。現行 main を base に取り直した)
- branch: `worktree-dev-wave-t1434-manifest-cli-cost`
- 正本: `docs/phase3-t189-model-routing-preregistration.md` §5.2 / §5.3 / §10 / §13、`docs/decisions.md` D674

## scope (閉じる 2 件)

- **(a) task manifest の CLI 入力口**: `tools/codex_reasoning_ab.py` の verb 関数
  (`supervise_pair`, `verify_manifest`, `aggregate_manifest`, `make_packets`, `append_verdicts`,
  `freeze_verdicts`, `reveal_mapping`) は既に `task_manifest: Mapping = TASK_MANIFEST` 引数を持つが、
  `main()` はどの verb にもこれを渡していない。外部 manifest を読む CLI 入力口を新設する。
- **(c) 費用の正規化計算**: 凍結 price snapshot の SKU 単価と receipt の token 数から、
  正規化 cost を計算する。**version の束縛 (実装済み) と cost 計算 (未実装) は別物**であり、
  実装も別の関数・別の失敗理由として分ける。

## scope 外 (明示)

- **(b) adjudication 層の task-specific oracle 対応** (`_load_adjudication`): §8 の独立 oracle
  ledger が未作成のため着手条件を満たさない。段 7 の記録に明記する。
- `price_version` の非 null 拒否 2 箇所: 2026-08-25 に解消済み。再実装しない。
- 事前登録の protocol (estimand, margin, gate 表, oracle, task 除外規則) は一切変えない。

## 確定済みユーザー裁定

- D674: (7) 価格情報の実データ取得は実施する。(1) 電力・標本数下限、(2) 独立 custodian は見送り。
- D95: 実装面は Codex `role=author` が書く。親は実装面を直接編集しない。

## 実測した前提 (brief 前 preflight)

1. `grep -n "cost\|usd\|USD\|unit_price\|price_per" tools/codex_reasoning_ab.py` は **0 件**。
   費用計算はこのファイルに存在しない。
2. `_parser()` (11098-11256) に `--task-manifest` 系の option は無い。`main()` (11259-) は
   verb 関数へ `task_manifest` を渡さない。
3. `_validate_price_version` (2657) と `_validated_slots_price_version` (8732) が
   非 null `price_version` を凍結 version と一致するときだけ受理する。(c) の前提は満たされている。
4. 凍結 artifact `output/t189-routing-preregistration/price-snapshot-v1.json` と
   `price-standard-table-excerpt.html` を pin するのは `tools/codex_reasoning_ab.py:96,106` と
   `orchestrator/tests/test_codex_reasoning_ab.py:130,140` の 4 箇所だけ。**本 wave は両 artifact の
   bytes を変えない** (読むだけ) ため `DW-O09`/`DW-O10` は発火しない。
5. 事前登録文書に whole-file SHA-256 pin は無い (`tools/check_docs.py` の pin は cleanup-branches
   skill だけ)。
6. price snapshot の実データ: `sku_mapping` は `gpt-5.6-sol` / `gpt-5.6-luna` の 2 model、
   単価 category は `input` / `cached_input` / `cache_write` / `output` の 4 つ、
   `price_unit = "per-million-tokens"`、値は decimal 文字列。
   `unknown_token_categories = ["cache_write"]` — receipt に対応 field が無い。
7. receipt 側の token field は `input_tokens` / `cached_input_tokens` / `output_tokens` /
   `reasoning_output_tokens` (8248-8255)。snapshot の `receipt_token_mapping` は
   input = `input_tokens - cached_input_tokens`、cached_input = `cached_input_tokens`、
   output = `output_tokens`、cache_write = 対応 field 無し (空)。
   `reasoning_output_tokens` は `output_tokens` の部分集合で二重計上しない。
8. 集計の軸 `_AXIS_FIELDS` (9280) は `benchmark_task_id` / `stage` / `requested_model` /
   `cache_condition` / `price_version` の 5 つ。cost の attach 先は
   `_replay_manifest` の `resources` 行 (9760-9789) と軸集計。

## 不変条件 (破ってはならない)

- **fail-closed**: 入力が欠ける・型が違う・凍結値と一致しないときは値を作らず拒否する。
  cost を「不明なら 0」にしない。
- **float を使わない**。単価は decimal 文字列であり、`decimal.Decimal` で計算する。
- **`cache_write` は価格不明**。receipt に対応 field が無いので、cost へ黙って 0 として
  混ぜず、「未計上 category」として明示的に出力へ残す。
- `price_version` が null の slot では正規化 cost を生成しない (束縛が無い費用は比較不能)。
- 既存の受理集合を広げない。task manifest CLI 入力口は、既定 (未指定) のとき現行の
  `TASK_MANIFEST` と等価な挙動を保つ。
- 凍結 artifact (price snapshot / 抜粋) の bytes を変えない。
- legacy 互換経路 (schedule descriptor 無し) の uncertified 扱いを変えない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 事前登録文書 §5.2 / §5.3 / §10 / §13 の**到達度記述**の更新は in-scope とする。
  根拠: 同文書は 2026-08-25 に到達度表を実測へ張り替えた前例を自ら記録しており、
  到達度は protocol でなく事実の登録である。実装後も「未実装」と書き続けることは
  台帳の虚偽になる。**protocol (estimand・margin・gate 表・oracle・task 除外規則) は変えない。**
  これが誤りなら、文書更新を段 4 で裁定パッケージへ回す。
- **(P2)** CLI 入力口は `--task-manifest <path>` を各 verb へ足す形とし、
  既定 (未指定) は現行 `TASK_MANIFEST` を使う。新しい manifest 生成器は作らない。
- **(P3)** 費用の正規化計算は**別関数**として実装し、`price_version` 束縛の関数には混ぜない。
  出力は per-run (resources 行) と軸集計の両方に載せる。
- **(P4)** cost の単位は USD、値は decimal 文字列で保持する (JSON へ float を出さない)。

## 成果物の形

- `tools/codex_reasoning_ab.py`: `--task-manifest` の CLI 入力口 + 外部 manifest loader、
  正規化 cost 計算関数 + 出力への接続。
- `orchestrator/tests/test_codex_reasoning_ab.py`: 上記の正例・負例テスト。
- docs: 事前登録文書の到達度更新 ((P1) が段 4 で維持された場合)、worklog / decisions の spool fragment。

## 成果物影響 (DW-G05)

- (a) を実装しないと、**held-out task を CLI から差し替える経路が無く**、事前登録が要求する
  task universe (§6.1) で装置を走らせられない。証拠 (certified 選択) の task 軸が
  T-181 の POS/NEG 2 件に固定されたままになる。
- (c) を実装しないと、§11.2 の resource 系指標のうち**費用が算出されず**、
  resource-overall gate が値を持てない。price version を軸に持つ集計はあるが数値が空のまま。

## 分割方針

- 段 5 の実装子は 2 本。A = (a) CLI 入力口、B = (c) 費用の正規化計算。
  編集面は同一 file だが領域が離れている (`_parser`/`main` 対 集計層) ため、
  **順次投入し親が統合**する (同一 file への並列書き込みを避ける)。
- 段 2/3 は plan 1 本、consult 2 レンズ。
