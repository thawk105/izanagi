---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-sort-swo-oracle-exclusion
seq: 1
---

## {{D:sort-swo-oracle-removal}}. test_sort_swo_oracle.py を受入全走から恒久除外する

**決定 (ユーザー裁定):**

1. `orchestrator/tests/test_sort_swo_oracle.py` を受入全走 (`tools/run_tests.py` 経由の
   `tools/dev_wave_wait.py acceptance`) から恒久的に除外する。
2. test file 自体は削除しない。`config.h` 欠落が解決したら復活できる形で残す。
3. 除外は「実行しない」設定であって、正しさゲートの緩和ではない。この区別を実装とテストで明示する。
4. 正しさ検証の他の部分 (CC variant の verifier、他の oracle) には一切触れない。

**理由:**

- 受入の非帰属 (non-attributable) 判定 (`tools/check_acceptance_reds.py`) が、
  `test_sort_swo_oracle.py` 系の失敗を 1 件ずつ `git worktree` 経由で直列に再検証するため、
  41 分以上を要することを実測した (2026-08-23)。並行 wave の一次資料解析では 89.5 秒/件である。
- ユーザーは「受入テスト全体の所要時間は最悪でも 5 分まで、40 分は研究開発を破壊する」という
  基準を示した。
- 失敗原因は `config.h` (masstree 依存) の不在という環境要因で、main 単独で再現する。
  本 wave が clean worktree で全件実測したところ **26 failed, 36 passed in 2.81s** であった。
  **file 自体の実行時間は些少であり、41 分の実体は非帰属判定である。** 除外の効果は
  受入 wall の短縮ではなく、非帰属判定の入力を空にすることである。
  なお 26 件すべてが同一原因かは全件では未検証であり、推定にとどまる。
- `sort_swo_oracle.py` は CC variant が合成する sort comparator の strict-weak-order 公理を
  検証する独立オラクルであり、`CLAUDE.md` 絶対規律 2 が保護する対象である可能性が高いことを、
  実行前にユーザーへ明示的に説明した。ユーザーはこのリスクを認識した上で、なお恒久除外を決定した。

**D532 との関係:**

D532 は却下した選択肢として「テストの削除・skip・selection の縮小で速くする — 規律 2 に反する。
検討対象にしない」と定めている。本決定は、その条項を
**`orchestrator/tests/test_sort_swo_oracle.py` の 1 file についてのみ** supersede する。
D532 の一般則 (selection 縮小で速くすることは規律 2 に反する) は他のすべての file について不変であり、
本決定を前例として除外対象を広げてはならない。実装側もこの制約を実行時 fail-closed で強制する
({{D:sort-swo-oracle-exclusion-mechanism}} を見よ)。

D591 は本 file の oracle environment consumer 24 関数を registry と独立 golden の双方へ登録した。
本決定はその登録を**維持する**。registry から node を削ると独立 golden との等値検査が赤になり、
かつ明示 target 走行・plain な収集 probe・resource 直列化・prewarm の consumer inventory が壊れる。
registry は selection list ではない。

**却下した選択肢:**

- 一時的な `--deselect` での回避 — 恒久対応にならず、今後の受入のたびに同じ超過に当たり続ける。
- `check_acceptance_reds.py` の性能改善を待ってから対応する — 改善完了までの期間、
  研究開発のスループットが損なわれ続けるため採用しない (別 wave で並行して進行中)。
- `pytest.ini` の `addopts` へ `--deselect` を書く — `pytest.ini` 冒頭が addopts 禁止を明記している。
  `tools/run_tests.py` の 4 ゲートは環境変数しか読まず ini の addopts を構造的に見ないため、
  ここに書くと「全走のつもりで実は選択走」が preflight を素通りする (規律 2)。
- ユーザー argv として `--deselect` / `--ignore` を渡す — これらは `_is_full_suite` と
  `_is_acceptance_run` を False にするため、受入形として認識されなくなる。受入全走に使えない。

**申し送り (今後のテスト性能方針、ユーザー明示):**

- テストスイート全体の所要時間は最終的に 5 分以内を目標とする。段階的な導入 (5 分以内に収まる形で
  機能を増やしていくこと) 自体は許容する。
