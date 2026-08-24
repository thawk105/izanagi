# [T-1619] 段 4 裁定と変異事前登録

親が段 3 の 2 レンズ (sol = 正しさ境界、luna = 整合・実効性) の全所見を real/refuted、
採用/不採用、scope 内/外で裁定した。

## 所見の裁定

| # | レンズ | 重み | 判定 | 裁定 |
|---|---|---|---|---|
| 1 | sol | must-fix | **real・採用** | 負の対照が共有化後だけの確認になっている。変異は**変更前 HEAD 版と変更後版の両方**へ走らせ、同一 node が同一 assert で赤くなる 4 状態を記録する。`DW-M08` の「新テストだけが検出する差分」の対称形として、本 wave は「前後で検出 node 集合が完全一致」を要求する。 |
| 2 | sol | should-fix | **real・親の実測で解消** | `PredicateResult` と `EvidenceRef` はともに `@dataclass(frozen=True)` (`orchestrator/campaign/s8c_preregistration.py:152,158`)。field は str / enum / tuple のみで、`__post_init__` が `evidence` を tuple 化する (`:165-166`)。深い不変性が成立するので raw instance の共有で安全。独立コピーは不要。この事実を記録へ残す。 |
| 3 | sol | should-fix | **real・不採用 (nit へ)** | gap-reason test を group 先頭へ移す案。受入は fail-fast で走らないため、成果物 (certified 選択・レポート・台帳) のどの値も受理集合も変わらない。`DW-G05` により nit / backlog とし、本 wave では実装しない。関数の移動は無用な diff を共有 file へ足す。 |
| 4 | sol | should-fix | **real・採用** | stale node の 32 秒を削減量に含めていた。live 5 件は 175 秒である。 |
| 5 | luna | must-fix | **real・採用** | 「48 worker でも必ず 5 setup」は過剰一般化。setup 回数は 5 node を実行した distinct worker 数 k (1 <= k <= 5)。表現を「worker ごとに再生成されうる。現観測では 5 worker へ分散した」に限定し、before/after で setup ごとの worker id と setup 回数を記録する。 |
| 6 | luna | must-fix | **real・採用** | stale 混入の訂正 (所見 4 と同一) に加え、work 下界差は実 wall の短縮保証ではない。下界と実測を別々に報告する。 |
| 7 | luna | should-fix | **real・採用 (表現訂正)** | real-repo 追加案の悪化量は「鎖が 147.6 秒になり、推定下界を約 36〜40 秒悪化させる」が正しい。45 秒は鎖そのものの延長量であって makespan 増分ではない。不採用の結論は変わらない。 |
| 8 | luna | must-fix | **real・採用** | 親 brief の「受入 duration 台帳の nodeid 表記が `@group` suffix へ変わる」は**誤り**。runtime は suffix を除いた key を引き (`orchestrator/tests/conftest.py:911-921`)、生成器も suffix を落とす (`tools/update_acceptance_duration_ledger.py` の `_strip_group_suffix`)。台帳 key は不変で、変わるのは duration 値だけ。brief を訂正する。 |
| 9 | luna | should-fix | **real・採用 (情報)** | `_XDIST_GROUP_NAMES_GOLDEN` の更新漏れで赤くなるのは `test_real_repo_group_collection_exactly_matches_canonical_nodes` の 1 件だけ。 |
| 10 | luna | should-fix | **real・部分採用** | 「old-ledger 走と updated-ledger 走を分けて受入全走を複数回」は本 wave の scope 外。受入全走は land 前の 1 回に限る (安い関門を全部緑にしてから投げる規律)。因果は focused 対比較で示す。台帳の再生成は [T-1620] の範疇であり本実装に含めない。 |
| 11 | luna | should-fix | **real・採用 (置き場所は変更)** | 共有 file の hunk は最小化する。ただし 5-node membership oracle は `test_real_repo_serialization.py` に置く。同 file の `_collect_xdist_group_report` を再利用するためで、predicates file へ移すと collection 機構の複製が要り、かえって大きく脆い変更になる。並行 wave (T-1618 / T-1621 / T-1593) は現時点で main との差分ゼロと実測済みで、所有衝突は現実化していない。 |

## 訂正後の数値 (記録・報告はこの値を使う)

- live 5 件の台帳 work: 47 + 4 x 32 = **175 秒** (stale 32 秒は除外)
- 既知 stale 補正後の総 work: 5348.9 - 32 = **5316.9 秒**
- 現 work 下界: 5316.9 / 48 = **110.8 秒**
- 共有後の見込み work 下界: (5316.9 - 130) / 48 = **108.1 秒**
- 見込み下界改善: **約 2.7 秒** (実 wall の短縮保証ではない)
- 削減見込み: 175 秒 → 約 45 秒 = **約 130 秒**
- floor 鎖: `s8c-preregistration-candidate` 103.0 秒 / `real-repo` 102.6 秒
- 新 group 鎖の受入条件: **103.0 秒未満**。超えたら不採用

