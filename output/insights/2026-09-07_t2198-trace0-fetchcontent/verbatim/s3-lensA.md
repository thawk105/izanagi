## 所見

### 1. 旧文法と新文法の受理集合は包含関係ではない

- 判定: **real。ただし意図しない余分 token の受理は見つからない。**
- 根拠: 現行実装は dependency token を内容で 1 本だけ抽出してから全 argv を比較する [paper_story_a2_certification.py:2091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:2091)。新案は先頭 5 本を位置で切り出す [s2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/artifacts/t2198-trace0-fetchcontent/s2-plan.md:43)。producer の実順序は [buildcache.py:1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:1965)。
- 再現または反例の具体形: 新なら通り、旧なら拒否される stock cell の列は次である。

```text
[
  "/usr/bin/cmake", "-S", "/src/ccbench", "-B", "/build/rr5-stock",
  "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
  "-DCMAKE_C_COMPILER=/usr/bin/gcc",
  "-DCMAKE_CXX_COMPILER=/usr/bin/g++",
  "-DCMAKE_PREFIX_PATH=/deps",
  "-DFETCHCONTENT_BASE_DIR=/fc",
  "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/fc/masstree-src",
  "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/fc/mimalloc-src",
  "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/fc/googletest-src",
  "-DCCBENCH_BACKOFF_FIXED=-1",
  "-DCCBENCH_BACKOFF_NOINLINE=0",
  "-DCCBENCH_BACK_OFF=0",
  "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
  "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
  "-DCCBENCH_WAL=0",
  "-DCCBENCH_TRACE=0"
]
```

  逆向きは上の列から FetchContent 4 本を除いた旧 canonical 列である。旧実装は通すが、新実装では controlled define が FetchContent prefix の位置へずれて拒否される。新実装では、追加 token、重複、欠落、並べ替えはいずれも prefix 検査または最後の全一致で拒否される。
- 成果物影響: 旧 protocol と新 protocol の受理言語が置換され、過去結果の再選択はできないが、新 protocol 内で余分 token が certified になる穴は確認できない。
- scope: **scope 内。** D1693 の「緩めない」は「新文法も閉じている」という意味なら正しいが、集合論的な「旧受理集合の部分集合」という意味では偽である。

### 2. `len(argv) < 10` は新しい最短長と不整合だが、短い tail の偶然受理はない

- 判定: **real。下限は stale。ただし偶然一致による受理拡大は refuted。**
- 根拠: 現行下限は [paper_story_a2_certification.py:2104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:2104)。新文法では fixed 9 本、dependency と FetchContent の path 5 本、controlled define 7 本なので最短は 21 本である。
- 再現または反例の具体形:
  - `fixed 9 + path 4` の全長 13 では、`path_tokens` が 4 本でも `expected` はさらに define 7 本を足すため全長 20 となり、argv と一致しない。
  - `fixed 9 + path 4 + define 7` の全長 20 では、slice の 5 本目が最初の define になり、GOOGLETEST prefix 検査で落ちる。
  - よって `tail` が 5 本未満のとき `expected == argv` になる解はない。
  - ただし実装が `path_tokens[index]` を直接読むなら `IndexError`、非 strict な `zip` なら最後の全一致による遅い拒否となる。CLI collector は `IndexError` も indeterminate に変換する [paper_story_a2_certification.py:4669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:4669) が、validator 単体の例外契約は崩れる。
- 成果物影響: 誤って certified にはならないが、短い argv が明示的な grammar rejection ではなく `IndexError` 経由の空 cells、空 effects、`indeterminate` になる余地がある。
- scope: **scope 内。**

### 3. loader の 6 条件だけでは prefix の意味を固定できない

- 判定: **real。ただし別層が実 producer との不一致を拾う。**
- 根拠: loader 案は構造条件だけである [s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/artifacts/t2198-trace0-fetchcontent/s2-plan.md:28)。現行 loader も grammar の scalar、fixed、toolchain を構造的に検査する [paper_story_a2_certification.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:418)。
- 再現または反例の具体形: 次はいずれも提案された 6 条件を満たすため loader 単体では止まらない。

```json
[
  "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
  "-DFETCHCONTENT_BASE_DIR=",
  "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
  "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST="
]
```

