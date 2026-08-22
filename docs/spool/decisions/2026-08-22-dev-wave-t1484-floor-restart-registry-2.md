---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1484-floor-restart-registry
seq: 2
---

## {{D:t1484-floor-restart-registry-recommendation}}. 床値 (8b v1 freeze) crash 復帰救出経路は D510/§10.5 準拠の事前割当 registry を推奨し、実装形状はユーザー裁定へ返す

**決定:**

1. `docs/phase3-8b-restart-runbook.md` の R-5 (crash 復帰の再生成) が未決着としていた
   「D496 決定3 と旧 §9項8 のどちらが優先するか」は、D510 決定4 (2026-08-18) が
   「8b §9項8 の再走全拒否より D496 決定3 を優先する」と名指しして既に決着していると
   確認し、R-5 本文をその旨へ更新する。設計正本は `docs/phase3-8b-descriptor-design.md`
   §10.5 (同日付の再凍結で仕様化済み、freeze-wide の事前割当 attempt registry、消費範囲は
   落ちた構成の同じ反復に限定) とする。
2. `orchestrator/campaign/trial_registry.py` の公開契約 (schema version・path・
   `ARMS`/`HOLDOUTS`・`TrialManifest`) を非互換に変更して 8b へ転用することはしない。
3. 8b 側の実装形状 (専用の新規モジュール、または `trial_registry.py` の attempt 状態機械
   本体を共通 core として抽出し 8c 互換 facade + 8b adapter を作る形) は、本 wave の
   docs-only な scope では確定しない。共通 core 抽出案を軽い推奨として記録するが、
   実際の抽出コスト (8c consumer への影響範囲) は測っていないため、次のユーザー裁定へ
   返す。
4. 実装許可と正式測定の認可を分離する。8b 側の attempt registry 実装は
   `docs/phase3-8b-descriptor-design.md` §10.6 (epoch 境界) に妨げられないが、正式測定は
   8c 側の判定器・証拠契約・attempt registry・結果 judge が発効するまで認可しない
   (8c 側の `judge()` に production caller が存在しないため、この gate は当面閉じたまま)。
5. 実装着手前に次の4点を実装 wave の段1 brief で閉じることを要求する。(i) 上記3の
   reuse 形状の判断、(ii) 既存の `s8b_holdout_admission.py` 共有 root・claim・ledger
   との束縛 (どちらを master とするか)、(iii) 8b 自身の失敗分類を性能出力を読む前に
   確定させる trusted launcher 設計 (現行実装は `measure_fn` 実行後に分類しており
   D510 決定4 の要件を満たさない)、(iv) crash 点4 (観測開始後) の再抽選バイアスの扱い。

**理由:**

- D510 決定4 の文言は「8b §9項8」を明示的に名指ししており、これを別途の新しい裁定として
  再度ユーザーに諮る必要はない。一方で `trial_registry.py` の literal 流用が 8c ドメイン
  固定 (ARMS/HOLDOUTS/schema/acceptance) のため不可能なことは段2 codex plan・段3 敵対
  2レンズが独立に確認しており、8b 側に何らかの対応物は要る。
- 段3 敵対レンズ (整合性・実効性レンズ) が、attempt 状態機械の本体 (genesis/reserve/
  classify/observe/terminal/accept) がほぼドメイン非依存で 8c 固有部分より一桁以上
  大きいことを file:line で示し、「8b 専用に新規複製する」という当初の暫定判断が
  未検証のまま確定推奨にされかけていたと指摘した。この指摘は段1 brief・段2 plan の
  どちらも行っておらず、独立コンテキストでの敵対検証がなければ見落とされていた。
- 8b の失敗分類が性能出力を読んだ後に決まっている実装上の事実は、D510 決定4 (「分類は
  信頼側の起動器が性能出力を読む前に確定する」) と直接抵触する。これは絶対規律2
  (正しさゲートを緩める変異を許さない) に関わるため、実装 wave が着手前に必ず解く
  前提として明記する必要がある。

**却下した選択肢:**

- 旧 R-5 (c) (crash した campaign をその protocol/env で terminal と扱う、現状の実装
  挙動) — D496 決定3・D510 決定4 が明示的に否定した形であり不採用。
- `trial_registry.py` をそのまま (非互換な契約変更を伴って) 8b へ流用する — 8c ドメイン
  固定の schema/path/ARMS/HOLDOUTS/`TrialManifest` を壊し、8c の稼働中 consumer
  (`p3_autonomous_workload_trial.py` 等) を破壊しうるため不採用。
- 本 wave 内で実装形状 (専用複製 vs 共通 core 抽出) まで確定する — 実際の抽出コスト
  (8c consumer への影響範囲・テスト改修範囲) を測っておらず、本 wave は docs-only の
  技術確認 scope であるため、確定は次のユーザー裁定と実装 wave の段1 brief に委ねる。
