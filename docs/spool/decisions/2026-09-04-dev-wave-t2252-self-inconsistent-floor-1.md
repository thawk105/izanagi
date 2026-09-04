---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2252-self-inconsistent-floor
seq: 1
---

## {{D:self-inconsistent-floor-series-exclusion}}. 自己整合しない較正の除外は系列単位で行い、宣言は層 3 に閉じる

**決定:** D1537 の実装は次の 3 点で固定する。

1. **除外の単位は環境系列である。** 有効な契約が pin する較正の `(path, sha256)` が宣言集合に
   完全一致する campaign では、within-run の候補形成を行わない。pin 由来だけでなく直下 record 由来も
   候補にしない。between-run は変えない。
2. **宣言は層 3 (`orchestrator/campaign/layer3_report.py`) の module 定数に閉じる。** 較正検証の
   共有 leaf や環境契約 module へは置かない。`orchestrator/tests/test_env_contract.py` の既知例外集合は
   独立 oracle として据え置き、層 3 側のテストが宣言集合と「登録簿の required 世代のうち実 bytes で
   自己比較に落ちる集合」の一致を実述語で検査する。
3. **除外は bytes 検証の後に行い、status 値を増やさない。** `_validated_pin_path` の SHA / directory /
   通常 file の fail-closed と `pin-file-missing` は従来どおり先に確定し、pin file が無くても契約の ref が
   宣言集合に入れば除外する。理由は within-run の search 詳細に固定文字列の key 1 つで残す。

**理由:**
- pin の path 1 本だけを除外すると、同 bytes の直下 copy が別名で置かれた場合に一致が戻り、
  「一致候補 2 件で重複エラー」だった campaign が「直下 1 件の新規一致」へ転じる受理拡大も起きる。
  D1537 の主語は path でなく当該環境系列である。
- 共有 leaf に置く frozenset は新しい production の例外台帳になり、材料レポートが記録する generator
  hash (`layer3_report.py` 自身) に束縛されない。較正検証 leaf は silo ladder の runtime binding と
  T-126 の code identity 閉包に入るため、無関係な identity も動かす。
- 「発効を待つ」状態を status 値に書くと、健全な世代が発効した後も authority が不変の歴史的 lock に
  対して語義が古くなる。理由 key は世代の状態を言わない。
- 宣言参照は「authority が解決した identity を裁定済み集合と比較する」ことであり、samples / tolerance を
  読んで述語を再実行する「再検査の関門」(D1537 却下肢) ではない。

**却下した選択肢:**
- pin の path 単位の除外 — 直下 copy で破れる。
- 較正検証 leaf への共有 frozenset — 例外台帳の新設に当たり、generator hash に束縛されない。
- 新 status 値 `self-inconsistent-awaiting-healthy-generation` — 裁定が要求せず、発効後に語義が古くなる。
- 検証前の除外 — SHA 不一致等の fail-closed を隠す。
