# 段 1 brief — [T-2593] 静的 tail 本走の投入経路を配線する

## 研究前進

B-10 静的 backoff の右 tail が表現可能域 (9999 マイクロ秒) 内で飽和するかは、事前登録
`docs/b10-backoff-static-tail-preregistration.md` の格子・判定式で本走を回さないと決まらない。
本走 driver は 2026-09-14 に着地済み (`orchestrator/campaign/b10_backoff_static_tail_formal.py`) だが、
Pegasus の投入経路が新種別を受理しないため、本走を投入できない。止まっているのは paper-story の
B-10 節 (探索走だけで「飽和の兆候なし」までしか言えていない) である。本 wave は投入経路の配線だけを
行い、投入はしない。完了判定 = 下記 4 点が実測で成立すること。

## 確定済みユーザー裁定 (依頼文より)

- 配線までが scope。**本走の投入は含めない。**
- 既存 3 系列 (`extended` / `t2266-tail` / `t2418-explore`) の受理集合は変えない。
- 実装面なので Codex `role=author` (D95) と変異事前登録が要る。規律 2 を緩めない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 実測した現状 (一次資料で照合済み、模擬なし)

- `t2500-tail-formal` の repo 内出現は driver 本体・その test・事前登録・過去 worklog だけ。
  `tools/pegasus/` 配下は 0 件。依頼の blocker は実在する。
- 新 driver の CLI は `--preregistration-commit` (必須) + subcommand。
  `run <workload> --explore-campaign <必須> --output-root <必須> --cache-root <必須> [--ccbench-dir]`、
  `report <campaign×3> --explore-campaign <必須> --output-root <必須>`。
  **既存 2 系列に無い必須入力が 2 つ増える** (`--preregistration-commit`, `--explore-campaign`)。
- 成果物: `run` は campaign 配下へ `reports/t2500-backoff-static-tail-formal-execution.json`、
  output-root 直下へ `t2500-backoff-static-tail-formal-<workload>-perf-preflight.json`。
  `report` は指定 dir へ stem の `.json` / `.dat` / `-complete.json` の 3 本。
  既存 2 系列の完了確認が見る `<stem>.dat` / `<stem>.json` は **campaign の `reports/` 配下**であり、
  新系列では位置も生成主体も異なる。ここを取り違えると完了確認が恒に赤か恒に緑になる。
- 1 workload 8 genome (事前登録 §4.1、境界参照 1000 を含む)。先例 `t2266-tail` と同数。

## 変更面 (実アンカー)

| file:line | 現状 | 要る変更 |
|---|---|---|
| `tools/pegasus/submit_b10_backoff_grid.sh:6-8` | usage が旧 3 種別 | 新種別を足す |
| 同 `:10-33` | 引数 loop | 新 2 入力の受理 (新種別のときだけ必須) |
| 同 `:36-38` | `case` が旧 3 種別 | 新種別を受理 |
| 同 `:184-187` | `QSUB_ENV` 組立て | 新 2 値を job へ伝播 |
| `tools/pegasus/b10_backoff_grid.sh:186-188` | `case` が旧 3 種別 | 新種別を受理 |
| 同 `:579-594` | stage 名と `SWEEP_COMMAND` (旧 driver 固定) | 新種別だけ新 driver を起動 |
| 同 `:620-665` | 完了確認が旧 2 stem のみ | 新種別の genome 数と成果物を検査 |
| 集団入口 | 不在 | 3 campaign を 1 集団として `report` する入口 |

## 不変条件

1. **既存 3 系列の観測可能な挙動を 1 bit も変えない。** `B10_RUN_KIND` が旧 3 値のときの
   argv・環境変数・成果物名・完了確認は現状と同一。負例テストでこれを守る。
2. 事前登録 `docs/b10-backoff-static-tail-preregistration.md` の bytes を変えない (凍結物、erratum 以外不可)。
3. driver 本体 (`b10_backoff_static_tail_formal.py`) を変えない。配線側だけを変える。
4. `--preregistration-commit` と `--explore-campaign` を script へ焼き込まない。投入者が渡す値とする。
   焼き込むと本 wave が「投入の一部」を先取りしてしまう。
5. `qsub -v` はコンマ区切りなので、伝播する値は既存の `OUTPUT_PARENT` と同じ文字集合検査を通す。
6. 新設するのは受理経路だけ。仮想リスク向けの gate・台帳・一般化を足さない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1-a) 集団入口は `submit_b10_backoff_grid.sh` の別 subcommand / 別 flag ではなく、
  **login 側で 3 campaign が揃った後に叩く独立 script** とするのが素直だと親は見ている。
  投入 script は qsub する役なので、完走後の集約を同じ入口に混ぜると責務が二つになる。
- (P1-b) 完了確認は新系列について「8 genome commit + `-execution.json` の実在」までとし、
  `report` の 3 本は集団入口側の責務とする。job は 1 workload しか見えないので集団報告は書けない。
- (P1-c) 新 2 入力は新種別のときだけ必須とし、旧 3 種別で渡されたら rc=2 で拒否する。
  黙って無視すると「渡したのに効かない」型の事故になる。

## 成果物影響 (DW-G05)

放置すると本走が投入できず、certified な選択の材料である B-10 tail 飽和判定が出ない。
配線後は投入 script の受理集合に `t2500-tail-formal` が 1 つ増える。既存 3 系列の受理集合・
成果物名・report schema は不変。

## 分割方針

段 5 は 2 名。U1 = `submit_b10_backoff_grid.sh` + 集団入口 script、U2 = `b10_backoff_grid.sh`。
テストは各自が自分の編集面の分を書く。所有 file は重ねない。
