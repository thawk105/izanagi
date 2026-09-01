---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2123-mutation-node-normalize
seq: 1
title: [T-2123] 変異 harness の比較器へ xdist group 接尾辞の同形化を入れた — 同じ規則が 2 実装へ複製されていた (コード + テスト、branch worktree-dev-wave-t2123-mutation-node-normalize、変異 16/16 KILLED)
---

## 本文

- `DW-M08` は「同形式へ正規化した記録 node との完全一致だけを KILLED とする」と要求するが、
  比較器がこの正規化を記録側へ適用していなかった。`xdist_group` を持つテストは
  期待 node を接尾辞なしで書くと MISMATCH、接尾辞込みで書くと collection 事前検査が
  起動前に中止する、という「どちらの表記でも書けない」状態だった。
  設計判断は {{D:mutation-node-match-key-seam}}、一次資料は
  `output/insights/2026-09-02_t2123-mutation-node-normalize/`。

- **親の前提が 2 つ覆った。** (a) 段 2 が「fan-out の終端検証器
  `tools/mutation_fanout_contract.py` が独立した比較器を持ち、`_match_key` の座すら無いまま
  `set(failed) == expected` を直接比較している」ことを見つけた。親は
  `tools/mutation_fanout.py` だけを grep して「比較器なし」と判断しており、探した file が
  1 本足りなかった。harness だけ直すと fan-out merge が新しい台帳を旧規則で拒否する。
  (b) 段 3 のレンズ A が「除去規則を nodeid 全体へ当てると path 内の `@` で別テストが
  同一視され偽 KILLED になる」ことを示した。現行 repo に該当 path は 0 件で到達不能だが、
  比較器の受理集合を広げない形 (test 名部分だけへ当てる) を採った。

- **段 6 のレビューが層の穴を検出した。** 同形化規則を 2 実装へ複製したのに、
  敵対的な負例が harness 側の実装しか呼んでいなかった。fan-out 側で同型欠陥が再発しても
  テストは緑のままになる。詳細は {{F:duplicated-rule-single-layer-controls}} と
  {{D:duplicated-rule-needs-per-layer-controls}}。fan-out 側へ負例 3 本を足し、
  変異も層ごとに登録し直した。

- **親の実測が 2 件の赤を出した。** どちらも子の申告と矛盾しない — 実装子・fix 子とも
  codex sandbox が socket を拒否して pytest を 1 件も起動できず、「実装済み・未実走」と
  正直に報告していた。1 件目は新規 fixture が `MISMATCH` record を組み立てながら
  `test_output_tail` を空にしていたもので、意図した assertion に到達する前に落ちていた。
  2 件目は login node 固有で、`--runner-mode local` を構造的に拒否する 2 テストが
  login では必ず落ちる (計算ノードでは 140 passed)。後者は本 wave の差分とは無関係である。

- **変異走行の 1 回目は erratum として残した。** 期待 node に parametrize されたテストの
  bare な関数名を書いて起動前中止した (F71 の再発)。2 回目 (probe) は 16/16 が赤を出したが
  7 件は期待集合が不完全で MISMATCH。実測の完全集合で再登録した 3 回目が本走である。
  probe で判明した実測: 比較 key の除去を外すと 6 テストが落ちる (resume、collection、
  flaky-hold policy、二表記重複拒否まで含む)。

- **冗長 gate を 2 件明記する。** 完全一致を包含へ緩める変異と、抽出 0 件の fail-closed を
  倒す変異は、既存テスト (`test_failed_nodes_strict_superset_never_counts_as_killed`、
  `test_mutation_nonzero_normal_rc_without_failed_nodes_is_parse_error`) も同時に殺す。
  本 wave の新機構を単独で証明するものではない (`DW-M03`)。

- 計算資源: 変異走行と焦点走はすべて計算ノードへ dispatch した。性能測定・campaign 実走は
  行っていない。文書 (`docs/dev-wave/mutation.md`) は触っていない — F71 の恒久対応欄が
  「規約の追加ではなく道具を規約へ合わせるのが対応」と既に定めており、契約側は現状で正しい。

## 次の一手差分

### 完了

- [T-2123] 変異 harness の比較器へ xdist group 接尾辞の同形化を入れ、fan-out 終端検証器の
  独立実装も同形に直した。正例・負例を層ごとに置き、変異 16 件が全て KILLED になることを実測した。
  remaining: none
  base: fe50d5f0a40a2cf9d9ccaee0028005707905cb62faf8d82e274a9d8426c401b7
