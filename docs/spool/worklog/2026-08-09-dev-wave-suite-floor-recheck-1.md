---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-suite-floor-recheck
seq: 1
title: [T-201] 択 (a) を実装した — 履歴走査の copy 検出を blob OID へ置き換え受入下限を測り直した (コード + docs、branch worktree-dev-wave-suite-floor-recheck)
---

## 本文

- **ユーザー裁定 2 件を本セッションで直接得た。** (1) 当初 brief は「測定と裁定材料まで、実装はしない」
  だったが、途中で **「(a) の実装まで進めていい」** と裁定された。これにより `t080_freeze_migration`
  (freeze 族の中核) の編集が確定し、条件 `DW-O08` / `DW-O09` / `DW-O10` が新たに成立したため、
  入口の巻き戻し規則に従って**段 1 へ巻き戻し**、brief v2 から段 2・3・4 をやり直した。
  旧 brief・旧プラン・旧レンズ 2 本・旧裁定は根拠として流用していない。
  (2) 走査の「対象を未変更のままコピー元にした commit も改竄とみなす」節の扱いについて、
  親が 3 択で諮り **「OID 重複検査を足す」** が選ばれた。詳細は {{D:history-scan-copy-clause}}。
- **親 brief の「既知の実測」が 3 つとも現状と食い違った。** (i) 受入 1055.40 秒は最新値ではない
  (現況 1174.40 / 1210.04 秒、既往最大 1809 秒)。(ii)「collect-only 6315 対 受入 7207 = 約 900 件差」は
  再現しない — 実測は collect-only 7459 件 / 11.22 秒で、同日 tip の受入 7458 件とほぼ一致し、
  `pytest.ini` の `testpaths` と `run_tests.py` の既定対象はどちらも `orchestrator/tests` の 1 本だけである。
  (iii) 比較基準にした「D104 測定時の 207 秒」は、**当時棄却された共有 cache 実装ありの arm** の値だった
  (同一ノードの baseline は 116.25 秒)。D104 の材料自身が **同一コードでノード間 1.8 倍**
  (116.25 / 200.72 / 214.34 秒) と記録しており、**日付・ノードを跨いだ wall 比を因果推定に使えない**。
  親が段 1 で出した「件数 1.75 倍に対し wall 5.09 倍」も同じ理由で撤回した。
- **段 3 の敵対レンズが親の裁定を 2 度倒した。** 1 度目 (旧 scope) は計測計画に所見 19 件で NO-GO。
  2 度目 (新 scope) は「全史 equivalence は恒真になる」(実 repo は receipt を触った commit が
  導入 commit 1 個だけなので新旧とも全件 False で一致してしまう) と
  「本番 entrypoint は `verify_receipt` 1 本ではない」(`s8b_oracle_report.py` が WAL の任意
  `validation_head` で `inspect_receipt_history` を呼ぶ) を real と判定した。前者により
  positive control の中核を全史比較から**合成 matrix** へ移した。
- **旧 scope で作った probe 6 ファイル (pytest plugin / cgroup sampler / 解析器 / PBS driver /
  microbench / 静的棚卸し) を破棄した。** レビュー 2 本で所見 19 件・NO-GO を受けており、
  裁定が「argv から 1 token を除く」に確定した後は必要な証拠が before/after の受入 wall だけに
  なったため、規律 5 と D104 決定 (3) に従って採用しなかった。repo には入れていない。
- **変異は 7 本中 6 本 KILLED、1 本 (M1) は等価変異**だった。M1 は「argv から `-M` を落とす」で、
  実 commit で検証すると `-C` だけでも `-M -C` と同じ 323 件の rename を検出する
  (git の `-C` は rename 検出を含む)。gate の穴ではない。**erratum**: M2 / M4 は KILLED だが
  事前登録より多い node が落ちた (既存テストも検出する過剰決定) ため MISMATCH と記録された。
- **変異 harness は 1 度 fail-closed で中止した。** spec の `category` に `diagnostic-sensitivity` と
  書いたが `tools/mutation_harness.py:38` の許可値は 3 つだけである。**変異は 1 本も走っておらず
  偽の緑は出ていない。** spec を子へ差し戻して修正した。
- **provenance 全走で新規違反 1 件を検出したが本 wave 由来ではない** (`2c1929533a6f`、t659 の
  `output/insights/.../verbatim/probe_split_window.py` に Codex `role=author` trailer がない)。
  所有 wave へ通知し、[T-682] として起票済みであることを確認した。その後 main へ入った
  `worktree-dev-wave-t139-r4-probe` 由来の形式違反 22 件と合わせ、全史監査は本 wave と無関係な
  赤を返す状態にある。
- 親の prompt でファイル path を相対的に書いた (「同 dir の X」) ため、段 2 の子が正しく
  fail-closed して 1 巡空振りした。**path は絶対で 1 行 1 ファイル書く**。

## 次の一手差分

### 更新

- [T-201] **P1・(a) 実装済み ((本エントリ)) / (b) 実装待ち**: 択 (a) 本番
  `t080_freeze_migration._history_touches_path` の走査置換を実装した。`--name-status` を `--raw` へ
  変えて同じ 1 回の呼び出しで destination blob OID を取り、`--find-copies-harder` を外し、
  exact copy を OID 一致で検出する。descendant 20 commit の実測で 45.31 秒 → 0.075 秒。
  受理集合の変化は「中身を変えたうえでのコピー (50〜99% 類似)」を検出しなくなる 1 点だけで、
  これは裁定済みの意図的な縮小である ({{D:history-scan-copy-clause}})。残るのは択 (b) の
  `output/` tracked bytes 削減で、本 wave の実測 (費用は tracked bytes への I/O に比例) が直接支持する。
  base: d6b33f8225c6e29820681043ef2e6db861d954bc88bf91738febcce3ff474153
