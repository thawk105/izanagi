## 現状の実測

- 裁定上の残件は D901 条項 2・3 であり、既存台帳への遡及は禁止されている。`brief.md:12-15,55-70`、`rulings-verbatim.md:25-45,51-68,78-88`。
- `orchestrator/campaign/backoff_hole_grammar.py:9-13` は 13 段の公開判定順を固定している。拒否は `:76-140` の固定 rule/reason、候補由来 bytes を出さない契約は `:15-19`。
- `_cpp_number_value()` は `orchestrator/campaign/backoff_hole_grammar.py:290-335` で十進浮動・十六進浮動・二/八/十六進整数を値へ畳む。`attribution_numeric_literals():452-491` は値だけを返し、元 token の正準表記は返さない。
- `validate_backoff_implementation():576-709` は suffix-free literal を受理するが表記を限定しない。現在のテストも `20`、`20.0`、`1e2`、`0x14`、`024`、`0b10100` 等を同時に受理している (`orchestrator/tests/test_p3_s4_loop.py:332-352,492-507`)。
- `quarantine()` は raw implementation を `render_hole()` し (`orchestrator/campaign/p3_s4_loop.py:275-290`)、全 gate 通過後その `edited_text` をそのまま書く (`:321-333`)。ここが現在、別表記を別 source bytes にする点。
- campaign identity は `default_cfg():898-928` の `search_config` を、`ident.canonical_preimage():196-223` が丸ごと正準 JSON 化している。したがって backoff 専用 key の注入に `ident.py` の汎用 schema 改変は不要。
- variant/source identity は `source_digest.canonical_source_preimage_bytes():1977-1991` の materialized source bytesを覆い、`compute():1994-2003` で SHA-256 にする。非-stock token は `src_token():2108-2117`、`resolve_evidence():2195-2235` で確定する。
- legacy cache pre-image は `buildcache.cache_key():618-636` の `src`、v2 は `_v2_identity():1289-1373` の `src_token` に source identity を含む。stock は legacy key から `src` 自体を省く (`:631-634`)。
- WAL の top-level schema は `wal.parse_line():351-393` の5キー固定だが、`payload` は JSON-native object として拡張可能。書込みの単一合流点は `_append_record():617-768`、糖衣は `log():963-970`。
- reject WAL の `BUILD_START` は `p3_s4_loop.record_diff_reject():376-398` が `genome`、`src_token`、`build_attempt_id` を記録する。通常 build も critic 側では同じ `BUILD_START.payload.genome/src_token` を読む (`orchestrator/critic/digest.py:761-780`)。
- `orchestrator/codex_roles/policy.py:485-513` は dormant adapter の受理・値一致検査に留まり、production producer は `p3_s4_loop`。`critic/digest.py` は `src_token` を opaque identity として扱うため、両ファイルに正準化ロジックを褤製する必要はない。
- 先例の `sort_swo_oracle.py:47-51,2573-2580` は全体文法版と個別 checker/contract 版を独立に持ち、identity 文字列へ `grammar{GRAMMAR_VERSION}` を明示的に織り込んでいる。
- 実測は静的読取のみ。書込み・pytest は行っていない。

## P1 の評価

採用。ただし「既存 genome」を次のように限定する。

- `p3_s4_loop.default_cfg():906-925` にだけ `backoff_grammar_version` を加える。sort/trigger の `default_cfg` や汎用 `ident.canonical_preimage()` には条件分岐を入れない。
- `source_digest` の版束縛は、`current != baseline` かつ tracked path に `include/backoff.hh` がある場合だけ行う。同ファイルが現在の backoff loop の単一駆動面であることは `source_digest.py:79-82` に明記されている。
- `src_token == STOCK` は従来どおり `"stock"`。したがって stock cache key、stock variant ID、既存 stock genome は不変。
- backoff 以外の非-stock token も従来の raw source digest のままにする。
- 一方、版導入前の非-stock backoff cache entry は再利用してはならない。ここまで「既存 genome の温存」に含める解釈は D901 条項 2 と衝突するため不採用。entry は削除せず残すが、新しい version-bound key からは到達不能にする。

## P2 の評価

そのままでは不採用。代案は「受理後・書込み直前の canonical materialization」。

`BUILD_START` に `"20"` を加えるだけでは、raw hole source が `20`、`0x14`、`2e1`、`20.0` のまま残る。すると `source_digest.py:1977-2003` が別 digest を作り、variant ID と `buildcache.py:631-634` の cache key も分裂したままである。D901 の「certified 選択の母集合から重複を除く」目的を達成できない。

推奨する正準形は次のとおり。

