---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2810-g1-launch-validation
seq: 2
---

## {{D:g1-launch-validator-current-shape}}. 凍結 v2 g1 の launch validator の受理集合を official 成果物の現物形へ広げる — journal は binding 2 形と `reservation-preflight` (任意・高々 1 件・campaign 前)、段階 6 lineage は「各 artifact の一意・非 merge 導入 i について C ≤ i ≤ G」と「G 自身が追加した世代文書 1 file の導入 == {G}」とし、policy 照合・scan 除外・cert 条件は変えない

**決定:**
1. `s8b_ratified_freeze._JOURNAL_KEYS` に `reservation-preflight` (producer `s8b_floor_campaign.py` の 10 key) を足し、`reservation-preflight` と `campaign-start`
   にだけ binding 2 key (`pbs_jobid` / `submission_nonce`) を optional に許す。受理形は (a) binding 無し campaign + binding 無し reservation 1 件 (campaign 前)、
   (b) binding 付き campaign + 同値 binding 付き reservation 1 件 (campaign 前) の 2 形だけ。片側 claim・値不一致・key 片欠け・型不正 (binding は非空 str、
   reservation の 7 数値 field は int > 0 で bool 拒否、`formula` 非空 str、`shared_dependency_prebuild` bool)・reservation 2 件以上・campaign 後の reservation・
   他 event への binding key は拒否する。binding は記録内の整合情報であり PBS job の外部認証ではない。
2. `_launch_validate` 段階 6 の「result / measurement_closure の導入集合 == {G}」を、各 path の一意 (`_unique_introduction`)・非 merge 導入 i について
   「cert C が i の祖先か同一」かつ「i が G の祖先か同一」(DAG 上の祖先関係) へ改める。上限 i ≤ G は段階 3 の G-tree 実在検査と一意導入から従う
   重複検査で独立保証に数えない。cert C の条件 (一意導入・非 merge・C < G 厳密) は不変。
3. G 偽装の検出は、G (`ratified.generation_commit`) 自身が追加した path (`_added_paths`) のうち世代文書形 (`_GEN_RE`) がちょうど 1 つあり、その導入集合が {G} で
   あることで保つ (cause `generation-introduction`)。path を `generation_number` から引かない (段 4 追補 1)。
4. `test_s8b_oracle_driver._ACTIVATED_G1_REFUSALS` (実 repo を root にする held 6 node の真値) は、ccbench pin 前進 (D2184) 後の live P3 実測値
   (layer-2 hit + `manifest-invalid` の policy 照合) へ更新する。pin 前進の統合時に本来追随すべきだった期待値の補完であり、成功条件の緩和ではない。
5. 本 wave の効能は「validator の互換性修復」と「新 main の historical reverify (`reverify_published_freeze`) が段階 4〜7 を通過して段階 8 に到達すること」に
   限る。live 経路は段階 4 の現行 policy 照合で拒否のまま (D2184、移行は T-2812 系)、historical は段階 8 で未発効候補文書
   `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` の scan hit で失敗のまま。候補文書の扱い (削除 commit を第一候補とする) は別裁定とし、本 wave は
   scan 除外を広げない。

**理由:**
- official run の journal は producer の設計どおり `reservation-preflight` と PBS binding を持ち、validator の allowlist だけが追随していなかった (決定台帳 25569 行付近の
  allowlist 方式の設計)。現物形に合わせるのは受理集合の最小の拡張で、producer が書き得る 2 形以外は拒否のまま。
- 現物 topology は cert C = result 導入 = X1' = G^ (D2077 の一方向順序 result → 候補 → G の帰結) で、旧条件は構造的に満たせない。区間受理 [C, G] は
  現物と既存 fixture (i = G) を同じ述語で受理し、下限・一意・非 merge を追加の制約として残す。相談 2 本 (`sol` / `luna`) は α を条件付きで支持し、条件
  (上限の重複性の明記、受理集合の一般化の明示、効能の限定、`reservation-preflight` の件数・順序) はすべて採用した。
- 世代文書 path を `generation_number` から引くと、`generation_number` だけを射影する既存 test (scope 以外の gate が全 green であることを pin する) と衝突する
  (焦点走 1 の赤 1 件)。G 自身の追加 path から引けば、G 偽装 (A を G と申告) は approval record が世代文書形でないため 0 個で拒否でき、既存の
  reason / cause と負例の期待を変えずに済む。

**却下した選択肢:**
- β (G を result と同 commit で作り直す) — D2120 項 2 (b) の再裁定が要り、G / A / X の参照へ波及する。
- γ (floor_source へ導入条件を課さない) — 同じ残存条件の下で受理集合を最も広げる。
- δ (`i == frozen_at_head` に束縛) — 独立 fixture の `frozen_at_head` は v1 由来で launch core は V1a を検査しないため fixture の全面変更が要り、D2077 が要求しない
  保証 (全 closure の初導入 = captured HEAD) を課し、measurement_closure が別 commit で導入される将来形を排除する。
- binding 必須 (official は PBS 下でのみ走る) — producer が `external_checkpoint_binding` 無しでも書き得る形を validator が拒否することになり、fixture 全更新が要る。
- 段階 6 で `resolve_active_generation` を呼ぶ — 段階 7 と二重で、段階 6 の H-pure な独立性 (resolver の結果を使わない) を崩す。
- 世代文書 {G} 検査を外して既存負例の期待 cause を段階 7 のものへ変える — 既存 test の期待値を変える。
- policy 照合の除去・live 経路への `expected_policy=None`・候補文書の exemption 追加 — D2184 / D2120 項 2 (a) が却下済み (規律 2)。