```json
[
  "-DFETCHCONTENT_BASE_DIR=",
  "-DFETCHCONTENT_SOURCE_DIR_MASTREE=",
  "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
  "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST="
]
```

  A-2 の exact literal test は [test_paper_story_a2_certification.py:1690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1690) で止められる。A-6 test は現在 grammar literal を比較していない [test_paper_story_a2_certification.py:1839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1839) ため、プランどおり exact assertion の追加が必要である。

  さらに実 producer との全一致を実際に通る test は次である。
  - producer 呼出し: [test_paper_story_a2_certification.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1130)
  - collector から validator が実行される地点: [paper_story_a2_certification.py:2579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:2579)
  - A-2 の実 test: [test_paper_story_a2_certification.py:4652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4652)
  - A-6 の実 test: [test_paper_story_a2_certification.py:2275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:2275)

  policy の順序や綴りだけが壊れれば、producer は canonical 順を出すのでこの層で拒否される。
- 成果物影響: test を通さず壊れた policy を投入すると collector は certified を選ばず indeterminate にする。壊れた policy に合う偽 argv 自体は validator の言語に入るが、policy bytes と protocol hashも変わるため hash 不変の穴ではない。
- scope: **scope 内。**

### 4. `trace0_cmake_argv` の新配列は preimage に入るが、受理意味の全体は protocol hash に束縛されない

- 判定: **real。prefix literal 自体の欠落は refuted だが、hash 不変で受理が動く経路は存在する。**
- 根拠: `_protocol_preimage` は `trace0_cmake_argv` 全体を含む [paper_story_a2_certification.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:290)。一方、hash はその JSON だけから作られる [paper_story_a2_certification.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:551)。Python 側の path 判定と `_QSUB_ENV_KEYS` は入らない。
- 再現または反例の具体形:
  1. 新 policy bytes を固定したまま、FetchContent 値の absolute-path 検査を nonempty 検査へ変えると、`-DFETCHCONTENT_BASE_DIR=relative` などが新たに通るが `protocol_sha256` は不変である。
  2. 新 policy bytes を固定したまま `_QSUB_ENV_KEYS` へ `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` を足す前後を比べると、同じ receipt の受理が変わる。実際の exact set 判定は [paper_story_a2_certification.py:1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:1282) である。
  3. shell literal の変更は protocol hash には入らないが、job body bytes は別の `job_body_sha256` で束縛される [paper_story_a2_certification.py:1230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:1230)。
  4. `buildcache._FETCHCONTENT_SOURCE_NAMES` は producer 順を変える [buildcache.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:58) が、policy を同時に変えなければ validator の受理言語は変わらず、producer が拒否されるだけである。
- 成果物影響: 同じ `protocol_sha256` のまま、receipt または argv が accepted と indeterminate の間を移り得る。artifact 内の policy hash は同じで、shell 変更だけは別途 job-body hash に現れる。
- scope: 新しい path 検査と qsub key の事実記載は **scope 内**。Python interpreter 全体を protocol identity に束縛する一般改修は **scope 外の裁定パッケージ候補**であり、本 wave 向けの新 gate は提案しない。

### 5. golden 張り直しに F36 型の自己参照はない

- 判定: **refuted。**
- 根拠: bytes hash は policy file の raw bytes、protocol hash は policy document の preimage だけから作られる [paper_story_a2_certification.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:339)。導出手順も policy path だけを入力にしている [s2-plan.md:222](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/artifacts/t2198-trace0-fetchcontent/s2-plan.md:222)。
- 再現または反例の具体形: 依存グラフは `policy bytes -> bytes hash / parsed preimage -> test literal` で一方向である。test file の bytes はどちらの hash 入力にも含まれない。
- 成果物影響: test literal を同じ commit で更新しても hash は再帰的に変わらず、certified 選択、レポート、台帳に循環は生じない。
- scope: **scope 内。**

### 6. 「live pin は hash literal 5 箇所だけ」は hash 検索としては正しいが、一般化すると偽