## プラン v2 (実装子へ渡す確定仕様)

1. `orchestrator/tests/test_s8c_preregistration_predicates.py`
   - `current_commit_snapshot` fixture を拡張し、snapshot commit に対する
     `evaluate_all` の結果を **1 度だけ** 評価して外側 `tuple` で保持する。
   - `test_current_repository_*` 5 件へ
     `@pytest.mark.xdist_group("s8c-predicate-snapshot")` を直接付ける。
   - 5 件の本体を共有結果の読出しへ変更する。**関数名・assert・件数は 1 つも変えない。**
   - `test_current_repository_snapshot_exactly_matches_head` の右辺は共有せず、
     この test 自身が `evaluate_all("HEAD", repo_root=_ROOT)` を新規実行する。
     `actual = snapshot` 等の恒真化は禁止。
2. `orchestrator/tests/test_real_repo_serialization.py`
   - `_XDIST_GROUP_NAMES_GOLDEN` へ `"s8c-predicate-snapshot"` を 1 行追加。
   - 5 canonical node の独立 literal frozenset を同じ golden 節へ追加し、
     `test_real_repo_group_collection_exactly_matches_canonical_nodes` 内で
     収集結果との完全一致を assert する。literal は対象 test file や conftest から導出しない。
3. `orchestrator/tests/conftest.py` と `REAL_REPO_SERIAL_NODES` は**変更しない**。
4. 受入 duration 台帳 (`acceptance_duration_ledger.json`) は**変更しない**。key は不変であり、
   値の更新は [T-1620] の範疇。

## 変異事前登録 (DW-M01 / DW-M08)

harness は `tools/mutation_harness.py`。schema は `izanagi-dev-wave-mutation-spec/v1`。
baseline 緑を必須とする。

**本 wave は意味保存 (検出力同値) の証明が目的なので、各変異を 2 版へ走らせる。**

- 版 A = 変更前 HEAD 版 (共有化なし)
- 版 B = 変更後版 (共有化あり)
- **KILLED の判定は、A と B で赤くなる node 集合が完全一致することを要求する。**
  片方だけが赤い、または赤い node が異なる変異は SURVIVED 扱いとし、
  検出力が変わった証拠として停止する。

| ID | 変異位置 | 期待 KILLED node (完全集合) | 単一理由性の根拠 |
|---|---|---|---|
| m01 | production の `EvidenceRef.blob_sha256` を 1 文字削って 63 byte にする | `test_current_repository_snapshot_has_zero_satisfied_predicates` | `len(ref.blob_sha256) == 64` を直接見る assert は本族でこの 1 件。status と evidence 非空は維持されるので理由が 1 つに絞れる |
| m02 | snapshot 側だけで contract blob の有効 whitespace 1 byte を別の有効 whitespace へ置換 (非対称変異) | `test_current_repository_snapshot_exactly_matches_head` | status / reason は不変で blob SHA だけが変わる。完全等値を見るのは本族でこの 1 件。両側へ同じ変更を入れる対称変異は等値が保たれ kill にならないため非対称にする |
| m03 | snapshot 内 `p3_autonomous_workload_trial.py` の `MAX_APPROVED_GENERATIONS = 2` を `1` へ | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | C11 の reason literal を見るのは本族でこの 1 件 |
| m04 | snapshot 内の実 consumer call `check_reservation` の末尾 1 文字を `x` へ | `test_current_repository_c12_registry_reports_unwired_allocation_consumer`, `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` | C12 の同じ status / reason を 2 件が観測するため、production-only 変異で片方だけを赤にはできない。**過剰決定を認めた上で 2 件を期待完全集合として登録する** (`DW-M03`) |
| m05 | snapshot 内の実 consumer call `read_binding` の末尾 1 文字を `x` へ | 同上 2 件 | 同上。m04 と別 run で適用し、read-binding edge 側の経路を別に踏む |

- 各変異は対象 node だけを別 run で走らせ、m04 と m05 を混ぜない。
- 実装子は各 anchor が production source に**一意に存在する**ことを先に検査し、
  一意でなければその変異を実行しない (`DW-M04`)。
- 受理集合を縮小する wave ではないため過剰拒否の正例は不要だが、
  版 A / 版 B の clean 走 (非変異) が両方緑であることを毎回記録する。

## scope 外へ分離する所見

- 受入 duration 台帳の stale entry
  (`..._accepts_both_calls`) の整理 → [T-1620]
- gap-reason test を group 先頭へ移す診断優先度の改善 (sol 所見 3) → nit / backlog
- 受入全走を old-ledger / updated-ledger で分けて 2 回測る設計 (luna 所見 10) → [T-1620] と併せて起票候補
