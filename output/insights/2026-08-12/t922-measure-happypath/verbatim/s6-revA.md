# 段 6 敵対レビュー A — T-922

静的レビューのみ実施した。pytest・再測定は行っていない。

## BLOCKER — 解決不能な linked worktree 登録を skip すると受理集合が広がる

`tools/pegasus/t810_coordinator.py:533-552` は、登録先が `FileNotFoundError` になると、その worktree root を roots から除外する。

具体入力:

- main root: `/srv/izanagi`
- common dir: `/srv/izanagi/.git`
- 外部 linked worktree: `/scratch/izanagi-wt`
- 登録: `/srv/izanagi/.git/worktrees/ext/gitdir`
- 変更前の登録内容: `/scratch/izanagi-wt/.git\n`
- `work_root`: `/scratch/izanagi-wt/output/t810`
- caller roots: `{"/tmp/forged-repository"}`

変更前は `/scratch/izanagi-wt/.git` が解決され、root `/scratch/izanagi-wt` が集合に入り、`work_root` は拒否される。登録内容を `/scratch/removed-worktree/.git\n` に差し替えると、変更後は `FileNotFoundError` を skip し、元の `/scratch/izanagi-wt` が roots から消える。そのため同じ `work_root` が repository-external として受理される。

期待: live common-dir に解決不能な登録があれば fail-closed。

実際: 解決不能な登録だけを無視して処理を続行する。新テスト `orchestrator/tests/test_t810_coordinator.py:1024-1040` は、この fail-open を正例として固定している。

親の論拠は部分的にだけ正しい。`/srv/izanagi/.claude/worktrees/x` は main root の子なので保護される。一方、`/scratch/izanagi-wt` のような main root 外の linked worktree は保護されない。したがって裁定の「caller は roots を増やすことしかできず迂回不能」という主張（`s4-adjudication.md:59-61`）は、live registry が欠落・改変しないという未記載の前提を必要とする。

成果物影響: repo 内へ work/output/ledger を置く入力が新たに受理され、repository-external 境界が破れる。

## BLOCKER — staged wrapper 統合テストが repo 依存を隠している

`orchestrator/tests/test_t810_coordinator.py:905-933` は、一時 package に次しか置いていない。

- `package/wrapper.py`
- `package/CCBench`
- `package/dependencies.json`

しかし子 process の `PYTHONPATH` は `runtime-shim:<repo-root>` である（同 `:924-927`）。そのため wrapper 冒頭の `from tools.pegasus import ...` は staged package ではなく repo から解決される。

具体入力:

- wrapper: `/tmp/t810/package/wrapper.py`
- cwd: `/tmp/t810/work`
- `PYTHONPATH=/tmp/t810/runtime-shim:<repo-root>` — 現テスト
- `PYTHONPATH=/tmp/t810/runtime-shim` — repository-independent な実行条件

期待: 後者でも staged wrapper が静的 request の decode と PBS runtime identity 補完まで到達する。

実際: package に `t810_harness_schema.py` と `t810_runner_policy.py` がないため、repo を外すと最初の package import と standalone fallback の双方が解決不能になり、request parse より前に停止する。現テストが証明するのは「staged wrapper file＋repo 実装」の混成経路だけであり、裁定 `s4-adjudication.md:67-74` の repository-external staged CLI 経路を代表しない。

これは R2 の「依存 bytes の authority」を閉じろという所見ではない。依存を一時 package に同梱し、repo を `PYTHONPATH` から外して実行するだけでも、authority を主張せず可用性を代表できる。現状は scope 内 S-D′ の唯一の統合証拠が test-only な依存で成立している。

成果物影響: staged package が計算ノードで import 前に失敗しても、land 前検査が緑になりうる。

## MAJOR — 統合テストは生成された PBS script 自体を実行していない

`orchestrator/tests/test_t810_coordinator.py:908-931` は script の最終行を読み、`shlex.split()` した argv を直接 `subprocess.run()` する。script file、shebang、`set -eu`、それ以前の行は実行されない。

具体変異:

```sh
#!/bin/sh
set -eu
exit 77
exec python3.10 /tmp/t810/package/wrapper.py --request /tmp/t810/work/slot-00/wrapper-request.json
```

期待: production では `exit 77` により wrapper CLI へ到達しないので統合テストが失敗する。

実際: 最終行は変わらないため、現テストはそれを直接実行して従来どおり wrapper へ到達する。generator と `_assert_canonical_job_script()` を同じ変異で更新すれば scheduler 側の自己整合検査にも拒否されない。

これは恒真テストではないが、「生成 script → staged CLI」ではなく「script 最終行から再構成した argv → staged CLI」の検査である。

成果物影響: 実際の PBS artifact が wrapper を起動不能でも、統合経路成立として記録されうる。

