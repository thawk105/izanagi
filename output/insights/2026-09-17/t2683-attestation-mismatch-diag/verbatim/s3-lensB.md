## 総括

- 独立所見は **real 2 件、refuted 5 件、must-fix 2 件**。静的検査のみで、pytest は実行していない。
- must-fix は、**production closure の配線を通らない試験計画**と、**診断 I/O の停止が失敗成果物の回収を妨げる経路**。
- sidecar は共有 attempt に残り、既存 collector の failure receipt から参照される。読み手不在という攻撃は refuted。
- P1 の「例外 message を保持する」は確認できたが、「失敗比較が成果物に残るので既存策で足りる」までは成立しない。
- 親 brief の `create_json` 指定と D474 の非 fsync 方針の衝突は、実装前に解消すべき。
- 以下、`driver` は `orchestrator/qualification/t126_driver.py`、`tests` は `orchestrator/tests/test_t126_qualification_driver.py`、brief・plan は指定された wave 資料を指す。

## 1. sidecar は読み手に届くか

**所見：refuted — 正常に公開できた sidecar には既存の保存・参照経路がある。**

- wrapper は `QUAL_ROOT="$REPO_ROOT/output/env/pegasus/qualification/t126"` と共有側を指定する。attempt は `/scr` の build cache とは別である（`tools/pegasus/t126_qualification.sh:56`）。
- driver の stderr は `job-staging/<job>.<nonce>/driver.stderr` に保存される。attempt の選択は stdout ではなく、提出済み attempt ID による（同 `:843–850`）。
- 失敗時にも attempt を削除する処理はなく、`job-result.json` をその attempt に書く（同 `:150–199`）。
- collector の `_manifest()` は attempt 内の通常ファイルを列挙し、failure receipt の `closure_manifest` に含める（`orchestrator/qualification/collector.py:228`, `:1318`, `:1371`）。post-job verifier もその closure を検査する（同 `:1524`）。

したがって、運用者は attempt の sidecar を直接読め、回収後は failure receipt の manifest から辿れる。専用レポート renderer はなくても「書いただけ」ではない。

**是正案：** scope 内では、既存 collector を呼ぶテストを所有 test file に追加し、sidecar が failure closure に入ることを確認する。wrapper・receipt schema の変更は不要。

なお rc=31 の表示は post-series 失敗でも `pre-attestation` のまま（wrapper `:211`）。stage の判別には sidecar／series ledger を使えるため、分類名の修正は今回の must-fix ではない。

**成果物への影響：** failed attempt の failure receipt に sidecar の path・size・hash が追加される。certified 選択と成功 receipt の受理述語は変わらない。

## 2. 親 brief P1 の実測の一般化

**所見：直接の message 握り潰しは refuted。ただし永続成果物への保存を一般化できない。**

`execution_guard.py:616–624` は非 pass 行を JSON 化して例外に含める。呼び手の到達先は次のとおり。

| 呼び手 | message の到達先 |
|---|---|
| `loop.py:187` | 例外をそのまま伝播。`run_campaign` の layout／WAL 作成前である（`:517`）。例えば `p2_2.py:376` → CLI は未捕捉 traceback として stderr に出る。campaign WAL には残らない。 |
| `s8b_oracle_driver.py:968` | `OracleDriverError` → refusal の文字列（`:980`, `:1458`）→ CLI の stdout JSON（`:2048`）。開始前なので WAL は書かない。 |
| 同 `:1147` | 再検査失敗 → session の `deviation.message` に保存（`:1637–1643`）。返却結果の `error` にも残る（`:1954`）。 |
| `screening_driver.py:336` | `_attest_required_contract` から伝播。`:468`／`:560` は後続 WAL 処理より前。例えば `backoff_sweep.py:317` の呼出しは CLI まで伝播して stderr traceback になる。 |
| `s8b_floor_campaign.py:7379` | `FloorCampaignError(str(exc))`（`:7398`）→ CLI stdout の error JSON（`:8684`）。初期拒否の成果物は作らない。 |

明示的に message を捨てる経路は、この追跡範囲では発見していない。stdout／stderr への出力を「捨てられる」とは扱わない。一方、それらの保存は外側の実行環境に依存する。

また、guard が保持するのは **非 pass 行だけ**であり、brief P2 の全比較行保存とも同一ではない。

**是正案：**

