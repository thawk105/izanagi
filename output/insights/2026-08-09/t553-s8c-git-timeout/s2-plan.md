採る実装は「2,000 要求ずつ分割しつつ、分割前の各 Git 呼び出し単位で入力・出力・15 秒を集計する」です。履歴比例予算は採りません。なお、親 brief には「同じ 15 秒内で同じ仕事を複数 process に分ければ赤が閉じる」という未実証の前提があり、段 4 へ差し戻す必要があります。

## 1. 分割の設計

対象は [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py) の次の箇所です。

| 現在位置 | 実装 |
|---|---|
| `:17-31` | `import time` を追加する。 |
| `:86-95` | `MAX_GIT_BATCH_REQUESTS_PER_CALL = 2_000` を `MAX_BATCH_REQUESTS` の直後に追加する。環境変数・CLI・関数引数へ露出しない。 |
| `:880-913` | `_git` に絶対締切を追加し、chunk 共通 helper を新設する。 |
| `:1102-1130` | `_batch_oids` の単一 `cat-file --batch-check` を helper 経由の chunk 実行へ置換する。 |
| `:1133-1179` | `_batch_blob_bytes` の size-check と blob-read の双方を chunk 実行へ置換する。 |
| `:1285-1327` | caller の署名・呼び方は変更しない。 |

新 helper は概ね次の構造にするべきです。

```python
def _git_chunked(
    root: Path,
    args: Sequence[str],
    stdin_lines: Sequence[bytes],
) -> bytes:
    total_input = sum(len(line) for line in stdin_lines)
    if total_input > MAX_GIT_INPUT_BYTES:
        raise PreregistrationError("git-input-limit", str(total_input))

    deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
    outputs: list[bytes] = []
    total_output = 0

    for start in range(0, len(stdin_lines), MAX_GIT_BATCH_REQUESTS_PER_CALL):
        chunk = b"".join(
            stdin_lines[start : start + MAX_GIT_BATCH_REQUESTS_PER_CALL]
        )
        output = _git(root, args, stdin=chunk, deadline=deadline)
        total_output += len(output)
        if total_output > MAX_GIT_OUTPUT_BYTES:
            raise PreregistrationError("git-output-limit", str(total_output))
        if time.monotonic() >= deadline:
            raise PreregistrationError("git-timeout")
        outputs.append(output)

    return b"".join(outputs)
```

`_git` は以下へ変更します。

```python
def _git(
    root: Path,
    args: Sequence[str],
    *,
    stdin: Optional[bytes] = None,
    deadline: Optional[float] = None,
) -> bytes:
```

`subprocess.run(timeout=...)` へ渡す値は、締切なしなら従来どおり `15.0`、締切ありなら次です。

```python
remaining = deadline - time.monotonic()
if remaining <= 0:
    raise PreregistrationError("git-timeout")
timeout = min(GIT_TIMEOUT_SECONDS, remaining)
```

`_git_text` は既存 monkeypatch seam を残すため、`stdin_lines: Optional[Sequence[bytes]] = None` を keyword-only 追加し、指定時だけ `_git_chunked`、未指定時は従来の `_git` を使います。`stdin` と `stdin_lines` の同時指定は内部 contract 違反として許さない設計にします。

### `_batch_oids`

`:1102-1130` の次の順序を維持します。

1. `len(commits) * len(paths)` を全体で検査し、超過なら chunk 化前に `batch-request-limit`。
2. `requests` は従来どおり commit-major / path-minor で作る。
3. 各 request を `f"{commit}:{path}\n".encode("utf-8")` にする。
4. `_git_chunked(..., ["cat-file", "--batch-check"], stdin_lines)` を1回呼ぶ。
5. chunk ごとには parse せず、連結した全 output に既存 `splitlines()`・件数・header 検査をそのまま適用する。

### `_batch_blob_bytes`

`:1133-1179` では、従来の `tuple(dict.fromkeys(oids))` を維持し、OID 行を一度だけ構成します。

