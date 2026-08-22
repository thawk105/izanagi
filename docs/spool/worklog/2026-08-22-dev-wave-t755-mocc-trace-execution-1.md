---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t755-mocc-trace-execution
seq: 1
title: [T-755] mocc trace v2のTRACE=1正しさ検証パイロットを実機実行しserializable・anomaly 0を得た (コード+テスト、branch worktree-dev-wave-t755-mocc-trace-execution、変異matrix = 手動kill-check2件ともKILLED)
---

## 本文

- 段6まで完了しmain着地済みのmocc trace pilot adapterを実機投入したところ、既存レビュー
  (コードリーディング中心) では検出できなかった実装欠陥2件を発見した。(1) CPU model環境gateの
  厳密文字列比較が実機の商標記号付き表記で偽陽性拒否 (sibling script `t141_region_profile.sh`の
  正規化パターンを移植し解消)。(2) verifier起動が計算ノードのIntel Python 3.9系で
  `orchestrator`パッケージを解決できず失敗 (`floor_campaign.sh`等の既存版数gateパターンを移植)。
  各々段2プラン→段3敵対相談2レンズ→段4裁定→段5実装→段6敵対レビュー2レンズのフルサイクルを
  経て修正し (段6所見: 1件目real0件、2件目real1件でfix)、手動mutation kill-check
  (正規化/fail-closed判定をそれぞれ無効化する単一変異→新設テストKILLED確認→復元) で
  回帰検出力を実測した。設計判断は {{D:t755-cpu-model-normalization}}、
  {{D:t755-verifier-interpreter-gate}} 参照。
- 3件目の障害 (worktree内staging areaの前回attempt build成果物残存によるhydrate拒否) は
  adapterのコード欠陥ではなく環境状態の問題と判明し、staging tree削除で解消 (コード変更なし)。
- 修正後、実機再実行 (request 934607.nqsv) が環境gate・build・761,914 txnのworkload
  (verifierの`--expected-commits`と実測commit数が一致)・trace採取・verifier起動まで完走し、**verifier_rc=0
  (serializable, anomaly_count=0, total_cycles=0, 12種の整合性検査すべてclean)** を得た。
  compute-node上の実行とlogin nodeからの独立再実行でbyte-for-byte一致を確認した
  (規律3、後付けにしない独立確認)。一次資料:
  `output/insights/2026-08-22_t755-mocc-trace-v2-pilot-serializability.md`。
- TRACE=0性能計測はmocc-trace-v2.patchのtrace.hh include行のコメント残存
  (`check_trace0_preprocess_identity.py`がreject) により本waveでも未実施のまま
  (別途人間手番のcommitが要る、worklog entry 812から変わらず)。TRACE=1の本結果はこの
  欠陥の影響を受けない。
- D662 (受入・land運用簡素化) をピア通知経由で把握したが、主checkout `docs/decisions.md`で
  独立に一次資料照合してから採用した (裏付けなしの初報は保留し発信元へ確認を求めた)。
- 本記録は別sessionが段7まで終えた時点でbranchに取り残されており、2026-08-23の別waveが
  受入・landだけを引き継いだ。引き継ぎ時に既land判定を内容照合で行い (fragment 2件は
  `docs/spool/FOLDED.md`に受領記録なし、insightはmainに不在、姉妹branch
  `worktree-dev-wave-t755-q2-mocc-trace-continuation`はmainに対し差分ゼロ)、未着地と確定した。
  local main 83baeefaを取り込む merge (競合ゼロ) の後もnet差分は5 file / 538 insertionsで
  引き継ぎ時と一致し、mainはmerge-base以降この2つの実装面fileを一切変更していなかった。
- 規律6 (別sessionの作業物の取り込み) に従い、取り込み前にread-only codex 1本で敵対監査した
  (job-id t755-land-audit2、model call 10・wall clock 322秒)。blockerもmust-fixもゼロ、
  nit 1件のみ。gate弱体化 (CPU model正規化の偽陰性化、verifier版数gateのfail-closed破れ) は
  両方とも成立しないと独立に確認された。
- 監査nitは採用した。insight本文が verifier 起動を `python3 -m orchestrator.verifier` と
  書いているのは略記で、実装 (`tools/pegasus/mocc_trace_pilot.sh`) は環境gateが解決した
  interpreterを絶対pathで起動する。この差をinsightへ明記した。**選ばれたinterpreterの実体
  pathはこのrunでは記録されていない** — scriptはVERIFIER_PYをreceiptにもlogにも書かない。
  記録を足す改修は実装面のためscope外とし、次の一手へ候補として残す。
- 引き継ぎwave側で見つけた記録の誤りを1件直した。本文が実行規模を`751,914txn相当`と
  書いていたが、この数値は一次資料 (insight・verifier出力JSON) のどこにも存在しない。
  実測・期待値とも761,914 txnであり、誤記として是正した。
- fragmentのtitleが単一引用符で囲まれていた。`tools/spool_fold.py`のfrontmatter解析は
  引用符を剥がさずcanonical見出しへそのまま埋めるため、land前に除去した。同型の着地が
  mainのworklogに3件ある ({{F:spool-title-quote-leak}})。
- 引き継ぎwaveで実測した検査: `check_wave_startup.py --mode resume --external-handoff` rc=0、
  全史`check_ai_provenance.py` rc=0 (5030件・新規違反なし)、`check_docs.py` rc=0、
  `spool_fold.py --dry-run` rc=0 (status: planned)、焦点走 (`test_mocc_trace_job_contract.py`
  + consumer の `test_hooks.py` + `test_check_trace0_preprocess_identity.py`) 497 passed /
  1 skipped。受入全走は本fragmentを含む最終tipに対して投入するため、その結果は本entryに
  含まれない (landの受領証が一次資料)。
- 段8の自己改善は候補2件。(i) title引用符の漏出は `docs/spool/README.md` の共通frontmatter節へ
  明文化し、{{F:spool-title-quote-leak}} を起票した。機械検査 (spool frontmatter lint) は
  gate新設のため未実施で裁定待ち。(ii) `dev_wave_codex.py` の `--reasoning` が段5/6以外で
  必須である旨をdocsから読み取れず、本waveで実際にrc=2の即死を踏んだ。統合先の候補2箇所
  (`DW-O01` と `DW-C01`) はどちらも先へ進めなかった — `DW-O01` へ1行足すとdev-wave docsの
  L1.5予算を9692 bytes > 9566 bytesで超え、`DW-C01` は節全体が `tools/check_docs.py` の
  exact literalでpinされていて実装面の変更なしには触れない。自己改善契約の「予算に収まらず
  意味等価にもできなければ変更を止めてユーザー裁定へ返す」に従い未実施とした。

## 次の一手差分

### 更新

- [T-755] Q2(a) mocc trace pilotの実機実行 (TRACE=1) が完了し、serializable・anomaly 0の
  結果を得た。TRACE=0性能計測は人間手番のsource commitが必要なまま未着手 (P1・Q1(a)・
  Q3(a)は既存記述のまま完了)。残る候補は2つ — (i) TRACE=0性能計測 (人間手番のsource commit
  待ち)、(ii) pilot scriptが選んだverifier interpreterの実体pathをreceiptへ記録する改修
  (実装面、本waveではscope外)。
  base: f1f86688e961f4fc57944277a8c6c273077f7222309a218695669e71f6087523
