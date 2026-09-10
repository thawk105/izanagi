## 壊せなかった点

- 現行の正式発行経路では attempt-registry 検査は迂回されない。`assert_trial_registry_acceptance` は必ず formal checker を呼び、v3 genesis だけを許し、v5 receipt を発行する。[trial_registry.py:6282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6282) [trial_registry.py:6293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6293) [trial_registry.py:6440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6440)

- v5 の `_assert_attempt_registry_consumption` は恒真ではない。具体的に以下は赤になる。

  - receipt の P/C と lifecycle row の P/C が違う → binding mismatch。[s8c_acceptance_receipt.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:550) [s8c_acceptance_receipt.py:1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1620)
  - P に canonical registry blob がない、または receipt prefix がそれを継承しない → 赤。[s8c_acceptance_receipt.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1638)
  - P 時点の blob が genesis 一行だけでない → 赤。[s8c_acceptance_receipt.py:1655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1655)
  - committed history が strict prefix でない、または別 path に認識可能な genesis がある → 赤。[s8c_acceptance_receipt.py:1899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1899) [s8c_acceptance_receipt.py:1907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1907)
  - initial unit に final terminal がない、複数ある、report hash が違う → 赤。[s8c_acceptance_receipt.py:1702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1702)

- 正式発行時の lifecycle 検査も強い。各 manifest trial に start/terminal が各一行必要で、accepted report・attempt row と照合される。[trial_registry.py:5402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5402) [trial_registry.py:5449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5449) [trial_registry.py:5469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5469)

したがって、「正規の issuer を通った v5 receipt の内部整合性」は壊せなかった。

## 見落とされている経路

1. **P1 は「genesis を含む commit」と「genesis を導入した commit」をすり替えている。**

   次の履歴は正式 issuer を含めて通る。

   1. commit G で manifest と genesis 一行を導入する。
   2. registry を変えず、無関係な変更だけを行った commit K を作る。
   3. K を `prereg_content_commit=P` とし、その直子 C に effective binding を置く。

   history gate は blob が前 commit と同一なら許可するため、G と K の間で registry が不変でも通る。[s8c_acceptance_receipt.py:1899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1899) P の検査は「P に genesis-only blob がある」だけで、P が導入 commit G かは検査しない。[s8c_acceptance_receipt.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1638) 正式 issuer 側も、P の blob と C の exact-parent 関係は調べるが、P が registry introduction commit かは調べない。[trial_registry.py:1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1462) [trial_registry.py:1510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1510)

   receipt に残るのは K であり、実際の導入 commit G ではない。従って P1 を「起点を作った commit が記録される」と読むなら、明確に壊れる。

2. **作成時刻・作成者・実行 code 版は記録されない。**

   genesis の exact schema に時刻、actor、argv、producer、code commit はない。[trial_registry.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:142) core が生成する値にもそれらはなく、schema の exact-key 検査により任意追加もできない。[attempt_registry_core.py:659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/attempt_registry_core.py:659) [attempt_registry_core.py:1506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/attempt_registry_core.py:1506)

   facade の入力にも commit や actor はなく、生成後に bytes を create-only で置くだけである。[trial_registry.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2471) [trial_registry.py:2526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2526)

   Git の author/committer は「commit した主体」であり「genesis を生成した実行主体」ではない。P の tree に code があっても、その code を実行した証明はない。別 checkout、installed module、手組み JSON が同じ canonical bytes を作れば区別不能である。

3. **standalone receipt verifier は正式 issuer の P/C 検査を再現しない。**

   `prereg_effective_commit` は parser では40桁の構文しか検査されない。[s8c_acceptance_receipt.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:388) `_assert_attempt_registry_consumption` は C を attempt rows と一致させるが、C が実在する commit か、P の直子か、measurement HEAD の祖先かを検査しない。`_blob_at_commit` が参照するのも P だけである。[s8c_acceptance_receipt.py:1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1620) [s8c_acceptance_receipt.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1638)

   したがって、C を例えば `"000…000"` とし、attempt rows も同じ C にして chain/digest を整えた初回履歴は、この verifier の条件上は C object 不在を理由に赤にならない。正式 issuer の exact-parent gate は [trial_registry.py:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1254) にあるが、standalone verifier からは呼ばれない。

