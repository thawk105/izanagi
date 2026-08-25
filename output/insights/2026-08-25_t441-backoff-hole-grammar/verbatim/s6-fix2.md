F1〜F13 の採用範囲を実装しました。変更は許可された4ファイルのみで、git add / commit は行っていません。

主な変更:

- C++20 pp-number を全 token 解釈し、`1e2`、`020`、`2'0` を実値で比較。`1..0` と UDL は fail-closed。
- 宣言後の `now_backoff` 出現を読み書き不問で拒否。
- 括弧付き declarator、入れ子宣言、attribute label、Unicode 空白を拒否。
- raw 4096 bytes、token 4096、nesting 256 に修正。
- raw-size preflight reject を WAL と whiteboard に記録。
- critic loader/renderer が `backoff-grammar` rule ID と専用診断を保持。
- 32形 corpus、15形合成経路、非開示、判定順、closure positive control を追加。
- `20` / `20.0` / `20.00` は引き続き受理。正準化、grammar version、既存 diffq identity は未変更。

`6935fcae` の新規期待値で訂正したもの:

- `helper(now_backoff)` の受理を `rebinding` 拒否へ変更。
- `value=100` + `1e2` の拒否を受理へ変更。実値100のため。
- `1..0` と `20_backoff` の帰属受理を `AttributionMismatch` へ変更。
- token 境界を4096/4097、nesting境界を256/257へ変更。
- `c3c5ca0a` に存在する既定期待値は変更していません。

## 総括

| Finding | 状態 | 対応 |
|---|---|---|
| F1 | closed | pp-number全体をC++20 literalとして解釈し実値比較 |
| F2 | closed | 宣言以外の全 `now_backoff` tokenを拒否 |
| F3 | closed | 撤回どおり未実装。3表記を維持 |
| F4 | closed | 括弧付き・関数ポインタ declaratorを拒否 |
| F5 | closed | 入れ子宣言とattribute付きlabelを拒否 |
| F6 | closed | separatorをspace/tab/CR/LFに限定 |
| F7 | closed | codepoint cap削除、token 4096、nesting 256 |
| F8 | closed | oversized preflightをWAL付きrejectへ変換 |
| F9 | closed | loaderでrule IDを保持し専用rendererを追加 |
| F10 | closed | 採用部分の否定assertを追加。既存hash/length面は未変更 |
| F11 | closed | 全レビューvectorの合成経路と優先順位・境界を追加 |
| F12 | closed | 32形それぞれの受理またはrule IDを逐語固定 |
| F13 | closed | 全非test orchestrator Pythonをalias込みで走査しpositive control追加 |

**実走 nodeid**

- 0件。
- 正規runnerを3回起動しましたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、`rc=16` でpytest子は未起動でした。緑とは報告しません。
- runnerが作成した3件の一時receiptディレクトリは、`output/`非書込み境界へ戻すため削除しました。workspace上では復元不能ですが、runner再試行で再生成可能な一時物です。

**実行済みの非pytest検査**

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0、既存handoff 2件の警告のみ
- `git diff --check`: rc=0
- 変更4ファイルのAST parse: 成功
- pure probe:
  - 32形 corpus: mismatch 0
  - 15形合成経路: mismatch 0
  - raw/token/nesting境界: 期待どおり
  - closure走査228ファイル: `p3_s4_loop.py::quarantine` の1点のみ

**未実走・未解決**

- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py) のpytest焦点走・全走。
- criticおよび `test_s6_sort_sweep.py` などの波及consumer test。
- build、mutation harness、全repo test。
- provenance監査は親commit後に実行すべきため未実行。
- 凍結対象 [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop_sort.py) のdocstringに旧 `_NOW_BACKOFF_RE` 名が残ります。runtime参照ではなく、編集禁止境界に従い未変更です。

**独自判断**

- literal解釈をC++20の標準整数・浮動小数・suffixに限定し、UDLと不正pp-numberを拒否。
- コメント内の数字は帰属fallbackのnumeric tokenに数えない。
- 入れ子・shadow宣言は `declaration-count.v1`、その他の宣言後出現は `rebinding.v1` に分類。
- criticへ保持するrule IDはgrammar固定allowlist内だけとし、不正値は空へ落とす。
- closure母集合をcampaign直下から全非test orchestrator Pythonへ拡大。

**静的な波及先**

- [backoff_hole_grammar.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/backoff_hole_grammar.py): validatorと数値帰属。
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/campaign/p3_s4_loop.py): attribution、preflight reject、WAL/whiteboard。
- [digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/critic/digest.py): loaderとcritic診断。
- backoffの`run_one_iteration` callerと帰属例外を検査するconsumer test。
- trigger/sortはexact marker分岐のため受理集合不変。
- `diffq-<hash>`、`byte_length`、短縮SHA、grammar version、cache/identityは不変です。