- production 値域は既存の lossless integer `1..1000` (`backoff_hole_grammar.py:712-727`)。
- 正準 numeric token は ASCII の基数10整数。
- 符号、先頭ゼロ、桁区切り、基数 prefix、小数点、指数、suffix は持たない。
- よって `20`、`0x14`、`2e1`、`20.0` はすべて `"20"`。
- materialized hole は固定して `double now_backoff = 20;`。
- canonical source から既存 `source_digest` が `source_bytes_sha256/src_token` を作り、WAL は既存の `genome` (`BACKOFF_FIXED=20`) と `src_token` にその同一性を記録する。raw literal を新しい WAL field として重複保存しない。

正準化は raw candidate が既存13段すべてを通過した後だけ行う。拒否 candidate は一切書き換えず、従来と同じ rule/reason を返す。したがって受理集合は増減せず、判定順も変わらない。

「source_digest が動いて identity が二重に変わる」点は欠陥ではない。canonical source への収束は条項3、grammar version による domain separation は条項2であり、独立に要求された二軸である。

## P3 の評価

採用。

- `BACKOFF_GRAMMAR_VERSION = 1` と共有 key `"backoff_grammar_version"` は `orchestrator/campaign/backoff_hole_grammar.py:30-46` 付近へ置く。
- `_REJECTIONS` の `backoff-grammar.*.v1` は個別拒否規則の版、`BACKOFF_GRAMMAR_VERSION` は受理集合・判定意味・canonical materialization 全体の版とする。
- grammar version を上げても、個別規則が変わらない限り固定 rule ID/reason bytes は変えない。
- 受理集合、判定意味、または数値正準形のどれかが変わる場合は grammar version を上げる。内部リファクタだけなら上げない。

## 実装プラン

1. `orchestrator/campaign/backoff_hole_grammar.py:30-46,284-335`

   - `BACKOFF_GRAMMAR_VERSION = 1` と `BACKOFF_GRAMMAR_VERSION_KEY = "backoff_grammar_version"` を追加し `__all__` へ公開する。
   - `_cpp_number_value()` を唯一の値解釈器として使う `canonicalize_backoff_implementation()` を追加する。
   - helper はまず既存 `validate_backoff_implementation()` の結果を要求し、不受理なら既存 `BackoffGrammarViolation` の固定 bytes で停止する。
   - lossless integer の production 値は `str(int(value))` とし、固定1文 `double now_backoff = <token>;` を返す。grammar 単体では受理されるが production 値域外の literal は新しい rejection にせず、既存表記を維持する。
   - `_REJECTIONS`、13段、`BackoffGrammarDecision` の schema は変更しない。

2. `orchestrator/campaign/p3_s4_loop.py:321-333`

   - raw `edited_text` に対する structural gate、host-effect gate、backoff grammar gate の現行順を維持する。
   - `decision.accepted` が確定した後だけ、backoff marker に対して `canonicalize_backoff_implementation()` を呼ぶ。
   - canonical implementation で `edited_text` と `working_diff` を再生成し、それを返却・書込みする。sort/trigger marker は現状どおり。
   - rejected path は raw implementation のまま `_backoff_grammar_rejection()` へ流し、候補 literal を投影しない。

3. `orchestrator/campaign/p3_s4_loop.py:368-373`

   - `diffq_variant_id()` の SHA-256 pre-imageを `genome.canonical() | backoff_grammar_version=<n> | impl=<raw>` にする。
   - rejected candidate も「どの文法で拒否されたか」を identity に持つ。raw implementation は引き続き hash pre-image 内だけで、WAL/public reason へ出さない。

4. `orchestrator/campaign/p3_s4_loop.py:898-928`

   - backoff loop の `search_config` にだけ  
     `"backoff_grammar_version": backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION`  
     を追加する。
   - `ident.canonical_preimage():212-223` が既存どおりこの key を campaign lock、cfg hash、campaign IDへ束縛するため、`ident.py` は編集しない。
   - sort/trigger config には追加しない。

5. `orchestrator/campaign/source_digest.py:63-71,98-101,1839-1845`

   - `backoff_hole_grammar` を import し、exact path `include/backoff.hh` を backoff binding 対象として定数化する。
   - private helper `_bind_backoff_grammar_version(raw_digest, tracked_paths)` を追加する。
   - backoff path が dirty のときだけ、例えば  
     `b"backoff-src-token/v1\0grammar=" + ascii(version) + b"\0source=" + ascii(raw_digest)`  
     の SHA-256 を返す。
   - raw source digest 自体を pre-image に残すため、hole 外改変や別コードが同じ numeric valueへ alias することはない。

