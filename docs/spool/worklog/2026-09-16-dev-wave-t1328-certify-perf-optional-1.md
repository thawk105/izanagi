---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1328-certify-perf-optional
seq: 1
title: [T-1328] perf 候補全滅で較正認証を止めず canonical probe の結果だけで分岐する (コード、branch worktree-dev-wave-t1328-certify-perf-optional、変異 matrix = baseline PASSED・10/10 KILLED・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「`tools/pegasus/certify_calibration.sh` が policy 候補の perf smoke 全滅時に
  `exit 2` する件を直す。失敗を成功扱いに変える方向は採らない — perf が本当に要る判定と、
  perf 無しでも成立する判定を分けて、後者だけが通るようにする。本題の分岐修正だけ」。
  詳細と逐語は `output/insights/2026-09-16_t1328-certify-perf-optional/`。
- **依頼の前提が一次資料と食い違い、段 4 で根拠を差し替えた。** 依頼文の「この計算ノードに
  perf は無く、perf 不在が較正認証を止めるのは実害である」は計算ノードについて現在成り立たない。
  `output/env/pegasus/calibration/job-staging/` の 19 attempt で **perf 段の失敗は 0 件**、
  直近 2026-09-15 の 3 attempt は `/usr/lib/linux-tools-5.15.0-135/perf` を選んで LLC 実カウンタを
  得ており `calibrate_rc=0` だった。言えるのは「観測範囲では perf 段の失敗を確認できない」までで、
  別ノード・kernel 更新・linux-tools 撤去・counter 権限変更が反例条件になる。
  **続行根拠は実害ではなく D352 違反の是正へ差し替えた。** 発火条件が仮想でない根拠は、
  D352 自身の実測 (2026-08-12 に計算ノード 8/8 で linux-tools 不在) と、本 wave の実測
  (login node の policy 候補 2 本が実行不可) の 2 つ。
- **親 brief の不変条件 1 は段 3 が撤回させた。** 「現在 fail する判定を 1 つも pass に変えない」は
  D494 と両立しない。D494 は候補全滅だけを degrade の根拠にせず probe に決めさせる裁定であり、
  「候補全滅 + literal perf が動く」入力の到達可能性拡大はその意図そのものである。
  {{D:perf-probe-decides-not-candidate-exhaustion}} で到達可能性と最終受理を分けた。
- **段 6 焦点再レビューが親の「ちょうど」の量化を不正確と判定し、親が受け入れた。**
  (a) 「候補全滅 + canonical available」は到達可能性の条件であって accepted の十分条件ではない。
  (b) 減分は旧版で実際に accepted になる入力との交差で書くべき。
  (c) **第三の縮小経路がある** — policy 候補配列に同一文字列を重複させると
  `perf_preflight.py:237` の重複検査が失敗し rc=2 になる (現行 policy の 2 候補は重複していない)。
  (d) 追加 probe のぶん所要が増えるので予約期限近傍の完走可能性まで不変とは言えない。
  同レビューは「`schema_v2` の accepted 制約が唯一の保証」という親の記述も訂正させた。
  実際は `sweep.py:272` → `report.py:106/115/121` → `cli.py:1039/1055` → `schema_v2.py:529/531` の多層。
- **login node の緑が隠していた欠陥を、計算ノードへの dispatch が暴いた。** 変異 baseline を
  計算ノードで走らせて初めて `probe_error` 対照 2 件が `assert 0 == 2` で赤になった。
  原因は fixture が `os.kill(os.getpid(), signal.SIGTERM)` に依存していたことで、
  **SIGTERM の無視設定は exec を越えて継承される**。継承環境では kill が起きず fixture は
  正常な CSV を書いて rc=0 で終わり、receipt は `status=available` になる。
  **test は緑のまま、意図した経路を 1 度も検査していない。** 詳細は
  {{F:inherited-sigterm-disposition-voids-signal-fixture}}。fix は login node で
  `SIGTERM=SIG_IGN` を親へ設定して再現し (修正前 2 件赤・receipt available、修正後 2 件緑)、
  SIGKILL へ替えて閉じた。
- **段 3 レビュー A の静的予測を実測が修正した。** A は M3・M4・M7・M8 を「別層が先に拒否するので
  帰属しない」と予測し親は erratum で再照準を指示したが、**実測ではいずれも狙いどおり新規テストが
  捕まえた**。とくに M8 は懸念された `holdout_observation` ではなく
  `test_cli_no_perf_preserves_all_sweep_reps` が検出した。一方 **M9・M10 は過剰決定**で、
  挙動検出は `test_cli_no_perf_*` だが `test_official_perf_closure.py` の構造検査も同時に赤になる。
  冗長 gate として明記し単独変異の挙動証拠から外した (DW-M03)。
- **DW-O16 が名指しする実行環境依存の型なので、親が login node で実機確認した。**
  (1) 全滅時 `CALIBRATE_PATH` = `/usr/bin:<元 PATH>`、選択時 = `<TMPDIR>/bin:/usr/bin:<元 PATH>`。
  (2) `/usr/bin/python3.10` が版数 smoke rc=0 かつ `perf_preflight` を import rc=0。
  (3) 常に成功する偽 `perf` を PATH 先頭へ置いても対象 3 file が 72 / 79 / 86 と素の環境と同数。
  **未実施:** canonical probe 自体の実走 (login では guard が `perf stat` 直叩きを拒否)、
  計算ノードへの認証 job 投入。
- **親が踏んだ罠。** `orchestrator/tests/test_pegasus_calibration_workload.py` は自走 harness を
  持たず pytest 専用 allowlist にあるため、`python3 <file>` は 0 件収集の偽緑 (rc=0・出力なし) に
  なる。`pytest.main` 経由で走らせ直して 79 件を確認した。
- **達成しないこと。** 認定較正取得は perf 不在では回復しない (全 sweep を終えても rejected・
  rc=1・未登録)。no-perf 走は 5 点 × 3 rep = 15 subprocess を消費し、全点 miss rate 欠損なので
  早期打ち切りも成立しない。perf 無しの測定証拠を正式較正へ昇格させる可否は裁定へ返す。
- **記録の訂正。** 段 5 実装報告の「既存テスト期待値の変更なし」は無限定には成り立たない。
  裁定で指定した閉包 inventory への CLI・sweep 追加と runner guard 期待値の
  `("not use_perf",)` → `("not use_perf", "use_perf")` は行っている。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、focus 1、fix 2)。
  変異は probe 1 回 + 本走 1 回 (計算ノードへ dispatch、各 11 走)。

