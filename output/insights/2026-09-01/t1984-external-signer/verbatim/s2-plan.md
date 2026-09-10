## 実装プラン

結論から言うと、bootstrap 死の読みは正しいです。回避案も成立しますが、次の条件付きです。

- 署名は `acceptance_launcher.py` 内ではなく、事前配置済みの外部 issuer が launcher 終了後に付ける。
- tip 側 waiter は launcher を直接起動せず、外部 issuer だけを起動する。
- 外部 issuer と鍵は受入開始前に人手で配置済みでなければならない。
- 現在の hook は repo 外 issuer 領域を防護しないため、hook 改修も必要。
- `test_dev_wave_land.py` の既存 unsigned-v5 正例と新しい fail-closed 要件は両立しない。編集禁止のまま全テスト緑にする安全な実装計画は成立しない。

静的検査のみで、pytest は実行していません。

| file:line | 何を変更するか | なぜ | 受理集合への影響 |
|---|---|---|---|
| `tools/wave_land_window.py:57-68,121-149,163-179,227-308` | lease payload と `_Lease` に `lease_generation` を追加する。新規取得時だけ `secrets.token_hex(32)` で 64 桁 lowercase hex を生成し、renew 中は不変、release・stale 回収後の再取得では新値にする。 | `lease_holder` は wave slug の決定的 hash で世代ではなく、現行には fencing token がないため。 | generation 欠落・形式不正の lease からの新規署名発行を拒否する。受理追加なし。 |
| `tools/wave_land_window.py:351-493` | `claim` / `renew` の結果へ generation を返し、保持者・main・generation を一組で返す。legacy 3-field lease は少なくとも release できるようにするが、署名発行には使わせない。 | 現在の実 lease を安全に移行しつつ、legacy lease を署名根拠にしないため。 | legacy lease による receipt 発行を追加拒否。 |
| `tools/dev_wave_wait.py:448-455,2736-2880` | `_ClaimContext` に generation を追加し、`acquired` / `held-self` で exact 64-hex を必須にする。 | issuer に渡す自己申告値ではなく、lease primitive が生成した値を保持するため。 | generation 欠落を拒否。 |
| `tools/dev_wave_wait.py:2883-2911,3995-4012` | `held` / `queued` を `unclaimed=True` の receipt 発行へ流す経路を署名 receipt では廃止する。実 lease generation を持たない invocation は receipt を発行しない。 | 排他権を取得していない走行には署名できる排他世代が存在しないため。現行自身も `no fencing token` と明記している。 | 追加拒否のみ。並行 acceptance の一部が通らなくなる。 |
| `tools/acceptance_issuer_reference.py:1`（新規） | 外部配置用 issuer の reviewed reference を置く。production waiter はこの repo 内 copy を実行・import しない。issuer は Git から launcher blob を独立選択し、旧 main launcher の v5 出力を検査して signed v6 へ変換する。 | issuer の運用 bytes を候補 tip から実行しないため。main の旧 launcher をそのまま使えるので bootstrap 死を避けられる。 | issuer 不在・bytes 不一致・署名不能を拒否。 |
| `/work/1/SFC/tanab/dev-wave-authority/acceptance_issuer.py:1`（新規・人手配置） | 上記 reference のレビュー済み operational copy、Ed25519 秘密鍵、公開鍵を固定 subtree に配置する。鍵 path を argv・環境変数で上書きできる設計にしない。 | 実際の発行権限を repo 外へ出すため。Codex の workspace-write 子には配置させない。 | 配置されるまで全 signed receipt 発行を拒否。 |
| `tools/dev_wave_wait.py:848-875,3783-3817` | `_default_launch_launcher` を外部 issuer 起動へ置換する。`_launcher_binding` による tip waiter 側 source 選択を production 経路から外し、issuer が `tested_main` の launcher を自ら読む。waiter の outcome/completion pipe は issuer が中継する。 | 現在は waiter 自身が `Popen` しており、D583 の起動 authority 分離になっていないため。 | 外部 issuer を通らない launcher 起動を拒否。 |
| `tools/dev_wave_wait.py:3878-3897,3995-4001` | issuer process は、main launcher が v5 temp を書き終えた後、署名済み v6 に安全に置換してから exit 0 を返す。waiter は issuer exit 0 の後だけ既存 atomic publish を行う。 | 旧 main launcher の無署名出力を final receipt として公開しないため。 | 無署名 temp、issuer の途中終了、inode/path drift を拒否。 |
| `tools/acceptance_receipt_signature.py:1`（新規） | canonical v6 の構築・Ed25519 検証を実装する。署名対象は `issuer_signature` 自身を除く全 root field とし、最低でも `acceptance_wave`、`tested_main`、`tested_tip`、`lease_generation`、`runner_executed_sha256`、`checker_content_sha256`、`verdict`、`launcher_receipt_sha256`、`issuer_key_id` を含める。 | 一部 field だけの署名にして未署名 field の改竄経路を残さないため。 | 非 canonical、field 過不足、署名不正を追加拒否。 |
| `tools/dev_wave_land.py:94-130,775-785` | outer receipt を exact v6 field set とし、v5 fallback は置かない。内部 launcher v5 projection とその `launcher_receipt_sha256` は v6 内で検証する。 | 署名なしを互換経路で受けると D431 の恒真化と同型になるため。 | 旧 v5 receipt を拒否。 |
| `tools/dev_wave_land.py:934-1160` | 最初に issuer key ID・canonical bytes・署名を検証し、次に署名済み generation を live lease の holder/main/generation と比較し、その後に現行の fingerprint・launcher/waiter/runner/checker Git binding と verdict 構造検査をすべて残す。 | 署名の真正性、再送防止、既存 v5 検査の積集合を取るため。 | 追加拒否のみ。現行の構造検査を削らない。 |
| `tools/dev_wave_land.py:4933-5081,5531-5565` | receipt verifier の内部以外は順序を変えない。協調 lock、provenance、再 preflight、ff-only、fold の位置を保持する。 | 既存 land 権威を変えない制約のため。 | 署名以外の受理集合は不変。 |
| `hooks/guard_write.py:71-72,216-288,301-365` | `/work/1/SFC/tanab/dev-wave-authority` を lexical/canonical subtree と既存 inode alias の両面で拒否対象に追加する。単なる文字列包含ではなく path-component 境界で判定する。 | 現在の normal path は repo 外 issuer path を許可するため。 | acceptance には影響せず、AI の既知の直接書込み面を縮小。 |
| `hooks/guard_bash.py:78-107,2217-2243,2381-2426,2492-2621` | 外部 authority root を fast-path trigger、tree overlap、redirect、writer argument、ancestor mutation の対象に追加する。 | 現在は repo 外絶対 path を明示的に防護外としているため。 | acceptance には影響せず、literal Bash write を追加拒否。 |
| `hooks/README.md:15-31,89-115,297-364` | issuer subtree について閉じる exact surface と、script・変数展開・MCP・persistent shell・同一 uid の残余を記録する。 | 「AI が書けない」を OS sandbox と誤記しないため。 | なし。 |
| `orchestrator/tests/test_external_acceptance_signing.py:1`（新規） | production signed receipt fixture の positive control と、署名なし・鍵違い・field 改竄・別 generation への再送の4負例を置く。自走 harness を持たせる。 | D431 と D906 の直接検査。 | なし。 |
| `orchestrator/tests/test_plain_runner_coverage.py:44-86` | 新規 test file を含む file 集合列挙メタテストを焦点走へ含める。 | harness/allowlist 漏れによる 0-test 偽緑を防ぐため。 | なし。 |

