---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2169-measurement-surface-closure
seq: 1
title: [T-2169] 正しさ検証を経ない測定面の閉包を測った — 測定面に verifier が無いのは規律 1 の要求で、争点は値の届き先だった (docs + insight、branch worktree-dev-wave-t2169-measurement-surface-closure、実装面 0・変異 matrix 免除)
---

## 本文

起票元 (entry 1170) の 3 主張はすべて構造的事実として再現した。しかし**どれも欠陥ではなかった。**
性能計測を trace-disabled build の別 run で行うのは絶対規律 1 の要求であり、測定面に verifier が
無いのは正常な状態である。争点は層 B、その値が certified 成果物へ届くかに移る。

- **pipeline の COMMIT 経路は閉じている。** verifier 発行 capability、commit receipt、
  WAL の live 再検証、persisted consumer の再検証の**合成**が担う。単一の関数ではない。
- **repo 全体は閉じていない。** ただし**未検証値を certified 成果物へ実際に運んでいる既存経路は
  無かった。** 実装差分 0 で返す。
- **親の provisional 裁定 5 件のうち 2 件が覆り、1 件は結論だけ残って理由が覆った。**
  (P5) 「D1360 / D58 / certified writer admission の 3 層で全経路が塞がる」は棄却。
  `require_certified_writer_authorization` の production caller は 5 site だけで、
  calibrator・T-810・standalone profile・submodule shell・S8c はこの層を通らない。
  (P1) 閉包の定義は入口集合が狭すぎた。(P4) floor は「記述的な calibration だから安全」ではない
  — screening の棄却閾値になり受理集合を変える。安全性は consumer の admission から立証する。
- **起票元の「official commit writer は certified 判定後に閉じている」は、
  `require_certified_writer_authorization` を指すなら誤りである。** 同関数は実行環境の
  authorization であって、correctness・verifier verdict・genome・source・binary・throughput・
  WAL を一切検査しない。pipeline では build より前に呼ばれる。
- **D1360 は方針の裁定であって共通の code gate ではない。** 実行コード上の参照は
  `genome.py:208` のコメントだけである。「D1360 で塞がる」を実装根拠に使えない。
- **起票元が問うた「D1360 をどの admission で強制するか」には答えが出た。**
  段 8c 正式系列の受理 consumer `s8c_result_judge` の観測受理面である。正しさ判定は caller 供給の
  boolean、attestation は caller が同じ値から計算できる SHA-256 と任意の非空 issuer 名だけで、
  そこから `official_conclusion`・`official_status`・`selection_evaluation` と順位が出る。
  **production caller は無く、module docstring 自身が「外部 producer / issuer が trust root で
  この wave の外」と明記する未接続 interface である。** 束縛の実装は新しい防壁の新設に当たるため、
  依頼の scope に従い実装せず裁定パッケージとして返す。
- **書かれるが読まれない不適格 marker を 4 件見つけた。** `ELIGIBLE_FOR_COMPARE`・
  `paper_gain_eligible`・`headline_eligible`・`fitness_eligible`。marker を反転しても certified 値は
  変わらないので marker 自体は nit だが、**これを barrier に数えると恒真な保証になる。**
  例えば scoping 出力を止めているのは flag ではなく出力先の repo 外強制と filename 不一致である。
- **層 A の全経路件数は主張しない。** 2 レンズが独立に「N はまだ言えない」と結論した。
  語による走査が submodule shell (116 本中、検索語をどれも持たない producer が実在) で閉じず、
  `output/` の再実行入口 4 件、`os.exec*`、callable default edge、class method が残余である。
  成果物は分類済みの一覧であって全数の主張ではない。
- **親の実測 2 件が子に訂正された。** `measure_point` caller 一覧に
  `s8b_floor_attempt_launcher.py:435` を含めたが、これは `capture_measure_point` である
  (正しくは直接 11 site + capture 1 site)。`trace=False` 18 hit は
  「`orchestrator/tests/**` 除外」の条件付きで再現した。
- 子は 3 体、全て `gpt-5.6-sol` / `xhigh` / 受理 (plan 1・consult 2)。工数は受領証が正本。
- **本 wave は測定を 1 件も行っていない。** build・benchmark・dispatch なし。read-only の静的調査。
- 実施記録と逐語 4 本は `output/insights/2026-09-02_t2169-measurement-surface-closure/`。

## 次の一手差分

### 完了

- [T-2169] 正しさ検証を経ない測定面の閉包を層 A / 層 B に分けて一覧化した。実在する欠陥は無く
  実装差分 0。残る 4 件は scope 外の裁定パッケージとして insight に記録した。
  remaining: none
  base: ea318ea7b9e20640bb1d794b88df1075c24d794c6cc144b3a87aa74ba5bf52f9

### 新規

- {{T:s8c-observation-authority-binding}} **P2・新規・ユーザー裁定待ち**: 段 8c の受理 consumer
  `s8c_result_judge` の観測受理面で、正しさ判定と attestation を権威へ束縛するかを決める。
  現状は caller の自己申告で `official_conclusion` と順位まで到達できる。production caller は
  無く未接続 interface だが、tictoc / cicada を接続する時点で D1360 を強制すべき場所はここである。
  実装は新しい防壁の新設に当たるため T-2169 では行わなかった。
- {{T:d58-screening-scope-enforcement}} **P3・新規**: D58 が定める screening の適用範囲
  (事前登録外の偵察 sweep と 8b opt-in) がコードで閉じていない。
  `prepare_screening_campaign()` は任意の `base_cfg` に screening を追加でき、
  preimage 一致しか要求されない。範囲限定を機械化するかを決める。
- {{T:ineligibility-markers-have-no-reader}} **P3・新規**: 書かれるが production の拒否判断に
  使われない不適格 marker 4 件 (`ELIGIBLE_FOR_COMPARE`・`paper_gain_eligible`・
  `headline_eligible`・`fitness_eligible`) を、読み手を付けるか marker を消すかで整理する。
  現状は恒真な保証に見える表示である。
- {{T:spawn-site-inventory-generic-helper}} **P3・新規**: spawn-site inventory が
  `silo_ladder_rung1._run` を非 CCBench と分類しているが、同 driver は CCBench binary を実行して
  throughput を parse する。inventory の単位が「subprocess を含む関数」であるため汎用 helper を
  caller で区別できない構造的限界である。単位を argv dataflow へ変えるかを決める。
