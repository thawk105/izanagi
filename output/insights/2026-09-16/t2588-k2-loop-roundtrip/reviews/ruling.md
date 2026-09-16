# 段 4 裁定 — [T-2588]

段 2 plan (rc=0)、段 3 相談 A (sol、rc=0)、相談 B (luna、rc=0) を受けた親の裁定。
**採用した是正はすべて「記録の書き方」と「実行の分岐」であり、新しい機構・gate・検査・台帳は
1 つも足さない** (D2044 項 9 逐語「新しい機構は足さず、既存経路だけで行う」)。

## real — 採用

### R1. critic の診断は次生成の型付き入力へ届かない (A1 / B1 が独立に一致)

現物: `p3_s4_loop.py:1237` の `planner_context_payload` は whiteboard・knowledge_input・任意
policy_hint しか射影しない。`prior_critic_reverse` の機械 consumer は `_fold_critic_reverse`
(`:2213`) と停止判定 (`:2486`) だけで、planner/coder の方向生成器へは渡らない。しかも
proposal-2 は評価しないので、保存した bool は本 wave 内では消費すらされない。

**裁定:** brief の完了条件 (c) を次へ改める。

- 改前: 「その診断と実測を入力にした proposal-2 が保存される」
- 改後: **「本走の実測結果 (`current_perf` / `leading_indicators` / whiteboard) を入力にした
  proposal-2 が保存される」**。critic 出力と親が解釈した `prior_critic_reverse` は
  **保存した**とだけ書き、「診断を次提案の入力にした」とは書かない。

policy_hint 経由で診断を流す案は**採らない**。run-card が固定した入力契約から外れ、
「既存経路だけ」の逐語にも反する。

### R2. 停止時の分岐を明示する (A3)

現物: `p3_s4_loop.py:2532-2533` が評価後の停止理由を返す。`:1270` の時間予算は 1 評価でも成立しうる。

**裁定:** 走行後に `stop_reason` を読み、**`continue` のときだけ** critic と proposal-2 の生成へ進む。
`continue` 以外なら生成せずに終え、「停止条件が成立したので次提案は作らなかった」と記録する。
新しい gate は作らない — 既存の返り値を読むだけである。

### R3. 主張しないことを 6 件足す (B4)

成果物には次の区別を明記する。

1. 往復の成立は、合成による改善や探索の有効性の実証ではない。
2. 新しい数値が出ても、固定 backoff の初期値変更であって新しい CC 構造ではない。
3. proposal-1 の certified は、候補間の certified な選択ではない。proposal-2 は未評価である。
4. `knowledge_use` は自己申告であり、K2 の利用因果を証明しない。
5. critic 診断の「保存」「入力への投入」「改善効果」はそれぞれ別である。
6. 歴史測定と今回 1 走の差は性能優越の根拠にならない。`last_delta_pct=null` を維持する。

### R4. 不在主張を確認範囲へ限定する (B7 / A6)

親は handoff へ「T-2581 の leading indicators は**どこにも残っていない**」と書いた。
両相談が独立に走査しても反証は出なかったが、**不在の証明にはならない**。

**裁定:** 「探した保存先 (T-2581 の job root、repo の insight、両 checkout) では LLC miss / IPC を
発見できなかった」へ限定する。あわせて、歴史測定を使う**直接の根拠は run-card が固定した入力**
であり、不在の証明ではないと明記する。T-2581 の throughput 713068 tps は job.stdout に残っている。

### R5. 代筆禁止に `confidence` を明記 (B nit)

`confidence` は role の自己申告である。欠けていたら親は代筆せず role 本人へ差し戻す
(2026-09-09 に同じ差し戻しをした前例がある)。`knowledge_use` / `classification` /
`data_boundary_report` も同じ。

## refuted — 不採用 (理由つき)

