# 段 1 brief — [T-2001] 凍結した B-4 分析契約を実行する経路

base main `343b8f5a5` / branch `worktree-dev-wave-t2001-b4-analysis-path`
wave slug `t2001-b4-analysis-path`

## 確定済みユーザー裁定 (この wave の入力。覆さない)

- **D1140**: 規則は凍結済み。実体の生成は「凍結済み規則の機械適用」であって新たな凍結判断ではない。
  規則の外で母集合を選び直さない。実体を見てから規則を変えない。
- **D1141**: `A_min = 0.60`、`n = 201`。`A_min` は必要数の導出にだけ使い判定の閾値にしない。
- **D1142**: verdict は全域関数。入力検証を**すべて**済ませてから分岐評価を始める。
  4 分類は 成立 / 不成立 / 判定不能 / protocol violation。
  `registry_violation_count > 0` は 1 件でも実験全体を protocol violation にする。
- **D1143**: 演算の欄は実行経路が実在するまで埋めない。
- **D95**: 実装面の author は Codex。親は実装面を直接編集しない。
- 規律 2 を緩める方向 (検査を甘くして通す) の変更は採らない。

## brief 前に実測した現状 (推測ではない)

1. `scheduled_attempt_registry` / `analysis_manifest` / `analysis_invalid` / `design_not_feasible` の
   4 語は、repo 内の **Python にも JSON にも 0 件**。docs では
   `docs/phase3-b4-reflux-ablation-preregistration.md` 1 件のみ。**実装は存在しない。**
2. `treatment_fired` / `assignment_followed` / `precursor_hash` は repo 全体で **0 件**。
   `reference_tps` は `orchestrator/qualification/contract.py:332` の
   `observe_relative(subject_tps, reference_tps, floor)` の引数名としてだけ実在する。
   同関数は `subject/reference - 1` を取り floor を乗法境界で比較する既存実装であり、
   §5.1.1 の「利得の差の絶対値が floor 以下なら tie」とは**境界の取り方が違う** (片側 bit を返す)。
   流用の可否は段 2 で file:line 単位に判定させる。
3. `whiteboard.result` の値域は実装上 `success | fail | rejected` の 3 値
   (`p3_s4_loop.py:744` `assert_whiteboard_value_domains`、`_WB_VALUE_DOMAINS`)。
   §5.1.1 の block `status` 4 値 (`certified/rejected/aborted/missing`) とは**別の型**である。
   adapter はこの写像を担う。段 4 の `delta_pct` は `None` 固定 (`state_from_dict` が強制) で、
   throughput は whiteboard に載らない。
4. §5 の欄ラベル 10 件は `orchestrator/campaign/p3_b4_admission_record.py:60-71` に
   **exact literal で pin** されている。実走前検査は「値セルが非空で予約 sentinel でない」
   ことだけを見る (同 file の `_SECTION5_SOURCE_CELL_CONTRACT_FAILED` の文言が自ら明示)。
   D1143 の懸念はここで実測として裏が取れる。
5. `docs/phase3-b4-reflux-ablation-preregistration.md` は `tools/check_docs.py:146` に
   **living** として登録済みで、whole-file SHA-256 pin は掛かっていない。
   `FROZEN_MANIFEST` (`orchestrator/tests/test_frozen_artifacts.py:41`) に `p3_b4_*` は **0 件**。
   → **DW-O09 は成立しない** (凍結成果物の bytes を変えない)。
6. 既存の統計実装: `orchestrator/preregistration/stress_check_simulation.py` に
   `_clopper_pearson_upper` / `_regularized_beta` が実在する (numpy 依存)。
   `orchestrator/campaign/attempt_registry_core.py` に append-only 台帳の
   汎用核 (`chained_event_row` / `assert_registry_rows` / `load_attempt_registry`) が実在する。
7. 稼働中 wave の編集面 (未 commit + branch 差分の両方を走査済み):
   `t1769-b4-wiring-probe` = `orchestrator/campaign/p3_b4_wiring_probe.py` + 同名 test。
   `t1840-b4-launcher` = commit 0 件、段 4 裁定済み。同 brief の scope は
   `p3_s4_loop.run_one_iteration`・3 driver の `main`・新規起動器・事前登録 §7.2。
   **本 wave の新規 file 群とは 1 件も重ならない。**

