## 所見

1. **real / `trusted`・`trust root` が設定済み公開鍵以上の保証を示す。**  
   該当: [acceptance_receipt_signature.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:39)、同 `TrustedPublicKey`、`load_trusted_public_key`、`verify_trusted_signed_receipt`、[acceptance_issuer_reference.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_issuer_reference.py:492)。下位 API はテスト生成鍵でも `TrustedPublicKey` を構築でき、固定 path にあること以外の独立な trust provenance は検証しない。  
   成果物への影響: signed receipt・レポート・台帳を「trusted/authentic」と誤読させ、設定鍵による署名確認を意味的真正性へ昇格させる。production 受理集合は現時点では不変。  
   逐語の修正案: `TRUSTED_PUBLIC_KEY_PATH` → `CONFIGURED_PUBLIC_KEY_PATH`、`TrustedPublicKey` → `ConfiguredPublicKey`、`load_trusted_public_key` → `load_configured_public_key`、`verify_trusted_signed_receipt` → `verify_configured_key_signed_receipt`。docstring は「fixed trust root」ではなく「fixed configured verification-key path」とする。

2. **real / issuer の再導出表と関数 docstring が再導出範囲を過大表示する。**  
   該当: [acceptance_issuer_reference.py:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_issuer_reference.py:6)、同 9–18、328–387、439。`tested_main` / `tested_tip` は caller の CLI 値との一致と Git object の存在を確認するだけで、issuer が独立に選定・再導出していない。`waiter_executed_sha256` は tip waiter blob の期待 hash と照合するだけで waiter process の実行 bytes を観測しない。`log_sha256` も caller 指定 path の終了後 bytes を hash するだけで、launcher による著作を証明しない。`re-derive its claims` は全 claim を再導出したように読める。  
   成果物への影響: signed report が main/tip の独立選定や waiter 実行実在を証明したものとして certified 選択・台帳から参照されうる。  
   逐語の修正案: `issue_signed_receipt` の docstring を「Execute tested-main's launcher, compare only the fields listed as issuer-derived expectations, preserve the remaining values as claims, and sign v6.」へ変更する。表では `tested_main` / `tested_tip` を「caller-bound context: exact Git commit existence and receipt equality only」、waiter 行を「expected content hash compared with `waiter_executed_sha256`; waiter process bytes are not independently observed」、log 行を「hash of the regular file at caller-supplied `--log-file`; authorship is not independently proved」とする。

3. **real / 段 4 の段 7 用逐語だけが、未実装の hook 防護を「追加した」と述べる。**  
   該当: `s4-adjudication.md:79-81,137-145` 対 `s5-author.md:79-85`。段 4 は外部 authority hook 防護を実装対象・記載可能事項に含めるが、段 5 は `guard_write.py` / `guard_bash.py` が不変で、Git-visible な変更は新規 4 file だけと報告する。`frag-decisions.md` 自体は hook を実装したとは書いていない。  
   成果物への影響: 段 7 が段 4 の逐語をコピーすると、存在しない防護面が worklog・台帳の保証として残る。production 受理集合への実影響はない。  
   逐語の修正案: 「署名検証 module・reference issuer・外部 authority の hook 防護を追加した」を「署名 payload／検証 library、reference issuer、fixture と検査を追加した」へ変更し、hook 追加は書かない。

4. **real / D431 の部分充足・unmet が台帳草稿に無く、test は未追跡 fixture を `tracked` と呼ぶ。**  
   該当: [test_external_acceptance_signing.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:148) 対 `s5-author.md:21-23,64`。production-v5 projection control はあるが、段 5 時点で fixture は untracked。operational issuer が発行した production signed-v6 を固定鍵 verifier へ通す control は存在しない。`frag-decisions.md` にこの区別がない。  
   成果物への影響: 台帳が D431 を全面充足と誤記し、再現不能な未追跡 fixture または test-key 正例を production control と数える。  
   逐語の修正案: 「D431 は部分充足である。実在 production-v5 receipt を canonical projection へ通す control と独立 literal／root-field 欠落反例は実装したが、本レビューでは未実走である。fixture は final commit で追跡されるまで充足と数えない。operational issuer が発行した production signed-v6 を固定設定鍵 verifier へ通す positive control は unmet であり、runtime test key の正例は production control ではない。」test docstring の `tracked production receipt` も、追跡完了までは `recorded production-v5 fixture` とする。

5. **real / D906 の 4 対象について「署名される field」と「独立に証明される事実」の対応表が不足する。**  
   該当: `frag-decisions.md:67-81`、[acceptance_receipt_signature.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:51)、[test_external_acceptance_signing.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:191)。草稿は checker と lease の限界は述べるが、main/tip、executor hash、verdict を含む全対応と、hash field の署名が実行実在を証明しないことを明示していない。`frag-decisions.md:71` の「issuer が起動した実行器の終了コード観測」も、正確には tested-main launcher が記録した `child_rc` を issuer が署名する構造である。  
   成果物への影響: 台帳の「D906 対応」が、署名された hash claim を実行 bytes の独立 attest として過大参照される。  
   逐語の修正案: 「D906 対象として署名 payload に実際に入るのは `tested_main`、`tested_tip`、`launcher_executed_sha256`、`waiter_executed_sha256`、`runner_executed_sha256`、`checker_blob_sha`／`checker_content_sha256`、`lease_generation`、`verdict` である。ただし入るのは識別子・hash・判定 claim であり、raw bytes や独立した process execution record ではない。特に waiter 実行 bytes は独立観測せず、checker content hash は期待 content hash、`lease_generation` は caller-supplied schema slot である。operational issuer・着地 verifier の bytes、同一 context の consume record は署名対象に含まれない。」を追記する。

