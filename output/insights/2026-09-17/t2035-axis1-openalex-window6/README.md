# [T-2035] 軸 1 OpenAlex — 6 窓目、未走 2 leaf のうち `Q6-SY2025` を取得し、`Q6-SY2026` は 1 窓に収まらないと実測して起動しなかった (2026-09-17)

新 epoch `AX1-20260902-E1` の OpenAlex 取得の 6 窓目。D2095 項 3 (未走 2 leaf の初回取得は 2 走目の裁定と
独立に取得できる) に従い、同じ登録 commit・同じ epoch・匿名 request で回した。
**1 起動 / 51 request で `Q6-SY2025` の pass 1 を取得し (条件 5 で `blocked_on_ruling`、不足 12 件)、
`Q6-SY2026` は件数 probe で 106 頁 (21,040 件) と分かり、満量の 1 窓 (施錠せずに出せるのは 96 頁) にも収まらないため
起動していない。** 依頼と D2095 項 3 の前提「各 20 頁前後、1 窓で収まる」は SY2026 について成立しない。

**軸 1 は `未完走` であり、成熟度は `RW1` のまま。論文は世界の不在を主張しない。**

凍結した実行記録は `docs/related-work/claim-survey/2026-09-17b-axis1-search-execution.md`。
5 窓目は `output/insights/2026-09-17/t2035-axis1-openalex-window5/`、
4 窓目は `output/insights/2026-09-08_t2090-axis1-openalex-window4/`。

## 中身

| file | 中身 |
|---|---|
| `manual-a.jsonl` / `manual-a-sy2025.stdout.json` | 親が手動起動した正規 runner 1 本の台帳 (cwd、argv の逐語、rc、state、reason_code、request 数、起動前後の残量、時刻) と stdout。argv は 5 窓目の dry-run (`driver-dryrun.txt` 8 行目) の逐語で、`--run-id` だけ `t2035-openalex-20260917b` (同日 2 窓目) |
| `liveness-probe-1.txt` | 取得前の生死確認 (無 filter、`per-page=1`、1 credit) の rate limit header の逐語 |
| `count-probe-sy2026.txt` | `Q6-SY2026` の登録 filter を `per-page=1` で 1 本投げた件数 probe の URL・header・`meta` の逐語。**証拠外** (取得器を通していない)。filter 付き検索は `per-page=1` でも 10 credit |
| `registration-check.json` | fetch-tree (登録 commit `4ec3eba04` を detach した木) での `tools/check_axis1_search.py registration` の出力 (`passed: true`) |
| `bundle-check.json` | 取得後の `tools/check_axis1_search.py bundle` の出力全文 |
| `evidence-detail.txt` | `Q6-SY2025` の証拠の射影: 頁ごとの申告総数・実要素数・頁内重複、pass 1 台帳の occurrences / distinct、頁境界を跨ぐ重複の再計算 |
| `leaf-states.txt` | `bundle-check.json` の leaf 診断から数えた OpenAlex 78 leaf の状態分布と、`complete` 以外の全 leaf の行 |
| `leaf-order.txt` | catalog の登録順の OpenAlex leaf 78 本 (窓 5 と同一、catalog から再導出して一致確認) |
| `project-window6.py.txt` | `evidence-detail.txt` / `leaf-states.txt` を bundle の現物から書いた使い捨て script の逐語 (親が job dir に書いて repo 外で実行、bundle と bundle-check.json の読み取りのみ。5 窓目で親が ad-hoc に計算した射影と同じ役で、repo の実装面には入れない) |
| `mirror/` | 生 bundle の部分複製 (`state/runtime.json` / `manifest.json` / `MANIFEST.sha256`)。`checkpoints/` は本窓で増減がなく、窓 5 の `mirror/checkpoints/` (67 本) と byte 一致なので複製していない |

## 生 bundle の所在

live bundle root (再開と検証はここで行う):
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (399 MB、窓 5 終了時 296 MB)

