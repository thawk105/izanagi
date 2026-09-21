## sandbox-children-use-self-run-harness-not-pytest

login node の Codex 子 (author / fix、workspace-write) では次の 2 つが走らない。

- `tools/run_tests.py`: local admission の予約台帳を sandbox から書けず dispatch へ落ち、`qstat -Q` が
  `EACCTAUTH Unknown user-id` で rc=16 (`child_started=false`)。
- `python3 -m pytest ...`: PreToolUse guard が pytest 起動前に拒否する。

走るのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** (各 test file の `__main__` 自走 harness) だけ。
`PYTHONPATH` を付けないと `ModuleNotFoundError: orchestrator` で collection 前に落ちる。

**Why:** 2026-09-05 dynamic-backoff wave で author 3 本が「pytest 未起動 (rc=16)」を報告し、fix 子 5 本は自走 harness で
全件実走できた。子が「未実走」と正直に書いても、親が実走しない限り緑の証拠は無い。

**How to apply:** author / fix の prompt に「`tools/run_tests.py` と `python -m pytest` は使わず、
`PYTHONPATH=. python3 <test file>` の自走 harness で走らせ nodeid と結果を報告する」と書く。新設 test file には
自走 harness (`test_plain_runner_coverage.py` が要求する形) を必ず付けさせる。親は統合後に `tools/run_tests.py` で
実走して受入証拠にする。
関連: [[codex-child-discipline]]

**pytest 専用 allowlist の file は `python3 <file>` が 0 件収集の偽緑 (rc=0・出力なし) になる (2026-09-16 [T-1328] 親が実測)。**
`orchestrator/tests/README.md` の allowlist に載る file (例: `test_pegasus_calibration_workload.py`) は
`__main__` 自走 harness を持たない。素で走らせると import だけして rc=0 で終わり、tail は空。
**guard を通る正しい形:** `PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['<file>','-q','-rf']))"`。
`python -m pytest` は guard 拒否だが `pytest.main` の埋め込みは通る。**走らせる前に allowlist を見る。**
子が「79 passed」と報告した file を親が素で走らせて空出力を得たとき、子の緑を疑う前にこの罠を疑う。

## author / fix 子は login で pytest を実走できない (2026-09-21)

`tools/run_tests.py` は preflight `qstat -Q` rc=1 で rc=16、`python3 -m pytest` 直叩きは guard_bash が拒否。子の報告は必ず
「実装済み・未実走」になるので、親が焦点走を計算ノードへ dispatch して赤を実測し fix を投げる
(2026-09-21 の wave: f1 赤 10 node → fix2 → f2 緑、f3 赤 2 → fixB1 → f4 緑)。fix は同木・同 branch に積む
(fix ごとに新 branch を切ると残骸を自分で作る)。
**追記 (2026-09-03、T-1851 A2α で実測)。** 子が pytest を走らせられない結果、**子が新設した
test 自身の fixture の誤りが親の実測まで漏れる。** 同 wave で 2 度続けて親の変異 baseline を
赤にした (共有 helper へ存在しない中間 directory を渡した `FileNotFoundError`、2 つ目の repo を
手作りして protocol schema の必須 key を 10 個落とした)。実装の 606 node は緑で、漏れたのは
子が書いた test だけである。

**恒久対応: fix / author 子の prompt へ次を入れる。**「実走できないなら、最低限 test module を
import して対象 test 関数を直接呼び出し、fixture が成立するか確かめよ (`tmp_path` は
`tempfile.mkdtemp()` で代用してよい)。さらに実行時に対象の検査を除去して、期待どおり赤化するか
まで確かめよ。」実測ではこの指示で子が `DIRECT_CALL_PASS` と `DID NOT RAISE` の両方を返し、
以後の漏れが止まった。pytest 緑の代わりにはならないが、fixture の成立と変異の反実仮想は取れる。

**この恒久対応は `DW-S05-C` へ入らなかった。** `docs/dev-wave/**` の L1.5 unique footprint は
9,696 bytes ちょうどで予算満杯であり、149 bytes の追記が `check_docs` を赤にする。
台帳側は F76 の再発として記録した。**docs に無いので、fix 子の prompt を書くときはここを引く。**

`docs/dev-wave/**` は合計予算 24,000 バイトに対し 23,991 バイト使用済み (空き 9 バイト) で、
この事実を `DW-O01` へ追記できない。予算の扱いは [[docs-budget-stewardship]] に従い、
本 wave では裁定パッケージへ送った。関連: [[orchestration-loop-pattern]]、
[[codex-plan-child-dies-surveying-huge-files]]、[[codex-auth-expiry-is-fail-closed-stop]]、
[[codex-children-cannot-run-pytest]]
