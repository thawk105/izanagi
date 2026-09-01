---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1835-t1718-tool-identity
seq: 1
title: [T-1835][T-1718] 事前ビルド道具の身元を生成物への独立期待権威で照合する — 過去 wave が「再現不能」で撤退した壁を非 debug 射影で越えた (コード + テスト + insight、branch worktree-dev-wave-t1835-t1718-tool-identity、変異 10/10 KILLED)
---

## 本文

- **この欠陥は一度実装され、再現不能で撤退した履歴がある。** 2026-08-23 の実機 run で
  `archive_sha256` が初回使用から不一致になり、2026-08-24 の commit `b913bb6e5` が
  「再現不能な archive byte pin」として撤去した。撤去後に残った toolchain manifest 束縛は
  realpath + version の束縛であり、**D1076 が明示的に却下した形**である。D1076 は撤去より後の
  ユーザー裁定なので、本 wave は D1076 を優先した。設計は
  {{D:masstree-nondebug-projection-authority}} と {{D:mocc-compiler-expected-version-body}}。
- **壁を越えた手段は非 debug 射影である。** raw bytes は `CXXFLAGS=-g` が DWARF へ埋める
  build directory の絶対 path により path 依存で再現しない。これは T-1431 と本 wave で
  独立に 2 回実測されている。一方、debug 情報を落とした射影は 6 本の独立 build
  (生成器の二重 build、共有 third-party cache の archive、別 path の login build 2 本) が
  同一値 `844334920db6…` を返した。raw sha256 は 6 本すべて相異なる。
  CCBench の build flag 変更も、計算ノードでの期待値生成も要らないと実測で確定した。
- **probe を回した価値があった。** 初回登録した変異 MU-2 は置換が広すぎて parser 全体を壊し、
  20 node を落としていた。これでは赤理由が 1 つに絞れない。外科的な形へ再照準し、
  本走で狙った負例 1 件だけが赤になることを確認した。probe なしで本走していれば、
  効いていない機構を効いていると誤認していた。
- **段 6 敵対レビューが構造的な穴を見つけた。** `.debug` で始まる名前を持つ relocation section が、
  その `sh_info` が live section を指していても hash から落ちていた。細工した archive が
  射影値を変えずに実コードの再配置を書き換えられる経路で、非 ALLOC・非実行・許可 type の
  条件だけでは塞げない。fix で `sh_info` の指す先も除外対象であることを要求する
  fail-closed 条件を足した。
- **覆した前提が 3 つある。** 親 brief の「`config.h` 一致が実 recipe 再現の証拠」は
  configure 段の再現しか示さない。段 2 プランの「T-1718 は gcc の計算ノード初回 probe が
  land 前に必須」は誤りで、計算ノード receipt に gcc の全文があり body digest は g++ と同一だった。
  親 brief の「道具が変わったことを検出する」も強すぎ、直接検出するのは
  archive 射影または version body の差である。
- **期待値は login node で発行した。** 計算ノードで実際に build した archive の射影は測っていない。
  食い違えば gate は fail-closed で発火し、期待値を再発行すれば回復する。黙って通ることはない。
- **計算ノードの queue 混雑で、実装子と fix 子は 1 度も pytest を走らせられなかった。**
  親・実装子・fix 子の 3 者とも `child_started=false` / `queue-wait-timeout` になり、
  テスト実測はすべて親が queue 回復後に行った。子の報告はいずれも
  「実装済み・未実走」と正直に書かれており、走っていないものを緑と報告した子はいない。
- **受入を 1 度落とした。** 走行中に親が記録 file を作ったため `prerun-clean` で停止した
  (rc=70、テストは未実行)。記録は受入より前に commit する。
- 逐語と変異台帳は `output/insights/2026-09-02_t1835-t1718-tool-identity/`。
- **ユーザー裁定へ返す 3 件**: (1) mocc の期待値が submit authority に束縛されておらず、
  policy を一時変更して読ませ capture 前に戻せば通る。(2) non-sort floor build / mocc の
  CCBench build / 通常 buildcache consumer へ同じ期待権威を広げるか (`buildcache.py` 所有 wave の
  終了待ち)。(3) T-1718 の保証水準を version drift 検出に留めるか、role 混成と launcher まで
  含む compiler identity を要求するか。

## 次の一手差分

### 完了

- [T-1835] masstree prebuild の道具の身元を、生成物 archive の非 debug 射影に対する独立期待権威で
  照合するようにした。射影は version 管理下の pure-Python parser が no-follow の 1 回読みから
  raw digest と併せて導出し、外部 command を新しい信頼点にしない。
  remaining: none
  base: 0ee50c4d082612a28600460b960ac44ef7da6bc839b7e13c5f01855534ec8d24
- [T-1718] mocc trace pilot の compiler を policy の期待 version body と fail-closed 照合し、
  policy の duplicate key 拒否と gflags / glog の未照合 launcher 経路の閉鎖を同じ変更単位で入れた。
  床値側の toolchain 束縛とは役割が違い二度書きにならないことを実測で確かめ、
  version 正規化の規約だけを再利用した。
  remaining: none
  base: ea668e9954fdd30ae890c52aa3bcbab43bf553cf68e7c5b2c2d45074eff3807a

### 新規

- {{T:mocc-policy-submit-authority-binding}} **P2・新規**: mocc の compiler 期待値を submit
  authority へ束縛する。現行は job が policy を source clean capture より前に読み、submit receipt は
  CPU 値だけを持つため、policy を一時変更して読ませ capture 前に戻せば committed policy と異なる
  期待値で gate を通せる。`submit_mocc_trace.sh` へ policy raw SHA と compiler mapping を捕捉し、
  job 側 raw bytes・shell 変数・最終 receipt の三者を照合する形にするかを決める。
- {{T:archive-authority-other-consumers}} **P3・新規**: masstree archive の独立期待権威を
  non-sort floor build、mocc の CCBench build、通常 buildcache consumer へ広げるかを決める。
  現行 gate が効くのは S8b `sort_best` の prebuild だけである。展開は `buildcache.py` を触るため、
  同 file を所有する稼働 wave の終了を待つ必要がある。
- {{T:mocc-compiler-role-challenge}} **P3・新規**: T-1718 の保証水準を決める。
  `tool_version_body()` は起動名の第 1 token を落とすため gcc と g++ の body が同一になり、
  role 混成を検出できない。version drift 検出に留めるか、固定 C / C++ challenge の出力照合まで
  要求するかの二択である。
