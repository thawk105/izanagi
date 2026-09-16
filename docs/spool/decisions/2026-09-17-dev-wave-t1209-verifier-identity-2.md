---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t1209-verifier-identity
seq: 2
---

## {{D:t126-code-identity-verifier-dsg-model-parse}}. T126 qualification の code identity へ verifier の dsg / model / parse を加える

**決定:**

1. **`REQUIRED_CODE_IDENTITY_PATHS` (orchestrator/qualification/contract.py) に `orchestrator/verifier/dsg.py` /
   `model.py` / `parse.py` を加え、37 path から 40 path にする。** 2026-08-17 /rulings 全件 第 5 回 #20 のユーザー裁定
   「含める」の実装である。verifier では従来 `core.py` だけを pin しており、serializability 判定の実体
   (dsg の cycle 検出、model の依存型、parse の trace 解釈) の変更が個別 code hash と driver
   (`t126_driver._identity_files()`) の disk / HEAD blob 照合の対象外だった。
2. **`series_identity()` の exact key set は 37-key 形から 40-key 形へ置換される。** 受理形は 1 形のままであり、
   受理形の増加ではない。検証ロジック、`schema_version`、hash domain、`REQUIRED_SCRIPT_IDENTITY_PATHS`、
   `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`、凍結 manifest は変えない。
3. **過去の qualification 成果物は歴史記録として据え置き、以後の取得から新 identity を適用する** (裁定の条件)。
   旧 37-key 形の series-identity を現行 code の verify (driver `verify` mode / collector の receipt 検証) に渡すと
   `contract.py` の `series identity code_identity required set mismatch` (ProtocolError) で invalid (driver CLI rc=2)
   になる。**bytes と当時の判定は保持されるが、現行契約への適合は失う。この不受理を過去の測定の無効化に
   使わない** (規律 7)。互換層・読み替えは作らない。実測範囲では tracked JSON に `code_identity` key を持つ
   成果物は 0 件で、live qualification は phase 3 の見送り台帳で scope 外 (repo 外の旧成果物の存在・利用は未確認)。
4. **独立の包含 test (`test_required_code_identity_includes_verifier_core_dsg_model_parse`) を置く。** verifier 4 file
   (core + 新 3) を production 集合から導出せず個別に assert する (T316 の `build_admission.py`、T529 の activation
   閉包 test と同型)。集合由来の既存 test (fixture・parameter・等価比較) は production 集合の誤削除に追随するため、
   これが無いと除去が緑のまま通る。repo 不変条件の test であって成果物の受理集合を変える gate ではない (D473 決定 4 と同じ位置づけ)。

**理由:**

- 「検証器の一部だけを見る同一性は主張を支えない」(裁定本文、規律 3 の面)。兄弟閉包 (campaign_lock、D442 / D473) は
  verifier 実装を既に束縛しており、D442 は「別閉包 (T126) は追随しない」と明記していた。本決定がその追随である。
- 純増だけで閉じるのが最小差分であり、壊れる committed 成果物が実測範囲に無い今が費用最小の窓である。
- superproject commit / tree は preimage に入っているため、commit された変更なら series identity は経由的に変わる。
  本決定が足すのは 3 file の**個別** code hash と disk / blob 照合であり、verifier 全閉包の完全な束縛と説明しない。

**却下した選択肢:**

- `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` も同時に加える — 裁定が名指すのは dsg / model / parse
  であり、依頼は「本題の identity 集合だけ」と限定した。pipeline.py の `from ..verifier import` (dispatch 面)、core.py の
  `result_to_dict` / `_domain_digest`、qualification/artifacts.py の `validate_live_receipt` がこの 3 file に依存し
  T126 の個別 code hash の対象外に残ることは事実として記録し、別件の裁定パッケージとして返す。
- 旧 37-key 形を読める互換層 / 二重受理 — 受理形を増やす向きであり、裁定の条件は「据え置き」であって「読み続ける」ではない。
- verifier package の census gate を T126 側にも新設する — 依頼の scope 外 (仮想リスク向けの gate・検査の追加)。
