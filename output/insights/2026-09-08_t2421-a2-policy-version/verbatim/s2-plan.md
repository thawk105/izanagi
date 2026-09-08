## 現状の構造

参照記号:

- C: [tools/plotting/plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2421-a2-policy-version/tools/plotting/plot_a2_certification.py:47)
- P: [orchestrator/campaign/paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2421-a2-policy-version/orchestrator/campaign/paper_story_a2_certification.py:49)
- T: [orchestrator/tests/test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2421-a2-policy-version/orchestrator/tests/test_plot_a2_certification.py:187)
- A: [t2364 certification.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2421-a2-policy-version/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json:1)

現在の経路は次のとおり。

1. C:47-70 の `CANONICAL_SHA256` が認証成果物と raw manifest を束縛し、`HISTORICAL_CURRENT_POLICY_VIEWS` が `(certification sha256, policy sha256)` の 1 組を、schema・protocol hash・6-key configure 集合へ対応付ける。
2. C:125-160 の `_expected_hashes` と `_load_tracked_authority` が、override のない本番経路では認証 path を pin 表へ束縛し、認証 bytes と raw-manifest bytes を検査する。
3. C:255-307 の `_load_current_policy` が埋め込み policy を strict base64 と `policy_sha256` で検査する。登録外なら C:176-191 の `_producer_policy_from_bytes` から `producer.load_policy(path)`、登録内なら C:194-252 の `_historical_policy_view` へ分岐する。
4. `_historical_policy_view` は schema、configure の key 集合、`_protocol_preimage` の hash の 3 点だけを確認し、その後 `Policy` と `CellSpec` を手書きで再構成する。対して通常経路の P:367-602 は policy 全体を検査する。
5. どちらの分岐も C:288-306 へ合流し、certification cell の exact shape、policy 順序・identity・genome、全 cell の `source_binding_status == "bound"` を検査する。さらに C:603-625 が manifest、受領証、raw、WAL、workload condition、median、effect の共通照合へ進む。
6. T:187-327 の `_current_fixture` は現行 7-key policy と 12-file closure を作る。T:340-396 の `_historical_policy_fixture` は `fetchcontent_path_argument_prefixes` を削った 6-key policy と現行の手書き adapter 用 entry を作り、T:501-649 が現行・歴史・未知 hash の分岐を検査する。

P:367-602 の `load_policy` に含まれる検査は以下のすべてである。

- P:250-260、367-376: regular-file・非 symlink、UTF-8 JSON、duplicate key、非有限値、root object。
- P:110-115、376-383: 13 top-level key の exact set、`POLICY_SCHEMA`、certification composition、非空 study。
- P:384-400: `historical_reference` の exact shape・commit・reference-only role、durable base の absolute canonical path、tracked destination の bounded relative path。
- P:401-413: scheduler の exact shape、値型、正の nodes、walltime 形式、bounded job body。
- P:415-434: performance common の exact shape・正整数・L-W0・WAL=0・lowercase silo・文字列値、legacy correctness の exact shape。
- P:436-444: controlled define の exact shape・文字列値・WAL/TRACE 整合。
- P:446-514: `trace0_cmake_argv` の exact shape、configure scalar の非空・空白なし・相互非重複、fixed arguments、FetchContent prefix、toolchain role/prefix、build argv 文法。
- P:516-593: study ごとの workload/cell 数、workload ID、label、rratio、adopted backoff、cell ID、workload、stock/adopted role、genome 型と値、各 workload の exact role pair。
- P:595-602: raw bytes hash、9-key protocol preimage hash、document 順序を保持した `CellSpec` tuple の構築。

世代依存にすべき箇所は P:129-134 の `_TRACE0_CONFIGURE_ARGV_KEYS` を使う P:450-453 の exact-key 検査と、追加 key の値を検査する P:472-487 の FetchContent blockだけである。それ以外の上記検査は両世代で共有する。