6. `orchestrator/campaign/source_digest.py:2108-2117,2195-2235,2238-2250`

   - `current == baseline` は最優先で `STOCK` を返す。
   - 非-stock では、捕捉済み `tracked_paths` を上記 helper に渡す。`resolve_evidence()` では `source_bytes_sha256=current` を維持し、`src_token` だけを version-bound token にする。
   - `resolve()` も同じ helper を通し、`resolve()` と `resolve_evidence()` が異なる token を返さないよう単一 private producer を共有する。
   - `SourceEvidence` の key 集合・schema versionは変えない。既存 receipt consumer への互換層追加は不要。

7. `orchestrator/campaign/buildcache.py:618-636,1289-1373`

   - pre-image schema は変更しない。
   - legacy cache は既存 `src=<version-bound-token>`、v2 は既存 `"src_token": <version-bound-token>` で版を束縛する。
   - `src_token == STOCK` の省略規則はそのまま維持する。
   - 実コード変更は docstringで version-bound token を明記する程度に留め、別の `grammar_version` 引数・互換 fallback・旧key探索を足さない。

8. `orchestrator/campaign/wal.py:38-60,487-540,617-646`

   - versioned lock の `identity.search_config.backoff_grammar_version` を読む helper を追加する。値は lock に記録された exact positive integerを使い、現在の定数から遡及推測しない。
   - `_append_record()` の lock snapshot 対象を `BUILD_START` にも広げる。
   - versioned lock 配下の `BUILD_START.payload` にだけ  
     `"backoff_grammar_version": <lock-declared int>`  
     を条件付き追加する。既存値が異なれば固定内部例外で停止する。
   - top-level WAL schema は不変。後続 stage は `build_attempt_id` でその `BUILD_START` に束縛されるため、全 payload への重複コピーはしない。
   - lock無し、または version key無しの legacy append は payload bytesを変更しない。

9. `orchestrator/campaign/wal.py:1377-1462,2087-2155,2178-2201`

   - `validate_backoff_grammar_bindings(records, campaign_lock=...)` を追加する。
   - lock に version key が無ければ即 returnし、旧 WAL を受理する。
   - version key がある場合、全 `BUILD_START` に同じ exact integerが必要。欠落・別値は `AttemptTopologyError`。
   - replay、tail repair、interrupted-attempt recovery、`records_by_stage()` から呼ぶ。`p3_s4_loop._duplicate_snapshot():1034-1073` も commit/trigger binding 検査と並べて呼び、duplicate 復元で迂回させない。
   - 既存 WAL への backfill は行わない。

10. 非編集面

   - `orchestrator/campaign/ident.py`: `search_config` を既に正準 pre-imageへ含めるため変更不要。
   - `orchestrator/codex_roles/policy.py`: dormant validator は raw candidate の受理確認だけを続け、materialization producerにしない。
   - `orchestrator/critic/digest.py`: canonical `src_token` を既に opaque に消費するため変更不要。
   - repo docs/worklog/decision の完了記録は親が担当し、実装子は上記コードとテストだけを編集する。

## テスト計画

