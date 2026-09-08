## must-fix

1. **must-fix — canonical stdout の期待値が実装自身を oracle にしている。**  
   [test_trial_registry.py:6823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6823) は期待値を `R._canonical_json_bytes` で生成するが、本番出力も [trial_registry.py:6611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6611) で同じ関数を使う。`sort_keys` や separator を壊しても双方が同時に変わり、この assert は緑のままになる。テスト側の `_canonical` など独立実装で比較する必要がある。  
   成果物影響: `genesis` の stdout が canonical JSON でなくなっても回帰を検出できない。

2. **must-fix — generation 不一致入力が内側の mixed-generation gate と過剰決定になっている。**  
   [test_trial_registry.py:6858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6858) は先頭 slot だけを `3` にし、残りを `2` のままにする。現在は外側の完全一致 gate [trial_registry.py:2502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2502) で落ちるが、これを除いても [trial_registry.py:2517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2517) から渡された mixed-generation genesis は、既存テスト [test_trial_registry.py:6923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6923) が示す内側の単一 generation predicate で落ちる。全 slot を一様に `3` へ変え、schedule hash も再導出すべきである。  
   成果物影響: `--prereg-generation` と一様で妥当な slot 集合の束縛を、CLI が本当に強制している証拠にならない。

3. **must-fix — strict JSON の3入力が別理由でも拒否される。**  
   [test_trial_registry.py:6877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6877) の重複-key object は必須 slot fields と generation を欠くため、寛容 decoder では [trial_registry.py:2502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2502) と slot schema [trial_registry.py:1975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1975) が拒否する。[test_trial_registry.py:6881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6881) の `[NaN]` も非-object として同じ gate に落ちる。[test_trial_registry.py:6880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6880) の `[\xff]` は UTF-8 違反に加えて、寛容な単一-byte decode 後も非引用 JSON token である。いずれも、対象 gate を通過すれば他は妥当となる入力へ再照準する必要がある。  
   成果物影響: strict decoder がなければ genesis artifact が作られる反例を構成できておらず、拒否理由の単独性を証明できない。

拒否経路の残りは次のとおり。

- 再作成は [trial_registry.py:2448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2448) の `O_EXCL` だけで拒否される。既存通常 file は前段 [trial_registry.py:1042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1042) を通過するため、これは単独である。
- top-level object は [trial_registry.py:6554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6554) の array gate で落ちる。
- 必須引数欠落は [trial_registry.py:6528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6528) の argparse gate で `main` 本体へ入る前に落ちる。

## nit

なし。

## 変異 M01〜M04 の殺され方

- **M01:** `test_genesis_cli_derives_manifest_digest_and_creates_canonical_registry` が [test_trial_registry.py:6819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6819) で赤になる。期待値は `hashlib.sha256(manifest.raw_bytes)` から独立に計算され、固定 digest との自己比較ではない。
- **M02:** 同じ正例 node が [test_trial_registry.py:6811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6811) で赤になる。fixture は generation `2` なので、定数 `1` は creator の完全一致 gate に拒否される。
- **M03:** `test_genesis_cli_requires_prereg_generation` が [test_trial_registry.py:6913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6913) で赤になる。既定値が `2` なら成功して `pytest.raises` が失敗し、それ以外なら期待した argparse 必須エラーと一致しない。
- **M04:** `test_genesis_cli_rejects_non_strict_slots_without_creating_artifact[duplicate-key]` と `[non-finite]` が [test_trial_registry.py:6896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6896) で赤になる。ただし赤になる理由は後段エラーとの文言不一致であり、上記の過剰決定がある。M04 は、全必須 fields を持つ valid slot に重複 key を置けば last-wins decoder が作成まで進めるため非等価であり、判定は「変異が等価」ではなく「テストが足りない」。

## 総括

must-fix 3件。digest 正例は固定定数 M01 を正しく殺す。一方、canonical stdout は自己 oracle、generation mismatch と strict JSON の一部は過剰決定である。

揮発値の焼き込みはない。commit hash・manifest digest・path は fixture から動的に導出され、絶対 path や時刻を期待値に固定していない。`HEAD^..HEAD` の対象2ファイル差分では既存テストの反転・緩和・skip・削除はなく、追加のみだった。自走 harness は [test_trial_registry.py:8350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:8350) で当該 file 全体を pytest 自動収集するため、node 数や file 列挙の更新は不要。実装子報告どおりテストは未実走であり、本判定は静的レビューである。