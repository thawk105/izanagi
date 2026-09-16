# [T-2590] + [T-2081] A-1 balanced5 sized 本走を pilot と同じ amended source 契約に乗せる

- wave: `dev-wave-t2590-a1-sized-source-contract` (2026-09-17、branch `worktree-dev-wave-t2590-a1-sized-source-contract`)
- 基準: local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0`
- 記録 commit: README 追補 `d6f12ed7d`、実装 `ad83b108b`
- 裁定: D1986 項 5 (AI 実装のまま進める、認可は据え置き)、D1323 (T-2081)
- **本走は投入していない。認可 (T-1505) も出していない。**

## 何を変えたか

pilot (`paper-story-a1-20260901-balanced5-pilot-v1`、attempt-0004) 専用に固定されていた計測経路の分岐 4 点を、
sized (`paper-story-a1-20260901-balanced5-sized-v1`) へ対称化した。

| 分岐 | 変更前 | 変更後 |
|---|---|---|
| source 契約 | `paper_story_a1_source.py` が v1 契約 (pilot / attempt-0004) 単一値 | study_id → (契約 path, sha256, source paths) の固定 2 要素表。sized は `paper_story_a1_source.v2.json` (sha `b50a4edf…`、11 key、`attempt` なし) と sized 追補 README (sha `6093de24…`) に束縛 |
| hydrate 入力と staging | submit の hydrate dir 要求・intent の hydrate 変数・job の staging が pilot 限定 | pilot / sized の両方。`_v3_group_intent` の pilot attempt-0004 条件は受領証再構成のため残す |
| source binding の生成 | `_source_relative_paths` が pilot にだけ 4 path を足す。job の閉包 3 箇所も pilot 限定 | study 別の 4 path (契約 → module → patch → 追補)。pilot は 10+4 / 5+4 で順序込み不変 |
| amended build の受理形 | consumer の amended admission 発火が v1 契約 path 固定 | 両契約 path で発火。`_trace0_commands_match` (FETCHCONTENT 4 token を要求する既存形) は不変 |

`_run_measurement_v3` の無条件な `study == 契約 study and attempt == 契約 attempt` は、study 一致 + pilot のみ attempt 照合に分けた。

## T-2081 (D1323) の閉じ

新規 gate も bytes 級検査も足していない。既存機構が sized を study 非依存に覆うことを test で確認した。

- `_assert_ccbench_acceptance` (submit / driver / consumer の 3 境界): submodule 直接の `rev-parse HEAD` = canonical pin と `status --porcelain --untracked-files=no` の空。sized policy で正例 1 + 負例 3 (tracked dirty / HEAD 不一致 / HEAD 解決失敗)。`_parent_porcelain` (親側 `--ignore-submodules=all`) が空でも submodule dirty で拒否。
- build 直前: `pipeline._require_canonical_build_source_state` が sized の `SourceContext` を trace / perf 双方で `validate` (pin + 期待 materialization) に通す。
- 出所の判定 = commit ID の確定可能性 (元 checkout の HEAD が canonical pin かつ tracked-clean、build source が pin + 指定 patch の期待 materialization と一致)。
- **限界 (記録):** 上記 test は Git 応答・期待 materialization 生成/比較を stub する。実 tree 検査の実証ではなく「既存機構への接続確認」。元 checkout の untracked は凍結 policy の `untracked_files_ignored: true` のとおり無視し、実測 source は pin から隔離生成する (段 3 A: 3 経路とも反例を構成できず)。

## 受理集合の変化 (段 3 A の表)

| 入力 | 変更前 → 変更後 |
|---|---|
| 契約なし sized binding (5 / 10 path) | 受理 → 拒否 |
| v2 契約入り sized binding (9 / 14 path、正しい digest) | 拒否 → 受理 |
| hydrate なし sized submit | 通過 → 拒否 |
| 登録条件を満たす sized measurement | `A1 source amendment requires pilot attempt-0004` で全拒否 → 進行可能 |
| pilot (attempt-0004) | 不変 |

helper `_validate_source_binding_for_paths` 単体は一契約性を保証しない (正規経路は閉包完全一致で両契約入り / 契約なしを拒否する)。

## 段 3 / 段 6 の所見と裁定

### 段 3 (敵対相談 2 本、`verbatim/s3-a-freeze-and-acceptance.md` / `s3-b-effectiveness.md`)

- A (凍結・規律・受理集合): pilot 履歴 binding の互換・両契約混入・hydrate の無検査経路・D1323 の反例 3 経路はいずれも構成不能 (refuted)。real = 受理集合の拡大と縮小の明記、T-2081 の閉じは実測前、追補 README への限定 2 文、pilot attempt 1〜3 の失敗分類の訂正。
- B (実効性・全層整合): 追加の pilot 限定分岐なし、閉包順序と `count == 3` は維持可能 (refuted)。real = sized fixture に `sizing_inputs` の 2 file が要る、root 不一致の期待 error は 2 分、M7 は正例 node、M8 は literal 照合の追加、現行 sized は 7127 行で先に落ちる。
- 裁定は `verbatim/s4-ruling.md` (全所見の real / refuted、plan v2、変異事前登録 M0〜M10)。scope 外の real 所見なし。

### 段 5 (実装、`verbatim/s5-author-round1.md` / `s5-author-round2-final.md`)

- 1 巡目は親の test 8 仕様誤り (呼出先を 14 path の validator と書いた。公開 binding は terminal 用 9 path) で、期待値を弱めずに停止した。2 巡目 (継続) で訂正。最終: 新規 14 test、sandbox 内 pytest 129 passed、反実仮想 20 変異 KILLED / 等価 1 SURVIVED。**最終状態は round2 の報告が正で、round1 は停止理由の記録。**
- v2 JSON の 4 束縛 (patch / policy / preregistration / amendment の sha) と `SIZED_CONTRACT_SHA256` は親が実 file から独立検算して一致。

### 段 6 (レビュー 2 本 + fix 1、`verbatim/s6-review-a.md` / `s6-review-b.md` / `s6-fix1.md`)

- production の must-fix ゼロ。real = 報告時点の不一致 (親が round1 だけを射影した所為、round2 で閉じる)、変異 anchor の再照準 (M4 は 2 行、M6 は `THIRD_PARTY_ARGS=()` 込み — 事前登録に反映)。nit = sized の hydrate 欠落時の文言が `attempt-0004 requires …` のまま (受理判定に影響なし、据え置き)。
- 焦点走 (計算ノード request 2324.nqsv、9 test file): 2 failed / 689 passed。(1) `test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base` = manifest file の未 commit 差分検査 (統合 commit 後に緑)。(2) `test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` = paired.py の `run_measurement` 内 `run_campaign(` sink の行番号 pin 7423 が差分 +5 行で 7428 へ (fix1 が 2 箇所を実値へ更新、pytest 47 passed、反実仮想 7429 で赤)。統合 commit 後の再走: spawn_sites + headline 82 passed、test_campaign 選択 node 6 passed。

### 変異 matrix (container `.codex/worktrees/t2590-mutcontainer`、統合 commit ad83b108b、runner = 3 A-1 test file、dispatch)

- probe (全件 SURVIVED 期待、`mutation-spec-probe.json` / `mutation-ledger-probe.json`): baseline PASSED、M0 SURVIVED、負例 10 件すべて赤で観測 node を収集。観測 node は全件が本 wave の新規 test で、既存 test の巻き添え 0 (冗長 gate なし)。
- 本走 (`mutation-spec-final.json` sha `865b0f10…` / `mutation-ledger-final.json`): **baseline PASSED、負例 10/10 KILLED、期待 node 完全一致 11/11、等価 M0 SURVIVED、MISMATCH 0、TIMEOUT 0**。走行後の container は HEAD ad83b108b、`status --porcelain` 空。

| id | 対象 | 操作 | KILLED node 数 |
|---|---|---|---|
| M0 | `paper_story_a1_source.py` `CONTRACTS = {` | 等価 (comment 付加) | SURVIVED (正例) |
| M1 | 同 `CONTRACTS` | sized の要素を落とす | 9 |
| M2 | 同 `load_contract` | 契約 JSON 自体の sha 検算を外す | 1 |
| M3 | 同 検算 loop | `amendment` の検算を外す | 1 |
| M4 | `paired.py` `_source_relative_paths` (2 行) | pilot 限定へ戻す | 4 |
| M5 | job script terminal 閉包 (J:997) | pilot 限定へ戻す | 1 |
| M6 | job script staging (J:1379-1381) | pilot 限定へ戻す | 1 |
| M7 | `paired.py` consumer 発火条件 | v1 契約限定へ戻す | 2 |
| M8 | `paired.py` `_run_measurement_v3` | literal `attempt-0004` 照合を study 非依存に | 1 |
| M9 | `paired.py` `_v3_group_intent` | sized の hydrate 必須を外す | 1 |
| M10 | `paired.py` binding 照合 | v1 契約限定へ戻す | 1 |

### 逐語の可逆正規化

`verbatim/s2-plan.md` は原文に行末空白 (markdown 改行) が 10 行あり末尾空白検査に抵触するため、表示用は行末空白を除いた (26,225 → 26,205 bytes、可視文字不変)。原文は `verbatim/s2-plan.original.gz` に保持 (原文 sha256 `3f95be9a9202d4a7a8cfdbac8ff5884be10ea69563cbcc68af5f5975682d26b5`、`gzip -dc` で復元)。

## この記録が主張しないこと

- sized 本走が実機で全層を通ったとは言わない。新規 test は materializer / 依存準備 / condition gate / campaign を stub する。実機の生死は pilot attempt-0004 が同じ経路を完走した事実に依拠する。
- 変更後 checkout で過去の pilot 束を再 materialize / 再発行できるとは言わない (`_verify_current_source_paths` は HEAD・blob・working sha を照合する既存の境界)。
- pilot の失敗分類: attempt-0001 / 0002 は bench 前停止、attempt-0003 は条件関門の拒否 (依存供給不足 + source 意味不整合)。sized の attempt を pin しない根拠はこれではなく、追補前の sized attempt が存在せず契約が束縛するのは source であって attempt ではないこと。

## 逐語の保存

`verbatim/` に段 1 brief と既裁定逐語、段 2 plan、段 3 敵対相談 2 本、段 4 裁定、段 5 実装報告 2 本 (round1 = 停止理由、round2 = 最終)、段 6 レビュー 2 本と fix 1 本を保存した。変異 spec と台帳 (probe / final) は本 dir 直下。運転 script・prompt・log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2590-a1-sized-source-contract/` に保全した。