- 40 分という所要時間は許容範囲外であり、同種の性能問題が今後発生した場合は、該当テストの除外を
  優先し、正しさ検証機構自体の再設計・高速化は別途 (性能を伴う形で) 検討する。

**復活条件:** `config.h` (masstree 依存) の欠落が解決し、受入全走で本 file が緑になること。
復活操作は除外表から該当 entry を 1 件削るだけで完了する。

## {{D:sort-swo-oracle-exclusion-mechanism}}. 恒久除外は受入形だけへ注入し、裁定外 path を実行時に拒む

**決定:**

1. 恒久除外は `tools/run_tests.py` の runner 側で実現する。`main()` が
   `_is_acceptance_run(args)` を評価し、True のときだけ除外表を純関数
   `_build_pytest_command` へ `exclusions` 引数として渡す。注入語は `--ignore=<絶対パス>` とし、
   既定 target の**前**へ置く。
2. 除外表の各 entry の path が裁定済みの literal 定数と一致しなければ、command を作らず
   専用 rc で停止する (実行時 fail-closed)。テストだけの担保にしない。
3. 走行ごとに stderr へ除外内容 (裁定 ID・path・理由・復活条件) を 1 行出す。除外を沈黙させない。
4. `orchestrator/tests/conftest.py` の growth hold 完全収集判定は、runner が注入した
   裁定済みの除外を認識し、それを理由に完全収集判定を落とさない。ユーザーが自分で渡した
   `--ignore` / `--ignore-glob` / `--pyargs` は従来どおり収集縮小として扱う。
5. `_suite_identity` の `full` は変更しない。

**理由:**

- 注入条件を `_is_acceptance_run` に束ねると、2 つの破れが 1 つの述語で同時に閉じる。
  (a) `python3 tools/run_tests.py orchestrator/tests` は positional を持つが受入形として
  認識されるため、positional の有無だけで判定すると除外を迂回する。
  (b) `-k <対象 file 内の test 名>` や `--collect-only` は positional を持たないため、
  positional の有無だけで判定すると逆に過剰除外され、復活経路と診断走行が壊れる。
- `_is_acceptance_run` は環境変数を読むため純関数ではない。`_build_pytest_command` の
  docstring は「外部状態を読まず」と明記しているので、判定は `main()` に置く。
  副次的に、`_build_pytest_command` を既定引数で直接呼ぶ既存テストの完全一致述語が
  1 文字も変わらずに済む。
- 注入を既定 target の前へ置くのは、`command[-1]` が既定 target であることを固定している
  既存 exact 述語を壊さないためである。
- **conftest の完全収集判定は、起動引数に `--ignore` があれば偽を返す。** 偽になると
  registry の growth hold が収集から欠落しても `pytest.UsageError` が出ない。
  対策なしに注入すると、除外の副作用で無関係な防壁が黙って外れる。これは規律 2 違反であり、
  「実行しない設定であってゲート緩和ではない」という裁定の前提そのものを崩す。
- 実行時 fail-closed を選んだのは、テストによる担保だけでは、テストを走らせない経路
  (受入以外の実行、テスト自体の改変) で発火しないためである。表へ裁定外 path を足した瞬間に
  受入走が起動時点で止まる方が、receipt へ証跡を足すより防壁として強く、編集面も小さい。

**却下した選択肢:**

- 注入条件を「positional target が無いこと」にする — 上記 (a)(b) の両方で破れる。
- `_build_pytest_command` の中で受入形を判定する — 純関数性を壊し、既存の完全一致述語も壊す。
- `_suite_identity` を `full` 以外へ変える — 受入形の認識が連鎖的に壊れ、受入自体を投入できなくなる。
- task-run receipt / aggregate / acceptance launcher receipt へ除外集合を必須 field として
  証跡化する — 検出可能性は上がるが編集面が 5 file 以上増える schema 移行であり、
  段階導入 (規律 5) に照らして本 wave の範囲を超える。実行時 fail-closed で最小構成に閉じ、
  証跡化案は次の一手として起票する。
- registry (`REAL_REPO_SERIAL_NODES` / `ORACLE_ENVIRONMENT_CONSUMER_NODES`) から
  対象 node を削る — 独立 golden との等値検査が赤になり、復活経路と独立監査を壊す。
