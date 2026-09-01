---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2139-b4-certified-connection
seq: 1
title: [T-2139] B-4 材料レポートと certified 選択の接続は今は実装できないと確定し、再開条件を固定する (docs のみ、branch worktree-dev-wave-t2139-b4-certified-connection、実装面の差分ゼロ)
---

## 本文

- 一次資料は `output/insights/2026-09-01_t2139-b4-certified-selection-connection/`。
  段 1〜4 の逐語を置いた。裁定は {{D:b4-report-to-selection-deferred}}。
- **実装面の差分はゼロである。** production / test code を 1 行も足していない。
  したがって変異 matrix は `DW-S04` により免除。受入全走は免除せず実走した。
- **段 3 の 2 レーンが独立に同じ blocker を出し、ユーザー指示で相談した Codex も同じ結論に達した。**
  起草した設計は「B-4 材料レポートの厳格な非認証 validator」としては成立するが、
  **certified-selection connection ではない**。呼び出し元・実 artifact・耐久参照が無く、
  実装しても certified 選択の受理集合・材料レポート・台帳は 1 bit も変わらない。
- **親の provisional 裁定が 1 件、段 2 で実測により覆った。** brief は接続を
  `verify_repository_preregistration_contract()` の受領証へ束縛する案を暫定裁定にしていたが、
  同受領証が検証するのは事前登録 §5.1.1 と source closure であって **§5 の発効状態ではない**。
  §5 の表は 11 欄中 9 欄が未記入のままである。呼び出す必要自体が無いと裁定し直した。
- **親の一般化が 2 件、広すぎた。** どちらも子の指摘を親が実物で確認して訂正した。
  (i)「到達可能な分析 verdict は 1 つだけ」→ 正しくは**材料レポートの正規コマンドに限れば** 1 つ。
  分析経路そのものは妥当な floor を渡せば `established` へ到達する。
  (ii)「certified 側の受け口はすべて構造的に閉じている」→ 閉じているのは Layer3 の正方向だけで、
  D1236 の WAL COMMIT 合流点にある支配点は**実際に発火する**。ただし材料レポートより前の
  sink なので接続先にはならない。
- **段 1 で引数の前提 1 件が覆った。** 引数は稼働中の [T-1769] が編集面を占有していると
  述べていたが、対応する branch・worktree・worklog entry はいずれも 0 件だった
  (T-1769 の成果物自体は着地済み)。実際に占有していたのは別 wave で、
  `p3_b4_admission_record.py` / `p3_b4_closed_critic.py` / `p3_b4_launcher.py` /
  `p3_b4_wiring_probe.py` とその test だった。本 wave はこれらを 1 file も編集していない。
- **受入 1 回目が非帰属の理由で落ちた。** 停止段は `merge-history-provenance` で、
  原因は wave の作業木が base で止まっており、その checker が main 側で新しく登録された
  既知違反 data を「index-only member does not match HEAD」と誤認したことである。
  実装差分とは無関係。`DW-O20` に従い `--ff-only` で HEAD を揃えてから再走した。
- 子は Codex `gpt-5.6-sol` / `reasoning=xhigh` を plan 1、consult 2、
  consult (裁定相談) 1 の計 4 本。全件 `check_codex_output.py` rc=0。
  すべて `sandbox=read-only` で pytest を実走していない。**子の未実走を緑と記録していない。**
- 正式 B-4 実走、qsub、性能測定、build は行っていない。
  事前登録文書と材料レポートの wire は 1 byte も変えていない。

## 次の一手差分

### 更新

- [T-2139] **P3・見送り (再開条件つき)**: B-4 材料レポートと certified 選択の接続。
  現 checkout では完成できないと実測で確定した ({{D:b4-report-to-selection-deferred}})。
  再開条件は次の論理積 — (1) 実物の材料レポートの安定した所在または計測 ID、
  (2) レポート生成後の正規呼び出し元と持ち主、(3) 耐久化した判定の保存先と sink からの参照、
  (4) 順方向を含める場合のみ floor 発効と発行可能な approval authority。
  起草した設計は却下案として `output/insights/2026-09-01_t2139-b4-certified-selection-connection/`
  に凍結してあり、そのまま実装する案ではない。
  base: 80ffbf5d3dcaccd943b7ceede0a99373d470c8cd4448149bd560543eee1366fe
