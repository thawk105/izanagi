# 段 1 brief — [T-2005] B-4 projection closure hash の事前登録

base main `d03855e92` / branch `worktree-dev-wave-t2005-b4-projection-registration`。

## scope

B-4 正式実走の blocker である「3 driver の projection closure hash が事前登録と admission
record のどちらにも登録されていない」状態を解消する。対象は base / sort / trigger の 3 driver
に限る。hash の汎用基盤・新しい台帳・新しい権限主体は作らない。

## 確定済みユーザー裁定 (引数より)

- 旧 hash を受理する緩和を作らない。
- 対象は 3 driver に限定し、既存の `projection_sha256(driver_kind)` をそのまま再利用する。
- 凍結物の再発行が要るなら、その手順と権限が既存の事前登録・批准の枠内で閉じるかを先に実測し、
  閉じないなら不足を記録して停止する。
- 見送り対象ではない (worklog 1083 が正式実走 blocker として再確認)。

## 起動時に実測した事実 (推測でなく実行結果)

1. main `d03855e92` の実測値 — base `72220e00…41d665` / sort `117fd6c9…c91047` /
   trigger `a32b9749…c773f2`。
2. `docs/phase3-b4-reflux-ablation-preregistration.md` §5 の
   「model snapshot / prompt hash / projection hash」欄は `未記入`。main に登録済み hash は
   1 件も無い (git grep)。admission record の artifact も repo 内に 1 件も無い。
3. **凍結物の再発行は要らない。** (a) 同文書は §0 が「発効前 draft」と宣言し、`check_docs.py`
   も living 扱いにしている。(b) `p3_b4_analysis_prereg_consumer.py` が exact pin する
   §5.1.1 の raw sha256 は、§5 の表だけを書き換えても不変であることを実測した
   (`0ceab4cd…91df30` が編集前後で一致)。(c) bytes を pin する commit 済み record は存在しない。
   よってユーザーが指示した停止条件は発火しない。
4. `_EXPECTATION_ROW_RE` は (model, prompt, projection) の 3 つ組を**ちょうど 1 組**しか
   受け付けない。driver ごとに 3 つ並べる形は現状 reject される (実測)。
5. この欄だけを埋めても §5 全体の関門は依然 reject する (実測)。他 9 欄の `未記入` が残るため。
   つまり本 wave は実走関門を開けない。開けないことが正しい。
6. `expected_effective_critic_prompt_sha256` は repo bytes だけから事前導出できる
   (`.claude/agents/critic.md` + `MEDIATED_CRITIC_CONTRACT` の純関数)。実測値
   `1b5006f6…35f0cf`。
7. `expected_claude_model_snapshot` は repo bytes から導出できない。D998 が「事前宣言 + 実行時
   照合」と定めた欄である。role frontmatter は `opus` であって snapshot slug ではない。
8. `projection_closure_manifest()` の閉包は `p3_b4_admission_record.py` と
   `p3_b4_closed_critic.py` 自身の bytes を含む。**この 2 file を編集すると 3 driver の hash が
   全部変わる。** 登録値は最終 tree で再計算した値でなければならない。
9. T-2049 の branch は main と差分ゼロ・未 commit 変更なし。現時点で編集面の衝突は無い。
   同 wave は §5 の「primary outcome」欄側、本 wave は projection 欄側。

## 不変条件 (緩めない)

- 旧 hash・stale hash を受理する経路、環境変数・CLI flag の逃がし道を作らない。
- §5 の他 9 欄を埋めない。関門を緑に見せない (D1060、D1000、絶対規律 2)。
- §5.1.1 の pin と `.claude/agents/critic.md` の bytes を触らない。
- 検査の名前・例外文言が証明範囲を越えない (D1000)。
- 新しい権限主体・汎用 hash 台帳を作らない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 欄は全部埋めるか placeholder のみ。** §0 は部分記入の例外を「実行責任者・開始時刻」
  1 行に限り、他 9 欄へ広げることを禁じる。したがって projection だけを書くことはできず、
  同じセルの model snapshot と prompt hash も同時に確定させる必要がある。
  provisional: この読みを採る。
- **(P2) model snapshot の値を本 wave で宣言してよいか。** repo bytes から導出できず、
  誤宣言は実行時に fail-closed で停止するだけ (安全側)。文書は発効前なので修正は自由。
  provisional: 宣言してよい。ただし宣言値の出所を実測で決められないなら (P4) へ倒す。
- **(P3) 3 driver をどう表すか。** provisional: 行 grammar を driver tag 付き 3 値へ広げ、
  record 側は `p3-b4-prerun-admission/v1` のまま、宣言 projection が文書の 3 値のうち
  当該 driver のものと一致することを照合する。schema 昇格は採らない。
- **(P4) 登録値は closure 変更のたびに陳腐化する。** T-2005 が発生した原因そのものである。
  「今登録する」のか「実走直前に 1 手で登録する道具と、陳腐化を赤にする検査を置く」のかは
  設計択一。provisional: 前者を本体とし、陳腐化検査を同じ変更単位に入れる。

## 成果物の形

- `docs/phase3-b4-reflux-ablation-preregistration.md` §5 の当該 1 セルの記入 (docs)。
- `orchestrator/campaign/p3_b4_admission_record.py` の行 grammar と照合の拡張 (実装面)。
- 負例を含む test (旧 hash 拒否、driver 取り違え拒否、部分記入拒否、陳腐化拒否)。
- worklog / decisions の spool fragment、insights 一式。

## 並列分割

段 2 は plan 1 本。段 3 は 2 レンズ (正しさ関門の緩み / 事前登録の空洞化と権限)。
段 5 は実装子 1 本 (編集面が 1 module + 1 doc + 1 test file に閉じるため分割しない)。
段 6 は敵対 review 2 本 + fix + 変異 matrix + 受入全走。
