## 所見

1. `_exact_trace0_configure_argv` は producer が生成できない FetchContent path token を受理する。

   - 判定: **real**
   - 重要度: **must-fix**
   - 根拠: `orchestrator/campaign/paper_story_a2_certification.py:2175-2185` は、FetchContent 値について非空かつ `os.path.isabs` だけを検査し、受け取った token 自体を `expected` へ戻している。一方 producer は base を canonicalize し (`orchestrator/campaign/buildcache.py:750-762,2448-2450`)、source 3 本も NUL なし、絶対 path、実在 non-symlink directory、canonical path に限定する (`orchestrator/campaign/buildcache.py:823-845`)。
   - 再現: 正常列の MASSTREE token だけを `-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/../` または値に `\x00` を含む `-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/x\x00y` へ変えると、現行 `_exact_trace0_configure_argv` は受理した。producer は前者を `/` に canonicalize して別 bytes を出し、後者は明示拒否する。
   - 放置時の影響: producer が実行・記録できない argv bytes でも trace0 が通り、対応する raw evidence が `cells` / `effects` を持つ positive report として参照されうる。
   - scope: **内**
   - 既存 gate の再照準: 少なくとも同じ path predicate 内で NUL と lexical noncanonical path を拒否し、producer が出せる token 集合へ狭める必要がある。

2. M4 は同値変異であり、登録 test は対象 guard の削除を検出しない。

   - 判定: **real**
   - 重要度: **must-fix**
   - 根拠: `minimum_argv_length = len(fixed) + len(path_prefixes) + len(ordered_define_tokens)` を満たせば、必然的に `len(tail) >= len(path_prefixes)` になる (`paper_story_a2_certification.py:2167-2174`)。したがって後者の guard は到達可能な受理集合を変えない。test は長さ 13 の列を作り、先の minimum guard の `"shorter"` でも成功する (`orchestrator/tests/test_paper_story_a2_certification.py:4961-4976`)。
   - 再現: `if len(tail) < len(path_prefixes)` のみを削除しても、同じ入力は line 2170 で `CertificationError` となり、対象 test は緑のままになる。
   - 放置時の影響: mutation 台帳で M4 を KILLED にできず、変異受入を閉じられない。認証値自体は変わらない。
   - scope: **内**
   - 再照準: M4 は登録から外すか、両 guard を失わせたときの例外 taxonomy を検査する明確な変異へ置き換える。

3. M2、M3、M8〜M14 は事前登録された完全集合より広い test を赤にし、単一理由性が成立しない。

   - 判定: **real**
   - 重要度: **must-fix**
   - 根拠:
     - M2 は canonical positive argv も拒否するため、swap negative だけでなく positive collector 群も赤になる (`paper_story_a2_certification.py:2163-2186`)。
     - M3 の prefix 部分一致化は少なくとも `duplicate-configure-token`、`unknown-configure-token`、`fully-disconnected` の 3 parameter を受理する (`test_paper_story_a2_certification.py:4979-5011`)。
     - M8〜M10 の同じ exact kwargs / argv は、二つの test が共有する `_assert_condition_gate_context` に加え、cleanup と real-record test でも検査される (`test_paper_story_a2_certification.py:101-163,166-299,302-345,475-545,808-844`)。
     - M12 と M13 は同じ forwarding を `test_official_run_observes_dependency_receipt_after_condition_prebuild` と `test_official_run_forwards_exact_fetchcontent_five_tuple` が重ねて検査する (`:4332-4590,4593-4735`)。
     - M14 で `_QSUB_ENV_KEYS` から key を削ると、新 key を持つ全 valid receipt が line 1315 の extra-key 判定で先に落ちる (`paper_story_a2_certification.py:1314-1326`)。
   - 再現: M8 の mimalloc prebuild keyword を落とすだけで、登録 node に加えて共有 helper を呼ぶ `test_condition_gate_uses_exact_offline_fetchcontent_argv` なども赤になる。
   - 放置時の影響: mutation 台帳の KILLED 理由と完全集合が事前登録と一致せず、どの gate が変異を殺したかを一意に参照できない。
   - scope: **内**
   - 再照準: M2 は positive を壊す「期待順交換」でなく位置-prefix 検査だけの無効化へ、M3 は影響する既存 3 parameter 全部へ、M8〜M10 は共有 helper の assertions を分離、M11/M12 は未定義変数を作らない well-shaped bypass、M13 は五値 forwarding test へ限定、M14 は key を optional にする gate 変異へ変更する。

