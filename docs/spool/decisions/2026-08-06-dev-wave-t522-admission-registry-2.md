---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t522-admission-registry
seq: 2
---

## {{D:pegasus-admission-registry-canonical}}. Pegasus admission の正本を data として置き、hook と checker を投影にする

**決定 (1): 正本は `tools/pegasus/admission_registry.json`。**
`hooks/guard_bash.py` の Python literal をやめ、`schema_version` + `entries` の JSON を唯一の正本とする。
hook と `tools/check_docs.py` は共有 validator (`tools/pegasus_admission_registry.py`) を通した**投影**であり、
どちらも正本ではない。値 (24 entry の `class` / `reason` / `primary_gate` / `evidence`) は移送前から
1 文字も変えない。D175 決定 1 の三値 admission と `_SANCTIONED_PATHS` の導出はそのまま維持する。

**決定 (2): 読み込み失敗はすべて空 registry へ縮退させ、module 初期化から例外を漏らさない。**
hook は Bash 呼び出しごとに新しい process として起動され、**遮断するのは rc=2 だけである**。
module 初期化で例外が漏れると process は rc=1 で死に、hook 契約上は遮断されないまま command が通る
= fail-open になる。したがって loader 呼び出しは `BaseException` (`SystemExit` / `KeyboardInterrupt` を含む)
まで捕捉し、`{}` と診断文字列へ縮退させる。`_SANCTIONED_PATHS` の導出も同じ `try` の中に置く。
返値は wrapper 側でも再検証する (plain `dict`、canonical な `tools/pegasus/` path、4 field 揃い、
非空 str、class 閉集合、非空 mapping)。validator が壊れても Pegasus 外の path が sanctioned にならない。

**決定 (3): 単調性 (D175 決定 6) の射程は正常系に限る。**
正本が読めない・schema に反する・未知 class を含むときは `tools/pegasus/` 配下を**すべて拒否する**。
このとき現在 `local-ok` の 5 本も落ちる。これは受理集合の縮小であり D175 決定 6 の例外だが、
規律 2 の下で fail-open は選択肢にならないため、**意図した fail-closed** として明示的に採る。
非 Pegasus の sanctioned 2 本 (`tools/run_tests.py` / `tools/check_ai_provenance.py`) は影響を受けない。

**決定 (4): loader は import machinery を使わず source bytes を `compile` / `exec` する。**
`spec_from_file_location` + `SourceFileLoader` は `__pycache__` を読み得るため、review した source と
実行されるコードが一致しない窓がある。hook と checker の両方で exact source bytes を読んで実行する。
ファイル読み取りは `O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC` + fd に対する `fstat` の regular 判定と
1 MiB cap で行う (`O_NONBLOCK` が無いと writer のいない FIFO で hook が止まる)。

**決定 (5): docs との同期検査は class と evidence に限り、射程を明記する。**
`check_docs.py` は runbook §7.0 の 24 行投影表、`unknown` 表の grandfather 明示、実測表の path 集合、
`tools/pegasus/README.md` の実行体宣言表と site タグ付き block を正本と照合する。
**`reason` / `primary_gate` の散文は投影しない** (裁定へ返した)。この検査は class の正しさ、資源の実測、
hook が `.claude/settings.json` へ実配線されていること、parser が実行 target と認識しない綴り
(`python3 -c`、cwd 相対、未解析 launcher) のいずれも保証しない。

**決定 (6): 未実測 4 本は grandfather を追認したまま据え置く。**
2026-08-05 のユーザー裁定に従い、`class` は `local-ok`、`evidence` は `legacy-admitted (未実測)` を維持する。
実測で変わるのは evidence であって class ではない。この例外は当該 4 本限りで、他 entry の許可根拠に
流用しない。

**却下した選択肢:**
- **loader を deadline 付き子プロセスで監督する** — 無限ループ耐性は上がるが、hook 本体が無限ループする
  risk と同種であり、Bash 呼び出しごとに process を 1 つ増やすコストに見合わない。限界として記録する。
- **canonical bytes の SHA-256 を test へ pin する** — 生成物から採った hash を期待値へ焼き込む形になり
  (F27 型)、不一致時に「hash を更新して通す」誘惑を作る。代わりに 24 entry × 4 field を独立 literal golden とした。
- **production validator に「ちょうど 24 entry」を要求する** — 合成 fixture の都合で validator を
  弱める圧力を生む。件数と class 内訳の固定は test 側の独立 golden に置く。
- **README の command 行を解析して実行 site を推定する** — 同じ手順を inline code や平文へ移すだけで
  検査を逃げられる。宣言表 + site タグ付き block へ置き換えた。
- **同一 inode の read 中書き換えの照合** — 更新側を atomic rename に限る運用契約で扱い、検査は入れない。

**射程 (この決定が保証しないこと):**
- 保証するのは「正しく `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` と判定され、現行 parser が実行 target と
  認識した綴り」の受理・拒否だけである。F121 の残穴 ([T-518]) は閉じていない。
- 平文 (fence の外) の手順、basename だけの言及、変数で組み立てた path は site 一致を検査できない。
- 研究成果物 (certified 選択、proof chain、凍結 bytes、3 台帳) は不変である。変わるのは開発 harness の
  Bash 面だけである。
