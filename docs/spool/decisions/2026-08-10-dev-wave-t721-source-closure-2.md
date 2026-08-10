---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t721-source-closure
seq: 2
---

## {{D:enforcement-source-closure}}. source closure を enforcement 閉包 8 path へ広げ、名乗りを「ident を通った呼出し」に限定する

**決定:**

1. **閉包を exact 8 path にする。** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` へ
   `execution_guard.py` / `loop.py` / `pipeline.py` / `wal.py` / `ident.py` /
   `artifact_admission.py` を加える。D259 決定 2 の「exact 2 path」を supersede する。
   検証の意味論 (記録 commit の blob と現在の disk bytes の一致であって current HEAD との
   一致ではない)、停止点 (`ident.ensure_campaign_identity` の 1 点)、fail-closed は変えない。
2. **識別子と wire key は変えない。** `contract_loader_*` は歴史的名称として残し、値が
   enforcement 閉包であることを定数直前・class docstring・本決定に書く。改名は成果物形式の
   別変更であり、本決定の範囲ではない。
3. **共有 v2 fixture は記録 commit の blob digest から作る (test-only)。** production の
   `capture_contract_loader_binding` / `verify_live_*` / `verify_committed_*` は変えない。
   閉包メンバーに未 commit 差分があるだけで fixture 生成が落ち、gate を検査していない
   16 の consumer が偽の赤になるためである (実測: clean 16 passed → dirty 6 failed、
   赤 6 件すべて fixture 生成側)。production の呼出し口 4 口は census テストで固定する。

**名乗ってよい範囲 (これを超えて書いてはならない):**

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
> 実際に完了した呼出しについて、**検査が読み取った時点の** enforcement source closure 8 path の
> disk bytes は、その呼出しが authority に採用した `contract_loader_commit` の同 path Git blob と
> 一致した。

- **「certified 経路が source-bound」とは名乗らない。** 閉包は推移的に閉じていない。
  `pipeline.py` は verifier / calibrator / buildcache / build_admission / source_digest へ、
  `execution_guard.py` は env_attestation / site_policy へ判定を委譲しており、いずれも閉包外である。
- **「ensure 成功時点で一致」とは名乗らない。** capture から lock 獲得までの間に再検査はなく、
  保証は「検査が読み取った bytes」までである。
- **停止点は certified sink の支配点ではない。** `pipeline.evaluate` と低層 WAL writer は
  ident を通さずに書け、S8b oracle driver が実在の別経路である。
- **admission 時点の disk 一致は保証しない。** admission は記録 commit の blob と記録 digest
  だけを照合し、working tree を読まない。これは意図した設計であり、正例テストで固定した。
- **in-process 改変・`__pycache__`・動的生成コード・成果物 bytes の改竄は検出しない。**
- **未束縛 bootstrap** = `campaign_lock.py`、`contract_loader_binding.py`、Git executable、
  既ロードの Python state。これらは閉包に入れない (検証器自身を自分で検証させないため) 。
  accidental drift のモデルでは受容できるが、敵対モデルでは root of trust である。

**受理集合の変化:**

- 既存 artifact は不変。`output/**/campaign.lock` は 32 本すべて v1 で、v2 は 0 本である。
- v2 wire の受理言語は exact-2 key から **exact-8 key への置換**であって、部分集合化ではない。
  旧 exact-2 map は拒否になり、exact-8 map は受理になる。
- 閉包 8 path のいずれかに未 commit 差分がある working tree からの certified 実行は、
  新規作成・resume とも `ident` の停止点で拒否される。これが本決定の目的である。

**却下した選択肢:**

- **`contract_loader_*` の改名。** v2 lock が 0 本の現在はコスト最小の窓だが、裁定は閉包拡張で
  あって wire 形式の変更ではない。敵対レビュー 2 本のうち 1 本は改名を推し、1 本は
  correctness hole ではないと判定した。窓の非対称性は裁定パッケージへ回した。
- **qualification の既存 exact set への統合。** 裁定で採られていない選択肢であり、
  campaign 側と qualification 側は別目的の別集合として残す。
- **共有 fixture の合成 digest 化。** 実 blob を読まない fixture は、記録 digest の実在を
  検査しなくなる。記録 commit の実 blob を読む形にした。
- **全 certified sink への gate receipt 導入。** 承認範囲外の受理集合変更であり、別 wave とする。
