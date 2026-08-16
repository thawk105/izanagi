---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1175-cell-admission-report
seq: 2
---

## {{D:cell-admission-failure-report}}. build cell admission の契約上の失敗を診断可能な partial report へ変換し、免除の根拠を verifier の独立再導出に置く

**決定:**

1. `p3_autonomous_workload_trial._finalize_cell_admission` は
   `_finalize_build_cell_admission` 由来の **`AutonomousTrialError` だけ**を捕捉し、
   exact な failure decision へ変換して `partial` report を publish する。
   `KeyError` 等の予期しない例外は従来どおり伝播させ、report を残さない。
   これは D217 の「例外境界: admission finalizer の失敗は回復させず伝播させ report を
   publish しない」を**その部分だけ** supersede する。D217 が却下した
   「後始末で admission が無い cell を推測して再確定する」は維持し、
   report 構築直前の decision 欠落 fail-closed 検査も変更しない。

2. **failure decision は自己申告として信用しない。**
   `assert_campaign_layer3_chain` は failure decision を見て検査を飛ばしてはならず、
   免除の前に verifier 自身が次の 2 つを**独立に再導出**する。
   (i) `campaign_root/reports/layer3_report.json` が存在しない、
   (ii) `require_admitted_campaign(campaign_root, CERTIFIED_ACCEPTANCE)` が
   `ArtifactAdmissionError` を送出する。
   どちらかが偽なら **拒否する**。campaign identity を持たない fallback cell の免除は、
   producer が実際に作る exact shape (identity key 不在・空 generations・
   `stop_reason=supervisor-error`・critic 破棄件数 0) に閉じる。

3. **新しい journal event を作らない。** 失敗の durable な記録は既存 `run-finish` event へ
   exact projection として持たせ、完全性検査が report の cell decision と完全一致で照合する。

4. **generation accounting は緩和しない。** failure 経路で accounting event を新規に「追加」しない。
   ただし harness 成功後に admission が失敗した場合に限り、
   **未確定の pending accounting を既存 literal `partial-generation` で 1 回だけ「確定」する**。
   代償として、critic 破棄件数 1 が指す最終 generation の accounting へ
   `partial-generation` 完全一致を要求する。

5. **certifying 経路は 1 文字も変えない。** `layer3_report` の certifying 判定と
   完全性検査の certifying 要求は `admission_status == "admitted"` の完全一致のままとする。
   trial status は producer と verifier が同一の positive 述語を共有し、
   build cell が全件 admitted でなければ `complete` にしない。

6. **top-level report schema の版は上げない。** nested decision の union を増やすだけとする。

**理由:**

- 完全性検査は「書かれた report を後から検証するもの」ではなく **report を書くこと自体の関門**
  である (F332)。同型の関門がその手前の cell admission にも残っており、
  実機の自律試行で role 出力が 1 回壊れるたびに試行台帳が丸ごと欠落していた。
  `run-finish` が指す report path は存在しないまま残り、診断材料は attempt journal だけになる。
- 免除の根拠を cell dict の自己申告に置くと、**admission 成功後に positive decision を
  failure 形へ置換する単一変異が生存し、Layer 3 chain 検査を丸ごと迂回できる**。
  独立再導出にすると、置換された cell の campaign は実体として admitted のままなので必ず落ちる。
  段 3 の敵対レンズがこの経路を指摘し、変異 matrix で kill を実証した。
- 新しい journal event を足すと terminal event の配置契約 (terminal は `run-finish` の直前) を
  巻き込む。F332 の恒久対応が 6 面同時になったのはこの連鎖が理由であり、既存 event への
  projection なら配置契約に触れずに済む。
- pending accounting を確定しないと accounting bijection が落ち、
  harness 成功後の admission 失敗だけが救えなくなる。新しい状態値は導入していない。

**却下した選択肢:**

- **failure cell を report から落とす** — 診断が消える。目的そのものに反する。
- **`Exception` 一括で report 化する** — fail-closed 境界を広げる。
  予期しないプログラミング例外まで「正常な失敗」に見せかけることになる。
- **failure 用に新しい accounting 状態 (`pending-pre-invoke-failure` 等) を要求する** —
  producer が生成しない形を verifier が要求することになり、実測された実失敗
  (role-invalid 経路、accounting は既に `partial-generation`) が**また拒否される**。
  段 3 の 2 レンズが独立にこれを指摘した。
- **失敗記録用の journal event を新設する** — terminal 配置契約と event 閉集合を同時に
  変えることになり、受理集合の変更面が本 wave の目的を超えて広がる。
- **report schema を v4 へ上げる** — 既存 artifact と fixture の受理集合が大きく変わる一方、
  nested decision の union だけなら旧 consumer は影響を受けない。
