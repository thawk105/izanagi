## 所見

略号: P = [producer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/campaign/paper_story_a2_certification.py:384)、C = [consumer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/tools/plotting/plot_a2_certification.py:168)、T = [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_plot_a2_certification.py:516)。

[RB-1] 主張: M7 は KILLED にならない。負例が同じ値を二重に検査する過剰決定 fixture である。

根拠: C:233-234 は `if any(cell.get("source_binding_status") != "bound" ...): _fail("current certification source_binding_status is not bound")`、C:432-433 は再び `if certified.get("source_binding_status") != "bound": _fail("current certification source_binding_status is not bound")` と検査する。T:727-735 は `source_binding_status` だけを `"token-mismatch"` にして同じ文言の例外を期待する。

具体的な破れ方: C:233-234 だけを外しても C:432-433 が拒否し、逆に C:432-433 だけを外しても C:233-234 が先に拒否する。どちらの一箇所変異でもテストは緑のままで、M7 は SURVIVED である。両方を外す変異は二箇所変異であり、事前登録条件を満たさない。

深刻度: blocker

最小の直し方: M7 を C:233-234 に再照準し、完全な `load_measurements` ではなく `_load_current_policy` を直接呼ぶ単一理由テストにする。C:432-433 は別変異として登録するか、今回は対象外と明記する。

[RB-2] 主張: M3 の置換位置は一意でない。

根拠: C:214-215 は `policy = _producer_policy_from_bytes(producer, raw, generation=historical_generation)` と世代を helper に渡し、C:178-181 は `return producer._load_historical_policy(path, generation=generation)` と producer に再転送する。世代受け渡しを消せる実効箇所が二つある。

具体的な破れ方: C:214-215 の引数だけを消す変異と、C:178-181 を常に `producer.load_policy(path)` にする変異が同じ観測結果になる。現在の正例は両方を殺すが、どちらの境界を守ったのか帰属できない。

深刻度: must-fix

最小の直し方: M3a を C:214-215、M3b を C:178-181 として分割し、それぞれ helper と producer loader の呼出引数を spy する。単一 M3 を維持するなら helper を廃して historical 分岐から private producer loader を直接呼び、受け渡し点を一箇所にする。

[RB-3] 主張: M6 の「歴史世代のときだけ」という変異は、指定された gate に一箇所変異として置けない。

根拠: P:394-401 で `generation` は `configure_argv_keys` に変換され、P:404-405 の共有本体は `configure_argv_keys` しか受け取らない。一方、対象検査 P:436-438 は `if tracked.is_absolute() or ".." in tracked.parts: raise CertificationError("tracked destination must be a bounded relative path")` であり、世代情報を持たない。T:707-719 は `document["tracked_destination"] = "../outside"` だけを負例にする。

具体的な破れ方: P:436-438 を単純に削除すれば歴史だけでなく公開 current loader の受理集合も広がるため、登録済み M6 より広い変異になる。現在のテストはその広い変異も殺すので、歴史世代固有の gate を証明したことにはならない。指定三 suite を検索した範囲では、current policy の不正 `tracked_destination` を直接拒否する別テストもない。

深刻度: must-fix

最小の直し方: 最小案は M6 を「共有 tracked-destination gate の削除」へ再登録し、current と historical の単一理由 fixture を各一本置く。歴史限定を維持するなら、共有本体へ明示的な private grammar generation を渡してから、その条件分岐を正確な一箇所として登録する。

実 t2364 統合境界には所見なし。T:33-36 は指定 root を固定し、T:1358-1362 は `if not root.exists(): skip(...)` の後に `assert not missing` とするため、root 全体不在だけが skip、部分欠損は failure になる。T:638-639 の逐語は `plot.load_measurements(T2364_REAL_ROOT, certification_path, raw_manifest_path)` であり、`expected_hashes` override は渡していない。

揮発値にも所見なし。新規期待値は canonical artifact の SHA-256、固定 path、schema、cell 順、closure 数であり、working tree hash、生成時刻、現在時刻を焼き込んでいない。AST テストは source を読むが source hash を期待値にしていない。

test 名の改名はない。docs 検索では [docs/failures.md:23025](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/docs/failures.md:23025) の `test_historical_rejects_changed_certification_bytes` だけが該当し、実装後も同名が T:658 に残る。

## 変異の帰属表

以下の略号は完全な nodeid を表す。

