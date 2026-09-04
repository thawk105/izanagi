# [T-2148] 排他権の世代の粒度と非保持走行の値 — 実装

D1527 の裁定を signed-v6 受領証の契約へ実装した wave の記録である。材料の実測は先行 wave が
済ませており、その一次資料は `output/insights/2026-09-02_t2148-lease-generation/` にある。
本 dir は**実装側の逐語と変異台帳**を持つ。

- 実装 commit: `b101d10e123533c3d751786d556f42a2feb2b500`
- 基準 main: `229e030a313bb1a3f5510d4991e327c00b538250` (ff で取り込んだ)
- 測定機: Pegasus login node からの dispatch (計算ノード)
- branch: `worktree-dev-wave-t2148-lease-generation-semantics`

---

## 1. 実装した意味論

`lease_generation` の受理値域を、64 桁小文字 sha256 の完全一致だけから
**`[0-9a-f]{64}` と予約語 `"not-acquired"` の直和**へ広げた。

- 64 桁値は**排他権の 1 回の取得**に対応し、別の取得へ再利用しない (D1527 の粒度)。
- `"not-acquired"` は**排他権を取得しなかった走行**を表す (D1527 が同じ回で定めることを求めた値)。
- 判定は完全一致だけで、前後空白の除去・大文字小文字の畳み込み・部分一致・Unicode 正規化を
  行わない。検査点は projection、canonical payload、expected の 3 経路で、reference issuer も
  同じ helper へ委譲する。
- どちらの値も caller の自己申告である。この module は live な排他権を読まず、取得の有無を
  検査しない。marker の一致は「caller が申告した状態と一致した」ことだけを意味する。
- D1443 に従い、**production の着地ツールがこの verifier を呼ばないためこの関門は不可避でない**
  ことを docstring へ明記した。
- 世代の**導出方式は選んでいない** (D1528 により鍵と発行権限の配置の後)。

## 2. 段 2 plan の 4 項目を段 3・段 4 が棄却した

段 2 plan は、marker に加えて次を提案していた。

- `project_v5_receipt` / `issue_signed_receipt` への必須 `lease_acquired: bool`
- verifier への `expected_lease_acquired`
- `(lease_acquired, lease_generation)` の組を検査する helper と早期の重複検証
- issuer CLI の `--lease-not-acquired` と required mutually-exclusive group

**親はこれを scope 膨張として棄却した。** 理由は 2 つである。

1. marker と 64 桁小文字 16 進は**構文的に交わらない**ので、値そのものが取得あり / 取得なしを
   運ぶ。既存の `payload["lease_generation"] == expected_lease_generation` は既にその 2 状態を
   区別する。bool 引数は同じ区別を 2 度目に行う関門であり、受理される受領証の集合も署名 bytes も
   変えない (`DW-G05` の成果物影響を書けない)。
2. 段 3 レンズ A が示したとおり、**bool を足しても取得の有無は照合されない** — 状態と期待値の
   両方を同じ caller が渡すためである。棄却によって失う保証は無い。

棄却の結果、公開関数の signature は 1 つも変わらず、既存 caller の呼び方も 1 箇所も変わっていない。
段 3 レンズ A が「必須 keyword 追加で壊れる caller 9 箇所」を挙げていたが、この所見は
**対象そのものが消えた**。

## 3. 段 3 の 22 所見と段 6 の 3 must-fix

段 3 は 2 レンズで各 11 所見 (real 7 + refuted 4 / real 7 + refuted 4)。逐語は
`verbatim/s3-lens-a.md`、`verbatim/s3-lens-b.md`、裁定は `verbatim/s4-ruling.md` にある。
段 6 のレビューは A が must-fix ゼロ・nit 1 件、B が must-fix 3 件だった。

**段 6 の must-fix 3 件はいずれも記録の訂正であり、コード変更を要さなかった。**
したがって fix 子は立てていない。内容と対応は次のとおり。

1. **T1 が M2 と M3 の両方で赤になる** (過剰決定)。→ 5 節のとおり分類して記録した。
2. **実装子の報告の「両者の repo 内 importer は当該 test file のみ」は誤り。**
   署名 module は issuer からも import され、issuer 自身が verifier を呼ぶ。→ 4 節で訂正した。
3. **T5 は fixture の projection や鍵の読取り・署名へ到達しない** (parser と入力検査で終わる)。
   → 5 節で証拠水準を分けて書いた。

## 4. consumer の閉包 (訂正版)

先行 wave の記録と親 brief は「production consumer は存在しない」と書いていた。段 3 レンズ A・B と
段 6 レビュー B の指摘に従い、次へ狭める。

- `tools/acceptance_receipt_signature.py` を import するのは
  `tools/acceptance_issuer_reference.py` と `orchestrator/tests/test_external_acceptance_signing.py`。
