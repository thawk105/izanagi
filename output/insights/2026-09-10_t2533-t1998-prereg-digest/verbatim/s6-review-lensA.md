## 前提と読んだ資料

指定された一次資料 6 件はすべて読めた。

- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s4-adjudication.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/AUTHORITATIVE-VALUES.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s5-author.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s3-lensA.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s3-lensB.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1790.md`

指定 worktree の `main..HEAD`、commit `3b64ffd7b` / `d424c1fa0` と、対象 3 ファイルを全文確認した。親 checkout・他 worktree は読んでいない。pytest は実走せず、親報告の 69 passed を再現したとは主張しない。

文書の sha256 は working tree、`3b64ffd7b` blob、`d424c1fa0` blob のすべてで `464e3af5…719c`。§4/§5 の job body、gitlink、環境契約、両 source digest は値の正本と一致し、§6 も現行 module 定数・計算と食い違っていない。

## 所見

1. **重大度: must-fix** — artifact identity を測定時点 blob ではなく現行文書から作っている。段4裁定は「成果物 commit の blob から導いた identity」との exact 一致を要求する (`s4-adjudication.md:106-109`) が、実装は current bytes から `documented` を作り、measurement blob は後から hash するだけで parse しない。[t1998_stock_inline_pair.py:1294–1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:1294)。初版では 2 SHA が同じなので 69 passed では区別不能。未被覆入力は、測定版 `Bm` の SHA=`Hm`・identity=`Im`、現行版 `Bc` の SHA=`Hc`・identity=`Ic` (`Im != Ic`)、定数を `MEASUREMENT=Hm` / `CURRENT=Hc`、artifact commit は `Bm` を持つ一方 artifact と引数を `Ic` で相互整合させたもの。この実装は 3 gate をすべて通すが、測定時点文書 `Bm` は `Ic` を登録していない。  
   **放置時の影響:** D1790 が想定する二版分離後、測定時点の事前登録に存在しない identity の成果物を受理し、逆に正しい旧 identity を拒否しうる。

2. **重大度: must-fix** — `git -C repo_root` は designated repository を固定していない。`subprocess.run` が環境をそのまま継承するため、`GIT_DIR`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`、replace refs により `git show` / `merge-base` の参照先を変えられる。[t1998_stock_inline_pair.py:347–384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:347)。未被覆入力は、`GIT_DIR=/alternate/.git` とし、その repo に canonical 文書を持つ commit `C` を置き、result/reservation/lock/preregistered の `repository_commit=C` と他 identity を正本値で相互整合させるもの。指定 worktree に `C` が存在しなくても `git show C:docs/...` は alternate repo から成功し、consumer は受理する。loader の ancestry も alternate `HEAD` に対して判定される。  
   **放置時の影響:** 成果物の `repository_commit` が指定 repository の commit でなくても測定時点文書との束縛を通り、参照 provenance が別 repo へ差し替わる。

3. **重大度: should-fix** — current SHA gate を単独で殺す永続テストがない。追加 loader 負例は working bytes と blob が異なるため [t1998_stock_inline_pair.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:387) で先に落ち、current pin 比較 `:389-391` の削除を検出しない。[test_t1998_stock_inline_pair.py:702–741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:702)。未被覆入力は「canonical spec と identity は維持し、末尾空白だけ加えた文書を HEAD に commit し、working bytes も同じにした一時 repo」。blob equality と parser は通り、現実装では current SHA だけが拒否する。consumer 側も「working document の散文だけ drift、artifact commit blob は初版」の入力が未被覆である。  
   **放置時の影響:** current pin 比較を消す回帰が焦点走を通過し、現行解析文書の受理集合が同じ spec を含む任意 bytes へ広がる。

4. **重大度: nit** — fixture の identity 実値化自体はテストを甘くしていないが、`repository_commit` と contract-loader binding は実行時 `HEAD` から自己整合的に生成され、履歴依存が残る。[test_t1998_stock_inline_pair.py:63–68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:63)、[同:145–187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:145)。`test_measurement_commit_without_preregistration_blob_is_rejected` は、将来 HEAD の contract-loader bytes が変わり「文書導入前かつ同一 bytes」の祖先が消えると consumer 到達前に `AssertionError` になる。`test_load_preregistration_returns_document_identity_from_real_head` は引数も期待値も HEAD なので、現 HEAD `d424c1fa0` に対し同じ文書 blob を持つ祖先 `3b64ffd7b` を渡すケースを検査しない。positive/inconclusive の `test_real_admission_and_receipts_accept_only_the_fixed_pair`、`test_baseline_and_target_source_identities_may_normally_differ`、`test_typed_trace_disabled_define_is_normalized`、`test_unstable_arm_is_inconclusive` も、HEAD の文書 blob が measurement pin と違えば落ち、同じなら後続 commit でも通る。  
   **放置時の影響:** production の値・受理集合は変わらないが、無関係な HEAD/history の移動で焦点テストが通過・準備失敗し、検査結果の参照安定性が変わる。