## 新設ゲートの恒真性検算

### `_assert_declared_file_identity`

発火する入力:

- file bytes: `b"evil"`
- declared SHA-256: `770e607624d689265ca6c44884d0807d9b054d23c473c106c72be9de08b7376c`（`b"good"` の digest）

結果: `declared SHA-256` 不一致で拒否する。`tools/pegasus/t810_coordinator.py:201-211`。

発火しない入力:

- file bytes: `b"evil"`
- declared SHA-256: `b5c1fb2efc6d6b4674c2fdcc48ce01b43a3b7c03763c0c3355de0099ee0f8c73`

結果: 通る。binary が自己整合した任意 bytes でも同じであり、これは裁定 R1 の残余と一致する。恒真ではない。

### 同梱 wrapper anchor

発火する入力:

- staged wrapper bytes: `b"evil"`
- `wrapper_sha256`: 上記 `b5c1...f8c73`
- shipped wrapper: coordinator と同じ directory の現 `t810_pbs_wrapper.py`

宣言検査は通るが、shipped bytes と異なるため `shipped wrapper bytes` で拒否する。`tools/pegasus/t810_coordinator.py:213-223`。

発火しない入力:

- staged wrapper bytes: shipped wrapper の完全な byte copy
- `wrapper_sha256`: その copy の SHA-256

結果: 通る。ただし同じ package の `t810_runner_policy.py` だけを別実装にしてもこの anchor は発火しない。これは裁定 R2 と一致する。恒真ではない。

### live repo anchor

発火する入力:

- coordinator root: 現 repo root
- `work_root=<repo-root>/orchestrator`
- caller roots: `{"/tmp/forged-caller-repository"}`

結果: caller 値にかかわらず最初の mkdir 前に拒否する。`tools/pegasus/t810_coordinator.py:695-708`。

発火しない正当入力:

- `work_root=/tmp/t810-external/work`
- `output_root=/tmp/t810-external/output`
- caller roots: `{"/tmp/unrelated-repository"}`

結果: repository root の外なので通る。

発火しない不正入力は最初の BLOCKER の外部 linked worktree 例である。したがって恒真ではないが、不完全な fail-open gate である。

## `publish_wrapper_request()` の逆参照

`tools/pegasus/t810_pbs_wrapper.py:353-358` の遅延 import については、現行経路で循環 import による破損は確認しなかった。

- coordinator import 時に wrapper の module 定義は完了する。
- `publish_wrapper_request()` が呼ばれる時点で coordinator helper も定義済みである。
- 計算ノードの wrapper `main()` は `publish_wrapper_request()` を呼ばないため、staged package に coordinator がないことだけで node main が壊れるわけではない。
- standalone package 上で publisher 自体を呼べば coordinator import が必要になるという新しい結合はある。ただし現行の node main への影響はない。

D331 との意味上の矛盾もない。private 名を認可境界として信頼しているわけではなく、effect 側の token 検査は残っている。ただし `_assert_staged_file_identities` は今後 shared API のように扱われるため、private 名変更が wrapper publisher を壊す結合になった。

## `sitecustomize.py` の代表性

production コードの次の条件は変更されていない。

- load 閾値: `<= 1.0`
- 連続サンプル数: 3
- deadline: `READY_TIMEOUT_SECONDS`
- sleep 要求: 最大 30 秒

一方、統合テストでは `os.getloadavg()` を常に `0.0`、`time.sleep()` を no-op にするため、3 サンプルは30秒間隔ではなく連続取得される。したがって、このテストは間隔やdeadlineの統合検査ではない。

ただし期待結果は `returncode == 2` / `pre_release_invalid` であり、production の受理正例を装ったテストではない。node probe を通過する正例を主張してもいない。単体の quiet-gate 検査が別にあるため、sitecustomize 自体を correctness gate 緩和とは判定しない。重大なのは、それと同じ `PYTHONPATH` で repo 実装まで注入している点である。

## 規律 1・裁定 §3

追加 I/O は次の時点にある。

- `prepare_group()` の repo identity 解決
- request publication 前の wrapper/binary 読取
- qsub effect 直前の wrapper/binary 再読取

いずれも benchmark measurement loop や性能計測 build 内ではない。規律 1 違反は確認しなかった。

R1 の binary authority は閉じていない。自己整合した任意 binary は通る。R2 とR3も残っている。guard/budget の2相化や canonical ledger anchor の半実装は差分にない。追加 helper は publication と scheduler の両方から呼ばれており、dead API でもない。

## 総括

**NO-GO**

**BLOCKER: 2件**

外部 linked worktree の fail-open は受理集合を直接広げる。加えて、scope 内とされた staged wrapper 統合経路は repo 注入なしでは成立する証拠がなく、現状のテストでは land 判定に使えない。