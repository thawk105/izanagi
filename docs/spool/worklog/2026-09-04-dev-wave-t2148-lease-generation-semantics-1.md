---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2148-lease-generation-semantics
seq: 1
title: [T-2148] 排他権の世代の粒度を取得ごとに定め、非保持走行の値を同じ回で確定した — 段 2 plan の 4 提案は「同じ区別を 2 度行う関門」として棄却した (コード + テスト + insight、branch worktree-dev-wave-t2148-lease-generation-semantics、変異 4/4 KILLED)
---

## 本文

- **D1527 の裁定をそのまま実装した。** `lease_generation` の受理値域を 64 桁小文字 sha256 の
  完全一致だけから、それと予約語 `"not-acquired"` の直和へ広げ、64 桁値は排他権の 1 回の取得に
  対応し別の取得へ再利用しないこと、予約語は取得しなかった走行を表すことを docstring の契約に
  固定した。設計判断は {{D:lease-generation-marker-and-no-second-discriminator}}。
  全文と逐語・変異台帳は `output/insights/2026-09-04_t2148-lease-generation-semantics/README.md`。
- **段 2 plan の 4 提案を親が棄却した。** 必須 `lease_acquired: bool`、
  verifier 側の `expected_lease_acquired`、組を検査する helper と早期の重複検証、
  issuer CLI の専用 option と mutually-exclusive group である。予約語と 16 進は構文的に交わらず、
  既存の完全一致が 2 状態を既に区別するので、いずれも受理される受領証の集合も署名 bytes も
  変えない。段 3 レンズ A が「状態と期待値の両方を同じ caller が渡すので、bool を足しても
  取得の有無は照合されない」を示したため、棄却で失う保証も無い。
  **結果として公開関数の signature は 1 つも変わらず、既存 caller の呼び方も変わっていない。**
- **段 3 レンズ A の所見 5 は「対象そのものが消えた」。** 「必須 keyword 追加で壊れる caller
  9 箇所」は bool を採る前提の指摘で、棄却裁定によって前提が消滅した。誤りだったのではない。
- **段 3 の 2 レンズが親 brief の主張を 1 件狭めさせた。** brief と先行 wave の記録は
  「production consumer は存在しない」と書いていたが、字義どおりには誤りで、issuer 自身が
  署名 module を import する。言えるのは「待ち手と着地ツールからこの 2 module への配線が無く、
  tracked な着地ツールは v5 だけを受理する。repo 外の運用 copy は未測定」までである。
- **段 6 の must-fix 3 件はいずれも記録の訂正で、コード変更を要さなかった** ため fix 子は
  立てていない。内容は (1) T1 が M2・M3 の両方で赤になる過剰決定、(2) 上記の importer graph の
  誤り、(3) T5 が fixture・鍵経路へ到達しないことの明記である。
- **変異は 4/4 KILLED (baseline PASSED / 失敗 node 0 件)。ただし M2 と M3 は黒箱で分離できない。**
  `verify_signed_receipt_signature` が内部で `canonical_signed_payload_bytes` を呼ぶため、
  marker を expected として検証する経路は canonical 層を必ず通る。`DW-M03` に従い T1 は単独層
  証拠から外し、M3 の T3 の赤は診断文字列だけの差なので kill に数えない。**差し引くと M3 を
  単独で押さえるテストは存在しない。** 段 6 レビュー A の nit も記録した — T4 は実装を変更前へ
  全戻ししても緑なので marker 機構の実在証拠には数えられない (union を広げる M1 の防壁としては有効)。
- **段 5 の実装子が codex 上流障害で 2 回失敗した (23:54 / 23:57 JST)。** 症状は
  `backend-api/codex/responses` の websocket・HTTPS 両方の 404 である。同 wave の段 2 が
  22:11 JST に stderr 完全空で成功していたことを切り分けの根拠にし、13 分待った 3 回目
  (00:18 JST) が rc=0 で成功した。**親はコードを代筆していない** (D95 決定 3)。F391 へ再発として
  記録した。再投入は prompt 本文を変えず `--job-id` を明示して行った。
- **子は 7 本。** 段 2 plan 1、段 3 敵対相談 2、段 5 実装 3 (うち 2 本は上記の 404 で失敗)、
  段 6 レビュー 2。成功した子はいずれも `check_codex_output.py` rc=0。段 3・段 6 の子は
  codex sandbox の制約で pytest を実走できず、正しく静的検査だけと申告した。実装子も
  pytest が dispatch preflight の rc=16 で子未起動になったことを「実装済み・未実走」と申告し、
  plain runner の 22 passed を別扱いで報告した。
- **親の実測。** 変更前の焦点走 17 passed / rc=0 (計算ノード dispatch)、変異本走 4/4 KILLED、
  full provenance 監査 rc=0、受入全走。編集面重複は全 branch の三点 diff で 0 件
  (`campaign_lock.py` を編集中の並行 wave とは別面)。
- **隔離 worktree の背景 job から他 worktree の未 commit を再走査できない** ことが実測で分かった。
  bash guard が `git -C <他 worktree>` と git を含む loop を拒否する。branch 側は
  `git log --branches --not main --name-only -- <files>` の単一 command で全走できる。

## 次の一手差分

### 更新

- [T-2148] **P2・D1528 待ち**: 排他権の世代の意味論。粒度 (取得ごと) と非保持走行の値
  (`"not-acquired"`) は D1527 の裁定どおり確定し、signed-v6 の契約へ実装した。
  **残るのは取得あり世代の導出方式の採用**で、D1528 により鍵と発行権限の配置が済んだ後に
  改めて提示する。現状の値は取得あり・取得なしとも caller の自己申告であり、D1450 の実効的な
  再送防止 (同じ値を別の取得で再利用することの拒否) は達成していない。
  base: 3c9181ee4191d13cd9849ea0ec2e376c6d5c382746995f57462a3bbb1af53aed
