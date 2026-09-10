単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md` — **段 4 裁定。これが実装の正本である。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値 (逐語)。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/brief.md` — 段 1 brief。**裁定で訂正された箇所がある** (下記)。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s2-plan.md` — 段 2 プラン。**裁定で否定された test 設計を含む。**
  test 設計は裁定の「プラン v2」で上書きされている。プランの test 設計をそのまま実装してはならない。

repo の path は次の worktree のものだけを使う。ここがあなたの作業ツリーである。

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site`

親 checkout (`/work/1/SFC/tanab/izanagi/orchestrator/...`) の path を使ってはならない。

## 段の宣言

これは段 5 (実装) である。sandbox は workspace-write。

- **コードとテストだけを編集する。** docs を編集してはならない。
- **commit してはならない。** `git commit` / `git add` / `git stash` / branch 操作をしてはならない。
  統合 commit は親が行う。
- push・remote 操作をしてはならない。
- 出力に結合文字 U+0300〜U+036F を使うな。
- 予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 実装するもの

段 4 裁定の「プラン v2」節をそのまま実装せよ。要点だけ再掲する
(**逐語の正本は裁定ファイル。食い違ったら裁定を優先せよ**)。

### 変更 1 — `orchestrator/campaign/p3_b4_launcher.py` の `_driver_configs`

`configs` を作った後の射影分岐を `if driver_kind == "base": ... elif driver_kind == "trigger": ...`
にする。base は `p3_s4_loop` の `_current_site()` → `_admit_env_contract(site)` →
`_campaign_cfg_for_site(cfg, site, _contract=contract)` を、既存 trigger 分岐と同じ順・同じ形で呼ぶ。
`sort` はどちらの分岐も通らない。driver 種の一般 dispatch 表へ畳んではならない。

### 変更 2 — `orchestrator/tests/test_p3_b4_launcher.py` に node N1〜N5 を足す

裁定の N1〜N5 の**性質**を満たすこと。node 名は既存の命名に合わせて自分で決めてよいが、
各 node がどの N に対応するかを報告に書け。

- **N1**: site=PEGASUS_COMPUTE (`site_policy.socket` を `bnode116` へ差し替え) で
  `_driver_configs("base", ctx)` の on/off 両 config の `ident.campaign_id` が、
  未射影 `default_cfg` の ID と**異なり**、`_campaign_cfg_for_site` を掛けた ID と**一致する**。
- **N2**: 同じ返り値の `bound_environment_contract` が解決済み contract と一致することを
  PEGASUS_COMPUTE と OTHER の両方で pin する。
- **N3**: launcher が作った context で **実物の** `require_b4_production_context` と
  `verify_launch_context` (G4) を PEGASUS_COMPUTE 下で通す。test 自身の算術で ID を比べない。
- **N4**: site=OTHER で `_driver_configs("base", ctx)` の ID が未射影 `default_cfg` と一致し、
  `measurement_env` が付かない。
- **N5**: site=PEGASUS_COMPUTE で `_driver_configs("sort", ctx)` の ID が未射影 sort
  `default_cfg` と一致する (射影されない)。

**seam**: `site_policy.socket` を差し替える (最下層 resolver)。`classify_site` は `environ` を
明示的に捨てるので環境変数は seam ではない。`current_site` に site 注入引数は無い。
`conftest.py:239-255` の中立化は autouse・function scope で setup 時に効き、
test body の再差し替えが後から勝つ。この事実は親が確認済みである。

## 絶対に守る不変条件

- **授権境界の拒否力を弱めない。** `require_b4_production_context` /
  `validate_production_context` / `require_any_context` の比較を緩めない。
  射影を足して「一致するようになる」のであって、比較を弱めるのではない。
- `_site_admits_measurement` の exact set を広げない。
- OTHER の campaign_id を変えない。
- `sort` の挙動を 1 bit も変えない。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・xfail 化を禁じる。
  既存テストが赤になったら実装側が誤りである。期待値のほうが誤りだと判断した場合は、
  実装を変えずに報告して止めよ。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしてはならない。
- 期待値へ揮発 payload (working tree hash、時刻、pid 等) を焼き込んではならない。
- 機構の正例・負例は実体を名指しし、依存先を stub して機構を迂回してはならない。
  特に負例は「今回入れる base 射影が無いと赤くなる」ものでなければならない。
  `_driver_configs` を通らずに手で作った config だけで赤くなる負例は**失格**である。

## 触ってはいけない file

`p3_s4_loop.py` / `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` / `site_policy.py` /
`ident.py` / `p3_b4_closed_critic.py` / `campaign_lock.py` / 事前登録 doc /
`orchestrator/tests/acceptance_duration_ledger.json` / docs 全般。

`[T-2317]` の `_assert_layout_matches_campaign` / `_with_campaign_location` 移植、
`[T-2318]` の sort 対応、仮想リスク向けの新しい gate・検査・台帳・一般化、
本題と無関係な refactor・命名変更・型注釈整理は、すべて scope 外である。足してはならない。

## 検査と報告の義務

- **緑には実走した nodeid と範囲を併記せよ。** 実走していない検査を「通した」と書いてはならない。
- 実走できない場合は `closed` と申告せず「実装済み・未実走」と書け。
- テストを新設したので、**親の名指しを網羅と見なさず、制約 meta-test を自分で洗い出して走らせよ。**
  この repo には test file の構造・命名・登録に関する meta-test がある。自分で探して走らせること。
- **この worktree では `python3 -m pytest` は guard に拒否される。** repo の自走 harness を使え。
  `PYTHONPATH=.` が要る場合がある。使った argv をそのまま報告に書け。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性を静的に列挙せよ。
  親の実測では `_driver_configs` の呼び手は直接 3 箇所 (`test_p3_b4_closed_critic.py:185,532,2702`)、
  `_marked_driver_configs` 経由 4 箇所 (`:819,1002,1029,2322`)、production 本体
  `p3_b4_launcher.py:547`、および `launch_bootstrap` / `launch_continuation` 経由の多数である。
- scope 前の現行の受理・拒否挙動を明記し、指示外の受理集合変更をしてはならない。
- 赤が残ったら、その内訳 (nodeid と理由) を完了報告に必ず書け。隠してはならない。

## 参考: 親が実測済みの事実 (再測不要)

- `_admit_env_contract` は site 4 値のうち PEGASUS_LOGIN と PEGASUS_SUSPECT で
  `ExecutionGuardError` を投げ、OTHER と PEGASUS_COMPUTE でのみ契約を返す。
- PEGASUS_COMPUTE の射影は campaign ID を変え、OTHER では変えない。射影は冪等である。
- この wave の baseline は
  `orchestrator/tests/test_p3_b4_launcher.py` + `orchestrator/tests/test_p3_b4_closed_critic.py`
  の焦点走で **106 passed / rc=0** (緑)。

## 出力形式

以下の H2 見出しをこの順で使え。

## 実装した変更 (file:line)
## 追加した test node と対応する N
## 実走した検査 (argv と nodeid と結果)
## 残った赤
## 波及の静的列挙
## 総括
