## 環境依存

- 所見: repo root を `cwd` にした `sys.executable -c` は、受入時に `PYTHONPATH` が未設定でも `orchestrator` を import できる。`-c` の先頭 import path が `cwd` になるためで、同じ方式の既存テストもある。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:38,1619-1621`、`orchestrator/tests/test_s8c_preregistration_predicates.py:2941-2962` / 成果物への影響: 標準の受入起動形では import error による偽赤は生じない。 / 直し方: 不要。

- 所見: `timeout=30` は共有 login node の既知の高負荷条件に対して余裕が不足する。repo 内の subprocess collection 先例は 120 秒である。 / real か refuted か: **real** / must-fix か nit か: **must-fix** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1618-1625`、`orchestrator/tests/test_pytest_collection_config.py:141-152` / 成果物への影響: verifier の report bytes は変わらないが、正しい実装が負荷だけで受入偽赤となり、commit を受理できなくなる。 / 直し方: 各 subprocess の timeout を **120 秒**へ上げる。健全時の所要時間は変わらず、真の hang の検出は最大 90 秒遅くなる。

- 所見: `check=True` と stderr capture の組合せでは、子が非ゼロ終了した際に `CalledProcessError.__str__` が stderr を表示しない。素の runner も例外名と文字列しか出さない。 / real か refuted か: **real** / must-fix か nit か: **must-fix** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1622-1626,2863-2867` / 成果物への影響: 受入が赤になっても import failure、verifier failure、環境異常を判別できず、検査結果の運用上の実効性が失われる。 / 直し方: `check=False` で受け、`returncode == 0` を seed、rc、stdout、stderr の bounded tail 付きで assert する。`TimeoutExpired` も捕捉し、保持されている stderr を assertion message に含める。

- 所見: subprocess が非ゼロ終了または timeout になった経路でも一時 trace directory は `finally` で削除される。`subprocess.run` は timeout 時に子を killして待ってから例外を送出し、`workers=1` なので残存 worker もない。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1602,1607,1612-1646` / 成果物への影響: subprocess failure による一時 trace の通常の残留はない。 / 直し方: 不要。

## 収集と meta-test

- 所見: 素の runner は `globals()` 中の全 callable `test_*` を動的収集するため、新テストも自動的に対象になる。固定件数は持たない。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:2851-2874`、`orchestrator/tests/test_plain_runner_coverage.py:60-74` / 成果物への影響: 素の自走から新テストだけが漏れることはない。 / 直し方: 不要。

- 所見: 新 node は real-repo、growth hold、flaky hold、slow、serial のいずれにも分類されない通常 node である。conftest の verifier inventory にあるのは共有 CCBench を読む別の既存 node だけで、新テストには decorator もない。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/conftest.py:259-263,2032-2071`、`orchestrator/tests/test_verifier.py:1592` / 成果物への影響: 不要な real-repo lock、skip、直列群への混入はない。 / 直し方: 不要。

- 所見: repo に global なテスト関数名・件数の固定 meta-test はない。名指しで影響を確認した `test_real_silo_node_always_verifies_tracked_fixture_without_skip` は既存 3 関数だけ、`test_real_repo_group_collection_exactly_matches_canonical_nodes` は real-repo marker 集合だけ、`test_every_test_file_is_self_runnable_or_allowlisted` は file 単位だけを検査する。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_skip_classification.py:327-354`、`orchestrator/tests/test_real_repo_serialization.py:1506-1526`、`orchestrator/tests/test_plain_runner_coverage.py:60-74` / 成果物への影響: 新しい通常 nodeid が exact inventory を崩す検査はない。 / 直し方: 不要。

- 所見: 受入所要時間台帳を変更しない裁定は算術上成立する。台帳は 20,042 node、90% gate が許す最大分母は 22,268 nodeである。親の約 21,866 nodeを基準に新 nodeを足しても `20042 / 21867 = 91.6541%` で、約 1.65 point の余裕が残る。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/acceptance_duration_ledger.json:20046-20048`、`orchestrator/tests/test_acceptance_schedule_order.py:660-713`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:87-97` / 成果物への影響: 新 node 1 件だけで台帳被覆 gate が赤になることはない。 / 直し方: 裁定どおり本 wave では台帳を変更しない。

## 変異登録の妥当性

- 所見: M1からM3を `KILLED` でなく `diagnostic sensitivity pin` とする区分は契約どおりである。いずれも受理集合、cycle 検出、fail-closed 挙動を変えず、構造化理由列の順序だけを変える。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `docs/dev-wave/mutation.md:16-20,55-64`、`orchestrator/verifier/dsg.py:517-546` / 成果物への影響: 診断順序の赤を correctness kill と過大計上しない。 / 直し方: 現行登録を維持する。

- 所見: M1 の期待失敗 nodeを新テストただ1件とする完全集合は、静的には妥当である。既存の順序完全一致テストを全件確認すると、`test_broken_silo_norw_fixture_contract` と structured report golden は各辺に WW が最大1件、parallel witness order テストは WR/RW のみ、version-dup テストは WR 1件である。real Silo combination テストは理由順を集合化している。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1749-1816,1819-1989,2077-2098,2635-2647,2705-2711` / 成果物への影響: M1 の失敗集合に既存 nodeが追加され、事前登録の完全一致が崩れる静的経路は見当たらない。 / 直し方: 段6で登録どおり実測確認する。ここでは緑とは報告しない。

