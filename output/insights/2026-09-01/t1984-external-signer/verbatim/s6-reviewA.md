## 所見

1. **real / production 用の固定 trust-root 境界をテストが一度も通っていない。**  
   [test_external_acceptance_signing.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:123) の全署名テストは、caller が作った `TrustedPublicKey` を低水準 API へ直接渡す。[同:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:268) も環境変数を設定した後、定数を比較するだけで loader を呼ばない。このため [acceptance_receipt_signature.py:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:368) が署名検証を迂回したり、環境・receipt 由来の鍵を採用しても現行 11 test は緑になりうる。  
   成果物への影響: activation 時にこの public boundary が配線されると、偽署名 receipt に基づく certified 選択が report・台帳へ記録されうる。現行 production 受理集合は未配線なので今は不変。  
   修正案: test 用固定 PEM と攻撃者 PEMを用意し、`verify_trusted_signed_receipt()` を直接通す正例・鍵違い負例を追加する。環境変数が攻撃者 PEM を指しても固定側を読むこと、trust root 欠落・不正 PEM が `ReceiptSignatureError` になることも実呼出しで固定する。test-key control であり production control とは呼ばない。

2. **real / M6・M7 は対象実装も負例も存在せず、KILLED になりえない。**  
   登録位置は [s4-adjudication.md:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1984-external-signer/s4-adjudication.md:120) だが、[s5-author.md:72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1984-external-signer/s5-author.md:72) のとおり hooks は不変で、`test_external_authority_hooks.py` も存在しない。さらに今回の A4 は hooks 編集自体を禁止している。  
   成果物への影響: 変異台帳・段 7 report が、実在しない hook 防護を KILLED／充足済みとして誤記できる。  
   修正案: M6・M7 を本 wave の登録から外し、下記の実在する署名境界へ差し替える。hooks を追加する修正は行わない。

3. **refuted / 署名 field の存在だけで通る実装ではない。**  
   [acceptance_receipt_signature.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:300) が exact root-field 集合を要求し、[同:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:358) が固定鍵の key ID と照合、[同:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:360) が Ed25519 を実検証する。receipt が公開鍵または鍵 path を運ぶ field はない。  
   成果物への影響: なし。  
   修正案: コード修正なし。境界テストのみ所見 1 のとおり補う。

4. **refuted / trust root と `cryptography` はコード上 fail-closed。**  
   固定 path は [acceptance_receipt_signature.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:39)。欠落・読取不能・非 regular・過大・読取中変化は [同:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:245)、不正 PEM・非 Ed25519 は [同:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:287) で拒否する。`cryptography` import 失敗は [同:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:29) で `RuntimeError` となり、skip・xfail・握り潰しはない。  
   成果物への影響: なし。  
   修正案: 実装修正なし。ただし所見 1 の負例で回帰を固定する。

5. **refuted / canonical 化は決定的で、launcher の 27/27 root field が署名対象に入る。**  
   [acceptance_receipt_signature.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:105) は `sort_keys=True`、固定 separator、ASCII escape、末尾改行を使う。[acceptance_launcher.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_launcher.py:495) との集合照合結果は次の全 field が COVERED: `acceptance_wave`, `argv`, `authority_kind`, `checker_blob_sha`, `checker_rc`, `checker_receipt_sha256`, `checker_status`, `child_rc`, `effective_scheduler`, `env_projection`, `flake_nodeids`, `launcher_blob_sha`, `launcher_executed_sha256`, `launcher_source_revision`, `lease_holder`, `log_sha256`, `post_fingerprint`, `pre_fingerprint`, `red_nodeids`, `resolved_runner_path`, `runner_executed_sha256`, `schema_version`, `tested_main`, `tested_tip`, `verdict`, `waiter_blob_sha`, `waiter_executed_sha256`。追加 3 field も含め、除外されるのは `issuer_signature` 自身だけ。  
   成果物への影響: なし。  
   修正案: なし。

6. **refuted / 4 方向の負例は生成可能。ただし「署名なし」だけは Ed25519 層の証拠ではない。**  
   [test_external_acceptance_signing.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:227) の署名なしは、[acceptance_receipt_signature.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:301) の exact-schema gate で先に赤となる冗長 gate であり、M1 の証拠には数えられない。鍵違い [test:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:233) は key ID を誤鍵に合わせているため拒否理由は `InvalidSignature` のみ。field 改竄 [test:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:241) は expected tip も合わせており署名不一致のみ。lease/tip 再送 [test:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:250) は署名済み receipt を変更せず、context mismatch のみで赤になる。  
   成果物への影響: なし。鍵違い・改竄が Ed25519 の実効負例を提供している。  
   修正案: 署名なし負例を M1 の根拠として台帳へ書かない。

