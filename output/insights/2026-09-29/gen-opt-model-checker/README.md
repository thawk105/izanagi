# 仕組みごとの小さいモデルでの全場面検査の共通部品 (gen-opt md_7、正しさ関門 U4、2026-09-29)

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_7.txt` (共通指示 `common-2.txt`。いずれも repo の外)。対象 item は [T-2887]。
- 設計の正本: `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` の §4 (取りこぼしへの設計) と §7 の U4 行。
- 切り出し元: `tools/vhash_forwarding_model/` (一次資料 `output/insights/2026-09-29/vhash-forwarding-model/README.md`)。**編集していない。**
- 作ったもの: `tools/cc_model_checker/` (5 file) と `orchestrator/tests/test_cc_model_checker.py`、受入所要台帳への 9 件の追記。
- 読んだ時点の main: `035fc11fa`。実装の最終 commit: `eb083d44e` (統合 `084e8820b` + 段 6 fix `eb083d44e`)。
- 実装は Codex author (plan 1・相談 2・author 1・review 2・fix 1・焦点再レビュー 1)。計算ノードは焦点走・変異本走・受入だけに使った。

---

## 0. 一目でわかる結論

| 問い | 結論 |
|---|---|
| 何を共通部品にしたか | VHash の小モデルのうち仕組みに依らない 4 つ: (1) 状態の全探索、(2) 確定した履歴の依存グラフの閉路判定、(3) 場面の全列挙 (L3 の記述子)、(4) 反例の閉じた形 (schema)。仕組みの状態・遷移規則・仕組み固有の安全性判定・場面の初期状態と witness は、仕組みごとの adapter が書く (§2)。 |
| 実際に使えるか (生死確認) | 共通部品の上で VHash の場面 S8 を再現した。VHash の状態遷移をそのまま共通の探索器に渡し、閉路判定だけを共通部品に替えると、v0 で閉路反例 (最短 12 手)、v1 で反例なしになり、訪問状態数 (v0 2,480、v1 2,032)・反例の有無・最短列の長さが VHash 自身の探索と一致した。v0 の反例は閉じた schema を通り、反例列を再生した最終履歴に閉路の各辺が実在した (§5)。 |
| 検査器が弱くないか | 手作りの正例・負例 9 test。検査器自身への変異 19 本 (対照 1 本 + 1 本 1 条件の 18 本) で、対照は生存、18 本はすべて登録した test で赤になった (login の自走)。計算ノードの本走は §4.3。 |
| VHash の受入で赤になった 2 件の再発防止 | 探索の時間上限は `time.monotonic` で `perf` を含む名前を条件に使わない (性能計測 file の検出 test に掛からない)。新 test file は自走 harness を持つ。焦点走でこの 2 群を含めて緑 (§6)。 |
| 限界 | **「固定した範囲で反例なし」は証明ではない。** 探索は adapter が定義した原子 step と逐次一貫のメモリの下での、与えた初期状態からの全 interleaving に限る。L3 の記述子を生成できることと、その場面を探索したことは別で、本 wave は L3 のどの場面も探索していない (§7)。 |

## 1. 依頼の範囲

依頼 (md_7) の「やること」1〜5 と成果物に対応させる。

| 依頼 | 本 wave でしたこと |
|---|---|
| 1. 仕組みに依らない部分の特定 | §2 の表 |
| 2. tools/ 配下の新 package (VHash は編集しない) | `tools/cc_model_checker/`。VHash の package を import しない (生死確認の probe だけが import する) |
| 3. 反例の schema を閉じた field に | §3.4 |
| 4. test (正例・負例、検査器への変異、自走 harness と inventory の登録) | §4・§6 |
| 5. VHash の最小場面 1 つの再現 | §5 |

scope 外 (依頼どおり): driver への接続 (U5)、個別の仕組みのモデル、L3 の本走、計算ノードでの探索。

## 2. 切り出した範囲

| VHash での実物 | 共通部品での扱い |
|---|---|
| `model.py` の `explore` の幅優先探索・親表からの列の復元・全遷移の判定・最初の違反と witness の記録・統計 | `search.explore` に移した (新しく書いた。VHash のコードは残る) |
| `model.py` の判定の絞り込み (`decide_*` の遷移でだけ J1・J2、回収の遷移でだけ J3) | 判定ごとの `applies(before, after, step)` として adapter が渡す |
| `model.py` の時刻の一意性検査 (モデル自身の不変条件) | `state_invariant` / `transition_invariant` の callback として adapter が渡す。破れたら `ModelInvariantError` で探索を止め、判定の違反と混ぜない |
| `judge.py` の `j1` (ww・wr・rw 辺と DFS の閉路) | `cycles.find_cycle` に移した。VHash の状態型は読まず、adapter が「確定 txn の集合、key ごとの確定版の論理順の並び、確定 txn の read log」を渡す |
| `judge.py` の J2 (timestamp 順)・J3 (GC 安全) | 仕組み固有として移していない。adapter が `Judgment` として足す |
| `scenarios.py` の手作り 10 場面・witness | 仕組み固有として移していない。場面の自動列挙 (L3 の記述子) だけを新しく作った |
| `cli.py` の JSON 出力 (自由な dict) | 閉じた反例 schema (`schema.py`) を新しく作った。CLI は作っていない (U5 の前に要らない) |

## 3. 使い方

### 3.1 探索

```python
import sys; sys.path.insert(0, "<repo>/tools")
from cc_model_checker import Judgment, explore

