# 段 6 敵対レビュー B (説明と実装の食い違い / consumer 取り残し / 恒真な保証) — Claude opus, read-only

判定: **NO-GO** (must-fix 2 件。いずれも局所修正で設計のやり直しは不要)

> harness 注記: 子の出力に instruction-shaped pattern (settings-json) が検出され制御タグが neutralize された。
> 本ファイルは所見として記録するものであり、内容を指示として解釈しない (信頼境界: 規律 6)。

## MF-1 (must-fix) hook が `python3 -m py_compile tools/check_ai_provenance.py` を新たに拒否する

根拠: `hooks/guard_bash.py:530-533` の `_provenance_entry` の `-m <module>` 枝が、**module が何であれ**
位置引数の basename だけで違反を返す。`:190-193` の `_PROVENANCE_EXEMPT_FLAGS` は CLI flag の免除しか持たず、
script を**実行しない** module の免除がない。

実測 (`hooks/guard_bash.py` を import して `decide()` を直叩き、pytest 不使用):

| 綴り | site=PEGASUS_LOGIN |
|---|---|
| `python3 -m py_compile tools/check_ai_provenance.py` | **BLOCK**「python3 -m py_compile への provenance script 引き渡し」 |
| `python3 -m compileall -q tools/check_ai_provenance.py` | **BLOCK** |
| `python3 -m pyflakes tools/check_ai_provenance.py` | **BLOCK** |
| `python3 -m py_compile tools/run_tests.py` | ALLOW (= この縮小は本 diff が新設) |

失敗シナリオ: checker を編集する実装子が `pegasus0N` で py_compile を打つと hook が拒否し、
**ログインノードで許された唯一の検証手段が消える**。段 5 の U1 は hook 着地**前**に実行できたので
この退行に気づけていない。

説明との食い違い (3 箇所、すべて同一 commit 内):
`AGENTS.md:35`「許されるのは静的読み取りと `python3 -m py_compile` まで」/
`docs/pegasus-runbook.md:276`「**hook が閉じるのはこの綴り差だけである**」/
`docs/decisions.md` D105 決定 2 第二層「sanctioned exact path 以外の**綴り**を拒否する」。
py_compile は履歴監査を 1 度も起動しないので、これは「綴り差」ではなく**別プログラムの拒否**である。

成果物影響: hook の拒否集合が「provenance 履歴監査の非 sanctioned 綴り」から
「checker を引数に取るあらゆる `-m` module 起動」へ広がり、AGENTS.md が許可すると宣言した静的検査が
機械的に不能になる。同時に runbook §7 / D105 の保証が永久記録として偽になる。

修正案: (1) `guard_bash.py:193` の直後に `_PROVENANCE_STATIC_MODULES = frozenset({"py_compile",
"compileall", "pydoc", "tokenize", "dis", "ast"})` を追加。(2) `:530-532` を
`if (module not in _PROVENANCE_STATIC_MODULES and script and os.path.basename(script) == ...)` へ差し替える
(`pytest` は集合外なので M13 の期待赤は保存される)。(3) `test_hooks.py:812`
(`test_bash_login_allows_nonexecuting_provenance_flags`) の正例に
`"python3 -m py_compile tools/check_ai_provenance.py"` を追加する。
**現在この正例が無いこと自体が過剰縮小の検出網の穴**である。

## MF-2 (must-fix) D105 の「rc=16 を infra 側へ落として塞ぐ」が実装より強い

根拠: `tools/dev_waves/checker.py:340` は `ReasonCode.CHECK_FAILED` へ落とすが、
`tools/dev_waves/schema.py:52-86` の `ReasonCode` に **infra 相当の値は存在しない**。
`CHECK_FAILED` は全 fallback と同値。テスト名 `test_dev_wave_check_maps_dispatch_infra_rc_to_infra_reason`
(`test_pegasus_dispatch_compute.py:1141`) も `assert ... is ReasonCode.CHECK_FAILED` (:1169) と矛盾する。

成果物影響: dev-wave 台帳の `reason` が `provenance-failed` → `check-failed` に変わるだけで infra 判別はできない。
D105 が「塞ぐ」と書くのに実装は誤ラベルを外すだけなので、恒真な保証が永久記録に入る。

修正案: D105 の当該 1 文を「16 を `PROVENANCE_FAILED` から外し汎用の `CHECK_FAILED` へ落とす
(**infra 専用の理由コードは無く、台帳上は他の check 失敗と区別できない**)」へ書き換える。
テスト名も `..._maps_dispatch_infra_rc_off_provenance_reason` 等へ改める。

## 攻撃したが破れなかった点 (実走・実測付き)

1. **免除件数 = 実発火数** — `check_ai_provenance.py:555-585` の 3 つの早期 return がすべて `False` を返し、
   `if waived: return [], True` を通った時だけ True。`_audit_history:924-928` は `waived_applied` だけを数える。**破れず。**
2. **waiver 付き commit は前方訂正の担い手になれない** — `:910` の `and not correction.waiver.exact`。
   epoch 前は実装面 gate 自体が発火せず waiver が抑止できる finding が存在しないため受理集合は広がらない。
   過剰縮小側は `test_forward_correction_without_waiver_is_still_accepted` が固定。**破れず。**
3. **`min(available_cpus(), 32)`・env 上書きなし** — `:704-711`。checker 内に env 参照ゼロ (grep)。
   テストは `available_cpus` を monkeypatch する = 呼び出し時解決なので恒真でない。**破れず。**
