---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t945-resume-mode
seq: 1
---

## {{D:startup-resume-mode-is-conditioned-fresh}}. 起動 gate の再開 mode は「点 1 だけを包含条件へ置換した fresh」とする

**決定:** `tools/check_wave_startup.py --mode resume` は、fresh の点 1 (`HEAD == local main`) を
「local main を包含し 0 commit 遅れ」へ置換したものとし、それ以外の検査 (作業 branch、進行中
操作なし、clean tree、submodule marker、handoff) は mode に依存せず共通尾部で必ず呼ぶ。
未知 mode は CLI の `choices` と Python API の双方で fail-closed とし、既定は `fresh` のまま
維持する。環境変数・設定ファイルから mode を読む経路は作らない。

**理由:**
- 再開 wave は自 wave commit を持つため、点 1 は構造的に必ず非 0 になる。NG 文面は「local main と
  同じ commit から fresh worktree を作り直す」と誘導するので、文面どおり従うと未 land の作業を捨てる。
- 既存の resume は条件を持たず、点 1 だけでなく branch と clean tree も無条件に素通ししていた。
  これは fail-closed gate の中に bypass mode を置くのと同じで、遅れた worktree・汚れた木でも緑を
  返す。worktree の `docs/` は基準 commit の凍結写しなので、遅れたまま起動した wave は古い裁定を
  正本として台帳を書く (F67)。
- 「包含し 0 遅れ」は `rev-list --count HEAD..refs/heads/main == 0` の 1 本で測れる。包含と 0 遅れは
  同値であり、ahead は自 wave commit として無制限に許してよい。

**却下した選択肢:**
- 手順書側で「再開時は点 1 を除く」と書く — 機械が受理集合を持たないため、除外の範囲が
  読み手ごとにぶれる。gate が保証しない事実を手順の文で保証したことにしてしまう。
- 現状維持 (再開のたびに親が個別判断) — 起動 gate の受理集合が人間の判断に依存し、
  fail-closed である意味が失われる。
- 3 番目の緩い mode を新設して既存 resume を残す — bypass mode が残るので目的を達しない。

## {{D:startup-gate-containment-is-raw-graph}}. 包含判定は raw commit graph 上で行い、偽装 3 経路を封鎖する

**決定:** 包含検査は replace ref を無効化した raw commit graph 上で行う。具体的には
(a) checker が起動する全 git へ `GIT_NO_REPLACE_OBJECTS=1` を固定し、(b) git common directory へ
自分で `info/grafts` を連結した path を `lstat` して legacy graft の存在を拒否し、
(c) `refs/heads/main` が symbolic ref なら拒否する。(c) は **mode 共通**で呼ぶ。
`rev-list` の rc≠0、空、非 ASCII 十進、符号付き、複数 token はすべて fail-closed で拒否し、
受理は `"0"` の完全一致だけとする。

**理由:**
- replace ref と legacy graft はどちらも親子関係を差し替えられるため、実際には分岐している HEAD に
  main を祖先として見せ、包含 count を 0 にできる。受理集合を広げる gate を新設する以上、
  その gate 自身を騙せる経路を残さない。
- `git rev-parse --git-path info/grafts` は終端 symlink を解決した path を返すので、
  `--git-path` の結果だけを `lstat` すると dangling symlink を検出できない。common directory から
  自分で連結すれば、解決させずに存在を判定できる。
- symbolic ref による偽装は包含だけでなく **fresh の等式検査も同じ OID を返して通す**。
  片方の mode だけ塞ぐと、攻撃者は塞がれていない mode を使えばよく、新設した保証が成立しない。
- 可視化 (`describe_main_divergence`) は「失敗しても受理集合を変えない」と自ら宣言している。
  gate がその戻り値や出力文字列を根拠にすると宣言と実装が食い違うため、gate は独立に git を
  実行し、可視化の例外は診断文字列へ落として gate を必ず走らせる。

**却下した選択肢:**
- 既定の git semantics (replace overlay 有効) を包含の意味とする — overlay は利用者が任意に
  差し込めるので、gate の意味が repository の設定次第で変わる。
- graft を「読める内容を持つ場合だけ」拒否する — 判定が git の内部挙動に依存し、
  dangling と有効の境界を checker 側で再現し続ける保守負債になる。
- `--repo` と期待 worktree の束縛、wave identity の認証まで本 mode で行う — checker の契約変更に
  なるため別裁定とし、本 wave では `--help` と `OK:` 行へ「認証しない」と明記するに留める。