- `orchestrator/tests/test_p3_s4_loop.py:332-352`

  `20`、`0x14`、`2e1`、`20.0` が引き続きすべて admission passし、canonical resultが完全一致するテストを追加する。canonicalizerを `int(token)` のように基数無視で実装する変異、`repr(float)` で `20.0` を残す変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:212-247`

  `quarantine(write=False/True)` を四表記で回し、返却 `edited_text`、`working_diff`、実ファイル bytes が同じ `double now_backoff = 20;` になることを固定する。helperを追加しただけで materialization に配線し忘れる変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:454-489,618-767,4630-4686`

  既存 rule-order corpusを維持し、rejected candidateでは canonicalizer が呼ばれない spy を追加する。canonicalizationを validatorより前に動かす変異、拒否を受理へ変える変異、rule IDを grammar versionへ連動させる変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:129-138,1293-1412,2258-2330`

  versioned lockを先に seedした production-shaped rejectでは `BUILD_START.payload` に version fieldが1個だけ入り、ABORTには重複しないよう期待 key 集合を改訂する。

- `orchestrator/tests/test_p3_s4_loop.py:1349-1412`

  現在の lock無し legacy WAL exact-byte テストは維持する。version key無しの lockでも同じ payloadを読めるケースを追加し、旧 WAL への遡及要求・無条件 field injectionを殺す。

- `orchestrator/tests/test_p3_s4_loop.py:1293` 付近

  versioned lockに対し version field欠落・異値の `BUILD_START` を `validate_backoff_grammar_bindings()` が拒否し、version key無しの legacy lockでは欠落を許す三分岐テストを追加する。writerだけ実装してreader検査を落とす変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:2041-2049`

  `diffq_variant_id()` が同一 versionでは決定的、versionを1だけ変えると別IDになるテストへ改訂する。accepted variantだけ版を束縛し reject identityを忘れる変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:2226-2255`

  base `default_cfg` に exact version keyがあり、sort/triggerには無いことを追加する。versionを変えた configで `canonical_preimage`、campaign ID、layoutが変わることも固定する。全 campaignへの無条件注入と identity注入漏れを殺す。

- `orchestrator/tests/test_p3_s4_loop.py:2952-2974`

  base on/off の hard-coded campaign ID goldenを新しい versioned IDへ更新する。期待値は実装から自己導出せず literalで固定する。

- `orchestrator/tests/test_p3_s4_loop.py:2041` 付近に source/cache blockを追加

  同じ canonical source digest＋同じ versionは同じ `src_token/cache_key`、version変更は両方を変える、`STOCK` と非-backoff sourceは変えないことを検査する。source tokenだけ変えて cache pre-imageから落とす変異、stockまで壊す変異を殺す。

- `orchestrator/tests/test_p3_s4_loop.py:1034-1073,5177` 周辺

  version field欠落の versioned duplicate WALを `_duplicate_snapshot()` が拒否し、正しい fieldなら復元するテストを追加する。通常 replayだけに validatorを配線し duplicate readerを忘れる変異を殺す。

## 負例と変異候補

現行テストが緑のままになり得る重要な変異は次のとおり。

- `BACKOFF_GRAMMAR_VERSION` を定義するだけで `default_cfg` に入れない。現行 identity テスト `:2226-2255` は reflux差しか見ない。
- campaign IDだけ変え、source token/cache keyを版束縛しない。現行 test fileには grammar versionと cacheを組み合わせる検査がない。
- WAL fieldを足さない、または ABORT/COMMITだけに足す。`:1349-1412` は意図的に lock無し legacy bytesしか固定していない。
- WAL writerがfieldを足すが、versioned lock＋field欠落の既存 bytesをreaderが許す。正常writer E2Eだけでは検出できない。
- canonical helperを単体実装するが `quarantine()` の最終 `edited_text` に使わない。現行 `:332-352` は admissionしか検査しない。
- raw sourceを残したまま、WALへ `"20"` を加えただけで完了とする。WAL表示は正しく見えても variant/cacheが四分裂する。
- version-bound tokenから raw source digestを落とし、同じ `BACKOFF_FIXED` の異なる不正 sourceをaliasさせる。
- backoff path条件を落として全非-stock sourceへ版を付ける。backoffテストだけでは sort/trigger cache churnを検出できない。
- `STOCK` にも版を足して既存 cache keyを壊す。新規backoff campaignだけのテストでは見逃し得る。
- grammar versionを上げるたび `backoff-grammar.*.v1` まで変更する。個別固定 bytesの意味と全体版が混同される。
- canonicalizationを13段より前へ動かし、現在拒否される literalや追加文を正規化で消して受理する。既存順序テストに canonicalizer非呼出し検査が無ければ偽KILLになり得る。

## 残るリスクと未決

- 親の裁定が必要な主点は P2。推奨は「accepted hole の canonical materialization」。単なる additive WAL field案は source/variant/cacheの重複を残すため却下する。
- P1を「campaign設定による明示的な型付け」にまで厳密化する場合、現射影には `cfg` を `source_digest/buildcache` へ渡す seamがない。その解釈なら `include/backoff.hh` の exact path判定で代用せず、親が `loop.py/pipeline.py` を追加射影して再計画すべきである。
- 現行 `source_digest.py:79-82` の「backoff loopは backoff.hh単一駆動面」を正本とするなら、path条件が最小実装であり推奨。
- grammar単体が受理する非整数 literalの正準形は本題外。productionの既存 `1..1000` lossless integer契約だけを十進整数へ畳み、非整数の受理・拒否挙動は変えない。

## 総括

- P1は stock・非backoffを不変にする条件付きで採用し、pre-versionの非-stock backoff cache再利用は認めない。
- P2は否定し、13段通過後の source materializationを `double now_backoff = 20;` へ正準化する。
- P3は採用し、全体文法版を個別 `.v1` rule IDから分離する。
- identityは campaign configとversion-bound `src_token`、WALは `BUILD_START.payload`、cacheは既存 `src/src_token` fieldで束縛する。
- 最も割れやすい点は、P1の「backoff campaignだけ」を `include/backoff.hh` のpath条件で十分に表せるかである。