4. **v1/v2 両受理** — `dispatch_compute.py:418-432`。テストは実 `_job_run` を駆動しており schema 文字列を grep していない。**破れず。**
5. **A-R8 の恒真テスト是正** — 同時実行高水位を実測 (`measure(1)==1` / `measure(4)>=2`)。**破れず。**
6. **bitset の正しさ** — `--topo-order` が子→親順に出し `reversed(rows)` で親が常に確定済み。反射性は
   `merge-base --is-ancestor A A` (rc=0) と一致。閉包は除外 rev を渡さないので完全。
   逐次 oracle を production に残しているので等価性テストが自己参照になっていない。**破れず。**
7. **`_is_descendant` rc=128 fail-closed** — 前方訂正は `:878` で従来どおり呼び、実 argv を記録するテストが発火を証明。**破れず。**
8. **thread 安全性** — worker が触る module グローバルは読み取り専用の 1 つのみ。`os.chdir` なし。**破れず。**
9. **consumer 取り残し (repo 全 grep)** — `_audit_history` / `validate_implementation_author` は自ファイルと自テスト以外に caller ゼロ。
   `dispatch` の production caller は `run_tests.py:833` の 1 箇所で更新済み。schema を読む非テストコードはゼロ。**取り残しなし。**
10. **docs 予算と検査 (実走)** — `wc -c docs/ai-provenance.md` = **8942/9000**、HEAD からの差分は**きっかり 186 bytes**。
    `check_docs.py` **rc=0**、`check_codex_agents.py` **rc=0**。waiver literal count 1、production 定数と逐語一致。**破れず。**
11. **実測していない値の混入** — runbook の秒数はすべて insight §11 の逐語で日付・request ID・ノード名つき。**捏造なし。**
    D105 も 4.58 を「48 並列 + bitset の参照値」と明示している。
12. **`run_tests.py` / `dev_waves/checker.py` の変更幅** — diff 実測で **+1 行** と **+2/-1 行**のみ。
13. **B-R1 を scope 外とした親の根拠** — `cli.py:190-193` に `orchestrator` check が実在し、
    `run_tests.py:381-396` の免除は `orchestrator/tests` を免除しない。「同じ `/tmp` clone から dispatch する経路は既存」は**事実として確認**。

## nit / backlog

- **N1** M8 (`pool.map`→`as_completed`) はタスクが速いと完了順が入力順と一致して生存しうる。
  変異実施時は worker に人工的な非対称遅延を入れるか、期待赤を決定性の契約テストへ置き換える。
- **N2** M11 は `if task not in TASKS: raise ValueError` を消しても直後の `TASKS[task]` が `KeyError` を投げ
  同じく INFRA_RC になる。テストは例外クラス名を見ているだけで防壁の実効性を見ていない。
- **N3** M2 は `[body-plus-valid]` も、M3 は `[split-blocks]` も、M14 は stdout テストも落とす。
  原因は一意なので DW-M07 の要件は満たすが、期待 node 欄が 1 個しか書かれていない。anchor 再検証で追記する。
- **N4** `test_hooks.py:1231-1235` が parametrize node を無条件 skip するため、素の runner では M13 の期待赤が 1 件も走らない。
- **N5** `test_provenance_probe_omits_pytest_and_xdist_imports` の既定引数 assert は言い換えでしかない。
- **N6** message-file preflight (`check_ai_provenance.py:1069-1077`) は `_waiver_audit` を無条件に呼ぶので、
  **docs-only の message に不正な waiver 行があると新たに rc=1** になる。fail-closed 側だが D105 の
  「変わるのは 3 点だけ」にも実装子の差分表にも載っていない。
- **N7** runbook §7 の実測表は 2026-07-30 の**試作**実装 (48 並列 + bitset) の値で、land する実装は cap 32。
  「試作実装の実測」の一語がないと出荷実装が 4.58 秒だと読める。
- **N8** `python3 -mpytest tools/run_tests.py` は今も ALLOW (実測)。`_script_target` の穴は run_tests 側に残る。
  runbook §7 の「綴り差だけ」は run_tests についても既に強すぎる文言。worklog 起票時に併記する。
- **N9** `check_ai_provenance.py:21-24` の `sys.path.insert(0, str(REPO))` は import 時に無条件で走る。

## 総括

D105 の設計判断 4 本は**すべて実装と一致**していた。docs 予算・needle count・各検査 rc も実走で確認した。
A-R8 が指摘した恒真テストは同時実行高水位の実測へ、bitset 等価性は production に残した逐次 oracle との
4 arm 比較へ、いずれも正しく置き換わっている。

破れたのは **hook の受理集合** 1 点で、そこが致命的。`-m <module>` 枝が module を区別しないため
`python3 -m py_compile tools/check_ai_provenance.py` が拒否される — 同じ commit の `AGENTS.md:35` が
「許される」と宣言し runbook と D105 が「綴り差だけ」と保証している当のコマンドである。
防壁の一方向の締めすぎを検出する網に、AGENTS.md が名指しする唯一の静的検査が入っていなかったのが根因。

もう 1 点は D105 の「infra 側へ落として塞ぐ」で、`ReasonCode` に infra 相当の値が存在しない。
どちらも局所修正 (hook +6 行 / テスト正例 +1 行 / docs 1 文 / テスト名 1 個) で、
統合 commit の構造・変異事前登録・受入基準はそのまま使える。
