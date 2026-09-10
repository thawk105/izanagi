# handoff — dev-wave t1336/t1337/t1347 再凍結 (2026-08-18)

- wave: `dev-wave-t1336-t1337-t1347-refreeze`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze`
- branch: `worktree-dev-wave-t1336-t1337-t1347-refreeze` (base main = a160f4aa)
- job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/`
- 開始: 2026-08-18 12:22 JST

## 状態

段 1 brief 作成済み。段 2 未着手。

## 段 1 brief

### scope

2026-08-18 のユーザー裁定 3 件が要求する事前登録の改訂を、**1 回の再凍結**として発効させる。
成果物は改訂文書と凍結 record までで、実装 (コード・テスト) は後続 wave へ分ける。

1. **[T-1336]** 最終判定から床値 (between-run floor) との比較を撤去し、**反復単位の対比とその分散**を
   判定の基礎に置く。順位の事実と性能主張を二層に分け、公式の性能主張は生値側に置く。
   走行内変動係数をそのまま閾値化する形は採らない。共分散は manifest の replicate 添字と
   observations の schedule 添字から復元し、`orchestrator/campaign/s8b_oracle_n_pilot.py` の
   `_sample_covariance` / `_sample_correlation` を使う。8b §6 判定表 条件 3 は 2026-07-16 裁定
   (8b §9) の再裁定として本改訂が上書きする。
2. **[T-1337]** 8b §9 項 8 の resume 全拒否より D496 決定 3 を優先し、**freeze-wide の事前割当
   attempt registry** へ改訂再凍結する。測り直しの単位は campaign 全体でなく**落ちた構成だけ**。
   観測済み値を後から差し替える経路は registry でも許さない。
3. **[T-1347]** role payload の closed key set から**真の workload 名を落とす**契約へ変える。
   `off` arm で role が作業種別を見ない形にする。

### 確定済みユーザー裁定 (再議しない)

