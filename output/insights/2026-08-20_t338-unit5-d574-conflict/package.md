# [T-338] 投入gate 単位5 (writer + conformance vectors) — D574 衝突の発見と裁定パッケージ (2026-08-20)

本 wave は単位5を実装しなかった。**理由は「難しいから」ではない。** 段1 brief 起草・段2 codex
plan (read-only) の結果、単位5の設計前提そのものが、本日 land 済みの別決定 (D574) と
正面から矛盾していると判明した。**判断はユーザーが行う。親は推奨を添えるが決めない。**

## 分かったこと (一言で)

単位5の設計根拠にしていた s1-classification (2026-08-18) の「manifest 自己 pin で conformance
vector index の digest を足せば足りる」という前提は、**D574 (2026-08-20 land、T-139 Q1
canonical decision) が名指しで却下済みだった。** D574 決定(4) 逐語:

> conformance vector index の trust edge を approval payload 側に置く。vector index の期待
> digest 三つ組は manifest 自身ではなく、有効な approval payload に置く。(中略) **manifest 単独の
> 自己 pin は受理の根拠にしない。**

D574 の却下選択肢にも同じ趣旨が明記されている: 「manifest 自身の vector pin だけを trust root に
する — manifest と index の同時差替えによる自己整合を止められない。」

## 経緯

1. `docs/decisions.md` D509 (単位分割・規模上限)・D563 (単位1/2設計規約) を正本として段1 brief
   (`verbatim/s1-brief.md`) を起草した。写像元は record-items-v2.md §6.10 (writer)・§7
   (conformance vectors) と、s1-classification.md (`output/insights/2026-08-18_t338-submission-gate-sizing/verbatim/s1-classification.md`)
   の「vector index の sha256 を1 field 足すのは新設機構ではない」という分類。
2. 段2 codex plan (`verbatim/s2-plan.md`、read-only・reasoning=max) が、自ら `docs/decisions.md`
   を確認した結果 D574 を発見し、s1-classification の前提と矛盾すると報告した
   (plan `## 4. NO-GO判定` 項目1)。
3. 親が `docs/decisions.md:23166-23217` (D574 全文) と、D574 の起票元 wave の worklog archive
   entry (720) (`docs/archive/worklog-phase3-0820-720-721.md`)、entry 720 が指す K2/K3 定義
   (`output/insights/2026-08-13_t139-land2-q4/package.md:116-135`) を直接読み、矛盾を確認した。

## 確認した事実

- **D574 は T-139 の Q1 決定であり、2026-08-13 の `/rulings` (K1〜K4/V1〜V5、全問 (a)) を
  本日 (worklog entry 720) docs のみで land した。** 実装差分はゼロ。B1 (V3 経由)・B4 (V2 経由)
  を閉じたと明記する。
- **entry 720 自身の「次の一手」は、T-139 の残作業を「投入経路 wave
  (manifest+resolver+writer+validator+vectors の実装、K2/K3 裁定に従う)」と明記している。**
  「writer」「vectors」という語が、T-338 単位5 のスコープ名と文字どおり一致する。
- **にもかかわらず、entry 720 は T-338 の「次の一手」欄を一切更新していない**
  (entry 720 直後の [T-338] carry は無変更で `(719)` のまま)。T-338 側の worklog thread
  (単位3/4 land、entry 724 含む) も D574 に一切言及していない。**T-139 (D574/K系列) と
  T-338 (D509 6分割) は、同じ実装面 (writer・validator・vector・manifest) を指しながら
  互いに参照しない 2 本の独立した意思決定系列になっている。**
- D574 決定(1)は、D320 (bytes級 provenance の新設・維持は既定で見送り) の例外を **3 対象**へ
  個別に認めている: (a) approval manifest 本体、(b) D282 の `record_items`/`receipt_schema`
  承認役割を後続で担う**新しい exact-byte approval payload**、(c) conformance vector index の
  期待 digest 三つ組。(b) は現行 `orchestrator/preregistration/approval_payload.py` (exact 6
  role、s2-plan.md 確認済み) を単純拡張しては済まない新規 payload であり、単位5 単独の scope を
  超える可能性が高い。
- **D574 決定(3) は、単位3が今日実装した B1 の閉じ方 (D509 決定5「第3経路」= `cmake_cache`
  申告値の拒否専用化のみ、raw `CMakeCache.txt` は読まない) より要求が広い。** 決定(3) 逐語:
  「validator は申告値と独立に、schema の argv に現れる macro 定義、compile_commands の当該TU
  の実 compile argv、実ファイル上の raw `CMakeCache.txt` を再読して三者を比較する。」
  単位3 (`_semantic_validator.py`、本日 land、worklog entry 724) が raw `CMakeCache.txt` を
  独立に再 parse しているかどうかは、本 wave は検証していない (scope外)。**もし読んでいなければ、
  今日 land したばかりの単位3 が同じく今日 land した D574 に対して既にギャップを持つ。**
