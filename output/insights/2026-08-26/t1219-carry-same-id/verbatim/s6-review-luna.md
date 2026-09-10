## 所見

### V-1 採番 archive 正例に許可外の fixture 補正が入っている
対象: orchestrator/tests/test_check_docs.py:11212  
攻撃: archive entry 1000 の次の一手への T-002 追加だけ残し、current entry 1 の `- [T-002] consumed` を除く。  
なぜ通ってしまうか: 後者が archive から current への別の rotation transition まで修復し、二つの条件を同時に変えている。  
直し方: entry 1 が元から消費する ID を archive target と carry に使い、参照先の次の一手だけを補正する。  
成果物影響: 採番 archive carry の受理証拠が、無関係な rotation sink の追加を前提にした値になる。  
重大度: must-fix。

### V-2 M3 は診断文字列だけで形式上 kill される
対象: orchestrator/tests/test_check_docs.py:10935  
攻撃: 登録 key ごとの `actual == expected` 検査を除去して T-211 occurrence を消す。  
なぜ通ってしまうか: parsed 数も 4 から 3 へ減るため、母数下限が別理由で rc=1 を維持する。テストは消えた診断文字列だけで失敗する。  
直し方: loaded checker の下限を 0 にするか、同数の有効 carry を足し、台帳照合だけが拒否理由になる入力にする。  
成果物影響: 登録 occurrence 消失の拒否層を撤去しても、受理集合を検査したという誤った mutation 証拠が残る。  
重大度: must-fix。

### V-3 M4 も per-key 検査が残るため受理集合を kill しない
対象: orchestrator/tests/test_check_docs.py:10919  
攻撃: 台帳総数の固定値照合を除去し、現テストどおり未観測のゼロ digest を登録する。  
なぜ通ってしまうか: 追加 digest の `expected=1, actual=0` が別 finding になり、総数検査なしでも rc=1 のままである。  
直し方: 台帳は実在する 4 件のまま `EXPECTED_KNOWN_CARRY_ID_MISMATCHES=5` だけを変える。  
成果物影響: 台帳総数 pin を撤去しても拒否集合が変わらない入力しか検査せず、固定値契約の独立性を証明できない。  
重大度: must-fix。

### V-4 M5 の同数検査は個別 candidate finding と拒否理由が重複する
対象: orchestrator/tests/test_check_docs.py:11004  
攻撃: `candidate_count != parsed_count` の finding だけを除去し、`(073)` などを入力する。  
なぜ通ってしまうか: invalid sample 自体が findings に追加されるので、新実装は依然 rc=1 となり、同数診断の欠落だけでテストが落ちる。  
直し方: sample を同数違反の付帯情報にまとめるか、M5 を「個別 finding と同数検査の双方を撤去」に再定義する。  
成果物影響: parser 完全性ガードを単独で失っても、受理集合を守ったという mutation 証拠にならない。  
重大度: must-fix。

### V-5 M8 の collapse 後も別の台帳違反で赤のままである
対象: orchestrator/tests/test_check_docs.py:10953  
攻撃: occurrence を target 73 の最初の 1 件へ collapse する。  
なぜ通ってしまうか: 新 source は消えるが、同時に既知 T-209〜T-211 も消え、台帳の `actual=0` が rc=1 を維持する。  
直し方: 台帳を既知 1 occurrence だけに specialize し、同じ target/ID の未登録 source を 1 件追加する。  
成果物影響: source 別 occurrence を target 単位へ戻しても、新 source の取りこぼしを受理集合として検出できない。  
重大度: must-fix。

### V-6 M10 の早期 return を観測するテストがない
対象: stage6/snapshot-s5.patch:663  
攻撃: incomplete finding は残したまま `return` だけ除去し、部分 universe と carry source を同時に渡す。  
なぜ通ってしまうか: 新設 direct tests はすべて `numbered_archive_input_complete=True` で、既存 fail-closed テストも元の構造 finding が残れば赤のままである。  
直し方: false を直接渡し、停止 finding 以外の mismatch、台帳、母数 finding が一切増えないことを確認する。  
成果物影響: 不完全な索引を使った参照診断が成果物へ混入し、誤った修正先を提示する。  
重大度: must-fix。

### V-7 key 不在・None・空集合経路は occurrence を全件数えていない
対象: stage6/snapshot-s5.patch:712  
攻撃: 同じ空 target を指す carry を 25 件、または異なる空 target を 404,326 件与える。  
なぜ通ってしまうか: 4 個の `dict[target]` が同一 target を 1 件へ collapse し、異なる target では全参照を保持して最後に sort する。  
直し方: 各分類を total counter と最大 20 sample にし、target 単位 dict を保持しない。  
成果物影響: 抑止件数が実 occurrence 数より小さくなり、最悪時はメモリ O(C)、sort は O(C log C) になる。  
重大度: must-fix。

### V-8 streaming テストは背後の全件 materialize を検出できない
対象: orchestrator/tests/test_check_docs.py:11108  
攻撃: 全 occurrence を list 化してから `iter(list)` を返す実装へ変える。  
なぜ通ってしまうか: iterator identity、順序、件数、scan 値はすべて現 assertion を満たす。呼出側も `carry_sources` を先に list 化している。  
直し方: 一手ずつ消費を記録する source/item generator を与え、最初の `next()` 前後で先読みされていないことを確認する。  
成果物影響: 404,326 carry の全保持へ退行しても、bounded-memory という成果物特性が検査上は維持される。  
重大度: must-fix。