`tools/acceptance_launcher.py` と `orchestrator/tests/test_acceptance_launcher.py` は、旧 main launcher が作る「内部 unsigned v5 record」の producer/test として原則変更しません。特に `test_acceptance_launcher.py:642-700` の canonical v5 検査を残すことで、外部 issuer が署名する前の入力契約を固定できます。

## 論点への回答

以下、論点ごとに確定事項と未確定事項を分けます。

## 論点 1 — bootstrap 死の回避経路

読みは正しいです。

- `tools/dev_wave_wait.py:2558-2577` は、`tested_main` に launcher があれば無条件に main blob を選び、無い場合だけ `tested-tip-bootstrap` を選びます。
- `tools/dev_wave_wait.py:2578-2596` はその blob bytes を取得・hash 照合します。
- `tools/dev_wave_wait.py:3783-3812` はその binding の source を waiter 自身が launcher process に渡して起動します。
- `tools/acceptance_launcher.py:23-28,170-171` は source revision を `tested-main` / `tested-tip-bootstrap` に限定します。
- `tools/acceptance_launcher.py:495-528` が作るのは unsigned v5 です。

したがって tip の `acceptance_launcher.py` に署名処理を追加するだけでは、本 wave の受入では main 側旧 launcher が動き、無署名 receipt ができます。tip 側 land が署名必須になれば自己拒否します。

