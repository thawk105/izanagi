# [T-953] SWO oracle 残余 5 件 — wave 逐語一式 (2026-08-13)

wave = `dev-wave-t953-oracle-residue` / branch = `worktree-dev-wave-t953-oracle-residue` /
起点 = `adf7997f`

worklog の該当エントリが要約の正本。ここは機械成果物の凍結先である。

## 何をしたか

[T-316] R2-b が残していた SWO oracle の残余 5 件 (a)〜(e) を閉じた。

- (a) 候補 compile 失敗時に trusted control の**事後** compile (postflight) を行い、
  環境故障との相関を測る。候補成果物は postflight の前に除去し、postflight は専用の
  別一時 directory で走らせる。除去に失敗しても postflight は飛ばさない。
- (b) contract ID を再構成し、公理判定の**実装 bytes** と走査範囲の意味論定数を束縛する。
  変更前は 2 関数 bundle と corpus データ hash だけで、`_CORPORA=(0,)` のように
  検査範囲を半減させても identity が動かなかった。
- (c) critic の oracle finding validator に kind ごとの exact key 集合、閉じた reason_code
  集合、producer 正準形の corpus_id、observations 要素の schema を入れる。
- (d) S1 の oracle REJECT を session ledger へ耐久化する。
- (e) S6 の docstring を実体へ是正する。

## 実測

| 項目 | 値 |
|---|---|
| 変異 matrix | **KILLED 12 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0**、baseline PASSED |
| 変異の HEAD 束縛 | `7c1fa911692bd06613208c2ef80c4f7c6c4a8669` |
| spec digest | `752a48683a1cb87c5591a79ddb625aaa45b23216a6d403a3953388808cc50c24` |
| 期待赤 node | 計 36 件 (M1=6 / M2=5 / M3=2 / M4=2 / M5=2 / M6=1 / M7=1 / M8=1 / M9=1 / P1=7 / P2=4 / P3=4)。**初回走行で全件一致** |
| 焦点走 (fix 第 1 巡後) | 159 passed / 4.68 秒 (Pegasus request 908801.nqsv) |
| 焦点走 (fix 第 2 巡後) | 160 passed / 4.63 秒 (Pegasus request 908811.nqsv) |
| 焦点走 (fix 第 3 巡後) | 100 passed / 2.54 秒 (Pegasus request 908849.nqsv、`test_s8b_oracle_manifest.py`) |
| 受入全走 1 回目 | 2 failed / 10,512 passed / 65 skipped (124.85 秒、Pegasus request 908839.nqsv)。赤 2 件は本 wave 帰属で、F30 五度目の再発 (編集面 source の pin 閉包漏れ)。fix 第 3 巡で是正 |
| Codex 工数 | 12 本 (plan 1 / consult 2 / author 2 / review 2 / fix 3 / focus 2)、model call 354、wall clock 8,103 秒、全件 rc=0 / evidence complete |

受入全走の結果は worklog の該当エントリを正本とする。

## 成果物

| ファイル | 内容 |
|---|---|
| `mutation-spec.json` | 段 4 で事前登録した変異 12 件 (負例 9 + 正例 3) の spec。schema `izanagi-dev-wave-mutation-spec/v1` |
| `mutation-ledger.json` | 上記 spec の本走台帳。runner scope は `test_sort_swo_oracle.py` + `test_critic.py` + `test_s1_direct_comparison.py` + `test_p3_s4_loop_sort.py` |
