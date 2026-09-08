## 実装方針

`orchestrator/campaign/contract_loader_binding.py` 内に、ordered path 群を一度の `git cat-file --batch` で読む generator を追加する。4 公開関数はその generator を tuple 順に消費し、現在と同じ順番で digest 検査、disk drift 検査、例外送出を行う。

`_head_commit`、`_require_commit`、62 path の集合と順序、binding schema、SHA-256 の入力、呼び出し元 3 module は変更しない。

## `_run_git` の変更

対象は `orchestrator/campaign/contract_loader_binding.py:251-315`。

- signature を次へ拡張する。

```python
def _run_git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> bytes:
```

- `subprocess.run` 呼び出し `:287-300` に `input=input_bytes` を加える。
- batch 呼び出しだけが `input_bytes=...` を渡す。それ以外は `None` のため、既存の `_validated_root`、`_head_commit`、`_require_commit` の argv と stdin 挙動は変わらない。
- 新しい subprocess wrapper は作らない。`subprocess.run` の spawn site は引き続き `_run_git` 内の 1 か所だけなので、`test_ccbench_spawn_sites.py:111` の台帳値 `1` は変更しない。
- `_GIT_HARDEN`、環境 allowlist・拒否集合、絶対 `/usr/bin/git`、return code 検査、stderr 処理はそのまま通す。

timeout は `GIT_TIMEOUT_SECONDS = 10` のままにする。対象はローカル object database 内の 62 個の小さい source blob であり、62 回の起動を一度へまとめる変更なので、現時点で timeout を広げる静的根拠はない。親の実測で batch 単体が 10 秒へ近づいた場合だけ別途再評価し、この wave には含めない。

## batch reader の追加

対象は現行 `_blob` の位置 `contract_loader_binding.py:343-345`。ここを概ね次の三層へ置き換える。

- ordered input を作る `_iter_blobs(root, commit, relative_paths)`。
- batch output を offset で解析し、`(relative, blob_bytes)` を tuple 順に yield する処理。
- 既存 `_blob(root, commit, relative)` を、一要素の `_iter_blobs` を最後まで消費する薄い互換 wrapper として残す。

dict を直接返さず generator にする理由は二つある。

- `relative_paths` の順序と重複を失わない。
- 各公開関数が一 path ごとに digest または disk を検査でき、先頭側の mismatch・drift を従来と同じ path 順で拒否できる。

全 query の `_relative_parts(relative)` 検査は subprocess 起動前に行う。path escape を batch protocol へ渡さない。

## stdin と path 表現

batch argv は次で固定する。

```python
_run_git(
    root,
    "cat-file",
    "--batch",
    "-z",
    input_bytes=batch_input,
)
```

`batch_input` は tuple 順の `os.fsencode(f"{commit}:{relative}")` を NUL で終端した列とする。`--unordered` は付けない。

`_relative_parts` は空白、tab、改行などを拒否していない。空白だけなら LF protocol でも扱えるが、改行は query 境界になるため、通常の一行区切りは `_blob` の既存受理面を狭める。`-z` は入力だけを NUL 区切りにし、要求された batch output の LF framing は維持するので採用する。`-Z` は出力形式まで変えるため使わない。

NUL は OS の path/argv として元から成立しない。query の encoded bytes に NUL があれば subprocess へ渡さず、従来の embedded-NUL 実行失敗と同じ種類・prefix の `ContractLoaderBindingError("contract-loader-git-error: ...")` にする。

## batch output の解析

各 path について、現在の offset から次の順に分岐する。

1. `expected_query + b" missing\n"` と一致する場合  
   `ContractLoaderBindingError` を `contract-loader-git-error:` prefix で送出し、対象 path と `missing` を含める。逐次版で `git cat-file blob` が非 zero だった場合と同じ分類になる。

2. `expected_query + b" ambiguous\n"` と一致する場合  
   同じく `contract-loader-git-error:`。他の status や malformed status line も受理せず同じ prefix にする。

3. success header の場合  
   最初の LF までを header とし、exact に `<oid> <type> <size>` の 3 field へ分割する。

4. oid  
   ASCII lowercase 40 hex でなければ `contract-loader-git-error:`。現行 binding が 40 hex commit を要求するため、SHA-1 repository の正規出力だけを受ける。

5. type  
   exact `blob` 以外は `contract-loader-git-error:`。`tree`、`commit`、`tag` 等の payload は loader blob として返さない。これは逐次 `cat-file blob` の型不一致と同じ拒否方向である。