- 裁定控え: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-18-rulings-full7-15rulings.md`
- 台帳 fragment: 未 land branch `worktree-rulings-20260818-floor-measurement` tip `fe56f5f7`
  (`docs/spool/worklog/2026-08-18-...-1.md` / `docs/spool/decisions/2026-08-18-...-2.md`)
- 正本: `docs/decisions.md` D496、`output/insights/2026-08-18_t1311-arm-execution-authority/README.md`
- D496 決定 3 の改訂 (落ちた構成だけ測り直す) は上記 decisions fragment の
  `{{D:remeasure-only-failed-configuration}}`。番号は land 時採番。

### brief 前の実測 (DW-S01)

| 事実 | 実測結果 |
|---|---|
| 8b 設計文書の bytes pin | `output/s8b-freeze/holdout_freeze.json` の `design_source.sha256` = `1829af7f…`、worktree 現物 = `5fbdd7ef…` (既に不一致) |
| その照合の現在地 | `orchestrator/campaign/freeze_verification_hold.HELD = True` (ユーザー裁定 2026-08-12)。check id `s8b-holdout.design_source-implementation-bytes` ほか 21 件が保留中 → **8b 文書の編集は凍結鎖を壊さない** |
| 8c 条件契約の世代 | `output/s8c-preregistration/condition-freeze/` は g1〜g5。tip = g5、`decider_version = s8c-decider/v2`、`ruling_reference = D441` |
| 次世代の生成手段 | `python3 -m orchestrator.campaign.s8c_preregistration prepare --ruling-reference <D> --revision-reason <理由>` が exclusive-create で g6 を書く |
| 世代番号を pin するテスト | 無し。`test_s8c_preregistration_invariant.py` は `range(1, tip+1)` で連番検査、`decider_version` は module 定数と照合 → **テスト編集不要** |
| 対比分散の既存実装 | `s8b_oracle_n_pilot.py`: `_observation_matrix` が完全 block を要求、`summarize_sessions` が構成対ごとに `absolute_difference` / `relative_difference` の反復ベクトルと `_difference_summary`、`joint_covariance` / `joint_correlation` を出す。`_sample_covariance` は n-1 標本共分散 |
| replicate 添字の出所 | `s8b_oracle_manifest.build_schedule` の row が `schedule_index` / `replicate_index` を持ち、pilot は `pilot_round = replicate_index + 1` として使う |
| role payload の漏れ | `orchestrator/campaign/p3_autonomous_workload_trial.py:264` `_COMMON_PAYLOAD_KEYS` が `"workload"` を含み、`ROLE_PAYLOAD_ALLOWLIST_SHA256` が key spec を pin |
| docs 予算 | `tools/check_docs.py` の byte 予算は dev-wave 3 層のみ。8b/8c 文書は「living doc」列挙 (行 64-65) で予算対象外 |

### 不変条件

- **規律 2 を緩めない。** correctness gate (legacy + S2) は一切変えない。改訂は受理集合を
  広げない方向で書く。attempt registry は**事前割当**であり、観測済み値の差し替え・後出し登録・
  成績を見てからの再走選択を許さない。
- 8b が凍結する事項の変更は 8b §8 の手続き (旧凍結本文を残す + 変更理由 + ユーザー承認記録) を踏む。
- 8c §5 の**値セル**へ規範・条件を書かない (8c §4 記入規約)。規範は §4 側へ置く。
- 8c / 8b とも三軸 canonical 綴りを書かない (8c §0)。spool fragment・insight も同じ。
- 凍結 record は **g6 の 1 本だけ**。空改訂・二重世代を作らない。
- 実装差分ゼロ (コード・テストを編集しない)。実装面が必要と判明したら段 4 で scope を再裁定する。

### 成果物の形

1. `docs/phase3-8b-descriptor-design.md` — 新規 §10「再凍結 2026-08-18」。§6 判定表 条件 3 の置換、
   §9 項 8 の改訂、§5.2 floor bullet の帰結を、旧本文を残したまま上書き規定として書く。
2. `docs/phase3-8c-preregistration.md` — §3 表 (crash 行・判定基準行)、§4 (T-1347 の role payload
   契約 1 項、標本設計の floor 依存)、§4 記入規約 (floor 欄・env_tag 欄の解除条件)、§5 欄名、
   §6 前提条件 4・7 の改訂。
3. `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json` (`prepare` が生成)。
4. spool fragment (worklog 1 / decisions 1)、insight package。

### 親の provisional 裁定 (攻撃対象)

- **(P1)** 8b の再凍結は新規 §10 として**追記**し、§5.2 / §6 / §9 の旧本文は改変しない
  (§8 の「旧 freeze と変更理由を残し」に従う)。代案 = §6 表を直接書き換える。
- **(P2)** 8c §5 の「対象別 between-run floor (H1 / H2)」欄は**削除ではなく置換**し、
  反復単位対比の判定パラメータを持つ欄にする。どちらでも §5 欄名集合 hash は変わる。
- **(P3)** g6 の `ruling_reference` は `D496` とする。本改訂が改訂する対象決定であり、
  新 D 番号は land 時採番のため事前に確定できない。
- **(P4)** T-1347 の docs 面は 8c §4 へ規範 1 項を足す形。実装 (`_COMMON_PAYLOAD_KEYS` /
  `ROLE_PAYLOAD_ALLOWLIST_SHA256`) は後続 wave。
- **(P5)** 実装差分ゼロにつき変異 matrix は免除 (DW-S04)。受入全走は免除しない。
- **(P6)** 段 5 の Codex 実装子は起動しない (docs-only)。段 2・3・6 の read-only / review 子は
  受理集合が変わるため省略しない (DW-C00)。

### 成果物影響 (DW-G05)

- **T-1336 を実装しない場合:** 8b §6 条件 3 が未確定の floor に依存し続け、判定表の連言が
  永久に「判定不能」に留まる。6 cell の性能主張が 1 件も出せない。
- **T-1337 を実装しない場合:** crash した cell の再測定が機構に拒否され、campaign が事故 1 回で
  終端する。D496 決定 3 (改訂後) と §9 項 8 が正面衝突したまま、どちらに従っても他方を破る。
- **T-1347 を実装しない場合:** `off` arm の role が真の workload 名を見るため、6 cell の on/off 差を
  descriptor 効果として解釈できない。8b の主張自体が成立しない
  (insight `2026-08-18_t1311-arm-execution-authority` §6-1)。
- **1 回にまとめない場合:** 世代 record が 3 本に分かれ、裁定の条件に反する。中間世代は
  他 2 件を未改訂のまま条件契約として凍結してしまう。

### 並列分割方針

- 段 2: read-only codex 1 本 (file:line 粒度のプラン起草)。
- 段 3: 敵対 2 本 — レンズ A =「改訂が受理集合を広げる/規律 2 を緩める経路」、
  レンズ B =「凍結手続き・世代 record・機械検査との不整合」。
- 段 5: 親が docs を編集 (実装面ゼロ)。
- 段 6: 敵対レビュー 2 本 (実 diff に対して)、fix は親。

### 受入・実測の環境

- テスト: `python3 tools/run_tests.py` (受入全走、相対・素の argv ちょうど)。
- 焦点走: `orchestrator/tests/test_s8c_preregistration_invariant.py` ほか変更面の検査側。
- `python3 tools/check_docs.py`、全史 provenance 監査、fold dry-run を受入前に緑にする。

## dev-wave 改善候補

(段 8 で一度だけ裁定する。現時点で記録した候補: なし)

## 実行ログ

- 12:22 JST 起動、クラス 3 起動手順。main clean = a160f4aa、handoff は README のみ。
- 12:2x JST 裁定控え・D496・fragment・8b/8c 文書・凍結機構・pilot 実装を実測。
- 12:5x JST worktree 作成、submodule 再帰初期化、段 1 brief 確定。