### V-9 共有 fixture の安全な解消には opt-in ledger fixture が必要
対象: orchestrator/tests/test_check_docs.py:421  
攻撃: 合成 archive だけを除く、または copied checker の台帳だけを空にする。  
なぜ通ってしまうか: 前者は全共通 repo を台帳消失と母数不足にし、後者だけでは production 台帳の統合検査を全 consumer から消す。  
直し方: 基本 fixture は台帳 `{}`、期待総数 0、下限 0 にし、専用 helper だけが実台帳と archive 73〜78 を同時に opt-in する。  
成果物影響: 無関係な archive/rotation テストの受理集合から entry 73〜78 を除きつつ、既知 4 occurrence の受理証拠を専用テストへ保持できる。  
重大度: must-fix。

### V-10 定数 specialize は静かには壊れないが旧実装 control を阻む
対象: orchestrator/tests/test_check_docs.py:1153  
攻撃: 定数を改名するか、positive-control テストを変更前 checker に対して実行する。  
なぜ通ってしまうか: `count(...) == 1` が setup で失敗するため偽緑にはならないが、旧 checker の受理判定へ到達もしない。  
直し方: legacy-control 用の明示モードを設け、通常モードでは現在の exact sentinel assertion を維持する。  
成果物影響: 定数改名は黙って下限を緩和せず全 fixture を赤にする一方、旧緑・新赤の実測根拠は setup error と区別できない。  
重大度: nit。

## 変異 M1〜M10 の kill 判定

| 変異 | 判定 |
|---|---|
| M1 | `test_backlog_guard_carry_same_id_mismatch_is_positive_control` が受理集合として殺す |
| M2 | `test_backlog_guard_carry_same_id_mismatch_is_positive_control` が受理集合として殺す |
| M3 | `test_backlog_guard_registered_carry_mismatch_removal_is_violation` が形式上殺すが、診断文字列のみ |
| M4 | `test_backlog_guard_carry_mismatch_ledger_total_is_enforced` が形式上殺すが、診断文字列のみ |
| M5 | `test_backlog_guard_carry_candidate_parse_break_is_positive_control` が形式上殺すが、診断文字列のみ |
| M6 | `test_backlog_guard_carry_reference_population_floor_rejects_shrink` が受理集合として殺す |
| M7 | `test_backlog_guard_carry_target_index_states_are_distinct[missing]` が診断分類として殺す。rc は他 finding でも赤 |
| M8 | `test_backlog_guard_same_target_and_id_from_new_source_is_violation` が形式上殺すが、別台帳違反で赤のまま |
| M9 | `test_backlog_guard_entry_universe_and_index_must_match` が受理集合として殺す |
| M10 | 殺せない |

新設テスト別の検出力は次のとおり。

| テスト | 判定 |
|---|---|
| `carry_same_id_mismatch_is_positive_control` | 意味上は旧緑・新赤。強い negative control |
| `known_carry_id_mismatches_are_clean` | 実台帳の positive acceptance |
| `carry_mismatch_ledger_entries_are_pinned_exactly` | 定数と digest の静的 pin。受理集合は見ない |
| `carry_mismatch_ledger_total_is_enforced` | 診断文字列のみ |
| `registered_carry_mismatch_removal_is_violation` | 診断文字列のみ |
| `same_target_and_id_from_new_source_is_violation` | source 診断は見るが、mutation 後も別理由で赤 |
| `carry_candidate_parse_break_is_positive_control` | 入力は旧緑・新赤だが、M5 単独には診断文字列のみ |
| `carry_reference_population_floor_rejects_shrink` | 独立した受理集合検査 |
| `entry_universe_and_index_must_match` | 独立した受理集合検査 |
| `carry_target_index_states_are_distinct` | 三分類の診断契約。受理集合はいずれも赤 |
| `fold_shape_carry_chain_is_clean` | fold 形の positive acceptance。spool 実生成は見ない |
| `carry_references_are_streamed` | iterator 形状だけで、materialize 退行は検出不能 |
| `carry_findings_are_sampled_without_early_stop` | mismatch 経路には有効。missing/index 経路は対象外 |

## 共有 fixture 波及の追加候補

- `test_backlog_guard_carry_candidate_parse_break_is_positive_control`: `candidate=5, parsed=4` は合成 archive の 4 carry を含む絶対値である。共有 archive を外すと本来は `1/0` になり、差分値へ直さない限り失敗する。
- entry 73〜78 または 2026-07-26 と衝突する既存入力は、対象ファイル内の exact 検索では見つからなかった。追加 archive は他の archive テストより早く、entry 78 の次の一手も空なので、これ以外の偶然の緑候補は静的には確認できない。

## 総括

M1、M2、M6、M9 は受理集合を検査するが、M3〜M5、M7、M8 は主に診断文字列で形式上 kill している。M10 は未検出である。  
共有 fixture は基本 checker を空台帳へ specialize し、実台帳と合成 archive を専用 helper で opt-in する構成が最も安全である。  
禁止された dangling、prose、unnumbered の 3 テストは差分上変更されていない。一方、採番 archive 正例には許可外の二つ目の補正がある。  
最悪 mismatch 経路の時間は carry 数に線形、索引空経路は target dict と sort によりメモリ線形、時間 O(C log C) まで増え得る。  
pytest は実行しておらず、緑は主張しない。