回避は可能ですが、署名を launcher の責務にしないことが条件です。

- tip waiter の現行 direct launch 点 `tools/dev_wave_wait.py:3810-3812` を「外部 issuer 起動」へ変更する。
- issuer が `tested_main` の launcher source を独立に読み、旧 launcher を起動する。
- 旧 launcher が v5 temp を書いた後、issuer が内容・live lease generation・Git bytes を検査し、signed v6 に変換する。
- waiter は issuer が署名済み temp を完成させて exit 0 になるまで `tools/dev_wave_wait.py:3889-3897` で待ち、既存の `3995-4001` で publish する。

これなら main launcher が署名を知らなくても成立します。

ただし、外部 issuer と鍵を本 wave の acceptance より前に人手配置する必要があります。現在その実在経路はありません。したがって「事前配置を含めて本 wave が自力で完結する」は不可能です。成立するのは次のどちらかです。

1. 人が issuer/key を先に bootstrap してから本 wave を受け入れる。
2. groundwork wave → 人手 bootstrap → v6 強制 wave に分割する。

## 論点 2 — 「AI が書けない領域」の機械化

現行 hook は repo 外 issuer path を守りません。

`guard_write.py` の normal path は部分文字列判定ではなく subtree 判定です。

- `_inside` は `path == tree` または `path.startswith(tree + os.sep)`：`hooks/guard_write.py:71-72`
- `classify_path` は repo 内 hooks、campaign、exploration、s8b-freeze、ccbench だけを判定：`216-288`
- repo 外絶対 path も `335-357` で `classify_path` に入りますが、上記 subtree に一致しなければ `288` で許可されます。
- `379-395` の部分文字列検査は hook 内部例外時の fallback であり、通常の防護対象決定ではありません。

`guard_bash.py` も path-aware な subtree/prefix 判定ですが、repo 外は明示的に防護外です。

- `tools/guard_bash.py` ではなく `hooks/guard_bash.py:2217-2228` が絶対 path を正規化します。
- `2231-2238` は「repo 外絶対 path は相対化せず素通り＝防護外」と明記しています。
- 対象文字列が無い command は `2528-2529` で fast-path 許可されます。

必要な変更は、固定 external root を両 hook の対象集合へ追加することです。

- `guard_write.py:216-288`：lexical/canonical subtree と inode alias を拒否。
- `guard_bash.py:78-107`：mention/tree trigger へ追加。
- `guard_bash.py:2381-2426`：tree/argument 判定へ追加。
- `guard_bash.py:2492-2621`：redirect、ancestor mutation、未知 writer を拒否。
- path 判定は `/authority-x` を `/authority` と誤認しない component-aware subtree とする。

本当に効く範囲は、信頼済み PreToolUse が観測した次だけです。

- Write/Edit/NotebookEdit/apply_patch の direct path。
- literal path が現れる Bash の直接 writer、redirect、削除・移動。
- external authority subtree 内の既存 hardlink alias。

効かない範囲は次です。

- script file 内の write、変数展開、`python3 -c`、persistent shell。
- MCP/apps/plugins、IDE、cron、別 process。
- hook trust が未登録・不発の session。
- path literal を持たない Git 操作。
- 同一 uid による秘密鍵の read、process inspection、hook 外の filesystem 操作。

この限界は `hooks/README.md:28-31,89-115,297-304,351-364` にも明記されています。別 uid・別 host・hardware token が使えない前提では、完全な「AI が書けない／鍵を読めない」境界は機械化できません。hook で閉じるのは既知の直接書込み面だけです。

## 論点 3 — 署名対象 field の実在と到達可能値

現行 `_receipt_bytes` は `tools/acceptance_launcher.py:477-528` です。

| D906 項目 | 現行 v5 field | 根拠 | 判定 |
|---|---|---|---|
| 検査した main | `tested_main` | `acceptance_launcher.py:500` | 実在 |
| 検査した tip | `tested_tip` | `acceptance_launcher.py:501` | 実在 |
| 実行器の bytes | 主対応は `runner_executed_sha256` | `526`。実行 source の hash は `568`、main 再読照合は `595-601` | 実在 |
| launcher/waiter の実行 bytes | `launcher_executed_sha256` / `waiter_executed_sha256` | `524-525` | 実在。ただし waiter の実行実在は自己申告面を残す |
| 検査器の bytes | 最も近いのは `checker_blob_sha` | `514-516` | 不完全 |
| 排他権の世代 | 該当 field なし | receipt 全 field は `495-527` | 不在 |
| 判定 | `verdict` | `509`。導出は `_validated_completion` の `426-472` | 実在 |

