---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t614-provenance-ledger
seq: 1
title: [T-614] provenance 監査に既知違反 6 件の固定台帳を入れた — 裁定どおり 6 SHA だけを置き、7 件目は恒久緩和にあたるため入れずに裁定へ返す (コード + docs、受入 7131 passed / 20 skipped、変異 9/9 で登録 node が赤・SURVIVED 0、branch worktree-dev-wave-t614-provenance-ledger)
---

## 本文

- **裁定 (worklog 284) の案 3 を実装した。** 6 SHA を checker 内の固定台帳
  (full SHA・finding 種別・裁定 ID) に置き、監査を既知と新規に分離して**正常完了時の rc は新規だけで
  決める**。既知は rc に関わらず stdout へ公開する。履歴は書き換えていない。設計は {{D:known-violation-ledger}}。
  `run_tests.py` の受入形でない走行への 1 行警告も同 wave で入れた ({{D:nonacceptance-run-warning}})。
- **受入条件は充足したが、言い方を正した。** 台帳導入前の既定の全走は **rc=1 / 1660 件中 7 違反**で、
  裁定の 6 SHA を全部報告した。ただし実測は 7 件なので、**「厳密に 6 件」という読みでは不成立**である
  (段 3 レンズ 3 の指摘を採用)。充足したのは「指定 6 SHA がすべて報告されること」。
- **裁定文が疑った T-300 退行は refuted。ただし rc=0 の発生原因は unresolved。** 既定範囲
  (`policy 50c1ef4e` + `--ancestry-path`、1659) と素の `rev-list 50c1ef4e..HEAD` (1659) は
  同一の 7 違反・同一 rc=1 を返す。段 3 が `git blame` で範囲式が初出 commit のまま不変であること、
  T-300 系 5 commit が範囲式を変えていないことを確認した。rulings session が rc=0 を見た当時の
  cwd・HEAD・実行経路・生コマンドは保存されておらず、**「解消済み」とは記録しない**。
- **7 件目 `3f2c43d7` は台帳に入れなかった。** 段 3 レンズ 3 が worklog (285) を掘り当て、
  **ユーザーが同 commit へ「今回だけ免除して land する。防壁の恒久的な緩和はしない」と
  裁定済み**だと判明した。台帳への追加はその恒久緩和そのものである。よって実装後も既定監査は
  **既知 6 / 新規 1 / rc=1** のまま残る。これは設計どおりの期待値であって緑ではない。
  **本 wave の commit は 1 件も違反に含まれない** (唯一の新規 finding が `3f2c43d7`)。
- **段 6 の fix が fail-open を作り、焦点再レビューが差し戻した — 本 wave で最も危なかった箇所。**
  「off-HEAD の部分 range で正常な既知 entry が偽 stale になる」を直す 1 巡目 fix は、policy epoch が
  現在の `HEAD` から見えないとき台帳 entry を stale 判定から外した。偽赤は消えたが、**checker の
  expected finding 生成が壊れたときに rc=0・known 公開なしで通る fail-open** になり、追加テストが
  その fail-open を期待値として固定していた。焦点再レビューが規律 2 違反として `regressed` 判定し、
  2 巡目で fail-closed へ倒し直した (epoch の可視性によらず常に stale rc=2、理由を 2 種に分けて診断)。
  偽赤側は非権威な invocation での過剰拒否として受け入れた — `PR-C03` が既に権威を既定 full 監査に
  限定しており、degraded な走り方で rc=2 になるのは安全側である。
- **3 巡目は「揮発値を焼き込んだテスト」の削除。** 2 巡目が追加した
  `test_default_history_reports_six_known_and_one_new` が `assert len(stdout_lines) == 7` で赤になった
  (実際は 16 行。waiver block を数え落としていた)。**行数を直さず削除した** — 実 repository の
  生きた監査結果を期待値に焼き込んでおり、無関係な wave が waiver を 1 つ増やすだけで赤になる。
  「既定の全走が既知 6 / 新規 1 を返す」は観測値であって不変条件ではない。
- **段 6 レビュー 2 本 + 焦点 1 本が計 6 件の must-fix を返した** — validator の型破損が rc=2 に
  ならない / 上記の偽 stale / 変異 M1 を殺すテスト不在 (生成 SHA が共通 prefix を持たない) /
  変異 M4 の control が恒真 (自分で台帳を空にしてから空を確認) / 裁定が明示要求した
  correction・waiver 合成テスト不在 / 警告が bounded 子で二重表示。**いずれもレビューが無ければ
  land していた。**
- **変異本走は 2 回中止してから成立した。いずれも harness の fail-closed が正しく働いた結果で、
  変異の結果ではない。** (1) `--runner-mode dispatch` + 素の runner は、runner が targeted 走行を
  ローカル実行して receipt 行が 0 件になり baseline が `PARSE_ERROR`。(2) `--runner-mode local` は
  collection 段が rc=16 — `run_tests.py … --collect-only -q` が bounded scope の cgroup attestation で
  落ちる。**(2) は本 wave の差分と無関係**で、`DW-O19` の手順で `run_tests.py` を起点 `c9990bc2` の版へ
  一時的に戻して同じ rc=16 を実測した (復元後 `git diff HEAD` 空)。同時刻の通常 targeted 走行は
  rc=0 / 178 passed なので `--collect-only` 特有の既存条件である。runner へ `--force-dispatch` を
  足して dispatch 経路で本走した。login ノードでの `python3 -m pytest` 直起動は hook が拒否したため
  迂回していない。初回台帳は erratum として凍結した。
