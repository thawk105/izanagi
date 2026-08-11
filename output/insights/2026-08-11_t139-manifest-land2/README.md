# [T-139] land 2 session 1 — 基礎層 (foundation-only)

branch `worktree-dev-wave-t139-manifest-w2`。land 1 の fold commit
`F_r` = `39d760985a5e37d20464c394760bf65596156566` の後、S6 (a) に従って同一 branch を継承した
land 2 の第 1 session である。**本 session は land しない。**

## 状態の申告 — `foundation-only`

**`package.md` §S7 の #1〜#3 を「満たした」とは記録しない。** 段 3・段 6 の 4 レンズが独立に
「resolver を書いても呼ぶ側が本 session の scope に無い以上、防壁は 1 度も発火しない」と判定した。
本 session が閉じたのは、承認 trust root の**基礎層**である。

## 入っているもの

| 面 | 内容 |
|---|---|
| `orchestrator/preregistration/erratum.py` | 第 2 erratum の承認 v2 (2 operation) 対応。erratum_id 別 exact-key grammar。合成経路の承認 membership 検査と digest 迂回封鎖 |
| `orchestrator/preregistration/blobref.py` | `str` subclass による digest 比較迂回の封鎖 (構築時の正規化 + 読取経路の再検査 + `bytes` 比較) |
| `orchestrator/preregistration/approval_payload.py` (新規) | 固定 `F_r` の `docs/decisions.md` から D282 承認 payload を exact-key で読む parser。機械可読の拒否理由つき |
| test 3 file | 上記に対する正例と負例。86 passed / 0 failed |

**`__init__.py` へは 1 名も export していない** (D264 の非 export を維持)。
ただし段 4 裁定に従い、これは security boundary ではなく**衛生**と呼ぶ。

## 入っていないもの (後続 session)

approval manifest 実体、`resolve_effective_preregistration`、`PreregBinding`、Git trust root の
強化、raw snapshot API、受領証 writer / 固定 semantic validator / conformance vectors、
`a13` 台帳 consumer、`submit_pilot` / PBS preflight / driver / collector、correctness anomaly の
構造化還流、certified 側 consumer、pilot 投入。

## 本 session が確定した順序制約 (新事実)

**承認 manifest は conformance vectors の digest を pin する義務がある** (承認済み
`record-items-v2.md` §7: 「conformance vectors を実装 wave が発行し、その digest を approval
manifest が pin する」)。vectors は §6 の cross-field 制約と §7.1 の 20 制約に対応する試験資材で、
固定 semantic validator と同じ session に属する。

→ **manifest 実体の発行は、semantic validator + vectors を作る session でなければ承認契約を
満たせない。** これは「consumer 不在」とは独立の、承認文書由来の順序制約である。

## 実測値 (checkout = `cb73aa10`)

- 焦点 3 file: **86 passed / 0 failed** (計算ノード dispatch)
- 変異 matrix: **9/9 KILLED、期待 node 完全一致、rc=0**
- 全史 provenance 監査: rc=0 (新規違反なし)

### 変異 1 巡目は期待 node の誤りで MISMATCH 3 件だった (erratum)

`mutation-ledger-round1-erratum.json` に残す。**9 変異とも赤くなっており生存は 0 だったが**、
親が期待 node を fix 子の報告から書き写し、実測で完全集合を再導出しなかった。

- MF2 / ME1: **過少申告**。実際に赤くなる node を取りこぼした (fix 子が自ら新設した node を
  報告に含めていなかった分を含む)。
- ME4: **過剰申告**。`approved_blobs` の role 集合検査を消しても「重複 role」の負例は赤くならない。
  **重複は前段の duplicate key 検査に先取りされている** (mask の実例)。訂正版に注記して登録し直した。

## 段 4 の変異事前登録は 10 件中 7 件が実効 gate に当たっていなかった (記録)

段 4 の時点では実装が存在せず、親は段 2 プランから変異位置を書いた。段 6 レビュー D が
静的追跡で「単独 KILL を書けるのは 3 件だけ」と判定し、残りを
mask / equivalent / テスト自身を弱めるだけ / 受理集合を動かさない診断赤 に分類した。
段 6 の fix 子 3 本へ「その検査を消したとき赤くなる nodeid を名指しせよ」と要求して照準し直した。

**`DW-M01` は「登録前にコードで確認する」ことを求めており、実装前の段 4 で位置だけを書いたのが
誤りである。** 実装が段 5 で生まれる wave では、段 4 の登録は暫定であり段 6 で再導出を要する。

## 敵対レンズが見つけた実欠陥 (すべて実行で裏付けあり)

1. **合成後 digest 比較が `str` subclass で迂回できた** (レビュー C、must-fix)。
   `blobref.py` を直した lane はこのファイルを所有しておらず、`erratum.py` を書いた lane は
   自分の担当所見ではなかった。**分割の副作用で同型欠陥が残った実例。**
2. **承認 payload の負例 14 件が基底例外を捕捉していた** (レビュー D、must-fix)。
   「拒否された」は見えるが「正しい理由で拒否された」を見ておらず、変異の
   `first_rejecting_node` を証明できない。
3. `compose_core` が承認 membership を確認せず全 registered ID を適用していた
   (謳うだけで発火しない恒真な保証)。
4. 見出し境界が先頭空白 1〜3 の ATX 見出しを認識しなかった。
5. `BlobRef` の構築後 subclass 再注入 (読取経路の再検査で閉じた)。
6. wave 前にあった `old_text` bytes 束縛の負例が等価物なしで消えていた。

## 成果物

- `mutation-spec.json` / `mutation-ledger.json` / `mutation-ledger-round1-erratum.json`
- `package.md` — ユーザー裁定パッケージ (RP-1〜RP-4)
- `verbatim/` — 段 1〜段 6 の全子出力の逐語
