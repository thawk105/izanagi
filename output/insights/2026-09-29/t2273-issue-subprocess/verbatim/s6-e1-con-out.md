## 論拠

(1) には反対する。事前登録の E1 は、追加 node 以外の **全共通 node の shard 割付一致**を有効対の条件にした。今回の構成では shard-0 の共通 node は一致する一方、shard-1 と shard-2 の間で共通 node が移動している。shard-0 だけを一致条件にするのは、系列開始後に有効性の基準を緩める変更である。W の値をまだ見ていなくても、対 1 が E1 で停止したという情報を得た後の変更であり、当初登録した検証として扱えない。前 wave で E1 が成立したことも、今回の例外を事前に許していた根拠にはならない。[今回の事前登録](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md)、[前 wave の事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/output/insights/2026-09-27/t2273-shard0-precopy-impl/verbatim/s4-ruling.md)

E1 が防いでいたのは、A/B の W_0 差を実装効果と読んだとき、系列全体の割付変更に伴う資源競合や実行順序の差まで混ぜてしまう誤りである。集計器は `e1_pair_check` で全 shard の共通 node を照合し、不成立なら `pair_metrics` の対差を land 判定へ採用しない。この条件は単なる報告上の注意ではなく、判定の入口である。[集計器](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/probe/t2273is_ab_analyze.py:225)

## W_0 が shard-1/2 の差から影響を受けうる経路

- 3 shard は別 job でも、**同じ計算ノードに配置されれば** CPU・メモリ・I/O を競合しうる。集計器は各 shard の dispatch receipt から hostname を記録するが、別ノード配置や競合の不存在を E1 の代わりに保証しない。[集計器](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/probe/t2273is_ab_analyze.py:194)
- 別計算ノードでも共有 FS は共通である。移動した test 群の読書き、共有 base の builder やその発行 child、早期 memo、各 shard の controller と collection の負荷・時点が変われば、shard-0 の worker が同じ node を処理しても待ち時間やキャッシュ状態は変わりうる。builder は shard ごとの xdist session 内で作られるため、同一 builder が shard 間で直接共有されるという主張ではない。[事実と選択肢](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s6-e1-consult-common.md)、[前 wave insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md)
- 受入の外側 dispatch と同時実行条件も影響経路になる。門番は他 session の leader 数と load1 に上限を置くが、同じ資源状態を固定しない。前 wave も、外側 dispatch と shard-1/2 を再現しない replica から実受入を推定できないと記録している。[前 wave insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md)

集計器の W_0 は shard-0 の JUnit suite time であり、`pre` は別量である。したがって他 shard の collection 時間を W_0 に直接足す話ではない。負荷や開始時点を通じた間接効果が問題になる。また、5 分判定の W_max は 3 shard の最大なので、shard-1/2 の構成差が判定量そのものに及ぶ。[集計器](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/probe/t2273is_ab_analyze.py:186)

## 代案

**(2) を採る。** 現系列は E1 不成立として `undetermined` と記録する。land 判定が必要なら、新設 node を所要時間台帳へ登録するなどして B の分割を調整し、投入前の login collection で「差は追加 node だけ」「全共通 node の shard 割付が一致」を確認する。登録だけで一致すると推定せず、実際の割付を照合する。B の実装 commit を固定し直し、温めと A,B / B,A / A,B の系列を初めから実施する。追加費用は提示資料の見積りで系列だけでも約 **1.5 node 時間以上**、準備と検証が別途必要となる。[事実と選択肢](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s6-e1-consult-common.md)

費用を掛けない (3) なら、現系列を構成差のある**探索的な観察**として保存し、W_0・W_1/2・W_max・pre/post と配置情報を併記する。その場合に言えるのは「その実際の A/B 構成で観測された差」までであり、事前登録の land 判定は出さない。

## (1) を採るなら最低限の条件

元の E1 不成立と基準変更の時点を明記し、旧基準による結論を `undetermined` のまま残す。shard-0 の選択 node と skip の一致、各条件内での割付安定、dispatch の配置と重なり、W_1/2・W_max・pre/post の変化を確認して公開する。これらは影響経路の調査であって、影響が無いことの証明ではない。緩めた E1 で**確証的な land 判定**を行うなら、その基準を固定してから独立した新系列で検証する必要がある。

## 総括

shard-0 の node 一致だけでは、W_0 の実行環境まで一致したとは言えない。
系列開始後の E1 緩和を、事前登録どおりの有効対として扱うべきではない。
land 判定には分割を揃えた新系列を使い、現系列は探索的記録に留める。