## 純増 (この wave が新しく閉じるもの)

事前登録 §6 前提条件 9 は今 **4 項目とも不在**である (実測 1)。純増は、
**凍結済み文面 (§5.1.1) を実行する 4 経路を実在させ、文面と実装の一致を機械検査にすること**。
文面だけの分析契約で実走する経路を閉じる。

## scope (実装する)

- **(S1) 分析契約の型と純関数** — `orchestrator/campaign/p3_b4_analysis_contract.py`。
  §5.1.1 の入力 4 種 (`floor` / `contract_binding` / `registry_violation_count` / block 列)、
  `analysis_invalid` の理由 enum 11 種、registry violation 理由 enum 5 種、
  順位規則、block score、`A_hat` の**有理数 exact 計算**、厳密符号検定 (`p_on` / `p_off`)、
  `theta` の Clopper-Pearson 厳密両側 95% 区間、D1142 の全域 verdict (上から順・最初に当たった分岐で確定)。
  **入力検証を全件先に済ませてから分岐評価を始める。** file system・時刻・乱数・環境変数を参照しない。
- **(S2) adapter** — raw な試行記録から (S1) の入力型を作る経路。
  raw 側の schema を明示宣言し、fail-closed で検証する。
- **(S3) 契約文面との一致 consumer** — 実装が持つ閉じた集合と定数を、
  `docs/phase3-b4-reflux-ablation-preregistration.md` §5.1.1 の**文面から独立に抽出した**
  集合と exact 比較する。実装は定数を自前で持ち、文面から導出しない (恒真化の遮断)。
- **(S4) 2 台帳の生成器と再生成完全性検査** — `scheduled_attempt_registry` (append-only、全件、
  固定 enum の理由付き) と `analysis_manifest` (適格性述語・canonical 順序・先頭 n 行)。
  manifest が registry と生成器から再生成でき、**行集合と順序が exact に一致する**ことを検査する。
  適格行が n 未満なら `design_not_feasible`。
- **(S5) 割当無作為化 schedule と遵守検査** — block ごと独立に確率 1/2、実走前に決めて
  manifest へ固定する。実走後の schedule 変更と schedule 違反を protocol violation にする。
- **(S6) 負例検査** — 規律 2 を守る側の正例・負例を実体名指しで固定する。最低限:
  registry の protocol violation 行を manifest から外して洗い落とす経路、
  manifest の生成後の追加・削除・並べ替え、`A_min` を判定閾値へ流用する形、
  `missing` を除外する形、検証前に値を読んで分岐する形。

## scope 外 (実装しない)

- **`docs/phase3-b4-reflux-ablation-preregistration.md` の編集** (P1 を見よ)。
- §5 の値セルの記入。母集合の実体 (`analysis_manifest` の bytes) の生成。
- 対象 driver と軸の選定、floor 再実測、`PerfConfig` 校正、env_tag 確定。
- B-4 起動器・識別子の鋳造 (T-1840)、配線 probe (T-1769)。
- proposal producer と critic 決定の因果束縛 (§10 の未了項、D1146)。

## 親の provisional 裁定 (攻撃対象。段 3 の 2 レンズはここを狙え)

- **(P1) 事前登録 doc を 1 byte も編集しない。** 理由は 2 つ。(a) `t1840` が同 file の §7.2 を
  編集する scope を段 4 で確定済みで、ユーザーが「同じ file を編集する必要が出たらその wave の
  land を待て」と明示した。(b) D1143 が要求するのは「実行経路が実在するまで埋めない」であって
  「実在したら同じ wave で埋めよ」ではない。実在させた範囲と未記入の欄は worklog と
  insights へ記録する。**反証しうる形:** §6 前提条件 9 の充足が doc 側の記述なしでは
  第三者に検証不能なら、(P1) は成果物影響を持つ欠落になる。
