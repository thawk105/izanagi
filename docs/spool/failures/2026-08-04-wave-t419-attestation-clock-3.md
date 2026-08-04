---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t419-attestation-clock
seq: 3
---

## 新規

### {{F:attestation-probe-observer-effect}}. attestation probe が自分自身の観測を汚し、全観測に帯外サンプルを焼き込んでいた [観測] [誤前提]

- 事象: Pegasus 由来の実効クロック観測は、**重複を除いた 23 の標本列すべて**が 2% 許容帯の外にある
  サンプルを 1〜2 個持つ。残る 46〜47 要素は例外なく厳密に 2101.0 MHz。帯外値は
  2951.7〜3096.5 MHz で、位置は毎回異なる (index 0, 1, 5, 6, 8, 10, 11, 24, 27, 28, 34, 38, 40, 43, 44 …)。
  内訳は `output/` 配下の JSON 成果物由来 21 と、実行時 observed 列 2
  (後者は F97 が記録した失敗 message に埋め込まれている)。
  出現回数では 24 だが、登録済み較正の標本列が attempt の複製と実行時 message の expected 列を
  合わせて 4 箇所に現れるため、相異なるのは 23 である。
- 根本原因: probe は `/proc/cpuinfo` の `cpu MHz` を論理 CPU 順に読む。**この読み取りを実行して
  いるプロセス自身が乗っているコアは、その瞬間 turbo にいる。** ログインノードで
  `/proc/cpuinfo` と `/proc/self/stat` の processor field を同時に採ると、6 回中 6 回、
  自分の走行 CPU が帯外側に現れた。位置が毎回変わるのはスケジューラの配置による。
  したがってこれは環境の異常ではなく**観測手続きが自分の観測対象を変えている** (規律 1 の型)。
- 影響: 較正 (expected) 側にも実行時 (observed) 側にも同じ効果が乗るため、
  **どちらを取り直しても「全要素が帯内」という述語は満たされない**。
  F97 が「登録済み較正が自分自身の述語を通らない」と記録した現象は、この効果が
  凍結成果物に焼き込まれた 1 事例である。
- 恒久対応: **未実施。** 是正方式 (K 回読んで論理 CPU ごとに最小値を採る /
  走行 CPU を記録して除外する) は受理集合と凍結 bytes に同時に触れるためユーザー裁定へ返した
  ({{D:effective-clock-self-consistency-gate}} 決定 (4))。**計算ノードでの因果は未立証**であり、
  走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した probe 実験が先行する。
  本 wave は緩和も迂回もしていない。
- 再発検知: 取得時の自己整合 gate (`effective-clock-self-comparison-failed`) が、
  同じ性質を持つ較正の新規登録を CLI publish 経路で拒否する。加えて契約 registry の
  全走査テストが、自己整合を満たさない entry の集合を既知例外 1 件と厳密に照合する。

### {{F:attestation-e2e-fixture-clamped-observation}}. E2E fixture が観測を帯内へクランプしており、実 probe が決して作れない観測で防壁を通していた [テスト代表性] [恒真ゲート]

- 事象: 実行時 attestation を通す E2E テストの probe fixture は、較正サンプルを
  `[median-delta, median+delta]` へ `min(max(...))` でクランプし、`tolerance_pct` を 100.0 に
  差し替えた観測を返していた。fixture 自身の docstring も「物理 Pegasus の実 attestation ではない」
  と書いていた。
- 根本原因: 実 probe が生成しうる観測の形 (必ず帯外要素を含む) を fixture が写さず、
  「通る観測」を合成して guard を通していた。そのため **E2E 経路は
  {{F:attestation-probe-observer-effect}} の型を構造的に検出できない**。
  同型の弱点は較正取得 CLI のテストにもあり、実 probe が返す `tolerance_pct=100.0`、
  48 標本、3 回の profile 取得を写していなかったため、
  CLI が渡す許容幅を定数へ固定化する変異が生存していた (段 6 の敵対レビューが摘出)。
- 恒久対応: 較正取得 CLI のテストを実 probe の形へ寄せ (`tolerance_pct=100.0`・48 標本・
  3 profile)、CLI 引数の許容幅が artifact へそのまま保存されることを 2 つの異なる値で pin した。
  registry 不変条件は合成ではなく**実登録 artifact** を入力に使う。
- 再発検知: 上記 pin を破る定数固定化を変異 matrix (`M07`) が撃つ。
  E2E fixture のクランプ自体は本 wave の変更面ではないため、**除去は未実施**であり
  裁定へ返した項目に含まれる。
