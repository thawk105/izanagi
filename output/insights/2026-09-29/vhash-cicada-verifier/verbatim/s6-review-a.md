## 所見

- **RV-1 — must-fix — [launch_cicada_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:471)、[broken-cicada-stale-read-ro.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/patches/broken-cicada-stale-read-ro.patch:21)**
  初回実測では 3 本とも巡回を検出したが、R4 の規則に帰属した witness は各 **0 件**だった。各 run の verifier JSON が報告する witness は総巡回数のうち先頭 20 件、事象ログは各 800 件である。現行パッチは事象の 200 件制限を外した版で、初回実走時のパッチ hash とも異なる。**影響:** 「期待した経路で検出」2 本以上という完了条件は未達で、巡回だけを根拠に正例の成功を一次資料へ書けない。**推奨:** 全件出力の J1/J2 再走を親が照合し、帰属した witness の C/R/W 行と事象行を提示する。帰属できなければ R4 の裁定どおり段 4 に戻す。`j1-c`・`j2-c` の結果ファイルは今回読めず、再走は親が照合する。

- **RV-2 — should — [instr-cicada-trace.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/patches/instr-cicada-trace.patch:80)、[broken-cicada-stale-read-ro.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/patches/broken-cicada-stale-read-ro.patch:60)**
  R の版は読み取り時に保存しているが、stale-read-ro 実測では commit 時の `ver_->ldAcqWts()` と保存値の不一致が **43 件**あった。stock の 0 件は対照の安定性を示す一方、43 件は壊し走行の全 R が同じ版オブジェクトを指し続けた証拠にはならない。**影響:** 当該読み取りの版と payload の対応が未確認のままでは、stale-read-ro の巡回を意図した古い版の選択に帰属できない。**推奨:** 不一致の txid・key を特定し、版の再利用や読み取り時点から commit までの変化を調べる。解決まではこの走行の trace 忠実性を保証済みと記さない。

- **RV-3 — should — [launch_cicada_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:307)**
  TRACE=0 の命令列比較は YCSB binary の `transaction.cc`、`ycsb_cicada.cc`、`util.cc` を網羅する。ただし変更した `transaction.hh` は `tpcc_cicada.cc`、`bomb_cicada.cc`、`sbomb_cicada.cc` にも include され、これらの TU は比較していない。**影響:** 命令列同一性の実測範囲を Cicada の全 workload に広げて主張できない。**推奨:** 主張を実測済み YCSB 構成に限定するか、残る workload の TU も同じ方法で比較する。

## 確認した点

- 計装は通常 commit で `cpv()` 後、read-only commit で早期 return 前に出力する。abort 経路には出力しない。初期版は `(1,0)` に写像され、`initial_wts` は worker 起動前に設定される。ReadElement の保存値は通常の copy/move で要素と一緒に移る。point read/update の範囲で、read-own-write の局所読みを独立した版読みとして出さない扱いも整合する。
- L0 の 4 run は巡回・数値 integrity 違反・READ_WTS_MISMATCH が各 0、C 行数と benchmark commit 数が一致した。TRACE=0 の比較対象 3 TU は正規化命令列が一致し、`nm`・`strings` に trace 残存がなかった。前処理出力の差は空行のみだった。
- 壊しパッチは各 1 箇所の挙動を変え、stock とは別 checkout に適用される。`attribute_break` の rw 辺の向き、初期版写像、no-rts-update の `v_ver < tx_wts` 判定は R4 と整合する。ただし帰属済み witness が初回結果に無いため、指定された C/R/W 行との実例照合は実施できなかった。
- 新 fixture 2 本と R8 の登録簿追加は既存 entry を変更していない。R6 erratum は、M-V1 が既存テストでも検出され、新テスト固有の検出力を示さないと正しく記している。
- 現時点で言えるのは、実測した YCSB point read/update 履歴で stock の巡回 0 と壊し走行の巡回検出を観測したことまで。`certified` ではなく campaign の受理経路にも未接続で、scan の phantom、insert/delete、promotion、group commit、他 workload は未検証である。

## 総括

**正例の経路帰属が未達**であり、現行パッチの全件出力再走も今回の資料からは確認できない。親による J1/J2 再走の照合と stale-read-ro の 43 件の不一致調査を終えるまで、R4 の完了判定や後続 VHash の正しさゲート成立は主張できない。