- **本 wave：** P1 を「message の伝播は維持されている。構造化 sidecar の永続保存は未対応だが、今回の変更対象は T126」と限定する。guard の bytes 不変は維持できる。
- **裁定候補：** 開始前・副作用ゼロの拒否に対して、stdout/stderr 保存で十分か、外側で診断を保存するかを決める。guard 自身への書込み追加を既成事実にしない。

**成果物への影響：** 拒否・certified 選択は不変。ただし開始前失敗では比較行への成果物参照がなく、生ログを失えば原因の値も失われる。この限界は今回解消されない。

## 3. 抽出 helper の実効性

### B1：real・must-fix — helper の緑が production 配線を証明しない

plan `:234–251` の新テストは helper を直接呼び、台帳テストも独自の `attestation_fn` を作る。production の `run()` 内 closure を通らない。

具体的な生存変異は次のとおり。

1. helper と新テストはそのままにする。
2. `driver:1204–1212` を現行処理のまま残す。
3. `_attest` の typed mismatch は現行 `except BaseException` に捕まり、子は31で終了する。
4. sidecar は存在せず、親は従来 message で拒否する。
5. helper 直呼びテストはすべて緑になり得る。

同様に、`driver:1243` だけ固定 message に戻しても、message helper の単体試験は通る。

**是正案：** 所有 test file で production `run()` の closure を実際に通す不一致テストを追加する。前段の認可・probe は fixture 化してよいが、fork、helper 委譲、wait、親の例外、台帳への記録は実物を通す。少なくとも上記二つの配線変異を killer に登録する。

**成果物への影響：** 配線漏れを放置すると受理集合は同じでも、実走の sidecar と台帳の診断参照が欠落し、T-2683 が未解決のまま完了扱いになる。

### capability 継承・通常終了への攻撃：refuted

`QualificationWriteCapability` は process ID に束縛されず、token と inode identity を検査する（`artifacts.py:145–205`）。fork はこれらを継承する。`create_json` は同期的に書込み・flush・fsync を完了して返る（同 `:465–492`, `:527`）。

したがって、提示された骨格どおりなら `os._exit` による Python buffer の未 flush は通常経路の問題にならない。ただし停止・強制終了は観点7の問題である。

**成果物への影響：** 通常完了した書込みについて、fork 継承や `_exit` だけを理由に sidecar が失われる根拠はない。

## 4. 親側 message の変更

**所見：refuted — 通常の診断 message 拡張は replay 契約を壊さない。**

- `run_series` は `str(exc)` を evidence に載せる（`driver:766`, `:819`）。
- `SeriesFSM.reject()` は evidence 全体を canonical JSON 化し、その bytes の hash を作る（`orchestrator/qualification/series.py:366`）。
- replay は外側の exact keys と hash を検査し、message の固定値や長さを要求しない（同 `:125–138`）。
- 既存 `test_attestation_failure_is_terminal_reject_with_exact_rc` は rc・rejected・観測数を確認するテストであり、固定 message を pin していない（`tests:660`）。
- 失敗では成功 series result の作成に到達しない（`driver:1282–1288`）。`verify()` が失敗 attempt を新たに成功扱いする変更でもない。

21 field の名前だけを載せる message に、現行コード上の長さ制限との衝突は見当たらない。実害を示せないため、短縮要求は nit。

**是正案：** plan の実 FSM／replay テストを維持し、production 配線まで接続する。全21 field の短縮仕様を追加する必要はない。

**成果物への影響：** reject evidence の bytes/hash は意図的に変わるが、台帳の形・replay の受理述語・成功時の attestation payload は変わらない。

## 5. 所有範囲・並行 wave

**所見：refuted — 計画された hunk による既存構造 pin の直接破壊は見当たらない。**

確認した pin は以下であり、追加 helper は該当 callsite を増減しない。

- `tests:229`：`validate_member_evidence` と prologue observation の call 数・引数。
- `test_campaign.py:5526`：`pipeline.evaluate` が1箇所で、authorization を渡すこと。
- `tests:370`：`build_run_context` の文字列。
- `test_t126_pegasus_tools.py:4533`：`validate_qsub_binding` の call 数。
- `test_official_perf_closure.py:254`, `:400`, `:660`：member evaluator と perf guard の配線。
- `test_artifact_admission.py:280`, `:306`, `:544`：driver を含む closure path 集合。

**是正案：** plan `:256` の焦点走を driver test だけに限定しない。末尾の consumer files を含める。今回の変更を理由に pin を緩める必要はない。並行 wave の実際の変更有無までは、この静的検査では保証しない。

**成果物への影響：** 計画どおりなら構造 pin に由来する受理集合変更はない。driver bytes が変わるため、新規実行の code identity とそれに依存する参照は変わる。

