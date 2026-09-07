---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2333-shard-timeline
seq: 2
---

## {{D:session-timeline-report-fields}}. 受入 shard report への観測 field 追加は `_REPORT_FIELDS` の厳密一致を保ったまま行う

**決定:** D1647 の「観測 field を足す」は、`tools/acceptance_shards.py` の `_REPORT_FIELDS` へ
`session_timeline` を**必須要素として足し**、`merge_reports` の
`set(report) != _REPORT_FIELDS` という厳密一致 gate は**そのまま保つ**ことで実装する。
部分集合判定・任意 field 許容への緩和は採らない。

**理由:**
- `merge_reports` は top-level key 集合の厳密一致を要求する。したがって「report.json に field を
  足す」実装は (a) `_REPORT_FIELDS` を伸ばす か (b) 厳密一致を緩める の 2 つしかない。
  (b) は gate の弱体化であり規律 2 に反する。D1647 の「受理集合には触れず」を
  「key 集合の字面が変わってはならない」と読むと、裁定が自分の命じた行為の唯一の実装を
  すべて禁じることになる。裁定は実行できるように読む。
- shard report は 1 回の走行の中で書かれ、同じ走行の中で読まれる。session dir は走行ごとに
  作られ、consumer はその session だけを読む。producer と consumer は同じ commit で出荷される。
  したがってこの変更以前に書かれた report が新しい consumer に渡ることはなく、
  **以前 certified になった走行が reject されることはない。**
- 「旧 14-key を厳密に読む既存 consumer がある」という段 3 の指摘は現物で refuted した。
  該当 script は過去の insight 用の入力準備であり、`orchestrator/tests` と `tools` から参照する
  test / tool が 0 件で、当時の shard 数と固定 count を要求するため新しい report を食わせられない。

**却下した選択肢:**
- 厳密一致を部分集合判定へ緩める — 未知の top-level key を持つ report まで受理するようになる。
- field を足さない — 裁定の実行を拒否することになる。

## {{D:no-timeline-shape-validation}}. 観測 field の形を検査する層は新設しない

**決定:** `session_timeline` の key 集合・型・有限性・非空性を検査する helper を
`validate_report_evidence` へ足さない。同関数と `merge_reports` は 1 行も変えない。
`_REPORT_FIELDS` への key 追加だけで、key の存在は既存 gate が保証する。

**理由:**
- D1647 は「gate・判定は足さない」と定め、timeline に基づく判定を同時に足す案を明示的に却下した。
  新 field 専用の検査 helper は検査の追加であり、それが守る危険 (壊れた timeline) は実在の欠陥では
  なく仮想リスクである。
- 検査を足さなければ、**観測値の内容が判定を変える経路が構造的に存在しなくなる。**
  「timeline に基づく判定ではない」と弁明する必要がなくなり、段 3 の両レンズが挙げた
  「欠測・malformed が merge verdict を変える」という懸念が設計から消える。
- 判定を足していないことは positive control で固定する。壊した timeline (配列、空 dict、NaN、
  key 欠落) を載せても merge が `ok` を返すことを検査し、その検査が恒真でないことを
  「`validate_report_evidence` へ非空検査を足すと赤になる」変異で確かめた。

**却下した選択肢:**
- 形だけの検査を足す — 「形」と称しても有限性・非空性は値と cardinality の条件であり、
  観測の欠陥が受入の判定を変える経路を作る。
- 検査も key 追加もしない — 厳密一致 gate があるので producer の出す report が全て弾かれる。

## {{D:collection-finish-clock-position}}. collection 終了時刻は acceptance plugin 自身の `pytest_collection_finish` (trylast) で採る

**決定:** 受入 shard の collection 終了時刻は、acceptance plugin に自前の
`pytest_collection_finish` を `trylast=True` で置いて採る。
`pytest_collection_modifyitems` の末尾では採らない。

**理由:**
- acceptance plugin の `pytest_collection_modifyitems` は `trylast=True` の**非 wrapper** である。
  一方 test suite 側の conftest の同 hook は wrapper であり、acceptance の hook が戻った後に
  yield 後処理 (real-repo shard state の検査、loadgroup suffix の除去、duration による LPT 並べ替え)
  を実行する。選別完了時点で時刻を採ると、これらの所要が「collection 後の空白」として記録される。
- この観測の目的は受入 wall の内訳を分けることであり、LPT 並べ替えと suffix 除去は分けたい
  区間そのものである。採取位置を誤ると観測の目的が潰れる。
- conftest 側の `pytest_collection_finish` は `tryfirst=True` なので、`trylast` の acceptance 側が
  最後に走り、memo の prewarm も含めた collection 全体の終端を捉える。

**却下した選択肢:**
- `pytest_collection_modifyitems` の末尾 — 上記のとおり実際の終端より早い。
- 両方を採って差分も記録する — D1647 が挙げた観測は 3 種であり、増やすのは射程外。
