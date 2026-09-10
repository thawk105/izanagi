結論は、P1 を採用し、現行 `land()` の `:1735` 直前へ関門を置く案です。以下は base `bcda1c02` の現行行番号です。実装・commit・pytest・checker 実走は行っていません。

## 1. W1 の実装位置と形

### 新しい rc

[tools/dev_wave_land.py:40-51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:40) の末尾へ、既存値と衝突しない次を追加する。

```python
RC_PROVENANCE = 29
```

`RC_AUDIT = 23` は申告された commit 閉包や ancestry の不整合用なので再利用しない。新関門は「子 checker 自体の全史監査が非 0」という別原因であり、`29` は現行 `0, 10, 11, 20..28` の次の空き値である。

### 新関数

[tools/dev_wave_land.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1363) の `_validate_generated_docs()` 定義直前へ、`_verify_provenance_history(repository: _Repository) -> None` を追加する。既存 `_validate_generated_docs` と `_preflight_fold_message` は変更しない。

関数の契約は次のとおり。

- checker は `repository.wave / "tools/check_ai_provenance.py"`。symlink・不存在・非 regular は `RC_PROVENANCE` で拒否する。
- argv は厳密に `[sys.executable, str(checker)]`。`--range` も `--message-file` も渡さず、既定の全史監査を使う。
- `cwd=repository.wave`、`env=_git_env()` に `PYTHONDONTWRITEBYTECODE=1` を加える。
- `stdin=DEVNULL`、`stdout=PIPE`、`stderr=PIPE`、`check=False`、`shell=False`、`close_fds=True`。
- `subprocess.run` の起動不能は `_Reject(RC_PROVENANCE, ...)` へ畳む。ここで `RuntimeError` を漏らすと、[tools/dev_wave_land.py:1955-1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1955) の rc 契約に乗らない。
- `completed.returncode != 0` を唯一の赤判定にする。rc 1・2・16・signal 等を land 側で再解釈しない。reason には子 rc と `_detail(stderr) or _detail(stdout)` を含める。

### `land()` への挿入位置

[tools/dev_wave_land.py:1735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1735) の `if active_plan is not None:` の直前へ、呼び出しを一つ置く。

```python
_verify_provenance_history(repository)
if active_plan is not None:
```

前後関係は次になる。

| 順序 | 現行 file:line | 処理 |
|---|---:|---|
| 1 | `tools/dev_wave_land.py:1673` | cooperative lock 取得 |
| 2 | `tools/dev_wave_land.py:1703-1708` | `_verify_main_clean`、`_verify_wave_clean` |
| 3 | `tools/dev_wave_land.py:1709-1714` | `_verify_audit` で A..T 閉包を固定 |
| 4 | `tools/dev_wave_land.py:1722-1734` | `_verify_heads` と stale-main 拒否 |
| 5 | 現行 `tools/dev_wave_land.py:1735` 直前 | 新しい全史 provenance 関門 |
| 6 | `tools/dev_wave_land.py:1783`, `:1879` | active/already-landed 側の `_fold_main_locked` |
| 7 | `tools/dev_wave_land.py:1921-1925` | `merge --ff-only` |
| 8 | `tools/dev_wave_land.py:1939` | ff 成功後の `_fold_main_locked` |

これにより、関門は lock 内だが、全ての既存 cheap reject 後であり、全ての main mutation・fold apply より前になる。赤なら main はまだ変更されない。38.3 秒の lock 保持は [parent-brief-v2.md:29-30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/parent-brief-v2.md:29) の P6 どおり受容する。

## 2. 監査対象と実行体

P1「対象 = wave tip の全史、実行体 = tip 側 checker」を採用する。

[tools/check_ai_provenance.py:29-31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:29) は repo root を ambient cwd ではなく `Path(__file__).resolve().parent.parent` から決め、[tools/check_ai_provenance.py:356-368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:356) の全 Git 呼び出しもその `REPO` を cwd にする。したがって、`cwd=repository.wave` だけでは足りず、checker path 自体も tip 側でなければならない。

引数なしなら [tools/check_ai_provenance.py:838-857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:838) により policy 導入 commit から tip の `HEAD` までが対象になる。

二つの失敗モードの評価は以下のとおり。

- main 側実行体を採ると、pre-FF では `__file__` 由来の main `HEAD` を監査してしまい、そもそも wave tip を見ない。別手段で旧 main checker を tip に向けても、known-violation 登録が tip にしかない wave は旧 checker で永久に赤となり、[parent-brief-v2.md:47-51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-provenance-known-violation/parent-brief-v2.md:47) の deadlock になる。
- tip 側実行体なら wave が checker 自体を弱められる。この risk は実在する。ただし land helper 自身も「悪意ある writer に対する sandbox ではない」と [tools/dev_wave_land.py:2-7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:2) で明記された cooperative trust 境界にある。checker 無変更という例外を作ると、まさに known-violation 登録 wave を塞ぐため、本 scope 内では P1 が一貫する。

`_preflight_fold_message()` が main 側を使うのは別理由である。[tools/dev_wave_land.py:1440-1478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1440) で fold を main に apply・stage した後、その main index と prospective fold message を検査するからである。checker の message-file 経路も [tools/check_ai_provenance.py:830-835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_ai_provenance.py:830) で実行 repo の staged paths を読む。wave 側で走らせれば別 index を見る。この main 選択は旧 main checker を trust root にする設計ではない。