- size phase: `_git_text(..., stdin_lines=oid_lines)`。この呼び出しで1つの15秒締切と1つの累積出力上限を使う。
- 全 size header を従来どおり検査し、`MAX_BLOB_BYTES` と `MAX_TOTAL_BLOB_BYTES` を全 OID 集合へ適用する。
- blob phase: `_git_chunked(..., ["cat-file", "--batch"], oid_lines)`。size phase とは別の15秒締切・出力集計を使う。
- chunk output を連結してから、現在の offset/header/size/trailing-newline/extra 検査をそのまま適用する。

### 戻り値が不変である根拠

- `_batch_oids` は引き続き `dict[tuple[str, str], Optional[str]]`。同じ request 順、同じ missing→`None`、同じ OID を返す。
- `_batch_blob_bytes` は引き続き `dict[str, bytes]`。first-occurrence dedup、挿入順、blob bytes が同じ。
- `git cat-file` は入力1行ごとに完結した応答を同順で返すため、連続する chunk output の `b"".join(...)` は単一 invocation の応答列と同じになる。
- parse を chunk ごとに行わず、全出力連結後に既存 parser を使うため、件数ずれや header 異常の判定順も保存できる。
- `_batch_oids`、`_batch_blob_bytes`、公開 API の signature は変更しない。

## 2. 総 wall-clock 予算

「operation」は、分割前の1回の bulk Git invocation と定義します。`validate_condition_freeze_at` 全体を新たに15秒へ押し込める設計は採りません。従来複数あった15秒 invocation や Python parse まで一括制限し、受理集合を縮めるためです。

| 論理 operation | 分割前 | 変更後 |
|---|---:|---:|
| `_batch_oids` の `--batch-check` | 1 call × 最大15秒 | 全 chunk で共通の絶対締切15秒 |
| `_batch_blob_bytes` の size-check | 1 call × 最大15秒 | size chunk 全体で15秒 |
| `_batch_blob_bytes` の blob-read | 1 call × 最大15秒 | blob chunk 全体で15秒 |

したがって `_batch_blob_bytes` 全体の Git 待ち上限は従来同様、最大15秒＋15秒です。1つの30秒共有締切にはしません。それでは size phase 単独で15秒を超えても後段の余りを使えてしまい、従来 `git-timeout` だった実行を受理するためです。

締切は全 request bytes の集計検査後、最初の chunk を起動する直前に1回だけ作ります。同じ float を全 chunk の `_git(..., deadline=deadline)` へ渡します。履歴長比例の予算は、履歴が長いほど旧15秒 gate を緩めるので不採用です。

変更する signature と caller は次のとおりです。

- `_git(:880)`: `deadline=None` を追加。
  - `_git_text(:911)` と `read_blob_at(:956)` など既存の非 chunk caller は省略し、従来どおり15秒。
  - 新 `_git_chunked` だけが同じ絶対締切を全 chunk に渡す。
- `_git_text(:909)`: `stdin_lines=None` を追加。
  - `_assert_repository_safe(:917/:919/:921)`、`resolve_commit(:932)`、`read_blob_at(:944)`、`_commit_graph(:1064)`、`_history_namespace_paths(:1089/:1094)`、`prepare_revision(:1662)` は省略し、挙動不変。
  - `_batch_blob_bytes(:1137)` だけが size phase の行列を渡す。
- `_batch_oids` と `_batch_blob_bytes`: signature 不変。
  - `_assert_rulings_exist(:1289-1290)` と `validate_condition_freeze_at(:1326-1327)` は変更不要。

予算切れは既存の `git-timeout` を使います。新 reason code は作りません。絶対締切切れと `subprocess.TimeoutExpired` は同じ資源 gate の失敗であり、既存 consumer は既に `git-timeout` を `freeze_reason_code` として扱っています。

## 3. 集計上限

