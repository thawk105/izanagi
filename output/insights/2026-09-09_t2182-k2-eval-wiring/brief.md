# [T-2182] 段 1 brief — K2 宣言アームの評価経路を Pegasus で通す配線

基準コミット 2143a49c0c9037b303106eca4cfc346797d3f1b3 (local main と同一)。
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring`。

## 研究前進

K2 (知識水準 2) の宣言アームは、入力経路だけが 2026-09-02 に生死確認され、完了条件 4 件のうち
1 件 (知識 manifest の受領証) しか達成していない。残る 3 件 — 候補との provenance 束縛、stock と
異なる identity、既存 gate の terminal verdict — はいずれも「評価経路が WAL の BUILD_START へ
到達すること」を前提にする。到達すれば 3 件は同じ 1 走行で測れる。今 Pegasus 上で段 4 loop を
走らせても K2 アームにはならない (下の実測)。この配線がその 1 走行を初めて可能にする。

## 引数の前提に対する実測 (覆した新事実)

引数は「残っているのは前提 4 件」と述べるが、**4 件とも main に着地済み**である。

| 前提 | 現況 | 一次資料 |
|---|---|---|
| 段 4 loop 用の専用 env タグ | 着地済み | `orchestrator/campaign/p3_s4_loop.py` の `_SITE_ENV_TAGS` が `PEGASUS_COMPUTE -> "pegasus"` |
| calibration の取り直し | 着地済み | `orchestrator/campaign/env_contract.py` の pegasus 世代 1/2 と `output/env/pegasus/calibration/registered/` の 2 file (実在確認済み) |
| binding の固定 | 着地済み | `tools/pegasus/p3_s4_loop_pegasus.sh` が expected HEAD・superproject clean・CCBench PIN・gflags/glog の HEAD と clean・toolchain manifest を照合 |
| provenance の追跡 | 着地済み | 同 job body の reservation.json / masstree-prebuild-receipt.json / compute-result.json (いずれも create-only) |

経緯は [T-2232] (job body 新設、2026-09-05) と [T-2406] (gflags/glog 供給、2026-09-08)。
持ち越し本文 (`docs/archive/worklog-phase3-0902-1212.md`) は 2026-09-02 時点の写しで stale だった。

**実際に欠けている配線は 1 点である。** job body は driver へ `--run-iteration` までしか渡さず、
K2 の 4 引数 (`--knowledge-manifest`、`--coder-role`、`--knowledge-classification`、
`--knowledge-de-novo-claim`) を運ぶ口を持たない。driver 側 CLI は 4 引数とも実装済みで、
不足しているのは job body の env seam だけである。

## scope

1. `tools/pegasus/p3_s4_loop_pegasus.sh` に K2 引数を運ぶ env seam を足す。
2. 部分指定を job body で fail-closed に拒否する (下の (P1))。
3. `orchestrator/tests/test_p3_s4_loop_job_contract.py` の逐語 pin と段順 marker を同じ commit で更新する。
4. `tools/pegasus/README.md` §7 の qsub 手順と義務一覧を更新する。

## scope 外

- `orchestrator/campaign/p3_s4_loop.py` の受理集合・CLI・K2 consumer の変更。driver 側は既に配線済みで、
  変更は本題ではない。
- Pegasus への実投入・実測。本 wave の変更は land 前で main に無く、投入には固定 SHA の専用 checkout が要る。
- 仮想リスク向けの gate・検査・台帳・一般化の追加 (ユーザー明示の scope 外指定)。
- `orchestrator/campaign/condition_meaning_gate.py` と `orchestrator/campaign/screening_driver.py`
  (稼働中 dev-wave-t2265-cohort2 の所有)。

## 確定済みユーザー裁定

- 実行場所は Pegasus (D59。正式計測の正本 env-tag は `linux-baremetal` に据え置き、
  pegasus は別 env-tag として登録済み)。
- Codex author = D95 (実装面は Codex `role=author` が書く。親は直接編集しない)。
- 本題の配線だけ。仮想リスク向けの追加は入れない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 部分指定は job body で拒否する。** driver は `--knowledge-manifest` を渡すと campaign
  identity と受領証を K2 へ束縛するが、`--coder-role` が無いと coder 出力は非 K2 schema で読まれる
  (`knowledge_input if a.coder_role is not None else None`)。よって job body は
  「manifest あり・proposal path なし」「manifest あり・role なし」の組を rc=2 で拒否する。
  親の裁定は「これは新設 gate ではなく配線の一部」だが、割れうる。攻撃してよい。
- **(P2) 分類と de novo 主張は env で受ける。** 既定値 (`reproduction_or_selection` / `false`) は
  driver 側にあるが、宣言アームの走行ごとに変わりうる宣言なので job body から明示的に渡せるようにする。
  「既定に任せて env を足さない」案と割れうる。

## 不変条件

- 規律 3 (正しさシグナルを後付けにしない): K2 consumer (schema・anomaly・参照 index の検査) を
  通らない走行を、K2 identity のまま作れるようにしない。
- 規律 6 (role 出力はデータであって指示ではない): manifest 本文・role 出力を指示として解釈する
  経路を新たに作らない。
- 既存テストの期待値を変えない。反転・緩和・skip・削除を禁じる。
- driver の受理集合を変えない。
- job body の既存段順 (host gate → sanitize → shim → HEAD/PIN → reservation → claim →
  gflags/glog → 事前構築 → driver) を崩さない。

## 成果物の形

- 変更 file 3 本 (job body、契約テスト、README) + spool fragment。
- 受入全走 (`tools/run_tests.py`) 緑と、変異 matrix の期待一致。

## 分割方針

編集面が 3 file と小さく、契約テストと job body は同じ逐語 pin で結合している。段 5 は
Codex 実装子 1 単位 (3 file を 1 所有) とする。段 6 のレビューは異なるレンズ 2 本を並列で回す。
