# T-2484 — dispatch外側timeoutの全区間契約

- authority: none
- default_effect: no-state-change
- 裁定: D2148項8の(a-1)+(a-3)。D2044項29の(b)不採用・(c)理由付き非拒否診断を維持。
- 一次資料: `output/insights/2026-09-18/t2484-watchdog-segments/README.md` §6。
- wave: dev-wave-t2484-timeout-contract。着手時local main: `7975385b55a2e3451f6c80d584a9312f44d5199d`。
- 原ログ: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/`。
- 逐語の可逆正規化: git diff検査に抵触した行末space/tabだけを除去した（可視文字不変）。
  `verbatim-normalization.json`に原文/正規化後のSHA256・byte数と1起点の行番号別除去suffix（hex）を保存。
  対応行の改行直前（最終行に改行が無ければ末尾）へsuffixを戻すと原文を復元でき、原文一致を実測した。

## 実装と主張範囲

collection、baseline、mutationの外側待機は `max(spec.timeout_seconds, P+Q+W+G+A+C)`。
Pは前段・観測・終端処理への運用余裕180秒。Q/W/G/A/Cは内側dispatcherのqueue、walltime、
overall grace、回収、cleanupの値を計上する。既定は5130秒、Q3600/G600なら8130秒。
collectionは既定W、実行側は既存walltime overrideを反映する。specが予算より長ければ短縮しない。
dispatchでは短いhang値を外側に使わず、localでは従来の短いhang値を維持する。

Pは既往3849 receiptの前段max15.9秒に10倍以上の余裕を取った暫定値であり、harness起動・
poll・I/O・終端処理の厳密な上限ではない。全区間を計上した有限の運用予算であり、先行発火ゼロや
orphan holdの消滅は保証しない。区間認識watchdogは追加していない。

既存collection gateは元specのQ+G判定を維持する。Q1800/G600でspec2399は従来どおり拒否、
2400は通過して実待機6330秒。新しい拒否gateはない。stderrに区間内訳・実効値と理由を出す。
内側dispatcherの期限、回収、qdel、hold、復元、失敗node完全一致、resumeの規則は変更しない。
rc16をKILLED/TIMEOUTへ読み替えず、既存hold条件に該当する場合だけhold・変異残置を維持する。

## 独立検証と修復

計画1本、相談2本、author1本、レビュー2本、fix1本、焦点再レビュー1本を正規の隔離Codex subprocessで実施。
逐語は`verbatim/`。相談とレビューのmust-fixは0。レビューの文書should1はM06のhold条件を明示して処置した。
全caller、既存gate、walltime override、local hang、内側holdとresume弱化の疑いはrefuted。
焦点再レビューは数値4条件と17変異の期待集合を独立に検算しGO。実測と静的判定は分ける。

consumer焦点走で2件の実在回帰を検出した。`test_mutation_worktree.py`の疑似dispatcherはimport時に
実行本体とSystemExitが走る構成だったため、新helperの定数importでharnessがledger作成前に終了した。
fixtureをimport時は副作用なしにし、実dispatcherと同じ5定数・walltime parserを付けた。
生成CLI本体と既存テスト期待値はAST比較で不変。production側の回収規則を変える修復はしていない。

## 変異事前登録

`mutation-spec.json`はP0（max引数交換の等価正例）、M1〜M15（全区間の各項・長いspec・各caller・
hang・既存gate・W経路・local期限）、M16（疑似dispatcherのimport guard撤去）を固定する。
診断専用1nodeを除く追加32nodeとM16の既存2node、計34nodeを選択する。
時間契約の変異は引数と数値契約の検出力であり、実際の長時間hang確率の測定ではない。
診断文字列の赤はkillに数えず、失敗nodeの完全集合一致を維持する。

## 実測済み記録

- harness単独: 148 passed（job9130、8.69秒、Elapse14秒）。bounded localのcap OOM後、正規runnerが
  計算ノードへ自動移送した。初回localの未完結果を緑とは数えていない。
- consumer初回: 837 passed / 3 skipped / 2 failed（job9136、56.85秒）。上記fixtureの回帰であり、
  失敗を環境由来とせず修復した。修復前の赤はこの記録に残す。
- 修正したworktree wrapper testのfile単独走: 47 passed（job9292、5.70秒）。失敗した2nodeも成功。
  焦点レビューの実走待ちpartialを親がこの結果でclosedとした。文書所見もclosed、regressedなし。
- anchor `a13570f973de748696b103035dcce95fd501b2ba`、fixture修復 `d93c15926b5a0d7e73804698bb8c8592843c5e2a`。
  commit前preflightとcommit後全史provenanceは新規違反なし。既知の履歴違反はそのまま保持する。
- 変異本走は修復後commit固定、baseline PASSED、17/17期待一致（16 KILLED、等価P0 SURVIVED）。
  MISMATCH/PARSE_ERROR/TIMEOUTは0、失敗node集合は全件完全一致。
  `mutation-results.json`、`mutation-attempts.json`とwrapper受領証を保存した。
  wrapperのterminal_ledger/shared_snapshot_matches/teardown_completedはtrue、child_rc=0。
  証拠をjob dirへ回収し、使い捨てcontainerを撤去した。
- 全8workerがaccepted、62 model calls、CLI reported tokens合計343894（launcher receiptの集計）。
  親セッションの使用量・金額や性能指標を表す値ではない。
