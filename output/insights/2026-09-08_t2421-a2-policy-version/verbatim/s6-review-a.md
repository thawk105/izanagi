## 所見

[RA-1] 独立 literal のテストは、実際に有効な定義が後から差し替えられても通る。

- 主張: 現実装の旧世代集合自体は独立した `frozenset` literal だが、その回帰テストは最初の代入しか検査せず、「有効な定義が独立 literal」という保証になっていない。
- 根拠: `paper_story_a2_certification.py:139` は現在、`_TRACE0_CONFIGURE_ARGV_KEYS_BY_POLICY_GENERATION = {` と正しく定義している。一方、`test_plot_a2_certification.py:564` は `assignment = next(`、同 `:591` は `assert literal_values == [current, historical]` であり、二つ目以降の再代入や table 要素の上書きを調べない。
- 具体的な破れ方: 現在の literal 定義を残した後で、同名を現行集合との差分式で再代入すれば、AST 検査は最初の未使用定義を読み、runtime の値比較も同値なので通る。たとえば旧世代を `_TRACE0_CONFIGURE_ARGV_KEYS - {"fetchcontent_path_argument_prefixes"}` から再構成しても検出できない。
- 深刻度: must-fix
- 最小の直し方: 対象名への module-level 代入が一つだけであることを assert し、同名への再代入、subscript 代入、`update` などの後続変更も拒否する。その唯一の代入の二つの値が直接の `frozenset({文字列 literal})` であることを検査する。

[RA-2] 公開 loader の新規回帰テストは、署名以外の公開契約を固定していない。

- 主張: 静的差分上、公開 `load_policy` の受理集合、検査順序、例外、戻り値は維持されている。しかし追加テストは署名だけで、依頼にある例外型・文言・順序と `Policy` 全 field の不変を検知しない。
- 根拠: `test_plot_a2_certification.py:594-600` は `inspect.signature`、引数名、kind、既定値しか検査していない。変更後本体は `paper_story_a2_certification.py:384-386` の `return _load_policy_with_configure_argv_keys(path, configure_argv_keys=_TRACE0_CONFIGURE_ARGV_KEYS)` である。
- 具体的な破れ方: wrapper が返却後に `Policy.path`、`raw_bytes`、`bytes_sha256` のいずれかを変更しても、この署名テストは通る。特定の malformed policy に対する検査順序や例外文言を wrapper 側で変えても同様である。
- 深刻度: nit
- 最小の直し方: shipped policy に対して `Policy` の六 field を固定する正例と、検査順序が競合する malformed policy 数件について exact な例外型・全文を固定する負例を追加する。

静的な境界照合そのものでは、公開 API の破れは見つからなかった。署名と既定値は同一で、現行集合による `_exact_keys` が先に成功しない限り追加された条件分岐へ到達せず、成功時は FetchContent 検査が必ず従来どおり実行される。`Policy(path, document, raw_bytes, bytes_sha256, protocol_sha256, cells)` の構築も `paper_story_a2_certification.py:634-640` で旧本体と同一である。

歴史 loader の呼び手は、射影された production code では `plot_a2_certification.py:180-181` の一件だけである。テストからは `test_plot_a2_certification.py:613-614` が未知・非文字列世代で直接呼ぶが、戻り値には到達しない。得られた歴史 `Policy` は plot 内で identity、cell、workload、condition receipt の検証に使われ、`plot_a2_certification.py:374-376` から producer の `_parse_condition_gate_admissions` に渡る。ただし `collect_results`、`preregister_attempt`、`validate_trace0_evidence`、CLI command など producer の実行・生成経路へ流す caller はない。

旧世代集合は `paper_story_a2_certification.py:146-150` の独立 literal であり、現行集合、集合演算、comprehension、共有 `frozenset` の別名を参照していない。公開 `load_policy` から世代引数へ到達する経路もない。

既存期待値では `test_historical_rejects_unknown_content_with_the_same_six_keys` の理由が FetchContent 欠落から不正 `tracked_destination` へ変更された。ただし未登録 policy hash の境界は `test_historical_rejects_unknown_bytes_with_the_same_v2_version` に移されており、実 t2364 正例は `expected_hashes` override なしで実体を読む。canonical hash 値の変更、fixture への現行 hash 差し込み、producer loader の stub 化は差分にない。

## 削除された検査の対応表

