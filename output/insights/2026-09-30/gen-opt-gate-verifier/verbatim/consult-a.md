## 所見

- **R1｜must-fix｜plan §U2・(P4)** — D5 を「gate 専用 assessment」として追加する一方、その不成立を `Integrity.clean()` に接続する手順がない。現行の認証は `clean()` の結果だけに依存する（`plan.md:85–89`、`orchestrator/verifier/model.py:501–519,554–572`）。**放置すると:** Q/V が整合していても emitter 証拠面を欠く build を certified にでき、B7 が通る。**推奨:** D5 の不成立と unavailable を `clean()` が必ず拒否する条件として明記し、D5 だけを壊す fixture で確認する。

- **R2｜must-fix｜plan §U2** — gate file の列挙を `gate_<整数>.log` としているが、不正な名前の file をどう扱うかがない。既存 trace parser も `trace_*.log` の列挙から始まる（`plan.md:42,48–56`、`orchestrator/verifier/parse.py:534–540`）。**放置すると:** `gate_x.log` などが存在しても「gate なし」と判定され、非要求の呼び出しで従来どおり certified になり得る。**推奨:** gate 名前空間に属する不正な file 名も検出し、到達不能として拒否する。

- **R3｜must-fix｜plan §U2** — 照合手順は `_CompactTrace` の列を前提にするが、既存 parser は整数が compact 列に収まらない場合 `_LegacyTrace` に切り替える（`plan.md:42–44,48–80`、`orchestrator/verifier/parse.py:898–905`）。**放置すると:** legacy fallback の走行で照合が省略されるか、検査不能になる実装上の分岐が残り、certified の受理集合が経路依存になる。**推奨:** legacy 経路も同じ gate 照合に通すか、gate 有効時の fallback を明示的に indeterminate にする。

- **R4｜must-fix｜plan §U1・(P3)** — pending txid の `take` は欠落を表せるが、二重の受け渡し、未消費の受け渡し、retry 開始時の残留を検出する状態遷移がない（`plan.md:16,22–23,32`）。現行 Silo の `commit()` は成功時に `writePhase()` を一度通るため通常経路では残留しにくいが、その事実だけでは壊した経路への検査にならない（`F/silo-transaction.cc:759–765`）。**放置すると:** 後続の Q が前の C の txid を使い、CCBench の記録を誤帰属する余地が残る。**推奨:** 試行開始で pending の空を検査し、受け渡し時の既存値・消費時の欠落をそれぞれ異常として記録する状態機械にする。

- **R5｜must-fix｜plan §U1・(P2)** — `((thid+1)<<48)|seq` について seq の 48 bit 検査は計画にあるが、`thid+1` の 16 bit 上限検査がない（`plan.md:18,20–21,59–60`）。**放置すると:** thread ID 65535 以上で上位 bit が溢れ、書き手刻印が衝突・genesis 化して D2 の照合を誤る。**推奨:** 発行側で `thid ≤ 65534` と seq の非零・上限をともに検査し、判定側にも境界 fixture を置く。

- **R6｜should｜plan §U2・(P6)** — B2 は計画上 D1(a) の単独 fixture とされるが、設計上の B2 は「tuple を直接書き換え、後続の他取引がそれを読む」場合に D2a も赤になり得る（`plan.md:99–103`、`gen-opt-correctness-gate/README.md:156–160`）。**放置すると:** 判定器変異の赤理由が重なり、D1(a) または D2a の片方を外した欠陥を fixture の成功から見落とす。**推奨:** D1(a) 用は後続読みを含まない履歴、D2a 用は D1 が整合する履歴に分ける。B4・B5 の D2a fixture でも既存の版・frame 検査が緑であることを先に固定する。

- **R7｜should｜plan §生死確認・(P5)** — F の素の TRACE build を「要求なし」で production CLI に掛ける計画は、gate のない F に従来の certified を出し得る。一方、事前登録案は gen-opt の certified に v2・要求ありを求める（`plan.md:91,119,123–127`）。**放置すると:** 一次資料で F の certified と新関門の certified を同列に読め、意味の版を上げた効果を過大に主張する。**推奨:** F の結果を旧判定による記述的対照と明記し、新関門の certified 集計から除外する。

- **R8｜should｜plan §TRACE=0** — D297 の指定引数は header 比較を有効にする正しい形だが、checker が比較するのは選定した configure 集合の consumer TU である（`plan.md:36–38`、`tools/check_trace0_preprocess_identity.py:59,1076–1102`）。**放置すると:** rc=0 を「全 build 設定・全 protocol で同一」と一般化し、後続 wave の性能 build への主張が強すぎる。**推奨:** report に実際の consumer と macro context を列挙し、記号検査も生成した各性能 YCSB binary に対応付けて記録する。

## scope 外で要る仕事 (裁定パッケージ候補)

- **U5 接続:** gen-opt driver が `require_gate_witness=True` を必ず渡し、発生条件 0 を `not-exercised` として採否に反映すること。現行 campaign 呼び出しは要求を渡さず、計画も既存 campaign には `False` を明示する（`orchestrator/campaign/pipeline.py:682–694`、`plan.md:83,87`）。U2 の完成だけでは、現行 campaign に入る B1 型の迂回は塞がらない。
- **gitlink と Silo 修正の統合:** U1 commit と取引内値の修正を評価対象 pin に取り込み、そこで build・D297・生死確認を取り直すこと。今回の branch と実測だけでは後続 wave の評価対象 build を保証しない。
- **epoch と履歴:** 判定器 bytes の変更で現行 E1 lock は古くなる。旧 lock・receipt を遡って更新せず、新たな発行と md_11 再開条件を land 時に裁定すること（`campaign_lock.py:49–74`、`plan.md:140–149`）。

## plan / brief で正しいと確認した点

- Q/V を別 file に置く判断は、既存 A 行との衝突を避ける。D1 の key 集合、D2b の全 key、巡回時の non-serializable 優先も設計に合う。
- `id_` は F の YCSB payload の先頭 8 byte で、load は key 整数を入れる。RMW で `val_` を写した後に新 `id_` を刻む順序も適切（`F/ycsb.hh:40–52,134–143,179–188`）。
- U0 の `last_commit_txid=0` をそのまま使わず欠落を `-` とする判断、V を既存 TRACE 区間の `#line 658` より前へ置く判断は妥当（`instr-silo-gate-witness-F.patch:26–46,136–151`、`F/silo-transaction.cc:677–700`）。
- 親の「32 本は v1、v2 は 0」は時点付き実測として扱うべきで、plan が歴史 lock と現行 closure を分けた点は正しい。`id_` の読み手不在は提示された検索範囲の結論であり、将来の `createKey()` 利用まで保証しない（`F/ycsb.hh:50`）。

## 総括

計画の照合式は概ね設計に沿うが、**D5 の certified への接続、不正 gate file 名、legacy parser 経路、pending txid の状態管理、thread ID 上限**を実装前に固定する必要がある。この段は静的点検であり、build・テスト・計測結果は判定していない。