# 段 1 brief — [T-609] certified writer の閉包

wave: `dev-wave-t609-certified-writer-closure` /
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure` /
起点 HEAD: `bb824d8b` (開始時の local main)

## scope

T-529 裁定 C(a) が別タスクへ切った「certified writer の閉包」を実装する。2 層。

- **(a) Python 層** — `orchestrator/campaign/loop.py` の `_authorize_measurement` が
  `env_contract is None` を site 検査より前に `return None` するため、契約に束縛されない run が
  `certified` へ到達できる経路を閉じる。呼び手の代表は
  `orchestrator/campaign/s8a_trigger_sweep.py:457`。
- **(b) shell 層** — `tools/pegasus/floor_campaign.sh` と `tools/pegasus/t126_qualification.sh` が
  Python gate より前に成果物を書く経路に、最初の書込みより前で効く契約 preflight を入れる。

## 確定済みユーザー裁定

- T-529 = C(a)「writer 閉包は新規タスクへ切る」(2026-08-07 /rulings §36、発話「推奨通り」)。
  **切り出しだけが裁定済みで、閉包の実装方式は未裁定。** 受理集合を変える設計択一が残るなら
  段 4 で裁定パッケージへ返し、親が勝手に採らない。
- 規律 2 により閉包は fail-closed 方向のみ。gate を緩める変異は採らない。

## brief 前の実測 (親が現物で確認、一般化も攻撃対象)

1. `_authorize_measurement` (loop.py:62-73) は `actual_site` を取得した直後に
   `if env_contract is None: return None` する。よって直後の
   「PEGASUS_COMPUTE では登録済み pegasus contract だけ受理」検査は `None` 経路で**死んでいる**。
2. `loop.run_campaign` の production caller は 14。`env_contract` を渡すのは
   `orchestrator/qualification/t126_driver.py:540` と
   `orchestrator/campaign/s8b_oracle_driver.py:1381` の 2 本だけ。
3. 残り 12 本 (p3_s4_loop / s8a_trigger_sweep / backoff_sweep / s6_sort_sweep / p3_kickoff /
   p2_2 / sanity_silo / demo / p3_s4_red / backoff_repro / p3_s4_loop_sort /
   p3_s4_loop_trigger_gating) は `ENV_TAG="linux-baremetal"` / `CLK=1800` /
   `NUMA=["numactl","--interleave=all"]`。
4. `env_contract.lookup("linux-baremetal")` は `attestation_mode="none"` /
   `clocks_per_us=1800` / `numactl=("numactl","--interleave=all")`。**3 と完全一致する。**
   よってこの 12 本へ registry contract を配線しても `_authorize_measurement` の全検査を通り、
   attestation も要求されない (= 受理集合不変)。
5. `pipeline.py:549` の「exact registered Pegasus contract 必須」は
   `qualification_policy is not None` の枝にだけあり、一般 campaign を覆わない。
6. 既存被覆は `orchestrator/tests/test_campaign.py:4100-4123` の 1 本のみで、これは
   `_authorize_measurement` を monkeypatch して receipt 素通しを見る。
   **`env_contract=None` 素通り自体を禁じるテストは 0 件** (純増検出力はここ)。
7. `floor_campaign.sh` は python 選定 (157-201) と `ATTEMPT_DIR` への書込 (88, 200-201) が
   driver 起動 (882-892) より前。`t126_qualification.sh` は `mkdir -p "$QUAL_ROOT/job-staging"` (75)。
8. 凍結 pin: `FROZEN_MANIFEST` (23 entry) に `loop.py` も 2 本の wrapper も**無い**。
   floor の既発行 receipt は `job_script_sha256` と `source_commit` を対で持ち、検証は
   `git show <source_commit>:<path>` 経由 (`test_pegasus_floor_tools.py:382`)。
   登録済み較正 `calibration-94a4b79fa31bba3c.json` の `job_script_sha256` は
   `certify_calibration.sh` 由来で本 wave の対象外。

## 親の provisional 裁定 (P) — いずれも段 3 の攻撃対象

- **(P1)** (a) の閉包は「12 caller へ `env_contract=lookup("linux-baremetal")` を配線し、
  `run_campaign` の `env_contract` から default `None` を外して `None` を拒否する」。
- **(P2)** 実測 4 より、この配線は受理集合を変えない。新たに拒否されるのは
  「PEGASUS_COMPUTE 上で linux-baremetal 契約の campaign を回す」経路だけで、これは正しい強化。
  → T-530 の「単独で塞ぐと承認外の受理縮小になる」という前提はこの範囲では成立しない。
- **(P3)** (b) の閉包は「最初の書込みより前に走り、書込みゼロで stderr + 非 0 exit する
  Python contract preflight」。失敗記録のための書込みも preflight より前に置かない。
- **(P4)** 凍結成果物の bytes は不変 (実測 8)。`DW-O10` は不成立。
- **(P5)** 受入・実測環境は本 worktree (Pegasus login node) での pytest 全走。
  Pegasus 実走 (qsub) はしない — 本 wave は計測値を生まない。

## 不変条件

- `certified` の受理集合は (P2) の 1 経路を除いて不変。縮小するなら段 4 で明記し正例を登録する。
- 既存テストの期待値を反転・緩和・skip・削除しない。
- 凍結 bytes 不変。docs は親だけが書き、実装子は commit しない。

## 成果物影響 (DW-G05)

実装しない場合、certified 選択結果と proof chain に「env 契約に束縛されない run」が混じったまま
残り、floor / T-126 を「最初の書込み前に保護した入口」と数えられない。結果として T-529 A(b) と
T-530 の前提が立たず、契約世代の活性化を入れても入口面の穴が残る。

## 分割方針

- 実装子 A = (a) Python 層 (`orchestrator/campaign/*.py`, `orchestrator/tests/test_campaign.py` ほか)
- 実装子 B = (b) shell 層 (`tools/pegasus/*.sh` と対応 test)
- 所有ファイルは素集合。依存があれば A を先行させる。
