## 変更点一覧

repo 全体の静的検索では、過去の WAL・ブロック記録を現行 `analysis_commit` と比較して拒否する経路は brief の 3 経路で全部だった。`analysis_commit` の実行コード上の参照は対象 2 ファイルに閉じ、追加の歴史的 consumer はない。

`orchestrator/campaign/b10_backoff_shape_sweep.py:470-472` と `tools/pegasus/b10_backoff_shape_campaign.sh:155-187` にも現行 HEAD 照合はあるが、これは投入 receipt と実際に実行する checkout の対応づけであり、過去 WAL・ブロック記録の無効化ではない。新 HEAD から新しい receipt を投入すれば通るため、除去対象には加えない。`prereg_commit` の祖先検査 `orchestrator/campaign/b10_backoff_shape_sweep.py:1348-1354` も事前登録との束縛なので残す。

- `orchestrator/campaign/b10_backoff_shape_sweep.py:213-222`

  現行コードの逐語:

  ```python
  "formula_sha256": self.formula_sha256,
  "analysis_commit": self.analysis_commit,
  "analysis_code_sha256": self.analysis_code_sha256,
  ```

  変更後の逐語:

  ```python
  "formula_sha256": self.formula_sha256,
  "analysis_code_sha256": self.analysis_code_sha256,
  ```

  `analysis_commit` が違うだけで `core()`、`binding_sha256`、`as_dict()` が変わり、campaign.lock、BUILD_START、build-admission commitment、ブロック記録の完全一致検査が拒否する条件を除去する。dataclass field `analysis_commit`、その形式検査、現行 HEAD の記録は残す。

- `orchestrator/campaign/b10_backoff_shape_sweep.py:2384-2388`

  現行コードの逐語:

  ```python
  or row.get("spec_sha256") != prereg.spec.spec_sha256 \
  or row.get("analysis_commit") != prereg.binding.analysis_commit \
  or row.get("analysis_code_sha256") != prereg.binding.analysis_code_sha256 \
  ```

  変更後の逐語:

  ```python
  or row.get("spec_sha256") != prereg.spec.spec_sha256 \
  or row.get("analysis_code_sha256") != prereg.binding.analysis_code_sha256 \
  ```

  過去 row の `analysis_commit` が記録時 HEAD、`prereg.binding.analysis_commit` が再開時 HEAD であることだけを理由に、内容ハッシュ一致のブロック記録を `resume-binding` で拒否する条件を除去する。直後の `analysis_code_sha256` 比較は残す。

- `orchestrator/campaign/b10_backoff_shape_sweep.py:2387-2389`

  現行コードの逐語:

  ```python
  or row.get("analysis_code_sha256") != prereg.binding.analysis_code_sha256 \
  or row.get("source_commit") != prereg.binding.analysis_commit \
  or type(request_id) is not str or not request_id \
  ```

  変更後の逐語:

  ```python
  or row.get("analysis_code_sha256") != prereg.binding.analysis_code_sha256 \
  or type(request_id) is not str or not request_id \
  ```

  投入時 HEAD を記録した過去 row の `source_commit` が再開時 HEAD と違うだけで拒否する条件を除去する。`source_commit` 自体のブロック記録 `orchestrator/campaign/b10_backoff_shape_sweep.py:3021` は残す。

変更しない重要箇所は、`analysis_commit` field と形式検査 `orchestrator/campaign/b10_backoff_shape_sweep.py:191-211`、現行 HEAD の記録 `orchestrator/campaign/b10_backoff_shape_sweep.py:1387-1395`、解析 bytes と現行 HEAD blob の照合 `orchestrator/campaign/b10_backoff_shape_sweep.py:1378-1385`、レポート行 `orchestrator/campaign/b10_backoff_shape_sweep.py:2655`、ブロック記録 `orchestrator/campaign/b10_backoff_shape_sweep.py:3030` である。correctness gate と凍結事前登録文書には触れない。

## 波及

- `PreregistrationBinding.core()` と `as_dict()`:

  `orchestrator/campaign/b10_backoff_shape_sweep.py:213-229` の `core()` から `analysis_commit` が消え、`as_dict()` も同 field を含まなくなる。`prereg_commit`、`prereg_blob_sha`、`spec_sha256`、`patch_sha256`、`formula_sha256`、`analysis_code_sha256` はすべて残る。

  直接 consumer は、config への格納 `:1478`、campaign.lock 比較 `:1565-1567`、BUILD_START 比較 `:1573-1585`、BUILD_START 記録 `:1602-1610`、過去ブロック束縛比較 `:2384`、JSON provenance の束縛投影 `:2598-2601`、ブロック記録 `:3028` である。

  テスト側の既存 consumer は `orchestrator/tests/test_b10_backoff_shape_sweep.py:381`、`:814-820`、`:1384`、`:1453`。いずれも計算値との比較であり、固定 schema key 数や固定 digest を期待していない。

