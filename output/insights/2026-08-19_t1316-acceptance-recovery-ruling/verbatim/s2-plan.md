# 裁定パッケージ草稿 — T-1316

## R-A. `merge-message-file` を常時用意して postclaim race を閉じるか

### 事実

- preclaim では、指定済み message file の実在を確認し、`HEAD..main > 0` なのに未指定なら claim 前に `merge-message-preflight` で停止する。`tools/dev_wave_wait.py:3732-3747`
- claim 後は main と `behind` を再確認する。`behind > 0` では、まず `owned-path-overlap` を検査し、その後 message file の未指定・読取不能・形式不備を `merge-message` として停止する。`tools/dev_wave_wait.py:3773-3798`
- 有効な copy があれば merge、message provenance 検査、commit へ進む。`tools/dev_wave_wait.py:3799-3848`。ただし `check_ai_provenance.py --message-file` は merge 後の prospective parent と変更 path も検査するため、message の妥当性を完全に main 非依存とは言えない。`tools/check_ai_provenance.py:2585-2609`
- `_message_has_ai_agent` は「非空かつ `AI-Agent:` で始まる行が少なくとも 1 行」を見るだけで、exact 1 行や trailer schema は保証しない。`tools/dev_wave_wait.py:2891-2909`。brief の「1 行」が exact 1 行を意味するなら訂正が必要である。
- 受入 command が起動する前の `merge-message` 失敗では child rc が存在せず、retry evidence も設定されない。`tools/dev_wave_wait.py:3709-3712`, `3957-3969`
- 再試行は `retryable-no-verdict-infra` の肯定的証拠がある場合だけで、それ以外は cleanup に進み lease を release する。`tools/dev_wave_wait.py:4186-4238`, `4255-4261`。`_release_once` は release 結果を検証している。`tools/dev_wave_wait.py:2912-2933`
- D486 はこの再試行境界と lease 保持を明示的に固定している。`docs/decisions.md:20259-20284`。release 後の再 claim は新しい待ち札となり、先着順を失う。`docs/decisions.md:20297-20299`
- CLI の `--merge-message-file` は現在 optional である。`tools/dev_wave_wait.py:1607-1625`。同じ `Path | None` が attempt 1/2 へそのまま渡される。`tools/dev_wave_wait.py:4297-4311`, `4323-4342`
- 既存 pin は、valid message なしの postclaim race が `merge-message` で終わり、claim 1 回・submission 0 回・release 1 回になることを固定している。`orchestrator/tests/test_dev_wave_wait.py:6736-6745`
- brief の「使用箇所 8 行」は誤りで、production source の列挙自体が 9 行 (`1613, 3689, 3732, 3739, 3793, 3795, 4301, 4329, 4437`) である。さらに tests から `run_acceptance` を直接呼ぶ箇所もある。`orchestrator/tests/test_dev_wave_wait.py:1341-1365`
- canonical な Pegasus runbook は既に message file を command に渡し、待機前に用意し、repo 外へ置くよう指示している。`docs/pegasus-runbook.md:803-813`, `921-922`, `991-992`。したがって `docs/dev-wave/operations.md` への追記だけでは、既存規約の強化であって機械的な enforcement ではない。

### 効き

P1 の条件を厳密に守り、各 wave 専用の valid な message file を repo 外に作成して process 終了まで保持し、初回・内部 attempt の全 invocation に渡すなら、今回の `merge_message_file is None` による `merge-message` 分岐は到達不能になる。`behind == 0` なら file は merge に使われず、余計な merge も発生しない。`tools/dev_wave_wait.py:3789-3798`

ただし、P1 が消すのは「message input が無い/読めない」sub-race だけである。queue 待ち自体、main の移動、`owned-path-overlap`、merge conflict、merge 後の provenance failure は残る。既存 runbook に近い規約があっても、実際の omission は再発しているため、運用規約だけでは不変条件を機械的には保証しない。

### 択一

1. **P1 — 運用規約のみ**

   各 wave で repo 外の immutable な message file を待機前に作り、`--merge-message-file` を常時渡す。内容は単なる `AI-Agent:` 接頭辞ではなく、`docs/ai-provenance.md:9-31` と `check_ai_provenance.py --message-file` を通る完全な trailer とする。既存 pin `test_postclaim_merge_message_requirement_still_catches_main_race` は残す。

   **条件付き暫定推奨。** コード変更ゼロで即時に特定 race を閉じられるが、既存規約の再掲に留まり、CLI omission や file の削除・書換えは防げない。単独の恒久策としては非推奨。