7. **refuted / D431 control は恒真化しておらず、production signed control とも呼んでいない。**  
   期待 hash・長さ・wave/main/tip は [test_external_acceptance_signing.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:29) の独立 literal。fixture は指定原本と byte-for-byte 同一で SHA-256 は双方 `e4026458…63d4`。[同:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:148) は exact projected hash を要求し、[同:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:169) は反対クラスを拒否する。test-key 正例は [同:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:218) で production control ではないと明記されている。  
   成果物への影響: なし。production signed-v6 control は正しく unmet のまま。  
   修正案: なし。

8. **refuted / A4 の禁止事項への違反は確認できない。**  
   `test_dev_wave_land.py`、`dev_wave_land.py`、`dev_wave_wait.py`、`acceptance_launcher.py`、`wave_land_window.py`、`hooks/`、3 campaign module、`docs/` はすべて Git 上不変。production caller はなく、現行 land は [dev_wave_land.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/dev_wave_land.py:94) の v5 exact schema のまま。lease generation は schema slot のみ。新 test は [test_external_acceptance_signing.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:285) に自走 harness があり allowlist 未登録。HEAD は main と同一で実装は未 commit。第三者 import は `cryptography` のみで、秘密鍵 bytes の literal・log・例外・戻り値露出はない。  
   成果物への影響: なし。production 受理集合・lease 排他・成果物参照は不変。  
   修正案: なし。

## 変異の再照準

- **M1: KILLED。** 実装には「等値比較」はないため、位置を「[acceptance_receipt_signature.py:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/tools/acceptance_receipt_signature.py:361) の `InvalidSignature` を握り潰して成功扱い」に言い換える。鍵違い・改竄負例はいずれも署名不一致だけで赤になる。
- **M2: SURVIVES。** 現行 test は loader を呼ばない。差し替えは「`_read_fixed_public_key()` が固定定数でなく `IZANAGI_ACCEPTANCE_PUBLIC_KEY` を採用する」。固定 PEM A・環境指定 PEM B を実際に loader へ読ませ、A の key ID 以外なら失敗させる。
- **M3: KILLED。** [test_external_acceptance_signing.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:191) の独立 31-field literal と canonical bytes の集合比較が、任意の 1 root-field 脱落を単独で検出する。
- **M4: KILLED。** 変異を具体的に `sort_keys=True → False` と固定する。fixture の projected hash は正規化時 `98c37c…4cfde`、挿入順時 `c9d8db…14618c` で異なり、独立 hash literal だけで赤になる。
- **M5: KILLED。** `tested_tip` 比較を省くと [test_external_acceptance_signing.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1984-external-signer/orchestrator/tests/test_external_acceptance_signing.py:261) は、他 context field と署名が有効なまま通って失敗する。
- **M6: 対象なし。** hook 部分文字列判定変異を削除し、「`verify_trusted_signed_receipt()` が固定 loader と低水準署名検証を迂回して payload を返す」へ差し替える。高水準 API に誤署名 receipt を渡す負例で単独 kill する。
- **M7: 対象なし。** hook root 集合変異を削除し、「`acceptance_wave` context 比較を省く」へ差し替える。正しい署名を別 wave の expected context に再送し、他条件を同一にした負例で単独 kill する。

## must-fix

- 固定 trust-root loader と `verify_trusted_signed_receipt()` を実際に通る test-key control を追加し、誤鍵・環境指定鍵・trust root 欠落・不正形式が fail-closed になることを固定する。
- 変異登録の M2・M6・M7 を上記へ差し替え、M1 の位置を例外握り潰し変異へ訂正する。M6・M7 を現状のまま KILLED と記録してはならない。
- hooks・production land・lease payload へは配線せず、受理集合を変更しない。

## 総括

静的検査のみで、pytest・自走 harness は実行していない。  
署名実装本体は field 存在だけの恒真 gate ではなく、27/27 field を決定的 bytes へ正規化して Ed25519 検証している。  
4 負例のうち署名なしは schema 層の拒否だが、鍵違い・改竄・context 再送は意図した単一理由で赤になる。  
D431 fixture、独立 literal、production signed control の unmet 表記、A4 scope は妥当。  
must-fix は production 用高水準境界の未テストと、M2・M6・M7 の無効な変異登録である。