親の事実 1〜7 はすべて確認できた。事実 2 だけ補足すると、成果物上の差分は確かに key 1 個だが、実装上は「世代別 exact-key 集合」と「その key が存在する世代だけに適用する値検査」の 2 箇所を連動させる必要がある。

- 事実 1: `policy_bytes_base64` を読む実 consumer は C:255-307 の 1 箇所で、呼出元は C:586-587 の `current-full` 分岐だけ。
- 事実 2: P:129-134 は 7 key。A:1 の埋め込み policy は 6 keyで、現在の shipped policy の唯一の内容差分は `fetchcontent_path_argument_prefixes`。
- 事実 3: C:47-55、125-144 により、override のない本番経路で未登録の認証 path は拒否される。
- 事実 4: C:57-70 の entry は指定された 2 hash の完全一致でしか選択されない。
- 事実 5: P:110-115 の 13 key に対し P:318-329 は 9 keyを含み、除外は `historical_reference`、`durable_measurement_base`、`tracked_destination`、`scheduler`。
- 事実 6: repo 内に現在の generator bytes hash の live pin はなく、C:857 は生成時記録、C:911-916 は generator 自身を live 検査しない。
- 事実 7: C:162-174、581-597 により policy loader は `current-full` だけで使われ、2026-08-24 legacy は別経路。

P1-a〜P1-c は覆さない。特に P1-a は正しく、現 adapter の受理 bytes は主 key で固定されているため、欠陥は受理集合の広さではなく、文法検査の重複と再利用不能性である。

## 実装プラン

**P:49、129-134 — 世代定数を追加する。**

P:49 の `POLICY_SCHEMA` 直後へ公開 generation ID を追加する。

```python
POLICY_GENERATION_CURRENT = "current"
POLICY_GENERATION_PRE_FETCHCONTENT_PATHS = (
    "pre-fetchcontent-path-arguments"
)
```

P:129-134 の現行 `_TRACE0_CONFIGURE_ARGV_KEYS` はそのまま現行文法の正本として残し、直後へ次の差分表を追加する。

```python
_TRACE0_CONFIGURE_ARGV_KEYS_BY_POLICY_GENERATION = {
    POLICY_GENERATION_CURRENT: _TRACE0_CONFIGURE_ARGV_KEYS,
    POLICY_GENERATION_PRE_FETCHCONTENT_PATHS: (
        _TRACE0_CONFIGURE_ARGV_KEYS
        - {"fetchcontent_path_argument_prefixes"}
    ),
}
```

値は generation ごとの exact key set だけとし、schema、protocol hash、study shapeなどの共通規則は複製しない。

**P:367-487 — `load_policy` に keyword-only generation を渡す。**

P:367 の署名を次へ置換する。

```python
def load_policy(
        path: Path | str = POLICY_PATH, *,
        generation: str = POLICY_GENERATION_CURRENT) -> Policy:
```

関数先頭で世代を解決し、未知値と unhashable 値を fallback なしで拒否する。

```python
try:
    configure_argv_keys = (
        _TRACE0_CONFIGURE_ARGV_KEYS_BY_POLICY_GENERATION[generation]
    )
except (KeyError, TypeError) as exc:
    raise CertificationError(
        f"unsupported policy grammar generation: {generation!r}"
    ) from exc
```

P:450-453 の `_exact_keys` 第 2 引数を `_TRACE0_CONFIGURE_ARGV_KEYS` から `configure_argv_keys` へ置換する。P:472-487 の FetchContent 値検査は次のように key 存在時だけ実行し、検査内容自体は一文字も緩めない。

```python
if "fetchcontent_path_argument_prefixes" in configure_argv:
    fetchcontent_path_argument_prefixes = configure_argv[
        "fetchcontent_path_argument_prefixes"
    ]
    if (type(fetchcontent_path_argument_prefixes) is not list
            or len(fetchcontent_path_argument_prefixes) != 4
            or not all(
                type(prefix) is str
                and prefix
                and not any(character.isspace() for character in prefix)
                and prefix.endswith("=")
                for prefix in fetchcontent_path_argument_prefixes
            )
            or len(set(fetchcontent_path_argument_prefixes)) != 4):
        raise CertificationError(
            "trace0 configure FetchContent path grammar is malformed"
        )
```

