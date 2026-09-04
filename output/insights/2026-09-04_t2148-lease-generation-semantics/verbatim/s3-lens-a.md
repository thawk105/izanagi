## 所見

1. **対象 (file:line):** [s2-plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:31)、[acceptance_issuer_reference.py:513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:513)、[同:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:521)、[acceptance_receipt_signature.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:357)、[verbatim-decisions.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/verbatim-decisions.md:118)  
   **何が問題か:** 同じ caller が `lease_acquired` と世代値を projection と expected の両方へ渡すため、実際の取得有無は照合されない。言えるのは「署名済み payload の marker/SHA 値が caller の取得状態・世代申告の正規化結果と一致し、署名後に改変されていない」ことだけである。D906 の却下形と同じなのは lease claim に独立な真実源がない点、異なるのは固定外部鍵と実署名検証が既に存在し、署名機構全体は単なる自己署名ではない点である。  
   **裁定にどう効くか:** D1527 の値域・契約は固定できるが、D1450 の「別取得への再利用拒否」を実効化した、または取得を検査したとは裁定できない。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** 本変更を「署名済み自己申告の表現契約」に限定し、取得対応・取得間一意性の強制は D1528 後に残ると明記する。

2. **対象 (file:line):** [s2-plan.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:46)、[同:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:50)、[verbatim-decisions.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/verbatim-decisions.md:123)  
   **何が問題か:** plan の「明示入力なら D1499 に該当しない」は強すぎる。明示 flag は暗黙の既定値をなくすが、固定 marker が caller の自己申告であることや、取得の証拠にならないことは変えない。  
   **裁定にどう効くか:** `"not-acquired"` は非保持状態の予約表現としては採れるが、新しい lease gate として扱えば D1499 の却下理由に当たる。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** 「D1499 に該当しない」ではなく「暗黙の既定値ではないが、同じ自己申告なので関門には数えない」と扱う。

3. **対象 (file:line):** [acceptance_receipt_signature.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:127)、[同:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:185)、[同:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:212)、[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:32)  
   **何が問題か:** plan どおり固定 literal の完全一致で実装する限り、canonical payload で新たに通る文字列は `"not-acquired"` の1つだけで、case variant、前後空白、接頭辞・接尾辞付き、Unicode 類似文字は通らない。programmatic 入力では `False/None` が新規受理されて marker へ変換されるが、`None` 自体は canonical 値ではない。`True/"not-acquired"`、`False/SHA値`、非 bool は拒否され、CLI では `--lease-not-acquired` のみが新規経路となり、`--lease-generation not-acquired` は拒否対象のままである。  
   **裁定にどう効くか:** 任意文字列への値域拡張という懸念は plan 自体からは成立しない。  
   **性質 (real / refuted):** refuted  
   **推奨する扱い:** marker 判定を exact equality とし、canonical 値域を `[0-9a-f]{64} ∪ {"not-acquired"}` から広げない。

4. **対象 (file:line):** [acceptance_receipt_signature.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:39)、[同:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:51)、[同:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:105)、[同:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:245)、[同:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:304)、[同:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:365)、[acceptance_issuer_reference.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:502)  
   **何が問題か:** plan の限定変更からは、固定公開鍵、秘密鍵との key-id 一致、Ed25519 検証、fail-closed key 読取り、v5/signed-v6 の exact root fields、canonical JSON 規則、署名前 payload 全体、context mismatch のいずれにも弱化は見つからない。唯一の受理拡張は意図された marker である。  
   **裁定にどう効くか:** 既存の署名・schema 防壁を理由に plan を却下する必要はない。ただし取得あり経路の canonical bytes が同一であることは実装後の pin で確認が必要である。  
   **性質 (real / refuted):** refuted  
   **推奨する扱い:** 現行の検証順序と exact field 集合を維持し、既存 acquired fixture の hash/length を変更しない。

