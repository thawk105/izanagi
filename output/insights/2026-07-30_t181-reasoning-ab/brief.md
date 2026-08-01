# [T-181] 段1 brief — focused review の reasoning `max` 対 `high` 限定 A/B

## scope

phase3 [T-181]: dev-wave の focused review (段6 焦点再レビュー) だけを対象に、
reasoning `max` と `high` を**同一の凍結入力**で比較し、must-fix 再現率・新規 finding・
token / model_calls / wall-clock を機械 receipt 付きで記録する。既定値 (DW-O01 の
`model_reasoning_effort`) は本 wave では変更しない。成果物は「裁定可能な insight」+
再現用の read-only ツール + 回帰テストとする。

## 段1 前提実測 (すべて本 wave で実測済み。模擬なし)

1. T-153(e)/T-154 wave の focus session 2 本の rollout JSONL が現存し、
   **prompt 原文 (2,000 chars) を逐語復元できる** (`019faca2-…` = focus1、`019facbe-…` = focus2)。
2. `turn_context.payload.effort` が **実効 reasoning の receipt** であり、両 focus とも `max`。
   `tools/codex_worker_ledger.py` は既にこの field を `reasoning` として読む。
3. focus1 実測 = model_calls 28 / CLI reported 320,640 tokens / 15:49→16:02。
   focus2 = 71 / 498,984 / 16:19→16:40。focus stage 合計 819,624 は (61)(64) の凍結値と一致。
4. focus1 の入力状態 (fix1 適用後) は再構成可能。fix2 の `apply_patch` 全文が rollout に残り、
   その `+` 側 4 箇所が統合 commit `9b26b3b` に逐語で実在する (grep 1/1/1/1) ため、
   **`9b26b3b` から fix2 を逆適用すれば fix1 状態になる**。
5. `docs/ai-provenance.md` @ `9b26b3b` は **8,832 bytes** で、focus1 逐語の実測値と一致する
   → 当該入力は focus1 と統合 commit の間で drift していない。
6. T-153(e) wave worktree (`.codex/worktrees/dev-wave-t153e-t15423`) は現存するが
   `tools/check_docs.py` +239 行等**後続 main 取り込みで drift 済み**。ゆえに live worktree を
   入力に使ってはならず、凍結 snapshot を作る必要がある。
7. codex CLI 0.146.0 実在、`gpt-5.6-sol` 実績あり。`tools/check_codex_output.py` が採用条件。
8. 既存テストでこの vector (reasoning 別 A/B、effort receipt 検証) を被覆するものは**皆無**
   (`grep -n reasoning tools/ orchestrator/` は ledger の token 集計のみ)。純増する検出力は
   「arm と実効 effort の不一致を fail-closed にする」「部分出力を GO と数えない」の 2 点。

## 不変条件 (破ったら停止)

- 既定 policy (DW-O01 の `max`) を本 wave で変更しない。T-184 が採用段。
- 両 arm は **byte 一致の prompt と byte 一致の入力 snapshot** を見る。片側だけ整形しない。
- 各 run の実効 effort は rollout の `turn_context.effort` で裏取りし、要求値と不一致なら
  その run を fail-closed で捨てる (品質差でなく配線事故だから)。
- 部分出力・`## 総括` 欠落・`check_codex_output.py` rc≠0 は「品質劣化」ではなく
  **無効 run** として別分類する (F43/F45 型と混ぜない)。
- 凍結成果物 (`FROZEN_MANIFEST` 23 件) には触れない。本 wave の insight は新規 path のみ。
- ground truth を後から動かさない。段4 で事前登録した R-1 判定規則を run 後に緩めない (規律2)。

## 実験設計 (P 付きは親の provisional 裁定 = 攻撃対象)

- **(P1) 入力は focus1 (fix1 状態) の 1 点だけとする。** 理由: focus1 だけが既知の real must-fix
  (R-1 = pre-policy でも canonical CAB parser を実行する非遡及違反) を持つ。focus2 入力は
  ground truth が GO / must-fix 0 で再現率が定義できない。
- **(P2) `max` 側も再走する。歴史 focus1.md を max arm の datapoint にしない。** 理由: 歴史 run の
  cwd は drift 済み worktree であり、snapshot と byte 一致しない。混ぜると prompt/入力差と
  reasoning 差が交絡する。focus1.md は ground truth の由来としてだけ使う。
- **(P3) n = 3 / arm (計 6 run)。** 予測費用 ≈ 320k tokens × 6 ≈ 1.9M tokens、
  wall-clock は並列で 20〜30 分。n=3 は差の解像度が粗い — 結論には必ず解像度の限界を書く。
- **(P4) 交絡の明示: focus1 の prompt は R-1 仮説を攻撃候補として名指ししている。** よって
  測るのは「盲目的発見率」ではなく **「名指しされた仮説を real と裏取りし must-fix に昇格させる率」**。
  この射程を insight の見出しに書き、盲目発見率と偽らない。
- **(P5) 採点は二層。** (a) 機械層 = 決定的 extractor で GO/NO-GO・must-fix 件数・
  所見対応表 (closed/partial/regressed)・R-1 marker (`check_cab` / `_has_co_authored_by_policy` /
  `pre-policy` の共起) ・token/model_calls/wall-clock/effort receipt を出す。
  (b) 意味層 = 親が逐語を読み real/refuted を裁定する。LLM judge は導入しない
  (採点器の非決定性を結論に持ち込まないため)。
- **(P6) 生死確認先行 (DW-G01)**: まず `high` 1 本を snapshot に対して走らせ、
  完走・`## 総括` 生成・effort receipt = `high` を確認してから残り 5 本を投入する。
  この 1 本は事前登録済みの replicate #1 として採用する。

## 成果物の形と DW-G05 成果物影響

- `tools/` の read-only CLI 1 本 + `orchestrator/tests/` の fixture 回帰。
  実装しない場合: reasoning routing の採用判断 (T-184) が逐語の目視だけになり、
  effort 配線事故 (要求 `high` / 実効 `max`) を検出できないまま policy 値が確定しうる。
- `output/insights/2026-07-29_t181-reasoning-ab/` に prompt・snapshot 台帳・6 run 逐語・
  受入 receipt を凍結。実装しない場合: 比較の入力同一性を後から監査できず、
  T-184 の stage matrix が再現不能な根拠に立つ。
- worklog エントリ + escalation 条件の**裁定パッケージ** (D は書かない。採用は T-184)。

## 分割方針

- 段2 plan / 段3 敵対相談は**省かない**。理由 (DW-C00): 実験設計の択一が割れ (P1〜P5)、
  結論が T-184 の policy 採用の根拠になるため、設計の妥当性そのものが成果物である。
- 段5 実装子は Codex `role=author` 1 本 (snapshot 再構成 + receipt/採点 CLI + テスト)。
  A/B の実走・変異・受入・記録は親。
- 段6 敵対レビュー 2 本 (レンズ = 実験妥当性 / 実装の fail-open)。
