---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2406-s4loop-gflags
seq: 2
---

## {{D:s4-loop-prefix-contract-exact-three-lines}}. 段 4 loop の job body で `CMAKE_PREFIX_PATH` を扱えるのは exact 3 行だけとし、事前構築にも同じ 2 root を explicit に渡す

**決定:** D1773 の移植を実装するにあたり、契約テスト `orchestrator/tests/test_p3_s4_loop_job_contract.py` の
`forbidden-cmake-environment-injection` を次の形へ改める。job body の実行面 (コメント専用行と heredoc を除いた面) で
`CMAKE_PREFIX_PATH` を含む行は、出現順に (1) sanitize 段の `unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE`、
(2) glog configure の `-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"`、
(3) `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` の exact 3 行だけを受理し、
他の代入・`unset`・`export -n`・`env -u` を含むあらゆる形を拒否する。(3) は gflags / glog の install 2 本の後、
masstree 事前構築の呼出しの前に 1 回だけ置き、事前構築は driver 2 分岐の両方より前になければならない。
`GFLAGS_INSTALL_DIR` / `GLOG_INSTALL_DIR` は `$TMPDIR` (job 別 scratch) 配下に束縛する。
さらに job body は masstree 事前構築 (`buildcache.prepare_masstree_fetchcontent`) へ同じ 2 root を
semicolon 区切りの `dependency_prefix` としても渡し、receipt の `configure_argv` に
`-DCMAKE_PREFIX_PATH=<gflags-install>;<glog-install>` が残るようにする。receipt の schema と key 集合は変えない。
admission registry の entry は分類・reason・gate・evidence に変えるものが無く不変とし、D1773 (c) の
「同じ commit で更新する」は「変える場合は同じ commit」と読む。

**理由:**

- D1773 (d) は env の `CMAKE_PREFIX_PATH` を driver 本走まで持たせることを要求する。従来の契約は
  同変数の代入を全面禁止していたので、受理形を足す必要があった。足す形を exact 1 行に限り、
  `unset` / `export -n` / `env -u` を含む全形を拒否しなければ、export 後に driver だけから prefix を
  外す job body が受理集合に残る (段 6 レビュー A の real 所見)。
- F813 の型 (判定器が環境から解決した実体が証拠に残らない) を避けるため、事前構築の receipt にも
  prefix を残す。driver 側は `buildcache.build_v2` が ambient prefix を identity へ束縛するが、事前構築の
  receipt は `configure_argv` しか持たないので、explicit 引数で同じ値を露出させるのが schema 不変の最小手
  (段 3 レンズ A / 段 4 裁定 A4)。計算ノードの実測 (job `983020.nqsv`) で receipt に
  `-DCMAKE_PREFIX_PATH=/scr/.../gflags-install;/scr/.../glog-install` が入ることを確認した。
- 検査面をコメント専用行と heredoc を除いた実行面に統一し、コメント専用行では heredoc opener を探さない。
  heredoc 内の required fragment (policy の 4 key、`dependency_prefix=`) はコメント専用行を除いた raw source
  でも照合する。これで「コメントアウトして契約だけ通す」型を塞ぐ (段 6 レビュー A / B の real 所見)。

**却下した選択肢:**

- **`printf -v` / `read` / 名前分割 `eval` / 綴りの難読化 / 行末コメントで marker を満たす形まで拒否する** —
  本 wave 以前から全 marker に共通する盲点であり、D1773 の範囲外の gate 拡張になる。同一主体が gate と
  検査を変えられる限り repo 内検査は完全防壁ではない (D387) ことを明記し、記録に留める。
- **receipt に gflags / glog の source HEAD や install realpath を足す** — 粗い provenance で足りる方針
  (D1773 (b)) と schema 不変の範囲を越える。
- **admission registry に無内容の更新を入れる** — 分類が変わらない以上、盛るだけになる。