- N1 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_rejects_changed_certification_bytes`
- N2 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_rejects_unknown_bytes_with_the_same_v2_version`
- N3 = `orchestrator/tests/test_plot_a2_certification.py::test_t2364_canonical_current_full_measurements_load_without_override`
- N4 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_exact_hash_pair_uses_the_historical_policy_view`
- N5 = `orchestrator/tests/test_plot_a2_certification.py::test_policy_generation_key_sets_are_independent_exact_literals`
- N6 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_rejects_unknown_content_with_the_same_six_keys`
- N7 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_still_rejects_nonbound_source_binding_status`
- N8 = `orchestrator/tests/test_plot_a2_certification.py::test_current_rejects_nonbound_source_binding_status`
- N9 = `orchestrator/tests/test_plot_a2_certification.py::test_historical_policy_loader_rejects_unknown_or_non_string_generation[unknown-string]`

N3 を含む集合は、t2364 root が完全に存在するという裁定上の前提である。root 不在なら N3 は skip、部分欠損なら baseline から failure となる。

| 変異 | 置換位置の一意性 | 狙う nodeid | 期待する KILLED node の完全集合 | 帰属 |
|---|---|---|---|---|
| M1: cert hash を主 key から外す | 可。C:209-210 の lookup で pair 表を policy hash に射影する一箇所変異 | N1 | {N1} | 可。certification bytes だけが変わり、policy bytes と policy hash は維持される。M1 なら歴史 loader が選ばれて最後まで通り、N1 が例外不足で赤になる |
| M2: policy hash を主 key から外す | 可。C:209-210 の lookup で pair 表を cert hash に射影する一箇所変異 | N2 | {N2} | 可。fixture は変更後 cert hash と旧 policy hash の pair を登録する。M2 なら改行だけ増えた policy が歴史文法で受理され、N2 が例外不足で赤になる |
| M3: consumer の世代受け渡しを消す | 不可。C:214-215 と C:178-181 の二箇所 | N3 | どちらの一箇所変異でも {N3, N4, N7} | 挙動としては KILLED だが位置帰属は不可。N7 は先行する current key 検査の異なる例外で赤になる |
| M4: 旧 key 集合を current と同一にする | 可。P:146-150 の historical literal 一箇所 | N3 | {N5, N3, N4, N7} | 可。N3 と N4 は欠落した FetchContent key で落ち、N5 は literal 差分で落ちる。N7 は source gate より前の key 検査で赤になる |
| M5: 未知世代を current へ fallback | 可。P:394-399 の世代解決 gate 一箇所 | N9 | {N9} | 可。ただし `[non-string]` case は P:391-393 の exact-type gate が維持されるため SURVIVED が正しい |
| M6: historical のときだけ tracked 検査を外す | 不可。P:436-438 は一箇所だが generation が到達していない | N6 | 登録どおりの一箇所変異は定義不能。最寄りの共有 gate 削除なら {N6} | 不可。最寄り変異は current の受理集合まで広げる。実効 gate へ再照準が必要 |
| M7: historical のときだけ source binding 後段検査を外す | 不可。C:233-234 と C:432-433 の二箇所 | N7 | 各一箇所変異は空集合。二箇所を無条件削除すれば {N7, N8} | 不可。現状の期待 KILLED は誤りで、M7 は SURVIVED |
| M8: 旧 key 集合から `toolchain_arguments` を落とす | 可。P:146-150 の historical literal 一箇所 | N3 | {N5, N3, N4, N7} | 可。N3 と N4 は余分な `toolchain_arguments` で落ちる。N7 は source gate より前の key 検査で赤になる |

## 読解で予測する赤

これは読解であって実測ではない。pytest は実行していない。

実装差分そのものによって赤になる既存 nodeid は、指定された三 suite では予測しない。

- `orchestrator/tests/test_paper_story_a2_certification.py`: 公開 `load_policy(path=POLICY_PATH)` の署名は P:384 のままで、current key 集合と FetchContent 値検査も実効上不変である。`test_policy_is_the_exact_literal_four_cell_protocol`、`test_p1_a2_default_policy_bytes_and_protocol_are_unchanged`、`test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list`、A-6 policy tests は赤を予測しない。
- `orchestrator/tests/test_paper_story_a2_job_contract.py`: fixture adapter は `load_fixture_policy(path=a2.POLICY_PATH)` で path-only 呼出を維持している。公開 loader に世代引数が追加されていないため、既存 nodeid の赤を予測しない。
- `orchestrator/tests/test_plot_a2_certification.py`: 既存名を保った historical 正例・負例は新しい世代表に合わせて更新されており、実装差分による赤を予測しない。N3 は新規 nodeid であり、root 不在時の skip と部分欠損時の failure は意図した挙動である。

変異を適用した場合に予測する赤は、上の帰属表の完全集合どおりである。特に M7 の一箇所変異では赤が一件もなく、ここが受入不能点である。

## 裁定からの逸脱

- M3 は裁定表の「C の historical 分岐」という単一位置になっていない。consumer branch と helper-to-producer の二段の受け渡しがある。
- M6 は裁定表の「歴史世代のときだけ」という条件を実装上の一箇所へ置けない。対象 gate まで generation が保持されていない。
- M7 は裁定の期待 `KILLED` を満たさない。同一入力を拒否する gate が二つあり、どちらか一方を外す変異は生存する。
- 上記以外の機能プランからの逸脱は認めない。二つの独立 `frozenset` literal、path-only 公開 loader、exact-type と未知世代拒否、pair key、完全 producer grammar、override なし t2364 統合は裁定どおりである。
- 「触らない」対象への逸脱はない。差分は指定三ファイルだけで、shipped policy、`Policy` dataclass、`_protocol_preimage`、`CANONICAL_SHA256` の hash 値、figure/provenance、producer 内部の path-only `load_policy` 呼出を変更していない。
- test の改名もなく、docs に残る既存参照は有効である。

## 総括

機能実装は裁定の policy 世代選択と実 t2364 本番境界を満たしており、override や揮発期待値もない。  
ただし M7 は単一変異で殺せず blocker、M3 と M6 も置換位置を一意に帰属できない。  
既存三 suite に実装差分由来の赤は読解上予測しないが、これは実測結果ではない。  
M3 の分割、M6 の実効 gate 再登録、M7 の直接単一理由テスト化が受入前に必要である。