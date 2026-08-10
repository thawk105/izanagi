# [T-740] 待ち手の正本 script — 逐語と変異台帳

ユーザー裁定 (a) (2026-08-10 /rulings) に基づき、受入 lease と背景 producer の待ち手を
`tools/dev_wave_wait.py` へ正本化した wave の逐語。branch は
`worktree-dev-wave-t740-canonical-waiter`。

## なぜ作ったか (wave 前の実測)

`tools/` に待ち手 script は存在せず、各 wave が `docs/pegasus-runbook.md` §7.3 の散文から
書き起こしていた。書き起こされた現物は 2 つとも欠陥を持っていた。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh` は
  `claim` の JSON 出力を `case "$out" in *acquired*)` の glob で判定している (F192 の型)。
- `/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b` の汎用待ち手は producer の死を
  `until ! pgrep -f "$PAT"` で判定し、`$PAT` が待ち手自身の argv に載るため常に自己マッチした
  (F32 の再発)。`.done` も成果物も揃った後に 20 時間 23 分と 7 時間 36 分 滞留し、
  wave が無音で死んだ。

## 段別の逐語

| ファイル | 段 | 主体 |
|---|---|---|
| `s1-brief.md` | 段 1 | 親 (裁定の前提 9 点の実測を含む) |
| `s2-plan.md` | 段 2 | codex `gpt-5.6-sol` / reasoning=max / read-only |
| `s3-lensA.md` | 段 3 | codex `gpt-5.6-sol` / max — 正しさ境界と受理集合 |
| `s3-lensB.md` | 段 3 | codex `gpt-5.6-luna` / max — 実効性と consumer 到達 |
| `s4-adjudication.md` | 段 4 | 親 (R1〜R12 の採用、U1/U2 の分離、変異事前登録) |
| `s5-impl.md` | 段 5 | codex `gpt-5.6-sol` / high / workspace-write |
| `s6-lensA.md` | 段 6 | codex `gpt-5.6-sol` / high — 実装 vs 裁定、fail-open |
| `s6-lensB.md` | 段 6 | codex `gpt-5.6-sol` / high — 実運用トレース |
| `s6-fix.md` | 段 6 | fix 1 巡目 |
| `s6-refocus.md` | 段 6 | 焦点再レビュー (`DW-O16`) |
| `s6-fix2.md` | 段 6 | fix 2 巡目 |
| `s6-fix3.md` | 段 6 | fix 3 巡目 (所有実装面 overlap 判定の実装) |

**敵対 3 本 (段 3 の 2 レンズは別として、段 6 のレビュー 2 本と焦点再レビュー) はすべて NO-GO を
返した。** blocker は 4 件で、うち 1 件は 1 巡目の fix が作り込んだ退行である。

## 変異台帳

事前登録は `s4-adjudication.md` の「変異事前登録」節。走行は 3 本。

| 台帳 | spec | 結果 | 位置づけ |
|---|---|---|---|
| `mutation-ledger-1-aborted.json` | (spec-2 の M1 を実 `pgrep` で書いた版) | **abort** | erratum。下記参照 |
| `mutation-ledger-2.json` | `mutation-spec-2.json` | KILLED 2 / MISMATCH 6 / **SURVIVED 0** | 事前登録した node 予測での走行 (M1〜M8) |
| `mutation-ledger-3.json` | `mutation-spec-3.json` | **KILLED 8 / SURVIVED 0** | 期待 node を実測へ揃えた走行 (M1〜M8) |
| `mutation-ledger-4.json` | `mutation-spec-4.json` | KILLED 6 / MISMATCH 3 / **SURVIVED 0** | fix 3 巡目の新設 gate を M9 として足した走行 |
| `mutation-ledger-5.json` | `mutation-spec-5.json` | **KILLED 9 / SURVIVED 0** | 確定走 (M1〜M9) |

ledger-3 から ledger-4 の間に fix 3 巡目が入り、新設 gate (所有実装面 overlap) の M9 を
`DW-M01` に従って事前登録した。fix でテストが増えたため M3 / M6 の失敗 node 集合も広がり、
ledger-4 では 3 件が MISMATCH になった。ledger-5 がその実測へ揃えた確定走である。
**どの走行でも SURVIVED は 0 である。**

**1 本目の abort は harness の限界を実測した** (worklog の同 wave エントリで新規起票している)。
M1 を*実の* `pgrep -f <pid>` で書いたところ pytest が hang し、harness の hang timeout (300 秒) が
dispatch を SIGTERM して receipt が `outcome.kind=infra` / `rc=16 / _SignalAbort: signal 15` に
なった。artifact の `job_stdout_path` が埋まらないため
`mutation record M1-pgrep-self-match.artifact dispatch path field が文字列でない` で
**matrix 全体が abort し、残り 7 変異は未実行のまま終わった**。
この hang 自体は「wave 前の形が本当に無音で止まる」ことの実証でもある。
M1 を注入 seam (`effects.run`) 経由の決定的な形へ再照準して 2 本目を完走させた (`DW-M02`)。

2 本目と 3 本目の差は `expected_nodes` だけである。変異の位置・置換・KILLED 期待は
段 4 の事前登録から変えていない。2 本目の MISMATCH 6 件は「捕まらなかった」ではなく、
親が予測した失敗 node 集合が実際より狭かったことを意味する
(`_observed_status` は失敗 node 集合の完全一致で KILLED を判定する)。

**M4 と M5 は 2 本目の時点で失敗 node 1 件、すなわち単一理由で殺せている** (`DW-M01`)。
この 2 件は fix 2 巡目で専用の単一理由テストを新設した箇所である。

## 変異と、それが守る不変条件

| 変異 | 壊す不変条件 | wave 前の実コードの形 |
|---|---|---|
| M1 | producer の生死は exact PID で見る | `t139-addendum-b` の `until ! pgrep -f "$PAT"` |
| M2 | 投入可否は `state` の exact 比較で決める | `run_acceptance.sh:20` の `case "$out" in *acquired*)` |
| M3 | 成功終端では lease を保持する | — |
| M4 | merge 後の `HEAD..main` 再検査で 0 でなければ投入しない | — |
| M5 | merge message の `AI-Agent:` trailer を検査する | — |
| M6 | 失敗終端では必ず release する | — |
| M7 | 完了は `.done` と成果物の両方で判定する | `wait6.sh:3-8` (`.done` 2 つだけで判定) |
| M8 | claim 前に branch identity を検査する | — |
| M9 | merge 前に所有実装面の overlap を見て、非空なら merge しない | — (fix 3 巡目で新設、88a5c1a3 の規範) |

M1 と M2 は memory `mutation-must-include-pre-wave-form` が要求する「wave 前の実コードの形」
そのものである。

## scope 外として裁定へ返したもの

- consumer (`.claude/commands/dev-wave.md`、`DW-C00`、`DW-O01`) への機械的結線。
  段 3 レンズ B と段 6 レンズ A / B が独立に「正本を作っても読まれなければ再発は止まらない」と
  指摘した。本 wave の scope は裁定 (a) の文言どおり「script の新設 + runbook §7.3 からの参照」
  までである。L1 への条文追加は [T-738] (c) が終端している。
- 受入 command の identity 強制 (`-- true` でも rc=0 になる)。

## 残した既知限界

`release` の権限証明が wave slug の digest だけであること、最終 postcheck から受入 command 起動
までの残余 race、fencing token の不在、SIGKILL / host 停止、任意 `-- COMMAND`。
いずれも本 wave 以前から runbook §7.3 に既記載であり、本 wave は悪化させていない。
