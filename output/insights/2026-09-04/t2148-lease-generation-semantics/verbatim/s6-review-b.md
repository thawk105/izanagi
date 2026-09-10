## must-fix

1. **対象:** `orchestrator/tests/test_external_acceptance_signing.py:294-319`  
   **何が問題か:** T1 は M2 と M3 の両方で赤になるため、`s4-ruling.md:128-129` の定義どおり、単独変異の層別証拠としては過剰決定された冗長 gate である。さらに M2 は T2 の fixture 構築でも赤になり、M3 による T3 の赤はエラー文だけの差である。  
   **放置時の成果物影響:** 試行台帳が canonical 検査と expected 検査を独立に検出したと誤記し、M2/M3 の kill-node 集合と証拠分類が不正確になる。  
   **修正の向き:** 新しい gate は足さず、実測では全 raw red node を記録し、T1 を M2/M3 の単独層証拠から除外し、T3 の診断文字列だけの赤を kill に数えない。

2. **対象:** `s5-author-report.md:29-35`  
   **何が問題か:** 「両者の repo 内 importer は当該 test file のみ」は誤り。署名 module は `acceptance_issuer_reference.py:67-89` からも import され、issuer 自身が `:524` で verifier を呼ぶ。  
   **放置時の成果物影響:** 材料レポートの repo 内依存・波及範囲から issuer→signature の辺が欠落する。  
   **修正の向き:** 「署名 module の importer は issuer と test、issuer の importer は test。waiter/lander への配線はなく、tracked lander は v5 のみ、repo 外 copy は未測定」と訂正する。

3. **対象:** `s5-author-report.md:16`  
   **何が問題か:** T1〜T5 全体が実 fixture・実 Ed25519 鍵を使うように読めるが、T5 は parser と issuer の入力検査で終了し、fixture の projection や鍵の読取り・署名には到達しない。  
   **放置時の成果物影響:** 材料レポートが T5 の検出力を暗号・fixture 経路の実証として過大計上する。  
   **修正の向き:** T1〜T4 の fixture/鍵経路と、T5 の parser/issuer 入力検査を分けて記述する。

## nit

無し。

## 変異 M1〜M4 の期待 node の予想

- **M1**
  - `test_unreserved_non_sha_lease_generation_is_rejected_on_all_paths`
  - `test_reference_issuer_accepts_only_reserved_not_acquired_marker`
  - issuer も同じ helper を使うため、T4 だけでなく T5 の `"none"` 側も赤になる。

- **M2**
  - `test_not_acquired_marker_is_signed_and_exact_context_passes`
  - `test_not_acquired_receipt_is_rejected_for_acquired_expected_context`
  - 後者は対象の context 比較ではなく、`_signed_control()` の canonicalization 中に赤になる。

- **M3**
  - `test_not_acquired_marker_is_signed_and_exact_context_passes`
  - `test_acquired_receipt_is_rejected_for_not_acquired_expected_context`
  - 後者は `context mismatch` が `invalid expected_lease_generation` に変わるだけなので、DWM03 上は kill に数えない。T1 は M2 と共有され、単独層証拠から除外対象。

- **M4**
  - `test_reference_issuer_accepts_only_reserved_not_acquired_marker`
  - marker が `launcher log path must be absolute` まで到達せず、`invalid lease_generation` になる。ほかの追加 node は赤にならない予想。

## 正しく実装されていた点

- D1527 と整合する。64 桁小文字 hex を取得ごとの値、厳密な `"not-acquired"` を非取得走行の値として union 化している。
- D1528 と整合する。64 桁値は「SHA-256-shaped」としか規定せず、live lease や特定候補から導出する方式を実装していない。世代の導出方式を選んでいないと言える。
- D1499 と整合する。marker は必須引数・既存の required CLI optionへの明示入力であり、暗黙の既定値ではない。自己申告で取得を証明しないことも明記されている。
- D1450 に対しては、`acceptance_receipt_signature.py:381` の完全一致が異なる申告世代を区別する。ただし一意性や再利用禁止は強制せず、docstring も「再送を防ぐ」とは主張していない。
- D1443 の縮退は `acceptance_receipt_signature.py:18-22` に明記されている。取得を検査せず、marker は caller 申告との一致だけで、production landing gate は不可避でない。
- 棄却された bool discriminator、expected bool、pair gate、新 CLI option、mutually-exclusive group は入っていない。テスト helper の既定値 `:119` は以前の固定 fixture 値を引数化しただけで、production の暗黙既定値ではない。
- 追加テストの検出行は次のとおり。
  - T1: `acceptance_receipt_signature.py:202,229,368` の marker 対応のいずれかを SHA-only に戻すと赤。
  - T2/T3: `:381` の lease-generation 比較を外すと赤。
  - T4: helper の marker 枝 `:143`、および三経路の呼出し `:202,229,368` を各々壊すと対応する subcase が赤。
  - T5: `acceptance_issuer_reference.py:465` を SHA-only に戻すと赤。
  - 実装行を一つも検出しない追加 test はない。
- 成果物への実質的変更は、署名 module/reference issuer の受理集合に厳密な `"not-acquired"` payload が加わること。取得ありの canonical pin、certified 選択結果、production landing の受理集合は変わらない。
- 完了報告は pytest を緑と偽記していない。pytest は子未起動、plain runner は別物として明確に区別されている。

## 総括

コード上の契約と scope は D1527/D1528/D1499/D1450/D1443 に整合し、production 関門や再送防止を過剰主張していない。  
最も重い所見は、T1 が M2/M3 共通の冗長な層別 gateとなり、変異証拠を独立に帰属できない点である。  
親は M1で T4+T5、M2で T1+T2、M3で T1+T3、M4で T5 が赤になるかを実測し、診断文字列だけの赤を除外すべきである。  
加えて author report の importer graph と T5 の証拠水準を訂正する必要がある。  
このレビューではテストを実走していない。