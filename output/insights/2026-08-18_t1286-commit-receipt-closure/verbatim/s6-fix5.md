## 総括

F1〜F6 はすべて実装し、攻撃入力の診断呼出しでは拒否を確認した。  
ただし必須 pytest runner が Pegasus dispatch 障害で本体未開始のため、全件 `partial` とする。  
dev-wave 規律どおりコード・テストのみ変更し、docs・hooks は未変更、commit も作成していない。

## 対応表 (closed/partial/regressed)

| Fix | 状態 | 判定理由 |
|---|---|---|
| F1 | `partial` | caller-built `VerifyResult` issuer を削除し負対照通過。pytest 未実走 |
| F2 | `partial` | certified view/source record/closure capability を必須化。pytest 未実走 |
| F3 | `partial` | 全 context 束縛、closure 台帳、一回消費を実装。pytest 未実走 |
| F4 | `partial` | WAL sink が実 lock bytes の SHA-256 を照合。lockless 維持。pytest 未実走 |
| F5 | `partial` | Git を `/usr/bin/git` に固定し子環境から `PATH` を除去。pytest 未実走 |
| F6 | `partial` | 未移行2 fixture を legacy raw helper へ移行。pytest 未実走 |

## 各 must-fix が塞がった根拠 (file:line)

- F1: `orchestrator/verifier/core.py:278-300` で実 `verify_trace_dir()` 完了後にだけ capability を生成する。caller-built `VerifyResult` は秘密 token を持たず `core.py:181-182` で拒否される。旧 `_issue_verification_capability` は消滅し、issuer census は `test_t1286_commit_receipt.py:603-621`。
- F2: admission-issued nonce は `artifact_admission.py:77-120` の closure 台帳に保持され、実 certified admission のみが `artifact_admission.py:1165-1172` で view に付与する。裸 mapping は `commit_receipt.py:379-386`、偽 view/capability は `commit_receipt.py:388-395` で拒否される。replay evidence issuer/token も runtime namespace から `commit_receipt.py:424-428` で削除される。
- F3: operation・variant・workload・sink・lock は object 自身ではなく `core.py:200-210` の closure 台帳に保存される。完全一致は `core.py:219-254`、再利用拒否は `core.py:243-245` と `core.py:265-276`、消費は receipt 発行前の `commit_receipt.py:297-312`。clone・属性改変・別 context の負対照は `test_t1286_commit_receipt.py:253-319`。
- F4: `wal.py:447-457` が物理 lock 存在時に raw bytes SHA-256 を再取得して validator へ渡す。`commit_receipt.py:348-365` が receipt 自身の値ではなく sink 観測値と照合する。lock 不在時だけ issuer binding を使用する。差替え後の直接 `wal.append` 負対照は `test_t1286_commit_receipt.py:170-192`。
- F5: 固定 executable と hardened argv は `contract_loader_binding.py:19-28,252-299`、`enforcement_source_ratification.py:30-46,180-209`。両 allowlist に `PATH` はなく、偽 Git は実行対象にならない。負対照は `test_t671_source_binding.py:392-423` と `test_enforcement_source_ratification.py:179-204`。
- F6: 歴史 WAL fixture 2件を `append_legacy_raw_commit` に移行した箇所は `test_p3_s4_loop.py:2294-2296,2338-2340`。production COMMIT sink を呼ばない。

## 変更点 (file:line)

- verifier capability 発行・束縛・消費: `orchestrator/verifier/core.py:159-308`
- primary/replay receipt admission: `orchestrator/verifier/commit_receipt.py:106-159,276-320,368-454`
- certified replay authority: `orchestrator/campaign/artifact_admission.py:77-127,1141-1194`
- pipeline context 配線: `orchestrator/campaign/pipeline.py:994-1005,1116-1124,1265-1274`
- replay consumer 配線: `orchestrator/campaign/replay.py:201-212`
- WAL lock 束縛: `orchestrator/campaign/wal.py:447-457`
- Git hardening: 上記2 verifier module
- 負対照、census、共有 receipt fixture、F6 fixture を更新

## 波及可能性

静的 caller census では production の変更対象は以下に限定される。

- primary verifier/issuer: `campaign/pipeline.py`
- replay admission: `campaign/replay.py`
- WAL validation: `campaign/wal.py`
- guided replay receipt consumer: `campaign/guided.py`
- 共有 fixture: `tests/commit_receipt_support.py`
- mock signature 追従: `test_campaign.py`、`test_s1_direct_comparison.py`
- closure member である `wal.py`、`contract_loader_binding.py`、`verifier/commit_receipt.py` を変更しているため、dirty tree 上の contract-loader-drift 系測定には波及し得る。

既存の構造期待 `len(commit_calls)==2`、`len(commit_calls)==4` は変更せず、診断呼出しで維持を確認した。

## 未実走・未解決

`python3 tools/run_tests.py orchestrator/tests/test_t1286_commit_receipt.py -q` は `qstat -Q preflight rc=1`、dispatch child `rc=16` となり、pytest 本体は開始されていない。このため `closed` は申告しない。

実行済み検査:

- 全変更 Python ファイルの `py_compile`: 成功
- `git diff --check`: 成功
- F1〜F6 の攻撃負対照・正常系の直接診断呼出し: 成功
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- docs・hooks の変更なし、commit なし