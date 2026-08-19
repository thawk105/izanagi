結論先行: 現プランは「production から identifier を1件削除し、frozen literal を不変にする」変異には有効です。ただし、scanner 実装の意味的破壊と、test literal の協調改変には残余があります。pytest は要求どおり未実行です。

### 1. 自己参照

- file:line: `s2-plan-output.md:49-61,104-109`、production 側は `coder_effect_gate.py:126-132`
- real/refuted 見込み: 設計意図は refuted（独立 literal を明記）。しかし実装拘束としては real。
- 反証: `_FROZEN_DENY_IDENTIFIERS` はまだ未実装で、author が次のように楽をしても既存 plan のテスト形状だけでは検知できない。

  ```python
  _FROZEN_DENY_IDENTIFIERS = {
      rule.category: frozenset(rule.identifiers)
      for rule in DENY_TABLE
  }
  ```

  production の削除と同時に baseline も縮むため、検査は緑になる。`Final` も runtime freeze ではない。

- 修正案: `test_coder_effect_gate.py:67` の RHS を全96件の文字列 literal に限定し、`test_coder_effect_gate.py:91` 付近へ RHS の AST 形状検査を追加する。`DENY_TABLE`、`effect_gate`、`_IDENTIFIER_RULE` の `Name`/`Attribute` 参照や comprehension を拒否する。

### 2. カバレッジの数学

- file:line: `coder_effect_gate.py:63,73,84,96,103`、既存テストは `test_coder_effect_gate.py:25-34,67-88,91-109`
- real/refuted 見込み: refuted。plan §5 の5候補はすべて実在し、既存の positive probe には直接現れない。

  - `fork` → process-shell
  - `fopen` → file-stdio
  - `socket` → network
  - `pthread_create` → sleep-block-thread
  - `syscall` → escape-hatch

  件数も `18 + 35 + 18 + 18 + 7 = 96` で正しい。`socket` と `syscall` は `test_coder_effect_gate.py:59` のコメント内に出るだけで、検出陽性試験ではない。

- 反証対象: plan §5 `:90-100`、brief `:38-42` の「代表外 identifier は旧テストを通過する」という評価。
- 修正案: なし。旧テストの SURVIVED/KILLED は未実走だが、ソース上の被覆関係は正しい。

### 3. superset 判定の穴

- file:line: `coder_effect_gate.py:126-132,576-605`、`test_coder_effect_gate.py:78-98`
- real/refuted 見込み: real。
- 反証: 新検査は `DENY_TABLE` の構造しか見ず、`_IDENTIFIER_RULE` と tokenizer の実動作を見ない。

  単純に mapping を1件削る変異は `coder_effect_gate.py:131` の件数検査で殺される。しかし、例えば `fork` だけ別カテゴリの rule value に差し替える、または `scan_host_effects:595` の lookup を `fork` のときだけ未登録キーにする変異は、辞書長を保ったまま成立する。既存の5代表 probeと frozen superset はともに緑になる。

- 修正案: 新検査の直後 (`test_coder_effect_gate.py:91` 付近) で、frozen の全 identifier に対し `scan_host_effects(f"{identifier}();")` を実行し、期待 category（および可能なら frozen rule ID）を確認する。最低限でも §5 の5候補には semantic positive probe を追加する。

### 4. 粗い文字列変異は scope 外か

- file:line: `tools/mutation_harness.py:567-588,990-992,1021-1053,2040-2056`
- real/refuted 見込み: real、かつ scope 内。
- 反証: harness は `replacements` を複数受け付け、複数 file を収集・累積適用・書戻しする。AST限定の強制はない。実績でも `t396.m6` は3ファイル同時変異で、`mutation-spec.json:117,120,125,130`、`README.md:76-83` に記録され、実際に `SURVIVED` している（`mutation-out.json:322-348`）。
- 反証対象: plan §6 `:108` および §5 `:90` の「production の対象だけを変異し frozen literal は不変」という運用前提。
- 修正案: 段6で、production の identifier 削除、test 側 frozen literal 削除、`96`→`95` の3 replacementを同一 mutation として事前登録する。現行案なら `SURVIVED` になるため、hash 防御を追加した後に `KILLED` を要求する。この mutation を out-of-scope 扱いしてはならない。

### 5. frozen literal の改ざん耐性

- file:line: `s2-plan-output.md:104-109`、planned insertion `test_coder_effect_gate.py:67,91`
- real/refuted 見込み: real。
- 反証: `96` の総数 assertionも author が `95` に変更でき、`Final` は編集抑止にならない。frozen literal を production に合わせて黙って縮めても検知機構はない。
- 修正案: `test_coder_effect_gate.py:67` に、category/identifier の正規化表に対する SHA-256 literal と総数を固定し、`:91` で両方を検証する。併せて `docs/decisions.md:23000` 付近の新規 T-1357 記録へ件数・hash・更新条件を記録する。これは協調改変への完全な暗号的防御ではないため、上記の cross-file mutation を受入条件にする。

### 6. brief P2 の履歴検算

- file:line: `s1-brief.md:22-29`、現行 `test_coder_effect_gate.py:151-171`
- real/refuted 見込み: brief の訂正は正しい（誤りは refuted）。
- `git show dc87fff7^` では、151-162 に `test_ordinary_for_range_for_and_data_dependent_loops_pass` が存在する。`git show dc87fff7` はその decorator と関数を削除している。現行151は `test_explicit_unconditional_loop_headers_are_rejected` の decoratorで、関数本体は171。
- `dc87fff7` は現 HEAD の ancestor でもあり、brief の主張に修正は不要。

## 裁定パッケージ候補

- T-1357を「table 構造の縮小検出」に限定し、scanner semantic coverageを別件にするか、全96 identifier probeを本waveへ含めるか。
- 同一リポジトリ内の test literal を完全な authority と見なせないため、hash＋cross-file mutation＋decisions記録を最低防御とするか、外部 baseline pin を別裁定にするか。

## 総括

判定: 条件付きで持つ。  
単一 identifier 削除に対しては、独立 frozen superset が有効。  
ただし scanner の実動作破壊と、frozen literal・件数の協調改変は現案で緑になり得る。  
semantic probe、hash、cross-file mutationを追加して初めて、限定された reward hack 耐性を主張できる。