- **provenance docs family の予算は引き上げていない。** `PR-A02` へ台帳契約を入れるため、
  補助的な `git log --format='%(trailers:key=AI-Agent)'` の確認手順と `PR-A03` の一部を意味等価に
  圧縮した (8981 → 8994 / 9000 bytes)。
- **段 8 の改善候補 2 件のうち、reference へ入ったものは無い。** (1)「scheduler へ届かず rc=16 の子は
  未実走と書く」は `DW-S05-C` に既に逐語で存在し追加不要だった。(2)「変異 harness の
  `--runner-mode` は runner が実際にその経路を通ることを要求する (targeted 走行は既定で local に
  落ちるため dispatch では `--force-dispatch` が要る)。spec と out は checkout 外へ置く」は
  `DW-M05` への実測に基づく追加候補だが、dev-wave 4 文書の aggregate 予算が
  **25,187 / 25,200 bytes で余地 13 bytes** のため収まらない。**予算のために安全義務の文面を
  圧縮・削除することは自己改善契約が禁じている**ので、変更せず裁定パッケージへ送る
  ({{T:dev-wave-mutation-runner-mode-doc}})。予算引き上げは提案しない。
- 正本 = `output/insights/2026-08-07_t614-known-violation-ledger/README.md`
  (段 4 裁定、段 3 の 3 レンズ、段 6 のレビュー 2 本と焦点、変異 spec・台帳・erratum を全文凍結)。

## 次の一手差分

### 完了

- [T-614] 案 3 の既知違反台帳を実装し、受入条件 (台帳導入前に既定の全走が指定 6 SHA を報告すること) を
  実測で検証した。`run_tests.py` の 1 行警告も入れた。7 件目 `3f2c43d7` の恒久的処置は
  {{T:provenance-known-violation-residual}} へ分離する。
  remaining: none
  base: 72011b0f0bffaef6adcd0d3729258f1cc5c0a2df39e309e749d2f410a1296a1c
- [T-596] 診断項。対象 6 SHA は [T-614] と同一で、台帳実装が本項を閉じる。残論点 2 件は
  (286) の裁定どおり現状維持 — merge commit への trailer 要求は既存契約のまま、逐語凍結先の
  `.py` も実装面判定のまま。
  remaining: none
  base: b74d26d8256c95348d72835d3fd5d07efe6a42fb8363464ef9b0b89376299ccc

### 新規

- {{T:provenance-known-violation-residual}} **P1・ユーザー裁定待ち**: `3f2c43d7` の恒久的処置。
  台帳追加は「防壁の恒久的な緩和」であり 2026-08-07 にユーザーが明示的に拒んでいるため、本 wave では
  入れなかった。結果として既定監査は既知 6 / 新規 1 / rc=1 のまま残り、**1 件ぶんの手作業帰属が続く**。
  原因は判明している — trailer 自体は在るが `AI-Agent:` と `Co-Authored-By:` の間の空行で Git が
  trailer block と認識していない。選択肢は (a) 現状維持、(b) 台帳へ追加 (恒久緩和を撤回する再裁定)、
  (c) 別経路 (`PR-C01` は correction の再開放を禁止)。成果物影響: 研究成果物の値は不変で、
  変わるのは commit gate の受理集合と、新規違反が 1 件の既存分に紛れる残余リスク。
- {{T:provenance-default-range-blind-spot}} **P2・新規**: 既定監査の範囲が `--ancestry-path` である
  ため、policy 導入前から分岐した branch 上の違反 commit を後日 merge すると、素の range には
  入るのに既定監査から落ちる。本 wave の実測では現に no-op (1659 = 1659) だが将来の穴である。
  素の `policy..HEAD` へ変えるのは strict な強化だが裁定外なので実装しなかった。成果物影響:
  この形の branch に新規違反が入ると、rc=1 であるべき既定監査が rc=0 になり受理集合が広がる。
- {{T:dev-wave-mutation-runner-mode-doc}} **P3・新規**: `DW-M05` に「`--runner-mode` は runner が
  実際にその経路を通ることを要求する (targeted 走行は既定で local に落ちるため dispatch では
  `--force-dispatch` が要る)。spec と out は checkout 外へ置く」を足したいが、dev-wave 4 文書の
  aggregate 予算に余地 13 bytes しか無く、安全義務の圧縮は自己改善契約が禁じている。
  [T-597] (予算) の解決に従属させるか、意味等価な縮約先を別途裁定する。成果物影響: 無し
  (手順の明文化のみ)。放置すると変異本走の空振りが再発し、wave の wall-clock だけが延びる。
- {{T:provenance-audit-consumer-gap}} **P3・新規**: 監査結果を消費しない層がある。
  `tools/dev_wave_land.py` は `--message-file` preflight しか呼ばず full-history を強制しない。
  `tools/dev_waves/cli.py` は stdout/stderr を `DEVNULL` に捨てて rc だけ保持するため、
  既知 SHA と件数が receipt に残らない。成果物影響: 「公開が唯一の抑止」という台帳の契約が
  自動層で成立せず、どの例外を何件消費したかが監査 receipt から復元できない。