- 判定: **real。**
- 根拠: 指定された資料内では旧 4 hash の literal は確かに test の 5 箇所だけである [test_paper_story_a2_certification.py:1763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1763)、[test_paper_story_a2_certification.py:1839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1839)。しかし A-2 grammar 全体を exact dict で固定する semantic pin が別にある [test_paper_story_a2_certification.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1720)。
- 再現または反例の具体形: policy に新 key を追加して hash 5 箇所だけ張り直し、`:1720-1741` を更新しなければ `test_policy_is_the_exact_literal_four_cell_protocol` は必ず赤になる。これは path hash ではなく grammar literal を key にする追加 pin である。
- 補足: `Policy` dataclass の hash は load 時導出 [paper_story_a2_certification.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:189)。role 名、schema 名、report 内 hash は動的参照で、今回の manual golden 張り直し箇所ではない。指定 test file に `pytestmark` または `xdist_group` はない。review ledger を含む repo 全体の否定は、今回許可された 8 ファイルだけでは **未確定**。
- 成果物影響: runtime 成果物は変わらないが、hash 5 箇所だけを更新した commit は semantic pin が stale のため test suite が赤になる。
- scope: **scope 内。**

### 7. 変異候補には帰属不成立と同値 mutant がある

- 判定: **real。全候補が恒真ではないが、現状の表だけでは変異ごとの帰属を証明できない。**
- 根拠: 事前登録候補は [s2-plan.md:277](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/artifacts/t2198-trace0-fetchcontent/s2-plan.md:277)。全 test に condition context を差し替える autouse fixture がある [test_paper_story_a2_certification.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:53)。

| 変異対 | 判定 |
|---|---|
| policy key を `_TRACE0_CONFIGURE_ARGV_KEYS` から削除 | loader が assertion 前に落ちる。赤にはなるが、policy を読む多数の test が同時に赤となり帰属不成立。 |
| loader の 6 条件 | 長さ、重複、空白、末尾 `=` は独立 fixture を作れる。exact list、要素 str の候補が表から欠落。nonempty は「str かつ `=` で終わる」から論理的に導かれ、単独削除は同値 mutant である。 |
| base と masstree の順交換 | producer 生成列を実 validator に渡せば有効。ただし他の prefix/order 変異でも同じ test が赤になる。 |
| source prefix 検査を 1 本削除 | typo token の値を absolute path のままにすれば、その prefix 検査だけが拒否理由となる。候補中では帰属が強い。 |
| 全一致を部分一致へ変更 | 既存の `-DUNKNOWN=1` 追加は controlled map に拾われないため、全一致だけを狙える [test_paper_story_a2_certification.py:4619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4619)。有効。 |
| disconnected を許す | 実 producer 位置へ挿入すると prefix の位置ずれでも落ち、末尾へ挿入すると全一致でも落ちる。専用機構への帰属は成立しない。 |
| staged verifier 呼出し削除 | mock の call と順序を明示検査すれば有効。戻り値だけ使う test では NameError など別理由で赤になり得る。新 test 本文がないため未確定。 |
| prebuild の source 1 本欠落 | `_REAL_CONDITION_GATE_FAMILY` を通し、mock producer が exact kwargs を比較する既存方式 [test_paper_story_a2_certification.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:176) なら有効。 |
| condition argv の欠落、順序変更 | actual helper から mock capture へ渡る tuple の exact 比較 [test_paper_story_a2_certification.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:192) は有効。新 test と既存 test の二重赤になる。 |
| receipt observer の移動、削除 | condition context の yield 完了、observer call、campaign call の event 順を検査すれば有効。単に receipt 値を fake するだけでは機構を通らず未確定。 |
| 5 値 forwarding | fake `run_campaign` の exact kwargs 比較は caller seam の証明として有効。ただし loop、pipeline、buildcache を通った証明には数えられない。既存 test は `loop.evaluate` と raw producer を差し替えている [test_paper_story_a2_certification.py:4252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4252)。 |
| qsub env key の削除、片側変更 | production validator の exact set と `qsub_environment == variables` を通せば有効 [paper_story_a2_certification.py:1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:1282)。qsub argv と receipt の両方を同じ別値へ変える変異は受理される。 |
| submitter の qsub と receipt の片側追加 | 対象 test file が射影外なので未確定。プラン記述どおり両面を exact 比較する必要がある。 |
| job body の `name-src`、copy 欠落 | 対象 test file が射影外なので未確定。shell 本体を mock で置換する test では証明にならない。 |

  `inspect.getsource` 依存箇所は [test_paper_story_a2_certification.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:74) と [test_paper_story_a2_certification.py:4110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4110)。前者は runtime helper test と対になっているが、後者は build/trace validator 本体を通らない。
