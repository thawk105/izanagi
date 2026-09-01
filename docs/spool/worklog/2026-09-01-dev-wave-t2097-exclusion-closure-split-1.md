---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2097-exclusion-closure-split
seq: 1
title: [T-2097] 受入 wall の床を分解し、排他閉包の細分化で取れるのは 9.5 秒だと実測して不採用にした (docs のみ、branch worktree-dev-wave-t2097-exclusion-closure-split、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **依頼の前提が実測で覆った。** 依頼は「排他閉包の細分化が残る唯一の方向」と書くが、
  D1035 が名指した排他鎖は D1008 と D1103 が既に解いている。床は
  「最長単体 node 126.13 秒 + 全 shard 共通の report 外費用 約 56 秒 + 最遅 shard 固有の
  約 21.9 秒」でできており、どれも排他閉包ではない。詳細と裁定は
  {{D:acceptance-floor-is-longest-node-not-exclusion}}、一次資料は
  `output/insights/2026-09-01_t2097-acceptance-floor-decomposition/`。
- **同じ結論に達した先例が既にあり、本 wave はそこを埋めた。** archive worklog 1054 の [T-1886] は
  2026-08-28 に同件を台帳から落としている (「裁定の前提だった『床は排他鎖』も成立しない」)。
  ただし当時は「追加の操作を発明せず終端する」で閉じており、**床の正体を実アンカーで示していない。**
  1114 が T-2097 として再起票したのはそのためだと見る。本 wave は床を成分へ分解し、
  各成分の大きさと、それぞれに必要な裁定を書いた。三度目の再起票を止めるにはこれが要る。
- **実装は 1 行も入れていない。** 段 4 で「実装しない」と裁定し、段 5・6 を飛ばした
  (`4 -> 7 -> 8 -> 9`)。理由は 2 つで、(a) 段 2 が出した唯一の具体案が正しさを弱める、
  (b) 効果量 9.54 秒が D1019 の走間差 32.27 秒より小さく現行の A/B で判定できない。
- **段 3 のレンズが親の裁定を 3 か所で訂正した。いずれも採用した。**
  (1) 親の (P3)「排他閉包の列挙は完全」は誤り。shard 配置閉包、`certified_evidence` の
  cross-worker flock (17 node)、controller prewarm の memo cache flock、access map 外の
  実 repo reader が抜けていた。
  (2) 親の (P2)「残差は排他待ちではない」は棄却。親は「排他 group の無い shard にも残差があるから
  最遅 shard の残差も排他待ちではない」と書いたが論理として成立しない。lock 待ちは
  `pytest_runtest_protocol` の wrapper で setup report より前に起きるため JUnit にも
  `report.json` にも現れず、**測れていない。**
  (3) 親は容量の床を歴史的な所要台帳から `9610.0/(48x3)=66.7 秒` と書いたが、同じ走で言うなら
  `12548.9/(48x3)=87.15 秒` である。台帳の exact-key 被覆は選択 19215 node のうち 17571 node
  (91.4%) で、代表例では台帳 55.0 秒の node が実走 126.13 秒 (2.29 倍) だった。
  最長単体が容量の床を上回るという結論自体は変わらない。
- **親の (P1) は下界の主張としては残ったが、「makespan は 1 秒も動かない」は強すぎた。**
  実走の最大 worker occupancy 135.68 秒と理論最適 126.13 秒の差 9.54 秒が詰め込みの余地である。
- **段 2 の期待短縮 20〜32 秒は採らなかった。** 上端は最遅 shard 固有の 21.9 秒が全部消える仮定で、
  下端は拘束されていない容量差を wall へ計上している。どちらも既存 artifact では支持されない。
  親が段 3 投入後に LPT で下界を取り直し、レンズ B も独立に同じ結論 (固定 duration なら上限 9.54 秒)
  へ到達した。
- **副産物として、`REAL_REPO_ACCESS_BY_NODE` の外で実 repo・共有 ccbench を読む経路を
  複数の producer で独立に確認した** (`test_b10_backoff_shape_sweep.py:1096` の実 submodule への
  `git archive`、`test_s8b_approved.py:34` の実 gitlink 読取、oracle environment 25 node が
  compiler include root として共有 ccbench を読む経路、`test_mocc_trace_pair.py:121`/`:154` の
  session fixture)。map 外では protocol lock を無取得で通過する。**本 wave の scope 外なので
  直していない。** 閉包を広げる作業を持つ見送り項目へ file:line 証拠を追記した。
  現に走る writer は 1 本・0.19 秒で競合窓は小さいが、小さいことと無いことは別である。
- **子は 3 本 (段 2 plan 1、段 3 敵対相談 2)。全部 read-only、全部 rc=0、
  `tools/check_codex_output.py` も 3 本とも rc=0。** 実測はすべて親が行った。
  段 5・6 を飛ばしたので workspace-write の子は 1 本も起動していない。
- 焦点走 `orchestrator/tests/test_check_docs.py` + `test_spool_fold.py` + `test_artifact_admission.py`
  = 871 passed / 3 skipped、rc=0 (Pegasus dispatch request 964341.nqsv)。
  `python3 tools/check_docs.py` = 違反なし、`python3 tools/spool_fold.py --dry-run` = rc=0。
  受入全走の数値は receipt を権威とする (記録 commit を受入の後に足すと land できないため)。
- **ユーザー裁定が要る 2 点を残した。** (a) 最長単体 126.13 秒を縮めること — D1035 が
  「個々のテストの短縮は採らない」と却下しているが、その却下は床が排他鎖だという前提の上にあった。
  (b) 全 shard 共通の report 外費用 約 56 秒 — wall の 26% を占め、3 shard すべてが払う。
  D1320 が未分解と書いた「session 合計と job 合計の差 約 75 秒」とは別の量で、どの裁定も触れていない。

## 次の一手差分

### 更新

- [T-2097] **P1・ユーザー裁定待ち**: D1035 が指示した排他閉包の細分化は実測で尽きた。
  床は「最長単体 node 126.13 秒 + 全 shard 共通の report 外費用 約 56 秒 + 最遅 shard 固有の
  約 21.9 秒 (未計測)」で、閉包を細分化しても最悪 shard の worker occupancy は動かない
  ({{D:acceptance-floor-is-longest-node-not-exclusion}})。**次のどれを選ぶかを決めてほしい。**
  (a) 最長単体 126.13 秒の短縮を解禁する — D1035 の「個々のテストの短縮は採らない」は
  床が排他鎖だという前提の上にあったので、前提が消えた今は再裁定に値する。
  (b) 全 shard 共通の report 外費用 約 56 秒 (wall の 26%、3 shard すべてが払う) を調べる —
  どの裁定も触れていない最大の未着手軸。
  (c) 最遅 shard 固有の約 21.9 秒を測る計測点を足す — lock 待ちと prewarm を分離できる。
  (d) 本項を台帳から落とす。
  base: 8882dc85284cab9687b4d52392539f44e4d4debe495368a054f31e1b9100e718

### 見送り追記

- [T-2019] 2026-09-01 に登録外 reader の file:line 証拠が増えた (`test_b10_backoff_shape_sweep.py:1096`、`test_s8b_approved.py:34`、`orchestrator/tests/conftest.py:576` 経由の oracle environment 25 node、`test_mocc_trace_pair.py:121`/`:154`)。追加裁定はせず記録のみ。