| 上限 | 素朴な分割で緩むか | 手当て |
|---|---|---|
| `MAX_GIT_OUTPUT_BYTES` | 緩む | 各「旧1 invocation」に属する chunk の raw output bytes を累積する。size phase と blob phase は旧来別 call なので別集計。 |
| `MAX_GIT_INPUT_BYTES` | 緩む | chunk 前に全 `stdin_lines` の byte 長を合計し、旧 full stdin と同じ値で `git-input-limit`。各 `_git` の per-chunk 検査も残す。 |
| `MAX_BATCH_REQUESTS` | 現在の積の事前検査を残せば緩まない | `_batch_oids` の product guard を chunk loop より前に固定する。chunk ごとにリセットしない。 |
| `MAX_BLOB_BYTES` | 緩まない | 全 size output を連結してから、各 blob header へ従来どおり適用する。 |
| `MAX_TOTAL_BLOB_BYTES` | 緩まない | dedup 済み全 OID の `sum(sizes)` を blob phase 開始前に一度だけ検査する。 |

`MAX_BATCH_REQUESTS` は現在 `_batch_oids` の guard であり、`_batch_blob_bytes` へ直接は適用されていません。新たに後者へ同 guard を足すと direct private caller の受理集合を縮めるため追加しません。production 経路では `_batch_blob_bytes` の OID は `_batch_oids` の結果由来なので、unique OID 数はその閉包内です。

## 4. 受理集合の不変性

| reason code | 現在の guard | 分割上の危険 | 閉じ方 |
|---|---|---|---|
| `batch-request-limit` | 全 commit×path 数 | chunk ごとの検査なら緩む | 分割前に全体 product を検査。 |
| `git-input-limit` | 旧 full stdin bytes | 各 chunk が小さければ通る | 全 request-line bytes を先に合計。 |
| `git-timeout` | 旧 invocation 1回15秒 | N×15秒へ緩む | 旧 invocation ごとに絶対締切を1つ共有。 |
| `git-output-limit` | 旧 invocation の全 raw output | chunk ごとなら緩む | parse 前に chunk 横断で累積。 |
| `git-failed` | Git/OSError/非0終了 | chunk 化で呼出回数が増える | どの chunk の失敗も同じ `git-failed` で即 reject。 |
| `git-output-utf8` | size-check の decode 不良 | chunk 単位 decode で判定順が変わる | raw output を全連結後、`_git_text` の既存 strict decode を1回行う。 |
| `cat-file-count` | 全要求数と全応答行数 | chunk 単位検査で理由が変わり得る | 全 raw output を連結後に既存全体件数検査。 |
| `cat-file-header` | size/header schema | chunk parser 化で順序が変わる | 現在の parser を連結結果へそのまま適用。 |
| `path-not-blob` | missing 以外の非blob | 同上 | request 順と全体 parser を維持。 |
| `blob-byte-limit` | 各 header size | なし | 全 header への現在の検査を維持。 |
| `blob-total-byte-limit` | unique OID 全体の合計 | chunk ごとの sum なら緩む | 全 size phase 完了後に1回だけ `sum(sizes)`。 |
| `cat-file-truncated` | blob output の改行欠落 | chunk 境界を EOF と誤認 | chunk 出力を連結してから現在の offset parser。 |
| `cat-file-size` | 宣言 size と framing | 同上 | 連結後に検査。 |
| `cat-file-extra` | 全要求処理後の余剰 bytes | chunk ごとの末尾検査で理由が変わる | 全連結結果の最終 offset で検査。 |

この手当て後、決定論的な内容・サイズ guard に緩むものはありません。なお `_batch_oids` の不正 UTF-8 と `_batch_blob_bytes` の一部非数値 header は現在も素の `UnicodeDecodeError` / `ValueError` になり得ます。既存 `PreregistrationError` reason ではないため、本 wave では挙動を変えません。

## 5. テスト計画

追加先は [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_core.py) の既存 resource guard 群 `:947-1054` 直後です。実 Git repository や履歴範囲は使わず、`tmp_path` は cwd の型だけ、Git 応答は monkeypatch で決定論的に与えます。

