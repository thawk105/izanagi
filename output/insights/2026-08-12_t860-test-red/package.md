# [T-860] 「テストが失敗するところ」の是正 — 材料と裁定パッケージ

wave: `dev-wave-t860-test-red` / branch `worktree-dev-wave-t860-test-red`
base: main `427da17c` / 実装 `71b9f5b0` / positive control `7dfb772a`

依頼 (ユーザー逐語): 「テストが失敗するところあると思う。適切にテストされているところか、
テストしているところを直してください」
裁定 (ユーザー逐語、2026-08-12): 「じゃぁテスト側を直して」

---

## 1. 赤の全体像 (親の実測)

| 走行形 | 結果 | 赤の所在 | 帰属 |
|---|---|---|---|
| 全走 (main 427da17c、計算ノード、583.00s) | 2 failed / 9123 passed / 20 skipped | `test_t793_report.py` の 2 node | **main 由来。本 wave の scope 外** |
| 焦点走 `test_spool_fold.py` (修正前) | 4 failed | real-canonical 4 node | 本 wave の獲物 |
| 焦点走 `test_spool_fold.py` (修正後) | 133 passed | — | — |

全走の 2 件は peer 3 セッション ([T-827] ほか) が独立に同じ結論へ到達しており、
`worktree-dev-wave-t827-slow-tests` の `292151a5` 等で修正済み。**本 wave は当該 file を触っていない。**
「main HEAD 自身がその 2 node で赤」という帰属は、本 wave の全走が独立 2 例目の実証になる。

## 2. 機序 — 全走で隠れ、焦点走でだけ落ちる赤

`tools/spool_fold.py::_load_rotate_limit(repo)` は fold 対象 repo の `tools/check_docs.py` を
`importlib.util.spec_from_file_location` で読む。その `check_docs.py` は
`from dev_waves.launch_authority import ...` という**絶対 import** を持ち、これは
**読み込む側 process の `sys.path`** で解決される。fixture repo の `tools/` は `sys.path` に無い。

repo 外 probe の実測:

| 条件 | 結果 |
|---|---|
| A. `sys.path` に `tools/` 無し (焦点走の状態) | **FAIL** `No module named 'dev_waves'` |
| B. 実 checkout の `tools/` を `sys.path` へ (全走の偶然と同じ状態) | **OK** value=100000 |

つまり全走が緑なのは、他 test module が `tools/` を `sys.path` へ載せる副作用に依存した偶然である。

**同型の 2 例目が既にある。** peer [T-827] の報告によれば [T-813] が
「`orchestrator/` が `sys.path` に入るかどうかが `test_reflux_ir.py` の module 直下
`sys.path.insert` という副作用に依存する」ことを実測している
(正本 `output/insights/2026-08-11_t813-acceptance-sharding/` の M-6b)。
`DW-G03` の「族一般化には独立 2 例」の条件が成立しうる。

## 3. 実装 (テスト側のみ)

`orchestrator/tests/test_spool_fold.py` だけを変更した。

- `_copy_real_canonical_family` が `tools/dev_waves/` の source/schema (15 files, 340,604 bytes) も
  byte-exact 複製する。実 repo には必ず存在するので、複製の欠落は模型の不忠実さだった。
- `_fixture_tools_imports` context manager が、fold 呼出しの区間だけ **fixture 自身の** `tools/` を
  `sys.path[0]` へ置き、`try/finally` で `sys.path` と `dev_waves` 系 `sys.modules` を復元する。
  module scope では `sys.path` を触らない (session 全体へ漏れる恒久汚染を作らないため)。
- 段 6 レビューの must-fix を受けて positive control を 1 node 追加した (下記 4)。

**production (`tools/spool_fold.py` / `tools/check_docs.py`) は 1 byte も変更していない。**

## 4. 段 6 敵対レビューの所見と処置

逐語は `verbatim/s6-review-lens-a.md`。blocker 0、must-fix 3、nit 2。

| # | 所見 | 親の裁定 | 処置 |
|---|---|---|---|
| M1 | 中心契約 (fixture 由来 import / 出入りの復元) を観測する node が 1 つも無い。`repo / "tools"` を `ROOT / "tools"` に書き換えても、両者の source bytes が同一である限り緑のまま | **real・採用** | positive control を追加 (`7dfb772a`)。M4/M5 の変異で恒真でないことを裏取り |
| M2 | 親 brief の「4 node は bytes 厳密 golden」は誤り。N37 は `status`・fragment・path の**構造判定**で `after_bytes` 比較を持たない | **real・採用** | 記録を「failure 台帳の byte 厳密 3 + real canonical plan 構造 1」へ訂正した。変異 M3 の実観測 (N37 が落ちない) が独立に裏付ける |
| M3 | 「全走でも緑」という受入条件が、既知 baseline (2 failed) と矛盾し非一意 | **real・採用** | 受入条件を「main 427da17c 由来の既知 2 node 以外に新規 failure なし」と明記した |
| N1 | `sys.modules` の復元対象は `dev_waves*` だけで、区間内に間接 import された stdlib 15 module と `sys.path_importer_cache` 3 entry は残る | real・**nit** | 現在残るのは stdlib のみで成果物影響を書けない。backlog |
| N2 | `rglob` の filter は source/schema 限定ではない。将来 `tools/dev_waves/` に大きい生成物が入れば複製される | real・**nit** | 現時点では追加 I/O 約 5.4MB (既存 fixture payload の約 3.73%)。backlog |

