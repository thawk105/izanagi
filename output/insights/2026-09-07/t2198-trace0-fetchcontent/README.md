# [T-2198] A-2 / A-6 認証経路の測定 build をオフライン依存へ配線した

wave branch `worktree-dev-wave-t2198-trace0-fetchcontent`。2026-09-07。

## 結論

**D1693 (D1688 の案 1、ユーザー裁定) を実装した。** 閉じた trace0 configure 文法へ FetchContent の
枠を**厳密な期待値として**足し、A-2 / A-6 の認証経路の測定 build を計算ノードの環境契約
(外部 network 不可) に合う staged 依存へ配線した。凍結された認証プロトコル同一性の golden 4 値
(5 箇所) を張り直した。

**実測はしていない。** 本 wave はコード・テスト・policy・shell を land させるところまでで、
A-6 の read-heavy 認証を実際に走らせるのは次の wave である。

## 何を変えたか

| 層 | 変更 |
|---|---|
| policy 2 本 | `trace0_cmake_argv.configure` へ ordered 4-prefix `fetchcontent_path_argument_prefixes` を追加 |
| 文法検査 | `_exact_trace0_configure_argv` の `expected` を `fixed + path_tokens + defines` にし、path segment を位置で切り出して prefix 一致・非空・(FetchContent 側は) 正規絶対 path・NUL 不在を検査。最終判定は `list(argv) != expected` の全一致のまま |
| policy loader | 新 key に list / 長さ 4 / str / 非空 / 空白なし / 末尾 `=` / 一意 を課す |
| 認証経路 | `run_workload` が staged 3 依存を検証し、条件 gate の prebuild と `capture_define_inputs` へ source dir を渡し、`run_campaign` へ 5 値 (base / source 3 本 / dependency receipt) を渡す |
| 投入器 | 必須 `--third-party-source-root` を追加。`realpath` の前後**両方**で安全値を検査 |
| job body | job-local scratch で `<name>` から `<name>-src` へ複製し、`run-workload` へ渡す |
| golden | A-2 / A-6 の bytes / protocol hash を編集後の policy の実 bytes から張り直し |

## 凍結成果物の扱い (D1693 と絶対規律 7)

- **過去の認証値は取り直していない。** 旧結果は旧 policy hash / 旧 protocol hash に束縛されたまま残る。
- **現行 policy の `protocol_sha256` は旧結果のものと一致しない。** 新旧の対応は次のとおり。