- 段2 codex plan 自身の見積り: s1-classification 準拠 (manifest 自己 pin) の薄い writer なら
  単位5 の production 純増は **98〜128行**で、単位6へ80行残しても名目上収まる (余裕
  18〜48行)。**D574 準拠 (payload 側 trust edge) まで含めると少なくとも125〜175行以上となり、
  単位6の余地を保証できない**、という数値も plan 自身が出している。

## この wave が実装しなかったもの

`orchestrator/submission_gate/` 配下のコード・テストは一切変更していない。段2 codex plan
(read-only) の起草だけで停止した。段3 敵対相談・段4 裁定・段5 実装は行っていない。

## 決めてほしいこと

### Q-A (最重要). 単位5は D574 のどちらの trust edge 設計に従うか

- **(a) D574 決定(4) に従う (payload 側 trust edge)。** s1-classification の manifest 自己 pin
  案を撤回する。単位5 の scope に「新しい exact-byte approval payload」または既存
  `approval_payload.py` の拡張を含める。production 見積りは125〜175行以上となり、
  D509 上限6,200行 (残余226行) に単位6 の余地を残せるかは未確定 — 別途の規模実測が要る。
- **(b) 当面は s1-classification 準拠 (manifest 自己 pin) で単位5 を実装し、D574 との
  reconciliation は別途の decision へ切り出す。** D574 決定(4) が明示的に却下した設計を
  採用することになるため、**規律2 (正しさゲートを緩める変異を許さない) に照らして採れない
  可能性が高い**、と親は考える。conformance vector index の trust edge は「受理集合を
  空にしない」ための機構であり、既に却下された自己 pin を敢えて採ると、後で D574 準拠へ
  作り直す前提の暫定実装になる。
- (c) 単位5 の scope を「writer 本体 (§6.10 箇条1、D574 と無衝突)」だけに縮小し、
  conformance vectors (§7、D574 と衝突する部分) を別 wave (D574 reconciliation 後) へ切り出す。
  writer 本体は段2 plan が GO と判定済み (`verbatim/s2-plan.md` §2)。ただし writer の
  「受領証 destination namespace」(plan NO-GO 理由4) は本 wave も未確定のまま。

**親は (a) を推奨する。** 理由: D574 は決定(4)の却下選択肢で自己 pin を名指しで却下しており、
(b) は既に却下済みの設計を実装することになる。規律2 は「正しさゲートを緩める変異を許さない」と
定めており、trust edge の弱い版 (自己整合で偽装可能) を作ってから作り直す提案は、遠回りなだけで
規律に照らして採用しにくい。ただし (a) は単位5 単独の scope・予算を超える可能性が高く、
「投入gateに production 2,570〜6,200行を投じるか」を問うた D509 決定8 Q-A と同じ構造の
費用判断になるため、**親は Q-A に確定推奨を付けない。**

### Q-B. 単位3 (本日 land、entry 724) の B1 実装は D574 決定(3) に対して監査が必要か

- **(a) 別 wave として直ちに監査する (親の推奨)。** 今日 land したばかりの2つの決定
  (D509系の単位3、D574) が同じ日に矛盾する要求を持ちうる状態を放置しない。
- (b) 単位6 (統合) の scope に含める。
- (c) 監査を保留する (理由を明記して見送る)。

### Q-C. T-139 (D574/K系列) と T-338 (D509 6分割) の関係を明示的に reconciliation する
  decision を起こすか

- **(a) 起こす (親の推奨)。** 「投入経路 wave (K2/K3)」と「T-338 単位5/6」が同一実装面を
  指すことを canonical に確定し、以後の worklog next-step 記述で相互参照させる。
- (b) 現状のまま (2 本の独立系列として進める)。→ 同じギャップが再発するリスクを親は指摘する。

## この wave が主張しないこと

- 単位5 の実装。コード・テストの変更はゼロ。
- D574 と D509/s1-classification のどちらが正しいかの裁定。これは親が決める性質のものではない。
- 単位3 (本日 land) に実際にギャップがあることの確定。可能性を指摘したに留まり、
  `_semantic_validator.py` の raw `CMakeCache.txt` 再読の有無は本 wave では確認していない。
- certified 選択・材料レポート・proof chain・凍結 bytes・受理集合の変更。いずれも不変である。