- `binding_sha256`:

  `orchestrator/campaign/b10_backoff_shape_sweep.py:224-226` の値が変わる。現行 fixture では旧計算が `642fe6eae6eabb1b874cabd33b8e7e2142a4966c161cb552017248ac0d1fd68a`、`analysis_commit` 除外後が `a55d9594f908131b66ee40d8dcd8386620d97a51b2e7a2a2ae3647f12acf49cc` となる。後者は `analysis_commit` が `ffffffffffffffffffffffffffffffffffffffff` でも `cccccccccccccccccccccccccccccccccccccccc` でも同値になる。

  直接 consumer は、BUILD_START の `input_sha256` 照合 `orchestrator/campaign/b10_backoff_shape_sweep.py:1581-1585`、generator input `:2490-2494` と `:2509-2517`、Markdown レポート `:2653`、report directory 名 `:3064-3067`。テスト consumer は `orchestrator/tests/test_b10_backoff_shape_sweep.py:820` と `:1435-1437`。

- campaign identity と campaign.lock:

  `as_dict()` は `config_for()` の `search_config` に入るため、`orchestrator/campaign/ident.py:196-229` の canonical preimage と `cfg_hash`、`:232-235` の campaign ID が変わる。B-10 の直接利用点は `orchestrator/campaign/b10_backoff_shape_sweep.py:2906-2910` と、他 workload の再収集 `:3049-3058`。

  2 ファイル外の consumer は、`orchestrator/campaign/loop.py:194-221` の campaign identity／protocol digest、`:385-409` の layout と resume、`orchestrator/campaign/ident.py:350-383` の既存 lock 比較、`:472-488` と `:538-603` の lock 検証・作成、`orchestrator/campaign/campaign_lock.py:459-478` の v2 envelope、`orchestrator/campaign/wal.py:2291-2307` の lock 永続化である。これらは汎用 consumer であり編集しない。

- generator receipt、build admission、build cache:

  `binding_sha256` は `orchestrator/campaign/build_admission.py:507-527` で generator receipt とその SHA に入り、`:615-675` で build-admission の `input_sha256` と receipt SHA に伝播する。

  verify 経路では `orchestrator/campaign/pipeline.py:1111-1178` が BUILD_START に receipt と receipt SHA を記録し、`:1180-1191` と `:1317-1327` が後続記録へ伝播する。`orchestrator/campaign/wal.py:1547-1562` が replay 時に再検証する。

  build／perf build 経路では `orchestrator/campaign/buildcache.py:2341`、`:2527-2551` が admission を build-cache preimage と full build digest に含め、`:2564-2574` と `:1678-1705` が cache hit を完全一致検証し、`:2850-2857` が manifest に保存する。したがって cache digest と cache directory も変わるが、追加の互換層は設けない。

- ブロック記録とレポート:

  `preregistration_binding` の形と値が変わるため、`orchestrator/campaign/b10_backoff_shape_sweep.py:2288-2294` の `record_sha256` も新規記録では変わる。JSON provenance の束縛部分 `:2598-2601` から `analysis_commit` は消える一方、Markdown の解析 provenance `:2655` と各ブロック row `:3030` には残り、JSON report の `records` `:2641` を通じても記録される。

repo 全体の検索では、B-10 固有の `analysis_commit`、`PreregistrationBinding`、`b10_preregistration_binding` の直接 consumer は対象 2 ファイル以外にない。上記の `ident.py`、`loop.py`、`campaign_lock.py`、`build_admission.py`、`pipeline.py`、`buildcache.py`、`wal.py` は値を不透明な config／receipt として読む汎用 consumer であり、編集対象外である。

## テスト計画