P:367-602 の残りの検査、`Policy` dataclass、`_protocol_preimage` は変更しない。generation を `Policy` や producer 成果物へ格納しないため、report schema と出力 bytes へ新フィールドは入らない。

**C:57-70 — 選択表の値だけを generation ID にする。**

`HISTORICAL_CURRENT_POLICY_VIEWS` 全体を次の形へ置換する。

```python
HISTORICAL_CURRENT_POLICY_GENERATIONS: dict[
    tuple[str, str], str
] = {
    (
        "e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671",
        "67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487",
    ): "pre-fetchcontent-path-arguments",
}
```

主 key は D1754 の `(certification sha256, policy sha256)` のまま維持する。`source_commit` は認証 bytes の一部として既に certification hash に束縛されているため、第三の選択入力にはしない。

**C:176-191 — temp-file helper に generation を受け渡す。**

署名を次へ置換する。

```python
def _producer_policy_from_bytes(
        producer, raw: bytes, *, generation: str | None = None):
```

現在の `return producer.load_policy(path)` を次へ置換する。

```python
if generation is None:
    return producer.load_policy(path)
return producer.load_policy(path, generation=generation)
```

登録外の policy は generation argument を渡さず、従来と同じ default current loader を通す。これは未知 hash を歴史文法へ送る fallback ではない。

**C:194-252 — 手書き adapter を全削除する。**

`_historical_policy_view` の定義を丸ごと削除する。schema・protocol identity は後段の共通検査で保持し、cell 構築は producer の完全な `load_policy` に一本化する。

**C:275-294 — exact pair から generation を選択する。**

C:275-287 を次の分岐へ置換する。

```python
historical_generation = HISTORICAL_CURRENT_POLICY_GENERATIONS.get(
    (certification_sha256, raw_sha256)
)
if historical_generation is None:
    policy = _producer_policy_from_bytes(producer, raw)
else:
    policy = _producer_policy_from_bytes(
        producer, raw, generation=historical_generation
    )
producer._validate_certification_cells(certification, legacy=False)
```

旧 entry 内の `protocol_schema` と `protocol_sha256` を使う C:280-285 の重複 assert は削除する。受理集合は緩まない。C:291-294 が引き続き `certification.protocol_schema == producer.POLICY_SCHEMA`、study、producer が再計算した `policy.protocol_sha256` を同時に検査し、exact pair 自体も選択表が固定するためである。

C:295-306 の cell 順序・identity・genome・`source_binding_status` 検査、および C:603-625 以降の receipt/raw/WAL/effect 照合は変更しない。generation は policy parse の前だけで使い、歴史 policy を通した後に別の証拠検査経路を作らない。

**T:340-649 — fixture と既存歴史テストを世代表へ移行する。**

- T:340-396 の `_historical_policy_fixture` は `HISTORICAL_CURRENT_POLICY_GENERATIONS` を monkeypatch し、値を `producer.POLICY_GENERATION_PRE_FETCHCONTENT_PATHS` にする。schema・protocol・configure key を複製した dict は削除する。
- T:516-531 の registry test は、entry 数 1、exact hash pair、値が producer の historical generation constant と同じことを検査する形へ更新する。
- T:534-540 の既存正例は full `load_measurements` が 12-file closure、cell 順序、source-bound 状態、effect crosscheck まで通ることを追加確認する。
- T:600-619 の observer は `def observe(path, **kwargs)` とし、登録外 bytes では `kwargs == {}`、つまり current default が無指定で呼ばれたことを検査する。

**既定経路の byte 不変保証。**

