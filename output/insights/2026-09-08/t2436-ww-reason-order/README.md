# verifier の理由列挙を key 順に整列し、同一 trace から同一の anomaly digest が出るようにした — 既存テストは整列の有無を区別できていなかった

**種別:** producer 側の局所修正 (1 行) と、それを撃つ正例テストの新設。
dev-wave `dev-wave-t2436-ww-reason-order` (2026-09-08)。裁定は D1817 ([T-2436]、/rulings 第 15 回)。
起点は `output/insights/2026-09-07_8c-rejected-witness-closure/verbatim/codex/s6-reviewB.md:52` の所見と
F896 (2) で、いずれも「verifier の出力は決定的」という前提が偽であることを指摘していた。

**閉じたのは WW 理由の順序だけである。** worker 数を変えても report 全体が同一であることは
本 wave の検査対象ではない。固定 seed 2 本の検出力は実測した CPython 3.10.12 に対する実証であって、
将来の Python の文字列 hash / set 実装に対する形式証明ではない。

## 1. 何が壊れていたか

`orchestrator/verifier/dsg.py` の `_reasons()` は、辺 `u->v` の WW 理由を
`u_writes.keys() & v_writes.keys()` という**未整列の集合**から走査していた。key は `str` なので
列挙順は `PYTHONHASHSEED` で変わる。結果として、**同じ trace から process ごとに違う理由順が出て、
anomaly digest が一致しない**。これは絶対規律 3 (正しさシグナルの再現性) に直接触れる。

wr 枝と rw 枝は `Txn.reads` という list を走査するので、この問題は WW 交差の 1 箇所だけにある。

## 2. 実測 (段 1 probe、`verbatim/s1-probe.md` に逐語)

共通 WW key を 6 個持つ 2 transaction の trace を作り、seed を変えて verifier を通した。

| seed | ww 理由の key 順 | result の sha256 |
| --- | --- | --- |
| 0 | 6,1,4,3,2,5 | `bf626278…` |
| 1 | 5,2,4,1,3,6 | `99dc7a97…` |
| 2 | 4,1,5,3,6,2 | `b0aeda23…` |
| 3 | 5,2,6,3,4,1 | `1b15d361…` |
| 4 | 1,6,3,5,2,4 | `b3f5fd64…` |
| 777 | 2,1,3,4,5,6 | `e5a5085e…` |

**6 seed が 6 通りの順と 6 通りの digest を出した。** 一方で `anomaly_count` はどの seed でも 1 で、
**受理集合は seed に依らない**。順序だけの問題である。

同じ probe で **rw 理由の順は 6 seed すべて `1,2,3,4,5,6` で安定**していた。段 4 では、
1 つの辺に WR 理由を 6 本持つ trace も作って測り直し、**wr も 6 seed すべて同一順**であることを
確かめた (`verbatim/s4-ruling.md` 第 2 節)。D1817 の scope (WW 交差だけ整列する) は十分である。

## 3. 本 wave の一番の発見 — 既存テストは整列の有無を区別できていなかった

着手前に追跡下の成果物とテストを全数走査した。

- anomaly の辺に理由を持つ**追跡下の成果物は 6 件**
  (`2026-08-26_mocc-g2-repro/runs/{19,24,30,31,32}/verifier.json` と
  `p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl`)。
  **1 つの辺に ww 理由を 2 本以上持つものは 0 件。**
- `orchestrator/tests/test_verifier.py` の `"reasons": [...]` golden **10 ブロックのうち、
  ww を 2 本以上持つものは 0 件。**
- text renderer の出力 (`ww key=…`) を含む追跡下の file は 2 件で、
  **1 行に `ww key=` を 2 個持つ行は 0 件** (`git grep -c "ww key=.*ww key=" -- .` が rc=1)。

つまり **整列を入れても既存の bytes は 1 つも変わらず、整列を外しても既存テストは全部緑のまま**である。
凍結成果物の再発行が不要なのはこのためであり、同時に「正例を足さなければ変異が生き残る」ことも
このためである。本 wave の実質的な作業は 1 行の修正ではなく、その 1 行を撃つ正例の設計だった。

## 4. 入れたもの

- `orchestrator/verifier/dsg.py:524` — `for k in u_writes.keys() & v_writes.keys():` を
  `for k in sorted(...)` にする。整列 key は key 文字列のみ。同一 key に WW 理由が 2 本出る入力は
  現行モデルでは構成できない (`u_writes` / `v_writes` が key ごとの辞書で、1 key 1 回しか append しない)。