5. **対象 (file:line):** [acceptance_receipt_signature.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:389)、[acceptance_issuer_reference.py:513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:513)、[同:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:521)、[同:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:570)、[test_external_acceptance_signing.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:123)、[同:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:142)、[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:153)、[同:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:224)、[同:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:241)  
   **何が問題か:** 必須 keyword の追加で壊れる tracked caller は上記すべてである。内訳は projection 4箇所、低水準 verifier 3箇所、高水準 verifier 1箇所、issuer API 1箇所である。静的検索上、これ以外の Python caller はない。  
   **裁定にどう効くか:** plan の「既存 helper 呼出しへの機械的変更」は概ね正しいが、署名 module 内の高水準 wrapper と issuer `main()` も漏らせない。repo 外の operational copy/importer はこの閉包に含まれない。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** 上記 caller を実装チェックリストとして全更新し、外部 caller 互換性は別所見11の裁定へ回す。

6. **対象 (file:line):** [s2-plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:31)、[同:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:35)、[verbatim-decisions.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/verbatim-decisions.md:52)、[acceptance_issuer_reference.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:4)、[dev_wave_land.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_land.py:94)、[同:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_land.py:783)  
   **何が問題か:** plan の「live lease 検査の証拠ではない」は marker の読み替えを防ぐ表現としては正しく、提案 test 名にも「lease 検査通過」という直接表現はない。しかし D1443 の縮退対象は別軸で、「署名 verifier 自体が production lander から迂回可能」であることだ。現行 issuer docstring は waiter/lander 未接続を記すが、plan が D1443 を満たす根拠として挙げる文言は自己申告性だけで、不可避でないことを明示していない。  
   **裁定にどう効くか:** marker の意味論は成立しても、D1443 を履行したという完了主張はそのままでは強すぎる。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** in-scope docstring に「production lander はこの verifier を呼ばず、この関門は不可避ではない」を明記する。新しい gate は追加しない。

7. **対象 (file:line):** [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:23)、[同:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:46)、[acceptance_issuer_reference.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:4)、[同:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:67)、[dev_wave_land.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_land.py:94)、[同:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_land.py:961)  
   **何が問題か:** 「この2 file を import するのは test だけ」は文字どおりには誤りで、issuer 自身が署名 module を import する。repo の executable source 全検索から言えるのは「waiter/lander は両 module を呼ばず、tracked production lander は v5 だけを受理する」までである。issuer docstring は repo 外の operational copy を想定しているため、「production consumer は存在しない」は repo 外まで一般化できない。また P4 は lander の受理集合なら正しいが、issuer CLI/API は plan 自身が `--lease-not-acquired` と `False/None` を新規受理する。  
   **裁定にどう効くか:** P4 を根拠に production 全体が不変とは裁定できない。保証対象を tracked waiter/lander に限定する必要がある。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** 「この repository の waiter/lander 接続面には consumer がなく、その受理集合は不変。repo 外 deployment は未測定」と書き換える。

8. **対象 (file:line):** [brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:33)、[test_external_acceptance_signing.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:43)  
   **何が問題か:** 基準 commit と現 HEAD は同一で、2 source file の SHA-256 は `1df4…70c` と `b9ea…97b`、Git blob は `d898…828` と `864a…6a7` だった。いずれも worktree 内に pin として現れない。test の `98c3…fdea` は projected canonical payload の pin であり、source bytes の pin ではない。  
   **裁定にどう効くか:** 「この基準 commit の repo 内に、2 source bytes の直接 pin は0件」という限定主張は維持できる。  
   **性質 (real / refuted):** refuted  
   **推奨する扱い:** repo・基準 commit・対象2 file を明記した限定主張として保持する。

9. **対象 (file:line):** [brief.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:7)、[同:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:35)  
   **何が問題か:** scope は3 file（うち tool は2 file）なのに、実測記述は「上記5 tool file」となっており走査対象を再現できない。現在の全 local branch に対する three-dot scanでは実際の3対象に committed overlap はなく、t733 も別面だったが、他 worktree の未commit内容は今回の「同 worktree だけを読む」制約では再検査できない。したがって「編集面重複0」は開始時点の報告であって恒久的事実ではない。  
   **裁定にどう効くか:** 現時点で plan を止める committed overlap は見つからないが、brief の実測記述だけでは全 worktree 分を監査済みと再認定できない。  
   **性質 (real / refuted):** real  
   **推奨する扱い:** 対象を正しく「3 file」と訂正し、親が author 開始直前に同じ3 fileの未commit重複だけ再実測する。

