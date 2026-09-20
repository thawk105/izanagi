---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: record-t2700-prewarm-ab-record
seq: 1
title: [T-2700] receipt memo prewarm の早期起動を同一 SHA の実受入で E/L 隣接対 7 組で対比較し、7 対とも早期起動ありが短い (対差中央値 +33.5 秒、Wilcoxon 片側 p = 1/128、配布開始の遅れ +25〜+41 秒で機序と整合) を記録した (docs-only land、実装 (測定用 opt-out) は impl branch、branch record-t2700-prewarm-ab-record)
---

## 本文

- 依頼 (T-2700 起票文、D1936 項 35) の範囲で 1 wave。一次資料は `output/insights/2026-09-20/t2700-prewarm-ab/README.md` (走表・対表・判定・失敗集計・再現資料)、設計判断は {{D:early-memo-ab-measurement}}。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/HANDOFF.md`。
- **必要走数の事前見積り**: 過去 523 session の stderr `IZANAGI_MEMO_PREWARM_V1` 行から機序を定量化 (L 経路は collection 通知後の同期解決 ≈ 30 秒で配布開始 86 秒、E 経路は解決が collection と並走して配布開始 60 秒 → 予測 δ ≈ 27 秒)。
  判定規則そのもの (Wilcoxon 片側 exact ≤ 0.05 ∧ 中央値 ≥ 15 秒) の検出力を MC で出し、δ=27 / σ_d=22 で 6 対 0.76・8 対 0.85、裾 model で 8 対 0.50。**必要走数は仮定依存で確定できない**と記し、有効 8 対 (上限 20 走) の固定予算で事前登録した (逐次検定なし)。
- 段 3 相談 (2 レンズ 1 本) は must-fix 7 を出し全採用。最重要は (a) 介入 = 早期 memo 機構全体の有無と H/D の意味の訂正、(b) 検出力を判定規則そのもので評価、(c) E 固有の失敗を捨てない 2 つの推定対象、(d) test は実 `pytest_configure` の結線を通す、(e) E 腕は env を空文字で明示 overlay。
- 段 5 は Codex author 1 本 (conftest の測定用 opt-out = env exact token を `pytest_configure` で config 属性へ、`_early_memo_selected` が属性を見る (synthetic config の既存 test は両腕で緑)、allowlist 1 key、test 4 本、集計器 + 履歴 script)。author sandbox では pytest 起動不能 → 親の焦点走 (計算ノード 7 file): 1041 passed / 2 failed (新 test の組み立て) → fix1 → **1043 passed / 0 failed**。実装 commit `7447c9a35` (= 測定 tip)。
  段 6 はレビュー 2 本 + fix2 (集計器: 診断の検出先、解析締切、束縛検算、失敗分類) + 焦点再レビュー (GO 不可: 系列制御の regressed、request 引数) + fix3 (`--series-state`) + fix4 (実物の receipt 形) + 測定中の fix5 (run.json の `+0900` を集計器が拒否した偽陰性 → 投入前に系列を止めて直した)。
  変異 6 件は probe で観測 node を集めてから final で **6/6 KILLED、期待 node 完全一致**。
- **測定 (2026-09-20 10:14〜17:55 JST、20 走、有効 7 対)**: 最遅 shard (7 対とも shard-0) の JUnit wall の対差 ΔW = L − E = +122.3 / +23.3 / +22.0 / +39.4 / +41.8 / +33.5 / +29.1 秒、中央値 +33.5 秒 (対率 6.9 %)、条件別中央値差 +29.2 秒、Wilcoxon 片側 exact p = 1/128 (両側 0.0156)、t = 3.35 (df 6)、σ_d = 35.1 秒。
  配布開始の遅れ ΔD_0 = +24.9〜+40.7 秒 (中央値 +32.8) で、対 1 以外は ΔW ≈ ΔD_0 (対 1 は最忙 worker の regime 差 +98 が乗った)。witness は全走で事前登録どおり (E: 3 shard `configure_node`、L: shard-0 だけ `xdist_node_collection_finished`)。判定 = 「成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上) + 腕別失敗 E=3 / L=0」、**8 対には未達** (無効 3 走の取り直しに 6 走を使い上限 20 で締切)。
- 棄却・限界: E の無効 3 走はいずれも他 wave の受入でも出る既知の間欠赤 (lock relay の timing 2 件、`output/runs/` 一時 dir の scandir race 1 件) で treatment 固有の失敗は 0 件だが、E にだけ当たった理由は未同定 (偶然の範囲 ≈ 0.12)。失敗を敗北に数える感度分析は 7 勝 3 敗 (p = 0.17) で有意でない。隣接対は同 allocation でなく node も対内で異なる。同時刻に別 wave の測定系列と受入が並走した。観測 σ_d は事前仮定より大きく、事後の検出力は δ=27 で 7 対 0.47。
- 運用の逸脱 (投入前・結果を見る前): 門番の他 wave 受入待ち手の上限を 1 → 2 に緩めた (63 分開かず)。集計器の時刻書式の偽陰性で 01-E 後に系列を止めて再開 (走番号は消費せず)。
- **早期起動 (T-2616) は現行 main の挙動であり、本測定は「止めると最遅 shard が ≈ 30 秒遅くなる」を示した。義務化・launcher 自動検査は scope 外 (D1936 項 35) で、追加実装は不要。** 実装 (opt-out) は main に入れず branch `impl-t2700-early-memo-optout` (tip `7447c9a35`) に保存、landing は本 insight と fragment だけ。
- 工数: codex 10 本 (consult 1、author 1、fix 5、review 2、focus 1、gpt-6-astra medium)、計算ノード job = 焦点走 2 + 変異 14 + 測定 20 走 × 3 shard、warm 1 (login local)。wave 07:06〜(land 時刻は fold の日付)。
- 残置: wave 木 `.claude/worktrees/dev-wave-t2700-prewarm-ab` (branch `worktree-dev-wave-t2700-prewarm-ab` = `7447c9a35`、impl と同 SHA) と子木 `.codex/worktrees/t2700-unit-impl` (branch `dev-wave-t2700-unit-impl` / `-fix1`〜`-fix5`、実装 5 path は main に無いので `remove-child` は拒否される見込み) は段 9 で撤去を試み、拒否なら unlock して残す。撤去は採否の裁定後に /cleanup-branches で (impl branch は残す)。

## 次の一手差分

### 完了

- [T-2700] 必要走数を事前に見積もり (仮定依存で確定不能と記録)、同一 SHA の実受入で E/L 隣接対 7 組 (上限 20 走) を取り、7 対とも早期起動ありが短い (対差中央値 +33.5 秒、片側 p = 1/128、機序指標 +25〜+41 秒) を記録した。一次資料 `output/insights/2026-09-20/t2700-prewarm-ab/README.md`。
  remaining: none
  base: 67da8b9b11ab1c0ba2cccdc1c05f0494bbd7fcee381c0156d3a8812435c1a0bc
