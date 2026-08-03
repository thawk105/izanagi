結論は **NO-GO**。面 1〜3 の局所的な負例は作れるものの、「正本 1 箇所」と「実成果物を守る全層」という brief の主張が成立していない。

### 面 3 は API 単位なら帰属するが、単層 KILL を child E2E の証明にすると F28 を再発する

- 深刻度: must-fix
- 根拠: `DW-M01` は先行拒否と単一理由性を要求する（[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/dev-wave/mutation.md:5)）。各面の前段検査は次のとおり。

| 面 | 値域検査より手前の検査 | 帰属 |
|---|---|---|
| 面 1 | subcommand 必須、`run` 選択、`--reasoning` の存在・値トークンだけ。型・正規表現検査なし（[codex_worker_launch.py:2461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2461)、[:2475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2475)）。下流は値をそのまま渡し（[:1104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:1104)）、rollout と等しいかを見るだけ（[:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:774)）。 | 成立 |
| 面 2 | subcommand 必須、`serve` 選択、`--effort` の存在・値トークンだけ（[cli.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:74)、[:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:92)）。下流の `SupervisorProfile` も非空 ASCII しか見ない（[daemon.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/daemon.py:219)）。 | parser の受理集合について成立 |
| 面 3 / spec | strict JSON、exact field set、schema version、environment、receipt schema の canonical/digest、budget、model 形検査の後、effort の文字列型と `_EFFORT_RE`（[schema.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:771)）。 | `none` なら成立 |
| 面 3 / argv | 長さ、全 token の文字列・非空・NUL、禁止 token、固定 token、option 順、model/effort 正規表現（[schema.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:835)）。 | `none` なら成立 |

  `_EFFORT_RE = [a-z][a-z0-9-]{0,31}`（[schema.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:832)）なので `none` は形検査を通り、提案集合には含まれない。

  ただし公開 worker 経路では `parse_worker_spec()` の後に `build_child_argv()` が再検査する（[worker.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:590)、[:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:231)）。片方だけを無効化しても他方が実 child を止める。直接 API テストは両関数とも `__all__` にあるため偽 KILL ではないが（[schema.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:869)）、それを E2E 防壁の KILL と数えてはならない。
- 失敗シナリオ: `effort="none"` の正しい形の worker spec → spec 側 membership だけ除去 → argv 側 membership が拒否し、実 child の受理集合は変わらないのに spec 単体テストだけ赤くなる。
- 成果物影響: 単層 KILL を E2E 証明として記録すると、変異台帳が実効受理集合を変えていない防壁を KILLED と誤認し、材料レポートの gate 根拠が偽になる。

段 4 では「各 exported API の単層変異」と「両 membership を同時に外す child E2E 変異」を分けて事前登録すべきである。

### 「許可リストの正本 1 箇所」は plan 適用後も成立しない

- 深刻度: blocker
- 根拠: plan 後も閉集合の独立宣言は **4 ファイル・5 集合オブジェクト**残る。

| 場所 | 集合 | 分類 |
|---|---|---|
| 新 `effort_levels.py` | Claude と Codex の各 `{low,medium,high,xhigh,max}` | capability 2 集合（[s2-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s2-plan.md:23)） |
| `launcher.py` | `{low,medium,high,xhigh}` | role runtime 検査（[launcher.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/launcher.py:349)） |
| `spec.py` | `{medium,high}` と role 固定組合せ | manifest policy（[spec.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:602)） |
| `codex_reasoning_ab.py` | `{max,high}` | live な凍結実験 arm（[codex_reasoning_ab.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_reasoning_ab.py:160)、[:5223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_reasoning_ab.py:5223)） |

  さらに値の live copy は manifest 1 ファイル、frontmatter 13 ファイル、worker 契約 1 ファイルに残る。したがって論理上 7 層、物理上 19 ファイルで reasoning/effort が規定される。

  - manifest の Claude/Codex 値集合はいずれも `{medium,high}`（[manifest.json:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/manifest.json:14)、[:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/manifest.json:339)）。
  - frontmatter も `{medium,high}`。`medium` は calibrator/coder/verifier、残り 10 件は `high`（例: [calibrator.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/.claude/agents/calibrator.md:6)、[auditor.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/.claude/agents/auditor.md:6)）。
  - frontmatter と manifest の一致・hash pin はある（[spec.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:582)）が、新 capability 集合との subset 検査はない。
  - `check_docs.py` は節名と dispatch を検査するだけで、`reasoning=max/high` の集合整合を見ない（[check_docs.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/check_docs.py:374)、[:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/check_docs.py:423)）。

  F39 の分類では、manifest/frontmatter は live copy、`review_ledger.py` の hash は独立 golden、A/B の既存成果物は凍結 snapshot、過去 insight の `max` 記録は歴史記録である。plan はこの分類をせず「policy subset」と呼んで scope 外にしている。