- `orchestrator/tests/test_verifier.py` —
  `test_multi_ww_reason_report_is_hash_seed_deterministic` を 1 本。
  `PYTHONHASHSEED` を `1` と `777` にした別 process を 2 本立て、report の bytes 一致を見る。
  加えて各 report で ww 理由が昇順であること、`verdict == "non-serializable"`、
  `serializable is False`、`anomaly_count == 1`、`total_cycles == 1`、`phenomenon == "G2"` を固定する。

fixture は新設していない。新設すると `test_all_v2_fixture_files_have_clean_framing` の
完全一致インベントリ検査 (`_V2_FIXTURE_FILES`) が赤になるため、既存 helper `_tmp_trace()` を使う。
新規 test file も作っていない (既存 file の自走 runner が引数なし `test_` 関数を自動収集する)。

## 5. `certified` を assert しない理由 (過剰決定)

段 3 のレンズ A は「`phenomenon` / `serializable` / `verdict` / `certified` も固定せよ」と指摘した。
親が実測したところ、`Integrity.clean()` は counter 11 個に加えて
`proof_surfaces.certification_gate_satisfied()` も要求する (`model.py:450-467`)。本 wave の合成 trace は
protocol の proof-surface metadata を持たないので、**counter が全部 0 でも `clean()` は False** になる。
したがって `certified is False` は「cycle があるから」と「integrity が unclean だから」の
**2 つの独立な理由**で成立し、`DW-M03` の言う過剰決定になる。`verdict` は `not serializable` を
先に見る (`model.py:503-515`) ので cycle だけで決まる。**`certified` は assert から外した。**

## 6. 変異 (`mutation/final-spec.json` と `final-out.json`)

**区分は 3 件とも `diagnostic sensitivity pin`** である。受理集合も fail-closed 挙動も変わらず、
構造化シグナルの順序だけを pin するため、`DW-M08` の明文により correctness kill として数えない
(harness の `expected_status` は期待 node の完全一致を要求する機構として `KILLED` を使う)。

| ID | 変異 | 結果 | 赤 node |
| --- | --- | --- | --- |
| M1 | `sorted(...)` を外して元の集合走査へ戻す | KILLED (期待一致) | 新テスト 1 件のみ |
| M2 | `reverse=True` で降順にする | KILLED (期待一致) | 新テスト 1 件のみ |
| M3 | 整列 key を版のタプルだけにする | KILLED (期待一致) | 新テスト 1 件のみ |

baseline は PASSED (rc=0、失敗 node 0 件、32.145 秒)。**3 件とも赤 node が新テスト 1 件の完全一致**で、
既存テストは 1 件も反応しなかった。これは第 3 節の静的走査 (既存 golden に多重 WW が 0 件) の実走裏取りである。

M4 候補 (`key=hash` で整列する) は**登録しなかった**。hash 値が seed で変わることは、
6 key の相対順が seed 間で必ず変わることを含意しないため、期待 node を事前確定できない。
probe 2 パスの費用に見合わないと裁定した。

等価変異 (赤を要求しない): `sorted(..., key=lambda key: key)`、
`sorted(v_writes.keys() & u_writes.keys())`、`sorted(set(u_writes).intersection(v_writes))`。

## 7. 段 3 / 段 6 の敵対検証で覆ったこと

段 3 のレンズは「親の探索は閉じていない」を 3 件指摘し、いずれも親が実測で解消した。

| 指摘 | 解消のしかた |
| --- | --- |
| wr 枝の安定性が parser まで証明されていない | WR 理由 6 本の辺を作って 6 seed で実測 (全 seed 同一順) |
| path 以外を key にした束縛を排除できていない | 探索では原理的に閉じない。**dsg.py は直近 1 週間で 3 回変わり main は緑**なので、内容に張られた live pin は存在しない |
| text 出力の成果物を見ていない | `ww key=` を含む追跡下 file は 2 件、1 行に 2 個持つ行は 0 件 |

段 6 のレビュー B は運用面の must-fix を 2 件出し、両方採った。

- subprocess の timeout 30 秒は混雑した共有 login node で不足し、正しい実装が負荷だけで赤くなる
  → 同種 subprocess テストの先例に合わせて **120 秒**。