- `load_policy()` の既定値は `POLICY_GENERATION_CURRENT` で、選ぶ key set と全検査順は現行と同じにする。
- P:4929-4932 の producer CLI 選択、shipped A-2/A-6 policy、`Policy.raw_bytes`、`_protocol_preimage`、report/materialize を変更しない。
- 既存の `orchestrator/tests/test_paper_story_a2_certification.py:1813-1826` が A-2 policy bytes hash `cacfdd5d...` と protocol hash `d99f08bc...` を pin している。A-6 も同ファイルの 1954-1998 が bytes と protocol hash を pin している。
- committed PNG、PDF、provenance、`CANONICAL_SHA256`、A:1 は編集しない。テスト生成物は `tmp_path` のみとする。
- 歴史世代の選択は記録済み policy の parse 方法だけを変える。`status`、correctness、`source_binding_status` を再分類せず、当時の測定を現行の正しさ主張へ昇格させない。

## テスト計画

**正例: `test_t2364_frozen_policy_loads_through_registered_generation`**

T:516 付近へ追加する。A:1 を直接読み、実 certification sha、埋め込み policy sha、protocol sha、4 cell 順序を確認しつつ、`producer.load_policy` の spy が `generation=POLICY_GENERATION_PRE_FETCHCONTENT_PATHS` をちょうど 1 回受けたことを確認する。

受理の含意: exact t2364 hash pair は 6-key 世代の producer 全体 loader で読み取られ、記録済み policy identity と cell identity を再構成できる。  
拒否の含意: 同じ bytes を current 世代へ送れば欠落した `fetchcontent_path_argument_prefixes` で拒否されるため、成功は current 文法の緩和を意味しない。

既存 `test_historical_exact_hash_pair_uses_the_historical_policy_view` は `test_historical_exact_hash_pair_uses_full_producer_policy_generation` へ改名し、synthetic 12-file closure 全体を通す正例として残す。

受理の含意: 歴史 generation で得た `Policy` も current-full の共通 receipt/raw/WAL/effect 経路を最後まで通る。  
拒否の含意: 歴史 generation 専用の証拠検査 bypass は存在せず、共通照合の失敗は現行経路と同様に拒否される。

**負例 1: `test_historical_generation_requires_certification_hash_component`**

T:543-553 を置換する。exact pair の正例を作った後、埋め込み policy は変えず `source_commit` だけ変更し、certification hash だけを変える。対応する単独変異は「policy hash だけで generation を選ぶ」であり、この test だけが追加テスト群の中でその弱化を観測する。

受理の含意: 変更前の exact pair は historical generation で受理される。  
拒否の含意: certification hash が変わった時点で historical generation は選ばれず、6-key policy は current loader により拒否される。

**負例 2: `test_historical_generation_requires_policy_hash_component`**

T:568-578 を置換する。歴史 policy に JSON として無害な末尾改行を追加して policy hash と certification bytes を更新し、registry には「新 certification hash、旧 policy hash」の不一致 pairだけを置く。対応する単独変異は「certification hash だけで generation を選ぶ」であり、この test だけがその弱化を観測する。

受理の含意: registry と実 bytes の両 hash が一致する基準 fixture は historical generation で受理される。  
拒否の含意: certification hash だけが registry と一致しても policy hash が異なれば historical generation は選ばれず、current loader が 6-key policy を拒否する。

**負例 3: `test_historical_generation_rejects_invalid_unhashed_tracked_destination`**

T:581-597 を置換する。歴史 policy の `tracked_destination` を `"../outside"` に変え、policy bytes と certification bytes を再計算し、その新しい exact pair を historical generation へ登録する。protocol hash は変えない。対応する単独変異は「historical generation のときだけ P:398-400 を飛ばす」であり、この test だけが手書き近似への退行を観測する。

受理の含意: 元の t2364 `tracked_destination` は bounded relative path として全体 loader を通る。  
拒否の含意: `_protocol_preimage` に含まれない field でも、exact pair の historical policy は producer の完全な文法により拒否される。

