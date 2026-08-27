# [T-1981] 性能測定の一回性を予約経路から撤去し、測定世代へ置き換えた

D1124 の実装 wave。本書は実測と裁定の所在を示す索引であり、状態の正本ではない
(状態は worklog 末尾、設計判断は decisions が正本)。

## 何が変わったか

過去の観測を理由に予約を拒否する関門を撤去し、**予約ごとに発行する測定世代**へ置き換えた。
cell の効果 key (6 field) は座標として不変のまま維持し、`O_EXCL` と attempt 一回性を
世代の内側へ限定した。世代 ID は `sha256({observation_role, campaign_run_id})` で
決定的に導出する。承認 flag `--confirm-irreversible-pilot-holdout` と env 伝播は
floor 経路から撤去した。

## 実測 (すべて親が採取)

### 台帳の実物

共有 admission root (`.git/izanagi/s8b-holdout-admission-v1/`) の投入時点の状態。

| 対象 | 件数 |
|---|---|
| cell claim | 36 (floor 12 / n_pilot 12 / oracle_driver 12) |
| attempt consumption marker | 228 (うち floor の 12 claim digest 配下が **96**、1 cell あたり 8) |
| `ledger.jsonl` | 36 行 |

D1124 が名指しした「12 cell」は `observation_role = floor_campaign` の 12 件で、すべて
`campaign_run_id = 20260824T205358Z-2c8cf9be`、`mode = pilot`。

### D1124 の前提の訂正

D1124 の「実害」節は当該 run を「途中死」と記すが、一次資料
(`output/insights/2026-08-25_t1431-floor-pilot-values/README.md`) では **driver_rc=0 で完走**し、
96 attempt すべてが `valid=True`、床値の実測値も出ている。成果物は repo 外の
evidence bundle へ意図的に退避されていた。**決定は覆らない** — 中核の論拠は run の生死に
依存しない。成果物影響が「床値が 1 つも出ない」ではなく「同じ cell を測り直せない」である点だけが変わる。

### 実機投入 (P4)

| | 撤去後 tip | main 単独 |
|---|---|---|
| request | `952615.nqsv` | `952631.nqsv` |
| 承認引数 | **なし** | あり (main の現行手順) |
| `qsub -v` の承認 env | **載らない** | 載る |
| 失敗までの時間 | 67 秒 | 62 秒 |
| 失敗段 | binary admission receipt | binary admission receipt |
| エラー本文 | `compiler input manifest の完全検証に失敗: external compiler input is unavailable` | **同一** |

投入元 checkout の `git rev-parse --path-format=absolute --git-common-dir` は
`/work/1/SFC/tanab/izanagi/.git` (実測)。共有 admission root を見ており、恒真な受入ではない。
台帳の 12 claim と 96 marker は残したまま投入した。

**判定:**

1. 撤去は実機で効いている — 承認なしで投入でき、`already consumed` は出ない。
2. **ただし cell 予約に到達していない**ため、12 cell が再測定を妨げないことの実機証明は無い。
3. **本 wave の回帰ではない** — main 単独で本文と失敗段の両方が一致する赤が出る。
4. **床値実測を止めるものが一回性から別の欠陥へ移った。** 2026-08-27 05:54 の job `951456` は
   この段を通過して 350 秒地点の予約段まで到達していた。

### テストと変異

- 焦点走 (17 file) = **1529 passed / 12 skipped**。残る 1 件は file 選択走の import path 未確立に
  よる非帰属の偽赤。
- `tools/check_docs.py` rc=0、`tools/check_ai_provenance.py` rc=0。
- 変異 matrix = baseline **PASSED** (rc=0・赤 0 件)、**KILLED 5 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0**。
  期待 node は probe 走 (全件 SURVIVED 期待) の観測から完全集合で登録した。

| 変異 | 期待 node 数 |
|---|---|
| 世代 ID を乱数へ戻す | 172 |
| 新世代 marker を旧 `consumed/` へ戻す | 91 |
| resume の cell claim identity 照合を無効化 | 1 |
| resume の ledger identity 照合を無効化 | 1 |
| 旧 marker の historical 解決を壊す | 6 |

最後の 1 件が殺す node には、旧 claim 12 件・旧 marker 96 件を配置して最初の attempt 消費まで
通す統合テストと、旧 bytes の inspection 5 本が含まれる。**「旧 bytes の可読性を温存した」が
空手形でないことの証拠である。**

## 選択側の防壁について (恒真な保証を作らないための記録)

段 3 レンズ A が「反復可能化だけを先に入れると、値を見た後に採用測定を選べる」を real で挙げた。
親は **real だが現時点で到達不能**と裁定した。根拠は次の 2 つだけであり、
**いずれも official が解禁されたら消える。**

- `orchestrator/campaign/s8b_floor_campaign.py:453-462` の `_assert_official_permitted()` が
  production で official を無条件拒否する (§8 未裁定)。呼び出しは `:6989` と `:7096`。
- `orchestrator/campaign/s8b_holdout_freeze.py:1617-1618` が
  `result.eligible_for_refreeze is not True` なら `FreezeError` を投げる。pilot は false。

`--floor-result` は `s8b_holdout_freeze.py:1884` で**呼び手指定の必須引数**であり、
複数の完走測定があればどれを再凍結へ渡すか選べる。D893 が要求した機構
(launch reservation / run nonce / terminal tombstone) は [T-469] として**未実装のまま**である。

**したがって「同じ試行を複数実行先で走らせて良い値を選ぶ」経路には、現在いかなる実装防壁も無い。**
本 wave はここへ恒真な保証を新設せず、事実として記録した。棚卸しは後続タスクの scope である。

## 逐語

- `verbatim/s2-plan.md` — 段 2 プラン起草
- `verbatim/s3-consult-sol.md` / `verbatim/s3-consult-luna.md` — 段 3 敵対相談 2 レンズ
- `verbatim/s4-adjudication.md` — 段 4 裁定 (11 節 + 変異事前登録)
- `verbatim/s5-author-a.md` / `verbatim/s5-author-b.md` — 段 5 実装子 2 本
- `verbatim/s6-review-sol.md` / `verbatim/s6-review-luna.md` — 段 6 敵対レビュー 2 本
- `mutation-spec-final.json` — 変異 spec (本走)

**変異の走行結果 JSON は repo 外へ退避した。**
`mutation-final-result.json` と `mutation-probe-result.json` は失敗 node の本文に holdout の
workload 条件 (`rr20`) を含み、`test_wave_files_do_not_contaminate_production_holdout_scan` の
holdout clean-scan を汚染する (実測: 受入全走で 41 件の赤。うち 39 件は oracle gate が
scan hit で追加の拒否理由を出し、拒否理由の exact 一致を固定するテスト群が落ちたもの)。
所在は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mutation-final-result.json`
と同 directory の `mutation-probe-result.json`。
**変異結果を repo の insight へそのまま置いてはならない。**