`checker_blob_sha` は次の理由で D906 を完全には満たしません。

- Git blob OID であって executed SHA-256 ではない。
- `child-green` では null：`dev_wave_land.py:1005-1013`
- `non-attributable-only` でだけ main/tip checker blob 一致を確認：`1118-1151`
- land verifier 自身の bytes を意味するなら、対応 field は完全に存在しません。

したがって新設候補は `checker_content_sha256` です。issuer が `tested_main:tools/check_acceptance_reds.py` の blob bytes を自ら SHA-256 し、常に署名対象へ入れます。非帰属経路では実際の checker binding とも一致させます。「検査器」が land verifier を指すという解釈は資料から確定できず、これは段4裁定事項です。

排他世代については、現在の production lease は実測上、

```json
{"holder":"d2a2c86650e5","main_sha":"08a17b3b3271dc6e0db575a7c15afbbbb91f6328","ttl":2400}
```

の3 fieldだけです。`tools/dev_wave_wait.py:4012` も `no fencing token is provided` と明記しています。`lease_holder` は `sha256(wave)[:12]`：`2812-2835` であり、世代ではありません。

新しい `lease_generation` は次の契約とします。

- 値域：`[0-9a-f]{64}`
- 生成元：`wave_land_window._create_lease` が新規 lease 作成時に生成
- renew：不変
- release・stale 回収後の再取得：新値
- waiter・issuer・land が holder/main/generation の三つ組を照合

新値は未実装のため、production 実値はまだ実測できません。実装後の positive control は本物の `wave_land_window.claim` を一時 lease directory へ通し、

- acquire で具体的な 64-hex が出る
- renew/held-self で同じ値
- release→reacquire で異なる値

を測る必要があります。理論上の正規表現だけでは DW-O13 を満たしたとは記録できません。

再送防止は、署名対象へ少なくとも次を束縛し、land 時に request/live state と比較して成立させます。

- `acceptance_wave`
- `tested_main`
- `tested_tip`
- `lease_holder`
- `lease_generation`
- `runner_executed_sha256`
- `checker_content_sha256`
- `verdict`
- `issuer_key_id`

これにより、過去 receipt は別 wave、別 main、別 tip、別 lease acquisition へ再送できません。厳密な「同一 generation・同一 request でも一度しか使えない」single-use まで要求するなら、外部 consume ledger が追加で必要です。現資料からそこまでが D906 の必須意味かは未確定です。

## 論点 4 — issuer が独立に再導出できる範囲

issuer が独立に再導出または直接観測できる値です。

| field | issuer の根拠 |
|---|---|
| `acceptance_wave` | request の wave と lease holder の決定的 hash を照合 |
| `tested_main` | live lease の `main_sha` と Git object 実在を照合 |
| `tested_tip` | repo HEAD と Git object 実在を直接照合 |
| `lease_holder` | `sha256(acceptance_wave)[:12]` と live lease を照合 |
| `lease_generation` | 外部 lease file から直接読取り |
| `launcher_source_revision` / `launcher_blob_sha` / `launcher_executed_sha256` | issuer 自身が main launcher blob を選択・読取り・起動 |
| `runner_executed_sha256` | `tested_main:tools/run_tests.py` の blob bytes を独立 hash |
| `checker_content_sha256` | `tested_main:tools/check_acceptance_reds.py` の blob bytes を独立 hash |
| `waiter_blob_sha` | `tested_tip:tools/dev_wave_wait.py` を Git から再導出 |
| `log_sha256` | launcher 終了後に issuer が log を直接 hash |
| `launcher_receipt_sha256` | launcher が書いた exact canonical v5 bytes を直接 hash |
| `issuer_key_id` / `issuer_signature` | issuer 自身の公開鍵と秘密鍵から生成 |
| `argv` / `resolved_runner_path` | issuer が exact argv を構成し、任意値を受け取らない |

待ち手の自己申告のまま残る値です。