4. **standalone verifier は lifecycle を再導出していない。**

   verifier が lifecycle に行うのは history prefix と prefix digest の検査だけである。[s8c_acceptance_receipt.py:1991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1991) `_assert_git_history_append_only` は lifecycle JSON を parse せず、Git history が空でも拒否しない。[s8c_acceptance_receipt.py:1736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1736)

   よって、他の証拠が妥当な手製 v5 receipt で、`lifecycle_path` を任意の非空 regular file に替え、長さと hash を合わせても、この verifier は start/terminal 不在を理由に赤にできない。`require_current_verified_receipt` も v5 を確認して同じ verifier を再実行するだけなので、この穴は閉じない。[s8c_acceptance_receipt.py:2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:2088)

   これは正式 issuer が行う lifecycle 再導出とは異なる信頼面である。

5. **入力照合も standalone verifier では部分的である。**

   genesis の `manifest_sha256` は receipt と比較されるが、genesis の `manifest_path` と receipt の `manifest_path` は比較されない。[s8c_acceptance_receipt.py:1632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1632) 同じ bytes を別 path に置き、receipt だけをその path に向けても path 差では赤にならない。正式 issuer 側では genesis path を照合している。[trial_registry.py:2680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2680)

6. **schema 分岐による迂回は存在するが、新規正式発行には直結しない。**

   parser は v1〜v5 を受け、v1〜v4 では attempt fields を `None` にし、attempt consumption は v5 のときだけ呼ぶ。[s8c_acceptance_receipt.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:765) [s8c_acceptance_receipt.py:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:819) [s8c_acceptance_receipt.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:2075)

   ただし新規正式 issuer は v5 固定で、current capability gate は旧 schema を拒否するため、これは generic verification surface の迂回であって新規 `accept` CLI の迂回ではない。[s8c_acceptance_receipt.py:2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:2097)

7. **abandoned start は provenance bypass ではないが、lifecycle が必ず閉じるという主張は壊す。**

   S8C profile は recovery を無効化し、現行 event schema に recovery を持たない。[trial_registry.py:2137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2137) [trial_registry.py:2195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2195) また `record_trial_terminal` は token を `consumed=True` にした後で registry/artifact の読出しと ledger append を行う。[trial_registry.py:4993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:4993) 後段で失敗すれば start-only ledger と消費済み token が残り、start-once gate が再開を拒否する。[trial_registry.py:4810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:4810)

   これは acceptance を通らないので provenance の迂回ではなく fail-closed な行き止まりだが、「production driver が lifecycle を必ず記録する」は恒真ではない。

8. **射影内に別 production caller は見つからない。**

   `create_attempt_registry_genesis` は facade 定義、facade から core への一回の呼出し、core 定義だけである。[trial_registry.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2471) [trial_registry.py:2517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2517) [attempt_registry_core.py:1431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/attempt_registry_core.py:1431) CLI も `register` / `accept` の二つだけである。[trial_registry.py:6502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6502)

   ただし射影外を読むことは禁止されているため、repo 全体の caller 不在はここでは証明できない。

## 総括

P1 は壊れた。現行保証が記録するのは「genesis-only bytes を含む任意の P」であり、genesis 導入 commit、生成時刻、実行者、実行 code 版ではない。G→無関係変更 K→C という、正式 issuer 自体を通る具体的反例がある。

P2 は正式 issuer 内では概ね成立するが、standalone verifier では manifest path まで束縛されない。P3 も正式 issuer 内では成立する一方、receipt verifier は lifecycle semantics を再導出しておらず、abandoned start は閉じない。P4 の argv 未記録はそのまま成立する。

従って P5 の根拠「起点の commit・入力・lifecycle は既存経路で記録・強制済み」は成立しない。ただし予定されている `genesis` CLI も、schema を変えない限り actor・時刻・code 版・argv・真の introduction commit を記録しない。CLI 追加は入口の標準化にはなるが、今回壊れた provenance 主張の修復にはならない。静的確認のみで、テスト実行はしていない。