`manifest.json` の SHA-256 = `06fbef369ed0bfb071e896d65ee1c1a2321709f5cb8cc787374da7aafbed21dd`
(走行前は `a6a42514e6d52c4e90243e706295f3ce215f4f5c91c0ad100a7d90f32d22e2a4` = 窓 5 の走行後値。無傷を確認してから起動した)。

`mirror/` は `raw/` `pages/` `ledgers/` `checkpoints/` を除いた複製で、**単独では `verify_bundle` を通らない**。

## 何をしたか

### 1. 起動の条件

- cwd は登録 commit `4ec3eba04` を detach した木 (窓 5 が `git worktree add --detach` で作った repo 外の
  fetch-tree `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2035-axis1-openalex-window5/fetch-tree` をそのまま使った)。
  登録検査は `passed: true`。
- 窓は 5 窓目 (残量 69、リセット 9/17 09:00 JST) の後 1 request も出しておらず、満量だった。生死確認 (21:35:37 JST):
  `x-ratelimit-remaining=999`、`x-ratelimit-reset=41063` (= 2026-09-18 09:00 JST)。
- 持続観測 (`state/runtime.json`) は前窓の 69 のままだが、取得器の発行規範 `remaining − 30 ≥ 10` は 69 でも 1 本目を
  通し、以後は header で更新される。窓 5 と同じく手動 1 本で観測を更新する必要があった。
- 駆動 loop は使っていない。対象が 2 leaf だけなので、親が正規 runner の argv を逐語で 1 本ずつ起動した
  (窓 5 の `manual-first` と同じ型)。裁定待ちの 4 leaf (`Q6-SY2014` / `SY2015` / `SY2021` / `SY2024`) と
  独立 2 走目 53 本は起動していない。
- 起動前条件「残量 ≥ 40 + 10 × 頁数」は `Q6-SY2025` で 999 ≥ 40 + 10 × 51 = 550 を満たしていた (頁数は走行後に判明。
  起動時は前窓の見込み「20 頁前後」で判断した)。

### 2. 結果

