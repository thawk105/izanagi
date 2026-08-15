---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1128-floor-same-root
seq: 2
---

## {{D:floor-shared-fetchcontent-base}}. 床値の oracle と build を job-local な FetchContent base で同一 tree へ束縛する

**決定:** 床値の `sort_best` cell について、job 一意な `$TMPDIR` 配下に canonical な
FetchContent base を 1 個作り、依存の prebuild と cell build が同じ `<base>/masstree-src` を
使う。oracle の `dependency_root` はその root へ明示束縛する。
`FETCHCONTENT_SOURCE_DIR_*` は渡さない。base 注入は `sort_best` cell に限定し、
非 sort cell の cache identity と binary 参照を変えない。

**理由:**

- oracle が要求しているのは pin された source ではなく build 済み masstree
  (`config.h` と archive) であり、これは pin ではなく build 順序の問題である (D413)。
  oracle は build より前に走るので、oracle 実行前に masstree だけを build する段が要る。
- build を共有 cache tree へ寄せる案は `FETCHCONTENT_SOURCE_DIR_*` の配線を要し、
  ユーザー裁定 (該当項目は「実装しない」) に反する。したがって oracle を build 側へ寄せる。
- `FETCHCONTENT_BASE_DIR` は FetchContent の repository と SHA pin を迂回せず、
  source / build / subbuild の親だけを変える。外部 source を権威として差し込む
  `FETCHCONTENT_SOURCE_DIR_*` とは機構が異なる。
- cell ごとの build dir 配下 `_deps` を oracle root にする案は不成立である。
  v2 の fresh configure は nonce staging で行われ、staging は build 後に削除されるため、
  oracle 実行時点で存在せず、build 後には残らない。

**却下した選択肢:**

- **共有 third-party cache を oracle 依存の root として使い続ける** — その tree に
  `config.h` が存在したのは過去の build の生成物で汚染されていたからであり (F319)、
  clean な cache では oracle が UNAVAILABLE になる。入口を残すと同じ穴を作り直す。
- **共有 (非 job-local) な base を使う** — 複数 job が同じ `_deps` で masstree の
  in-source build を同時に走らせる危険がある。job-local なら `mkdtemp` の時点で排他が成立する。
- **base を全 cell へ渡す** — 非 sort cell 10 件の cache identity と binary 参照が
  job ごとに変わる。今回の欠陥は `sort_best` の oracle と build の不一致であり、
  非 sort cell に oracle は無い。

## {{D:dependency-identity-authority-is-content}}. 依存 tree の同一性は内容で主張し、実効 root を build 自身の成果物から検証する

**決定:** masstree 依存の同一性の権威を **内容** (HEAD + `config.h` sha256 + archive sha256) に置く。
`st_dev` / `st_ino` は診断として記録するだけで、一致を必須条件にしない。
build が実際に使った masstree source root は **build 自身の成果物 (`CMakeCache.txt`) から
読み取って**期待値と照合する。configure argv の文字列検査は補助であって合格の根拠にしない。
依存 receipt を v2 build identity の preimage へ入れ、completion を publish する前に
**実効 root から**内容を取り直して入力 receipt と比較する。

**理由:**

- 実効値を見る検査 1 本は、環境変数を個別に禁止する検査の集合を包含する。
  ambient な CMake toolchain から source root を差し替える経路があるため、
  argv に禁止 token が無いことは「build が期待した tree を使った」ことを証明しない。
- 内容が同一なら再 populate が起きても証拠は成立する。inode 一致を必須にすると、
  内容が同じでも停止する過剰拒否になる。逆に inode が同じでも archive が差し替われば
  検出できないので、内容照合が必須である。
- base path を cache identity へ入れると job ごとに必ず cache miss する一方、
  base path は中身を証明しない。内容 receipt を入れれば
  「別の masstree で作った binary が cache hit する」経路が閉じる。
- publish 前の照合を期待 base に対して行うと、実効 root が期待外の build でも
  completion が publish され、次回の cache hit で受理されうる。
  **fresh で拒否したものが cache 経由で通る**という合成欠陥になる。

**却下した選択肢:**

- **ambient な `CMAKE_TOOLCHAIN_FILE` を拒否または hash 固定する** — 実効 root の照合が
  それを包含する。環境変数の有無で受理集合を不必要に縮めない。
- **cache hit でも絶対 root の再一致を要求する** — 内容が同じでも job が変わるだけで拒否され、
  2 回目以降の本番走で `sort_best` の受理集合が空になる。
- **依存 tree を書込み不能にして再 fetch を禁止する** — download / 書込み権威の変更であり、
  別審査が要る。本 wave は検知して fail-closed に留める。

## {{D:closed-detail-codes-for-dependency-prebuild}}. 依存 prebuild と postflight の失敗を段階別の閉じた診断へ変換する

**決定:** base 作成、pin 済み CCBench checkout、prebuild configure、prebuild target、
build 後の照合の各失敗を、**段階別の閉じた detail code** へ変換し、
永続化してから `OracleStatus.UNAVAILABLE` で停止する。oracle 未実行・`build_fn` 未実行を保つ。
実行失敗に `invalid-path` を流用せず、閉集合へ実行失敗を表す値を足す。
build 後の照合は preflight ではないので、postflight 専用の閉じた detail code と
永続化区間を設ける。

**理由:**

- 規律 3 (正しさシグナルを後付けにしない) は pass/fail ではなく
  **なぜ壊れたか**を構造化して返すことを要求する。停止するだけで理由が台帳に残らなければ、
  次の一手のシグナルにならない。
- filesystem の消失競合で素の `FileNotFoundError` が抜けると、
  fail-closed ではあるが失敗理由が診断 artifact から消える。
- 実行失敗を `invalid-path` へ流用すると、path が不正だったのか実行が失敗したのかが
  台帳から区別できなくなる。

**却下した選択肢:**

- **総括 `except Exception` 1 本で受ける** — どの段で落ちたかが失われる。
  実際、総括捕捉が段階別の分類を隠していたために、テストの偽の緑が 1 件生まれた。