10. **対象 (file:line):** [s2-plan.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:39)、[同:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/artifacts/t2148-lease-generation-semantics/s2-plan.md:61)、[acceptance_issuer_reference.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:564)  
    **何が問題か:** plan は `main()` が CLI の二択を `(True,value)` / `(False,None)` へ変換するとする一方、テスト案は parser の raw attributes しか検査しない。`main()` が state を反転・固定・欠落させても parser test は通る。  
    **裁定にどう効くか:** module API・issuer CLI・test の3層はすべて scope に入っているが、CLI から API への実効境界だけ証拠が不足する。  
    **性質 (real / refuted):** real  
    **推奨する扱い:** 同じ test file で `main()` から `issue_signed_receipt()` へ渡る2組を直接固定する。新しい production gate は不要である。

11. **対象 (file:line):** [acceptance_issuer_reference.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:4)、[brief.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/brief.md:7)、[verbatim-decisions.md:150](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-semantics/verbatim-decisions.md:150)  
    **何が問題か:** repository copy は「外部配置用 reference」であり、実運用 copy の存在、version、caller は測られていない。3-file scope の実装は、その copy を更新しない。  
    **裁定にどう効くか:** 裁定パッケージ候補は「T-2148 は repo 内 reference contract だけを変更し、外部配置・production rollout は D1528 の鍵儀式後まで未実施と明記する（推奨）」対「現 wave で外部配置も更新するため scope と人間権限を再裁定する」の二択になる。  
    **性質 (real / refuted):** real  
    **推奨する扱い:** 前者を採り、外部 deployment を実装済み・production 有効とは報告しない。

## brief と plan が正しかった点

- 現行値域が64桁小文字16進だけであることは、[acceptance_receipt_signature.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:46)、[同:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:185)、[同:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:212)、[acceptance_issuer_reference.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:463) と一致する。

- `"not-acquired"` はハイフンを含むため SHA-256 値域と構文的に交わらず、固定 literal の完全一致なら予約語1つだけの拡張にできる。

- 非保持状態は producer に実在し、[dev_wave_wait.py:2905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_wait.py:2905) で `unclaimed=True` となり、[同:3907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/dev_wave_wait.py:3907) で保持再確認を飛ばす。[nonholding-run-receipt.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/output/insights/2026-09-02_t2148-lease-generation/nonholding-run-receipt.json:1) に lease 関連 field が `lease_holder` しかないことも一致する。

- v5 field 集合を変えず、既存 `lease_generation` slot の値域だけを disjoint union にする構成は、canonical schema と署名対象 field 集合を増やさない。

- 固定鍵、署名検証、exact root fields、canonicalization、context mismatch を維持する変更方針は現行コードと整合する。

- module API、repo 内 issuer CLI、test の3層はいずれも3-file scopeに含まれている。scope 外なのは別配置される可能性のある operational copy と production waiter/lander 配線である。

- tracked production lander が v5 exact schema のみを受理し signed-v6 verifierを呼ばない、という限定された consumer 観測は正しい。

## 総括

最も重い所見は、追加される state と expected が同じ caller 由来であり、取得有無も取得間一意性も検査しないことである。  
`"not-acquired"` の canonical 受理拡張自体は予約語1つに限定でき、既存の暗号・schema 防壁を弱める必要はない。  
親は production consumer 不在を「tracked waiter/lander 未接続」へ狭め、3-file overlap と CLI→API state mapping を実測すべきである。  
D1443 については自己申告性だけでなく、署名関門が production landing で不可避でないことを記録する必要がある。  
外部 operational copy の有無と同期状態は残る不確実性であり、D1528 後へ明示的に残すのが妥当である。  
pytest その他の実走は行っていない。