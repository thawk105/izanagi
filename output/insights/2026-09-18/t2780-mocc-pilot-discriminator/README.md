# T-2780: mocc pilot discriminator の入力配線修正

authority: none
default_effect: no-state-change

## 実装と研究上の到達点

`tools/pegasus/mocc_trace_pilot.sh --t1943-g2-discriminator` が、現行 verifier の要求する
X/P 計装 source を build と検証へ渡せるようになった。実装は `f93281e55`、author 作業の
終端は `f75ca703c`。着手時 local main `b2037abfa` からの Codex 回収木へ、独立監査後に
実装 bytes を変えず merge した (`1d2ec1b66`、phase checkpoint を同時記録)。

- hydrate は driver import と Python >=3.10 を probe した絶対 interpreter を使う。
- T1943 では `instr-mocc-lock-coverage.patch` の touch set を確認して build 前に適用する。
- verifier の source root は同じ patched `BUILD_SOURCE` を指す。
- T1943 receipt は v2 へ置換し patch/source の digest を束縛する。旧 v1 を拒否し、general v4 は維持する。
- verifier の判定規則と rc 許可集合は変更していない。異常 variant の認証を許可していない。

## 計算ノードでの生死確認

既存 request `5905.nqsv` を回収した。submit の成功と本走の成功を分離し、終了時刻入りの
`job5905/accounting.txt` を確認してから receipt 判定を行った。終了は 2026-09-18 16:09:44 JST、
accounting Elapse は127秒。queue 待ちをこの所要へ含めない。

`liveness-recovered-verdict.json` と独立監査 `verbatim/recovery-audit.md` が以下を裏付ける。

- job-result v2、receipt T1943 v2 / completed、failure.json 不在。
- receipt → sidecar → job-result、patch → receipt → sidecar、discriminator → receipt の SHA-256 一致。
- patch touch set は `cc/mocc/transaction.cc` 1本、numstat は65追加・0削除。
- workload / verifier / discriminator / TRACE0 preprocess identity はいずれも rc=0、結論は `no-g2`。
- `official_certification=false`、`serializable_elevation_allowed=false`。本走の成功は正式認証や G2 の再現成功を意味しない。

