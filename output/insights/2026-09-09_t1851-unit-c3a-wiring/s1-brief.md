# [T-1851] 単位 C3 — 段 1 brief (2026-09-09)

branch `worktree-dev-wave-t1851-unit-c2` を継承 (tip `38aed135f`)。**land しない (D1341)。**
7 単位が揃うまで branch 上の unlanded checkpoint に留める。

## 研究前進

床値 campaign の公式走行は今も試行台帳へ 1 行も書かず、result も v4 のままである
(親の実測: `launch_floor_attempt()` の production 呼び手 0 件、`s8b_floor_campaign.py` から
attempt registry への参照 0 件、`s8b_floor_contract.py:36` が `RESULT_SCHEMA = LEGACY_RESULT_SCHEMA`)。
このため D1032 が要求する「測り直しを台帳内の試行番号軸で追跡し、性能量に到達する前に理由を固定する」を
成果物で示せない。**最小差分は production 経路を launcher の certified 入口へ配線し、result を既設 v5
契約へ切り替えること。** 完了判定 = fake でない campaign → launcher → registry → result v5 の到達を
実 campaign 1 本で示し、gate 入力の実値域を記録する。

## 確定済みユーザー裁定と既裁定

- 単位選択はユーザーが親へ委任 (逐語)「単位 D2 ... など、裁定 2 の結論に沿って単位を選んでください」
  「判断に迷うところはcodexに相談して決めてください」。裁定 2 の結論 = **(a) 単位を割る** →
  配線と実値域を新単位 **C3** へ分ける。codex 相談 (read-only、`out-consult-unit.md`) も C3 を推奨し、
  依存順 `C → D2` を `s4-adjudication-r2.md:29,34` で裏取りした。
- D1341: 配線と proof chain 束縛は同じ変更単位で land する (片側 land しない)。
- D1703: 単位が揃うまで持ち越し裁定を個別に裁定しない。裁定待ちでも進行中作業は塞がらない。
- D1661: 主経路の単位 C を先に通す。journal の TOCTOU は本 scope に混ぜない。
- D1660: 旧世代 token の再検証入口は作らない。current-generation marker で新規実走する。

## scope (純増のみ)

1. campaign の直接計測経路を launcher の certified 入口へ配線する。
2. production result を v4 から既設 v5 契約 (attempt registry proof) へ切り替える。
3. 実 campaign 1 本で gate 入力の実値域を記録する。

## 不変条件

- 凍結 23 件の bytes を変えない。特に `output/s8b-freeze/floor_protocol.json`
  (`test_frozen_artifacts.py:41-64` が sha256 `261cec1c7f42...` で pin)。
  `FORMULA_ID` は据え置き (裁定 1 は未裁定。改版すると同 pin に届く)。
- 正しさゲートを緩めない。fake registry・injected `measure_fn` を実値域の代替にしない。
- launcher の perf 述語の新しい直接 call を作らない (契約 9 節 B-07 の inventory が落ちる)。
- `attempt_registry_core.py` に `aborted=False` keyword と `OriginSealed(False, ...)` を書かない。

## (P1) 親の provisional 裁定 = 段 3 の攻撃対象

- **(P1-1)** 実値域は Pegasus の既登録 `tools/pegasus/submit_floor.sh` 1 本で供給する。
  **F660 は発火しない** — main 側 `tools/pegasus/admission_registry.json` に
  `floor_campaign.sh` / `submit_floor.sh` が実在する (親が main の現物で確認)。
  job は `PBS_O_WORKDIR` を repo root にするので wave checkout の code で走る (elapstim 上限 10:00:00)。
  login node の走行は到達性確認にだけ使い、値域の母集合とはしない。
- **(P1-2)** 実装面は 5 file 以内 (campaign / contract / test 2 本 / 受入所要台帳) で収まる。
  超えたら C3 を完成扱いにせず停止し、C3a (配線・v5 producer) と C3b (実 campaign・値域記録) の
  分割を裁定へ返す。
- **(P1-3)** v5 切替は certified 成果物へ到達しない (契約 v3.1 0 節: 到達経路 0 件) ため凍結面を動かさない。

## 変更面の実アンカー (分類でなく現物)

| アンカー | 現状 |
|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:6215` | `_run_session` — attempt_id を自前で作る |
| 同 `:6262` | `self.measure_fn(...)` の直接計測。launcher を通らない |
| `orchestrator/campaign/s8b_floor_contract.py:36` | `RESULT_SCHEMA = LEGACY_RESULT_SCHEMA` (v4) |
| 同 `:38-40, :96-99` | `READABLE_RESULT_SCHEMAS` と `_RESULT_KEYS_BY_SCHEMA` に v5 が既設 |
| `orchestrator/campaign/s8b_floor_attempt_launcher.py:210` | `_PRODUCTION_DEPENDENCIES` (registry + capture) |
| 同 `:1189` | `launch_floor_attempt()` — certified 入口、production 呼び手 0 件 |
| `orchestrator/campaign/s8b_floor_stats.py:1155` | v5 result の live inspector (既設) |

main の 115 commit はこの編集面に触れていない (親が `git diff --stat` で差分 0 を確認)。

## 成果物の形

branch checkpoint、insight 一式 (brief・裁定・逐語・変異台帳・受入 receipt)、
spool fragment (worklog / decisions / failures)、実 campaign の値域記録。

## 並列分割方針

段 5 は 2 子。子 A = campaign 配線 (`s8b_floor_campaign.py` と対応 test)、
子 B = contract v5 切替 (`s8b_floor_contract.py` と対応 test)。所有 file を素集合に切る。
受入所要台帳の add-only は main 取り込み後に 1 本の子で 1 回だけ行う。

## 受入・実測環境

受入全走は login node (`tools/dev_wave_wait.py acceptance --lease-optional`)。
実値域は Pegasus (`submit_floor.sh`)。所要は job の Elapse を正とする。