- `tools/acceptance_issuer_reference.py` を import するのは当該 test file だけ。
- **待ち手 (`tools/dev_wave_wait.py`) と着地ツール (`tools/dev_wave_land.py`) からこの 2 module への
  配線は無く、tracked な着地ツールは v5 だけを受理する。**
- **repo 外の運用 copy は未測定である。** 本 wave はそれを更新していない。

したがって本変更が変えるのは、署名 module と reference issuer の受理集合、およびテストの受理集合
だけである。certified な選択結果、材料レポート、試行台帳の値、production の受入・着地の受理集合は
変わらない。

## 5. 変異検査 — 4/4 KILLED、ただし M2 と M3 は構造的に分離できない

probe (全件 SURVIVED 期待で観測 node を集める) → 本走の 2 段で行った。

| ID | 変異 | 結果 | 観測 node |
|---|---|---|---|
| M01 | 共通 helper の marker 枝を「文字列なら何でも受理」へ緩める | KILLED | T4, T5 |
| M02 | canonical payload の検査だけ sha256 のみへ戻す | KILLED | T1, T2 |
| M03 | expected 側の検査だけ sha256 のみへ戻す | KILLED | T1, T3 |
| M04 | issuer の入力検査を sha256 のみへ戻す | KILLED | T5 |

- baseline は PASSED / rc=0 / 失敗 node 0 件。台帳は `mutation-ledger.json`
  (spec hash `0cfda4bf…`、`repo_head=b101d10e1`)。probe は `mutation-probe-attempt1.json`。
- **T1 は M2 と M3 の両方で赤になる。** `verify_signed_receipt_signature` は内部で
  `canonical_signed_payload_bytes` を呼ぶため、marker を expected として検証する経路は
  canonical 層を必ず通る。**この 2 層は黒箱テストで分離できない。** `DW-M03` に従い、
  T1 は M2 / M3 の単独層証拠から外す。
- **M3 における T3 の赤は診断文字列だけの差である** (`signed receipt context mismatch` が
  `invalid expected_lease_generation` になる)。どちらも拒否なので受理集合は変わらない。
  `DW-M03` に従い kill の証拠に数えない。
- 差し引き後の単独層証拠は次のとおり。**M02 は T2 が単独で押さえる**
  (canonical 層で marker が拒否されると `_signed_control(lease_generation="not-acquired")` の
  受領証構築自体が落ちる)。**M04 は T5 が単独で押さえる。M01 は T4 が押さえる。**
  **M03 を単独で押さえるテストは存在しない** — 上記の構造的結合のためである。
- 段 6 レビュー A の nit も記録する。**T4 は実装を変更前へ全戻ししても緑になる**ので、
  marker 機構の実在証拠には数えられない。M01 (union を過度に広げる方向) の防壁としては有効である。
- T1〜T4 は実 production-v5 fixture と実 Ed25519 鍵を通す。**T5 は parser と issuer の入力検査で
  終わり、fixture の projection や鍵の読取り・署名へは到達しない** (段 6 レビュー B の must-fix 3)。

## 6. 段 5 が codex サービスの 404 で 2 回失敗した

実装子の投入は 3 回行った。1 回目 (23:54 JST) と 2 回目 (23:57 JST) は
`wss://chatgpt.com/backend-api/codex/responses` と
`https://chatgpt.com/backend-api/codex/responses` の両方が 404 を返し、
`backend-api/codex/models?client_version=0.152.1` も 404 で、`turn.failed` で終わった。
codex CLI は `0.152.1`、実行 bytes の sha256 は receipt に記録されている。

**同 wave の段 2 (22:11 JST) は stderr が完全に空で成功していた**ので、22:23〜23:54 の間に
repo 外で状態が変わったと切り分けられる。13 分待って 3 回目 (00:18 JST) を投入すると rc=0 で
成功した。**親はコードを代筆していない** (D95 決定 3)。詳細は failures 台帳へ記録した。

## 7. 測定と推論の区別

| 事項 | 出所 |
|---|---|
| 変異 4/4 KILLED、baseline PASSED | **実走** (計算ノード dispatch、台帳あり) |
| 変更前 baseline 17 passed / 変更後 22 passed | **実走** (前者は親の dispatch、後者は実装子の plain runner) |
| 段 5 の 404 と 3 回目の成功 | **実走** (attempt log と receipt) |
| consumer 閉包 (4 節) | **repo 全体の grep**。repo 外の運用 copy は未測定 |
| M2 / M3 が黒箱で分離できないこと | **コード読解 + 変異の観測 node の一致** |
| 「取得の有無は照合されない」 | **コード読解** (段 3 レンズ A、段 6 レビュー B が独立に確認) |

## 8. この wave が言えないこと

- D1450 の**実効的な**再送防止は達成していない。同じ 64 桁値を別の取得で再利用することは
  拒否できない。粒度の契約と非保持走行の値を確定したところまでである。
- 世代の導出方式は選んでいない。inode・xattr・保護された sidecar・外部台帳のいずれも採用していない。
- repo 外の運用 copy と production への配線は更新していない。