result = explore(initial_state,
                 transitions=lambda s: [(next_state, step), ...],
                 judgments=[Judgment("J1", applies=lambda b, a, e: ..., check=lambda b, a, e: reason_or_None)],
                 state_invariant=..., transition_invariant=..., witness=...,
                 max_states=None, max_seconds=None)
result.statistics.complete   # queue を尽くしたときだけ真。上限で止めたら偽で stop_reason が理由
result.first_by_judgment["J1"]  # 判定ごとの最初の違反 (幅優先なので最短列) または None
```

- 状態は不変で hash でき、等価と hash が「将来の遷移と全判定に効く情報」をすべて含むこと (adapter の契約。探索器は検査できない)。
- 既訪問の状態へ戻る遷移も判定してから捨てる。違反が見つかっても探索は続ける。
- 時間上限は `time.monotonic`、有限の非負数だけを受ける。

### 3.2 閉路判定

`find_cycle(committed_txn_ids, versions_by_key, read_log_by_txn)` は閉路 (`Cycle(txns, edges)`) か `None` を返す。

- `versions_by_key[key]` の並びが**論理的な版の順**。初期版 (書き手 `INITIAL_WRITER`) を先頭側に置く。並べ方 (VHash なら wts 順) は adapter の責務。
- 辺: 同じ key の隣接した確定版の書き手の間に ww、読んだ版の書き手から読者へ wr、読者から「読んだ版より後の**全**確定版」の書き手へ rw。自分自身への辺と、自分の書いた版を読む read は辺を作らない。直後の版だけに rw を張ると、初期版を挟む閉路を見逃す (test `test_cycle_all_later_versions`)。
- 辺の根拠は `from_version`・`to_version` の組 (ww = 前版・後版、wr = 読んだ版・読んだ版、rw = 読んだ版・上書きした後続版)。
- 不正な履歴 (版 ID の重複、同じ key に同じ取引の版が 2 つ、書き手・読者が確定集合に無い、read の版が無い・key が食い違う、初期版が後ろにある) は `ModelInputError` で拒否する。判定の違反ともモデルの不変条件とも別の型。

### 3.3 場面の全列挙 (L3)

`iter_l3(transactions)` (2 または 3) が記述子 `ScenarioDescriptor(id, txn_ops, initial_versions)` を決定的な順で返す。1 txn の操作列は {R, W} × {A, B} の 1 個 (4 通り) と 2 個 (16 通り)、key ごとの初期版は 1 個か 2 個。件数は 2 txn で 20² × 2² = 1,600、3 txn で 20³ × 2² = 32,000 (設計 §4.3 の試算と一致、test で固定)。

**記述子は timestamp を持たない。** 時刻の割り当てと版の順は仕組みごとの adapter が決め、その規則を仕様の digest に含める (U5 への設計メモ §8)。同じ操作列でも時刻の配置で結果が変わりうるので、L3 は「操作列 × 初期版数の全組合せ」であって「時刻配置の全組合せ」ではない。

### 3.4 反例の閉じた schema (`cc-model-counterexample/1`)

field は次で全部: `schema`、`specification_digest` (`sha256:` + 64 hex)、`scenario_id`、`judgment_id`、`steps` (各 step は `number`・`thread`・`name`・`key`・`version_id`・`observed_value`)、`cycle_txns`、`cycle_edges` (各辺は `source`・`target`・`kind`・`key`・`from_version`・`to_version`)、`rule_ids`。

- 未知 field・欠落 field・型違い (bool を int として受けない)・重複 JSON key・NaN を拒否する。
- 文字列は `[A-Za-z0-9_.:-]` の 1〜64 文字 (空白・改行を含む自由文は通らない)。観測値は null・bool・|値| ≤ 2^63 の整数・同じ文字種の原子文字列だけ。VHash のように値を持たないモデルは null を使う (生死確認で確認)。
- 件数上限: steps 1,024、閉路の txn・辺と規則 ID は各 64。
- `J1` の反例は閉路が必須で、辺が txn の並びを順に結んで閉じていること。他の判定 ID では閉路 field は null。
- 任意の `vocabulary` を渡すと、`judgment_id`・step の `name`・`rule_id` を仕様が宣言した語彙と照合する。
- **schema を通ることは形の保証であって、反例が真であることの保証ではない。** 真偽は反例列の再生で確かめる (§5 の probe がその形)。また `ignore_previous_instructions` のような原子文字列は文字種では拒否できないので、coder へ返す U5 は仕様の語彙を必ず渡し、文字列をデータとして扱う (規律 6、§8)。

## 4. 検査器が弱くないことの確認

### 4.1 手作りの正例・負例 (`orchestrator/tests/test_cc_model_checker.py`、9 test)

| test | 確かめること |
|---|---|
| test_search_all_edges_and_shortest | 分岐した小さい遷移系で、全遷移の判定、既訪問の状態へ戻る遷移の判定、幅優先の最短列、違反後も全状態を回ること、witness の列 |
| test_search_limits_and_invariant_error | 状態数・時間の上限で complete が偽、時間上限の NaN・無限大の拒否、状態・遷移の不変条件の破れが `ModelInvariantError` になり元の例外を保つこと |
| test_cycle_ww_only_required / test_cycle_wr_only_required / test_cycle_write_skew_rw_only_required | ww・wr・rw のそれぞれが閉路に必須となる専用の履歴 (その辺種を消すと閉路が消える) |
| test_cycle_all_later_versions | 初期版を挟む rw (直後の版だけに張ると見逃す) |
| test_cycle_input_validation | 不正な履歴 6 種の拒否と、正しい履歴の受理 |
| test_l3_counts_order_ids | 件数 1,600 / 32,000、ID の一意性、順序の再現性 |
| test_counterexample_schema | JSON の往復、未知 field・自由文・bool の番号・欠落・つながらない閉路・重複 key・NaN・件数超過・語彙外の拒否 |

### 4.2 検査器自身への変異 (login の自走)

eb083d44e の package と test の複製に 1 本ずつ注入し、test file の自走 harness を回した。生出力 `raw/mutation-selfrun-results.json`、spec `raw/mutation-spec.json` (sha256 `81570c3d…`)。

| 変異 | 外した条件 | 期待 | 観測 | 赤になった test |
|---|---|---|---|---|
| MC0 | comment だけ (対照) | 生存 | 生存 | なし |
| MC1 | 各状態で最初の遷移だけ展開 | 赤 | 赤 | test_search_all_edges_and_shortest |
| MC2 | 既訪問先への遷移で判定しない | 赤 | 赤 | 同上 |
| MC3 | 最初の違反で探索を打ち切る | 赤 | 赤 | 同上 |
| MC4 | queue を後入れ先出し (深さ優先) | 赤 | 赤 | 同上 |
| MC5 | 新しい状態の不変条件を見ない | 赤 | 赤 | test_search_limits_and_invariant_error |
| MC6 | 上限で止めても complete を真 | 赤 | 赤 | 同上 |
| MC7 | ww 辺を作らない | 赤 | 赤 | test_cycle_ww_only_required |
| MC8 | wr 辺を作らない | 赤 | 赤 | test_cycle_wr_only_required |
| MC9 | rw 辺を作らない | 赤 | 赤 | rw を使う閉路の 4 test (外した条件は 1 つ。どの閉路 fixture も rw 辺を 1 本は使う) |
| MC10 | rw を直後の版だけへ | 赤 | 赤 | test_cycle_all_later_versions |
| MC11 | 版 ID の重複検査を外す | 赤 | 赤 | test_cycle_input_validation |
| MC12 | 未知 field を許す | 赤 | 赤 | test_counterexample_schema |
| MC13 | 原子文字列の文字種検査を外す | 赤 | 赤 | 同上 |
| MC14 | 長さ 2 の操作列を列挙しない | 赤 | 赤 | test_l3_counts_order_ids |
| MC15 | 同じ key の同じ書き手の重複検査を外す | 赤 | 赤 | test_cycle_input_validation |
| MC16 | 時間上限の有限性検査を外す | 赤 | 赤 | test_search_limits_and_invariant_error (赤の理由は NaN と +∞。-∞ は負数検査でも拒否されるので MC16 の証拠に数えない) |
| MC17 | steps の件数上限を外す | 赤 | 赤 | test_counterexample_schema |
| MC18 | 語彙の照合を外す | 赤 | 赤 | 同上 |

外す条件は 1 変異 1 つにした (VHash の GC 接続 wave で 2 つ同時に外すと状態が爆発した先例による)。

### 4.3 計算ノードでの変異本走

同じ spec (sha256 `81570c3d…`) を、repo 外の独立 clone を eb083d44e に固定し、`tools/pegasus/dispatch_compute.py --task mutation` の束ね経路 (変異 wrapper 1 呼び出しを計算ノードの 1 job にまとめ、内側は `--runner-mode local` で `tools/run_tests.py` を回す) で走らせた。request 35515.nqsv、Elapse 495 秒、wrapper rc=0。結果は **登録 19・完了 19・一致 19 (KILLED 18、SURVIVED 1 = MC0、MISMATCH 0)**。KILLED の赤 node は自走の期待 node の完全集合と一致した。生出力 `raw/mutation-final-results.json`。

1 回目の投入 (request 35499.nqsv) は、束ね経路の dispatcher が `tools/mutation_worktree.py` を自分で前置するのに、起動 script が argv の先頭へ `python3 tools/mutation_worktree.py` を重ねて渡したため、計算ノード上の wrapper が引数不足 (argparse、rc=2) で 6 秒で終わった。変異は 1 本も注入されていない。起動 script から重ねた部分を外して投げ直したのが上の結果である。

## 5. 生死確認 — VHash の場面 S8 を共通部品で再現

repo 外の使い捨て probe (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_7-model-checker/probe/liveness_vhash_s8.py`、sha256 `ddc76b01…`、Codex author が書き親が実行後に repo 外へ退避。repo には入れていない) を、親が wave の木 (084e8820b) に対して実行した。生出力 `raw/liveness-stdout.json`。