## 受理集合の変化

緩んだ経路はない。production 差分は既存条件を削除・変更せず、既存 artifact 検査の後へ条件を conjunction として追加している。したがって、通常の Git 参照下では変更後に受理される入力は必ず変更前にも受理されていた。fixture の synthetic 値から実値への交換も production の受理集合を広げない。

| 入力 | 変更前 | 変更後 |
|---|---|---|
| 正本 identity、commit の文書 blob=`464e3af5…` | 受理 | 受理 |
| artifact と引数だけを coherent な別 gitlink/env/script/source にする | 受理 | `preregistration-identity-mismatch` |
| 正本 identity だが commit に文書がない／別 SHA | 受理 | `measurement-preregistration-sha-mismatch` |
| working 文書の散文・CRLF・BOM・末尾空白だけ drift | 受理 | `current-preregistration-sha-mismatch` |
| 旧 job body、誤 target digest `6454d9f3…` を artifact と引数の両方に置く | 受理 | 文書 identity mismatch |
| `GIT_DIR` 等で別 repo の canonical blob を参照させる | 受理 | 依然受理。所見2の未閉鎖経路 |

既存負例の test body は変更されていない。fixture の実値は新 gate を通る値なので、従来の単独不正は従来位置で拒否される。特に `test_launcher_script_digest_is_bound_to_preregistration` は [test:627–640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:627) のままで、reservation 比較 [consumer:1126–1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:1126) が新 gate `:1272` より先に発火し、`launcher-script-identity-mismatch` / `reservation.binding.script_sha256` を維持する。

## 単独では発火しない検査

追加された 3 gate 自体に、初版の 2 定数同値を理由とする冗長性はない。

- current SHA は、working 文書だけを trailing-space drift させ、measurement commit の blob を初版のままにすれば単独で発火する。
- measurement SHA は、working 文書を初版のまま、artifact commit を文書導入前または別 blob の commit にすれば単独で発火する。既存の追加負例もこの形である。
- document identity は、両文書 SHA を初版のまま、artifact と引数を coherent な alternate gitlink 等へ変えれば単独で発火する。

したがって `MEASUREMENT_TIME_PREREGISTRATION_SHA256 == CURRENT_PREREGISTRATION_SHA256` でも、比較対象 bytes が「artifact commit の blob」と「現在の working file」で異なるため、片方は他方を含意しない。これは実装誤りではない。

一方、parser の構造拒否は public 経路では current whole-file SHA に含意される。pinned document 自体が valid なので、duplicate key、field 閉集合、hex、schema、`preregistration.current.spec` の parse-error 分岐は、直接 `_parse_preregistration` を呼ぶか SHA 衝突がない限り単独では発火しない。これは exact whole-document pin の帰結であり、受理集合の穴ではない。

parser 単体では次の入力を受理する。

- canonical 文書の先頭に UTF-8 BOMを置く。
- LF を CRLF に置換する。
- marker/fence 行の末尾に space/tab を足す。
- block 外へ任意の prose・末尾空白を足す。
- marker を行頭でなく、別文字列の途中に置く。

いずれも正規表現が非 anchor で、CRLF・行末空白を明示許容するためである。ただし public consumer/loader では whole-file SHA が先に拒否する。本文へ exact marker をもう一度書く入力、exact marker を使った入れ子 block は `text.count != 1` で拒否される。duplicate key、余剰/欠落 field、大小文字・長さの違う hex に素通りは見つからなかった。

`_reject` は常に `T1998PairRejected` を raise するため、catch 後の `current_preregistration`、`documented`、`measurement_preregistration` が未定義のまま使われる通常入力経路はない。[t1998_stock_inline_pair.py:474–483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:474)。Git の非ゼロ終了もすべて拒否され、argv 配列と lowercase hex40 により shell/revision 注入はない。locale は捨てられる stderr の文面しか変えない。成功時参照を変えられる `GIT_*` 環境だけが所見2の実害である。

## 総括

通常環境で旧受理集合を緩めた差分はなく、既存 launcher 拒否 provenance も維持されている。  
3 gate は初版で同じ SHA 値でも比較対象が異なり、相互に冗長ではない。  
must-fix は、identity の版を current 文書から取っている点と、Git の参照 repository が環境で差し替わる点。  
current SHA の単独負例は焦点テストから欠落しており、parser の厳密性も whole-file pin の内側では単独発火しない。  
文書の固定値と §6 は値の正本・module 実装に一致している。  
pytest は本レビューでは実走していない。