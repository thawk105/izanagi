---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-known-violation-review-20260823
seq: 3
---

## 再発

### F144

- **再発: 2026-08-24** — known-violation 台帳の見直し wave で、親が自作した実測 script 4 本の
  欠陥に気づかないまま結論をユーザーへ 3 度報告した。敵対 2 レンズが実データで否定した。
  欠陥は 4 種類ある。(1) `_commit_paths()` は変更 path を全部返し、
  `validate_implementation_author()` が `_is_implementation_path()` で絞った集合だけを
  finding 対象にするが、script はこの前段 filter を再現せず**gate と違う母集合を測っていた**。
  (2) `git merge-file` という blob 単位の低水準 3-way merge の結果を「実際の merge で競合し
  人が手解決した」と一般化して報告した。rename 検出・`.gitattributes` の custom merge driver・
  当時の strategy を再現しないため、示せるのは「素の 3-way merge では競合した」までである。
  (3) `bytes.splitlines()` を使って末尾 LF の差を潰し、出現回数の条件も実装しないまま
  「plan の述語を満たす 4 件」と称した。(4) 生成器分類が canonical trailer を検査せず
  `'AI-Agent:' in body` だけを見たため、trailer block の配置誤り 1 件 (`3f2c43d758`) を
  「manager が実装面を直接 commit」へ誤分類した。
  再測定では (1)(2) の値は偶然変わらなかった (12 件、増加 20 回・減少 2 回) が、
  land 根拠としては成立していなかった。F144 本体の「計測器そのものに正しさの検査を置かなかった」と
  同じ根本原因で、今回は**権威実装が既に repo に在るのに、その判定順序を写さず別実装で測った**点が
  新しい。
- 追加の恒久対応: memory `parent-measurement-must-mirror-authoritative-filter` —
  権威ある checker / gate が既に repo にあるとき、親の使い捨て実測 script は
  その**判定順序と前段 filter を関数ごと再利用する** (import して呼ぶ)。再実装しない。
  再利用できない場合は、母集合の差を出力へ 1 行で明記してから報告する。
  低水準 command による再計算 (`git merge-file` 等) は、権威実装が使っていない限り
  「代理であり本体ではない」と明記する。
