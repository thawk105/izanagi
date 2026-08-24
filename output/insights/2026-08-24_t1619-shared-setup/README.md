# [T-1619] 受入の重複前置きを s8c predicate 族で共有化した

- wave: `dev-wave-t1619-shared-setup`
- branch: `worktree-dev-wave-t1619-shared-setup`
- base main: `971f0fd74bc7e32b172d541c692220ac5d617c01`
- 実装 commit: `b5a835fe9d4119a25cc960a2b82f6c4cd04067db`
- fix commit: `5d5dfbb7`
- 裁定: D747 (削除ではなく共有化)、本 wave の decisions fragment 2 件

## 何が重複していたか

`orchestrator/tests/test_s8c_preregistration_predicates.py` の `test_current_repository_*` は、
同じ repository snapshot に対する同じ `evaluate_all` を各 test が再実行していた。
snapshot 自体は `scope="module"` の fixture で共有されていたが、**xdist では fixture が
worker ごとに作り直される**ため、5 件が別 worker へ散ると前置きを丸ごと払っていた。

直列走と並列走を同一コマンドで比べるとこれが直接見える。

| 走行 | setup の計上 | 合計 |
|---|---|---|
| 直列 (`-n 0`) | **1 回** (12.49 秒) | 82.93 秒 |
| 並列 (xdist 既定) | **5 回** (各 15.44 秒) | 43.49 秒 |

`scope="module"` は「1 プロセス内で 1 回」であって「suite 全体で 1 回」ではない。

## 何をしたか

1. fixture が snapshot commit の評価を 1 度だけ行い、外側を `tuple` にして共有する。
2. 5 件を新しい xdist group `s8c-predicate-snapshot` へ入れ、同一 worker に閉じる。
3. `test_current_repository_snapshot_exactly_matches_head` の**右辺は共有しない**。
   この test 自身が実 HEAD を独立に評価する。両側を共有値にすると恒真化して検出力を失う。
4. group 名の独立 golden に加え、5 canonical node の独立 literal と **item 件数**を固定する。

## 効果 (同一条件の対比較、計算ノード)

コマンドは前後とも
`python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_predicates.py -q -p no:randomly -k current_repository --durations=0`。

| | 変更前 | 変更後 |
|---|---|---|
| setup 回数 | 5 | **1** |
| setup 合計 | 77.17 秒 | **25.57 秒** |
| call 合計 | 70.11 秒 | **13.29 秒** (残り 4 件は表示閾値未満) |
| setup + call | **147.28 秒** | **38.9 秒** |

前置きの work が 73.6% 減った。

**受入全走への外挿は条件付き推定である。** 変更前の setup 回数は 5 node を実行した
distinct worker 数 k (1 以上 5 以下) に依存する。k=5 かつ焦点走と同じ費用比を仮定すると、
台帳の live 5 件 175 秒は約 46 秒になり削減は約 129 秒。k が小さいほど削減は小さくなり、
k=1 なら約 95 秒である。既知 stale entry を除いた総 work 5316.9 秒に対する work 下界の
改善は約 2.7 秒で、**これは下界の改善であって実 wall の短縮保証ではない**。

新しい鎖は実測 38.9 秒で、既存 floor (`real-repo` 102.6 秒 /
`s8c-preregistration-candidate` 103.0 秒) を下回るため新しい律速にならない。

## 意味を保存したことの証拠

同一 spec (`sha256=9e80d9eb...`) を変更前後の両版へ当て、**両版 baseline 緑**のもとで
赤くなった node 集合を比較した。

| 変異 | 対象 | 版 A (971f0fd7) | 版 B (b5a835fe) | kill 集合の一致 |
|---|---|---|---|---|
| m01 | 評価器の SHA 生成を 63 文字へ | 1 件 | 1 件 | 一致 |
| m02 | evidence 契約 file の whitespace 1 byte (非対称) | 1 件 | 1 件 | 一致 |
| m03 | C05 の reason code literal | 1 件 | 1 件 | 一致 |
| m04 | 汎用 reason code literal | 3 件 | 3 件 | 一致 |
| m05 | `PredicateResult.evidence` を空に | 5 件 | 5 件 | 一致 |

**5 変異すべてで kill 集合が完全一致した。共有化で失われた検出力はない。**

版 A の再走 (m05 の期待集合を実測どおり再登録) は
**baseline 緑・5/5 KILLED・SURVIVED 0・MISMATCH 0**。

版 B は harness の status label が 5 件とも MISMATCH になるが、これは検出力の差ではなく
**harness が group 接尾辞を正規化しない**ためである (failures 台帳へ記録)。
期待 node は collection (接尾辞なし) で実在検査され、失敗 node は接尾辞付きで記録されるので、
どちらの書き方でも完全一致しない。正規化して比較したのが上表である。

## 変異の可視性 — 事前登録を差し替えた理由

段 4 で最初に登録した 3 変異は、被検査テストから**構造的に見えない**面を対象にしていた。
段 2 plan がそう設計し、段 3 の敵対 2 レンズも指摘しなかった。親が段 5 進行中に見つけ、
probe 2 本で実証してから可視面へ再照準した。

| 面 | working tree 変異の可視性 | 実測 |
|---|---|---|
| テストが import する評価器コード | **見える** | 1 件だけ赤 (単一理由性が成立) |
| blob として読まれる評価対象 file | **見えない** | 5 件すべて緑のまま |
| working tree から読み直される evidence 契約 | snapshot 側のみ | 非対称変異として m02 に採用 |

変異 harness は変異を commit せず working tree へ書く。一方、評価は resolved commit の
blob を読む。この型の変異は「効かない」のではなく「見えない」ので**偽の SURVIVED** を作る。

