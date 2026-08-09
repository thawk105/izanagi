実装は完了しました。編集したのは指定された [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:242) と [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2397) だけです。docs 編集・stage・commit は行っていません。

### 実装前の受理・拒否挙動

実装前は次の状態でした。

- 段 dispatch は pair の平坦集合だけを検査し、`U/C`、trigger、edge 所有者を保持しない。
- allowlist 済み bare path、mode 欠落・未知値・retype を受理し得る。
- 4 file cap と合計 25,200 bytes を拒否条件とし、L1/L1.5/L2 は未計測。
- pair 差、allowlist 外 path、登録節の欠落・孤児、UTF-8・symlink・非 regular file は拒否。
- 親の先行編集に対する赤は指定された `DW-CTX` / `DW-O04` の2件だけでした。

### 実装内容

- parser 出力を `(owner, mode, path, section)` の edge 集合へ変更。
- typed U/C map、flatten view、層分類を edge から導出。
- 凡例・段表 header、mode、condition trigger を exact 検査。
- 各行の path 集合と pair path 集合を束縛し、bare path を拒否。
- self doc の exact `の全節` だけを `_SELF_SECTIONS` へ展開。
- 可視 H2 offset で raw byte slice を作成し、分類被覆と可視 H2↔slice 1:1 を併設。
- L1=10,625、L1.5=9,566、L2単節=1,000 bytes に置換。
- file cap、aggregate、cap-sum 検査を削除。ただし4冊の読取・UTF-8・regular file・symlink・再帰 registry 閉包は維持。
- L2-only file は fail-closed。
- `DW-CTX` と `DW-O04` の3 edge共有を保持。
- M1〜M12 の KILL node、self全節・共有edge・DW-O20+154の正例、F42 meta-testを追加。
- `PROVENANCE_REFERENCE_LIMITS` family は未変更。

### 検査結果

実走済み:

- `python3 -B tools/check_docs.py` — rc=0、`違反なし`
- `python3 tools/check_codex_agents.py` — rc=0
- `git diff --check` — rc=0
- `py_compile` — rc=0
- in-memory adversarial probe — mode欠落・未知値・bare path・trigger変更を検出、fence/comment/raw HTMLを不可視化、malformed H2は1:1 findingだけで検出
- 実測再現 — L1 10,625/15、L1.5 9,566/20、L2 5,008/13、最大 DW-O09=935
- 共有 edge — `DW-CTX` 3件、`DW-O04` 3件を確認

pytest は実装済み・未実走です。以下を runner 経由で試しましたが、いずれもテスト本体の起動前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。

- 新規 node群＋F42 meta-test の焦点範囲
- `test_synthetic_repo_baseline_clean` 単独
- `orchestrator/tests/test_check_docs.py -x -q` 全体

したがって、pytest の緑や所見の `closed` は主張しません。

### 静的な波及先

- caller: `main()` → `_check_command_docs_guard()`、`tools/check_docs.py` を呼ぶCI・受入経路。
- 共有 fixture: `_build_min_repo()`、`_write_command_guard_docs()`、command-guard matrix、living-doc victim 選定。
- consumer test: operation contract pin、dispatch positive controls、reference inventory、synthetic baseline。
- live Python consumer は指定どおり production と当該 test の2本だけです。

### 本 wave の限界

表外自然言語による条件性変更、event加重読量、外部 supervisor の実 `DW-CTX` 結線、新規L2 admission controlは未解決のままです。

## 総括

- 狭まる方向: L1/L1.5超過、L2単節超過、mode/trigger/header drift、bare path、H2 parser不一致を新たに拒否。
- 広がる方向: L2各節≤1,000なら旧file cap・25,200合計超過を受理し、DW-O20 489+154も受理。
- UTF-8・regular file・symlink・registry閉包とself allowlistは維持。
- checker、agent検査、構文、差分衛生、in-memory probeは緑。
- pytestとF42 meta-testはrunner rc=16のため実装済み・未実走。
- docs編集・commit・stageは行っていない。