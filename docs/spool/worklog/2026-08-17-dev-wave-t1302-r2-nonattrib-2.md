---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1302-r2-nonattrib
seq: 2
title: ユーザー裁定 R2 を発効させた — 待ち手の node exact 検査が checker の flake 分類を丸ごと弾いており、実装済みに見えて一度も動いていなかった (コード + docs、branch worktree-dev-wave-t1302-r2-nonattrib)
---

## 本文

- **ユーザー裁定の適用範囲を確定した。** 依頼は裁定パッケージ #2 について「残余を明示受容する形に
  するのであって、検査を消して緑を買う形は採らない」であり、択 (c) (flake を別集合で通し、
  受領証・land 結果・台帳へ残す) を採った。設計判断は {{D:r2-flake-observation}}。
- **止めていたのは checker ではなく consumer だった。** checker は 2026-08-16 の `8a2b735b` から
  5 field の `flake` node を出していたが、待ち手の node exact 検査が
  `{classification, nodeid, rerun_rc}` 固定だったため必ず `_StageFailure` になっていた。
  実 producer が書いた receipt (`output/insights/2026-08-17_t1116-nonattrib-checker/probe2-receipt.json`)
  を消費側述語へ当てて再確認した。
- **親 brief の前提 2 件を子が実測で倒した。** (a)「wave 側単独再走 rc が 1 以外なら全部 flake に
  なる fail-open」は偽で、checker は `tools/check_acceptance_reds.py` で rc を `{0,1}` へ限定済み。
  よって待ち手側の rc pin は現 producer に対する narrowing ではなく防御深度である。
  (b)「flake が wave 側 runner の rc=0 を受入証拠にする初の経路」も偽で、child-green が既にそう。
  この 2 件目により、runner 束縛の根拠を「本 wave が開ける窓の補償」から
  「ユーザー裁定済み [T-1283] の非帰属経路への部分実装」へ差し替えた。
- **敵対レンズが設計を 1 箇所反転させた。** runner blob 等値を `flake_nodeids` 非空で条件分岐させる
  当初案は、flake を非帰属と偽った受領証で gate を素通りできる。`non-attributable-only` 全体へ
  無条件化した。
- **手順違反を 1 件記録する。** `DW-O13` (gate 入力の実在、最遅読了は段 2 前) を未読のまま段 2 を
  回した。段 4 で新 gate 候補が判明した時点で入口の巻き戻し規則に従い、段 2・3 の成果物を
  invalidate し、brief v2 で段 2 から再実行した。旧成果物は後続の子へ渡していない。
  再実行後のプランと 2 レンズは、無効化した版と独立に同じ結論の中核へ到達した。
- **段 6 のレビュー 2 本が must-fix 5 件を出し、fix 子が全件を閉じた** (焦点再レビューで
  closed 判定)。内訳は合成 repo fixture の runner 欠落 (実測赤 3 件の真因)、land の
  retryable 誤分類、outer 側 disjoint 述語の検出力ゼロ、実 producer の混在相互 pin 欠落、
  64 KiB 境界テストの偽緑。
- **通知経路の受理幅が 21 byte 縮んだ。** land 結果 JSON へ `acceptance_flake_nodeids` を足した分
  (compact 表現で 30 byte) だけ、64 KiB 上限に収まる payload が小さくなる。fixture を縮めて
  数値を合わせる形は偽緑なので、旧最大 payload が超過することと新境界を独立 literal で pin した。
- **変異 matrix は 13/13 KILLED、MISMATCH 0、SURVIVED 0** (anchor `4906e063`、
  `--runner-mode dispatch`、期待 node 22 件の完全集合)。過剰拒否検出の正例 1 件 (P01) を含む。
  当初の P01 (child-green にも checker/runner 等値を要求する) は 71 node を落とす過剰決定だったため、
  `DW-M03` に従い単一理由の形 (runner 等値なのに拒否する向きの反転、7 node) へ差し替えた。
  初回 probe (全件 SURVIVED 期待) の結果は `output/insights/2026-08-17_t1302-r2-flake/` に残した。
- **変異 baseline を緑にするため、本変更前から赤い 1 件を変異走から除外した。**
  `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は
  login ノードでも計算ノードでも `campaign env_tag は exact str でなければならない` の TypeError で
  落ちる。変更前の main で同じ赤を実測しており、本 wave の差分は到達しない。台帳に未登録だったので
  新規項目として起票する。
- **子の工数。** codex 11 本 (plan 2・consult 4・author 1・review 2・fix 1・focus 1)。
  うち plan 1 本と consult 2 本は `DW-O13` の巻き戻しで破棄した。review の初回投入 2 本は
  `--lane` を review 段へ渡して argparse で落ちており、`.done` を残したまま別名で再投入した。

## 次の一手差分

### 完了

- [T-1302] 非帰属 checker のユーザー裁定 R2 を実効化した。待ち手・outer receipt v4・land・
  3 test file・runbook・{{D:r2-flake-observation}} を同時に改訂し、flake を `flake_nodeids` として
  別集合で受領証と land 結果へ残す形にした。残余は原因を問わない観測分類として明示受容した。
  remaining: none
  base: d22493a12155e80c0b1989e409764ecfc36853018b84b008383bb1b8a7281fe4

### 新規

- {{T:rerun-pass-evidence}} **P2・新規 ([T-1302] 段 3 レンズ A 由来)**: 単独再走の rc=0 に
  「対象 nodeid が call phase まで実行され PASSED した」証拠を要求する。現在は rc=1 のときだけ
  FAILED/ERROR の証明を要求し、rc=0 は対象が 1 度も実行されていなくても通る。新機構になるため
  [T-1302] では設計メモに留めた。[T-1283] 族。
- {{T:rerun-shape-parity}} **P3・新規 ([T-1302] 段 3 レンズ A 由来)**: 初回全走と単独再走の
  argv・環境変数・pytest 選択・scheduler を同形にする。現在は checker が
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD` 等を消す一方、待ち手は `PYTEST_ADDOPTS` /
  `PYTEST_PLUGINS` しか見ないなど、両者の意味論が揃っていない。全走限定赤の残余幅を決める要因。
- {{T:mutation-baseline-green-doc}} **P3・新規・ユーザー裁定待ち ([T-1302] 段 8)**:
  変異 harness が baseline 緑を要求すること、変更前 main の赤は runner argv の `--deselect` で
  外して台帳へ根拠を書くことを `docs/dev-wave/mutation.md` へ入れたいが、**L1.5 層の
  unique footprint 予算に 172 bytes 収まらない** (実測: 9738 > 9566)。`DW-M03` 単節への統合でも
  層予算で落ちる。上限は上げない既裁定 ([T-1300]) があるため、収容先 (既存文の縮約か新規 L2 節か
  見送りか) をユーザー裁定へ返す。
- {{T:exploration-env-tag-red}} **P2・新規 ([T-1302] の変異 baseline で実測)**:
  `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
  main で決定的に赤 (`campaign env_tag は exact str でなければならない` の TypeError)。
  受入全走を必ず非緑にするので、受入は毎回 checker の非帰属判定に依存している。
