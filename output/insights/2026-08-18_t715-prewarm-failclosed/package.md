# [T-715] receipt memo の fail-closed 化 + prewarm 新設 — 実装 wave の記録

wave: `dev-wave-t715-memo-failclosed` / 2026-08-18 12:23〜15:12 JST
base: main `a160f4aa` / 実装 commit `dd1fefa9`、fix commit `db0baaae`
一次資料: 同ディレクトリの `verbatim/` (段 2 プラン、段 3 レンズ A/B、段 4 裁定、段 6 レビュー A/B)、
`mutation-spec.json`、`mutation-ledger.json` (1 巡目)、`mutation2-ledger.json` (fix 後)

裁定 = [T-715] 択 (b) (2026-08-11 /rulings)。正本 =
`output/insights/2026-08-10_t692-xdist-walltime/package.md` の R-a。

---

## 1. 裁定の前提のうち、実測で覆ったもの

| # | 実測 | 08-10 package / 裁定文の前提 | 差 |
|---|---|---|---|
| M1 | `prewarm` / `pre_warm` は repo の Python 全件で **0 件** | 「prewarm を前提化する」 | **prewarm は実装が存在しなかった。** 本 wave が新設した |
| M2 | 解決 1 回 = **15.3 秒** (login) / **19.70 秒** (計算ノード、無競合) | 「1 回 22.4 秒」「commit 数に比例して数百秒規模」 | 2026-08-12 裁定の凍結検証保留 3 件で縮んだ。保留が解ければ再び伸びる |
| M3 | 本番 resolver 1 回で `search_repository` → `enumerate_repository_files` が 1 回発火し **13,565 file** を列挙・読取 | R-a の穴の前提 | **穴は健在だった。** 実装理由はこれで成立する |
| M9 | `real-repo` group の直列和は **125.5 秒 / 69 node** (< wall) | 「wall はほぼ group の直列和 1388.80 秒で説明でき、その 96% は 2 node」 | **律速モデルが崩れている。** 現在の律速はスループット (直列総和 5,991.2 秒 ÷ wall 173.10 秒 = 実効 34.6 worker) |

## 2. 「worker 起動前」は実装不能だったこと (裁定文からの縮小)

裁定 (b) の字面は「worker 起動前に runner が 1 回解決して cache を作り」である。
xdist 3.8.0 の実装を読むと、この字面をコードで満たす経路は存在しない。

- `dsession.py:83-91` `DSession.pytest_sessionstart` が `NodeManager` を作り、同じ関数で
  `setup_nodes()` = worker 起動を行う。
- `dsession.py:103-105` は controller の item collection を短絡する
  (`prohibit collection of test items in controller process`)。

したがって「collect 結果を見て prewarm する」と「worker process 生成前」は両立しない。
**本 wave が満たすのは「test body が 1 本も走る前」**であり、裁定の目的
(session 中に production 経路が実 repo を再解決しない) はこれで達成される。
prewarm の barrier は `pytest_xdist_node_collection_finished` (xdist) と
`pytest_collection_finish` (非 xdist) に置いた。
**collection 時に consumer が resolver へ到達しないこと**も meta-test で固定してある
(縮小が成立する前提そのものの機械化)。

UID の確定だけは `pytest_configure` で行える (`NodeManager` が読む前)。
`tools/run_tests.py` の argv は 1 文字も変えていない。

## 3. 敵対レビューが見つけた恒真ゲート (段 6 の主要 must-fix)

段 5 実装は「公開端の fail-closed」を serial 分岐でしか守っておらず、
**公開 `real_repo_receipt()` に「xdist UID があるときだけ production resolver へ倒す」分岐を
足すだけで、新設検査も変異も全部すり抜けられる**状態だった (レビュー A 所見 1、Critical)。
AST の caller 検査も `_resolve_now` という名前だけを見ており、別名・`getattr`・module 属性を
検出できないことが read-only probe で実証された。

fix で、公開 2 endpoint × UID 下の cache miss / 破損 / lock 不能を負例に加え、
AST 検査を到達しうる呼出し全般へ広げた。この形は変異 MT3 が KILLED で裏取りされている。