| field / 意味 | 閉じない理由 |
|---|---|
| `pre_fingerprint` | waiter が runner 前に計算したという主張。issuer が同じ時点を独立観測しない |
| `post_fingerprint` | 同上。構造・preとの一致だけでは実行時点の真正性にならない |
| `env_projection` | waiter process の実効環境は issuer から完全再構成できない |
| `waiter_executed_sha256` の「実際にその bytes が走った」という意味 | Git 上の期待 digest は再導出できるが、実行実在は waiter の自己申告 |
| `effective_scheduler` | 現行は waiter の log parser 結果 |
| `checker_rc` / `checker_status` | completion protocol からの自己申告 |
| `checker_receipt_sha256` | issuer に checker receipt 本体が渡らない |
| `red_nodeids` / `flake_nodeids` | completion protocol からの自己申告 |
| `verdict="non-attributable-only"` の意味的正しさ | 上記 checker 系自己申告に依存 |
| `tested_tip` が「待ち手自身が実際に検査した tip」であるという意味 | Git ref/object は再導出できても、waiter の検査実在までは証明しない |

`child_rc` はどちらの表にも完全には属しません。これは待ち手自己申告ではなく、issuer が起動した main launcher の観測値です。issuer が runner を直接 wait しない設計では「issuer 自身の独立再導出」とも言えません。

D583 の集合については、

- 現行 launcher が独立に得る3値は `child_rc`、`log_sha256`、`runner_executed_sha256`：`acceptance_launcher.py:582-610`
- 起動 authority を issuer へ移しても、この launcher 内の3値集合自体は変わりません。
- issuer はその外側で Git由来の main/tip/launcher/waiter/runner/checker digest、live generation、log hash を重複再導出できます。
- `child_rc` を issuer 自身の観測へ昇格するには、runner process の直接所有まで issuer へ移す別設計が必要です。

自己申告表に挙げた field は、署名しても内容の真正性は閉じません。

## 論点 5 — 編集面と所有の分割

安全な path 素集合は次のように割れます。

| 実装単位 | 専有 path |
|---|---|
| A: receipt/lease/issuer protocol | `tools/dev_wave_wait.py`、`tools/dev_wave_land.py`、`tools/wave_land_window.py`、`tools/acceptance_receipt_signature.py`、`tools/acceptance_issuer_reference.py`、`orchestrator/tests/test_wave_land_window.py`、新規 `orchestrator/tests/test_external_acceptance_signing.py` と fixture |
| B: external authority hook | `hooks/guard_write.py`、`hooks/guard_bash.py`、`hooks/README.md`、新規 `orchestrator/tests/test_external_authority_hooks.py` |
| H: human bootstrap | `/work/1/SFC/tanab/dev-wave-authority/` の operational issuer・秘密鍵・公開鍵。Codex 所有なし |

次の path は触りません。

- `orchestrator/tests/test_dev_wave_land.py`
- `orchestrator/campaign/artifact_admission.py`
- `orchestrator/campaign/campaign_lock.py`
- `orchestrator/campaign/contract_loader_binding.py`

ただし重大な競合があります。

`test_dev_wave_land.py:285-365` は unsigned v5 receipt を作り、`622-627` は schema が exact v5・field set が exact 27 field であることを固定しています。さらに `974-1009` など多数の正例がその receipt を `LAND.land()` へ通します。

したがって production `land()` が署名と generation を必須化すると、既存正例は必ず赤になります。新規 test file へ負例を逃がしても、この既存正例の入力は更新されません。

署名 optional、v5 fallback、test module 名による bypass、CLI だけ署名必須で `land()` は unsigned を許す、という回避はすべて発行 authority の迂回路になります。採用できません。

よって現在の「同 file 編集禁止」を保ったまま、D906 を production で強制し全走を保つ stage 5 単位は存在しません。段4で次のどちらかを裁定する必要があります。

1. 稼働中 wave の commit 後まで待ち、`test_dev_wave_land.py` の fixture/正例更新を許可する。
2. 本 wave は fencing/hook/issuer groundwork だけに分割し、署名強制は後続 wave に送り、間は明示的に未閉鎖とする。

新規 test file の file 集合メタテストは `orchestrator/tests/test_plain_runner_coverage.py:44-86` です。新規 file に `_run()` / `__main__` を持たせても、このメタテスト自体を焦点走へ含めます。

## 論点 6 — positive control

指定の production receipt は読めました。`acceptance-receipt-1.json:1` は canonical な v5 1行 JSONで、27 field を持ちます。

- `schema_version = dev-wave-acceptance-receipt/v5`
- `authority_kind = dev-wave-acceptance-launcher`
- `launcher_source_revision = tested-main`
- `child_rc = 0`
- `verdict = child-green`
- checker 4 field はすべて null
- `tested_main`、`tested_tip`、launcher/waiter/runner digest、fingerprint 等は実値
- `lease_generation`、issuer key ID、signature は存在しない

