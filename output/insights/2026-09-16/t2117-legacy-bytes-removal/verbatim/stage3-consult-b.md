## 所見 1 — 親 brief の P1-c は一般化しすぎている

- **主張:** `benchmark_snapshots` を使わないことだけでは登録不要と判定できないが、plan の採用構成では更新不要という結論を支持できる。
- **根拠:** `brief.md:74–84,99–100`。`orchestrator/tests/test_real_repo_serialization.py:1432–1471` は、登録済み node を seed とする **他の session/module fixture も含めた** consumer 閉包を要求する。一方、`plan.md:133–146` は共有資源・共有 fixture を使わない構成に限定している。
- **壊れる具体例:** `benchmark_snapshots` を使わず、登録済み consumer と同じ `real_known_axes_doc[module]` を使う新 node → brief の一般則では登録不要になるが、閉包検査では登録漏れになる。今回の function scope の `tmp_path`・`monkeypatch` 構成には該当しない。
- **重大度:** nit。brief の説明の問題であり、plan の阻害要因ではない。

## 所見 2 — 観測 wrapper には generator を消費する実装上の落とし穴がある

- **主張:** route B の patch 観測を単純に追加すると、実関数へ渡す入力を空にして正例を壊しうる。
- **根拠:** `plan.md:31,36` は patch 順序の観測を要求する。`tools/codex_reasoning_ab.py:965–976` が渡すのは list ではなく generator で、同 `:901` がこれを消費する。
- **壊れる具体例:** wrapper が `recorded = list(patches)` の後に `original(files, patches, **kwargs)` を呼ぶ → author/fix1 が適用されず route B は `base` のまま → 正例で mismatch。観測用に実体化した列を実関数にも渡せば回避できる。
- **重大度:** nit。plan はこの誤実装を指定しておらず、確定した欠陥ではない。新設検査は不要。

## 裁定照合 — m2 合成化を禁止する逐語は確認できない

- **主張:** D1367・D1382・D1615・[T-2117] と、plan の各変更との衝突は確認できない。
- **根拠:**
  - `rulings-verbatim.md:31–34`：D1367 の名前実在 guard と自己検査を、plan `:22` は維持する。
  - 同 `:69–87`：D1382 は **m2 を名指ししておらず**、「歴史 anchor そのもの」が m2 であるとも書いていない。
  - 同 `:95–102`：D1615 のコード変更制限は「合成不能な検査を terminal と扱うとき」という条件下の指示であり、具体対象は source-bound node。一般的な terminal 処理の規律ではあるが、m2 の合成復帰まで禁止するとは読めない。
  - 同 `:5–7`：[T-2117] は常時実行 node への移行を要求するが、新しい関数名や旧関数の削除は要求しない。既存 m2 を常時実行へ改修する plan `:13–20` はこの条件を満たす。
- **壊れる具体例:** source-bound 関数へ静的 skip を追加 → 消失に依存しない digest・台帳 assert も停止する。これは D1615 違反だが、plan は当該関数を変更しない。
- **重大度:** nit（確認事項）。裁定違反の所見なし。

## 登録簿・collection — plan §4 を覆す機械的原因は確認できない

- **主張:** 提案された入力構成と node 名では、登録簿・xdist・所要台帳による必然的な失敗は静的読解から導けない。
- **根拠:** `orchestrator/tests/conftest.py:260` の inventory は手書き集合。同 `:642–655` の完全一致は分類集合間の検査であり、全収集 node との一致ではない。同 `:2144–2152` は登録済み node に marker を付ける。所要時間が未登録なら同 `:1675–1695,1740–1743` は未知として扱う。`orchestrator/tests/growth_test_holds.py:745–756` も既存 held 関数の存在検査であり、新関数を禁止しない。
- **壊れる具体例:** inventory だけへ新 node を追加し分類集合を更新しない → import 時に `RuntimeError`。plan はどちらも変更しないため、この失敗を導入しない。新負例名の既存定義も検索では見つからなかった。
- **重大度:** nit（確認事項）。実走結果ではなく、調べた条件に失敗原因がないという判断。

## helper — 実在し、auxiliary の差替えも可能

- **主張:** plan の helper 参照は正確で、`_synthetic_task_manifest` は auxiliary の後置差替えを妨げない。
- **根拠:** `orchestrator/tests/test_codex_reasoning_ab.py:6581–6599` は manifest 全体を deepcopy してから `tasks` を置換するため、`shared_provenance.auxiliary_sessions` はコピー内に残る。同 `:8926–8934` にその差替えの既存例もある。rollout writer は `:836`、一時 repo 作成は `:2417–2454`、commit 定数差替えは `:2461–2462` に存在する。production の auxiliary 検証は `tools/codex_reasoning_ab.py:2750–2764`。
- **壊れる具体例:** helper の戻り値を未変更のまま合成 sessions root に渡す → 歴史 session を探索して失敗する。ただし plan `:125` は三つの auxiliary pin の差替えを明示している。
- **重大度:** nit（確認事項）。helper 不適合の所見なし。

## scope と撤去残り — source-bound の条件付き照合は今回の撤去対象ではない

- **主張:** plan に要求外の gate・台帳・一般化の新設はなく、残る source-bound の歴史 bytes 照合は D1615 による維持対象である。
- **根拠:** `plan.md:26–64,160–172` の専用 helper・負例・変異候補は二経路の到達と不一致拒否に直接対応する。`orchestrator/tests/test_codex_reasoning_ab.py:9158–9168` の現存 rollout 照合は条件付きで、同 `:9163,9169–9175` の常時実行 assert と併存する。
- **壊れる具体例:** 「歴史 bytes 照合が残る」という理由で source-bound 関数まで撤去 → D1615 の維持指示に反し、常時実行の検査も失う。plan はこれを行わない。
- **重大度:** scope 外。source-bound の再設計へ広げる根拠はない。

## 総括

最も重い指摘は、親 brief の P1-c が登録不要条件を一般化しすぎている点（nit）。
plan §4 は既に必要な限定を加えており、採用してよい。
blocker / must-fix に相当する裁定衝突・必然的な受入失敗は確認できなかった。
以上は静的読解のみで、pytest・変異の実走やファイル変更は行っていない。