## 次の一手差分

### 完了

- [T-1328] `certify_calibration.sh` の perf 全滅時 `exit 2` を D494 の形へ直し、
  `use_perf` を CLI → sweep → runner へ伝播させた。変異は baseline PASSED・10/10 KILLED・
  期待 node 完全一致。受入全走の結果は本 fragment の追記で記録する。
  remaining: none
  base: 1eb134155885dd382567a3dfdf0bb74e72ab75a4383624ee4ef0da9f9a37b58a

### 新規

- {{T:no-perf-calibration-promotion}} **P2・新規・ユーザー裁定待ち**: perf 無しの測定証拠を
  正式較正として何に使えるようにするか。現契約では全 sweep を終えても
  `analyze.py:48-57` が飽和点を選べず、`report.py:106-123` と
  `orchestrator/campaign/env_contract.py:606-631` (content-addressed registered path と accepted を
  要求) が登録・利用への道を閉じる。昇格には「perf に依存しない較正が何を保証するか」という
  新しい認証契約が要る。段 3 相談 B と段 6 レビュー B が独立に同じ所見を real・scope 外と判定した。
  択一は (a) 現状維持で証拠保存だけに留める、(b) no-perf 較正の別 schema と受理条件を新設する
  (D493 の「degraded は緩い分岐ではなく別の厳しい分岐」に従う)、(c) no-perf 走そのものを
  evidence-only と明示して較正系列から外す。