| 純増点 | 追加 nodeid・現在の配置 | fixture / monkeypatch / 主 assert |
|---|---|---|
| (a) OID 結果同一性 | `::test_batch_oids_chunking_matches_single_call_result`、`:1016-1033` の後 | `tmp_path`, `monkeypatch`。`M._git` を stdin 1行ごとの正規 header/missing 応答へ置換。chunk 幅を全件超と `2` に変えて、`list(result.items())` が完全一致し、split 時の call 数が増えることを確認。 |
| (a) blob 結果同一性 | `::test_batch_blob_bytes_chunking_matches_single_call_result`、`:1036-1054` の後 | 重複 OID を含む fixture。`M._git` が size header と raw blob framing を返す。単一幅と幅 `2` で dict の順序・keys・bytes が完全一致。size phase 内、blob phase 内で全 chunk に同じ deadline が渡ることも spy する。 |
| (b) 入力集計 | `::test_chunked_git_input_limit_is_aggregate_across_chunks`、`:987-998` の後 | 幅 `1`、各行は上限内だが2行合計は上限超。`M._git` は must-not-run。`git-input-limit` と call 0。 |
| (b) request 集計 | `::test_batch_request_limit_applies_before_chunking`、`:1016-1033` の後 | 幅 `1`、`MAX_BATCH_REQUESTS=2`、要求3件。`M._git` must-not-run、`batch-request-limit`。 |
| (b) output 集計 | `::test_chunked_git_output_limit_is_aggregate[oids]`、`[blob-size]`、`[blob-data]`、`:1001-1014` の後 | 幅 `1`。各 chunk は上限内、同じ旧 invocation の合計だけが上限超になる fake。各 phase で `git-output-limit`。blob-data case では size phase 合計は上限内にする。 |
| (c) per-call 15秒 | `::test_git_deadline_uses_remaining_time_without_exceeding_per_call_cap`、`:947-984` の後 | `M.time.monotonic` と `M.subprocess.run`。残り10秒なら `timeout=10`、締切なし／残り15秒超なら `timeout=15.0`。 |
| (c) operation 総時間 | `::test_batch_oids_chunks_share_one_monotonic_deadline`、同じ timeout 群の後 | 幅 `1`、fake clock と `M._git`。各 chunk は6秒相当で単独15秒未満、3 chunk 合計18秒。全 call が同じ deadline を受け、3回目までに `git-timeout` になることを確認。deadline の作り直しなら赤になる。 |

既存の次の期待値は一切変更しません。

- `:981/:984` の `git-timeout`
- `:997` の `git-input-limit`
- `:1011` の `git-output-limit`
- `:1024-1033` の `batch-request-limit`

[test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_s8c_preregistration_invariant.py) は変更しません。特に `:124-161` の `repository_candidate_commit` と全履歴を通る `validate_condition_freeze_at` をそのまま acceptance とし、履歴範囲・generation・検査内容を縮めません。

read-only 指示に従い pytest は実行しておらず、緑は主張しません。

## 6. 静的 caller / consumer とリスク

使用した閉包検索式は次です。

```text
rg -n --glob '*.py' '\b(_batch_oids|_batch_blob_bytes|validate_condition_freeze_at|condition_freeze_valid_at|activation_report_at|effective_at|require_effective_preregistration)\b' .
rg -n --glob '*.py' '\b(_git|_git_text)\s*\(' orchestrator/campaign/s8c_preregistration.py orchestrator/tests/test_s8c_preregistration_core.py
```

### 直接 caller

- `_batch_oids` / `_batch_blob_bytes`
  - `s8c_preregistration.py:1289-1290` — `_assert_rulings_exist`
  - `:1326-1327` — `validate_condition_freeze_at`
  - core test `:1028`, `:1053`
- `validate_condition_freeze_at`
  - `s8c_preregistration.py:1431` — `condition_freeze_valid_at`
  - `:1547` — `_activation_report_at`
  - `:1688` — `prepare_revision`
  - core test `:483,492,496,507,514,523,540,550,558,573,586,622,649,674,763,774,804`
  - invariant test `:131`
- `activation_report_at`
  - `s8c_preregistration.py:1618` — `effective_at`
  - `:1769` — `require_effective_preregistration`
  - `:1803` — `check` CLI
  - core test `:690,860,879,896`
  - predicate test `:436,446`
  - invariant test `:195`