4. 新実装だけが受理する argv は実在するが、余分 token・順序違い・空値・別変数名は受理しない。

   - 判定: **real。ただし意図された protocol 置換であり欠陥ではない**
   - 重要度: **nit**
   - 根拠: `buildcache._v2_commands` の実出力順は dependency、base、masstree、mimalloc、googletest、controlled defines (`buildcache.py:1936-1971`)。policy 2 本も同順 (`paper_story_a2_certification.v2.json:70-77`, `paper_story_a6_certification.v2.json:64-71`)。
   - 新実装のみが受理した具体列:

     ```text
     /usr/bin/cmake
     -S /source
     -B /build
     -DCMAKE_BUILD_TYPE=Release
     -DENABLE_SANITIZER=OFF
     -DCMAKE_C_COMPILER=/usr/bin/gcc
     -DCMAKE_CXX_COMPILER=/usr/bin/g++
     -DCMAKE_PREFIX_PATH=relative-dependency
     -DFETCHCONTENT_BASE_DIR=/
     -DFETCHCONTENT_SOURCE_DIR_MASSTREE=/
     -DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/
     -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/
     -DCCBENCH_BACKOFF_FIXED=-1
     -DCCBENCH_BACKOFF_NOINLINE=0
     -DCCBENCH_BACK_OFF=0
     -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
     -DCCBENCH_NO_WAIT_OF_TICTOC=0
     -DCCBENCH_WAL=0
     -DCCBENCH_TRACE=0
     ```

     `_v2_commands` から得た 21 token であり現行 checker も受理した。旧実装は FetchContent 4 token を `expected` に含めないため拒否する (`HEAD` 版 `paper_story_a2_certification.py:2133-2140`)。
   - 反例:
     - tail 6 本目へ二本目の `-DCMAKE_PREFIX_PATH=/other` を挿入: 最終全列比較で拒否。
     - base と masstree を交換: prefix 位置検査で拒否。
     - dependency または FetchContent の空値: 拒否。
     - FetchContent の相対値: 拒否。
     - `-DFETCHCONTENT_BASE_DIR_EXTRA=/` と `-DFETCHCONTENT_BASE_DIR:PATH=/`: exact prefix に一致せず拒否。
   - 放置時の影響: 正規の新 protocol だけが新しい FetchContent build を選択でき、旧結果は旧 hash 参照のまま残る。意図どおり。
   - scope: **内**

5. dependency prefix の相対 path 受理は新たな緩和ではない。

   - 判定: **refuted**
   - 重要度: **nit**
   - 根拠: 新実装は `index > 0` にだけ絶対 path を要求する (`paper_story_a2_certification.py:2176-2183`)。旧実装も dependency token について、prefix 一致と `partition("=")[2]` の非空しか検査していない (`HEAD` 版同ファイル:2133-2137)。`buildcache._v2_commands` も非空 dependency string をそのまま token 化する (`buildcache.py:1937-1939`)。
   - 反例: 上記具体列の `-DCMAKE_PREFIX_PATH=relative-dependency` は新 checker を通る。FetchContent なしの対応する旧 17-token 列も旧 checker を通る。
   - 放置時の影響: dependency prefix の受理集合はこの点で変化せず、既存 report や台帳参照は動かない。
   - scope: **内**

6. minimum length、semantic policy pin、golden 4 値には不整合を認めない。

   - 判定: **refuted**
   - 重要度: **nit**
   - 根拠:
     - `fixed` は 9 token、path は 5 token、controlled define は全 cell で 7 tokenなので最短は 21。値は cell ごとに変わるが key 数は変わらない (`paper_story_a2_certification.py:2083-2090,2145-2169`)。`_v2_commands` の A-2/A-6 全 cell 実出力も各 21 token だった。
     - 削除された `len(argv) < 10` を参照する別 caller/test はなく、現行 caller は `validate_trace0_evidence` の一箇所だけ (`:2288`)。
     - loader は指定された type、長さ 4、str、非空、空白なし、末尾 `=`、一意性を検査する (`:452-467`)。
     - 順序交換や綴り違いは loader 単体を通るが、producer の実列は line 2178 で拒否される。さらに shipped policy の変更は A-2 と A-6 の exact dict test が固定する (`test_paper_story_a2_certification.py:1764-1791,1956-1983`)。
   - golden の再導出結果:
     - A-2 bytes: `2e97d69b60b73a1395d6b5efdc0198ee0cfbf84cfb48cabed442e705e64f41ea`
     - A-2 protocol: `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c`
     - A-6 bytes: `8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8`
     - A-6 protocol: `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`
   - 導出: bytes 値は各 policy の実 bytes、protocol 値は `_protocol_preimage` の 9 policy field を canonical JSON 化した bytes から計算した (`paper_story_a2_certification.py:298-309,575-581`)。test file はどちらの入力にも含まれず循環はない。
   - 放置時の影響: hash、report、台帳参照に追加の drift はない。
   - scope: **内**