6. **real / 未閉鎖項目 12 だけ、閉じない機序が書かれていない。**  
   該当: `frag-decisions.md:82`。項目 1–11 は機序を持つが、12 は「協調境界」とだけ記す。  
   成果物への影響: 次の作業者が署名部品の配線だけで候補コード性も閉じると誤認し、台帳の未閉鎖参照を消しうる。  
   逐語の修正案: 「**着地ツール自身が候補コードであること。** 着地 verifier は wave worktree 側の `tools/dev_wave_land.py` の bytes で実行され、main 起点の不変 bytes または外部 trust root へ束縛されていないため、候補が verifier を変更して署名検証を迂回できる。この協調境界は本 wave では閉じない。」

7. **refuted / 草稿に「閉じた」という記録が残る。**  
   該当: `frag-decisions.md:18-20,45-48,86-90`。現在の関門で効かない、enforcement 完了と数えない、正しさ主張は未閉鎖、と明記されている。  
   成果物への影響: なし。修正不要。

8. **refuted / single-use または特定 issuer 実行を保証する命名・記述がある。**  
   該当: `acceptance_receipt_signature.py:11-14`、`acceptance_issuer_reference.py:30-33`、`frag-decisions.md:50-52,74-75`。同一 context の一回性を保証しないこと、特定 issuer 実行を証明しないことを明記している。test 名も別 context 再送拒否に限定される。  
   成果物への影響: なし。修正不要。

9. **refuted / production の受理集合または既存 test の期待値を変更した。**  
   該当: `s5-author.md:25,68-85` と新規 3 file。production waiter/land/launcher の変更・caller 追加はなく、新規 test は test-key verifier と production-v5 projection だけを直接検査し、signed-v6 の production 受理を要求していない。  
   成果物への影響: production 受理集合、既存 test の期待値とも静的には不変。なお本レビューでは実走していない。

## 段 7 の逐語

**書いてよいこと**

- 「【機構追加・未強制】exact v5 payload から canonical signed-v6 payload を構築し、固定された設定済み公開鍵による Ed25519 署名と wave/main/tip/lease context を検査する library を追加した。」
- 「tested-main launcher を起動し、明記した Git blob／log の期待値を照合して署名する repository 内 reference issuer を追加した。operational issuer の配置または実行実在を意味しない。」
- 「main/tip 等の識別子、executor/checker の hash field、lease-generation slot、verdict を署名 payload に含めた。ただし、署名は field の意味的正しさや全 process の実行 bytes を独立に証明しない。」
- 「production-v5 fixture の projection control、test-key 機能正例、署名欠落・鍵違い・改竄・別 context 再送の負例を追加した。本レビューでは実走していない。」
- 「production waiter/land には配線しておらず、unsigned-v5 の既存受理集合を変更していない。」
- 「D431 は部分充足である。production-v5 projection control は実装済みだが、fixture は final commit で追跡されるまで充足と数えない。production signed-v6 を固定設定鍵 verifier へ通す positive control は unmet であり、test-key 正例は production control ではない。」

**書いてはならないこと**

- 「外部署名主体・operational issuer・鍵配置を実装した／稼働させた。」
- 「署名検証が production 着地関門で効いている」「unsigned-v5 を置換した」「signed-v6 を現行 land が受理する。」
- 「受領証は trusted／authentic／verified である」「payload の意味的正しさを証明した。」
- 「特定の reference issuer が実行されたことを証明した。」
- 「main/tip を issuer が独立に選定した」「waiter・checker を含む全実行 bytes を独立に証明した。」
- 「single-use／replay-protected／nonce により同一 context の再利用を防いだ。」
- 「production の lease generation を生成・配線した。」
- 「外部 authority hook 防護を追加した。」
- 「D431 を全面充足した」「production signed-v6 positive control が通った」「fixture は tracked である」（追跡完了前）。
- 「公式 runner、pytest 全走または本レビューの検査が緑だった。」
- 「D906 enforcement または着地受領証の真正性を閉じた。」

## must-fix

1. `trusted` 系 API・例外文を「固定された設定済み公開鍵」に限定した命名へ直す。
2. issuer の provenance 表と `re-derive its claims` を修正し、caller-bound／issuer-derived／未再導出 claim を分離する。
3. 段 7 の逐語から未実装の external-authority hook 防護を除く。
4. D431 の部分充足と production signed-v6 control の unmet を草稿へ追記し、fixture の tracked 表現を最終状態と一致させる。
5. D906 の署名 field 対応と、hash claim・実行実在の区別を逐語で追記する。
6. 未閉鎖項目 12 に、候補側 verifier bytes へ依存する具体的機序を追記する。

Nit（must-fix ではない）: `frag-decisions.md` が新規 test／fixture を実装一覧に含めないこと自体は、保証の過大記載ではない。

## 総括

real は 6 件、refuted は 3 件。  
production の受理集合変更、既存 test 期待値変更、将来必須化の先取りは静的には認められない。  
主要な問題は実装の効力ではなく、`trusted`、再導出、実行 bytes、D431 を実際より強く読める記録である。  
特に段 4 の hook 追加済み表現は現物と不一致なので、段 7 へコピーしてはならない。  
D906 enforcement、operational issuer、production signed-v6 positive control はすべて未閉鎖のままである。