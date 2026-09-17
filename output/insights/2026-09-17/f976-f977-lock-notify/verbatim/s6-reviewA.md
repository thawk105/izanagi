## 契約との一致

**所見**: 【must-fix 1】昇格時の gate open 拒否が、外側 reader の SH を失わせたまま `mode="read"` を残す新しい失敗経路になっている。
**分類**: real
**根拠**: `orchestrator/tests/conftest.py:1364` の `fcntl.flock(state.fd, fcntl.LOCK_UN)` が `:1366` の `_open_real_repo_lock(gate_path)` より先にあり、`:1390` の cleanup は `if created:` に限定されるため、既存 state の mode・holders は残る。
**影響**: 外側 reader が例外を捕捉して継続すると、以前は SH で排他されていた別 process の writer と同時に資源へ入れる。
**推奨**: gate の open・登録を SH 解放より先に行い、その後の UN・gate 待ち・main 待ちを gate cleanup の `try/finally` 内へ置く；common key の open 拒否後も外側 SH が保持される負例を追加する。

これは既存の「EX 変換を試して失敗した後の SH 喪失」と区別すべきです。今回の経路では、main EX の試行に到達する前に open の安全検査だけで SH を失います。`s5-a1.md` の cleanup テスト報告は fresh writer の検査であり、この昇格経路を覆っていません。

## reader 検査の配置

**所見**: common-dir resolver が legacy 排他の外へ移り、旧来の resolver 保護条件を production の入口では維持できていない。
**分類**: real
**根拠**: `orchestrator/tests/conftest.py:1495` の tuple は `:1497` の `_real_repo_lock_path(resource)` を最初の gate 試行前に評価する一方、`orchestrator/tests/test_real_repo_serialization.py:2610` は「legacy EX holder 中に common-dir resolver が呼ばれた」を拒否しているが、呼出対象は `_real_repo_file_lock` に留まる。
**影響**: nit；resolver 自体の排他範囲は縮むが、本体が誤った common key で入場する経路は確認できない。
**推奨**: この例外を docs に明記し、既存テストの保証を production 入口全体へ一般化しない；旧 writer 保持中の `_real_repo_locks` を対象に resolver の挙動を検査する。

**所見**: 排他外の resolver が writer による一時的な Git 管理情報の変化を拾い、従来は待機後に成功した reader を拒否する可能性がある。
**分類**: plausible
**根拠**: `orchestrator/tests/conftest.py:1130` 以降は `rev-parse` の非零終了・不正出力・common-dir の解決失敗を即時例外にし、`:1497` の事前解決には legacy main の保護がない。
**影響**: 該当する書換えがあれば受入の偽赤が増えるが、このレビューでは実際の writer 経路との組合せを未確認。
**推奨**: must-fix には数えず、writer の変更対象と resolver の読取対象が交差する具体例を確認する。

## 循環の再検算

**所見**: s3-a の三者循環を、そのまま今回の実装の新規 deadlock として扱うことはできない。
**分類**: refuted
**根拠**: `orchestrator/tests/conftest.py:1491` の `if not _REAL_REPO_PROCESS_LOCKS:` と `:1512` 以降の main 取得により、当該 reader は common gate を待つ時点で legacy main を保持しない。
**影響**: nit；旧反例の `A → B → W → A` に必要な「B の legacy SH」が存在せず、その反例では受入の赤を説明できない。
**推奨**: 旧反例は解消済みとして扱い、既存の昇格・順序逆転による循環と分ける。

残る待ちグラフの境界は次のとおりです。

- **昇格と fresh writer**：A が common SH を保持したまま legacy SH を落とし、W が legacy EX を取得すると、`A → legacy/W → common/A` が成立し得ます。これは旧実装の変換失敗でも成立する**既存**の循環です。
- **parent→ccbench**：fresh 取得の順序は維持されています。外側 ccbench 保持から内側 parent を要求する逆順の入れ子は、`A → parent/W → ccbench/A` という**既存**の循環を作れます。
- **同 process の入れ子 reader**：保持 state があるため gate 検査を迂回し、新しい gate 待ち辺を追加しません。
- **reader 事前検査中の Condition 保持**：検査開始時の state は空で、Condition を保持したままなので、manager が管理する同 process の holder の解放を新たに妨げる循環は構成できません。既存 main 取得中の RLock 待ち問題とは区別します。

writer が gate を待つ辺は、gate holder が待つ同 key の main への辺として追跡できます。検査した組合せでは、既存の main 間循環とは別の新しい循環は特定できませんでした。実 flock による再現検査は未実施です。

## fails-closed の保存

**所見**: 「共有 deadline」を、期限到達後の取得成功も禁止する厳密な時刻上限と読むことはできない。
**分類**: refuted
**根拠**: `orchestrator/tests/conftest.py:1267` 以降は NB flock を先に試し、競合した場合だけ期限を判定する；`:1517` の `timeout_s=max(0.0, ...)` もゼロ予算での試行を許す。
**影響**: nit；期限後の即時取得を誤って退行と判定するテストは、既存契約と異なる赤を作る。
**推奨**: 待機予算の共有として評価し、ゼロ予算でも NB 試行があることを維持する。