- 失敗シナリオ: `workers.md` の `reasoning=max` を `ultra` に変更 → `check_docs.py` は通る → `DW-O01` の直接 `codex exec` が新 catalog を参照せず起動 → requested reasoning と実効 reasoning がずれる。
- 成果物影響: drift 後のレビュー結果が誤った reasoning 名で材料レポートへ入り、certified 選択が参照する実行条件を取り違える。

role/実験 subset を広い capability 集合へ置換してはならないが、少なくとも全 subset・manifest/frontmatter・worker 条文が capability の部分集合であることを機械検査し、冗長な launcher 検査を整理する必要がある。

### 3 面はいずれも現行 dev-wave の実 Codex/Claude 経路を十分には守らない

- 深刻度: blocker
- 根拠:

  - M4 の `max` は live だが、段 2/3 は [workers.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/dev-wave/workers.md:7) と [:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/dev-wave/workers.md:12) から、[operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/dev-wave/operations.md:8) の `codex exec` を直接使う。repo 内に `codex_worker_launch.py --reasoning max` を渡す production caller はなく、コード caller はテストだけ（[test_codex_worker_launch.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:360)）。したがって M4 は面 1 について過剰一般化である。
  - 面 2/3 は D74 により fake-only で、real `claude -p` 経路自体が存在しない（[decisions.md:2955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/decisions.md:2955)、[:2991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/decisions.md:2991)）。
  - 試行台帳の `tools/task_runs/cli.py --reasoning` は無制限のまま（[cli.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/task_runs/cli.py:76)）、payload へそのまま入り（[:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/task_runs/cli.py:138)）、schema も slug 形しか検査しない（[schema.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/task_runs/schema.py:425)）。
  - 過去 receipt の `reasoning` は非空文字列なら通り（[codex_worker_launch.py:1983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:1983)）、`check-receipt --expect-reasoning` も unrestricted（[:2512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2512)）。
  - `codex_reasoning_ab.py` は直接 Codex を起動するが（[codex_reasoning_ab.py:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_reasoning_ab.py:1800)）、新 catalog とは無結線である。

- 失敗シナリオ: `task_runs ... agent_run --product codex --reasoning ultra ...` → CLI と schema が受理 → `agent_run.reasoning="ultra"` の試行台帳が publish される。3 面の新 gate は一度も通らない。
- 成果物影響: 試行台帳の reasoning 受理集合と legacy receipt の受理集合が変わらず、材料レポートは依然として不正 requested 値を参照できる。

裁定パッケージ候補は二択である。

1. `task_runs`、legacy receipt、DW-O01 直接経路、A/B arm の capability subset 検査まで scope を広げる。
2. scope を現行 3 面に保つ代わりに、成果物影響を「手動 launcher と fake supervisor の事前 hardening」に縮め、現行 certified/material/試行台帳を守る主張を削る。

面 2/3 を今入れる価値は一行で言えば、**real 開放前に永続 spec/argv と fixture の契約を固定し、不正値を将来の正常 baseline にしないこと**であり、現時点の実 Claude 子を守る価値はゼロである。

