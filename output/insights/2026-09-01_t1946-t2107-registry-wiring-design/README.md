# [T-1851 前半] + [T-2107] + [T-1946] — 試行台帳の配線と proof chain 束縛の設計

2026-09-01。branch `worktree-dev-wave-t1946-t2107-registry-proof-wiring`、
base `2bf9cf387` (着手時 local main) から `e1e53d7db` へ ff 済み。**実装面の差分はゼロ。**

この wave は「実装する」指示で始まったが、段 4 の 2 巡目で**本 wave では実装しない**と裁定した。
成果は、4 本の独立検査を通した実装可能な設計と、残る 13 件の blocker への具体的な修正案、
および次 wave が段 5 から始められる材料である。

## 中身

| file | 内容 |
|---|---|
| `brief-v2.md` | 差し替え版の親 brief。scope・与件・親裁定・実アンカー |
| `s4-adjudication-r1.md` | 段 4 裁定 1 巡目。所見 18 件の採否、親裁定 6 件、親 brief の訂正 8 件 |
| `s4-adjudication-r2.md` | 段 4 裁定 2 巡目。**本 wave の終端裁定**。所見 21 件の採否、親裁定の具体化訂正、裁定パッケージ |
| `parent-findings.md` | 親の独立実測と、plan が引いていない既裁定 (D880 / D1032 / T-1851) |
| `overlap-scan.txt` | 編集面の重なり走査の証跡 (走査時刻・main head・各 worktree の head/base/変更数) |
| `verbatim/s2-plan-v1.md` | 段 2 plan 1 巡目 (前提が誤っていた版) |
| `verbatim/s3-r1-lens-a.md` `verbatim/s3-r1-lens-b.md` | 段 3 検査 1 巡目 (所見 A-1〜A-9、B-1〜B-9) |
| `verbatim/s2-plan-v2.md` | 段 2 plan 2 巡目 (**次 wave の出発点**) |
| `verbatim/s3-r2-lens-a.md` `verbatim/s3-r2-lens-b.md` | 段 3 検査 2 巡目 (所見 A2-1〜A2-8、B2-1〜B2-13) |

## この wave が確定したこと

### 1. 対象は 2 件ではなく 3 件の閉包だった

T-2107 の配線は **T-1851 の前半と同一の作業**である。T-1851 の段 4
(`output/insights/2026-08-27_t1851-floor-retry-ordinal-axis/s4-adjudication.md`) が次 wave へ渡した
骨格の前半が、逐語で「launcher / campaign 配線、final inspector / verifier までを同時に land する」
と書いている。T-1851 は D1193 / D1194 で裁定済み・実装待ちである。
D1341 と T-1851 段 4 の「書き手と検査を別々に land する分割は不可」が、3 件を 1 commit へ束ねる。

### 2. 裁定済みの proof の形だけでは束縛が恒真になる

D1337 が定めた `{row_count=N, chain_head_at_N}` の prefix 証明は、**genesis 1 行だけの台帳でも、
別 campaign の台帳でも検証が通る。** 4 本の独立検査がこれを実測した。
その result 自身の試行が 1 件も入っていない台帳を束縛して certified になり得る。
これは D1194 が却下した「台帳の欠落を許したまま追跡を謳う状態」そのものである。

親は「被覆の追加は D1337 の変更ではなく D1194 の実装である」と読んで採用したが、
**ユーザーが覆せる裁定として返す** (`s4-adjudication-r2.md` の裁定パッケージ 2)。

被覆の実装は、集合等値では足りない。比較の片方が producer 由来だと恒真のままなので、
schedule と admission claim から独立に導出した authoritative な planned attempt 集合と、
全単射で照合する必要がある (A2-6 + B2-1)。

### 3. 配線に必要な入力 6 件は、いずれも解がある

分類権限 (新設)、profile 構築用の回復権限 (既存の scheduler accounting authority を流用)、
run-start receipt digest、admission claim digest の公開射影、測り直しの ordinal 軸
(D1032 + T-1851 段 4 の承認済み読み)、consumption marker の path 不一致。
詳細は `s4-adjudication-r1.md` の親裁定 4。