7. 指定された「甘い test」類は、M4 と重複帰属を除けば認めない。

   - 判定: **refuted**
   - 重要度: **nit**
   - 根拠: golden は実際の hash を動的に期待値へ差し込まず固定 literal である (`test_paper_story_a2_certification.py:1813-1823,1984-1987`)。M8〜M13 は依存層を stub しているが、対象 call、kwargs、順序を実際に通す。`inspect.getsource` を使う test も対象 wiring の runtime assertion と対になっている。`tmp_path`、scratch path、USER、request ID は synthetic harness から導出され、live 時刻や live job ID の焼込みではない。
   - 再現または反例: `test_condition_gate_uses_exact_offline_fetchcontent_argv` は保存した real context manager を実行し、stub consumer が受け取った完全な kwargs と configure tuple を比較する (`:166-299`)。
   - 放置時の影響: M4 と mutation 帰属を直せば、これらの test 構造だけで certified report の値が不当に緑になる経路は確認できない。
   - scope: **内**

## 変異事前登録の帰属判定

- **M1: 未確定。** 現実装に GOOGLETEST 専用 branch がなく generic loop なので、「1 本削除」の注入形が一意でない。index 4 の prefix/nonempty/absolute predicate だけを skip する exact diff へ具体化すれば、登録 test の 3 parameter に再照準できる。
- **M2: 不成立。** 期待順自体の交換は swapped negative を受理する一方、canonical positive evidence を広く拒否する。位置-prefix 検査だけを無効化する変異へ再照準が必要。
- **M3: 不成立。** 部分一致化では少なくとも `duplicate-configure-token`、`unknown-configure-token`、`fully-disconnected` の 3 node が赤になる。完全集合をこの 3 件へ修正する必要がある。
- **M4: 不成立。** 下限 guard は minimum-length guard から論理的に導かれ、単独削除は同値変異。登録から外すべきである。
- **M5: 帰属成立。** 末尾 `=` のみを削除すると `missing-equals` case だけが loader を通る。他条件は同じ入力を拒否しない。
- **M6: 帰属成立。** 長さ検査のみの削除で 3 要素の `wrong-length` case が通る。後続 loader は長さを再検査しない。
- **M7: 帰属成立。** 一意性検査のみの削除で `duplicate` case が通る。別条件は全て満たす。
- **M8: 不成立。** prebuild kwargs は登録 node 以外に共有 helper、cleanup、multi-cell、real-record test でも検査される。
- **M9: 不成立。** capture tuple は `test_paper_condition_gate_is_p_strict_and_precedes_campaign` と専用 test が同じ helper で二重検査し、cleanup と real-record test にも同じ assertion がある。
- **M10: 不成立。** 順序交換も M9 と同じ複数 assertion を赤にする。
- **M11: 不成立。** 呼出しを文字どおり削除すると `staged_sources` が未定義となり、専用 test 以外の成功系 `run_workload` test も広く赤になる。well-shaped な未検証 mapping への置換変異へ再照準が必要。
- **M12: 不成立。** observer 呼出しの単純削除は `dependency_receipt` 未定義の cascade を起こし、M13 側の forwarding test も赤になる。well-shaped 固定 receipt への置換で call/order gate に絞る必要がある。
- **M13: 不成立。** mimalloc forwarding は M13 専用 test と M12 の integration test の双方が検査する。
- **M14: 不成立。** `_QSUB_ENV_KEYS` からの削除は missing case を通すだけでなく、現行 key を持つ全 valid receipt を extra-key として拒否する。key を optional にする exact-set predicate 変異へ再照準が必要。
- **M15: 不成立。** copy 行削除は job-contract test が直接検出するが、生成された staging inventory は `run_workload` 冒頭の staged-source verifier (`paper_story_a2_certification.py:3412-3423`) にも拒否される。単一理由 KILL として数えず、producer contract regression として残すのが妥当。
- **M16: 不成立。** suffix なし destination も同じ job-contract testと downstream staged-source verifier の二層で拒否される。M15 と同じ再分類が必要。

## 総括

最も重い所見は、FetchContent path token の値が producer の生成可能集合より広く、noncanonical path や NUL 入り token まで trace0 checker が受理する点である。
余分 token、二本目の dependency prefix、順序交換、空値、FetchContent の相対 path は閉じた全列比較により拒否され、D1693 の「余分 token を許さない」は維持されている。
一方、M4 は同値変異で、M2、M3、M8〜M16 の多くは事前登録どおりの単一理由性を満たさない。
policy literal、最短 21 token、producer 順序、golden 4 値には不整合を認めなかった。
read-only 条件に従い pytest は実行せず、静的検査と書込みを伴わない関数評価だけで判定した。