- **(P2) adapter の入力 schema はこの wave が宣言する。** 実測 2 のとおり
  `treatment_fired` / `contaminated` / `protocol_ok` / `precursor_hash` には**現時点で producer が無い**。
  adapter はこれらを**必須 field として要求し、欠落を fail-closed で拒否する**。
  値を推定・既定値で補わない。producer の実装は t1840 系の起動器の領分として残す。
  **反証しうる形:** DW-O13 は「field が実環境で取りうる値を実測し、要求する値が到達可能か
  確かめてから述語を採用する」と定める。到達不能なら採用せず値域を裁定へ書く。
  この wave は「到達不能を fail-closed で拒否する adapter」を採るが、これが
  「到達不能な述語の採用」に当たるなら (P2) は差し替えを要する。
- **(P3) 一致 consumer は doc 文面を parse する。** 実装側が定数を自前で持ち、
  consumer が doc から独立抽出して exact 比較する向きにする。逆向き (実装が doc から導出) は
  恒真化するので採らない。**反証しうる形:** doc の日本語表現に依存する parse は脆く、
  doc の無害な字句変更で赤になる。その脆さが安全側か否か。
- **(P4) block score / 順位規則の tie 判定を `observe_relative` へ寄せない。** 実測 2 のとおり
  境界の取り方が違う (片側 bit)。§5.1.1 は「2 つの利得の差の絶対値が floor 以下なら tie、
  境界値は tie に含める」と両側かつ境界含みを要求する。**反証しうる形:** 既存関数を
  正しく合成すれば同値なら、重複実装は純減である。

## 不変条件 (破ったら停止)

- **`A_min = 0.60` を判定の閾値として使わない。** 必要数の導出にだけ使う (D1141)。
- **`n` を予算に合わせて切り下げない。** 適格行が n 未満なら `design_not_feasible` (D1141)。
- **`missing` を除外しない。** `rejected`/`aborted` の下位に置き、行そのものを落とさない。
- **`rejected` と `aborted` の間だけが常に tie。**
- **verdict は上から順に評価し最初に当たった分岐で確定する。** protocol violation が
  汚染より優先する (D1142)。
- **registry の protocol violation 行を manifest から外して洗い落とせない。** 件数を verdict の
  入力に渡し、1 件でも実験全体を失格にする (D1142)。
- 純関数は file system・時刻・環境変数・乱数・network・model・global state を参照しない。
- 既存 test の期待値を変更しない。marker 不在の通常走行の受理集合を 1 bit も変えない。

## 成果物影響 (DW-G05。scope 各項が無い場合に成果物のどこが変わるか)

- (S1) 不在 → B-4 の実験 verdict が人手の集計になり、certified 選択の根拠となる
  「成立 / 不成立 / 判定不能 / protocol violation」の 4 分類が再現不能な値になる。
- (S2) 不在 → 実走成果と分析入力の対応づけが人手になり、§7.1 の全件報告が検証不能になる。
- (S3) 不在 → 集計の実装が文面と違っても検出できない (D1143 の理由そのもの)。
- (S4) 不在 → file-drawer が開いたまま。不都合な campaign を台帳へ載せない経路が残り、
  レポートの母集合が事後に動く。
- (S5) 不在 → 帰無分布が二項分布にならず、p 値と信頼区間が意味を失う。
  レポートの `p_on` / `theta` 区間が根拠のない数値になる。
- 4 項目とも不在なら **§6 前提条件 9 が未充足で B-4 は実走できない** (台帳本文の逐語)。

## 並列分割方針

所有ファイルが素集合になるよう 3 単位。(S1) が型を定めるので**先行**させ、
限定 patch を展開してから (S2)+(S3) と (S4)+(S5) を並列投入する。

- 単位 A (先行): `orchestrator/campaign/p3_b4_analysis_contract.py` + 同名 test。
- 単位 B: `orchestrator/campaign/p3_b4_analysis_adapter.py` + 一致 consumer + 各 test。
- 単位 C: `orchestrator/campaign/p3_b4_analysis_ledgers.py` + 同名 test。

## 環境

login node での `python3 tools/run_tests.py` を既定とし、§7.0.0 の自動判定に従う。
受入全走は `tools/dev_wave_wait.py acceptance` 経由。計算ノードへの強制 dispatch はしない。