### `test_dev_waves_cli.py` の plain runner が新テストを黙って飛ばす

- 深刻度: must-fix
- 根拠: plan は同ファイルへ負例・正例を追加する（[s2-plan.md:150](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s2-plan.md:150)）が、`_run()` は既存テストを手列挙している（[test_dev_waves_cli.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:357)）。`test_plain_runner_coverage` は `_run`/`__main__` の存在しか見ず、列挙漏れを検出しない（[test_plain_runner_coverage.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_plain_runner_coverage.py:35)）。これは F42 の「既存ファイルへのテスト追加」型（[failures.md:872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/failures.md:872)）。
- 失敗シナリオ: effort choices を後日除去 → pytest では新負例が赤になるが、`python3 orchestrator/tests/test_dev_waves_cli.py` は新関数を呼ばず rc=0。
- 成果物影響: plain-runner の試行記録が偽緑となり、面 2 の gate が消えた checkout を検査済みとして参照できる。

新関数を `_run()` に追加し、同ファイルの直接実行と meta-test の両方を受入範囲へ明記する必要がある。

### M6 は既存の依存方向ではなく `tools/dev_waves → codex_roles` の新規辺である

- 深刻度: nit
- 根拠: 現在の `tools/dev_waves/schema.py` は標準ライブラリと相対 `redaction` だけに依存する（[schema.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:1)）。既存の `orchestrator` import は別スクリプト `codex_worker_launch.py` にしかない（[codex_worker_launch.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:35)）。さらに leaf import でも `codex_roles/__init__.py` が `spec`/`policy` を eager importし（[__init__.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/__init__.py:3)）、`spec` は review ledger を読む（[spec.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:26)）。現時点の循環はないが、独立 alias で schema を読むテスト（[test_dev_waves_schema.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:20)）へ role package 初期化を持ち込む。
- 失敗シナリオ: role ledger/import の退行 → effort と無関係な dev-waves schema の standalone collection が失敗。
- 成果物影響: 受理集合自体は変わらないが、面 3 の検査・変異実測が無関係な role import 赤で不能になるため nit。

neutral な `tools/effort_levels.py` 等なら新規依存辺を避けられる。

## 確認事項

- 過剰実装: 新 ReasonCode・新 exception は不要で、plan も既存 `INVALID_ARGS` / `DevWavesError` を正しく再利用している。7 論理ケース（3 面の負例・正例 + P2 順序保持）は過剰ではない。
- 並列分割: 現 plan の A/B/C はファイル上は素集合。`conftest.py`、package `__init__.py`、`schema.py.__all__` の編集も不要。ただし上記 blocker を直して `launcher.py` / `spec.py` / task-runs を追加するなら、段 4 で所有集合を再確定すること。
- F41: 本レビューでは実測値がなく再発していない。親の targeted/full/mutation 記録には、各走の実 checkout と commit を必ず併記する（[operations.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/docs/dev-wave/operations.md:102)）。現レビュー checkout は `e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e`。
- pytest は実行しておらず、緑の主張はしない。

## 総括

- GO / NO-GO: **NO-GO** — 正本の単一性と実成果物へ至る gate coverage が未成立。
- blocker: **2 件**。
- blocker 1: capability・role policy・実験 arm・live config・worker 条文の関係が機械束縛されず、「正本 1 箇所」が虚偽。
- blocker 2: 現行 direct dev-wave 起動、task-run 台帳、legacy receipt が 3 面を迂回する。
- 面 1: **変異帰属は成立する** — `none` より手前に値域検査がなく、choices 除去だけで CLI 受理集合が変わる。
- 面 2: **変異帰属は成立する** — `none` より手前は required/token 検査だけで、choices 除去だけで parser 受理集合が変わる。
- 面 3: **各 exported API 単位では成立する** — `none` は `_EFFORT_RE` を通る。ただし child E2E の帰属には spec/argv の二層同時変異が必要。
- 面 3 の具体例: **`none`**。