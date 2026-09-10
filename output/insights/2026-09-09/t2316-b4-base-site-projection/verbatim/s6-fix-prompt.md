単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md` — 段 4 裁定 (実装の正本)。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s6-ra.md` — 段 6 敵対レビュー A (逐語)。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s6-rb.md` — 段 6 敵対レビュー B (逐語)。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py`

repo の path は次の worktree のものだけを使う。ここがあなたの作業ツリーである。

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site`

## 段の宣言

これは段 6 (fix) である。sandbox は workspace-write。段 5 実装子の契約をそのまま継承する。

- **コードとテストだけを編集する。** docs を編集してはならない。
- **commit してはならない。** `git commit` / `git add` / `git stash` / branch 操作をしてはならない。
- push・remote 操作をしてはならない。
- 出力に結合文字 U+0300〜U+036F を使うな。
- 予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。無出力が最悪である。

## 背景 (実測済み・再測不要)

commit `db95ffb3b` で `_driver_configs` に base の site 射影を入れ、test node N1〜N5 を足した。
親が変異 probe を実走し、次を実測した。baseline は PASSED (rc=0、赤 node 0)。

| 変異 | 実測で赤くなった node |
|---|---|
| base 射影ブロック削除 | N1、N2、N3 |
| `_campaign_cfg_for_site` を marker だけに置換 | N2 |
| 分岐を `{"base","sort"}` へ拡大 | N5 |
| `_current_site()` を literal OTHER へ | N1、N2、N3 |
| base の helper を trigger の同名 helper へ差し替え | (SURVIVED = 等価変異。両実装は逐語同一) |

**しかし段 6 の敵対レビュー 2 本が、全 5 node を通過する非等価変異を 3 つ見つけた。**
あなたの仕事はこの 3 つを殺せるように test を強くすることである。

## 直すもの (must-fix、3 件)

### F1 — off arm が 1 node も覆われていない (レビュー RA1)

次の変異が全 5 node を通過する。

```python
if driver_kind == "base" and context.arm == "on":
```

現行 node は `_test_context()` の既定 `arm="on"` しか使わず、N3 も `arm="on"` の
`launch_bootstrap` だけである。N1 の「both arms」は `reflux` の on/off を並べているだけで、
**launcher context の arm は両方とも `"on"`** である。

production では context の arm がそのまま `_driver_configs` へ流れる。off launch で射影が消えると
launcher の未射影 off ID と base driver が再導出する射影済み ID がずれ、`drive_iteration` の
exact validator に拒否される。**B-4 は on/off の対で初めて ablation になるので、
off 側が build へ届かなければ成果物 (certified 選択) が作れない。**

→ **`arm="off"` の launcher context でも base 射影が掛かることを pin せよ。**

### F2 — LOGIN / SUSPECT の fail-close が 1 node も覆われていない (レビュー RA2 = RB1)

次の変異が全 5 node を通過する。

```python
site = site if site in {"OTHER", "PEGASUS_COMPUTE"} else "OTHER"
```

現行 node の hostname は `bnode116` (COMPUTE) と通常ホスト (OTHER) だけである。
この変異が通ると、**計測用 env bytes を作れない site で linux-baremetal 契約を束縛した
config が作れてしまう** — 記録される campaign identity と実環境が食い違う。
これは正しさ防壁 (fail-close) の弱体化であり、規律 2 に触れる。

親の実測: `_admit_env_contract` は site 4 値のうち `PEGASUS_LOGIN` と `PEGASUS_SUSPECT` で
`ExecutionGuardError` を投げる。hostname `pegasus02` → LOGIN、`pegasus-mystery` および
hostname 解決不能 → SUSPECT。ただし **どちらも `_has_nqsv()` が True であることが条件**である
(`site_policy.classify_site` を読め)。

`conftest.py` の autouse fixture は `site_policy.socket` と `site_policy._has_nqsv` の
**両方**を中立化する (`_has_nqsv` は False に倒す)。同 fixture の docstring は
「test 側の宣言が後から勝つ」と明記している。**したがって LOGIN / SUSPECT を再現するには
`socket` だけでなく `_has_nqsv` も test 側で差し替える必要がある。** ここを外すと
site は OTHER に落ちて test が恒真に緑になる。恒真な緑は失格である。

→ **base の `_driver_configs` が LOGIN と SUSPECT で拒否することを pin せよ。**
   拒否は例外の型で確かめ、診断文字列だけに依存してはならない。

### F3 — sort の不変が ID しか見ていない (レビュー RA3)

次の変異が全 5 node を通過する。

```python
elif driver_kind == "sort":
    site = p3_s4_loop._current_site()
    contract = p3_s4_loop._admit_env_contract(site)
    configs = tuple(
        ident.bind_environment_contract(cfg, contract)
        for cfg in configs
    )