## 6. 変異 matrix の帰属

plan `:267–275` を、記載された assertion に対応させると次のとおり。

| 変異 | 静的評価 |
|---|---|
| M1 | sidecar の存在検査が赤になる。 |
| M2 | 成功時の sidecar 不在検査が赤になる。 |
| M3 | governor を含む `failed_fields` の検査が赤になる。 |
| M4 | 21行・20 pass 行の検査が赤になる。 |
| M5 | 空比較の sidecar 検査が赤になる。 |
| M6 | helper の返却値31の検査が赤になる。ただし production の親は非ゼロをすべて31へ変換するため、「外部 rc 不変」の専属証明ではない。 |
| M7 | probe 失敗時の sidecar 不在検査が赤になる。 |
| M8 | **変更箇所に依存。** message helper を固定文言化すれば赤。production `raise AttestationError(...)` だけを固定文言化すると、指定 killer は緑のまま。 |
| M9 | reader の OSError ケースで赤になる。 |
| E1 | comment だけなら生存する等価対照として妥当。 |

**real は B1 と同じ配線欠落であり、重複計上しない。** M8 は編集対象を exact に指定し、production callsite の変異を別登録すべき。

既存テストだけで殺せるのは、比較述語を緩める変異、空比較を受理する変異、probe 例外の既存包装を壊す変異（`tests:320`, `:329`, `:349`, `:361`）。M1〜M9 の sidecar／helper の追加動作は、既存テストだけでは基本的に検出できない。

**成果物への影響：** helper のみを撃つ matrix では、実走の診断参照欠落を見逃す。M6 の helper rc 差だけなら production 成果物の拒否分類は変わらない。

## 7. scope 逸脱

### B2：real・must-fix — 「診断 write が失敗しても31」は回収結果の不変を保証しない

plan `:286` は fsync stall を認めつつ、「rc=31 のまま」と説明している。しかし次の具体的経路が残る。

1. 新規 mismatch sidecar の staging file を作る（`artifacts.py:452–459`）。
2. `os.fsync(fd)` などで子が停止する（同 `:470`）。
3. attestation timeout が子を SIGKILL する（`driver:1234–1237`）。
4. SIGKILL では `finally` の staging 削除が実行されない（`artifacts.py:487–491`）。
5. collector は `.create-*` の残存を拒否する（`collector.py:238–240`）。

結果は、診断を足さなければ回収できた不一致 attempt に対して、**failure receipt の発行まで阻害し得る**。通常の書込み例外は `finally` で清掃されるため、それ自体を問題とはしない。plan の `create_json` を丸ごと例外化するテストでは、この強制終了経路を検証できない。

さらに親側の sidecar 読取りは子の deadline 管理外で行われる案であり、例外捕捉は I/O の停止を上限時間に制限しない。wrapper の外側 timeout に達すると rc=124 になる可能性もある（wrapper `:834–843`）。

**是正案：**

- **本 wave：** 親 brief の `create_json` 指定を無条件採用せず、D474 `:10` の非 fsync 方針との解決を実装条件にする。writer 内部での停止・強制終了と、その後の failure closure 回収を受入条件へ加える。
- **裁定候補：** capability を保った非 fsync 診断 writer を2 file内に設けるか、共通 artifacts API／collector の診断 staging 回収まで scope を広げるか。共通層を変更せず「解決済み」とはできない。
- collector が未知 staging を拒否する既存防壁を、今回のために一括緩和してはならない。

**成果物への影響：** certified 選択は依然拒否でも、failure receipt とその台帳終端参照が作れなくなる。親読取りの停止では job-result の rc／failure class も変わり得る。

新 gate・validator・成功 receipt を追加しない方針自体は scope 内。P1 の guard 不変更も、観点2の未保証部分を明示すれば、T126 の局所修正として説明できる。

## 裁定パッケージ候補

1. **診断 I/O と回収可能性：** D474 の非 fsync を満たす writer の置き場所と、強制終了後の診断 staging の扱い。B2 の解決に必要。
2. **execution_guard の開始前拒否：** stdout/stderr の比較行で十分とするか、外側で sidecar 保存を担うか。副作用ゼロの既存契約との調整を含む。

## 焦点走に含める test file

- `orchestrator/tests/test_t126_qualification_driver.py`
- `orchestrator/tests/test_t126_pegasus_tools.py`
- `orchestrator/tests/test_t126_qualification_artifacts.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_artifact_admission.py`
