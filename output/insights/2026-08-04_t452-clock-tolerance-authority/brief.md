# 段 1 brief — [T-452] effective_clock.tolerance_pct の権威設計

wave: dev-wave-t452-clock-tolerance-authority / branch: `worktree-dev-wave-t452-clock-tolerance-authority`
worktree (repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-clock-tolerance-authority`
base = local main `a98916a` (worklog 末尾エントリ (185))。

## scope

`effective_clock.tolerance_pct` の**権威の設計案を起草し、裁定パッケージで返す**。本 wave は
**実装しない** (docs のみ)。実装は [T-419] U-1 (probe 実験) → U-2 (較正再取得) のサイクルが所有する。
[T-453] (silo_ladder_rung1 の median 比較 consumer) は別タスクの所有。設計案は射程を明記するだけで
実装案を確定しない。

## 確定済みユーザー裁定 (前提であり攻撃対象ではない)

- 2026-08-04 /rulings: 権威は **policy 固定値の方向**で設計する。実測 smoke 分布由来は採らない方向で
  起草し、最終形は設計案で確定する。
- D143/D155: **述語 (expected median ± tol% に observed 全要素) を正とする。** 述語を緩める案
  (中央値どうし比較・帯外 1 個許容) は裁定で却下済み。規律 2 により受理集合は広げない。
- D155 決定 (2): canonical 述語は `execution_guard.effective_clock_comparison_passes`。issuer
  (`env_attestation`) の独立実装は**意図的に残す** (相互裏取り)。統合案を出してはならない。

## 段 1 で実測した前提 (一次資料 = 現 worktree のコードと登録 artifact)

1. 述語 `orchestrator/campaign/execution_guard.py:182` = `allowed_delta = |median(expected)| * tol/100`、
   observed の**全要素**が帯内。`tol=100` → 帯 `[0, 2*median]`。したがって
   **literal な恒真ではなく「median の 2 倍超 (または負) の標本だけが落ちる」実質恒真**である。
   設計案はこの区別を正確に書くこと。
2. 登録済み較正 `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`:
   48 標本のうち 47 個が 2101.0、1 個が 3080.935 (median から **+46.641 %**)。
   `tolerance_pct=2.0` でも `5.0` でも self-comparison は **False**。通すには **tol ≥ 46.65 %** が要る。
   → 「現 artifact が通る policy 値を選ぶ」道は物理的に無い。`quality.status` は `accepted`。
3. observed 側 probe は `orchestrator/campaign/env_attestation.py:439` で `tolerance_pct=100.0` を
   **sentinel** として書く (「実行時観測は自前の policy tolerance を持たない」)。schema
   `EffectiveClockProfile` は expected/observed 共用のため、**schema の上限を狭めると sentinel が
   schema 違反になる**。この構造的衝突が設計の核心。
4. 取得時 gate `orchestrator/calibrator/cli.py:381,608`
   (`effective-clock-self-comparison-failed`) は **publish される profile 自身の tolerance** で
   自己比較する。CLI に 100 を渡せば gate も自明に通る。
5. 境界検査は 2 箇所のみ: CLI `cli.py:487` `(0,100]`、schema `schema_v2.py:236-239` `(0,100]`。
6. 凍結 bytes の pin 閉包 (DW-O09): `env_contract.py:186-192` (path + sha256)、
   `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の binding (path + sha256 +
   contract_sha256)、`test_env_contract.py` 3 site、`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` 1 件
   (`test_env_contract.py:436-463`、T-419 U-1/U-2 で削除予定)。**`FROZEN_MANIFEST` に `output/env/`
   は 1 件も無い。** 本 wave はこれらの bytes を変えない。

## 不変条件

- 凍結 bytes・pin・受理集合を本 wave で変えない。コードもテストも編集しない (docs のみ)。
- 述語を緩める案・attestation を外す案・issuer 統合案は出さない (裁定済み却下)。
- 設計案は「実装しないと成果物の何がどう変わるか」(DW-G05) を各項目に 1 行で書く。

## 成果物の形

`output/insights/2026-08-04_t452-clock-tolerance-authority/` に設計案 README (裁定パッケージ = U-1…
の設計択一形式) + 子の逐語 + prompt、`docs/spool/` に worklog fragment。commit は親のみ。

## 親の provisional 裁定 (P1)〜(P5) — **すべて攻撃対象**

- **(P1)** 権威は repo 内の単一 policy 定数に置く。CLI `--effective-clock-tolerance-pct` は
  撤去、または「policy と一致することの検査」へ降格する。
- **(P2)** 固定値は **2.0** (現行登録値と同値) を第一候補とする。根拠は「governor=performance の
  定格から外れたコアが無い」という述語の意図であり、smoke 分布ではない。
- **(P3)** observed の sentinel `100.0` は「tolerance を持たない」ことの型で表現する
  (observed 側で optional / 専用型)。schema 上限を狭める案とは排他。
- **(P4)** 恒真化を塞ぐ機械は「値域を狭める」ではなく「権威の一元化 + observed に tolerance を
  持たせない」で行う。値域を狭めるだけでは publish 経路の手入力権限が残る。
- **(P5)** 本 wave は実装しない。実装は T-419 U-1 → U-2 のサイクルへ同梱する。

## 成果物影響 (DW-G05)

実装しない場合、較正の再登録が**権威なき手入力の tolerance** で行われうる。100 を渡せば取得時
gate も実行時述語も実質恒真になり、certified 選択が依拠する「計測環境が登録時と同じ」という
proof chain の主張が**受理集合を持たない**まま campaign 実行が通る。

## 分割方針

段 2 = codex read-only 1 本 (設計案起草)。段 3 = 敵対 2 レンズ並列。段 4 = 親裁定 (実装しない →
4→7→8→9)。段 7 = 親が記録。
