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

## 2026-09-15 追記 — 元 wave の研究記録を回収した

**この節より上 (1〜86 行) は 2026-09-10 の回収時の記述であり、1 byte も変えていない。**
本節は、元 wave `worktree-dev-wave-t2515-calib-rr95-rr5` (確認 tip `559bcbc29`) に残っていた
研究記録のうち、これまで main に着地していなかった分を 2026-09-15 に回収した記録である。
**新しい測定はしていない。コードも 1 行も変えていない。**

回収した実体は次の 2 つ。どちらも元 branch の blob と byte 一致で、内容は当時のままである。

- `original-verbatim/` — 元 wave の子 13 本の逐語 (段 1 brief、段 2 plan、段 3 相談 2、
  段 4 裁定と追補、段 5 author、段 6 review 2 / fix 3 / 焦点再レビュー 1)。
- `original-mutation/` — 元 wave の変異 spec / report 各 2 本。
  **`repo_head` は `18704ae18` で、本 directory に既にある `mutation-final*.json` /
  `mutation-probe*.json` (`repo_head` = `35a740cd4`) とは別の実測である。**
  後者は 2026-09-10 の回収 wave が現行合成に対して再走した結果で、前者の代替にはならない。

既存の `job-evidence/` 7 file、`mutation-*.json` 6 file、`recovery-verbatim/` 11 file は
いずれも変更していない。

### 回収した事実 1 — interpreter ドリフトの年表

元 wave が実測した 4 つの時点である。**この 4 点が確かめられた事実であり、
「認証経路が 3 週間連続で実走不能だった」ことは、これらの証拠からは導けない。**

| 日付 | commit / job | 出来事 |
|---|---|---|
| 2026-08-06 | `892707.nqsv` | 元 wave が確認した範囲で最後に成功した認証 calibration。**条件関門はまだ無い** |
| 2026-08-20 | `3c9932591` | `orchestrator/verifier/parse.py` へ Python 3.10 専用式が入る (潜在) |
| 2026-09-01 | `0218acc61` | 条件関門を全 driver へ義務化。認証 job body がこの import 経路へ入る (発火) |
| 2026-09-10 | `988653.nqsv` | rr95 / rr5 の投入で発現。21 秒・`rc=1` で停止 |

限定して言えるのは、**元 wave が確認した認定 attempt には当該関門の実走記録が無かった**ことと、
潜在化から発現まで約 3 週間、関門経由での発火開始から発現まで約 9 日が経っていたことである。
「2026-08-06 以降ずっと故障していた」とは言えない — F500 は同じ script の別の呼出しで
別の認証投入と失敗を記録している。

検知穴として言えるのは 3 点に限る。(a) python3.10 の smoke 選定ブロックが、それを必要とする
呼出しより後ろに置かれていた。(b) 既存の unit test は job body の shell を静的に読むだけで、
関門が実際にどの interpreter で起動されるかを見ていなかった。**login node では `python3` が
3.10 に解決されるため、仮に実行しても再現しない。計算ノードでしか出ない差である。**
(c) この経路を長く通さなかったこと自体が、発見を遅らせた。

**台帳上の扱い (2026-09-15 の判断):** これは新規の失敗型ではなく、`F500`
(同 script が裸の `python3` を呼び 3.10 構文で落ちる型) の再発である。
F500 には既に 2026-09-10 の再発が載っているが、それは pristine source verifier の呼出しで、
本件の条件関門は同族の別呼出し・別観測にあたる。

### 回収した事実 2 — 静的な字面照合は、正規化 1 行の挿入で恒真になる

元 wave の変異本走 (8/8 KILLED、期待 node 完全一致) が裏付けた知見である。
根拠となる spec / report は `original-mutation/` にある。

| 変異 | 殺した node | 件数 |
|---|---|---|
| M5 `RRATIO=${RRATIO#+}` を gate 直前へ挿入 | `test_submitter_rejects_an_unregistered_ratio_before_side_effects[+5]` | **1 件だけ** |
| M6 先頭 0 の除去を挿入 | 同 `[05]` | **1 件だけ** |
| M4 job body 側から `95` を落とす | `test_job_rechecks_the_submission_workload_and_records_it` | **1 件だけ** |
| M8 関門 argv を素の `python3` へ戻す | `test_condition_gate_uses_smoke_checked_interpreter_selected_before_call` | 1 件だけ |

M5 / M6 は**静的な literal 抽出テストでは緑のまま通り抜ける**変異である。実起動の負例を
足していなければ検出できなかった。M4 は投入側と job body の許可値を突き合わせる検査だけが捕まえる。

**当時と現在の対応 (混同しないこと):** M8 が殺した node
`test_condition_gate_uses_smoke_checked_interpreter_selected_before_call` は、後続の
D1936 項 6 が条件関門ごと撤去したため現行 main に存在しない。本 directory の
`mutation-final-report.json` が記録する M8 の 8 node は、回収 wave が現行合成に対して
再走したときの別の期待集合である。

### 回収した事実 3 — レビュー 3 本が揃って見落とした赤を、焦点走が捕まえた

