# [T-2035][T-2037] 軸 1 OpenAlex — 打ち切り後の再開、5 窓目の取得 (2026-09-17)

新 epoch `AX1-20260902-E1` の OpenAlex 取得を、D1760 の打ち切り後にユーザーの直接指示で再開した記録。
**12 起動 / 93 request で未走 leaf の pass 1 を 7 本進め (完走 5・条件 5 で 2 本落ち)、
独立 2 走目 5 本は 5 本とも `second_pass_digest_mismatch` になった。**

再開はユーザー指示 (`/dev-wave` 引数) による D1760 の部分的な supersede であり、決定の正本は
decisions 台帳の該当エントリ (本 wave の fragment から採番) である。**軸 1 は `未完走` であり、
成熟度は `RW1` のまま。論文は世界の不在を主張しない。**

凍結した実行記録は `docs/related-work/claim-survey/2026-09-17-axis1-search-execution.md`。
4 窓目は `output/insights/2026-09-08/t2090-axis1-openalex-window4/`、
3 窓目は `output/insights/2026-09-07/t2090-axis1-openalex-window3/`、
2 窓目は `output/insights/2026-09-05_t2090-axis1-openalex-window2/`。

## 中身

| file | 中身 |
|---|---|
| `driver.py.txt` | 駆動 loop の逐語 (repo 外の使い捨て script。実装面ではない)。Codex `role=author` の実装子が窓 4 の逐語を土台に書き、差分は docstring の窓番号・path 定数 2 行・除外集合への 2 leaf 追加だけ (親が diff で確認、fix 0 巡) |
| `driver-dryrun.txt` | 親が実 bundle へ通した `--dry-run` の全文 (計画 62 件: 再開 0 / 未走 9 / 2 走目 53) |
| `driver-stdout.txt` | 駆動 loop の stdout (6 起動、残量 159 で停止) |
| `fetch-window5.jsonl` | loop の起動 6 本の台帳 (key、段、state、reason_code、request 数、起動前残量、時刻) |
| `launch-order.txt` | loop の起動順の key |
| `manual-first.jsonl` / `manual-first.stdout.json` | loop の前に親が手動起動した 1 本 (段 A の 1 件目 `Q6-SY2018`、dry-run の argv を逐語で使用)。前窓の持続観測 (57) を今窓の値へ更新するため |
| `manual-b.jsonl` / `manual-b-0000NN.stdout.json` | loop 停止後に親が手動起動した独立 2 走目 5 本 (checkpoint 000009〜000013 の `canonical_runner_argv` を逐語で使用) |
| `leaf-order.txt` | catalog の登録順の OpenAlex leaf 78 本 (窓 4 と同一、catalog から再導出して一致確認) |
| `evidence-detail.txt` | 起動した 12 leaf の証拠の射影: 段 A は**頁ごとの申告総数・実要素数・重複数**と pass 1 台帳の occurrences / distinct、段 B は pass 1 と pass 2 の distinct と **work ID 集合の差** (page 証拠の `parse` / `records` 節と `ledgers/*.passN.*.json` から採った) |
| `leaf-states.txt` | `bundle-check.json` の leaf 診断から数えた OpenAlex 78 leaf の状態分布と、`complete` 以外の全 leaf の行 |
| `liveness-probe-1.txt` / `liveness-probe-2.txt` | 取得前後の rate limit header の逐語 (`per-page=1`、各 1 credit) |
| `registration-check.json` | fetch-tree (登録 commit を detach した木) での `tools/check_axis1_search.py registration` の出力 (`passed: true`) |
| `bundle-check.json` | 取得後の `tools/check_axis1_search.py bundle` の出力全文 |
| `mirror/` | 生 bundle の部分複製 (`checkpoints` / `state` / `manifest.json` / `MANIFEST.sha256`) |

## 生 bundle の所在

live bundle root (再開と検証はここで行う):
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (296 MB)

`manifest.json` の SHA-256 = `a6a42514e6d52c4e90243e706295f3ce215f4f5c91c0ad100a7d90f32d22e2a4`
(走行前は `f3aeb91f823d2820d289668cbc85b8a3a0b51ca44608d46fc135847b48da0035` = 窓 4 の走行後値。無傷を確認してから起動した)。

`mirror/` は `raw/` `pages/` `ledgers/` を除いた複製で、**単独では `verify_bundle` を通らない**
(checkpoint の `bundle_root` は上の絶対 path であり、manifest の path 集合は除いた 3 つを含む)。

## 何をしたか

### 1. 起動の条件

