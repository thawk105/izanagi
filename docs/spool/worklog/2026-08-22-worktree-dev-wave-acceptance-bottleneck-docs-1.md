---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: worktree-dev-wave-acceptance-bottleneck-docs
seq: 1
title: '[T-1468] 受入全走の誤帰属防止2件 (checker infra失敗の扱い・受入投入と記録commitの順序) をdev-wave docsへ着地させた (docsのみ、branch worktree-dev-wave-acceptance-bottleneck-docs)'
---

## 本文

- ユーザーから command 引数「受入全走のボトルネック解消。半日近く受入全走が失敗しまくり、
  開発が非常に停滞している」を受けて調査した。並行 peer session 4件 (lease coordinator・
  dev-wave codex failure recovery [T-183]・acceptance lease staleness quantification
  ([T-1469] 本人)・dev-wave known-violation resolution) へ SendMessage で照会し、一貫した
  証言を得た: 直近半日の支配的コストは lease 直列化そのもの (15+ 並行 wave 下で claim 待ち
  中央値約42分、lease coordinator 実測では受入投入〜land完了7時間中の実テスト実行はわずか
  8分44秒。改修案は [T-1461]/D270 で既に却下済みで再訪の新根拠なし) と、今夜限りの急性要因
  (ユーザー本人による external/ccbench pin の直接 commit `09ce607b` → provenance 赤 +
  `test_ccbench_full_sha_matches_real_gitlink` 赤が全 wave の受入 preflight をブロック、
  `t-1458 registry-orchestrator connection` セッションが対応中で `ddf30399` 時点では解消
  済みと3セッション独立に確認) の2つだった。どちらも他 session が対応済み/対応中と確認した
  ため本 wave は触れず、docs 予算超過で実装見送りのまま滞留していた「受入全走の誤帰属防止」
  自己改善候補の着地に絞った。
- 着地させた2件:
  1. [T-1468] (`docs/archive/worklog-phase3-0821-796.md`、旧称「T-1462」。ユーザーの繰り返し
     依頼「自分のwaveで起こしたわけではないテスト失敗でウェーブ失敗するの許さない」に由来) —
     `tools/check_acceptance_reds.py` の rc 非0が (a) 帰属あり rc=1、(b) 判定不能 rc=2、
     (c) checker 自身の Pegasus infra 失敗、の3種を区別せず同じ `_StageFailure` に畳んで
     いた。(c) は no-verdict retry の対象外で attempt が全損になる制御フロー上の事実を
     `DW-O18` へ明記し、`rc=0 かつ status=non-attributable-only は受理成功` も明記した。
  2. [T-1451] (`docs/archive/worklog-phase3-0820-767.md`) — `DW-S06-C`「親が変異matrixと
     受入を再走する」が段6内の受入投入を示唆する一方、記録commitは段7という構成が、land
     対象tipへの最終受入投入のタイミングを曖昧にしていた (取り違えると記録commitがtested
     tipから漏れ land rc=23)。`DW-O12`(「裁定手順と実行手順の差」、追記前611 bytes空き)
     へ明記して解消した。当初提案先だった `DW-S07`/`DW-C00` はL1総予算(10,625 bytes)が
     既に逼迫(追記後11,038 bytes相当まで到達)しており収まらなかったためL2側の空き節へ
     移設した ({{D:dw-o12-sequencing-note-placement}} 参照)。
- 3件目 (`docs/archive/worklog-phase3-0821-792.md` 候補2「探索目的の全走も隔離worktreeで
  行う」、実測: 12 failed+3 errorのうち11+3件がnear-miss) はT番号を持たないprose only候補
  のまま滞留していたため本waveが新規登録した ({{T:exploratory-run-worktree-isolation}})。
  理想的な設置先 `DW-O20` は984/1000 bytesで空き16 bytesしかなく収まらないため未着地の
  まま持ち越す。
- `docs/dev-wave/**` のL1/L1.5/L2予算は3層とも逼迫状態にあると2セッション独立に確認された
  (entry 792、本wave)。予算定数自体の見直しは本waveのscope外 (規律5) とし、着地できなかった
  候補の記録に留めた。
- 一次資料: 本 fragment、`docs/dev-wave/operations.md` の DW-O18/DW-O12 diff、
  `python3 tools/check_docs.py` (違反なし)。

## 次の一手差分

### 完了

- [T-1451] land 対象 tip への最終受入投入は段7記録commit完了後に行う旨を DW-O12 へ明記した。
  remaining: none
  base: 20469cdd9bd5c7e512d75851e8764e52f5951f18d762646f63c9970625ee0d0e
- [T-1468] checker 自身の Pegasus infra 失敗は no-verdict retry 対象外・rc=0 かつ
  status=non-attributable-only は受理成功である旨を DW-O18 へ明記した。
  remaining: none
  base: debfadc3981bb6168cfea78e914ea9d1a172ba3fa9cebcbc0feaf4be4ab1aba9

### 新規

- {{T:exploratory-run-worktree-isolation}} **P3・新規**: 探索目的の全走も隔離 worktree で
  行う旨を DW-O20 (984/1000 bytes、空き16 bytes) へ追記する候補。`docs/archive/
  worklog-phase3-0821-792.md` 候補2 が一次資料 (T番号未採番のまま滞留していたため本 wave
  で新規登録)。dev-wave docs L1/L2 予算の圧縮 (既存文の統合・重複除去) を伴う専用 wave で
  ないと着地しない。