interpreter 選定ブロックを条件関門より前へ移したことで、`test_pegasus_tools.py` の
`_calibrate_interpreter_fragment()` の抽出範囲 (`CALIBRATE_PYTHON=""` から `# CLI ` まで) に
gflags / glog の build と条件関門まで入り、harness が `GFLAGS_SOURCE_PATH: unbound variable` で
落ちた。段 6 のレビュー A / B / 焦点再レビューはいずれもこれを挙げていない。
**焦点走が捕まえた (1 failed / 1349 passed)。** 焦点走の対象集合を名前の推測ではなく
参照関係で引いた結果である。修正では「PATH shim を実際に実行して検証する」部分を静的 assert へ
格下げせず、選定ブロックと shim 1 行を別々に抽出して連結する形を採った。

### 回収した事実 4 — 依頼の前提が一次資料と食い違っていた

元 wave への依頼は「A-6 はここで止まっている」と書いていたが、`docs/paper-story/2026-09-05.md` §8 は
A-6 の停止原因を計算ノードの `FetchContent_Populate(masstree)` 失敗と記録しており、
較正不足とは書いていない。元 wave は成果物を変えず、根拠を T-2515 原文の
「B-4 の 3 workload セルが 2 件不足」へ置き換えた (`original-verbatim/s4-ruling.md`)。

### 回収した事実 5 — 元 wave のセッション異常と判断の訂正

`original-verbatim/` と元 wave の worklog fragment にだけ残っていた観測である。

- 長く待つ command を短い `timeout` で包んだ結果、計算ノードへ dispatch された job が queue 待ちの
  まま 900 秒で SIGTERM された。dispatcher は自ら qdel して `rc=16` で終了したが、
  **orphan hold が 2 箇所に残った。** qstat で job 不在と source の clean / HEAD を確認して外した。
- 段 5 / 6 の子へ `--reasoning` を渡して `rc=2` で即死した。effort は docs 権威から導出され、
  caller 指定はできない。
- 段 6 レビュー B の 1 回目が、最後の見出しを `### 総括` で書いたため採用検査で `rc=1` になった
  (採用は H2 必須)。中身は完成しており、1 回目も `original-verbatim/s6-review-b.md` に残っている。
- 隔離セッションから子 worktree へ git を実行できなかった (`git -C` も `cd` も guard が拒否)。
  代わりにツリー同士の全比較で所有違反ゼロを確かめてから複写し、複写後に再度全比較で byte 一致を
  確認した。3 回とも所有 path 以外の差分は 0 件だった。
- 受入全走が 2 巡とも赤になったとき、親は「完全に非帰属」と判定したが**覆った** —
  元 wave は `output/insights/` に 25 file を足し、軽かった test を subprocess 11 起動へ変えており、
  資源面の到達経路は実在した。併せて親は `docs/failures.md` を `t1259` と `TimeoutExpired` という
  **字面**で引いて「該当 F 無し」と結論したが、F57 と F862 が実在した。
  **台帳は事象の型で書かれるので、file 名や例外名では引けない。**
  この判断の誤りは新規の型ではなく、`F766` の根本原因 (1)「台帳を主題ではなくファイル名で引いて
  正しい族を見落とす」の再発である。
- 待ち手が producer 生存中に rc=0 を返す事象を 1 wave で 3 回観測した。`.done` 非空判定が
  3 回とも捕まえ、誤って先へ進んでいない。これは `F355` の再発である。
- 既存 accepted 2 件の `binary_sha256` は**互いに一致せず** (`9ef84125...` と `25c82a74...`)、
  CCBench head も既存 `d706650c...` に対し当時の pin は `511c9538...` だった。
  **この系の比較可能性は binary の同一性で担保されていない**という観測である。
- 元 wave の工数記録は「codex 子 9 本」と書いているが、内訳 (plan 1 / consult 2 / author 1 /
  review 3 / fix 3) の合計は 10 である。確定値としては扱わず、原文の不一致として記す。

### 後続裁定との関係 — 当時の判断を現在の方針として読まないこと

`original-verbatim/` と元 wave の spool fragment には、**後続のユーザー裁定で覆った判断**が
歴史資料として残っている。現在の方針は次のとおりである。

| 当時の判断 (逐語に残る) | 現在の方針 |
|---|---|
| `silo-backoff-fixed.patch` を materialize して関門に同値性を実測させ、receipt に新 shape を足す | **D1936 項 6** が、供給していない `BACKOFF_FIXED=-1` の指定・configure argv・genome 宣言・専用条件要求を整合して取り下げると決めた。同項は「未 land の `certify-materialize-backoff-patch` は本裁定と食い違う範囲を採用しない」と明記している |
| 実 repo 走査を伴う autouse fixture を module ごと 1 回にする | **D1936 項 43** が承認し、T-2579 が実装して着地済み |
| 認証経路の定期 smoke を新設するかを裁定に返す | **D1936 項 46** が見送りと決めた |
| 待ち手の偽成功を機構側で直すかを裁定に返す | **D1936 項 47** が、rc だけを信じる consumer の実在を調べ、存在すれば既存の完了判定へ揃える局所修正だけを行うと決めた |
| rr50 を先に取り直してから rr95 / rr5 を同一世代で取る | **D1986 項 1** が、レコード数の選択規則へ取りこぼし率の下限を足すと決めた。rr5 の却下記録は却下のまま残す |

### 当時取れていないもの (変わらない)

2026-09-10 の 2 job (`988706.nqsv` / `988708.nqsv`) はいずれも `admitted=false` で、
shell は `rc=2` で停止した。**当時の実測で accepted calibration は 1 件も生産していない。**
条件関門の拒否を迂回した記録も無い。この節は当時の記録であり、
その後に取得された較正について何かを主張するものではない。