**負例 4: `test_policy_loader_rejects_unknown_generation`**

T:649 付近へ追加する。shipped current policy を `generation="unknown-policy-generation"` で直接読み、`CertificationError` の `"unsupported policy grammar generation"` を期待する。対応する単独変異は「未知 generation を current へ代替する」であり、この test だけが generation ID の fail-closed 性を観測する。

受理の含意: `POLICY_GENERATION_CURRENT` と登録済み historical generation だけが選択可能である。  
拒否の含意: typo、将来値、非登録値を現行または最も近い文法へ推測して読み替えない。

既存の以下の負例は維持する。

- T:556-565: certification 内の `policy_sha256` と埋め込み bytes の不一致。
- T:600-619: 未登録 policy bytes が historical generation へ流れず、無指定 current loader へ流れること。
- T:622-649: current generation が FetchContent key 欠落と prefix list の破損を拒否すること。
- T:675-895: schema family、12-file closure、campaign claim、receipt、raw、WAL、source token、`source_binding_status`、median、effect の既存負例。

この段では read-only のため pytest は実行しない。親は実装後に少なくとも `tools/run_tests.py` 経由で `orchestrator/tests/test_plot_a2_certification.py` と、producer の policy loader を覆う `orchestrator/tests/test_paper_story_a2_certification.py` を実測する。

## 変異事前登録の候補

1. **M1: certification hash を主 key から外す。**  
   C:275-276 の planned exact lookup を次へ置換する。

   ```python
   historical_generation = next((
       value
       for (_cert_sha, policy_sha), value
       in HISTORICAL_CURRENT_POLICY_GENERATIONS.items()
       if policy_sha == raw_sha256
   ), None)
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_historical_generation_requires_certification_hash_component`。cert bytes だけを変えても歴史世代が選ばれ、期待した current-grammar 拒否が消えるため KILLED を期待する。

2. **M2: policy hash を主 key から外す。**  
   C:275-276 の planned exact lookup を次へ置換する。

   ```python
   historical_generation = next((
       value
       for (cert_sha, _policy_sha), value
       in HISTORICAL_CURRENT_POLICY_GENERATIONS.items()
       if cert_sha == certification_sha256
   ), None)
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_historical_generation_requires_policy_hash_component`。registry の policy hash と実 bytes が異なるのに歴史世代が選ばれるため KILLED を期待する。

3. **M3: consumer の generation 受け渡しを無効化する。**  
   C:275-287 の historical branch に置く

   ```python
   policy = _producer_policy_from_bytes(
       producer, raw, generation=historical_generation
   )
   ```

   を次へ置換する。

   ```python
   policy = _producer_policy_from_bytes(producer, raw)
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_t2364_frozen_policy_loads_through_registered_generation`。t2364 policy が current 7-key 文法で拒否され、spy も generation を観測できないため KILLED を期待する。

4. **M4: historical generation の key set を current と同一にする。**  
   P:134 直後に追加する表の

   ```python
   POLICY_GENERATION_PRE_FETCHCONTENT_PATHS: (
       _TRACE0_CONFIGURE_ARGV_KEYS
       - {"fetchcontent_path_argument_prefixes"}
   ),
   ```

   を次へ置換する。

   ```python
   POLICY_GENERATION_PRE_FETCHCONTENT_PATHS: _TRACE0_CONFIGURE_ARGV_KEYS,
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_t2364_frozen_policy_loads_through_registered_generation`。正しい generation を渡しても frozen 6-key policy が拒否されるため KILLED を期待する。

5. **M5: 未知 generation を current へ fallback する。**  
   P:367 直後へ追加する generation lookup の例外処理

   ```python
   raise CertificationError(
       f"unsupported policy grammar generation: {generation!r}"
   ) from exc
   ```

   を次へ置換する。

   ```python
   configure_argv_keys = (
       _TRACE0_CONFIGURE_ARGV_KEYS_BY_POLICY_GENERATION[
           POLICY_GENERATION_CURRENT
       ]
   )
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_policy_loader_rejects_unknown_generation`。未知値が shipped current policy を読めてしまい、期待した例外が消えるため KILLED を期待する。