分類権限は**新しい信頼の根**にあたるため、ユーザーが覆せる裁定として返す。

### 4. 理由の機械導出は、規則としては既に凍結されている

現行 campaign の `excluded_reason` は、凍結閾値を使う単一の純関数
`s8b_floor_stats.assess_session()` と固定の優先順位で決まり、自由選択は無い
(`s8b_floor_campaign.py:6078-6109`)。D1032 の「性能量に到達する前に理由を固定する」は、
**規則の凍結**という意味では現行コードでも満たされている。

両レンズが指摘したのは**信頼境界**であり、導出を実行しているのが campaign (信頼境界の外) だという点。
修正は同じ純関数を launcher 側から呼ぶだけで済む。

### 5. 共有 admission root に 2026-08-27 の実装試行の残骸がある

Git common dir 配下の共有 admission root に、schema v1 かつ 2 段 path の台帳 (193 行 =
freeze 1 + start 96 + seal 96、12 budget key ごとに start 8 件) と consumption catalog (96 行) が
実在する。mtime は 2026-08-27 19:53:23 で以後不変。この 2 段 path を書ける code は main に無い。

凍結 hash は本番の値ではなく、本番 campaign にも通常 test にも影響しない
(test は一時 Git repository を作る。レンズ B が refuted と判定)。**削除も書換えもしていない。**

### 6. 規模と土台

更新テストは AST 静的計数で C-family 103 node + D-family 117 node = 220 node に達する。
変更行数は 2,650-4,000 行超。実装単位は `B1 → A → B2 → D1 → C → D2` の 6 段
(plan v2 の A→B→D→C→D 順は、A が受ける marker capability を B が後から定義するため不成立)。

さらに、本 wave の編集面 2 file を稼働中の 3 wave が同時に触っている。
先にそれらを着地させないと統合の基準が定まらない。

## 次 wave の出発点

1. 稼働 3 wave (t2027、t2074 の 2 系統) の着地を待つ。
2. `verbatim/s2-plan-v2.md` を土台に plan v3 を起草し、
   `s4-adjudication-r2.md` の 13 blocker と 6 段分割の境界 (symbol・引数・戻り型) を確定する。
3. 6 段を順に unlanded checkpoint として作り、統合後に 1 commit だけ land する (D1341)。

変異事前登録は plan v3 の確定と同時に行う。plan v2 の候補 9 件と、
A2-7 の再照準 (M6・M9)、A2-3 の追加負例 (第 11 start が拒否される) が出発点になる。

## erratum — 逐語の可逆最小正規化 (DW-S07)

`verbatim/s2-plan-v1.md` は行末に半角空白 2 個 (Markdown の強制改行) を持つ行が 6 行あり、
`git diff --check` に抵触した。**可視文字を変えない可逆最小正規化**として行末空白だけを除去した。

- 原文: sha256 `42a1c879aff0255eb4cfac99a0ab1f671cac6f53543bc0bb5ede50a45b8c2457`、33800 bytes
- 正規化後: sha256 `4991af178c7ca4a4166f54ffa8498af2f0c0fb2f3480cf9627ebeccf18abb990`、33788 bytes
- 除去した bytes: 12 (6 行 x 半角空白 2)
- 復元法: `## テスト計画` の `### 正例` 節にある、行末が test node id で終わる 6 行
  (`test_protocol_generations_use_distinct_paths_under_one_freeze`,
  `test_freeze_budget_replay_allows_total_at_limit_across_protocol_generations`,
  `test_current_measurement_generation_marker_launches_one_planned_attempt`,
  `test_attempt_registry_capture_returns_full_binding_positive_count_and_tail_head`,
  `test_v5_prefix_proof_survives_valid_later_append`,
  `test_historical_reverify_accepts_v4_without_attempt_registry`) の末尾へ半角空白 2 個を戻す。
- 他の 5 つの逐語 file には行末空白が無く、正規化していない。
