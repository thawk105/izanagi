静的 focused re-review の結論は、**mutation本走への GO** です。残る実装 blocker はありません。テスト実走は0件で、author報告の pass 件数は検証済みgreenとして扱っていません。

## 所見別判定

| # | 所見 | 判定 | 根拠 |
|---:|---|---|---|
| 1 | path-absent bind failureが`getsockname()` EPERMへ進み、既存SKIPをFAILへ縮小 | **closed** | bind失敗後にnofollow statを行い、不在なら直ちに`False`。[integration.py:1128](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1128)。fixtureも`getsockname()` EPERM＋`assert_not_called()`を固定 [同:1240](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1240)。 |
| 2 | exception種別×pathname状態×pending verdictのmatrix不足 | **closed** | FNF-absent×pending True/False、FNF-present、EPERM/EIO-absent、success-presentを区別 [同:1261](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1261)。pending verdictが意味を持つFNF-absentだけ両値を持ち、再送出ケースではverdictが観測結果を変えないため、必要な判別集合は閉じている。 |
| 3 | M‑T146‑Bが等価変異 | **closed** | broad `except OSError`ではEPERM/EIO-absentが抑止される一方、testは元例外の同一性を要求する [同:1312](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1312)、[同:1361](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1361)。静的には2 nodeで非等価。 |
| 4 | `-rf -rs`がFAILED node記録を失う | **partial** | 正しい形式は`-rfs`で、DW-M08の`FAILED`抽出条件を満たす [mutation.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/docs/dev-wave/mutation.md:49)。ただし旧planには誤形式が残り [plan-v2:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s4-adjudication-plan-v2.md:18)、mutation本走と台帳は未実施。これは本走で閉じる運用条件で、実装blockerではない。 |
| 5 | recovery前のdirect observationとpreexisting identity no-touch | **closed** | patch終了後・finalizer前にpathnameをnofollow観測 [integration.py:1345](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1345)、recoveryは外側finally [同:1380](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1380)。preexistingはbefore/after identity、mode、symlink target、socket非生成を直接固定 [同:1405](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1405)。 |
| 6 | M‑T146‑A/Cの単一帰属 | **closed** | Aはpartial-bindだけ、Cはsuccess-presentだけが静的に赤になる。既存T-138正負gateは各anchorを対象断面で通らない。anchor候補は下記のとおり各1箇所。 |
| 7 | close複合fault・hostile writer・production partial-bind | **scope外維持** | helperのclose複合例外とTOCTOUは残るが、single-writer test helperの現acceptanceに追加影響なし。production helperも不変更 [protocol.py:246](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/protocol.py:246)。 |
| 8 | 旧穴3 / regression guard / identity再固定＋新policyの記録分類 | **partial** | 静的分類は確定したが、段7の最終台帳は未作成。旧穴は3種類・4 node、regression guardは3 node、identity＋新policyは2 nodeとして記録すべきで、全9 nodeを「9件の旧欠陥」と数えてはいけない。 |

## file:line確認

- OSErrorの過剰な`False`化はありません。`False`になるのはsocket生成、pathを作らないbind失敗、chmod/stat/listenのcapability syscall [integration.py:1124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1124)。preexisting観測、path-present後の`getsockname()`、cleanupの非FNF、postcondition違反は送出されます [同:1110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1110)、[同:1131](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1131)、[同:1149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1149)。

- FNF-presentは`observed_error is unlink_error`により元FNFそのものを要求します。EPERM/EIO-absentも同じidentity assertで元非FNFを要求し、同型・同errnoの作り直しでは通りません [同:1361](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1361)。

- pending Falseはlisten faultでcleanup前のreturn値を`False`にし [同:1331](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1331)、FNF cleanup後に`result is pending_verdict`を直接確認します [同:1357](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1357)。cleanup verdict退行時、`closed`・例外assertは先に赤くなりません。

- exact anchor候補は次の各1箇所です。

  - M‑A: `owned = probe.getsockname() == alias` [同:1135](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1135) → partial-bindだけ。
  - M‑B: unlink直後の`except FileNotFoundError`＋次のnofollow statを含む文脈 [同:1150](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1150) → eperm-absent/eio-absentだけ。単独の`except FileNotFoundError`は複数あるためanchorに使えません。
  - M‑C: unlink成功後のabsence block全体 [同:1159](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1159) → success-presentだけ。

- 差分は`+269/-16`の1ファイルのみです。追加部分に新しい実害blockerは認めません。isolation meta-testは`socket.socket`到達を推移的に導出し、marker集合を完全一致で固定しています [isolation-contract.py:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:70)、[同:102](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:102)。

## real

残るreal実装blockerはありません。

運用上残る2点は、mutation本走を`-rfs`で実施してFAILED/SKIPPED node・reasonを別々に保存することと、段7で次の分類を記録することです。

- 旧穴3種類: partial-bind、FNF-after-real-unlink、no-op unlink。FNFのpending True/Falseは2 nodeだが1欠陥。
- regression guard: FNF-present、EPERM-absent、EIO-absent。
- identity再固定＋新policy: regular-file、broken-symlink。
- 追加の段6 regression guard: path-absent bind時の`getsockname()`非呼出し。

旧flagを放置した場合の影響はproduct artifactではなく、mutation台帳からFAILED nodeが消え、KILLEDの単一帰属を裁定できなくなることです。

## refuted

- 「current helperが全OSErrorをcapability Falseへ潰す」はrefuted。
- 「M‑Bはfix後も等価」はrefuted。
- 「M‑A/Cが既存gateに先にkillされる」はrefuted。
- 「269追加行そのものが新しいmust-fixを生んだ」はrefuted。非FNF-present追加などは冗長guard候補にはなりますが、現事前登録変異や具体的なtest acceptance変化を伴うblockerではありません。

## scope外

- socket close / dirfd closeとprimary cleanup例外の複合fault。
- close→unlink順序の独立oracle。
- hostile concurrent writerによるstat/unlink間の置換。
- production `bind_repo_socket()`の同型partial-bind一般化。

いずれも今回のsingle-writer test helperの受理集合またはproduct artifactへ追加影響を書けないため、scope外維持が妥当です。

## 総括

**GO。mutation本走へ進めます。**

sourceへの追加fixは不要です。M‑A/B/Cを上記の一意anchorで適用し、`pytest -q -rfs`でrc・FAILED node・SKIPPED node/reasonを保存してください。

これは静的GOであり、テストgreen・mutation KILLED・wave完了の承認ではありません。テストは実走しておらず、author報告の件数も検証済みgreenとして記録していません。