| 起動 | leaf | 頁 | state | reason_code | 残量 |
|---|---|---|---|---|---|
| 手動 | `Q6-SY2025` | 51 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` | 999 → 489 |
| (起動せず) | `Q6-SY2026` | 106 (件数 probe) | — | — | 489 → 479 (probe 10 credit) |

起動は 21:36:00〜21:39:35 JST (約 4 秒/頁)。新しい checkpoint はない (`blocked_on_ruling` は再開点を残さない)。
残量は 479 で止め、次窓の手動更新 1 本が出せる状態を残した。持続観測は runner の最終値 489 のまま
(件数 probe は取得器の外なので runtime.json に載らない)。

### 3. `Q6-SY2025` — 申告総数は一定、頁境界の重複 25、不足 12 件

`evidence-detail.txt` の数値。

| leaf | 申告総数 (全 51 頁一定) | occurrences | distinct | 頁内重複 | 頁境界を跨ぐ重複 | 不足 | 結果 |
|---|---|---|---|---|---|---|---|
| `Q6-SY2025` | 10065 | 10078 | 10053 | 0 | 25 | **12** | `blocked_on_ruling` |

- 窓 5 の `Q6-SY2021` / `SY2024` (不足 1 件) と同じ条件 5 の形で、規模が大きい (申告総数は 2024 年の 4669 の
  2.2 倍、不足も 12 件)。頁境界を跨ぐ重複は 25 occurrence あり、頁内の重複は 0。
- **条件は緩めていない。** 取得器は `blocked_on_ruling` にしており、本走行はその判定をそのまま記録している。
- 検査器の leaf 診断は窓 3〜5 と同じく `leaf_page_evidence_missing` (`expected_passes=[1, 2]` に対して pass 2 が無い
  方が先に立つ)。走行時の理由は台帳側 (`manual-a.jsonl`) に残る。

### 4. `Q6-SY2026` — 106 頁で 1 窓に収まらない、起動すると bundle が自己施錠する

`Q6-SY2025` の 51 頁が前窓の見込み (20 頁前後) を大きく超えたので、`Q6-SY2026` は起動前に頁数を実測した。
登録 filter と同じ request を `per-page=1` で 1 本投げると `meta.count = 21040` → 200 件/頁で **106 頁 = 1060 credit**。

- 取得器の発行規範は各 request の前に「持続観測の残量 − 30 ≥ 10」を見るだけで、`x-ratelimit-reset` を見ない
  (U12)。残量 R から施錠せずに出せるのは ⌊(R − 40) / 10⌋ request (満量 1000 で 96、生死確認後の 999 で 95。
  次の 1 本は出せるが残量が 40 を切る) であり、106 頁の leaf は**どの窓からでも**途中で `paused_quota`
  (`continue_cursor`) に入り、持続観測が 40 未満のまま固定される。以後は窓がリセットしても
  観測を更新する 1 本が出せず、**bundle 全体が二度と request を発行できない** (U12 が登録した既知の穴)。
- 残量 479 から起動しても同じ (44 頁で止まり残量 39)。CLI に頁数上限はない。
- したがって本 wave は起動していない。取得には窓またぎ設計 (U12、取得器の変更 = 登録 tool の変更) か catalog 側の
  再分割 (amendment、新 epoch) が要り、どちらも本 wave の scope 外である。**D2095 項 3 の「1 窓で収まる」は
  見込みであり、実測で覆った。** 裁定パッケージへ新事実として返す (下記)。
- 件数 probe は 10 credit だった (`x-ratelimit-credits-used: 10`)。無 filter の生死確認 (1 credit) と違い、
  filter 付き検索は `per-page` に関係なく 10 credit である。

### 5. 打ち切り時点からの状態の変化 (OpenAlex 78 leaf)

| 状態 | 窓 5 終了時 | 本窓終了時 |
|---|---|---|
| `complete` (独立 2 走まで完了) | 8 | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 | 53 |
| 条件 5 で未完走 (再開点なし、`Q1` / `Q4` / `Q5`) | 3 | 3 |
| 2 走不一致で未完走 (再開点なし) | 6 | 6 |
| 条件 5 で pass 1 が落ちた (再開点なし) | 4 | **5** (+`Q6-SY2025`) |
| `declared_total_drift` で pass 1 が落ちた (再開点なし、裁定待ち) | 2 | 2 |
| 未走 | 2 | **1** (`Q6-SY2026`、1 窓に収まらない) |

検査器は `bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` (rc=2)。

## 裁定パッケージへ足す新事実 (D2095 の包み)

- **項 3 の訂正:** 未走 2 leaf のうち `Q6-SY2026` は 106 頁 (1060 credit) で、現行の取得器では 1 窓に収まらず、
  起動すると bundle が自己施錠する (U12)。選択肢は (a) `Q6-SY2026` を未走のまま置き、軸 1 の材料は 77 leaf 分で
  「限定付き」とする (成熟度は元々 `RW1`)、(b) U12 の窓またぎ設計を実装する (取得器 = 登録 tool の変更、
  D1207 の意味的 amendment に当たるかの判定を含む)、(c) catalog 側で `SY2026` を半期などに再分割する (amendment、
  新 epoch)。親の推奨は (a) — 2 走目の扱い (項 1) が (a) なら軸 1 は `RW1` のままで、SY2026 1 本のために契約を
  動かす理由がない。
- `Q6-SY2025` は条件 5 で落ちた (不足 12 件)。項 2 の「落ちた leaf」に加わる (据え置きの推奨は変わらない)。

## この wave が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。**repo の実装面の差分は 0。** 駆動 loop も書いていない。
Codex 子は起動していない (軽量版、子ゼロ)。
