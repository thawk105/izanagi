---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2613-append-only-constant
seq: 1
---

## {{D:attempt-history-gate-constant-reduction}}. attempt registry の全 ref 履歴 gate は、同じ 3 規則のまま少数 process へ再構成した形を採用し、成長項が残ることを記録する

**決定:** 発行側 `orchestrator/campaign/trial_registry.py` と受入側 `orchestrator/campaign/s8c_acceptance_receipt.py` の
`_assert_attempt_registry_history_append_only` を、commit ごとの `ls-tree -r` と blob ごとの `cat-file` process
(現行、1 呼出 = 1 + 11,7xx + 約 1.78 億 process) から、`cat-file --batch-check` / `cat-file --batch` (応答 256 MiB 上限の
chunk 分割) / `log --stdin --root --diff-merges=separate --full-history --raw -z --no-renames --no-abbrev
--no-show-signature --format=%H --diff-filter=AMT` の計 37 process へ再構成した形 (commit `6616fa06c`) を採用する。
規則は R1 (topo 順・全 ref の canonical の strict prefix 拡張と deleted)、R2 (全 commit の全 tree の非 canonical
path にある genesis 形 blob の拒否)、R3 (working の prefix 拡張) と拒否文言を現行のまま保ち、範囲限定・path filter・
size filter・cache・受領証は導入しない。canonical の解決は directory の tree object を成分ごとに parse し entry mode
(中間 `40000`、末尾 `100644`/`100755`/`120000`) で判定する (object 種別だけで判定しない)。診断は (rank, 段, path bytes)
最小の 1 件で、帰属不能な process/応答異常だけ順序保証外。git 呼出は両 module とも既存の `_git` に `input_bytes` を
足しただけ (spawn site 各 1、発行側の 300 秒/回は不変、受入側に timeout は足さない)。

**理由:**
- D2044 項 19 / D2034 の順序どおり、範囲を 1 件も削らず定数だけを下げた。実 repo (11,778 commit、到達可能 unique blob
  49,123 件 / 7.37 GB) での同時刻対照 (旧版標本の窓内観測からの外挿 vs 削減版の全走、2 走) で、削減版 1 呼出
  34.7〜46.1 秒に対し旧版推定 1.7×10^6〜5.4×10^6 秒 (20〜62 日)。事前登録した採用条件 (N_max < E_min/100、
  合成 repo の旧新一致 10/10、AMTD 復元と 20 標本の 20/20 一致、5 区分の窓内被覆、全 git 呼出 rc=0) を満たした
  (`output/insights/2026-09-18/t2613-append-only-constant/README.md` §3.3)。
- 現行形は genesis 作成後に 8c の登録 launch と受入 receipt 検証を最初の 1 回で止める (完走不能)。
- 等価性の根拠: 固定した C について「全 tree の blob entry 集合 = root と各 parent への差分の新側 A/M/T の和集合」
  (初出による帰納法)、`-m` / root 表示 / 署名表示の repo-local 設定依存を argv で固定、C を stdin で固定 (ref 変動の遮断)、
  entry mode の検査、診断順の path 順 tie-break。実 git fixture の負例・正例 (両 file 35 / 34 node) と変異 matrix で守る。

**却下した選択肢:**
- `<commit>:<path>` の `cat-file --batch-check` だけで canonical を判定する — object 種別しか分からず、gitlink entry が
  blob/tree oid を指す壊れた tree で現行より緩む (段 6 レビュー A の反例)。
- raw log に `--all` を残す — 固定 C の外の ref 変動で失敗・変動する。`--stdin` に一本化した。
- `rev-list --objects` で (path, blob) を列挙する — 1 object 1 path しか出ず、同じ genesis blob の別 path copy を見落とす。
- 受入側の戻り値・`current_bytes` の契約変更 — production caller に不要で、旧新比較の不一致を生んだ。変更前へ戻した。
- 範囲限定 (HEAD 祖先・直近 N commit) — D2044 項 19 が「定数削減で足りないことを示してから」と順序を定める。本 wave は
  設計しない。

**記録しないこと (D2034):** 削減版の主項は O(到達可能 unique blob bytes) (本文読取 20〜22 秒) と O(commit) の metadata で、
成長比例費用は残る。「解消した」とは記録しない。1 呼出 35〜46 秒 (login node、負荷 14〜48) が 8c の運用に足りるかは本 wave では
判定しない。壊れた tree (同名 entry 重複、mode と object 種別の不一致) では旧版と文言・受理が異なりうる (insight §4.3、未証明の残余)。
