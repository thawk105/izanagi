# 段 6 所見の裁定と fix1 (2026-09-30 16:55 JST)

入力: s6-review-a.md (レンズ A 正しさ・実効性、astra・ultra、accepted)、s6-review-b.md (レンズ B 過剰・削除、astra・ultra、accepted)。

| ID | 判定 | 採否 | 扱い |
|---|---|---|---|
| RB-1 L1.5 増枠は不要 (must-fix) | real | 採用 | 親が DW-O01 完了判定文・DW-O05・DW-S05-B を意味を保って縮約 (4af3c92b2)。一時変異 (予算 9_696) で check_docs 違反なしを実測。予算定数とテスト pin 6 箇所の復元は Codex fix1 (単位 A)。RB-1 の DW-O05 案は「親の義務」を「prompt に書く文」へ移す意味変更なので不採用、親が別の縮約を当てた |
| RA-1 / RB-2 rulings の DW-S03 参照 (should) | real | 採用 | 4af3c92b2 で追加、「次の順で収集」→「順に収集」で 5,623 bytes (上限ちょうど) |
| RA-2 所要台帳の新 node 10 件 (nit) | real | 不採用 (nit) | 受入実走の所要で台帳を更新する既存運用に任せる。未実測値は書かない |

所見ゼロではないが、レビューは「委任拒否の素通り・恒真化なし」「V1〜V5 互換・consumer 形式破壊なし」「過去 receipt 4,038 件に反転対象 0 件」を静的に確認。

## 変異と焦点走の扱い (依頼「計算ノードは使わない」との衝突)

- `tools/mutation_harness.py --runner-mode local` は Pegasus login で拒否 (`_refusing_local_site`)、login での直接 pytest は `hooks/guard_bash.py` が
  「baseline 重量対象 (pytest)」として拒否する。login で変異を走らせる sanctioned な経路は無く、dispatch は計算ノードを使う。
- 裁定: 依頼 (ユーザーの直接指示) を優先し、**変異 matrix は本 wave では未実施**。事前登録 (s4-ruling.md、mutation/spec-probe.json) と注入位置の一意性確認
  (m1〜m7 すべて置換元 1 件) までを記録し、報告冒頭に未実施と理由を書く。変異を回すなら計算ノードへの dispatch が要る (所要は未見積り)、と提案する。
- 段 5 統合後の焦点走 (focus-s5) と失敗 node の再走 (rerun-r1) は bash script 経由の直接 pytest で、guard_bash の login 重量検査をすり抜けていた
  (直接打った同種コマンドは guard が拒否して判明)。結果 (103 失敗 → repo 外 TMPDIR・低並列の再走で 102 緑、残る 1 件
  `test_campaign.py::test_layout_rejects_path_traversal` は変更面と無関係な output_root 偽赤) は参考値に留め、正式な検証は受入全走
  (明示 shard 3、login で走る sanctioned 経路) に寄せる。すり抜けは段 8 の改善候補 (防壁の穴) として扱う。
