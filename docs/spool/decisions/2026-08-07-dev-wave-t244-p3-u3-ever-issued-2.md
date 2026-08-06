---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t244-p3-u3-ever-issued
seq: 2
---

## {{D:u3-ever-issued-not-monotone}}. ever-issued cell 台帳は実装しない — repo 内の台帳は単調にならず、批准済みの予算 root trust model と両立しない

**背景:** P3 の設計裁定パッケージ §9 の択一 U-3 は「世代を跨ぐ同一 cell の再発行をどう禁じるか」を
問い、(a)「ever-issued cell」台帳を series 全体で持ち全世代で重複拒否する案が推奨・批准された
(意味等価性の判定は人間 gate に残す)。本 D はその実装 wave の判断である。逐語と裁定パッケージの
正本 = `output/insights/2026-08-07_t244-p3-u3-ever-issued-cell/`。

**決定 (1): 実装しない。** 段 2 のプランは file:line 粒度で成立していたが、段 3 の敵対 2 レンズが
**独立に同一の迂回路**を構成した。台帳を repo 内の commit 済み artifact に置き authority と同じ
捕捉 commit から読む形では、新しい authority document を書く主体が同じ commit で台帳の該当 entry を
`(series, cell) → 旧 origin` から `→ 新 origin` へ**置換**できる。置換後は「台帳に載っている」
「origin が一致する」の両方を満たすため gate を通る。したがって実装できるのは
**1 commit 内の 2 ファイルの整合**であって「ever-issued」ではない。

**決定 (2): 単調性を与える 2 手段が現状どちらも塞がっていることを固定する。** (i) 外部の
append-only anchor は、予算 root の同一性に関する択一で明示的に却下され、「同一 clone 内の
honest caller に対する保証と明示的に弱めて名乗る」案が批准済みである。(ii) 検証可能な
predecessor chain (epoch router) は D179 決定 3 が推奨形として起草したが未実装で、設計 wave 送りが
確定している。よって**批准済みの 2 つの択一 (予算 root の弱い trust model と、全世代重複拒否) は
現状の実装面で両立しない。** これは裁定時点で未見の新事実であり、親が不採用にせず
ユーザー再裁定へ返す。

**決定 (3): 「世代」が実装のどこにも存在しないことを実測として固定する。** authority document の
root key は `authority_schema` と `origins` の exact 2 つで、generation / supersedes / active pointer に
相当する field を持たない。origin ledger 本体に `epoch` / `generation` の綴りは 0 件で、
`series` の綴りは manifest field の定義・parse・canonical 化にしか現れない。production runtime の
初期化は明示禁止のままで、genesis は origin 集合を一度に焼き込み、後から足す event 型が無い。
したがって「同一 series の連続する authority document」を「世代」の代理と読み替える案は
continuity を表現できず、採らない。

**決定 (4): 台帳を書く主体 (issuer) が無い状態で gate だけを立てない。** 最初の entry を誰がいつ
載せるかは、本番 authority への entry 発行が「evidence 正本 + producer topology + 許可された
実行経路」の 3 条件成立後の人間承認 provisioning と定められた時点でそこに属する。3 条件は
いずれも未成立である。issuer 不在のまま入れると、受理集合に「存在しないファイルを要求する」条件が
増えるだけで、防げるものは増えない。

**決定 (5): DW-G04 の発火 gate を満たさないと判定する。** 現行の production 入力は authority が
entry 0 件、台帳が空で、coverage の走査は 0 回、absent / conflict の分岐は発火しない。既存の
単一 authority blob 内の cell 重複拒否は別条件であり、新 gate の発火 artifact path ではない。
発火条件を満たす既存 artifact path も計測 ID も brief に書けないため、設計メモへ留める。

**決定 (6): 名乗りの上限。** 本 wave が名乗ってよいのは「実装可否を検証し、実装しないと裁定して
択一を返した」までである。P3 充足・部分 P3・provisioning 解禁・多世代開放・cap-lift・
certified 選択は名乗らない。「意味等価な再発行を防いだ」「全世代重複拒否を実装した」とも
名乗らない。D114 の承認上限 1、D166 の P4 FAIL、P3 の FAIL はいずれも不変である。

**理由:** 実装しても防げるものが増えず、名乗り (全世代重複拒否) と実装 (同一 commit の整合) が
食い違う。ここで部分実装すると、D164 が却下した「発火しない検査を防壁として記録する」と、
D147 が却下した「未結線のまま leaf だけ land する」の両方を同時に踏む。加えて、過去 wave の
使い捨て probe を subprocess 実行して終了コードを検査する受入テストが現役で存在するため、
実装すれば受入全走が赤になる。プランはこの probe を「歴史 artifact」と誤認していた。

**却下した選択肢:**
- 台帳の Git 履歴単調性 (parent commit の台帳との包含) を本 wave で検査する — merge・初回導入・
  shallow clone・履歴書換えの扱いを決めずに first-parent だけを正本にすると、批准された trust model
  とは別の履歴 trust model を発明することになる。
- 同一 commit の authority ↔ registry 整合だけを別名の防御部品として入れる — 発火経路が無く、
  現役 consumer を壊し、防げるものが増えない。研究前進に直接効かない防御的堅牢化を既定で
  見送るという裁定 (D205) にも当たる。
- 親の裁量で「弱い保証」として実装し完了と記録する — 未裁定設計の既成事実化であり、
  D121 却下案 (b) と同型である。

**研究状態への影響:** なし。本 wave は docs と逐語のみで、production 挙動・受理集合・
certified 選択・材料レポート・試行台帳・proof chain・凍結 bytes はいずれも不変である。
実装差分が無いため変異 matrix と実装後の受入全走は対象外。