6. size  
   ASCII の非負 decimal 以外を拒否する。宣言 size 分を raw output から切り出せなければ、途中 EOF・git の短絡として `contract-loader-git-error:` にする。

7. record delimiter  
   宣言 size 分の直後が exact LF でなければ拒否する。blob 自身の末尾 LF は size 内の bytes であり、その後に protocol LF がもう一つ必要になる。`splitlines()` は binary blob を壊すため使わない。

8. 全 path 消費後  
   offset が stdout 長と exact 一致しなければ、余分な response、ずれた framing、途中からの偽 header として `contract-loader-git-error:` にする。

`_run_git` が非 zero return code や timeout を検出した場合は parser へ到達させず、既存の `contract-loader-git-error:` または `contract-loader-git-timeout:` をそのまま使う。return code が zero でも出力が途中で切れていれば parser が fail-closed にする。

missing response は expected query bytes と照合するので、別 path の missing line が現れた場合も順序不一致として拒否できる。success header は query を含まないため、Git の documented ordered response を対応規則とする。fake が success record を入れ替えた場合は、後段の path 固有 digest または disk 照合が必ず拒否するよう、test では異なる blob を使う。

## 4 関数の変更

`capture_contract_loader_binding` の `:353-360` は次の形にする。

- `_iter_blobs(root, commit, CONTRACT_LOADER_RELATIVE_PATHS)` を一度だけ作る。
- yield された各 `(relative, blob)` について `_read_regular_file_no_follow` を呼ぶ。
- `disk != blob` は現在と同じ `contract-loader-drift: disk bytes が HEAD blob と不一致:`。
- clean な場合だけ同じ blob bytes の SHA-256 を同じ tuple 順で dict へ入れる。
- 返り値は同じ `ContractLoaderBinding(commit, digests)`。

`verify_live_contract_loader_binding` の `:372-383` は、batch からの各 blob に対し、現在と同じ順番で次を行う。

1. 記録 digest と blob digest を比較し、不一致なら `contract-loader-blob-mismatch:`。
2. 全 path で `_read_regular_file_no_follow` を行い、disk と blob を比較し、不一致なら `contract-loader-drift:`。

`verify_committed_contract_loader_binding` の `:396-401` は disk を読まず、batch の各 blob と記録 digest のみを比較する。返り値 `None`、exact binding 型検査、`_require_commit` は変えない。

`verify_committed_contract_loader_blobs` の `:412-420` は引数 `relative_paths` の順序どおり batch を消費する。mapping の事前正規化や cache は加えず、現在と同じ path ごとの lookup と digest 比較を保つ。

clean input では全 62 path が必ず `_read_regular_file_no_follow` を通る。drift 検査の間引き、digest の省略、process 内 cache は行わない。

## `_blob` と test support

`_blob(root, commit, relative)` の signature は維持する。一 path の `_iter_blobs` を完全に消費し、唯一の blob bytes を返す薄い wrapper にするため、既存の直接利用面は消さない。

`orchestrator/tests/campaign_lock_test_support.py:12-20` は、62 回 `_blob` を呼ぶ comprehension を次の構造へ変える。

- `_iter_blobs(root, commit, campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS)` を一度だけ消費して ordered dict を作る。
- その dict の bytes から現行どおり SHA-256 map を作る。
- dirty disk を読まず recorded commit blob を使う性質は維持する。

これにより、多数の consumer test が使う共有 lock fixture も一度の batch になる。cache や production の検査省略ではない。

## 他 test の最小追随

`test_artifact_admission.py:2331-2334` の fake は、現行 test 自体では偽 top-level を返した直後に拒否されるため batch kwarg へ到達せず、今すぐの実行だけなら壊れない。ただし `_run_git` の代替として signature が不完全になるため、次の二つの一行編集を行う。

```python
def redirected_git_view(
    root: Path, *args: str, **kwargs: bytes | None,
) -> bytes:
```

```python
return real_run_git(root, *args, **kwargs)
```

`test_ccbench_spawn_sites.py:111` は値を変更しない。parser や stdin 作成 helper は `subprocess.run` を呼ばず、同 test に既存の `("<module>._run_git"): 1` を再確認させる。

`ident.py`、`artifact_admission.py`、`p3_b4_wiring_probe.py` の production call site は一切変更しない。

## 所有 test の計画

追加・更新は `orchestrator/tests/test_t671_source_binding.py` に集約する。

