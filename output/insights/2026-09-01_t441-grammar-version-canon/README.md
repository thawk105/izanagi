# [T-441] backoff 受理文法の版束縛と数値正準化 — 一次資料

D901 条項 2 (文法の版を identity・WAL・cache へ束縛する) と条項 3 (hole の数値表記の正準化) を
実装した wave の一次資料。裁定は D1034 (D942 の条件付き親裁定を追認)、D836、D901、D95。

## この dir の構成

- `s4-ruling.md` — 段 4 の裁定。親の前提の採否、所見の裁定、変異 12 件の事前登録。
- `s6-fix-ruling.md` — 段 6 の fix 裁定。2 レンズの所見の採否と、期待値更新を許可した 2 箇所。
- `mutation-erratum.md` — 事前登録から 2 件を外して 2 件を足した理由。
- `mutation-spec-final.json` — 本走に使った変異 spec。
- `mutation-summary.json` — probe と本走の集計。
- `verbatim/` — 各段の子の出力そのまま。

## 引数の前提が実測で 1 件覆った

依頼は「未実装なのは受理文法への initializer-literal と statement-count の追加」と述べていたが、
着手時点の local main で両方とも実装・執行済みであった。親が validator を実走して確認した。

| 入力 | 結果 |
|---|---|
| `double now_backoff = 20;` | accepted |
| `double now_backoff = 20.0f;` | rejected `backoff-grammar.initializer-literal.v1` |
| `double now_backoff = 20UL;` | rejected `backoff-grammar.initializer-literal.v1` |
| `double now_backoff = 10 + 10;` | rejected `backoff-grammar.initializer-literal.v1` |
| `double now_backoff = 20; int x = 1;` | rejected `backoff-grammar.statement-count.v1` |
| `double now_backoff = 0x14;` | **accepted** |
| `double now_backoff = 2e1;` | **accepted** |

最後の 2 行が条項 3 の未実装を実証する。同じ値 20 の 3 表記がすべて別 token になる。
依頼の他の記述 (裁定の指定、「版束縛と数値正準化を同じ変更単位に」) は条項 2・3 と整合するため、
scope を条項 2・3 として進めた。

## 親の provisional 裁定が 2 件覆った

- **P2 (正準化は台帳記録側だけ)** — 段 2 のプラン子と段 3 の 2 レンズが独立に、
  台帳併記では source bytes が分かれたままで重複が畳まれないと指摘した。撤回して
  材料化時の正準化を採った。
- **P4 (新規 test file を作る)** — 稼働中の別 wave の hunk 位置を実測したところ
  40-102 行に限られ、本 wave の編集は 212 行以降で衝突しないと分かった。撤回して既存 file を使った。

## プランの中心案を 1 件差し替えた

段 2 のプランは、編集された path (`include/backoff.hh`) が dirty かどうかで版束縛の可否を決める
案だった。段 3 の 2 レンズが独立に、同じ path を材料化する別 producer
(`backoff_extended_sweep`、`b10_backoff_shape_sweep`) の実在を名指しした。
campaign 由来の版を明示引数で渡す形へ差し替えた ({{D:backoff-grammar-version-explicit-campaign-arg}})。

## 段 6 で最も重かった所見は既定値だった

段 3 のレンズ A だけが挙げ、親が独立に実測で裏を取った。共有の reject helper の既定が
`None` でなく backoff の版 1 になっており、版を渡さない 7 箇所の呼び出し
(`s6_sort_sweep.py:360`、`p3_s4_loop_sort.py:202,225,231`、
`p3_s4_loop_trigger_gating.py:486`、`s8a_trigger_sweep.py:462`、`p3_b4_wiring_probe.py:1419`)
まで backoff の版に束縛されていた。fix で既定を `None` へ戻し、旧 id との exact 一致を固定した。

## 赤の推移と、変異内容に帰属しない停止

親が login node で実走した焦点走の推移は 52 → 7 → 4 → 0 である。
最初の 52 件は全件が `contract-loader-drift` で、HEAD blob 束縛 file を未 commit のまま走らせた
ことによる。実装の回帰ではない。consumer へ広げた走では 47 → 0 で、原因は fixture が
lock より先に WAL を書いていた順序であった。