これは現行 field 構成の production control には使えますが、新しい署名述語の positive control には使えません。test key で後付け署名したものを「production signed receipt」と呼ぶのも D431 違反です。

正しい取得順は次です。

1. reviewed external issuer と鍵を人手配置する。
2. 実際の acceptance invocation から signed v6 receipt を発行する。
3. その exact receipt と公開鍵だけを tracked fixture に取り込む。秘密鍵は取り込まない。
4. test 内で fixture の重要 field を独立 literal と照合してから production verifier に通す。

期待値は test source 内の literal とし、次から作りません。

- `os.environ`
- production schema/key/path 定数
- verifier の戻り値
- production loader

positive control は、例えば次を literal 固定します。

- schema文字列
- acceptance wave
- tested main/tip
- lease generation
- issuer key ID
- verdict
- public key bytesまたはその公開 fixture digest

負例は同じ recorded fixture を基準に必ず4方向置きます。

- 署名なし：`issuer_signature` を削除し拒否。
- 鍵違い：独立 literal の別 public key で検証し拒否。
- field 改竄：`verdict` または `tested_tip` を変更し、再署名せず拒否。
- 再送：valid receipt を別の literal `lease_generation` または別 `tested_tip` の expected context へ渡して拒否。

D431 の恒真化と同型の退化については、次で検出できます。

- signed/unsigned 双方を受ける退化 → 署名なし負例が赤にする。
- trust root を無視する退化 → 鍵違い負例が赤にする。
- 一部 field を署名対象から外す退化 → field 改竄負例が赤にする。
- expected land context を比較しない退化 → 再送負例が赤にする。

v5 fallback が一つでも残れば、署名なし負例と production gate の分類が壊れるため不採用です。

## 未閉鎖

- OS 上の別 uid・別 host・hardware token が使えず、同一 uid の AI が鍵を読めないこと、issuer process を改変・観測できないことは保証できない。
- hook が閉じるのは、信頼済み PreToolUse が観測する direct Write/Edit/apply_patch と literal Bash writer だけ。script、変数展開、persistent shell、MCP/apps/plugins、IDE、cron は開いたまま。
- external issuer/key の人手 bootstrap は未実装・未実施。これなしでは本 wave 1本の acceptance は成立しない。
- `lease_generation` は現行 production に存在せず、提案した 64-hex の production 実測も未実施。
- legacy lease から generation 付き lease への移行方法と、現在保持中 lease の release 時点は未裁定。
- `child_rc` は main launcher の観測であって、issuer 自身による runner exit の独立観測ではない。
- `pre_fingerprint`、`post_fingerprint`、`env_projection`、`effective_scheduler`、checker 結果、red/flake nodeid は待ち手の自己申告性を残す。
- `waiter_executed_sha256` は期待 Git bytes と照合できても、実際にその bytes が走ったことまでは証明しない。
- 「検査器」が red checker を指すのか land verifier を指すのかは資料から未確定。現行 v5 はどちらの解釈でも完全な executed-bytes field を持たない。
- lease generation による再送防止は別 wave/main/tip/lease acquisition 間を閉じる。完全な single-use を要求するなら外部 consume state が別途必要。
- land verifier 自身が候補コードである T-696 境界は残る。
- 親の起動点が external issuer を省略して別経路を直接呼ぶ問題は、hook だけでは完全には閉じない。
- `test_dev_wave_land.py` 編集禁止中は、安全な署名必須化と既存全走の両立が不可能。
- 以上が残るため、D1197 に従い「外部署名主体で真正性が閉じた」とは記録できない。

## 総括

bootstrap 死の診断は正しく、外部 issuer が旧 main launcher の v5 出力を後段で署名する配線なら回避できます。  
lease generation、全 field 署名、live generation 比較、4方向負例の設計は採用可能です。  
現行 hook は repo 外 path を守らないため、そのまま「AI が書けない」とは扱えません。  
外部 issuer/key の人手 bootstrap が無い状態では、本 wave 1本の自力完結は不可能です。  
さらに `test_dev_wave_land.py` の unsigned-v5 正例を編集できない限り、安全な production 強制と全走は両立しません。  
段4では「人手で事前配置し、競合解消後に1 waveで強制」か「groundwork と強制を2 waveへ分割」の択一が必要です。