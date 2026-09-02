---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2187-adaptive-3const
seq: 1
---

## 新規

### {{F:mutation-wrapper-observes-shared-main}}. 変異 wrapper の事後検査が共有 main を観測し、並行 land で本走が全損する [手順漏れ] [観測者効果]

- 事象: `tools/mutation_worktree.py` で変異本走を投じたところ、6 走の見積もりどおり最後まで
  走ったのに `mutation worktree aborted: 共有木の事後検査に失敗: source/main 共有木の観測
  bytes が変化した` で rc=125 になり、成果ゼロで捨てることになった。
- 根本原因: 同 wrapper の事後検査は **自 worktree だけでなく共有 main checkout** の
  `git status` / `submodule status` の stdout bytes 不変も要求する。したがって
  (a) 走行中に親が repo を触る、(b) **並行 wave が local main へ land する**、のどちらでも落ちる。
  `DW-O19` は同 wrapper を「主 tree を変異させない経路」として案内するが、
  この観測範囲を書いていないため、**親が何も触らなくても落ちうる**ことが読み取れない。
  本件の wave では走行中に main が実際に前進していた。
- 恒久対応: 並行 land が続く間の本走は `DW-M05` が正本と定める `tools/mutation_harness.py` を
  自 worktree へ直接回す。固定 HEAD 束縛・起動/復元時の内容比較・`flock` 単一走行・逐次 flush・
  signal 復元はすべて harness 側が持つ。落ちるのは wrapper 独自の「共有木を触っていない」主張だけ。
  走行後に自 worktree の clean と HEAD を親が確認し、その確認を記録へ書く。
- 再発検知: rc=125 を見たら捨てる前に `--out` の ledger を読む。`summary` の `recorded` が
  `registered` と一致していれば走行自体は完了しており、失敗したのは最後の検査だけである。
  本件でも baseline PASSED・5 変異すべて記録済みだった。

### {{F:figure-fixture-smaller-than-real-grid}}. 作図の合成 fixture が実寸より小さく、実データでしか出ない欠陥を 2 回続けて通した [恒真ゲート] [被覆漏れ]

- 事象: 新図種の単体テスト 22 件が緑のまま、実データを渡すと 2 回続けて落ちた。
  (1) `duplicate grid coordinate` — 格子座標を `(step, interval)` で作り、probe が構造的に
  必須とする無 backoff セル (3 定数が stock 値で埋まる) が陽性対照と必ず衝突していた。
  **正しく作られた入力では常に落ちる**状態だった。
  (2) `FigureLayoutError: text bbox overlap` — 実寸 6x5 格子の注記密度で重なった。
- 根本原因: 合成 fixture が 1 workload あたり 2 セルしかなく、**実寸の格子形状と注記密度を
  一度も踏まなかった**。座標の一意性もレイアウト検査も、セル数が小さいと恒真に通る。
  上流には親の brief の欠落もある — 結果 schema で「無 backoff セルを 2 次元格子上どう扱うか」を
  producer と consumer の間で決めていなかった。
- 恒久対応: 作図の合成 fixture を**実寸と同じ格子形状・同じ軸点数**にする。本件では
  刻み 6 値 x 間隔 5 値 + 無 backoff、スレッド 8 点へ揃えた。
  producer が構造的に必須とするセルは、consumer 側の fixture にも必ず含める。
- 再発検知: 図の生成は合成テストだけで closed としない。**実データで両モードを実走し、
  rc=0 と 3 成果物 (png / pdf / provenance) の生成を親が確かめる**まで完了と申告しない。