- `condition_freeze_valid_at`
  - repository内に実 caller なし。
- `effective_at`
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:2348`
  - `orchestrator/campaign/trial_registry.py:2484`
  - public-signature test `test_s8c_preregistration_core.py:897`
  - monkeypatch consumer `test_p3_autonomous_workload_trial.py:3819`
- `require_effective_preregistration`
  - `trial_registry.py:1223` — registered launch admission
  - `trial_registry.py:2211` — formal acceptance
  - core test `:699,715,729,744`
  - `test_trial_registry.py:916` の negative-control monkeypatch
- 非 Python の契約 consumer
  - `s8c_preregistration_evidence_contract.v1.json:289` の `effective_at(prereg_commit) -> run start`

### 発効経路への影響

成功時は OID/None mapping、freeze record bytes、Markdown/evidence hash、blob bytes が同一なので、`FreezeValidation`、`ActivationReport`、`effective`、report digest の意味は変わりません。freeze JSON producer と `output/s8c-preregistration/condition-freeze/*.json` は無変更です。

失敗時は従来と同様 fail-closed です。

- deadline超過 → `git-timeout`
- aggregate output超過 → `git-output-limit`
- `_activation_report_at` はこれを `freeze_reason_code` に記録し `effective=False`
- `effective_at` は `None`
- trial launch / acceptance は exact capability を得られず拒否
- `prepare-revision` は destination 作成前に例外となり CLI rc=2

主なリスクは次です。

- 現在の約6,861 OID request は幅2,000で4 process になる。process 起動・pack 読み直しが増え、同じ15秒内では単一 process より遅くなる可能性がある。
- g2以降は `_assert_rulings_exist` でも同じ helper を通るため、decisions blob 検証にも性能差が波及する。
- `_commit_graph` と `_history_namespace_paths` は引き続き単一15秒 call であり、別の timeout producer は残る。
- private `_git` monkeypatch が新しい `deadline=` keyword を受けられない場合はテストが壊れる。ただし現存 fake はいずれも `**kwargs` を受けており静的には問題ない。
- `xdist_group` は同一 group の配置 affinity であり、他 worker からの負荷を排除する排他 fixture ではない。

## 親 brief へ返す問題

1. 「今日 reject される入力をすべて維持」と、今回観測した同じ candidate の `git-timeout` を成功させる目的は、文字どおりには両立しません。維持できるのは内容・サイズ guard と「15秒を超えた実行は同じ reason で reject」という境界です。

2. 同じ aggregate work を同じ15秒内で複数 process に分けても、wall-clock が短くなる保証はありません。親実測は単一 call が無負荷約2秒、全走負荷下で15秒超ですが、chunk がその差を改善する証拠はまだありません。

3. brief の「`MAX_BATCH_REQUESTS` が15秒と自己矛盾」という主張は、総締切を15秒に保つ本案では解消しません。分割は1 process の大きさを制限するだけで、50,000 request を15秒で処理できる容量証明にはなりません。

4. F57 の引用は「production gate を緩めず test fixture を harden」ですが、本 scope は production chunking だけで fixture を harden しません。段 4 で、これを contention mitigation として試すのか、fixture 側の全走負荷隔離を scope に戻すのかを裁定すべきです。後者でも履歴範囲を縮める案は不要です。

## 総括

採る設計: 固定幅 `MAX_GIT_BATCH_REQUESTS_PER_CALL = 2_000`、旧 Git invocation ごとの15秒絶対締切、入力・出力のchunk横断集計。  
戻り値・public signature・reason code・freeze bytesは維持し、既存4 guardテストと全履歴 invariant は変更しない。  
履歴比例予算と validation 全体15秒化はいずれも不採用。

未解決の設計択一: 実装案内部にはなし。実測で赤を閉じるかは親 acceptance の go/no-go 条件。

親への差し戻し: chunking の有効性未証明、F57 の fixture hardening と scope の不一致、literal な受理集合不変との矛盾、15秒のままでは最大要求容量の自己矛盾が残る点。