# 2026-09-19 B-5 生成器対照 (LLM / ランダム変異 / 機械 sweep) の事前登録 v1 を作った記録

- wave: `dev-wave-b5-generator-contrast-prereg` / branch `worktree-dev-wave-b5-generator-contrast-prereg`
- 基点 main: `a99425b66` (21:42 JST)、記録前に `657e1e5a7` を ff-only で取り込み
- ユーザー決定 (2026-09-19): 「既に許可された編集面 (固定 backoff hole) の内で、LLM (K2 loop) / ランダム変異 /
  機械 sweep の 3 生成器を同一予算で比べる事前登録の作成を認可する。本走と D1409 の条件変更は認可しない」
- 成果物: `docs/b5-generator-contrast-preregistration.md` (v1、未発効)、`docs/README.md` の 1 bullet。実装面差分ゼロ
- 専用 handoff: repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/HANDOFF.md`

## 一行で

**固定 backoff hole の受理域は整数 µs 1..1000 の 1000 点で完全列挙可能であり、3 生成器の比較は D1067 の
「条件付き優越」の形でだけ事前登録できる。事前登録 v1 を別 file に置き、既存機構で欠ける部品 (較正動作点の
CLI、session 契約の束縛、B/A 台帳、重複の fresh 評価、exact correctness 経路、random 生成器、sweep の hash 順
B 点、解析 consumer) を「実装が要る」と名指しした。本走は認可されていない。**

## 段 1 実測 (親、実コード)

| 要素 | 実測 |
|---|---|
| hole の受理域 | `backoff_hole_grammar.py` の Tier 1 文法 (`double now_backoff = <literal>;` 1 文) と `validate_backoff_value` (整数 1..1000)、`p3_s4_loop.py` の value == literal の帰属整合 |
| LLM arm (K2 手動 loop) | `p3_s4_loop --run-iteration <proposal.json> --coder-role coder-v4-autonomous-k2 --knowledge-manifest ...`、`tools/pegasus/p3_s4_loop_pegasus.sh` で単回評価 1 job。性能構成は `default_perf()` = 100k records / 4 thread / extime 1 / reps 2 の配線規模に固定 (CLI に上書き口なし)。`drive_iteration` は単一 layout で入口停止、同一 genome は `_resolve_duplicate` で WAL から復元 (T-2746 の fresh layout 運用ではどちらも発火しない) |
| 機械 sweep | `backoff_extended_sweep.py` の `EXTENDED_SWEEP_US` 29 点 (0 を含む)、`MEASUREMENT_SEEDS` 固定順、較正動作点 (`p2_2.py`: 1M / 48 / 3 s / 5 reps)、B 点 mode なし、template 式経路 |
| ランダム変異 | 不在 (2026-08-26 の意味検索の結論を維持。本 wave で全コードの意味検索は再実施していない) |
| bench の session | `pipeline.py` `_run_bench` は `remeasure_until_stable(max_rounds=3)` で品質再測定、`require_all_reps` 等の flag を持つ |

## 段 2〜6 (Codex、全段 `gpt-6-astra` / medium)

| 段 | 子 | 受理 | 要点 |
|---|---|---|---|
| 2 plan | `codex/plan.md` (17 call、19 分) | accepted | 事前登録の全文草案、実行可能性の照合表 (file:line)、既知結果台帳、費用 3330 session、P1〜P9 応答。brief を 3 点訂正 (入口停止・重複復元・支持集合) |
| 3 相談 A (正しさ) | `codex/consult-a.md` (7 call) | accepted | must 3: session 成立条件 (bench の 3 round 再測)、同値 anomaly の波及、brief の停止・支持集合。should 2: scheduler 中断の分類、初回 stock の受渡し |
| 3 相談 B (事前登録・統計) | `codex/consult-b.md` (9 call) | accepted | must 3: 共有 stock と符号反転 exact 検定、不安定性と判定不能の優先順位、brief の訂正。should 4: endpoint CV で等価域が膨らむ、fallback 込み score の意味、台帳と設計選択の対応、Erratum の境界 |
| 4 裁定 (親) | `rulings-stage4.md` | — | brief 訂正 C1〜C5。全所見 real・採用。費用を 3330 → 1773 論理 session へ縮小 (探索 job ごとの stock と endpoint 専用 floor を採らない) |
| 6 独立レビュー | `codex/review.md` (16 call) | accepted | 一次資料との照合 全項一致 (digest・commit・sha・tps・定数・経路・算術)。must 3: exact 検定の前提が不足、副解析の切替規則が未確定、生成不成立が判定順の外。should 2: Tier0 中の時間切れの B 計上、stock CV の集約式 |
| 6 fix (親、docs) | §3.3・§7.2・§7.3・§7.4 を修正 | — | 独立性と符号対称性を登録する仮定として明示、副解析の使用規則を一意化 (fallback 対 ≥ 2 → 副解析で判定、対 < 6 または block < 1 → 対不足で判定不能)、生成不成立を判定順 3 番へ統合、pipeline 投入前後で A/B を分離、CV は 4 値の最大 |
| 6 焦点再レビュー 1 | `codex/focus.md` (5 call) | accepted | closed 3 / partial 2 (exact 検定の前提、副解析の結論の射程)。新規 must 1 (親が足した「6 対では有意になりえない」は Holm の段階閾値と矛盾)、should 1 (段 4 裁定からの変更 3 点を裁定として記録すべき) |
| 6 fix 2 (親、docs) | §7.3・§7.4・§13・§14 | — | Holm の記述を訂正、副解析の結論の射程を明記、(iii) の効能の主張を縮小。段 4 からの変更 3 点を `rulings-stage6.md` に記録 |
| 6 焦点再レビュー 2 | `codex/focus2.md` (受理) | accepted | closed 3 / partial 1 → 新規 must 1 (「(iii) は全 block 共通の単一ショックには効く」も誤り: 全対差が同じ確率変数なら誤判定 1/2)。親が防壁の主張を全て外して閉じた (DW-O16 の 3 巡上限、`rulings-stage6.md`) |

親が段 6 レビューの投入後に §1 へ 1 段落を足した (D1441 で「非列挙」が操作的定義へ改められている事実と、本書がその
判定を行わないこと)。この段落は独立レビューの読んだ版に無い。焦点再レビューの版には含まれる。

## 費用の算術 (事前登録 §11)

1773 論理 session = 探索 1080 + 系列開始 stock 108 + endpoint 再計測 540 + block stock 45。bench 設定時間だけで
約 7.4 時間、旧環境の verifier 所要 (140.66〜433.33 秒 / 件) の外挿で約 69〜213 時間 (推定)。百時間級。

## 検査

- `python3 tools/check_docs.py` — 違反なし (本文修正後に再走)。
- `python3 -m orchestrator.campaign.s8b_holdout_freeze search` — rc 0、holdout 語 (rr80 / rr20) の hit なし。
- `git diff --check` — 空。NFC 検査 — OK。
- 変異 matrix — 実装面差分ゼロで免除 (DW-S04)。受入全走 — 段 7 の後に投入 (結果は worklog fragment)。

## dev-wave 改善候補

- 引数の `2026-08-26_b5-contrast-review-verbatim/` は実在せず、実体は `output/insights/2026-08-26/b5-contrast-review-verbatim/` だった。
  段 1 で path を実測して差し替えた。手順の欠落ではなく引数の写し誤りなので候補にしない。