ほかに閉じた must-fix: worker 側でも `pytest_collection_finish` が発火する問題 (2 レンズが
独立に Critical 判定)、conftest と consumer の module identity 分裂、conftest の eager import が
既存契約 (`test_pytest_failure_digest.py` が固定する repo root 外からの単体 import) を壊す問題、
memo の process state が pytest session 境界を越える問題。

## 4. 変異 matrix — SURVIVED 1 件が本物の検出穴だった

runner 範囲は期待 node をちょうど含む 2 file の serial 走 (`-n 0`)、dispatch recipe。

| 巡 | KILLED | MISMATCH | SURVIVED |
|---|---|---|---|
| 1 巡目 (`mutation-ledger.json`) | 3 | 2 | **1 (MT2)** |
| fix 後 (`mutation2-ledger.json`) | **4** | 2 | **0** |

**MT2** (`_cache_store` の `except` 末尾の `raise` を削除し wave 前の握り潰し形へ戻す) が
1 巡目で SURVIVED し、落ちた node が 1 つも無かった。原因は検出穴で、
`test_receipt_memo_l1_to_l5_are_fail_closed_and_uid_is_hashed` が
`mock.patch.object(memo_module, "_cache_store", side_effect=store_error)` により
**`_cache_store` 自体を差し替えており、実関数の本体が 1 度も実行されていなかった**。
固定できていたのは呼び出し側の扱いだけで、関数自身の契約 (失敗を握り潰さず送出する) は無防備だった。
実 `os.replace` を失敗させる負例を足し (`db0baaae`)、再走で KILLED になった。

MISMATCH 2 件は生存ではない (DW-M03)。事前登録を結果に合わせて書き換えていない。

- **MT1**: 期待 3 node に対し観測 4 node。`test_receipt_memo_process_state_is_scoped_to_pytest_session`
  も落ちた。親の予測より検出が広かった側の過剰決定。
- **MT6**: 期待 2 node のうち `test_receipt_memo_module_identity_and_resolver_caller_are_fixed`
  だけが落ち、wiring 検査は反応しなかった。eager import の検出は identity 検査 1 本が担っている。

## 5. 時間 (test-time regression rule)

| 指標 | 変更前 tip `a160f4aa` | 判定 |
|---|---|---|
| 全走 pytest 実行時間 | **173.10 秒** (12,761 passed / 95 skipped) | 閾値 = 1.1 倍 = **190.41 秒** |
| CPU 飽和度 | 1423.94 秒 / 126 秒 = **11.30 コア相当 (48 中 約 24%)** | **非飽和**。規則により非飽和で 1.1 倍超は不可 |

静的上界は「既存 wall へ計算ノードの q = 19.70 秒を丸ごと加算」で `192.80 秒` = 1.114 倍となり、
**上界では合格を主張できない**。段 2 プランが書いた 188.40 秒 (1.088 倍) は login node の
q = 15.3 秒を使った取り違えである。判定は実測で行う (§6)。

なお現行は 48 worker が同時に受け皿を求めて flock 待ちになり、
`test_s8b_oracle_driver.py` の 14 node が 61〜66 秒帯 (直列和 909.9 秒) を占めている。
単独 process では同じ node が 19.70 秒 / 0.03 秒なので、この帯の大半は待ちである。
prewarm はこの待ちを解消するため、wall は増えるより減る見込みだった。

## 6. 受入と実測値

受入全走の結果は worklog の該当エントリに記録する (本 package は実測前に値の欄を作らない)。

## 7. scope 外として残したもの (ユーザーへ返す)

- **pickle の closed-schema codec 化**: `_cache_load` は型検査の前に `pickle.loads` を実行する。
  wave 前から在る信頼境界の穴で、本 wave が作ったものではない。memo の外形を変えるため別 wave。
- **runner の infrastructure failure 分類**: memo の構造化 message までは実装したが、
  `tools/run_tests.py` の rc 体系を増やす案は同 runner の契約変更になる。
- **production CLI 子プロセスの 2 回目解決** (R-e): brief の時点から scope 外。
- **`--forked` / remote xdist (`--tx ssh=`) 対応**: 発火条件を実在 artifact で書けない (DW-G04)。
- **`_prune_stale_caches` が他の生存 session の cache を消しうる**: TTL 6 時間で、
  それより古い session は実質死んでいる。backlog。