2. **P2 — CLI/API で必須化し、claim 前に message を snapshot する**

   `tools/dev_wave_wait.py:1613` を必須引数にし、`run_acceptance` 側 (`4297-4311`) でも `None` を拒否する。さらに `_validated_message_copy` (`2897-2909`) を queue 待ち前へ移し、postclaim では元 file ではなく保持した temp copy を使う (`3732-3798`, `4181-4185`)。full provenance 検査 (`3799-3825`) と `owned-path-overlap` は維持する。pin test (`6680-6746`) には「claim 前拒否」を追加し、既存の fail-closed 検査を削除しない。

   **推奨。** omission と queue 待ち中の file 消失・書換えをコードで封じられる。API 互換性と tests の更新が必要で、merge-context 依存の provenance failure までは解消しない。

3. **P3 — message をコード側で自動生成する**

   `merge-message-file` を省略した場合に待ち手が既定 trailer を生成し、`3732-3798` の failure を回避する。

   **非推奨。** model・reasoning・role の帰属、implementation author 要件、prospective merge の変更 path は現在の merge context に依存する。`tools/check_ai_provenance.py:1231-1261`, `2585-2609`。誤った固定 trailer は provenance の虚偽記録になり得る。

4. **現状維持**

   optional argument と postclaim pin を残し、`merge-message` 失敗時は従来どおり release する。

   **非推奨。** fail-closed 自体は守るが、D253 の待ち札を失い、D486 が再試行を許さないため、t1180 の 52 分級の待ち直しを再発させる。`docs/archive/worklog-phase3-0817-630-631.md:583-587`

### 親の推奨

P2 を恒久策として裁定へ提出する。P1 は、コード変更を避ける場合の暫定 mitigation としてのみ採用し、`docs/pegasus-runbook.md` の既存規約を「behind の有無に関係なく、全 invocation で、process 終了まで保持」と明文化する。

D253 の FIFO 意味論、D486 の retry evidence 境界、受領証 schema、rc 意味論は変更しない。

## R-B. P1 が閉じない postclaim failure と scope 外の回復

### 事実

- `owned-path-overlap` は message 検査より先に terminal failure になる。P1 で救済してはならない。`tools/dev_wave_wait.py:3790-3797`
- message が存在しても、merge 後の provenance 検査に失敗すれば受入 command は起動せず cleanup される。`tools/dev_wave_wait.py:3799-3838`, `docs/pegasus-runbook.md:975-988`
- D253 は FIFO を定めるが、待ち時間の上限は保証していない。`docs/decisions.md:11664-11670`
- `merge-message` を retryable infra failure に分類するには、D486 の six conditions を新設・変更する必要がある。`docs/decisions.md:20263-20272`

### 効き

「検出はできるが release して待ち札を失う」現状は安全側だが、回復性はない。message 不備を同一 process 内で再試行可能にすると待ち直しは減る一方、D486 の肯定的証拠境界と lease 占有時間を変更する。

queue timeout を短くしても postclaim race は消えず、claim churn と FIFO 運用コストだけが増える。

### 択一

- **現行 fail-closed を維持する** — 正しさと D486 を守るが、回復性は P1/P2 に委ねる。**推奨。**
- **pre-command failure も lease 保持のまま再試行する** — 待ち札喪失を減らせるが、D486 の境界変更と新しい肯定的証拠が必要。**非推奨・別裁定。**
- **queue 待ちを短縮する** — 待ち時間の観測値は変わるが race の原因を解かない。D253 の FIFO/待ち時間意味論に触れるため **scope 外**。

### 親の推奨

T-1316 は message input の可用性だけを扱い、`owned-path-overlap`、merge provenance、queue timeout、pre-command retry は別裁定へ残す。D253/D486 を緩める recovery は採用しない。

## 総括

- postclaim の `merge-message` は、valid で保持された file を全 invocation に渡せば特定可能性を閉じられる。
- brief は production 使用箇所の件数を 8 ではなく 9 とし、`AI-Agent:` 検査を exact 1 行と一般化しない。
- P1 は暫定 mitigation、恒久策としては必須化＋claim 前 snapshot の P2 を推奨する。
- D253 の FIFO、D486 の肯定的 retry 境界、owned-path-overlap は不変とする。
- 残る不確実性は、full provenance の merge-context failure と運用規約の実施 enforcement である。