gate timeout は同じ `_real_repo_flock_until` を使うため、`RuntimeError`・`real-repo lock deadline exceeded; fails-closed:`・gate の `path=`・`holders=` の形式を引き継ぎます。検査段の残予算は最初の resource に渡され、２番目の resource は別予算です。

通常の成功・gate/main timeout・待機中の `KeyboardInterrupt` は gate の UN/close を通ります。fresh の open 拒否は外側 cleanup を通ります。ここから「昇格失敗後も外側 reader が保護される」とは結論できず、must-fix 1 は別に残ります。

## 排他の向き

**所見**: must-fix 1 は管理状態だけの不整合ではなく、移行期の別 worktree writer に対する排他を実際に弱める。
**分類**: real
**根拠**: `orchestrator/tests/conftest.py:1364` で common SH を解放して `:1366` が拒否された場合、legacy 側の巻戻しは `:1420` の降格だけで、common SH の復元はない。
**影響**: 外側 A が例外捕捉後に読む間、gate を知らない旧コードの sibling worktree W は別 legacy key と共有 common EX を取得して書ける。
**推奨**: must-fix 1 と同じ修正・負例で閉じる；独立した２件目には数えない。

成功する昇格での `UN → gate → EX` の隙間は、他 writer が先行できる順序変更です。新しい writer 本体は main EX 成功後にしか入らないため、その隙間だけを排他破れとは数えません。失敗後に外側 reader が続行する問題とは別です。

## rolled-back の述語

追加指摘なし。静的な経路検算は以下です。`L` は取得時 main、`T` は wave tip、`R` は recovery の rollback ref です。

| 経路 | 結果の主要値 | message rc |
|---|---|---:|
| 通常 rollback 成功 | `fold-failed`, after=L≠T | 0 |
| recovery shape A | `fold-failed`, before=T, after=R≠T | 0 |
| already-landed 側 rollback 成功 | `fold-failed`, after=T | 3 |
| planning・no-fold・merge 前 preflight 失敗 | `fold-failed`, after=L≠T | 0 |
| after=None | `fold-failed`, after=None | 3 |
| rollback 不完全 | `fold-rollback-failed` | 3 |
| landed / already-landed | 成功 status | 3 |

根拠は `tools/dev_wave_land.py:4541`、`:4677`、`:5240`、`:5257`、`:5289`、`:5460`、`:5502`、`:5559` と、`tools/wave_land_window.py:618`〜`:628` です。

`main_before` を見ないことで、取得前後に main が進んだ merge 前失敗も通知対象になります。本文が述べる「この land 結果の after と tip が異なる」は真であり、巻戻しが実行されたという追加主張はありません。固定文は AST から抽出して **661 bytes** と再計算しました。`_ADVISORY` の差分はありません。

## docs との一致

**所見**: README の「writer の飢餓を防ぐ」は、実装と親の裁定パッケージが認める保証範囲より強い。
**分類**: real
**根拠**: `orchestrator/tests/README.md:258` は「writer の飢餓 (F976) は…防ぐ」と断言するが、`orchestrator/tests/conftest.py:1491` は既存 holder の reader を除外し、gate 自体も NB polling である。
**影響**: nit；保証されない進捗を docs 上で保証したことになる。
**推奨**: 「gate EX 保持中に fresh reader の事前検査を待たせ、writer の飢餓を抑制する」程度へ限定する。

**所見**: README の common-dir 解決順の説明に、追加された事前解決の例外が記載されていない。
**分類**: real
**根拠**: `orchestrator/tests/README.md:254` は「worktree-root key を先に取得してから Git common-dir を解決」とするが、`orchestrator/tests/conftest.py:1497` は main 取得前に解決する。
**影響**: nit。
**推奨**: 本体用 key は legacy 取得後に再解決する一方、fresh reader の gate 検査用には事前解決する旨を追記する。

## 裁定パッケージ候補

**所見**: gate 取得前からの writer 優先と、昇格失敗後の外側 reader の安全な続行は、今回の局所実装では保証されない。
**分類**: real
**根拠**: `orchestrator/tests/conftest.py:1267` 以降は待機順を管理しない polling、`:1390` は既存 state の取得失敗を復元しない；`s4-ruling.md` の裁定パッケージ１〜３もこれらを留保している。
**影響**: writer の期限切れと、変換失敗を捕捉した外側 reader の無保護続行が残る。
**推奨**: 公平性・待機登録・state 毒化などは別裁定とする。ただし、新規 open 拒否経路を増やさない must-fix 1 はこの留保に含めない。

## 総括

**must-fix は１件、NO-GO。**

gate を安全に open してから SH を解放する順へ変更し、昇格中の common gate open 拒否後も外側 reader の排他が残ることを検査してください。

全指定資料と878行の差分を静的に確認しました。ファイル変更・git 状態変更・pytest 実行はしていません。author の実走報告を、このレビュー自身の実走結果とは扱っていません。
