# T-2515 — rr95 / rr5 投入対応と失敗実測の回収

2026-09-09〜10 の測定記録を、参照 branch
`worktree-dev-wave-t2515-calib-rr95-rr5` の確認 tip
`559bcbc29cfa27412f103b608e8ac708dcfae6b9` から回収した。
**accepted calibration は取得できていない。** 新規測定は今回の回収には含めない。

## 回収範囲

`ad002de1b`、`bcfd2b931`、`3dbf7ea1d`、`18704ae18` の必要差分は、
sanctioned な submit/job shell の rratio 集合に exact な 5 と 95 を足すこと、
条件関門を既存の smoke 済み Python 3.10 で起動すること、その consumer test と利用説明である。
現行 main の T-2535 による offline FetchContent 供給と verifier interpreter 選定は維持する。

`ec17af5dc` から回収した `job-evidence/` の 7 ファイルは当時の bytes のままである。
旧 wave の fixture 共有化と付随する裁定 fragment (`559bcbc29`) は回収しない。
旧 worklog fragment の未着地の判断・新規タスクも転載しない。
回収に伴う現在の検査記録は当時の実測と区別する。

## 当時の失敗実測

1 巡目の rr95 job `988653.nqsv` は commit `bcfd2b931` で投入された。
`988653-rr95-condition-gate.stderr` は verifier import 中に
`TypeError: unsupported operand type(s) for |: 'type' and '_LiteralGenericAlias'`
が発生した記録であり、`988653-rr95-failure.json` は shell stage の失敗を記録する。
条件関門が既定の Python 3.9 で起動され、後段の Python 3.10 選定が間に合っていなかった。

2 巡目の rr95 `988706.nqsv` と rr5 `988708.nqsv` は commit `3dbf7ea1d` で投入された。
条件関門は import を越えて構造化記録を出したが、両方とも次の判定で停止した。

| arm | reason | macro |
|---|---|---|
| supply-effectuation | configure-failed | BACKOFF_FIXED |
| runtime-meaning | materialized-branch-invalid | BACKOFF_FIXED |

記録は `988706-rr95-condition-gate.jsonl`、`988708-rr5-condition-gate.jsonl` と各 `failure.json`。
`988706-rr95-submit-receipt.json` は workload の `ycsb_rratio` が `95` と束縛された投入受領証である。
これらは当時の実行がそこまで到達した証拠であり、現在の実装の受入結果ではない。

当時の CCBench pin `511c9538` には宣言した `BACKOFF_FIXED` が無かった (F934 / T-2320)。
条件関門の拒否を迂回して accepted を作ってはいない。D15 の workload 別校正を満たす
rr95 / rr5 の accepted record は、この実測では増えていない。
「B-4 の 3 workload セルが揃った」「A-6 が動いた」とは主張しない。

## 残る作業

T-2515 の校正取得自体は未完了。2026-09-10 の後続裁定は、stock を較正対象のままにして、
供給していない `BACKOFF_FIXED=-1` の指定・宣言・専用条件要求を整合して撤去すると決めた。
正本は `output/insights/2026-09-10_rulings-all-verdicts/README.md` と同資料が指す裁定項 6。
したがって、この過去の拒否を「今も必要と承認された正しさ条件が拒否した」とは説明しない。
撤去の実装と校正取得は別の変更単位であり、今回の回収では旧条件の拒否を保つ。
patch materialize、receipt schema 拡張、再測定も今回の範囲外である。
shell 2 経路の exact な許可集合を、calibrator CLI 全体の許可集合とは同一視しない。

## 回収差分の関連検査

`e618883c2` に本回収差分を重ねた commit 前の固定状態で、親が `tools/run_tests.py` を通して
7 ファイルを個別に実走した。合計 **1,379 passed / 4 skipped / 0 failed**。
内訳は calibration workload 70、pegasus tools 69、floor tools 143、official perf closure 7、
docs checker 572 (skip 3)、hooks 474 (skip 1)、spawn sites 44。
独立した敵対レビュー 2 本はいずれも GO、must-fix 0。Codex agent 検査と docs 検査も rc=0。
これは関連検査の結果であり、変異検査や最終受入全走の結果ではない。

## 回収差分の変異検査

固定 commit `35a740cd4805763b6600e190409cf9db5bd21f91` で実走した。
D842 / D1358 の既存 `mutation` task を使い、各 wrapper を計算ノードの 1 job へ束ねた。
probe は `989985.nqsv` (会計 Elapse 217 秒)、本走は `989993.nqsv` (218 秒)。
基準走はどちらも70件通過。本走は **8/8 KILLED、期待 node 完全集合に一致、rc=0**。
timeout、parse error、survived、mismatch はいずれも0。

| 対象 | 検出した内容 | 失敗 node 数 |
|---|---|---:|
| M1 / M2 | rr95 / rr5 が投入されなくなる | 各3 |
| M3 / M4 | submit で51を受理 / job で95を拒否する集合変更 | 2 / 1 |
| M5 / M6 | +5 / 05 の正規化で不正入力が rc=0 へ進む | 各1 |
| M7 | README の許可集合の退行（docs 整合 pin） | 1 |
| M8 | 未選定の裸 Python へ戻すと実起動が rc=97 になる | 8 |

M7をruntime実効性の証拠には数えない。M3/M4には受理集合の構造検査も含む。
M5/M6は後続の別関門や診断文の違いだけで落ちたものではなく、実際の rc=0 対期待2の失敗である。
M8は旧期待の1 nodeを流用せず、probeの観測8 nodeから本走期待を機械生成した。
初回probeは全件SURVIVED期待とし、8 MISMATCHになった記録も保存した。

生のspec・report・attempt sidecarは本directory、今回の段ごとの逐語は `recovery-verbatim/`。
最終受入全走はこの記録時点では未実施。