## 3. 既存 64 テストへの波及

### 既存テストの stub 境界

[orchestrator/tests/test_dev_wave_land.py:119-123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:119) の合成 repo fixture に、即時 `SystemExit(0)` する tracked `tools/check_ai_provenance.py` を追加し、同じ base commit へ含める。

これなら既存テストは38秒の実 checkerを走らせずに済む一方、新しい production 関門・path 解決・`subprocess.run`・returncode 判定自体は通る。`_verify_provenance_history` を一律 monkeypatch してはならない。そうすると関門呼び出しを削除した変異まで既存テストが通る。

fixture executable にする理由は、通常の `_land()` 経路だけでなく、別 process の [orchestrator/tests/test_dev_wave_land.py:2482-2515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:2482) と CLI E2E の [orchestrator/tests/test_dev_wave_land.py:2667-2695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:2667) にも stub が届くためである。

既存 `_preflight_fold_message` stub は `:1547`, `:1671`, `:1798`, `:1853`, `:1888`, `:2067`, `:2652` のまま残す。これは fold message だけの隔離であり、新しい全史関門の stub を同じ `with` へ足さない。既存期待値は一つも変更しない。

### 新規テスト

[orchestrator/tests/test_dev_wave_land.py:1228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:1228) と `_WRAPPER` 定義の間へ、少なくとも次の4本を置く。末尾の `_run()` は [orchestrator/tests/test_dev_wave_land.py:2866-2875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:2866) で `test_*` を自動収集するため一覧更新は不要。

1. `test_provenance_gate_rejects_tip_nonzero_before_ff`

   main の fixture checker は rc 0、wave tip の checker を rc 73 にして commit する。`RC_PROVENANCE/rejected`、reason 内の `rc=73`、main HEAD が base のまま、を assert する。関門削除・main 側 checker 選択・非0無視・ff 後配置のいずれでも赤くなる。

2. `test_provenance_gate_accepts_tip_zero_under_lock`

   main base の checker を rc 71、tip で rc 0 に直す。tip checker は `cwd`、`sys.argv[1:] == []`、lock の nonblocking 取得が `BlockingIOError` になることを repo 外 marker に記録する。`RC_OK/landed` と marker を assert する。main executor へ戻す変異、`--range` 追加、lock 外移動で赤くなる。

3. `test_provenance_gate_has_no_bypass_or_already_landed_shortcut`

   repo 外 control file に従って rc 0/73 を返す同一の tracked tip checkerを使い、まず緑で land、次に control を73へ変えて同じ requestを再実行する。2回目が `already-landed` でなく `RC_PROVENANCE/rejected` になることを固定する。併せて [tools/dev_wave_land.py:77-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:77) の `LandRequest` field 集合と [tools/dev_wave_land.py:1969-1983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1969) の parser option 集合を exact に assertし、skip field/flag追加を赤にする。checker削除・symlinkも `RC_PROVENANCE` になるケースを同テストで列挙する。

4. `test_provenance_subprocess_contract_uses_direct_returncode`

   新関数自体は stub せず、`LAND.subprocess` だけを記録 facade に差し替える。fake `run` 内で以下を assertする。

   - argv の型が list で、値が `[sys.executable, tip_checker]` と完全一致
   - `cwd == repository.wave`
   - `shell is False`
   - `check is False`
   - `stdin=DEVNULL`, `stdout=PIPE`, `stderr=PIPE`, `close_fds=True`

   rc 73・green-looking output では `_Reject(RC_PROVENANCE)`、rc 0・red-looking output では通過させる。custom `returncode` property のアクセス回数も assertすれば、stdout grepや例外経由ではなく returncode を直接読んだことを固定できる。文字列 command、`bash -c`、`| tail`、`shell=True`、出力内容判定のいずれへ崩しても赤になる。

## 4. W2 の DW-S01 追記

[docs/dev-wave/core.md:31-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/docs/dev-wave/core.md:31) には既に、検査・テスト追加 wave 向けの「性質で既存被覆を検索」がある。これを重複させず、前提実測用 probe 一般へ射程を足す。

[docs/dev-wave/core.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/docs/dev-wave/core.md:35) の最初の文「brief 前に承認済み裁定の前提を実測する。」の直後、同じ段落内へ次の一文を入れる。

> そのための probe を書く前に同じ性質を固定する既存テスト・検査を検索し、既存被覆で足りるなら新設しない。

UTF-8で151 bytes。段落を同じ改行数で reflow すれば、`8655 + 151 = 8806 bytes`、[tools/check_docs.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/check_docs.py:177) の9600-byte予算に対して794 bytes残る。予算値は変更しない。

## 総括

- 採用設計: tip 側 checker による tip `HEAD` の既定全史監査を、現行 `tools/dev_wave_land.py:1735` 直前で無条件実行し、非0を `RC_PROVENANCE = 29` で拒否する。理由は、checker無変更のまま正しいtipを監査しつつknown-violation登録waveのdeadlockを避けられる唯一の案だから。
- 最大の risk: tip が `check_ai_provenance.py` 自体を弱められること。これは本関門だけでは除去できず、cooperative trust境界の残余riskになる。
- 親が段4で裁定すべき択一: **(A) P1を採用してこの残余riskを受容する（推奨）** / **(B) 本waveを止め、tipから独立したimmutable trust rootを別scope・別裁定で設計する**。旧main checker単独案はdeadlockと誤ったrepo-root監査のため選ばない。