- `test_batch_blob_reader_accepts_ordered_binary_blobs_and_nul_delimited_queries(monkeypatch)`  
  空白、改行を含む二つの valid relative path と、末尾 LF・埋め込み NULを含む異なる blob bytes を受理する正例。fake `_run_git` が exact argv、NUL 終端 stdin、tuple 順を検査し、parser の返す path と bytes が期待 literal と一致することを確認する。

- `test_blob_compatibility_wrapper_uses_one_batch_query(monkeypatch)`  
  `_blob(root, commit, relative)` が従来と同じ bytes を返すことを受理し、`cat-file blob <expr>` への後退や複数呼び出しを拒否する。

- `test_batch_reader_rejects_one_missing_path_of_sixty_two(tmp_path, monkeypatch)`  
  fixture commit から中央の一 path だけを index から除いて commit し、disk file と残り 61 blob は正常な状態を作る。`capture_contract_loader_binding()` が `contract-loader-git-error:` で始まり missing path を含む例外を出すことを確認する。

- `test_batch_reader_rejects_ambiguous_and_non_blob_responses(monkeypatch, response_kind)`  
  `<obj> ambiguous\n` と、valid header だが type が `tree` の二例を拒否し、双方が `contract-loader-git-error:` で始まることを確認する。

- `test_batch_reader_rejects_truncated_output(monkeypatch)`  
  中央 response の header size より body が短い stdout を返し、zero return 相当でも `contract-loader-git-error:` になることを確認する。

- `test_batch_reader_rejects_size_or_record_lf_corruption(monkeypatch, corruption)`  
  size が実 payload より小さい、大きい、body 後の protocol LF がない、の各形を拒否する。blob 自体が LF で終わる正常 response は正例側で通す。

- `test_batch_reader_rejects_extra_output_after_last_record(monkeypatch)`  
  62 response の後に 1 byte または余分な header を付け、EOF exact 検査が `contract-loader-git-error:` にすることを確認する。

- `test_committed_verification_rejects_reordered_batch_output(monkeypatch)`  
  digest と長さが異なる二 blob の complete response を逆順で返す。parser が順序を勝手に並べ替えず、最初の path で `contract-loader-blob-mismatch:` が出ることを確認する。二 blob を同じ bytes にしない。

- `test_committed_verification_rejects_one_digest_mismatch(tmp_path, monkeypatch)`  
  62 entry のうち中央の一 entry だけを `sha256(b"mismatch:" + recorded_blob)` へ変える。他は正しいまま direct verifier を呼び、例外文字列が `contract-loader-blob-mismatch:` で始まり対象 path を含むことを確認する。

- 既存 `test_live_verification_rejects_each_dirty_enforcement_source`  
  一 path だけへ `b"\nuncommitted edit\n"` を加える構成を維持し、assert を単なる包含から `message.startswith("contract-loader-drift:")` へ強める。対象 path も引き続き検査する。

- `test_capture_batches_blobs_but_reads_all_sixty_two_disk_paths(tmp_path, monkeypatch)`  
  `_validated_root` だけを既知の fixture root へ固定し、実 `subprocess.run` と `_read_regular_file_no_follow` を記録 wrapper で包む。capture が後述の exact 2 Git calls、tuple 順の 62 disk reads、独立に作った期待 digest mapを返すことを確認する。

既存の clean 正例 `test_exact_twenty_four_clean_closure_capture_and_live_verify` は実際には 62 path を検査しているため、内容を維持する。必要なら node 名だけ `sixty_two` へ訂正するが、外部 nodeid 利用の可能性を避けるなら改名しない。

## 恒真 assert の回避

現行 test の次の assert は、batch 実装の正しさを単独では証明しない。

- `set(binding.contract_loader_blob_sha256s) == set(expected)` は `ContractLoaderBinding.__post_init__` 自身が exact key 集合を強制するため、parser の順序や bytes 対応の証拠にはならない。
- `_REPO_ROOT` が `Path`、例外 class が `Exception` の subclass という assert は、個別の拒否分岐を証明しない。
- 単に subprocess 数が `63` 未満という assert は、blob 検査をゼロ回にしても通る。

そのため新 test は、異なる blob bytes、中央一 path だけの破損、exact argv、exact stdin、exact call 数、独立に計算した digest を使う。順序入替 test は同一 blob を使わず、digest mismatch が必ず観測可能な入力にする。

## subprocess 数と性能の裏取り

静的 call graph 上、完全な public capture は次の 3 process である。

1. `_validated_root`: `rev-parse --show-toplevel`
2. `_head_commit`: `rev-parse --verify HEAD^{commit}`
3. `_iter_blobs`: `cat-file --batch -z`