| # | 疑い | 反証 |
|---|---|---|
| 1 | 本 plan が正しさの受理集合を広げる | 自己申告を保持したまま K2 loader を通し、指示検出・完全文法・literal/value 一致・source index を検査する経路しかない。verifier 不通過は reject のまま (B2) |
| 2 | 指定 WAL が前回と同じ指示検出を起こす | 相談 B が 15 行の本文を実際に読み sha256 も照合。値 40/30/40 の build・verify・bench・commit 記録だけで、役割に実行・検証省略・参照制限を求める文字列は無い (B3) |
| 3 | repo 内の新規実装 file が必須 | 射影・検査・投入・digest 読出しはすべて既存関数と既存 CLI で足りる (B5)。実装面の差分はゼロのまま |
| 4 | T-304 の所有侵犯・改名後 schema への依存 | 2 file は参照先であって編集手順が無い。WAL の `throughput_tps` を role の `throughput_ops_sec` へ写す向きで、改名完了を前提にしていない (B6) |
| 5 | 実測が型付き入力へ届かない / 率の単位が違う | 写像は現物と一致。`abort_rate` と `llc_miss_rate` は 0..1 なので ×100、`ipc` はそのまま (A2、D118) |
| 6 | 同一 campaign ID なので過去 terminal に skip される | 今回の ID は T-2581 と**同一の `p3-s4-loop-s4-autonomous-409e13f8` になる** (A4 が再導出)。しかし `loop.py:579` の replay は渡された layout の WAL だけを見るので、新規 submit-tree では skip は起きない。ID を変えるための設定変更は不要 |
| 7 | pin / verifier の修正が今回も必要 | PIN も gitlink も `511c9538…` で一致。`verifier/parse.py:323-330` は v1 拒否・v2 要求のまま。`55d0f2399` から現 HEAD まで `orchestrator/verifier` に差分なし (A5) |

## nit — 記録時に反映するだけ

- plan の参照行が 12 箇所ずれている (A7)。成果物の値も受理集合も変えないので plan は差し戻さない。
  記録では相談 A が照合した正しい行を使う。
- `load_proposal_file` の `coder_role` 既定値は `None`。plan:37 は署名ではなく今回の呼出し形である。
- 拒否は `RolePolicyError` より先に `EventValidationError` が出うる (`p3_s4_loop.py:2236`、
  `codex_roles/events.py:178-186`)。拒否種別を想定外エラーと誤分類しない。
- **`src/coder-leakproof-context.md` の "Measurement Setup" 節は実配線規模と食い違う**
  (file は 1M records / 48 threads / 3 runs、現物 `default_perf()` は 100000 / 4 / reps=2)。
  K2 射影では現物へ訂正した。これは親が段 1 で見つけた独立の所見である。

## 変異事前登録

**実装面の差分がゼロなので `DW-S04` により変異 matrix を免除する。**
受入全走は免除しない。実 repo を読むテストは段 7 の記録前に実走し、結果を worklog へ書く。

## plan v2 (確定した実行順)

1. planner-v4 を 1 回 spawn (`materials/planner-input-1.json`)。
2. coder-v4-autonomous-k2 を 1 回 spawn (leakproof_context = `materials/leakproof-context-k2.md`、
   knowledge_input、baseline、planner_direction、whiteboard=[])。
3. `materials/proposal-1.json` を保存 (planner の内側 proposal + coder の K2 envelope 全体 +
   `prior_critic_reverse: null`)。**自己申告 field を代筆しない。**
4. login で既存検査 3 本: `assert_closed_proposal_schema` → `validate_backoff_preflight` →
   `load_proposal_file`。
5. 専用 submit-tree から README §7 の 9 変数で qsub 1 本。
6. 完了後、`compute-result.json` と WAL を読む。**verdict と `stop_reason` を確認。**
7. `stop_reason == "continue"` かつ緑のときだけ: critic 1 回 → planner-2 → coder-2 →
   `materials/proposal-2.json` を保存 (評価しない)。
8. 記録 (insight + spool fragment) → 受入全走 → land。
