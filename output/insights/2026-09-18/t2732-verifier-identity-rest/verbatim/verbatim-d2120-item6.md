### 項 6 — T126 code identity へ verifier の残り 3 file を足す

対象: T-2732 (D2091 の却下欄)。

**決定:** `REQUIRED_CODE_IDENTITY_PATHS` に `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を
加える (40 → 43 path、択 (a))。D2091 と同じ条件 — 純増、受理形は 1 形のまま key set 置換、過去の qualification
成果物は歴史記録として据え置き、互換層・二重受理は作らない、独立の包含 test を置く。

**理由・採らない案:** 3 file は pipeline の dispatch 面、`result_to_dict` / `_domain_digest`、`validate_live_receipt` に
依存され、個別 code hash と disk / blob 照合の対象外に残る (superproject の commit / tree と D473 の loader 閉包では
束縛済み)。commit 済み成果物に `code_identity` key を持つものが 0 件の今が費用最小の窓。(b) 足さない + 限界明記は、
後で足すほど旧成果物の再受理問題が増える。