- 所見: M2 は降順が昇順期待に反するため確実に赤になる。M3 は全キーの sort key が同じ `(u.commit, v.commit) = ((1,1),(1,2))` となり、Python の stable sort が入力 set intersection の順序を温存する。親が固定 seed 1 と777で異なる set 順を既に観測しているため、bytes 一致と昇順 assertの双方に検出力がある。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1595-1601,1614-1638`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:24-31,105-110` / 成果物への影響: M2/M3 が生存して diagnostic pin が空文化する懸念はない。 / 直し方: 不要。

- 所見: DW-M01 の単一理由性も成立する。M1/M3 は最初の report bytes 一致で止まり、M2 は昇順理由列で止まるが、意味上はいずれも同じ「WW key順契約の破れ」である。前後の受理判定や内側の edge 集合は変わらない。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `docs/dev-wave/mutation.md:5-10`、`orchestrator/tests/test_verifier.py:1628-1643`、`orchestrator/verifier/dsg.py:523-546` / 成果物への影響: 一つの変異を複数の独立 gate が過剰決定した証拠にはならない。 / 直し方: 不要。

## 下流への波及

- 所見: 理由順の変更は JSON renderer、text renderer、critic の表示順へ実際に伝播する。ただし全経路が入力順をそのまま保持するだけで、再整列や先頭理由だけを意味論として採用する処理はない。 / real か refuted か: **real** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/verifier/report.py:26-32,144-154`、`orchestrator/critic/digest.py:784-815,1289-1305,1380-1386` / 成果物への影響: 多重 WW anomaly の JSON、text、critic 表示が key昇順へ安定化するが、verdictや理由集合は変わらない。 / 直し方: 変更目的どおりなので不要。

- 所見: campaign consumer の意味論破壊はない。reflux は理由を全件検証し、types を理由の初出順から再導出するが、WW 群内の key並替えでは types は変わらない。witness digest は理由順を含むため新しい多重 WW reportでは変わるが、embedded anomalyから同じ方法で再計算される。mocc discriminator は RW-only edgeだけを対象にするため WW順は到達前提外である。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/campaign/reflux_result_evidence.py:324-407,592-612`、`orchestrator/campaign/reflux_formal_consumer.py:1248-1264`、`orchestrator/campaign/mocc_g2_discriminator.py:548-580` / 成果物への影響: 既存の受理・拒否分類は変わらず、新規多重 WW witness の constraint digestだけが決定的な値になる。 / 直し方: 不要。

- 所見: 追跡下凍結成果物の再発行不要という裁定は妥当である。独立の tracked `output` scanでも、多重 `ww key=` 行および JSON の WW reasonを含む成果物は0件だった。順序不変と bytes不変が同値になる条件は、他フィールドと encoder設定が同一、serializerが配列順を保持、並べ替える要素の serialized valueが相異なることである。ここでは reason dictが keyで相異なり、`sort_keys=True` は object keyだけを整列して配列を整列しないため条件を満たす。 / real か refuted か: **refuted** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/verifier/report.py:17-32`、`orchestrator/tests/test_verifier.py:1604-1609`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:46-51` / 成果物への影響: 現在追跡されている凍結成果物の bytesは変わらない。 / 直し方: 再発行不要。

## 残る限界

- 所見: 親が挙げた「CPython 3.10.12、固定入力、seed 2本に限る」と「workers=1に限る」は正しく、必須の限界である。 / real か refuted か: **real** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1595-1607,1614-1617`、`output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md:139-145` / 成果物への影響: 将来のPython実装、別key集合、worker数間の同一性まで保証したと誤読すると保証範囲を過大表示する。 / 直し方: 裁定文どおり明記する。

- 所見: この2点だけでは直接検査した出力 surface の限界が抜ける。新テストが直接比較するのは compact JSON bytesだけで、`render_text`、critic表示、`witness_class_sha256` は共有 `reasons` 順からの派生保証であり、個別のcross-process比較はしていない。 / real か refuted か: **real** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1604-1609,1628-1638`、`orchestrator/verifier/report.py:144-154`、`orchestrator/campaign/reflux_result_evidence.py:406-407` / 成果物への影響: 現行実装のbytesには問題ないが、テストが各rendererやconsumerを直接保証しているとの過大な説明になる。 / 直し方: 「直接 pin するのは JSON report と WW理由列。text表示と下流digestは同じ理由列を使うことからの派生保証」と記録する。新規テスト追加は不要。

- 所見: 子の import 保証も標準の非isolated `python -c` と repo-root `cwd` に限られる点を明記すると境界が閉じる。 / real か refuted か: **real** / must-fix か nit か: **nit** / 根拠の file:line: `orchestrator/tests/test_verifier.py:1615-1621`、`tools/run_tests.py:1255-1262` / 成果物への影響: 現行受入には影響しないが、将来isolated起動へ変えた場合まで import保証があるとの誤読を防ぐ。 / 直し方: 「現行 `tools/run_tests.py` の標準起動環境に対する保証」と限界に1句加える。

## 総括

静的レビューでは、実装・変異登録・収集分類・台帳被覆率・下流consumer・凍結成果物に correctness 上の穴は見つからなかった。一方、受入運用上の **must-fix は2件**ある。

1. subprocess timeoutを30秒から120秒へ引き上げる。
2. 非ゼロ終了とtimeout時に stderrを必ず assertionへ載せる。

pytestや自走 harnessは実行していないため、緑とは報告しない。