レビューが**攻撃して破れなかった**点 (所見ゼロの裏取り): golden 到達、例外の握り潰し経路の不在、
入れ子・既存 module 復元、xdist worker 間干渉、fixture 閉包、検出力の直接緩和、production 非変更、
module-scope 汚染の新設なし。

## 5. 変異 matrix

runner scope は `orchestrator/tests/test_spool_fold.py` 全体。ledger は同ディレクトリの
`mutation-ledger-round{1,2,3}.json`、最終 spec は `mutation-spec-round3.json`。

| 変異 | 位置 | 内容 | 期待 | round 3 結果 |
|---|---|---|---|---|
| M1 | test | fixture への `tools/dev_waves/` 複製を削除 | KILLED (5 node) | **KILLED 一致** |
| M2 | test | `real_f196_f197` node から context manager を外す | KILLED (1 node) | **KILLED 一致** |
| M3 | production `spool_fold.py:1818` | supersede 挿入 offset を `.end()` → `.start()` | KILLED (8 node) | **KILLED 一致** |
| M4 | test | context manager が fixture でなく実 checkout の `tools/` を掴む | KILLED (1 node) | **KILLED 一致** |
| M5 | test | 退出時の `sys.modules.update(original_modules)` を落とす | KILLED (1 node) | **KILLED 一致** |

**round 3 = 5/5 KILLED、期待 node 完全一致、baseline PASSED (rc=0)。**

erratum (消さずに残す):

- **round 1 の M3 は MISMATCH。** 期待を real canonical の 3 node と登録したが、実観測は
  synthetic 5 node を含む 8 node だった。`DW-M08` に従い初回を probe と明記し、実観測から
  完全集合を再導出して round 2 で一致させた。M1/M2 は round 1 から一致していた。
- **M3 の実観測に N37 が含まれない**ことが、上記レビュー M2 (N37 は byte golden ではない) の
  独立な裏付けになっている。

**新旧両走 (`DW-M08`) について。** 変更前 HEAD へ同じ変異を走らせる形は取れない —
変更前の tree では baseline 自体が当該 4 node で赤であり、harness が fail-closed で止まるためである。
その事実そのものが新旧差分の証拠になる: **変更前は 4 node が入力によらず必ず落ちるので検出力ゼロ、
変更後は M3 (production の byte offset 変異) で 3 node が正しい理由で落ちる。**

## 6. 裁定パッケージ (ユーザー裁定待ち)

### R1. production `_load_rotate_limit` の cross-checkout import 結合

`_load_rotate_limit(repo)` は fold 対象 repo の `check_docs.py` を読みながら、その依存
(`dev_waves`) を**呼び出し側 process の `sys.path`** で解決する。`tools/dev_wave_land.py` は
main checkout を fold しうるので、**fold 対象 repo と実行元 repo が異なる場合、別 repo の
`dev_waves` が使われる**。現状は import 失敗が `SpoolValidationError` になる fail-closed なので
正しさの穴ではないが、結合は残る。

- 本 wave では**実装しない** — ユーザー裁定「テスト側を直して」の scope 外。
- 選択肢: (a) 現状維持 (fail-closed なので実害なし)、(b) `_load_rotate_limit` が対象 repo の
  `tools/` を import 文脈へ束縛する、(c) `check_docs.py` 自身が自分の隣を `sys.path` へ入れて
  自己完結にする。(c) は `check_docs.py` の bytes を変えるので pin 閉包の再確認が要る。
- **成果物影響:** 現状 (a) のままなら、fold は「読んだ `check_docs.py` の定数」と「別 repo の
  `dev_waves` の挙動」を混ぜた状態で 3 台帳の bytes を書きうる。実害は観測していない。

### R2. 「全走では緑・焦点走では赤」型を受入が構造的に見逃す件

本件の 4 node は、全走を権威とする現行の受入では**構造的に検出できなかった** (他 module の
import 副作用で隠れるため)。同型が [T-813] M-6b に既にあり、**独立 2 例目**である。

- 選択肢: (a) 現状維持、(b) 段 6 の受入に「変更 file の焦点走」を 1 本足す、
  (c) `DW-O18` の焦点走規定を強め、変更 file の単独走を必須にする、
  (d) test module の import 副作用そのものを検査する meta-test を置く。
- **成果物影響:** (a) のままなら、部分走・焦点走を回した作業者だけが踏み続け、
  全走の緑が「その file が単独で健全である」ことを意味しない状態が続く。
- コスト注意: (b)/(c) は走行時間を増やす。ユーザー恒久ルール「開発するほどテストが遅くなる
  構造を作らない」に照らして、増分を実測してから決めるべきである。

**決着 (2026-08-12、実測して (c))。** 焦点走 1 本の増分は Pegasus で login 往復 26.8〜32.0 秒、
受入と同一 job へ畳んだ理想形でも 5〜16 秒だった (`run_tests.py` の dispatch 免除集合は非実行
flag だけなので、実行を伴う焦点走は必ず計算ノードへ回る)。閾値 10 秒を超えたため (b) は不採用で、
`DW-O18` を「変更した test file は受入全走の前に別 process の単独走で 1 度確認する。全走の緑は
その file 単独の緑を含意しない。既に回す走行へ相乗りさせ、受入の後へ足さない」へ強化した。
実測表と file 別分布は worklog の当該エントリを正本とする。
