# 段 4 裁定と plan v2・変異事前登録 (親、dev-wave [T-2236])

## 段 4 裁定 (親、07:12 JST。裁定 inbox 再走査: main は b4631a92e のまま、新規裁定なし)

所見の裁定 (A = レンズ A 正しさ境界、B = レンズ B 実効性):

- A1 **real・採用**: land 競合時の契約を明文化する。入力 JUnit は `d3ebafc0…` に固定。land で main 側台帳が進んでいたら
  main の現物を base に同じ 3 JUnit で `--refresh` を再走する (決定的)。main が add-only で足した非凍結 node のうち
  入力 JUnit に無いものは落ちる (consumer では 1.0 秒扱いへ戻る、次の add-only wave が再登録)。落ちた node は
  **名前と件数を insight に記録**する。refresh を F902 の和集合 merge へ流用しない (両者は別契約: add-only = 既存値保持、
  refresh = 非凍結の置換)。手編集・main 値の無条件持越しはしない。
- A2〜A8 **refuted** (根拠は各所見のとおり。A4 は親の実測 4 でも一致 = 凍結 426 行の往復差 0)。
- A9 / B7 **real・採用**: 被覆分子は 24361 (= 24379 − stale 18)。brief の数字を訂正 (本 handoff・insight・worklog に反映)。
- A must-fix 2 / B #9 **real・採用**: 変異 #9 の fixture は coverage 一覧に「JUnit にあるが refresh が除外する凍結新規 node」を
  含める (正例 1/2、変異 2/2)。plan v2 の test 10 へ反映。
- A nit 1 **採用**: 兄弟 file (`test_critic_extra.py::` 型) を非凍結として更新する正例を test 2 か 3 の parameter に足す。
  A nit 3 / B nit **採用**: failed/error の非凍結 entry は「削除する」と仕様として断定する。
- B1 / A P4 **real・採用**: brief の「原因なので…そのまま均す」は過剰断定。記録は「観測上の乖離が大きく更新対象として妥当。
  割付・wall への効果は未確認 (after 1 走の観測値のみ)」に改める。差 3151 秒 = 既知 node 2932 秒 + 未登録 219 秒。
- B2 **real・採用 (親の実測 script の是正)**: 集計 script に consumer の `nodeid@group` fallback を足して再集計し、
  差を記録する (影響は凍結 `@real-repo` 1 件と見込むが実測する)。
- B3 / B4 **real・採用 (検算項目)**: 最終検算に 3 shard 横断の canonical nodeid 重複検査・failed/error 件数・producer の
  採用集合との一致を足す。producer 自身も重複を拒否するので二重の防壁になる。
- B6 **real・採用**: 記録の分類を訂正 (上記)。
- B8 **real・記録**: 凍結 8 suite の残差は合計 −334 秒でも shard 間差で最大 563 秒 (均等負荷 6046 秒の 9.3%) 残りうる。
  T-1903 (pin の述語化) が未実施である限りの既知限界として insight に書く。scope 外。
- B9 **未実測・after 実測で置換**: 最大連結成分と refresh 後の予測負荷は、after 1 走の report.json (割付) と JUnit
  (shard 別直列和) で実測して記録する。事前の概算はしない。
- B P2 (1 走の競合膨張が数値和の割付を歪めうる) **real・記録**: 順位だけでなく数値和を使う割付器への一般化は不可。
  1 走入力の限界として記録。4 走の結合は生成器が拒否するため採らない。
- B P4 (before 4 走は反復比較の代わりにならない) **real・採用**: 記録形式を B の列挙どおりにする (session・commit・
  collection 件数・台帳 hash・割付・worker 数・wall の取得元・成否・条件)。結論は「更新後 1 走の観測値。効果と原因は未判定」。