## 追加した guard の負の対照

独立 oracle は当初 canonical 名の set 比較だけだったので、parametrize による item 増加を
検出できなかった。件数の assert を足したうえで、対象を一時的に parametrize して
group の item を 6 件にする probe を走らせた。

- 追加した件数 assert: `actual=6 expected=5` で赤くなった。
- 既存の set 比較 assert: **発火しなかった** (canonical 名に潰れるため)。

穴の実在と閉塞の両方を同じ走行で示している。

## 緑の記録

- `orchestrator/tests/test_s8c_preregistration_predicates.py` — 194 passed
- `orchestrator/tests/test_real_repo_serialization.py` の group 契約・shard・loadgroup・
  負の対照 meta・decorator provenance の 6 nodeid — 6 passed
- `python3 tools/check_ai_provenance.py` — 5488 件、新規違反なし
- `python3 tools/check_docs.py` — 違反なし

## scope 外の所見

- 受入所要台帳に現 source へ存在しない nodeid
  `..::test_current_repository_c12_allocation_binding_helper_accepts_both_calls` が残っている
  ([T-1620] の実証材料)。本 wave では台帳を変更していない。
- `_snapshot_current_commit` は archive 対象 path を決めるために実 HEAD の評価を
  もう 1 回行っている。これを `exactly_matches_head` の右辺と共有すればさらに約 13 秒縮むが、
  **採用しない**。本族は直列 node registry に属さないため、fixture 構築時点と assert 時点の
  間に実 repo が他の writer に変えられる可能性があり、現行コードはその不一致を赤で検出する。
  共有するとこの検出を失う。

## verbatim

- `verbatim/s2-plan.md` — 段 2 plan
- `verbatim/s3-sol.md` / `verbatim/s3-luna.md` — 段 3 敵対相談
- `verbatim/s4-adjudication.md` / `verbatim/s4-addendum-mutation.md` — 段 4 裁定と追補
- `verbatim/s5-author.md` — 段 5 実装
- `verbatim/s6-sol.md` / `verbatim/s6-luna.md` / `verbatim/s6-fix.md` — 段 6
- `mutation-spec-A-rev2.json` / `mutation-result-A3.json` — 版 A の変異 matrix (5/5 KILLED)
- `mutation-result-B3.json` — 版 B の変異 matrix (正規化前は MISMATCH、比較結果は上表)

## erratum — 逐語成果物の可逆最小正規化

段 6 の子出力 3 件は行末に半角空白を持ち、`git diff --check` に抵触した。
`DW-S07` に従い**可視文字を変えない**最小正規化 (行末の空白と tab の除去) だけを行った。
復元は各行の行末へ元の空白を戻すことで行える。元 bytes は下表の hash で照合できる。

| file | 正規化行数 | 元 sha256 | 元 bytes | 正規化後 sha256 | 正規化後 bytes |
|---|---|---|---|---|---|
| `verbatim/s6-fix.md` | 3 | `5134939d87e4eb52537524318d809b5cf4007484698bf01e18ffbbce1b8cd8d5` | 1965 | `828c53edccba093fd9ece9f6825b23eea0c104a6427d9eb238f52f10c92801ed` | 1959 |
| `verbatim/s6-luna.md` | 2 | `7b2d4b7fb828456745de221ed4425e7783d3581dc0357362db8e971a0d728ffd` | 5960 | `6b33318e805156e32baba3dfcb858ff55b644fc7672c50d5f4184dbae86affe4` | 5956 |
| `verbatim/s6-sol.md` | 3 | `65412f6ebb23e22a8422598b441aef0cf09bfe2afcac0029368d984e7195db2f` | 4719 | `afd21b48ad237fdee2dbb50f52994d705bb646779a2cb11aa2cec5ba7d335d75` | 4713 |

除去した bytes はいずれも markdown の hard line break として書かれた行末空白であり、
本文の語・数値・判定は 1 文字も変えていない。

## DW-M07 契約の本走 (最終 tip)

初回の版 A 再走を投入した時点で条件 15 (fix 後に変異を走らせる直前) が成立していたのに、
親が `DW-M07` を読まずに `--runner-mode local` で投入していた。節を読み直し、
契約どおりの本走を最終 tip に対して投入し直した。

- 最終 tip: `c312f3762c2c0f49de40b985c94bfb10b40f6349`
- anchor 5 件の一意性を投入前に再検証 (全件 1 箇所)
- `--runner-mode dispatch`、runner argv へ `--force-dispatch`、
  `--attempt-out` と `--wrapper-attempt` のペア指定、`--detached`
- baseline rc=0、失敗ゼロ

| 変異 | rc | kill 件数 | 変更前 (971f0fd7) の kill 集合と一致 |
|---|---|---|---|
| m01 | 1 | 1 | 一致 |
| m02 | 1 | 1 | 一致 |
| m03 | 1 | 1 | 一致 |
| m04 | 1 | 3 | 一致 |
| m05 | 1 | 5 | 一致 |

**最終 tip の kill 集合は変更前の版と完全一致した。** status label は 5 件とも MISMATCH だが、
これは group 接尾辞を harness が正規化しないためであり (failures 台帳に記録)、
検出力の差ではない。

成果物: `mutation-result-final.json`、`mutation-attempt-final.json`。

初回の local 走 (`mutation-result-A3.json` / `mutation-result-B3.json`) は消さずに残す。
本走で使った変異はいずれも runner の実行経路に無いため、`DW-M07` が local を避ける理由
(runner 自壊による `rc=16`) は本 spec では発生せず、実際に両走とも正常終了している。