変異本走は計算ノード側の事情で 3 回停止した。いずれも変異の内容とは無関係である。
1 回目は baseline の job が待ち行列で 900 秒の時間切れ、2 回目は 1 回目が残した sidecar、
3 回目は収集段の受領証欠落 (rc=16) である。毎回 hold と sidecar を手順どおり除去し、
作業ツリーが clean で変異が復元済みであることを確認してから再投入した。
**変異の内容は 1 件も変えていない。**

## 受入全走の 1 回目で出た 9 赤

`4a44b2096` を tested tip として投入した受入全走は **9 failed / 19476 passed / 92 skipped**
だった。9 件とも自分の差分に帰属する。焦点走の対象から `test_p3_b4_launcher.py`、
`test_p3_b4_raw_record_producer.py`、`test_p3_b4_wiring_probe.py` の 3 file が漏れていた。
DW-O26 が「変更した production file を参照する consumer test も含める」と定める型の取り逃しである。

- 8 件 — `orchestrator/campaign/p3_b4_wiring_probe.py:1475` が `L.default_cfg` 由来の版付き
  campaign lock を書き、直後の `:1476` が版を渡さずに reject を記録していた。
  段 6 の fix が入れた fail-closed 検査が正しく発火していた。probe を production と同じ
  呼び出し形へ揃えて閉じた。
- 1 件 — `orchestrator/tests/test_p3_b4_launcher.py:899` が `default_cfg()` の
  `search_config` の key 集合を exact に固定していた。条項 2 が identity へ版を束縛することの
  直接の帰結なので、定数参照で 1 key だけ足した。

## 同じ型を 1 件ずつ潰していた — 全件確認へ切り替えるのが遅かった

「版付き lock を書くのに版を渡さない」fixture は 3 経路にあり、本 wave は
それを **3 回に分けて 1 件ずつ**直した (fix2 → fix3 → fix5)。最後の fix で
`orchestrator/tests` 全体を AST 走査して全件数えたところ、対象は次の 3 件だけで
残存 0 件と確定した。

- `test_p3_s4_loop.py::_seed_b4_admitted_history`
- `test_p3_b4_closed_critic.py::_write_admitted_attempt`
- `test_p3_b4_raw_record_producer.py::_make_clean_admitted_fixture`

**最初の 1 件が出た時点で全件を数えていれば、fix を 3 回に分けずに済んだ。**
新設した fail-closed 検査が既存 fixture を落とす型では、1 件目の時点で
「同じ形の呼び手を全部数える」ことが所要を決める。

## 版検査は 5 回発火し、5 回とも呼び手を直した

「版付き lock を書くのに版を渡さない」形は wave 中に 3 経路で現れた
(B-4 履歴 fixture、closed critic fixture、配線 probe)。production は lock を確定してから
版を明示して呼ぶ。いずれも検査の省略・条件分岐の追加・lock の legacy 化・テストの skip を採らず、
呼び手を production と同じ形へ揃えて閉じた。**受理集合を緩める方向の変更は 1 件も入れていない。**

## 実測値

- 変異: 12/12 KILLED、期待 node と完全一致、SURVIVED 0、MISMATCH 0。baseline は rc=0・失敗 0。
- 焦点走 (fix 後): `test_p3_s4_loop.py` 単独で 340 passed。
- 焦点走 (main 取り込み後、6 file): 1209 passed / 3 skipped。
- 呼び出し規約: `run_campaign` 73 call / 23 files、`resolve_evidence` 27 call / 22 files、
  `source_digest.resolve` 35 出現。いずれも既定 `None` のため無改変。
  実装子の報告は `resolve_evidence` を 28/23 としていたが、段 6 のレンズ B が
  文字列 literal 1 件の混入を指摘した。上の値が正しい。

## main の取り込み

wave の最中に local main が 66 commit 進み、起動時の編集面重複検査で名指しした T-1999 が着地した。
実装面で交差するのは `p3_s4_loop.py` の `run_one_iteration` だけである。git は競合なしで
自動 merge したが、競合の不在とテストの緑は合成の正しさを保証しないため、
Codex role=author の合成監査を独立に走らせた。must-fix と should-fix はゼロだった
(`verbatim/merge-audit.md`)。