やり方: VHash の `s8_prefix()` (S8 の初期状態から 18 手進めた、VHash 自身の test が使う途中状態) から、v0 と v1 のそれぞれで (a) VHash 自身の `explore` と (b) 共通の `explore` + 共通の `find_cycle` (J1 の判定を `decide_*` の遷移に限る、VHash と同じ絞り込み) を上限なしで回した。

| protocol | VHash の探索 | 共通部品 |
|---|---|---|
| v0 | J1 反例あり、最短 12 手、訪問 2,480 | J1 反例あり、最短 12 手、訪問 2,480 |
| v1 | 反例なし、訪問 2,032 | 反例なし、訪問 2,032 |

v0 の反例は閉じた schema に変換して検証を通り (step の `observed_value` は全て null)、反例列を VHash の `replay` で再生した最終状態で VHash 自身の J1 も閉路を返し、共通部品の閉路の各辺 (種類・key・根拠の版) が再生後の履歴に実在した。所要は 1 探索 0.14〜0.18 秒 (親の実走)。

示していないこと: S8 の初期状態からの全探索 (prefix から始めた)、J2・J3 を共通部品で扱うこと (VHash 固有として移していない)、S8 以外の場面、L3 の場面。

## 6. 登録と受入

- 自走 harness: 新 test file の末尾に、test_* を名前順にすべて呼び失敗があれば exit 1 にする harness を置いた (`test_plain_runner_coverage.py` の検査を満たす。allowlist に載せていない)。
- 性能計測 file の検出 (`test_official_perf_closure.py`): 探索の時間は `time.monotonic` で、`perf` を含む名前を条件に使わない。inventory には何も足していない。
- subprocess を使わない (`tools/check_subprocess_bytecode_guard.py` rc=0)。
- 受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json`: 新 test 9 件を `tools/update_acceptance_duration_ledger.py --add-only` で追記した (既存 entry は不変、`--check --add-only` で追加 0 件を確認)。
- 焦点走 (親、計算ノード): fix 後の 12 file で 934 passed・3 skipped・失敗 0 (成長 hold 0)。対象は新 test、自走 harness・bytecode guard・性能 file・certified writer・探索 namespace・wiring probe・収集設定・login headroom・受入順序・台帳更新・A1 headline の各 test。
- 受入全走の結果は本 dir に書かない (受領証と worklog が所在)。

## 7. 範囲と、確かめていないこと

- **「固定した範囲で反例なし」は証明ではない。** 探索は adapter が定義する原子 step、逐次一貫のメモリ、与えた初期状態に限る。key 数・txn 数・操作数の外、弱いメモリモデル、途中で入場する txn、範囲読み・insert・delete は、adapter がモデルに入れない限り範囲外。
- **L3 は記述子の生成だけ。** 1,600 / 32,000 件を生成でき件数が合うことは確かめたが、どの仕組みでも L3 の場面を探索していない。txn 3 個の層は設計 §4.3 の試算で最大約 58.7 CPU 時間 (1 構成 6.6 秒という VHash の最大値を仮定した上限でない試算) で、仕組みごとに実測して決める。
- **状態の同一視は adapter の契約。** 等価・hash から判定に効く情報を落とすと反例を見逃すが、探索器はそれを検出できない。
- **閉路判定の版順は adapter の責務。** 誤った順で渡すと偽の辺・辺の見逃しが起きる。入力検査は ID・書き手・key の整合までで、順の正しさは検査しない。
- **schema は形だけを保証する。** 真偽は再生で確かめる。原子文字列でも命令めいた語は書けるので、語彙の照合と「データとして扱う」ことは U5 の義務 (§8)。
- **診断の優先順:** 件数上限の超過は要素の型の誤りより先に報告される (受理集合は変わらない。焦点再レビューの nit)。
- 進行保証 (deadlock・starvation) は判定しない。探索器は終端状態の数だけを数える。

## 8. U5 (driver 接続) への設計メモ (実装していない)

- 反例なしの結果を「合格」に使うには、反例 schema とは別の結果の記録が要る: 仕様の digest、adapter の時刻割り当て規則、探索した場面 ID の集合、各探索の `complete` と `stop_reason`。**`complete` が偽の探索を合格に数えない。**
- 反例を coder へ返すときは、仕様が宣言した語彙 (`judgment_id`・step 名・規則 ID) を `vocabulary` に渡して照合し、文字列はデータとして扱う (規律 6)。
- 反例は再生して真偽を確かめてから失格に使う (設計 §4.2 の 7、F1060)。

## 9. 何を確かめ、何を確かめていないか

確かめたこと (実行による):
- 新 test 9 件が計算ノードの pytest で全件成功 (統合時 4.22 秒、各 test 0.01〜0.22 秒)、fix 後の焦点走 934 passed・失敗 0。
- 変異 19 本の自走が事前登録どおり (§4.2)。
- S8 の v0 / v1 で共通部品と VHash の探索の結果が一致 (§5)。

確かめていないこと:
- L3 の場面の探索、S8 以外の VHash の場面、J2・J3 の共通化。
- 段 A の仕組みのモデルでの使い勝手 (まだモデルが無い)。
- U5 からの利用。

## 10. 次の一手

- 段 A の最初の仕組みのモデル: adapter (状態・遷移・時刻割り当て・場面の初期状態・witness) を書き、`explore` と `find_cycle` と schema を使う。L3 の txn 2 個の層 (1,600 構成) をまず login で流して 1 構成の所要を実測し、txn 3 個の層を計算ノードに流すかを見積もる (仕組み 1 つあたり 2 node 時間を超えるならユーザー確認)。
- U5 ([T-2888]): §8 の結果記録と語彙の照合を driver 側に置く。

## 11. 再現

```bash
# test (Pegasus login では tools/run_tests.py 経由)
python3 tools/run_tests.py -q orchestrator/tests/test_cc_model_checker.py
# 自走
PYTHONPATH=. python3 orchestrator/tests/test_cc_model_checker.py
```

変異の自走に使った親の script は repo 外 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_7-model-checker/mutation/build_and_selfrun.py`)。本 dir の `raw/` はその出力の複製。