- cwd は登録 commit `4ec3eba04` を detach した木 (`git worktree add --detach`、repo 外の job dir)。
  登録検査は `passed: true`。
- 窓は 9/8 以降 1 request も出していなかったので満量だった。生死確認 (00:36 JST):
  `x-ratelimit-remaining=999`、`x-ratelimit-reset=30190` (= 2026-09-17 09:00 JST)。
- 駆動 loop は窓 4 の逐語に 2 点だけ変更を入れた (path 定数、除外集合に `Q6-SY2014` / `Q6-SY2015`)。
  `Q6-SY2015` は `resume_action=continue_cursor` の checkpoint `000060` を残しているため、除外しなければ
  段 A0 に乗って再開されてしまう。裁定待ちの 2 本は走らせていない。段 A0 の経路自体は残した。
- 持続観測が前窓の 57 のままで loop が起動前に止まるため、窓 2 と同じく計画 1 件目を親が手動で正規
  runner に通して観測を更新した (取得器の発行規範には触れていない)。
- 残量は起動と起動の間に `state/runtime.json` から読み、200 未満で新規起動を止めた。

### 2. 結果

| 起動 | leaf | 頁 | state | reason_code |
|---|---|---|---|---|
| 手動 | `Q6-SY2018` | 5 | `pass_complete` | — |
| loop | `Q6-SY2019` | 7 | `pass_complete` | — |
| loop | `Q6-SY2020` | 9 | `pass_complete` | — |
| loop | `Q6-SY2021` | 11 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` |
| loop | `Q6-SY2022` | 12 | `pass_complete` | — |
| loop | `Q6-SY2023` | 16 | `pass_complete` | — |
| loop | `Q6-SY2024` | 24 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` |
| (loop 停止) | `Q6-SY2025` の前 | — | 残量 159 < 200 | — |
| 手動 | `Q3-SY1997` 2 走目 | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 手動 | `Q3-SY1998` 2 走目 | 1 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 手動 | `Q3-SY1999` 2 走目 | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 手動 | `Q3-SY2000` 2 走目 | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 手動 | `Q3-SY2001` 2 走目 | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |

残量 999 → 69 (93 request × 10 credit)。生死確認 2 本で別に 2 credit。新しい checkpoint は
`000063`〜`000067` の 5 本 (完走した pass 1 の 2 走目の再開点)。

**最近年の頁数が大きい。** `Q6` は 2018 年の 5 頁から 2024 年の 24 頁 (申告総数 4669) まで単調に増え、
段 A の 7 leaf だけで 84 request を使った。1 窓 (約 80 request) では段 A が終わらず、段 B は loop から
1 本も起動できなかった。

### 3. loop 停止後の残量を段 B に使った

loop は残量 159 で止まった。閾値を下げて loop を回し直すと、計画順で先に来る段 A の `Q6-SY2025`
(20 頁超の見込み) が起動し、取得器の自己施錠 (残量 40 未満で 1 request も出せなくなる) を招く。
そこで loop は使わず、親が段 B の先頭 5 本 (計 9 request、各 1〜2 頁) の checkpoint argv を逐語で
1 本ずつ起動し、起動前に「残量 ≥ 40 + 10 × 頁数」を確かめた。残量 69 で止め、次窓の手動更新 1 本が
出せる状態を残した。

### 4. 段 A — 申告総数は一定、頁境界の重複が常態、落ちた 2 本は 1 件不足

`evidence-detail.txt` の数値。

| leaf | 申告総数 (全頁一定) | occurrences | distinct | 頁境界の重複 | 結果 |
|---|---|---|---|---|---|
| `Q6-SY2018` | 888 | 889 | 888 | 1 | `pass_complete` |
| `Q6-SY2019` | 1242 | 1242 | 1242 | 0 | `pass_complete` |
| `Q6-SY2020` | 1598 | 1600 | 1598 | 2 (終端頁 p8 は 0 件) | `pass_complete` |
| `Q6-SY2021` | 2043 | 2044 | **2042** | 2 | `blocked_on_ruling` (1 件不足) |
| `Q6-SY2022` | 2251 | 2255 | 2251 | 4 | `pass_complete` |
| `Q6-SY2023` | 3183 | 3187 | 3183 | 4 | `pass_complete` |
| `Q6-SY2024` | 4669 | 4671 | **4668** | 3 | `blocked_on_ruling` (1 件不足) |