- `check=True` は子の stderr を見せないので、赤の原因 (import 失敗 / 検査器の失敗 / 環境異常) を
  区別できない → `check=False` にして終了コードを assert し、message へ seed・rc・
  stdout/stderr の末尾 4096 byte を載せる。`TimeoutExpired` も捕捉する。

段 6 の焦点再レビューは全 14 所見の対応表を出し、**13 件 closed / 1 件 partial** で閉じた。

## 8. 残る限界

- 固定 seed 2 本 (`1` / `777`) の検出力は、実測した CPython 3.10.12 と固定入力に対する実証である。
  将来 Python の文字列 hash や set 実装が変われば、2 seed が偶然同順になる可能性までは排除できない。
  現行環境では 6 seed すべてが異なる順を出すことを実測している。
- 本テストは `workers=1` だけを通す。**worker 数を変えても report 全体が同一**であることは
  本 wave の検査対象ではない。
- 型注釈を破った手製の入力 (`Write.key` に `int` と `str` を混ぜる) を `DSG` へ直接渡すと、
  整列が `TypeError` を出す。通常の trace 経路は key を ASCII 文字列へ正規化するので到達しない。
  段 6 のレビュー A・焦点再レビューがともに nit と判定した。防壁は足していない。
- 素の `python -O` で起動すると、追加した `assert` は無効になる。ただしこのリポジトリの標準
  runner は `-O` を付けず、対象 file 全体がもともと素の `assert` 前提なので、本 wave で
  弱まったわけではない。
- 新テストの nodeid は `orchestrator/tests/acceptance_duration_ledger.json` へ登録していない。
  被覆 gate は「登録済み ÷ 収集 >= 0.90」で、20042 / 21867 ≒ 91.65%、閾値まで約 1.65 point の
  余裕がある (段 6 レビュー B が独立に検算)。登録は台帳更新を主目的とする別 wave が行う。
  **推定値を実測せずに登録してはならない。**

## 9. 逐語

- `verbatim/brief-s1.md` — 段 1 brief。
- `verbatim/s1-probe.md` — 段 1 と段 4 の probe 実測 (seed ごとの順と digest)。
- `verbatim/s4-ruling.md` — 段 4 裁定。段 3 の全所見の real/refuted と plan v2、変異事前登録。
- `verbatim/codex/` — 段 2 / 3 / 5 / 6 の codex 子への投げ文と返り全文 (16 file)。
- `mutation/` — 変異の spec・結果・attempt。

## 10. 段 8 (自己改善) の裁定 — 候補 3 件、本文編集はゼロ

実測で気づいた作法の欠落を 3 件記録し、いずれも**本文編集はしない**と裁定した。

| 候補 | 実測 | 裁定 |
| --- | --- | --- |
| 変異 harness の spec・出力は試験対象 checkout の外に置く必要がある (`--spec` を insight dir へ置いて rc=2) | 本 wave で 1 例 | 収容せず記録に留める (下記) |
| 変異 harness は起動前に tree が clean であることを要求する (未追跡の insight 逐語で rc=2) | 本 wave で 1 例 | 同上 |
| 凍結成果物の再発行要否を確かめるとき、追跡 artifact 全件を JSON parse する走査が要る (今回は使い捨ての python で行った) | 本 wave で 1 例 | `DW-G03` の独立 2 例規則により候補記録に留める |

前 2 件の収容先は `DW-M05` である。実際に 1 行 (120 byte) を追記して `tools/check_docs.py` に
掛けたところ、**L1.5 層の予算を 118 byte 超過**した (9814 > 9696)。追記前の L1.5 は 9694 byte で、
**残り 2 byte** しかない。D730 / D782 の手順は「既存記述の削減を試す → 独立 3 例以上なら例外として
収容する → それでも収容先を作れないと確かめられた場合にだけ上限を引き上げる」であり、

- 削減で 93 byte を捻出するには、安全義務を書いた既に極度に圧縮された文へ手を入れることになる。
  自己改善契約は「予算のために安全義務を削除・弱化してはならない」と明記している。
- 本 wave での実測は **独立 1 例**であり、例外収容の条件 (独立 3 例) を満たさない。
- どちらの摩擦も **tool が rc=2 と理由の全文を出す自己診断型**で、合わせて 3 分程度の損失だった。

よって D730 の手順どおり「実施しない」へ落とす。**上限引き上げは行わない。**
同型が別の wave で再現したら 2 例目・3 例目として数え、3 例に達した時点で例外収容の条件が満たされる。
