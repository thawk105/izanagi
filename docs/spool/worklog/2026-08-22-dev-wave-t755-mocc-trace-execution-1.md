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
- 受入全走 attempt 1 (tested-main 83baeefa / tested-tip 01c7d2fa) は
  26 failed / 14259 passed / 96 skipped で rc=1 で戻った。赤は全件
  `orchestrator/tests/test_sort_swo_oracle.py` で、oracle が third-party cache の masstree に
  `config.h` を見つけられず `outcome='config-h-missing'` で UNAVAILABLE を返すことによる。
  本waveの差分 (mocc trace pilot script とその契約テスト) からは到達しえない面である。
  `DW-O18` に従い tested-main 83baeefa 単独の detached worktree で当該 file だけを再走し、
  **同じ 26 failed が再現**することを親が実測した (フレークではなく決定的な非帰属赤)。
  main の worklog は同じ 26 件を「担当外」として既に記録している。
- attempt 1 の非帰属判定は `check_acceptance_reds.py` の `git worktree add` が rc=128 で
  失敗し `status=invalid-input` で判定不能に終わった。同じ `git worktree add` を手で再現すると
  rc=0 で成功する。投入時点で他に 3 本の受入全走が同じ repo に対して走っており、共有 `.git` への
  ロック競合による一過性失敗と判断した (main の worklog に同型の先例あり)。attempt 2 を投入する。
- attempt 2 も判定器が別型の一過性失敗で終わった (submodule の cache-only URL rewrite が
  rc=255、共有 `.git/config` へのロック競合)。全走自体は 36 failed / 14249 passed で、
  attempt 1 の 26 件に `orchestrator/tests/test_t810_coordinator.py` 系が加わっている。
  投入時点で他 wave の受入全走が 4 本同時に走っており、赤の件数も判定器の失敗も
  並行度に連動する。いずれも本 wave の差分の面ではない。以降は既知の一過性失敗
  (`invalid-input` / `no-verdict-infra` / `claim-timeout`) だけを再試行し、
  `status=attributable-red` が出たら即停止する自動ループへ移した。
- **ユーザー裁定 (2026-08-23): 非帰属判定器 `tools/check_acceptance_reds.py` を使わない。**
  「40 分も main land を長引かせるものは使い物にならない。これは進化探索を回す
  リポジトリでもある」。同じ裁定が並行セッション 2 本からも通達され、三重に裏が取れた。
  親は再試行ループと走行中の受入を停止し、判定器の probe 残骸 worktree も撤去した。
  実測した所要は attempt 1 が pytest 222.10s の後に判定器 42 分、attempt 2 が判定器 7 分、
  attempt 3 は 2 時間 12 分走行しても未終了。律速は赤 1 件ごとに使い捨て worktree を
  作って直列再走する構造で、13900 file・lustre 上では赤 36 件で 40 分を超える。
- **この裁定の帰結として本 wave の land は保留する。** 受入受領証は (i) 全緑か
  (ii) 赤が全て非帰属と判定された、のいずれかでしか出ない。判定器を使わないと (ii) が
  閉じるため、`test_sort_swo_oracle.py` の 26 件が残る限り受入は緑にならない。
  **赤を親の自己判断で担当外と認定して land することはしない** (絶対規律 2)。
  26 件の除去は別セッション `remove sort-swo-oracle test` が担当しており、着地後に
  受入 1 回 (約 4 分) と land を行えばよい。段 1〜8 と規律 6 の取り込み監査は完了済みで、
  branch worktree-dev-wave-t755-mocc-trace-execution を残す。
- 26 件の根本原因を特定し 4 セッションへ共有した。`sort_swo_oracle` の oracle environment
  解決が masstree の `config.h` を持つ dependency root を要求するが、この機体では候補
  3 経路とも解決しない。共有 cache は `config.h` も `configure` も持たない素の clone で
  (`tools/pegasus/README.md` §6 の設計どおり)、どの worktree も ccbench を build して
  いないため build tree 側の候補も存在しない。**このテスト群は別 wave のビルド副産物の
  残存に暗黙依存している。** 共有 cache へ `config.h` を置くのは設計に反するため行わない。
- 共有した所見のうち、判定器の代替設計 (赤 1 件ずつ probe する代わりに tested_main で
  全走を 1 回回して赤集合を差分する) が別セッションからユーザーへ諮られ、**全走差分方式
  への再設計として裁定された**。計算量が O(赤の件数) から O(1) になり、probe worktree が
  不要になるため rc=128 競合・submodule rewrite rc=255・残骸放置・判定中の main 競走が
  構造的に消える。相手側の裏付け実測は 1 dispatch = 約 22 秒の固定費で、26 件直列は
  dispatch だけで 572 秒となり 5 分は原理的に不可能というもの。
- 差分方式に固有の偽陽性リスクを実測から指摘して返した。本 wave の 2 回の全走は
  並行受入 3 本で 26 failed、4 本で 36 failed であり、**赤集合は並行度で動く**。
  main 側を空いた時間、tip 側を混んだ時間に撮ると差の 10 件が attributable 候補として
  出て、無関係な wave の land を再現しない形で止めうる。あわせて main 側の赤集合は
  tested_main の SHA だけで決まり wave に依存しないため、repo 外へ cache して全 wave で
  共有すれば全走 2 回が 1 回に畳めることも渡した。
- **この再設計が着地すると本 wave の land 条件が変わる。** 26 件は main 側にも tip 側にも
  出るため非帰属と判定され、26 件の除去を待たずに受領証が出る。したがって本 wave の
  再開条件は「`remove sort-swo-oracle test` の着地」または「判定器再設計の着地」の
  **いずれか早い方**である。

## 次の一手差分

### 更新

- [T-755] Q2(a) mocc trace pilotの実機実行 (TRACE=1) が完了し、serializable・anomaly 0の
  結果を得た。TRACE=0性能計測は人間手番のsource commitが必要なまま未着手 (P1・Q1(a)・
  Q3(a)は既存記述のまま完了)。残る候補は2つ — (i) TRACE=0性能計測 (人間手番のsource commit
  待ち)、(ii) pilot scriptが選んだverifier interpreterの実体pathをreceiptへ記録する改修
  (実装面、本waveではscope外)。
  base: f1f86688e961f4fc57944277a8c6c273077f7222309a218695669e71f6087523