- 成果物影響: 帰属不成立のままでは test が赤でも壊れた機構を特定できず、別 gate の偶然の赤を証拠にして誤った certified 実装を採用する余地が残る。
- scope: **scope 内。**

### 8. 1 key 案と 3 key 案は argv 受理言語の証明力では同等

- 判定: **refuted。「1 key の方が厳密に強い」とは証明できない。採用自体は妥当。**
- 根拠: producer は base、source 3 本を固定順で組む [buildcache.py:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:1937)。両案とも最終 `list(argv) == expected` を維持する。
- 再現または反例の具体形:
  - producer の `_FETCHCONTENT_SOURCE_NAMES` だけを並べ替えると、1 key 案も3 key 案も policy 順と不一致になり拒否する。
  - policy だけを並べ替える場合も両方拒否する。
  - producer と policy を同時に並べ替える場合は両方が新しい protocol hash を伴って受理する。
  - よって「buildcache 定数との食い違いが黙って通る」経路はどちらにもない。
  - 3 key 案は prefix と name の連結が非一意になり得るため、異なる policy 表現が同じ token 言語を表す余地がある。1 key は full prefix を直接 hash するので、この表現上の曖昧さだけは小さい。
- 成果物影響: producer と policy の片側だけが変われば、両案とも certified 選択なし、report は indeterminate。同時変更なら両案とも protocol hash が変わる。
- scope: **scope 内。**

## 親 brief への反証

- 「live な pin は test の 5 箇所だけ」は、**旧 hash literal の出現数**という限定なら指定資料内で正しい。しかし「今回更新が必要な live semantic pin は 5 箇所だけ」という一般化は偽である。A-2 grammar 全体の exact dict assertion [test_paper_story_a2_certification.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1720) も更新必須である。プラン自身はこれを変更面へ追加しており、親 brief の漏れを事実上訂正している。
- 「`FETCHCONTENT_FULLY_DISCONNECTED=ON` は本経路に出ない」への反証はなし。producer は `post_oracle_dependency_binding is not None` の場合だけ生成する [buildcache.py:1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:1944)。
- 「`_protocol_preimage` の構成 key は変えない」への反証はなし。新配列は既存の `trace0_cmake_argv` 配下に入る。
- repo 全体の review ledger、別 test file、xdist 設定まで含む pin 閉包は、指定された 8 ファイルだけを読むという制約下では未確定。

## プランへの推奨

1. `len(argv) < 10` を放置せず、slice 前に path token が exact 5 本あることを明示検査する。さらに最終期待長 21 は固定値でなく `len(fixed) + len(path_prefixes) + len(ordered_define_tokens)` から検査する。
2. 1 key 案は維持してよい。ただし「3 key より受理言語の証明力が強い」ではなく、「同じ閉じた言語を、非一意な再合成なしで表す」と根拠を修正する。
3. A-6 test にも 4 prefix の exact literal assertion を実際に追加する。golden hash の更新だけでは、誤 literal と誤 golden の同時更新を止められない。
4. loader mutation は exact list、要素 str を追加し、nonempty 削除は末尾 `=` 条件と同値な mutant だと明記する。disconnected test は閉包 test であって専用 rejection 機構への帰属証拠には数えない。
5. verifier と receipt observer の test は mock の戻り値だけでなく、production call の存在と順序を event で検査する。5 値 forwarding の fake campaign test は caller seam 限定の証拠として扱う。
6. `protocol_sha256` が policy data を束縛しても、Python interpreter と qsub exact set までは束縛しないという限界をプランに明記する。一般的な code-identity gate の新設は本 wave では行わず、必要なら scope 外の裁定パッケージへ送る。

## 総括

最も重い所見は、同じ `protocol_sha256` のまま Python の path 判定や qsub env exact setを変えると受理が動くことである。
新しい 4-prefix 配列そのものは preimage に入り、追加 token を許す穴も見つからない。
旧文法と新文法の受理集合は意図どおり置換されるため、「緩めない」は閉包維持の意味に限定すべきである。
`len(argv) < 10` は最短 21 本へ整合させ、短い slice を明示的な `CertificationError` にする必要がある。
1 key と3 keyは全 argv 一致の証明力では同等だが、1 keyは再合成の曖昧さが少ないため採用継続でよい。
golden 5 箇所だけでなく、A-2 exact grammar literal と新しい A-6 literal assertionも更新対象である。