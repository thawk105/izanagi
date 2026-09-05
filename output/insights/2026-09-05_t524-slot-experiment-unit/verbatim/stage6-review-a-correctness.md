## 所見

- **blocker** — legacy schema が新検査の迂回路になっています。[s8c_acceptance_receipt.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:733) は v1〜v5 を受理しますが、attempt registry 検査は v5 にしか適用されません。[s8c_acceptance_receipt.py:1796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1796) `require_current_verified_receipt` にも schema-current 条件はありません。[s8c_acceptance_receipt.py:1809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1809) 実際、追加テスト自身が v5 から attempt fields を除いて v4 に変えた receipt を `VerifiedAcceptanceReceipt` にしています。[test_s8c_acceptance_receipt_v2.py:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1112)
  放置時の成果物影響: 下流の verified receipt 集合に「全 slot 消費の証拠を一切持たない v1〜v4」が残り、レポートや台帳が旧 schema を選ぶだけで D1269 の保証を失います。

- **blocker** — v5 verifier は registry の自己整合性を見るだけで、それが結果観測前に外側 receipt の manifest/P に固定された genesis かを証明していません。genesis と event には manifest hash/path と P/C が存在しますが、[s8c_acceptance_receipt.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:113)、core loader へ expected binding を渡さず、外側との比較は slot projection と trial tuple だけです。[s8c_acceptance_receipt.py:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1536) [s8c_acceptance_receipt.py:1544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1544) さらに履歴検査は最初の blob が genesis-only だったことを要求しないため、完成済み registry を最初の commit で導入しても通ります。[s8c_acceptance_receipt.py:1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1627) issuer 側には P 時点の initial blob を照合する既存 gate があります。[trial_registry.py:3555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:3555)
  放置時の成果物影響: 結果を見た後で選択した六件から registry と receipt を同時作成したり、別 manifest の registry を外側 receipt に結合したりでき、verified レポート集合と参照先が事前宣言から変わります。

- **must-fix** — downstream verifier の attempt 履歴検査は現在の `HEAD` ancestry しか見ず、同一 repository の別 ref にある第二 root や alternate-path root を検出しません。[s8c_acceptance_receipt.py:1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1627) issuer の既存検査は明示的に `rev-list --all` と全 tree path を検査しています。[trial_registry.py:2586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:2586) [trial_registry.py:2599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:2599) [trial_registry.py:2626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:2626)
  放置時の成果物影響: 同一 repo の複数 ref で別々の slot 組を走らせ、良い側を checkout すると、その側の receipt とレポートだけを verified な参照として下流へ渡せます。

- **nit** — originless 比較では attempt prefix SHA だけを揮発化しています。[test_reflux_originless_compatibility.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/tests/test_reflux_originless_compatibility.py:205) 同じ prefix には桁数が変わり得る PID、starttime、時刻が入るため、`attempt_registry_prefix_bytes` も実行間で変わり得ます。[s8c_acceptance_receipt.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:122) lifecycle の byte count は既に同理由で揮発扱いです。[test_reflux_originless_compatibility.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/tests/test_reflux_originless_compatibility.py:198) 成果物の受理境界ではなく、deterministic-control の偶発的な赤になり得る点です。

## 揮発分類の判定

**正しい。**

`attempt_registry_prefix_sha256` は start/classification/terminal の時刻、process identity、report digest を推移的に含むため、等価な再構築でも値が変わります。[s8c_acceptance_receipt.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:122) [s8c_acceptance_receipt.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:133) [s8c_acceptance_receipt.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:145)

これはテスト比較上の揮発分類に限られ、production verifier は指定 prefix の SHA を現物から再計算して exact 一致を要求しています。[s8c_acceptance_receipt.py:1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1451) [s8c_acceptance_receipt.py:1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:1529) したがって SHA の揮発化自体は検査穴ではありません。ただし上記 nit のとおり byte count も同様に揮発します。

## 受理集合は広がっていないか

広がっています。

- v5 を追加しながら v1〜v4 も同じ sealed verified capability に到達できるため、実効受理集合は狭まっていません。
- v5 内でも、P 時点の genesis 固定を欠く完成済み後付け registry と、同一 repo の別 ref に第二 root がある状態を受理します。
- 一方、attempt schema v3 の単一 generation、legacy field 排他、明示 schema map、generation の capability digest 束縛には拡大を認めません。[attempt_registry_core.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/attempt_registry_core.py:733) [attempt_registry_core.py:751](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/attempt_registry_core.py:751) [trial_registry.py:2112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:2112) [trial_registry.py:2082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/trial_registry.py:2082)
- `replicate_index>0` も receipt projection で拒否されており、この面の拡大はありません。[s8c_acceptance_receipt.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t524-slot-experiment-unit/orchestrator/campaign/s8c_acceptance_receipt.py:634)

## 段 4 裁定からの逸脱

- 「下流が独立に検査する」という主目的から逸脱しています。v5 分岐自体は発火しますが、legacy downgrade と事前固定未証明により不可避な gate になっていません。[ruling-stage4.md:48](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t524-slot-experiment-unit/ruling-stage4.md:48)
- 「同一 repository の best-of-N は閉じている」という採用前提を、下流 verifier の `HEAD` 限定履歴検査が維持していません。[ruling-stage4.md:18](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t524-slot-experiment-unit/ruling-stage4.md:18)
- §3(c) で作らないとした production producer、全世代台帳、人間承認 authority、性能値分岐などの混入はありません。

## 総括

M1/M2 の generation 境界、空集合拒否、series key 据え置きは正しく実装されています。  
M3 の v5 分岐も dead code ではなく、issuer の v5 出力から到達します。  
`retryable-failure` は core 上で中間状態に留まり、測定後の失敗を捨てる受理経路は見つかりませんでした。  
揮発 SHA の分類と production 側の exact digest 照合も正しいです。  
ただし legacy downgrade、事前固定未証明、同一 repo 別 ref の三経路により、D1269 の下流保証は成立していません。  
結論は **blocker あり** です。