単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 4 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 親 brief (段 1。**これ自体も攻撃対象**):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`
- 段 2 プラン (攻撃対象):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s2-plan.md`
- 先行決定 D1768 の逐語 (producer が従う規則の出所):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-d1768.md`
- 設計正本 §3 の逐語 (§3.4 outcome 対応表が producer の規則):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-design-s3.md`

# 段 3 — 敵対相談 レンズ A (正しさ境界: 規律 2 と受理集合)

あなたは izanagi の dev-wave 段 3 の敵対検証子である。プランを守るな、検査せよ。親 brief 自身も検査対象である。
**実装はするな。ファイルを 1 byte も編集するな。commit するな。**

## repo

cwd は worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer` (local main 34af5a571 と同一)。
プランが引く file:line は必ず現物で確かめよ。巨大ファイルは `grep -n` で位置を出してから `sed -n 'A,Bp'` で読め。
書込可能な tmp が無いので pytest の緑を要求しない。静的検査でよい。走らせていないものを緑と書くな。
予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。無出力が最悪である。

## このレンズの攻撃面

1. **producer が consumer より緩い形を発行しうる隙間。** プランの S1 の 3 方向分岐を `reflux_formal_consumer.py` の `_validate_wal_outcomes` (1264-1396) と `_valid_witness_anomaly` (1155-1235) の要求と 1 対 1 に突き合わせ、producer が `outcome=rejected` + class を出すのに consumer が FC07 で落とす入力、または逆に producer が発行拒否すべきなのに record を出す入力を**具体的な VerifyResult の値**で示せ。特に: dirty integrity、`indeterminate`、`total_cycles > anomaly_count` (切詰め)、`anomaly_count > 1`、`certified=True` かつ `serializable=False` の矛盾、`anomalies` が空で verdict が non-serializable。
2. **恒真条件。** producer の各条件が、入力の候補集合に含意されて恒真になっていないか (例: `VerifyResult` の型が既にそれを保証する) を検査せよ。恒真な条件は保護と数えない。変異で暴ける形か。
3. **class の式の同一性。** (P1) の 2 案 (式を 1 箇所へ寄せる / 複製して pin) それぞれで、producer と consumer の digest が乖離しうる経路 (canonical JSON の float 許容、bool、順序、`trace_dir` の残留、WAL 往復による型変化) を挙げよ。WAL に書かれた `verify.anomalies[0]` と in-memory の `result_to_dict(vr)["anomalies"][0]` の canonical bytes が一致することは自明か。反例があれば示せ。
4. **複数 class から 1 件を選ぶ経路。** 設計 §3.4 は「都合のよい 1 件を選ばない」を定める。プランの発行拒否がこれを守るか、`anomalies[0]` を取る実装が `max_report` の切詰めと組み合わさって「実は複数あるのに 1 件に見える」入力を通さないか検査せよ。
5. **親 brief の provisional 裁定 (P1)〜(P4) を独立に攻撃せよ。** 親の推奨を採用する前提で読むな。
6. **親の実測値の一般化。** brief §1 の fixture 実測 (8 件) を根拠に「複数 class の実 fixture は無い」と一般化している。一般化の穴を指摘せよ。

## 出力形式

所見ごとに H2 見出し `## A-<n>: <一言>` を置き、各所見に次を必ず書け:
- **主張** (1〜2 文)、**根拠** (file:line と具体的な入力値)、**帰結** (放置時に成果物・受理集合・参照がどう変わるか 1 行、DW-G05)、**推奨** (採用 / 修正案 / scope 外へ送る)、**確度** (real 確定 / 要実測 / 推測)。
最後に `## 総括` (5 行以内: real 確定の件数、最も重い所見、プランを支持するか) を必ず置け。
出力へ結合文字 U+0300〜U+036F を使うな。
