# [T-2871] 段 6 裁定 4 (親) — 焦点走 5 回目 (33689.nqsv、13d0e0913) の赤 3 件

焦点走: 3 failed (focus5.log)。login の run_tests.py 経由 (dispatch 強制なし) でも同じ 3 件を 23.91 s で再現した (local-probe1.log)。stock も build・verify まで到達するようになった。

| # | 赤 | 原因 (失敗本文とコードから) | 裁定 | 処置 |
|---|---|---|---|---|
| R13 | T1 (`..._two_processes_...`)・T3 (`..._reused_identity_...`) | stock の評価が verify の後 `評価中に例外 → abort: list index out of range`。代役 `checkout` が `fixtures._mock_pipeline(...)` を checkout ごとに 1 回だけ開くため、bench / trace の模擬台本 (round index を持つ) が 1 評価分しかなく、同じ checkout の 2 評価目 (stock) で尽きる。backoff 手本の「arm ごとに新しい bench script」の前提 | real・自分起因 (代役) | fix-4: 模擬 pipeline を**評価 (run_campaign 呼出し) ごとに**新しく開く。例: `P.run_campaign` を包む spy が呼出しごとに `_mock_pipeline` の context に入る。build・evidence の代役もその中で有効にする |
| R14 | T2 (`..._crash_consumes_...`) | 2 本目の子で `AuditorGateFailure: 帰属汚染: auditor.diff_digest と実際の working_diff の digest が不一致`。production の `patchharness.checkout` は process ごとに新しい隔離 worktree を作り、`applied` は抜けるときに patch と候補の書込みを元に戻す。代役は checkout で同じ root を返し、`applied` を `nullcontext` にしているため、強制終了した 1 本目の候補の書込みが source に残り、2 本目の候補の working diff が auditor の審査対象と食い違った。実 auditor gate は正しく拒否している | real・自分起因 (代役) | fix-4: (a) 代役 `checkout` は親が 1 回だけ用意した pristine source を、呼出しごと (= process ごと) に新しい dir へ複製して返す。(b) 代役 `applied` は enter 時に対象 source file (`P.axis.SOURCE_REL`) の bytes を保存し、exit 時に戻す (production の patch revert の模擬)。これで stock は stock の source を、次の process は pristine を見る |

受理・拒否の含意: R13・R14 は test の代役だけを production の流れに近づけ、driver・auditor gate・admission の受理集合を変えない。通る正例 = 各 process が新しい checkout で候補 (auditor digest 一致) → stock を評価し、2 本とも stock `certified-stock` になる T1。拒否されるべき例 (変えない) = auditor が審査した diff と異なる working diff は実 auditor gate が `AuditorGateFailure` で拒否する (今回の T2 の赤そのもの)。

反復: 子は pytest を走らせられないので、親が login の `tools/run_tests.py ... -k pegasus` (受入形でない確認) で緑を確かめてから計算ノードの焦点走を取り直す。
