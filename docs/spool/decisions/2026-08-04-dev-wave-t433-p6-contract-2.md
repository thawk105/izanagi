---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t433-p6-contract
seq: 2
---

## {{D:p6-sufficiency-contract}}. P6 の意味的充足は admission 結線までを要求する認定契約の案として起草する — 集合出力だけの実装・条項削除 fail-open・名乗りだけの独立性を認定から排除し、採否と V1 は裁定パッケージへ返す

**背景:** D150 決定 (6)(a) は「実装のふりをした非適用」の判定基準 — 空 handler と恒真 assert が
D138 の列挙 (handler・全 witness-kind adapter・正負 calibration・未知 kind の fail-closed) を
形式的に満たす穴 — を意図的に未定義とし、裁定パッケージへ返した。ユーザー裁定 (2026-08-04 の
/rulings、worklog (175) の V2 項) は「P6 設計 wave が意味的充足契約の案を起草し、正負 calibration の
具体反例・非空の限界効果を示す変異・独立検査者の要求を含めて裁定パッケージで返す。V1
(`NOT_CLAIMED` の射程) も同 wave で扱う」。本 wave はその設計 wave である。契約案本文と逐語の正本 =
`output/insights/2026-08-04_t433-p6-sufficiency-contract/`。

**決定 (1): 中心所見を記録する — 認定手続にも「限界効果ゼロ」が再発する。** 段 3 の敵対レンズ
2 本が独立に同一の欠陥へ到達した (合議ではない): 期待される集合値 (`forbidden_candidate_keys`、
`marginal_keys`) を返すだけで候補 admission に一度も作用しない実装が、段 2 案の calibration・
全変異・独立再計算をすべて通過できる。D138 決定 (1) が受理集合について示した「限界効果ゼロ」と
同型の恒真化が、充足**認定**の層でも成立してしまう。したがって契約は「正しい集合を返すこと」と
「受理集合が実際に変わること」を別条項に分け、後者を end-to-end の admission A/B 対
(P6 有効アームで禁止候補が generalized cut を唯一の理由に build 前 reject され、無効アームで
同じ候補が通る) で検査することを認定の中心要件とする。

**決定 (2): 契約は人間 gate の判定規則 + 判定可能条項の列挙として書き、機械 gate を作らない。**
認定の出力は機械 status field でなく docs artifact の認定記録 (対象 revision SHA・契約版 hash・
corpus / 変異集合 hash・verdict・検査者 attestation への参照) とし、cap-lift receipt (別 T、
worklog の V3 項が所有) はこの記録への参照を収容する。認定記録は revision に束縛され、cap-lift
承認者は申請時に現 revision との一致を照合する義務を負う (不一致 = 認定無効・保留)。発火は
「実装 land 後・cap-lift 申請前の認定 request 起票」で定義し、request 前は D150 決定 (4-b) の
承認保留が既定のまま残る。

**決定 (3): 変異排除規則はコア条項について fail-closed とする。** 「反転変異を書けない条項は
恒真として契約から落とす」という一般規則をそのまま全条項に適用すると、規律 2 由来の条項
(verifier 必須・exact cut 独立性・admission 結線) を「変異を書けなかった」ことを理由に削除できる
fail-open になる。コア条項は削除不可とし、反転変異を書けない場合は認定不可とする。あわせて
kill 判定は calibration verdict の反転のみ (副作用 bit を数えない)、合接条項は conjunct 単位、
変異と hidden case の最終選択権は独立検査者、corpus・対応表は認定 request 前に hash 固定とする。

**決定 (4): 独立検査者は名乗りでなく監査可能な証拠で要求する。** fresh context の宣言だけでは
申請者自身の別 session と区別できない。認定記録に attestation (入力閉集合の digest・workspace
非継承・hidden case / 変異を検査者が選択した旨) を必須添付し、偽装を機械的に不可能にすると
主張せず「事後監査で反証可能な証拠を残すこと」を契約義務とする。真正性の確認は人間 gate。

**決定 (5): V1 は量化を明示した (a′) を推奨し、ユーザー裁定へ返す。** 既存 3 択 (per-run gate /
cap 不開放 / global 免責) はいずれも「run」の量化が未定義で、同じ入力集合に許可と不許可の両方を
導ける (両レンズ一致)。(a′) = P6 状態の判定単位は cap-lift 申請 (revision・origin・運転構成・
claim 有無を固定し receipt に束縛)、run 単位の義務は receipt との conformance (構成が異なる run は
承認の外で上限 1 に落ちる)、`NOT_CLAIMED` は申請をまたぐ standing 免責にしない。ユーザー裁定
U2 (`NOT_CLAIMED` だけを免責) は申請評価の中で保存される。「`NOT_CLAIMED` 構成に多世代を許すか」
という D150 決定 (6)(b) の残余は (a′) でも残り、(a′) は許す側の答えである。

**決定 (6): 実装しない。** 根拠は独立に 3 つ: (a) ユーザー裁定の文言が「設計と裁定パッケージまで」。
(b) `DW-G04` — 認定手続の発火条件を満たす既存 artifact (P6 実装・calibration fixture・認定
request) が 1 件も無い。P6 実装の不在は識別子 4 種の文字列不在 + D150 決定 (4-b) の記録 +
phase 文書の記載の合成で確認した (文字列不在単独を意味的不在の証明としない)。(c) 契約の採否と
V1 が未裁定であり、実装は既成事実化になる。段 5・6 は飛ばし、変異事前登録・変異 matrix・
受入全走は対象外 (実装差分ゼロ)。承認上限 1 (D114)・凍結 bytes・事前登録文書は不変。

**却下した選択肢:**
- 集合出力の一致だけで「実装済み」を認定する (段 2 案) — 決定 (1) の恒真化がそのまま残る。
- 反転変異を書けない条項を無差別に削除する排除規則 — 規律 2 条項まで削除できる fail-open。
- fresh context の名乗りを独立性の証拠に数える — 自己検査の儀式化。attestation の無い認定は
  D150 決定 (4-b) が禁じた「宣言を証拠に数える」の変種になる。
- claim 有無の状態分類を handler calibration のケースに置く — 4 値実行結果と状態語の型境界
  (D150 決定 (3)) を calibration 内で壊す。状態分類の照合は認定手続 (人間 gate) 側に置く。
- 認定の失効を自動検知する機械 gate の新設 — 本 wave の不変条件 (機械 gate を作らない) に反する。
  申請時照合の人間義務として規定し、機械束縛は将来 wave の所有とする。

**この決定が確定していないこと:** 契約案の採否 (U1)、V1 の裁定 (U2)、adapter 正例要件 (U3)、
calibration 新鮮性 (U4)。いずれも裁定パッケージとしてユーザーへ返した。

**研究状態への影響: なし。** 本 wave は docs と insights のみで、production 挙動、実験の機械
受理集合、certified 選択、材料レポート、proof chain、凍結 bytes はいずれも不変である。契約が
採用された場合に変わるのは cap-lift の規範上の受理集合 (基準不在の保留 → 基準付き認定) だけで、
それは採用の裁定時に発効する。