6. **M6: historical generation だけ shared tracked-destination 検査を外す。**  
   P:398-400 の

   ```python
   if tracked.is_absolute() or ".." in tracked.parts:
   ```

   を次へ置換する。

   ```python
   if (generation == POLICY_GENERATION_CURRENT
           and (tracked.is_absolute() or ".." in tracked.parts)):
   ```

   対象 nodeid: `orchestrator/tests/test_plot_a2_certification.py::test_historical_generation_rejects_invalid_unhashed_tracked_destination`。protocol hash が同じ不正 historical policy を全体 loader が受理してしまうため KILLED を期待する。

## リスクと未確認事項

- pytest と実 t2364 external root を使う figure-data 構築は実測していない。実装後の実測は親担当である。
- historical `Policy.path` は旧 adapter の `Path("<historical-embedded-policy>")` から、削除済み temp file の resolved path へ変わる。現在の consumer 経路は `document`、`cells`、hash だけを使い `path` を provenance へ出さないが、テストでこの前提を確認する。
- P:2153-2219 の実行時 configure argv validator は FetchContent key を前提とする。今回 historical policy から呼ばれるのは receipt/source validation だけなので支障はないが、historical `Policy` を producer の再実行へ流用できるという一般保証にはしない。
- producer loader の署名変更は、monkeypatch wrapper が `path` だけを受ける既存テストに影響しうる。T:600-619 の observer は `**kwargs` 対応が必要で、`test_paper_story_a2_job_contract.py:596-610` の wrapper も既定呼出しだけであることを親が回帰確認する。
- A-2 と A-6 は同じ `load_policy` を使うため、generation の既定を誤ると A-6 の exact policy test も壊れる。既定値と shipped policy bytes pin を同時に確認する。
- test helper は `expected_hashes` override を使えるが、本番 CLI は C:125-144 の repo-owned pin 表からしか hash を得ない。テスト成功を本番の未知 path 受理と取り違えない。
- generator source の変更後に図を再生成すれば、C:857 により新 provenance の `generator.sha256` は当然変わる。既存 provenance は C:911 の定義どおり生成時記録なので、今回は committed figure bundle を再生成・更新しない。
- exact cert hash は `source_commit` を含む認証 document 全 bytes を束縛する。選択表に `source_commit` を追加しても独立した閉包強化にはならず、二重正本になる。

## 裁定パッケージ候補

- **producer が generation ID を成果物へ記録する案。** 将来は自己記述性を上げられるが、result schema、producer bytes、凍結 pin の変更を伴うため今回実装しない。
- **consumer または producer loader の live source pin。** 現在の figure provenance は生成時記録だけなので、将来「どの loader bytes で再解釈したか」を強く束縛する必要が生じた場合の別裁定候補とする。
- **`_protocol_preimage` から除外された 4 field の扱い。** 今回は policy bytes hash と certification hash、完全 loader 検査で閉じている。protocol identity 自体へ含める変更は既存 protocol hash と全成果物を変えるため別パッケージとする。
- **A-6 の歴史世代。** loader は共有するが、A-6 artifact 向け generation registry や consumer 波及は今回扱わない。

## 総括

- 採る設計は、producer の共有 `load_policy` に keyword-only generation を追加し、文法差を configure key set 1 点で表す方式である。
- consumer は exact `(cert sha, policy sha)` から generation だけを選び、手書き `_historical_policy_view` を削除する。
- 捨てる設計は permissive fallback、`source_commit` を加えた三重 key、producer 成果物への generation 記録である。
- 歴史読みは保存時文法による再現であり、記録済み測定を現行の正しさ主張へ昇格させない。
- 段 4 の択一は「D1754 の hash pair を維持する案」と「`source_commit` を選択入力へ追加する案」で、前者を推奨する。