- `orchestrator/tests/test_b10_backoff_shape_sweep.py:825` 付近に、HEAD-only drift と WAL resume を一つのテストで検証する。

  受理: 保存側を `analysis_commit=ffffffffffffffffffffffffffffffffffffffff`、再開側を `analysis_commit=cccccccccccccccccccccccccccccccccccccccc`、両方の `analysis_code_sha256=eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` とし、`core()`、`as_dict()`、`binding_sha256` が一致して M17 と同形の lock／BUILD_START が通ることを確認する。  
  拒否: 再開側だけ `analysis_code_sha256=dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd` に変え、`binding_sha256` が `e7a5b1fc168b453785fff9f9c2bbc0b78c9e56b584bad7714a6cd7c569a53dc2` 相当へ変わって `PreflightError(code="resume-binding")` になることを確認する。

  同じテストで `binding.analysis_commit` が dataclass field として取得可能である一方、`"analysis_commit" not in binding.core()` と `"analysis_commit" not in binding.as_dict()` も確認する。digest literal 自体はテストへ固定せず、等値／不等値で検査する。

- `orchestrator/tests/test_b10_backoff_shape_sweep.py:1191` 付近に、過去ブロック記録の HEAD-only drift を検証する。

  受理: row の `analysis_commit` と `source_commit` を `ffffffffffffffffffffffffffffffffffffffff`、現在 binding の `analysis_commit` を `cccccccccccccccccccccccccccccccccccccccc`、双方の明示的 `analysis_code_sha256` を `eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` とし、`_validate_prior_block_records()` が row を返すことを確認する。  
  拒否: 現在 binding と row の `preregistration_binding` を `analysis_code_sha256=dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd` にそろえつつ、row の明示的 `analysis_code_sha256` だけを `eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` のまま残し、残存する `:2387` の比較だけで `resume-binding` になることを確認する。

  受理後の row に旧 `analysis_commit` と旧 `source_commit` がそのまま残ることも assert し、provenance の消失を防ぐ。

- 既存の `orchestrator/tests/test_b10_backoff_shape_sweep.py:805-824` は変更せず、完全に同じ束縛の WAL が再開可能という正例を維持する。

  受理: 既存 M17 は `analysis_commit=ffffffffffffffffffffffffffffffffffffffff`、`analysis_code_sha256=eeee...eeee` の同一束縛を通す。  
  拒否: `orchestrator/tests/test_b10_backoff_shape_sweep.py:624-635` の M08 は binding key 自体が欠落した legacy WAL を引き続き `resume-binding` で拒否する。

既存テストに、旧 `binding_sha256` literal、`analysis_commit` を含む exact key set、または固定 campaign ID を期待するものはないため、必然的に壊れる既存テストはない。pytest はこの段では実走しておらず、親が対象ファイルを `tools/run_tests.py` 経由で実測する。

## 判断が割れる点

- P1-a: 同意。`analysis_commit` は `PreregistrationBinding` field として残し、`core()` だけから外すのが、記録を保ちつつ束縛・比較・同一性ハッシュから除く最小変更である。`orchestrator/campaign/b10_backoff_shape_sweep.py:2655` と `:3030` の直接記録が provenance を担う。

- P1-b: 同意。`binding_sha256`、campaign ID、lock preimage、build-admission receipt、build-cache digest が変わることを受け入れる。今回の編集自体が `ANALYSIS_REL` の bytes と `analysis_code_sha256` を変えるので、旧 on-disk 状態は内容束縛によって既に再開不能であり、互換層を加える利益がない。

- P1-c: 同意。`:2388` の `source_commit` 比較は代替検査なしで除去する。現行比較は row の値を元 receipt と照合せず、単に現行 HEAD と比較しているだけなので provenance の真正性を高めておらず、代替 gate は本題外となる。receipt bytes の hash 再読 `:2414-2425` はそのまま残る。

- P1-d: 同意。M17 と M08 はそれぞれ「一致束縛は通す」「束縛欠落は拒否する」という基線として維持し、上記 2 テストで HEAD-only drift の正例と `analysis_code_sha256` drift の負例を追加する。これで 3 除去経路と残す内容ハッシュ検査を分離して検証できる。

## 総括

変更は `core()` からの 1 field 除去と、過去 block row の commit 比較 2 本の除去に限定する。  
6 個の内容束縛、解析 bytes と現行 HEAD blob の照合、correctness gate はすべて維持する。  
`analysis_commit` と `source_commit` は Markdown／JSON records／block row の provenance として残す。  
直接の歴史的拒否経路に漏れはなく、他の HEAD 照合は投入 receipt と実行 checkout の対応づけなので残す。  
最も危うい点は、`as_dict()` から消えた `analysis_commit` を誤って直接のレポート行・ブロック記録からも削除してしまうことである。