```

`bound_environment_contract` は campaign ID の正準 preimage に入らないので、N5 の ID 比較は通る。
しかし裁定の不変条件「**sort の挙動を 1 bit も変えない**」は破れている。

→ **N5 を強くし、sort の返り値が ID だけでなく `bound_environment_contract` も
   未射影 `default_cfg` と同じであることを pin せよ。**

## ついでに直すもの (低・1 件)

### F4 — N2 の失敗 site が特定できない (レビュー RB2)

`test_base_driver_configs_bind_resolved_contract_for_both_admitted_sites` の contract 検査は
ラベル無しの `assert all(...)` で、失敗しても hostname / expected_site が表示されない。
どちらの site で落ちたか分かるようにせよ。**検査を弱めずに**診断だけを足すこと。

## 絶対に守る不変条件

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・xfail 化を禁じる。
  既存テストが赤になったら実装側が誤りである。期待値のほうが誤りだと判断した場合は、
  実装を変えずに報告して止めよ。
- **N1〜N5 の既存の検査を弱めない。** 足すだけにする。node を消したり統合したりしない。
  親が変異 probe で観測した死に方 (上の表) が変わってはならない。
- 授権境界 `require_b4_production_context` / `validate_production_context` /
  `require_any_context` の比較を緩めない。
- `_site_admits_measurement` の exact set を広げない。
- OTHER の campaign_id を変えない。`sort` の挙動を 1 bit も変えない。
- **`orchestrator/campaign/p3_b4_launcher.py` の実装は変えなくてよい。**
  F1〜F4 はすべて test 側で閉じるはずである。実装を変えないと閉じられない所見があるなら、
  変える前に報告して止めよ。
- 恒真に緑になる test を書かない。特に F2 は `_has_nqsv` を差し替えないと恒真に緑になる。
- fixture へ現行 hash を差し込む、揮発 payload を焼き込む、といった甘くする型を使わない。
- 機構の正例・負例は実体を名指しし、依存先を stub して機構を迂回しない。

## 触ってはいけない file

`p3_s4_loop.py` / `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` / `site_policy.py` /
`ident.py` / `p3_b4_closed_critic.py` / `campaign_lock.py` / `conftest.py` / 事前登録 doc /
`orchestrator/tests/acceptance_duration_ledger.json` / docs 全般。

## 検査と報告の義務

- **緑には実走した nodeid と範囲を併記せよ。** 実走していない検査を「通した」と書いてはならない。
- **この worktree では `python3 -m pytest` は guard に拒否され、`tools/run_tests.py` は
  sandbox から rc=16 になる。** repo の自走 harness を使え (`PYTHONPATH=.` が要ることがある)。
  使った argv をそのまま報告に書け。実走できなければ `closed` と申告せず
  「実装済み・未実走」と書け。実走は親が行う。
- 所見ごとに closed / partial / regressed の対応表を出せ。表なしで root cause が閉じたと
  判定してはならない。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性を静的列挙せよ。
- 赤が残ったら nodeid と理由を必ず書け。隠してはならない。

## 出力形式

以下の H2 見出しをこの順で使え。

## 所見対応表 (F1-F4 の closed / partial / regressed)
## 変更した file:line
## 追加・強化した test node
## 実走した検査 (argv と nodeid と結果)
## 残った赤
## 波及の静的列挙
## 総括