- B must-fix 5 **採用**: 「今回更新した非凍結 = 23953 件、現 collection と交わる保持凍結 = 408 件」を記録する。
- B #2 変異注意 **採用**: 凍結値上書き変異は共通 key だけ上書きする形にする (KeyError の別理由赤を避ける)。
- B #6 変異注意 **採用**: `sort_keys=False` 変異の fixture は既存台帳の凍結 entry を非 sort 順に置く。
- B nit (親 script が主 checkout を読む) **採用**: 集計 script の repo path を wave worktree に揃えて再走し、値が同じことを確認。
- scope 外のまま: `--coverage-against` の marker 行対応 (backlog)、T-1903、閾値・凍結 prefix・除外集合、scheduler。
- 「実装しない」裁定はなし → 段 5 へ進む。

plan v2 (plan の設計を基礎に、上記採用分を反映):

1. `tools/update_acceptance_duration_ledger.py`: `--refresh` を `--add-only` と排他 group で追加。`_refresh_result(generated,
   existing_durations)` を `_add_only_result` の隣に追加 (凍結 = 既存 entry を値ごと保持、非凍結 = JUnit 由来で置換・削除・追加、
   凍結 prefix の JUnit testcase は採用しない)。描画は canonical (`sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False` + LF)。
   stdout: `mode=refresh`、`preserved_frozen=`、`replaced=`、`added=`、`removed=`、`excluded_frozen_suite=`。
   `--check` / `--coverage-against` / `--output` は refresh 後の集合で従来どおり動く。既存台帳が不在・不正なら rc=2。
2. test 12 本 (plan の一覧) + 兄弟 file 正例 + 変異 #9 用 coverage fixture。既存 test は削除・改名・期待値変更なし。
3. 台帳: author が上記 command (plan の手順 3) で生成し、`--check` で rc=0 を確認する。
4. 親の検算: 凍結 426 行の byte 一致 (refs/frozen-entries-before.txt)、T-1574 の 8 hash・12 値・removed 不在、
   `nodeid_count` = 24379、非凍結 stale 0、被覆 24361 / 24568、重複 0、failed/error 0、canonical 再描画一致。

変異事前登録 (B-057、anchor は実装後に exact 行へ転記。expected node は `orchestrator/tests/test_update_acceptance_duration_ledger.py::…`):

- M0 (等価): `_refresh_result` の docstring だけを同義に書換 → SURVIVED 期待。
- M1: 非凍結採用の prefix 除外条件を外す (凍結 JUnit testcase を採用) → `test_refresh_excludes_all_frozen_junit_nodes`。
- M2: 凍結 map のうち JUnit と共通する key の値を JUnit 値で上書き → `test_refresh_preserves_frozen_entry_bytes_and_values`。
- M3: 結果の初期値を凍結 map でなく既存全 map にする (非凍結の旧名が残る) → `test_refresh_replaces_nonfrozen_entries_and_removes_old_names`。
- M4: 共通する非凍結 key に旧台帳値を採用 → 同上 (異値 case)。
- M5: 凍結値に `_quantize_seconds` を再適用 → `test_refresh_preserves_frozen_entry_bytes_and_values` (5.89 → 5.9)。
- M6: 描画の `sort_keys=True` → `False` → `test_refresh_renders_canonical_bytes` (既存台帳の凍結 entry を非 sort 順に置く fixture)。
- M7: `--refresh` と `--add-only` の排他 group を独立 option に戻す → `test_refresh_and_add_only_are_mutually_exclusive`。
- M8: refresh 分岐で既存台帳不在を空 map として扱う → `test_refresh_requires_existing_ledger`。
- M9: coverage へ渡す集合を refresh 後の集合でなく JUnit 全集合にする → `test_refresh_check_and_coverage_use_refreshed_nodeids`
  (coverage 一覧に凍結新規 node を含む fixture)。
- 単一理由性は実装後 (段 6) に `DW-M07` で anchor を確認する。T-1574 への帰属 (M1/M2 で実台帳を再生成すると赤) は
  隔離 worktree で producer を変異させて実台帳を再生成する補助 probe として親が 1 回実測する (matrix 本体には入れない)。
