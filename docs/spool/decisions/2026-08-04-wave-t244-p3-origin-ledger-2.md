---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t244-p3-origin-ledger
seq: 2
---

## {{D:p3-origin-ledger-deferred}}. [T-244] D121 P3 の origin ledger は実装を差し戻す — 予算を origin へ束縛する設計が origin 識別の未確定で成立せず、batch 必須化で FSM の形も決まらない

**背景:** D121 決定 (7) の P3 は「origin ledger が単一 in-flight・CAS・crash replay・削除耐性を持つ」
であり、無条件義務のまま未充足だった。本 wave は新規 leaf 1 本としてこれを実装するために起票され、
file:line 粒度の実装プランを起草した (逐語 = `output/insights/2026-08-04_t244-p3-origin-ledger/`)。
段 3 の敵対 2 レンズが**独立に NO-GO** を返し、real 所見 17 件・疑い 1 件・nit 1 件を出した。

**決定 (1): 本 wave では実装せず、プランを設計メモとして凍結する。** 決め手は 2 件である。

第一に、**予算を `reflux-origin` へ束縛する設計 (D121 決定 5) が、origin 識別の未確定によって
成立しない。** プランの `origin_id` は caller が渡す不透明な 64hex で、ledger root も caller 注入
であるため、(i) 別の `origin_id` を名乗る、(ii) 同じ registry bytes を持つ別 root を 2 つ用意して
別 inode の flock を得る、の 2 経路で予算が新品になる。これは D121 決定 (5) が campaign ID について
塞いだ穴と同型である。塞ぐ規則 — origin preimage への束縛、同一の科学的 cell へ複数 origin を
発行しない機械規則、authority root の同一性 — は**設計本文 §⑤ が「未解決」として明示的に残した
項目**であり、値ではなく構造である。

第二に、**軸 (iii) (候補 batch の事前凍結) の必須化により FSM の形が決まらない。** プランの
状態機械は 1 slot = 1 query bind = 1 scalar result であり、batch cardinality・全候補の事前 commit・
seal までの結果非公開を表現できない。batch commitment を nullable な seam に留めると、
単一 in-flight は「batch を使わず逐次 query する」か「複数候補を 1 つの不透明 digest と名乗る」かの
どちらでも**恒真化する**。

**決定 (2): P10 の充足は設計本文 §⑤ の未解決欄を閉じない。** 本 wave の走行中に予算値の裁定が
land し、P10 (予算値・origin authority・軸 (iii) がユーザー裁定で確定) の 3 点が揃った。
しかし P10 は人間 gate の条件であり、origin をどう識別するか・重複発行をどう禁じるか・batch を
どう表すかという**設計項目は P10 の外にある**。「P10 が揃ったので P3 に着手できる」と読んではならない。

**決定 (3): leaf 単体では「P3 充足」と名乗らない。** 実効性に必要な層 (producer、registry/issuer、
CLI/driver、正式記録、consumer、batch policy、storage/lock admission) のうち、leaf が担うのは
codec と FSM だけである。consumer 束縛 (P7) を欠く leaf が保証するのは「正しい registry と policy を
渡し、この API だけを使う協調 caller」に対する FSM/CAS/replay に限られる。記録してよい名乗りは
「P3 用 origin-ledger の codec/FSM prototype」までとする。

**決定 (4): 予算 policy は floor 制約を必須とする。** 予算値を下限式から導き直すという裁定が
land した以上、下限制約を 1 件も持たない policy を正規値として受理してはならない。値そのものは
authority が入れるため、実装は値をハードコードせず immutable な制約として受け取る。

**却下した案:** (a) 未確定部分を親の裁量で決めて実装する — D121 却下案 (b)
「未裁定設計を既成事実にする」と同型であり、両レンズが独断確定と判定した。
(b) 未結線のまま leaf だけ land して「P3 実装済み」と記録する — D115 が却下した
「索引だけ作り consumer を付け替えない」、D122 決定 (4) が却下した「CLI へ届かない解禁」と同型。
(c) 既存の資格審査台帳を直接 import して共有化する — 別 package の編集は本 wave の scope を越え、
capability・lineage・event state が異なる。

**先行実装との関係 (正直な会計):** 資格審査側の attempt 台帳は、hash chain・連番 create-only file に
よる CAS・二相 commit・厳密一致 idempotency を既に実装している。本設計の純増は state commitment に
よる CAS、origin 用の 7 event 文法、外部 anchor、query/iteration 予算の 4 点に限られる。
なお「台帳を消せば常に新品になる」は一般化として誤りである — 生き残った成果物を持つ consumer は
台帳欠落を拒否する実テストを持つ。

**研究状態への影響:** なし。本 wave は docs と逐語のみで、production 挙動、受理集合、certified 選択、
材料レポート、proof chain、凍結 bytes はいずれも不変である。実装差分が無いため変異 matrix は対象外。
