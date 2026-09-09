---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2265-cohort2-cert
seq: 1
---

## {{D:cert-seed-thread-axes-cost-only-supersede}}. 認証 mode へ seed と thread 軸を通す — D1852 の費用判断だけを上書きする

**決定:** `--mode certify` の受理形へ、cell 別の thread 閉表と policy 2 の compile seed 閉表を足す。
これは D1852 の却下欄「認証 mode へ seed を通す」を**費用の面だけ**上書きする部分 supersede であり、
D1852 の他の理由は引き続き有効とする。

- 上書きするのは「12 seed すべてを exact に認証すると 312 job になり、現実的でない」という費用判断だけ。
  ユーザーがその費用を承知のうえで直接指示した。
- **残す:** 認証の射程を広く書かない。新軸は exact 閉表にする。依頼が要らない cell へ広げない
  (`tuned` と `cw-as-dyn` は 48 threads のまま)。成果物は層別 coverage で書く。
- 受理形の拡張は cell 別に閉じる。seed 軸は policy 2 だけに開き、seed を使わない腕には開かない。
- claim は検証済みの軸からの exact な閉写像とし、既に発行済みの 4 軸は現行 literal を 1 文字も変えない。

**理由:**
- D1852 の却下理由のうち非費用のもの (「認証は正しさの主張なので、射程を広く書くことは
  絶対規律 2 に対する直接の緩みになる」) は、費用の裁定が覆っても効き続ける。
  全面撤回すると、台帳上は受理形の拡張抑止が費用問題だけだったことになる。
- 受理形を広げる変更は正しさゲートへの直接の攻撃面である。閉表を cell 別に閉じ、
  既存の拒否を 1 つも消さないことで、広がる先を依頼が要求する範囲に限れる。

**却下した選択肢:**
- D1852 の全面撤回 — 非費用の理由まで消える。
- thread 閉表を全 cell 共通にする — 定数を 1 本にする実装都合のために、依頼が要らない
  `tuned@24` と `cw-as-dyn@24` まで認証の受理集合へ入る。
- 値の形で「既発行 receipt 用の旧 claim」を判定する分岐を置く — 後から作った同形の receipt も
  再受理でき、台帳の既発行 receipt 参照を置換できてしまう。

## {{D:certified-build-is-not-the-trial-build}}. 認証した実行体が試験の実行体と違うときは、その差を claim 本文へ書く

**決定:** 直列性認証の claim には、認証対象を特定する軸として **build 条件**も書く。
現行の認証経路は `BACKOFF_TRACE=0` かつ terminal define なしの実行体を build するので、
新規に生成する claim にはそれを明記する。**backoff 診断計装を入れた実行体で取った試験について
「その実行体を認証した」と書いてはならない。**

**理由:**
- 認証経路は `genome_for(cell)` を既定引数で呼ぶため計装なしの実行体を build する。
  一方 cohort 2 の反実仮想試験は、割当列と terminal event を記録するために計装ありの実行体で走る。
  cell 設定と compile seed が同じでも、build される実行体は別である。
- terminal event は記録だけでなく制御器・LCG・割当の更新も止めるので、無害な表示差ではない。
- 射程を広く書くことは絶対規律 2 に対する直接の緩みである (D1852)。

**却下した選択肢:**
- 計装入り genome を認証対象にする — 受理形・claim・絶対規律 1 の解釈すべてに関わる。
  必要な改修だが、本決定とは別に諮る。
- build 条件を書かずに「同じ cell を認証した」と書く — 読み手が試験の実行体の認証だと読める。

## {{D:no-unmeasured-predicate-on-build-identity}}. build 同一性の述語は、値域を実測してから採用する

**決定:** 認証 group の 24 request に対して `binary_sha256` や `build_cache_key` の singleton を
要求する述語を**置かない**。実行体が同一であることの確認は `genome` と source identity で行い、
group 間の実行体相異も `genome` で判定する。

**理由:**
- `build_cache_key` は job ごとの build context / admission identity から算出されるので、
  24 job では必ず異なる。要求する値が到達不能である。
- `binary_sha256` の job 跨ぎ決定性は未実測だった。**実測すると 1 group 24 row すべてが異なる。**
  CCBench の build は job を跨いで byte 再現しない。この述語を置いていれば、
  すべての group が受領証を発行できなかった。
- `DW-O13` は「field の実在では足りない。その field が実環境で取りうる値を実測し、
  要求する値が到達可能か確かめてから述語を採用する。到達不能なら採用せず、測った値域を裁定へ書く」
  と定めている。

**却下した選択肢:**
- `binary_sha256` だけ singleton を要求する — 決定性が未実測のまま gate にすることになり、
  既に通っていた経路まで塞ぎうる。
- 述語を置かず確認もしない — group 間の実行体相異が主張できなくなる。`genome` で確認する。
