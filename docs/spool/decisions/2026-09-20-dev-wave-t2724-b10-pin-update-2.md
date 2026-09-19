---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2724-b10-pin-update
seq: 2
---

## {{D:b10-freeze-tree-pin-follows-generation-g}}. B-10 の freeze-tree 起動契約を D2120 項 2 (b) で導入した世代 G を含む tree へ更新する — 旧測定の解釈は不変で、新 phase の事前登録成立ではない

**決定 (親の裁定、entry 1688 の設計 §7 と本依頼「Codex author が literal を再計算値へ更新」に従う):**
`tools/pegasus/b10_backoff_grid.sh` の `EXPECTED_FREEZE_TREES_SHA256` と
`orchestrator/tests/test_backoff_extended_sweep.py` の同 literal 2 箇所 (job script の文字列検査、実 tree digest の固定 pin) を、
旧値 `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (19 file、G 無し) から
新値 `6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415` (20 file、G 有り) へ更新する。
新値は保存枝 chain/X2/G を merge した木で着手時に再計算した値で、G (`output/s8b-freeze/holdout_freeze.v2.g1.json`、
blob `15861416f`、sha256 `7e1114068433…`、20,737 byte) の追加だけが旧値との差分である。

- **変わるもの:** 本更新を含む版の job script が要求する起動条件 (`B10_RUN_KIND` を問わず)。この版の job script は
  G を含む現在の 20 file の tree だけを受理し、G を欠く tree、別 file の追加、既存 file の 1 byte の変更、G の削除を
  測定前の digest 検査 (`fail 2`) と test で拒否する (算法上の性質。実測は一次資料に記録する)。旧 script と旧 tree を備えた
  旧 checkout の組はこの更新で失効しない (旧版を失効させる機構は無く、本決定はそれを足さない)。
  算法・完全一致比較・対象 dir 集合 (`output/s1-freeze` + `output/s8b-freeze`)・job 前後の一致検査・`completion.json` の記録は不変。
- **変わらないもの (規律 7):** cohort 1 (group `b10-backoff-grid-20260915T061814Z-545445`) と cohort 2 (D2157) の
  `freeze_trees_sha256` = 旧値の記録 (results 稿 2 本、`completion.json` 6 件、insight、archive) は測定時点の事実として書き換えない。
  当時の判定も変えない。旧値と新値の対応 (G の追加だけ) は本決定と一次資料に残す。
- **成立しないもの:** 本更新は B-10 の新 phase の事前登録成立でも本走許可でもない。事前登録 `cad6f46d8` の bytes は不変で、
  次の cohort・帯・phase は従来どおり別途の登録 commit と裁定を要する (D1789 / D2050 / D2157 の枠組みのまま)。

**授権根拠:**
- D2120 項 2 (b) (ユーザー裁定 2026-09-17) は G の導入を授権し、G の path は `s8b_ratified_freeze.FREEZE_DIR = "output/s8b-freeze"`
  と `resolve_active_generation` が要求する固定 path で、pin の対象 dir から外せない。G を main に載せる (項 2 (a)) と
  pin の旧値は必ず不一致になるので、G の取り込み・現行の全 file 完全一致検査・B-10 の継続利用を保つ条件下で、規律 2
  (hold / 除外 / 条件付き assert は不採用) と両立する形は pin を G 込みの値へ
  更新することだけである。
- pin が守るのは「将来の B-10 job が要求する凍結 tree の同一性」(job script 595 / 647 行) であり、過去の成果物との対応は
  各 job の `completion.json` が記録する (定数に依存しない)。よって更新は発効済み事前登録の書き換え (D1789 の対象) に当たらない。
- 前 wave (entry 1688) は「赤を見た同じ主体が同じ wave で期待値を変える」形を避け、更新を別 context・独立レビュー・
  変異 2 件・負例 3 件付きの本 wave へ送った。本 wave はその条件で更新を行い、実測 (焦点走・変異・負例・受入全走) の結果と
  証拠の所在は一次資料 `output/insights/2026-09-20/t2724-b10-pin-update/README.md` に記録する (本 fragment は land の fold で
  台帳に載るので、記録時点で実測が済んでいなければ一次資料に「未実施」と書く)。

**却下した選択肢:**
- 複数値受理 (旧値と新値のいずれかを受理) — 「新旧どちらか」は G の有無を検査しなくなり、pin の意味 (tree の同一性) を失う。規律 2。
- prefix 除外 (G の path を digest から外す) — G を含む tree を凍結対象から外すことになり、世代文書の改竄を pin が見なくなる。
- hold / skip / 条件付き assert — D532 / DW-O18 に反する検出力の削除。
- test だけ更新し job 定数を旧値のまま (前 wave の択 2) — test と job の束縛が切れ、実投入が旧 pin で止まる (両レンズが refuted)。
- pin を撤去して `completion.json` の記録だけに頼る — 起動前の fail-closed 検査を失う。
