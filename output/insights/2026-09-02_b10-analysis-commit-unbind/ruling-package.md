# 裁定パッケージ — B-10 analysis_commit 束縛の除去で残った 2 件

本 wave (B-10 事前登録束縛から `analysis_commit` による再開拒否を外す) の段 3 独立検査で出た
real 所見のうち、依頼の scope 外として実装しなかったものを 2 件返す。いずれも急ぎではない。

---

## 1. 計測値の読み取りコード 2 file を、内容束縛の閉包に入れるか

### 何が起きているか

B-10 の分割走 (相 / workload ごとに job を分ける) では、途中で切れた campaign を再開する。
再開時に「前と同じコードで測っているか」を確かめる仕組みは 2 つある。

- **contract-loader 束縛** — `ident.verify_against_lock` (`orchestrator/campaign/ident.py:385-396`)
  が、campaign.lock に記録した 24 file の内容ハッシュを現物と突き合わせる。
  閉包 `CONTRACT_LOADER_RELATIVE_PATHS` (`orchestrator/campaign/campaign_lock.py:49-74`) には
  `pipeline.py`・`loop.py`・`wal.py`・`ident.py`・`artifact_admission.py` と
  検証器一式 (`orchestrator/verifier/*`) が入っている。
- **解析コード束縛** — B-10 固有で、driver 自身 1 file の内容ハッシュ
  (`analysis_code_sha256`) を束縛する。

**この 2 つの外に残るのが `orchestrator/calibrator/benchparse.py` と
`orchestrator/calibrator/analyze.py` である。** 前者は計測出力から throughput を読み取り、
後者は安定性 (unstable 判定) を出す。どちらも correctness certification には関わらないが、
レポートに載る `median_tps` と `unstable` の値を決める。

これまでは `analysis_commit` (投入ツリーの HEAD) が束縛に入っていたため、この 2 file を
変更した commit があると再開が拒否されていた。ただしそれは**副作用**で、
無関係な commit 1 つでも同じように拒否していた。本 wave はその commit 同一性による拒否を外した。

### 選択肢

- **(A) 何もしない (現状維持)。** 分割走の途中でこの 2 file を書き換えれば、
  前半と後半で読み取り規則が違う値が同じレポートに載りうる。
  実際に起きるには「分割走の最中に calibrator を書き換えて再開する」という運用が要る。
- **(B) 2 file を contract-loader 閉包へ足す。** 内容ハッシュで束縛されるので、
  変更したら再開が拒否される。挙動で守る形なので絶対規律 7 と向きが合う。
  ただし閉包は B-10 専用ではないので、**全 campaign の再開条件が厳しくなる**。
  calibrator を触る開発中に、無関係な campaign の再開まで止まる。
- **(C) B-10 の束縛にだけ 2 file の内容ハッシュを足す。** 射程は B-10 に閉じる。
  ただし B-10 固有の束縛 field が増え、事前登録文書 §1 の列挙と実装がずれる
  (文書は「解析コード SHA」1 つとしか書いていない)。文書の改訂が要るかは別途判断が要る。

### 親の推奨

**(A) 現状維持を推奨する。** 理由は 3 つ。

1. 発火条件が実運用に無い。B-10 の分割走は同じ checkout から連続で投入する運用で、
   途中で calibrator を書き換える手順が存在しない。`DW-G04` の「発火条件を満たす既存 artifact path
   か計測 ID を brief に書けること」を満たせない。
2. (B) は射程が広すぎる。守りたいのは B-10 の 1 campaign の分割走であって、全 campaign ではない。
3. (C) は凍結文書との整合を先に決める必要があり、この wave の外の判断になる。

発火する運用が実際に必要になった時点で (C) を再検討するのがよい。

---

## 2. 過去のブロック記録に書かれた commit 名を、どこまで信用するか

### 何が起きているか

B-10 は 1 セルごとにブロック記録 (JSON) を書き、その中に `source_commit` (投入時の HEAD) と
`analysis_commit` (解析コードを読んだ HEAD) を残す。本 wave の前は、再開時にこの 2 つを
**現在の HEAD と一致するか**で検査していた。無関係な commit で拒否される原因の 2 つがこれだった。

本 wave はこの 2 比較を外した。結果、validator はこの 2 値を照合しなくなり、
レポートには記録されたまま載る。

**ただし外す前も真正性は担保していなかった。** 現在の HEAD と比べていただけで、
その row が本当にその commit で作られたかは確かめていない。
receipt の bytes ハッシュ照合 (`orchestrator/campaign/b10_backoff_shape_sweep.py:2414-2425`) は
そのまま残っている。

### 選択肢

- **(A) 現状のまま (本 wave が採用した形)。** 2 値は非認証の provenance 情報として記録する。
  レポートの `records` に載る commit 名は「記録された値」であって「検証された値」ではない。
- **(B) 記録された commit 値を、保存済み receipt や当該 commit の解析 blob ハッシュへ束縛する。**
  provenance の受理集合を狭められる。新しい検査とテストが要る。

### 親の推奨

**(A) を推奨する。** 本 wave の裁定でも (A) を採った。理由は、(B) が守るのは「レポートに載る
commit 名の正しさ」であって、測定値そのものや correctness の主張ではないためである。
論文の主張に必要なのは粗い provenance までで、bytes 級・commit 級の認証は要求されていない。
必要になるとすれば、外部からブロック記録を受け取る運用を始めるときである。現在その経路は無い。

---

## 出所

- 段 3 独立検査 (レンズ A = 正しさ境界、レンズ B = 整合と実効性) の成果物は
  `output/insights/2026-09-02_b10-analysis-commit-unbind/verbatim/` 配下。
- 親の裁定は同 `verbatim/s4-adjudication.md`。