生 artifact の元は `.codex/worktrees/t2780-compute/output/env/pegasus/mocc-trace/job-staging/0:5905.nqsv`。
全体の保全先は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/attempts/job-staging-copy/0:5905.nqsv`。
複製後の `diff -qr` は rc=0。Git にはこの節の小さい receipt と判定証拠を置き、大きい trace/binary は追跡しない。

## レビュー裁定と保証範囲

段2/3・author・段6レビュー2本・引継ぎ監査は `verbatim/` に逐語保全した。
既存裁定 `s4-ruling.md` の §1 A-S1 と §2項1には receipt boolean の採否に不整合があったが、
実装は §2項1の5 field を採り、boolean は build 配線の記録として限定する。コンパイラが実際に
読んだ bytes の独立証明とはしない。TRACE0 の preprocess test と binary watermark 不在は異なる検査である。

段6 B-MF1 は、done 到着後の終端確認不足。今回の5905については accounting 本文と qstat 不在を
親が確認後に判定したことで閉じる。独立 reviewer の qstat は EACCTAUTH で失敗しており、
その再確認を独立実績に数えない。終了時刻入り accounting は両者が直接確認した。

hydrate fixture は interpreter・argv・cwd と probe の環境を観測するが、実 hydrate の PYTHONPATH
全被覆は主張しない。general mode の verifier source は従来の未計装 checkout のままであり、今回の変更範囲外。
rc=1 の compute 実走も今回の5905にはない。fixture の被覆と区別する。

## 検査記録の訂正

旧 `focus-1.log` は login の bounded local がメモリ上限へ到達後、job5893 に dispatch して
1591 passed / 3 skipped、114.92秒で完了した。login 完走でも受入全走でもない。
旧 author の pytest.main 埋込み実走と `mutation-probe-local.json` は `tools/run_tests.py` を通して
いない。実行規律からの逸脱を保持し、正式検査の代替にしない。

変異の再登録は `recovery-ruling.md` と `recovery-mutation-spec.json`。M8 は job-result writer の
binding 欠落拒否が実効 gate で、後段の field assertion による検出とは記録しない。
M2/M3 は条件文字列・診断記録への sensitivity pin とし、correctness kill へ加算しない。
回収時の正式変異試行1/2は interpreter 指定 / walltime 形式で投入前に拒否され、child_started=false。

統合後の全史 provenance は job6361、11460件・新規違反なし、既知違反56件を別途報告した。
既知違反を消したという意味での緑ではない。check_codex_agents と check_docs は rc=0。

## 正式変異と焦点走

正式変異は job6360 / bnode113、固定 `f93281e55`、accounting Elapse=202秒。
`recovery-mutation-3.json` は baseline PASSED (149件)、M0 SURVIVED (149件)、M1〜M8 KILLED、
期待失敗 node の完全集合一致、MISMATCH/PARSE_ERROR/TIMEOUT は0。
`recovery-mutation-attempt-3.json` が外側 job と内側 local runner を束縛する。
内側の local は計算ノードであり login 実行ではない。

| 変異 | 実効検出 | 解釈 |
|---|---|---|
| M1 素の python3 | fallback 正例で hydrate rc=3 | interpreter 選択結果の配線 |
| M2 version 比較削除 | probe 条件文字列の assertion | sensitivity のみ、恒真化の一般保証なし |
| M3 rejected 記録削除 | failure の候補列挙 assertion | diagnostic sensitivity のみ |
| M4 apply 削除 | postimage 不一致 | 実 source への適用 |
| M5 touch set 判定除去 | 不正 touch set が rc0 | 適用前拒否 |
| M6 mode guard 除去 | general で git 呼出が発生 | general 不変 |
| M7 verifier source 差戻し | source argv 不一致 | patched source 到達 |
| M8 binding 削除 | job-result writer の binding differs、正常終了 assertion が赤 | 最終出力の拒否、後段 field assertion の実績ではない |

挙動検出6件と sensitivity 2件を分ける。M0 の注入はコメント1行だけで source diff の実在も
台帳に束縛されている。repo 内 gate と検査を同じ主体が変更できる限り、意図的な弱体化への
完全な防壁ではない。

追加焦点走 job6365 は contract / pegasus_tools / mocc_proof_surface の239件が通過 (5.29秒)。
TRACE0 preprocess 同一性の既存 witness を含む。contract 単独は正式変異 baseline149件、
pegasus_tools 単独も正規 run_tests 経由で72件が通過。旧全14 file焦点走の結果と合算しない。

## 終端手続きの停止

記録後の全史監査job6378は15分のqueue-wait-timeoutでchild_started=false。
10分予約・1時間queue待ちで再投入したjob6403には23:12 JSTという開始予定が表示された。
親はその後の正規headroom観測がlocal可だったことを理由に、QUE中の6403をqdelした。
この取消しでdispatcherがcompute-marker-not-observedと判定し、F47の自動投入停止ラッチが発火した。
これは親の操作による停止であり、実装修正や監査内容の不合格ではない。

ラッチは専用木の `output/pegasus-dispatch/submission-disabled.json`、requestは6403.nqsv。
runbook §7.6/§8に従い、ユーザー自身の端末で投入の永続性・qstat可視性・終了会計を確認する
手番へ返す。ラッチの自動削除・別木への投入での迂回はしない。最終受入・main land・清掃は未実施。
元tipのbundleと全pilot artifactを保全し、専用の `CODEX-HANDOFF.md` に再開手順を残す。

### 再開の追補

上記説明後、ユーザーが「main landまでやれよ。自己改善よろしく」と指示した。
今回の既知取消しによるラッチの復旧を含む指示として、6403のqstat不在と、保全済みJSONとの
SHA-256一致を確認して元ラッチをjob dirへ退避した。人間端末probeを実行済みとは記録しない。
通常のF47条件を変更する実装や解除機構は追加しない。
自己改善は、DW-C00の生産者停止箇所からrunbook §7.6を読む導線と、mutation taskの既存入力形式の
明示だけである。待ち短縮のためのqdelを避け、終端まで正規待ち手で回収する。