したがって「無加工の capture が 2 process」という assert は事実と異なる。要求された `rev-parse + cat-file --batch = 2` は、process-count test で `_validated_root` を既知 root へ固定した capture 本体の測定として固定する。

その test は call 数だけでなく、1 回目が HEAD rev-parse、2 回目が唯一の batch、batch stdin が exact 62 query かつ tuple 順であることも確認する。逐次 `_blob` へ戻せば 63 process、batch 自体を省けば 1 processになるため恒真ではない。別途 spawn site 台帳が source 上の `subprocess.run` 1 か所を固定する。

親の login A/B は brief にある同一 nodeid を同条件で改修前後に測る。実装 test の elapsed だけでなく、共有 fixture 経由の `_run_git` 回数低下も照合する。計算ノード上での効果は P4 のままなので、受入全走の最遅 shard wall と対象 module W が得られるまでは改善を実測済みとは書かない。

## 変異事前登録

runner は D1712 に従い、`test_t671_source_binding.py` と同ファイルへ追加する所有 test だけに絞る。

| 変異 | 赤になる所有 test |
|---|---|
| `_run_git` から `input=input_bytes` を削除 | `test_capture_batches_blobs_but_reads_all_sixty_two_disk_paths` |
| `-z` を削除し LF join へ戻す | `test_batch_blob_reader_accepts_ordered_binary_blobs_and_nul_delimited_queries` |
| query の tuple 順を reverse または sort する | 上記正例と process-count test。順序に対する冗長 gate |
| `_blob` を旧 `cat-file blob` 呼び出しへ戻す | `test_blob_compatibility_wrapper_uses_one_batch_query` |
| `missing` response を空 blob として扱う | `test_batch_reader_rejects_one_missing_path_of_sixty_two` |
| `type == blob` 検査を削除する | `test_batch_reader_rejects_ambiguous_and_non_blob_responses` |
| size 不足時の EOF 検査を削除する | `test_batch_reader_rejects_truncated_output` |
| body 後の protocol LF 検査を削除する | `test_batch_reader_rejects_size_or_record_lf_corruption` |
| 全 response 後の exact EOF 検査を削除する | `test_batch_reader_rejects_extra_output_after_last_record` |
| path と記録 digest の比較を削除する | direct digest mismatch test と既存 admission mismatch test。冗長 gate |
| live/capture の `disk != blob` 分岐を削除する | 既存 dirty-source test と loader-drift-before-lock test。冗長 gate |

source file 自身の drift だけで赤になった node は kill 証拠に数えず、各 test の期待 prefix・path・call count が意図した分岐を名指しした場合だけ kill とする。

## provisional 裁定の評価

(P1) 採用する。size framing と path 順を厳密に解析すれば、missing、型不一致、短絡を path 単位の `ContractLoaderBindingError` へ写せる。  
ただし success response は query を返さないため、順序入替は異なる blob の digest・disk 照合で fail-closed になることを test で固定する。

(P2) 既定どおり触らない。`ident.py:283-284` の capture 後の live verify は process を増やすが、呼び出し元変更は禁止 scope である。  
省略の安全性と実効差は別 wave の材料であり、本プランには含めない。

(P3) 既定どおり触らない。content-addressing の性質だけでは、この wave で cache の寿命・root identity・例外再現を追加設計する理由にならない。  
process 内 memo、negative cache、共有 cache はすべて本プラン外とする。

(P4) 現時点では未確定である。login profile は原因仮説を強く支持するが、48 worker 下の wall 改善を直接証明しない。  
親の同一 test A/B と受入全走で最遅 shard wall・対象 module W を取り、そこでのみ成立を判断する。

## 静的確認と実走境界

指定された射影資料はすべて読めた。read-only のため file 編集、commit、pytest、性能測定は行っていない。

author 段では差分後に、62 path literal の集合・順序が不変、production call site 3 module が無変更、spawn site 台帳値が不変、4 関数の返り値と例外 prefix が維持されていることを静的 diff でも確認する。テストの緑、A/B 数値、受入 wall は親の実走結果が出るまで主張しない。

## 総括

- `_run_git` に keyword-only `input_bytes` を加え、62 query を一度の `cat-file --batch -z` へ送る。
- ordered generator で各 blob を従来順に digest・disk 照合し、全 62 path の drift 検査を維持する。
- malformed、missing、非 blob、短絡、順序入替を所有 test で fail-closed に固定する。
- `_blob` は互換 wrapper として残し、共有 test support も一度の batch へ追随させる。