| 旧検査 | 旧コードの逐語 | 新実装の対応 | 判定 |
|---|---|---|---|
| certification の protocol pair | `impl.diff:515-520` の `"historical certification protocol assertion failed"` | `plot_a2_certification.py:143-145` が実 certification SHA を pin に照合し、`:209-215` が exact cert/policy pair で世代を選び、`:219-222` が `protocol_schema` と再計算済み `policy.protocol_sha256` を照合する | production の `load_measurements` 経路では覆う |
| policy root と schema | `impl.diff:447-450` の `"historical embedded policy schema assertion failed"` | `paper_story_a2_certification.py:411-416` の `_loads_json`、`_exact_keys`、`document["schema_version"] != POLICY_SCHEMA` | 覆う。型と top-level key も旧実装より強い |
| configure object と六 key | `impl.diff:451-454` の `"historical trace0 configure key assertion failed"` | `paper_story_a2_certification.py:146-150` の旧世代 literal と `:488-490` の `_exact_keys` | 覆う |
| protocol preimage の固定 hash | `impl.diff:455-459` の `"historical embedded policy protocol assertion failed"` | `paper_story_a2_certification.py:639` で再計算し、`plot_a2_certification.py:221-222` で certification 値と照合する。certification 値自体は exact certification SHA pin に包含される | production 経路では推移的に覆う |
| `performance_common`、workload、cell の必須形 | `impl.diff:461-490` の `"historical embedded policy view is malformed"` | `paper_story_a2_certification.py:453-632` の完全 loader。exact key、件数、型、role pair、genome、perf projection を検査する | 旧検査以上に覆う |
| `Policy.raw_bytes` と `bytes_sha256` | `impl.diff:493-496` の `raw_bytes=raw`、`bytes_sha256=raw_sha256` | `paper_story_a2_certification.py:637-639`。さらに consumer が `plot_a2_certification.py:199-202` で embedded hash を先に照合する | 覆う |
| `Policy.cells` の組み立て | `impl.diff:467-487` の `CellSpec(...)` | `paper_story_a2_certification.py:566-640` | 覆う。label、role、genome、perf の値は同じ |
| 歴史 policy の path | `impl.diff:492` の `Path("<historical-embedded-policy>")` | `paper_story_a2_certification.py:635` の一時 file の resolved path | assert ではない。値は変わり、一時 file 削除後は存在しないが、現 plot 経路は参照しない |

削除された拒否検査に、現 production 経路で未被覆のものはない。protocol pin の同値性だけは、private `_load_current_policy` を不正な SHA 引数で直接呼ばず、`load_measurements` が実 bytes の SHA を渡すという呼出契約に依存する。

## 恒真な assert

- `test_plot_a2_certification.py:640` の `assert data["measurement_conditions"]["artifact_profile"] == "current-full"` は、`:626` で `_profile(...) == "current-full"` の entry だけを列挙し、consumer `:589-590` が同じ literal を設定するため、正常 return 後は恒真である。
- 同 `:642` の `assert len(data["external_inputs"]) == 12` は、consumer `plot_a2_certification.py:273-275` と `:313-314` が current-full の exact 12-file closure を先に強制するため、正常 return 後は独立した保証にならない。
- 同 `:643-646` の `authority_matches is True` は、consumer `plot_a2_certification.py:596` が検証結果にかかわらず成功時の各 rowへ literal `True` を書くため、完全に恒真である。
- 同 `:695` の schema assert は、helper が v2 document を作り、変異が末尾改行追加だけなので setup の再確認にとどまる。
- 同 `:712-716` の六 key assert は、helper `:352-354` が FetchContent key だけを削除した直後に、無関係な `tracked_destination` だけを変えて確認している。system under test の保証ではない。

歴史分岐が発火しないテストは次のとおりである。

- `test_historical_rejects_changed_embedded_policy_hash` は `policy_sha256` を `"0" * 64` にするため、`plot_a2_certification.py:199-202` の embedded SHA 検査で registry lookup 前に止まる。
- `test_historical_rejects_changed_certification_bytes` は certification SHA 成分を外して current loader に落とし、FetchContent key 欠落で止まる。
- `test_historical_rejects_unknown_bytes_with_the_same_v2_version` は registry の policy SHA 成分を意図的に旧 hash のままにし、current loader に落として FetchContent key 欠落で止まる。これは M2 用の lookup 境界テストであり、歴史文法テストではない。

一方、`test_historical_still_rejects_nonbound_source_binding_status` は偽陽性ではない。変更後 certification と policy の exact pair を `test_plot_a2_certification.py:727-732` で再登録するため歴史 loader を通る。producer の `_validate_certification_cells` は `paper_story_a2_certification.py:4412-4425` で `"token-mismatch"` を既知 status として受理し、その後 `plot_a2_certification.py:233-234` の `"current certification source_binding_status is not bound"` で落ちる。したがって、歴史世代を選択したまま後段検査を発火させている。

## 裁定パッケージ候補

- 歴史 `Policy` は通常の `Policy` と型上区別されず、producer の全 `Policy` 引数へ手動で渡せる。現在の caller は plot だけだが、実行系の `_exact_trace0_configure_argv` は `paper_story_a2_certification.py:2232-2235` で旧文法に存在しない `fetchcontent_path_argument_prefixes` を無条件参照し、到達すれば `CertificationError` ではなく `KeyError` になる。
- 歴史 `Policy.path` は `plot_a2_certification.py:168-187` が削除する一時 file を指す。現 consumer は未使用だが、同じ `Policy` を path authority として扱う consumer には安全に再利用できない。
- 世代化されているのは configure key 集合だけである。`POLICY_SCHEMA`、top-level keys、値制約、`_protocol_preimage` は共有され、将来の締め付けで exact t2364 pairが再び読めなくなる。
- 歴史世代で読んだ結果も `artifact_profile="current-full"` として返り、provenance に policy generation は残らない。ただし同じ figure 経路は削除前 adapter にも存在したため、本差分が新設した絶対規律 7 違反とは判定しない。機械可読な区別を必要とするなら別裁定が要る。

## 総括

現実装に、公開 `load_policy` の受理集合・例外契約・戻り値を変える差分は見つからなかった。  
旧世代集合は現時点では独立 literal で、歴史 `Policy` の production caller は plot 一本に閉じている。  
削除された検査は production の hash-bound 経路では完全 loader と後段 identity 検査により覆われる。  
ただし最重要の独立 literal 回帰テストは後続再定義で迂回できるため、[RA-1] は must-fix である。  
M7 の負例は歴史世代を実際に選択してから、狙った後段 message で失敗している。