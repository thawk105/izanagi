---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-freeze-chain-hold
seq: 2
---

## 新規

### {{F:hold-target-colocated-with-correctness-gate}}. 保留対象の bytes/pin 検査と、保留してはならない測定公正・admission・防壁が同じ関数に同居していた [恒真ゲート] [テスト代表性]

- 事象: 凍結チェーン検証の恒久保留を関数単位で行おうとしたところ、保留対象の同一性検査と、
  裁定が明示的に対象外とした検査が**同じ関数の数行違いに同居**していた。異なる 4 モジュールで
  独立に 5 件。関数まるごと保留すれば、いずれも黙って消えていた。
  - `orchestrator/campaign/s8b_holdout_freeze.py` — 保留対象 `_verify_source`/`_verify_head`
    (`:874-877`) の直後 `:879-880` が **holdout 漏洩検出器 + rr50 陽性対照**、`:865` が
    **未承認世代の admission 拒否**、`:974-978` が **`variant_binding` 再導出** (測定対象構成の
    取り違え防止)。
  - `orchestrator/campaign/s1_known_axes_freeze.py` — 保留対象 `:863-879` の手前 `:859`
    (実体 `:677-707`) が **`system_gate` と `ident_all` の flags 同一性** = S-1b の比較公正。
  - `orchestrator/tests/test_frozen_artifacts.py:125-136` — **23 件を 1 loop で検査**し、
    その中に selector prediction・journal・payload・envelope・raw response の**盲検封印 14 件**
    (`:57-84`) が含まれる。ファイル自身が `:31-32` でこれを「盲検封印」と定義している。
    保留すれば oracle 結果を見た後に予測と根拠を整合的に差し替えられる。
  - `orchestrator/campaign/t080_freeze_migration.py:2169-2268` の `verify_receipt` —
    receipt bytes/履歴と同時に陽性対照 (`:2219-2221`)・**holdout live leak scan** (`:2222-2226`)・
    **live ccbench identity** (`:2227-2230`)・**known schema と S-1b pairing** (`:2231-2237`) を実行。
    同じ検査が official adapter (`:2321-2332`) にも重複。
- 根本原因: 裁定が対象を**機構名**で与え (「凍結チェーン検証」)、実装者がそれを**関数**へ写像した。
  検査の粒度は行であって関数ではないのに、保留の粒度を関数で取った。同居は設計の不備ではなく
  **正常な凝集** — 同じ document を 1 回読んで複数の性質を検査するのは自然であり、今後も起きる。
- 恒久対応: `DW-O09` の pin 閉包列挙と同じ扱いで、**保留を導入する wave は「保留する行の前後を
  関数境界まで目視し、対象外の検査が同居していないか」を段 4 の裁定項目にする**。
  機械側は t816 wave が導入する **held marker の stderr 出力 + `check_id` の閉じた値域**
  (集合外は fail-closed) が、保留した検査点の実集合を走行ごとに可視化する。
  可視性が唯一の防波堤である以上、marker が届かない経路 (CLI subprocess・xdist worker) を
  残さないことが対応の一部である。
- 再発検知: 保留を伴う wave の敵対レビューに「保留対象と対象外が同じ関数に同居していないか」を
  必須レンズとして置く。本件は段 3 の read-only 敵対子 1 本 (正しさ境界レンズ) が 5 件すべてを
  静的検査だけで捕捉した。親の brief と段 2 プランはどちらも見落としていた。