- 申告総数は 7 leaf すべてで全頁一定。窓 4 の `declared_total_drift` は本窓では出ていない。
- **頁内の重複は 0 だが、頁境界を跨ぐ重複が 7 leaf 中 6 leaf にある。** cursor 分頁の最中に並びが
  動いて同じ work が 2 頁に現れる形で、通った leaf も同じ現象を持つ。通るか落ちるかは、押し出された
  work が別の頁に再出現するか (重複だけで済む) 消えるか (distinct が 1 件足りない) の差である。
- 落ちた 2 本はどちらも不足 1 件。窓 3 の `Q3-SY2025` / `SY2026` (2〜3 件不足) と同じ条件 5 の形。
- **条件は緩めていない。** 取得器の `blocked_on_ruling` をそのまま記録している。

### 5. 段 B — 12 日を隔てた独立 2 走目は 5 本とも不一致

pass 1 は 9/5 (窓 2)、pass 2 は 9/17。`evidence-detail.txt` の数値。

| leaf | pass 1 申告/distinct | pass 2 申告/distinct | 2 走目で増えた ID | 消えた ID | 共通 ID の順序 |
|---|---|---|---|---|---|
| `Q3-SY1997` | 233 / 233 | 234 / 234 | 2 | 1 | 変化 |
| `Q3-SY1998` | 185 / 185 | 184 / 184 | 3 | 4 | 変化 |
| `Q3-SY1999` | 220 / 220 | 216 / 216 | 3 | 7 | 変化 |
| `Q3-SY2000` | 225 / 225 | 225 / 225 | 2 | 2 | 変化 |
| `Q3-SY2001` | 222 / 222 | 220 / 220 | 0 | 2 | 変化 |

- **申告総数が同じ `Q3-SY2000` でも中身は 2 件入れ替わっている。** 総数の一致は同一性の証拠にならない。
- 5 本すべてで共通 ID の並び順が変わっている。索引側の並び (relevance) が更新されている。
- 窓 2 の 2 走目 (2 日を隔てて 8 本中 1 本不一致) より格段に高い不一致率であり、**残る 2 走目待ち 48 本
  (pass 1 は 9/5・9/7・9/8) も同じ運命になる見込みが強い。** 「同じ登録 request を日を隔てて 2 度投げて
  同じ集合が返る」という完走条件は、生きた索引に対して日数が経つほど成立しなくなる。
- 不一致 leaf には後継 checkpoint が無く、再取得しか経路が無い (窓 2 と同じ)。

### 6. 打ち切り時点からの状態の変化 (OpenAlex 78 leaf)

| 状態 | 窓 4 終了時 | 本窓終了時 |
|---|---|---|
| `complete` (独立 2 走まで完了) | 8 | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 | 53 (−5 不一致、+5 新規) |
| 条件 5 で未完走 (再開点なし、`Q1` / `Q4` / `Q5`) | 3 | 3 |
| 2 走不一致で未完走 (再開点なし) | 1 | **6** |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 | **4** |
| `declared_total_drift` で pass 1 が落ちた (再開点なし、裁定待ち) | 2 | 2 |
| 未走 | 9 | **2** (`Q6-SY2025` / `SY2026`) |

検査器は `bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` (rc=2)。検査器の leaf 診断では条件 5 と drift の「再開点なし」6 本は
`leaf_page_evidence_missing` として現れる (`expected_passes=[1, 2]` に対して pass 2 が無い方が先に立つ。
窓 3・4 と同じ構造)。走行時の理由は台帳側 (`fetch-window5.jsonl` / `manual-b.jsonl`) に残る。

## この wave が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。**repo の実装面の差分は 0。**
駆動 loop は repo 外の使い捨て script で、逐語を本 directory に `.txt` で置いた。

## 次の窓へ

- 未走 2 leaf (`Q6-SY2025` / `SY2026`、それぞれ 20 頁前後の見込み) と 2 走目待ち 53 本。1 窓 (約 80 request)
  で未走 2 本は収まるが、2 走目 53 本 (132 頁) は 2 窓分。
- ただし §5 のとおり、日を隔てた 2 走目は不一致になる見込みが強い。**2 走目を続けるかどうかは裁定事項**
  であり、本 wave は取得結果を報告するだけで方針を変えていない。
- checkpoint の argv は逐語で渡す (`--run-id` を差し替えない)。`continue_cursor` は第 3 の再開経路。
  重複除去の照合 key は `leaf_query_id`。一過性の 429 は再計画して待てば通る。
- loop の閾値を下げて残量を使い切るときは、計画順で先に来る段 A の大きい leaf が自己施錠を招かないか
  頁数で確かめる (本窓は段 B を親が手動で回した)。