| policy | 旧 bytes sha256 | 旧 protocol sha256 | 新 bytes sha256 | 新 protocol sha256 |
|---|---|---|---|---|
| A-2 | `42bfee487c9e517b9876fbb41f8a4b4de53266ced1543263087bbd637ecc897e` | `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4` | `2e97d69b60b73a1395d6b5efdc0198ee0cfbf84cfb48cabed442e705e64f41ea` | `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c` |
| A-6 | `4ca15d071f0bc10febe3274d0523b59f0e4903bf612ff050bef7e6728a3700d4` | `a73bc3a0eabd1bcb960779c9b61b20983ef3cfb88d76d50c073e9ced4f6be445` | `8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8` | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` |

新しい 4 値は親が独立に再計算し、実装子の申告値と完全一致することを確認した
(`hashlib.sha256(path.read_bytes())` と `load_policy(path).protocol_sha256`)。

- **旧 submission receipt は現行の exact qsub env 契約でも再受理されない。** 新しい環境変数
  `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` が exact key 集合へ入ったためである。ただしこれは新しい破壊
  ではなく、`protocol_sha256` と job body hash の変化に既に含まれている。
- **`protocol_sha256` が束縛するのは policy document であって、Python 側の述語や qsub env の
  exact 集合ではない。** 同じ protocol hash のまま Python の path 判定を書き換えれば受理は動く。
  これは本 wave が作った欠陥ではなく認証プロトコル同一性の既存の射程であり、`CLAUDE.md` 絶対規律 7 の
  「repo 内の挙動検査は gate と検査を同じ主体が変更できる限り意図的な弱体化への完全な防壁ではない。
  この限界は主張せず明記する」に従って**明記だけを行い、新しい gate は作らなかった**。

## 受理集合はどう変わったか

新しい期待値は旧期待値の**上位集合ではなく別の閉じた言語**である。D1693 の「緩めない」は
閉包の維持を指し、集合の包含ではない (段 3 レンズ A 所見 1)。

- 新たに受理: producer が実際に出す FetchContent 4 token 付きの canonical argv。
- 引き続き拒否: 余分 token、2 本目の dependency prefix、順序違い、空値、相対 path、
  `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` の混入。
- **新たに拒否**: NUL を含む値、`/../` のような lexically noncanonical な値
  (producer が生成できない token。段 6 レビュー A 所見 1)。
- **新たに拒否**: `realpath` 後に comma / `=` / 改行を含む投入器の path
  (段 6 レビュー B 所見 1)。

## 反証された前提 (依頼文と F808 / D1524 の記述)

依頼文と F808 は「`run_campaign` は FetchContent の source dir を受け取る引数を持たない」と書くが、
**現行 main では偽である。** `orchestrator/campaign/loop.py` の `run_campaign` は 5 引数すべてを持ち、
`pipeline.evaluate` 経由で `buildcache` へ素通ししている (commit `466528512`、T-2356 で着地)。
裁定 D1524 / D1693 の効力は変わらないが、**共有 pipeline の横断改修は不要**になり、
残っていたのは「認証経路の呼び手が 5 引数を渡していない」ことと「閉じた文法が FetchContent token を
拒否する」ことの 2 点だけだった。F808 と D1524 の当該記述は追記で訂正する (絶対規律 7)。

## 段 3 / 段 6 で real と裁定した所見

| 所見 | 出所 | 扱い |
|---|---|---|
| `<name>-src` 配置の生成者が設計から欠落 | 段 3 レンズ B | 入力契約を hydrate の実出力 `<root>/<name>` へ変え、job body で変換する形に改めた |
| producer が出せない path token を認証器が受理 | 段 6 レビュー A | 既存 helper `_lexical_absolute_path` + NUL 拒否で狭めた |
| 投入器が canonicalize 後を再検査していない | 段 6 レビュー B | `realpath` 後にも同じ安全値検査を掛けた |
| 到達不能な下限検査 | 段 6 レビュー A / B が独立に指摘 | 削除した。直前の全長検査から論理的に導かれ、どの入力でも発火しない |
| A-6 側に grammar の exact literal 検査が無い | 段 3 レンズ A | A-6 にも追加した |
| `run_workload` の直接呼び手 5 箇所のうち 1 箇所が計画から漏れ | 段 3 レンズ B | 5 箇所すべて更新した |

refuted: 床値 verifier の pin 出所 (共有 `tools/pegasus/policy.json` 由来で問題なし、親も独立に実測)、
receipt 観測時点、条件 gate の configure 被覆、job-local copy の Git 検査、golden の自己参照。

未確定として残したもの: 3 依存の実サイズ・`/scr` 容量・copy 所要。本 wave では測れない。
同じ機体で同型の copy を既に 2 driver (`submit_floor.sh`、`p3_s4_loop_pegasus.sh`) が行っている。

## 変異 matrix

**19 変異すべて KILLED。生き残りゼロ。baseline は全巡 PASSED。**

| 巡 | 対象 | 登録 | 結果 | 台帳 |
|---|---|---|---|---|
| probe | m01〜m19 | 全件 SURVIVED (node 収集) | 9 走で orphan-hold により中断。6 KILLED / 3 SURVIVED | `mutation-ledger-probe.json` |
| B | m01〜m09 本登録 + m10〜m19 probe | 9 件 KILLED + 10 件 SURVIVED | m01〜m09 が node 完全一致で KILLED、m10〜m19 は全件 KILLED (probe に対して MISMATCH) | `mutation-ledger-b.json` |
| C | m10〜m19 本登録 | 10 件 KILLED | 10/10 一致 | `mutation-ledger-c.json` |

### probe 巡の erratum (`DW-M02`)

初回 probe で **m01 / m02 / m08 が生き残った**。原因はいずれも「別の検査に隠れて、その検査だけを
撃つ負例が存在しない」型で、親が特定した。

- **m01 (prefix 一致検査)**: 期待値は受け取った token をそのまま echo するので最終の全一致比較でも
  捕まらず、`_argv_controlled_defines` は `-DCCBENCH_` 始まりしか見ない。撃つには
  「位置は正しいが prefix が違い、値は正規絶対 path」が要る。
- **m02 (非空検査)**: index 1〜4 の空値は直後の `_lexical_absolute_path` が拒否するため隠れる。
  lexical 検査を持たないのは index 0 (`-DCMAKE_PREFIX_PATH=`) だけで、その空値の負例が無かった。
- **m08 (loader の要素数 4 検査)**: 既存の `wrong-length` 負例は 3 要素なので一意性検査
  (`len(set(...)) != 4`) にも掛かって隠れる。長さ検査だけを撃つには「5 要素でうち 1 つが重複」
  (set サイズ 4) が要る。

3 件とも負例を足し、**狙った検査の項だけを一時的に落とすと対応する 1 node だけが赤になる**ことを
実測してから復元した (`verbatim/s6-fix2.md`)。実装は変更していない。穴はテストの不足であって
実装の欠陥ではない。

### 単一理由性の除外 (`DW-M03`)

**m16 (`_QSUB_ENV_KEYS` からの新 key 削除) は 74 node を赤にする。** 新 key を持つ正しい receipt が
すべて extra-key 判定で先に落ちるためで、赤の理由が 1 つに絞れない。**冗長 gate として明記し、
単独変異の証拠からは外す。** 段 3 レンズ A がこの過剰決定を事前に予測しており、実測が一致した。

## 実測した検査

| 検査 | 結果 |
|---|---|
| 親の焦点走 1 (認証・job 契約・plot・buildcache・official perf closure・spawn sites・hooks) | 974 passed / 1 skipped、rc=0 (計算ノード) |
| 親の焦点走 2 (campaign・段 4 loop) | 815 passed / 3 skipped、rc=0 (計算ノード) |
| 変異 matrix | 19/19 KILLED、node 完全一致 |
| `check_ai_provenance.py` (全史) | 新規違反なし |

受入全走の結果は記録 commit の後に追記する。

## 次 wave の出発点

A-6 の read-heavy 認証を実際に投入する。`fetch_third_party.py hydrate` が作る
`<root>/{masstree,mimalloc,googletest}` を `submit_paper_story_a2_certification.sh` の
`--third-party-source-root` へ渡す。3 依存の実サイズ・`/scr` 容量・copy 所要は未実測なので、
初回投入で観測する。

## erratum — 逐語の行末空白を可逆最小正規化した (D88 / `DW-S07`)

codex 子の出力に markdown の hard line break (行末の半角空白 2 個) が含まれ、
`git diff --check` の trailing whitespace に抵触した。`DW-S07` に従い、
**可視文字を 1 文字も変えない可逆最小正規化**として行末空白だけを除いた。
原文は下表の hash と byte 数で同定でき、**該当行の行末へ半角空白 2 個を戻せば復元できる**。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 対象行 | 除去 bytes |
|---|---|---|---|---|---|---|
| `verbatim/s2-plan.md` | `e874765674f0f8d86b4597a4810eb270dd3f851cc7f94e89b429a263dba446cc` | 20531 | `72fe96364ae2805c772c250872811f9f84db47a4eb8e38bfdcbd31a1f0777ccf` | 20493 | 19 | 38 |
| `verbatim/s3-lensA.md` | `947058acdbb3c513f25c1257fef3e46f11eaaf6983665da9ae6d573e0c5b32ed` | 22739 | `ce457fd40d7adba0e488da82f8d2f4d467b4cd503b66bfbfb4b2ba98b1f59322` | 22729 | 5 | 10 |
| `verbatim/s3-lensB.md` | `22c692a754539ba558e32ddcc7b428e38ba9252c378cc76d2907c6e3bc1a3c3e` | 13221 | `4a89b04aab30dfcdabf88d0c6acb0ba322db96b807680fc82361d851c8370325` | 13213 | 4 | 8 |
| `verbatim/s5-author.md` | `b2422f7363014282c9e729d611a853c5d804cc58390d1ec461b7bf23a80fc69f` | 6487 | `7846db0fe9b7d730bfc011ec9922e0f89b0aa5d1d6d6a014a7a812644c411be0` | 6479 | 4 | 8 |
| `verbatim/s6-fix1.md` | `d79eb5fb6300157a439a6eeb95071e551d1617a273734c7b1cdc5a4233545fb4` | 4031 | `6e1b084513c61bab424767eed853991f8b59472ee5308ad8ca855f017906af4e` | 4025 | 3 | 6 |
| `verbatim/s6-fix2.md` | `14b80532ad149265e039df08bbd4a52c02dc06f99f8988f23aa7eb7cfd9618ef` | 2870 | `00b4ca988c4062c41858e06377024a8431ebad43c8557bbdd765c8ebea252896` | 2864 | 3 | 6 |
| `verbatim/s6-reviewA.md` | `f1d0ad3dcea90091f30e806197ccdfe740e3944bc4dc5800f64d6d0d72088277` | 14391 | `813e5da3b20b2021572325c663b8f8ec76328ef58a3a96c7d287508cff0fd7e7` | 14383 | 4 | 8 |
| `verbatim/s6-reviewB.md` | `903f5b625bea771c2eb016e96dc041159cd74c011ee15900e4e42f20a9efcbde` | 13683 | `6cbbc281cc2887cd74da735a67ad37c865b1091710363dbe4fd0eb4248c41f19` | 13673 | 5 | 10 |

除去したのは行末の半角空白のみで、tab・全角空白・改行・可視文字は 1 byte も変えていない。
`verbatim/s1-brief.md` と `verbatim/s4-adjudication.md` は親が書いたもので抵触が無く、無変更である。
