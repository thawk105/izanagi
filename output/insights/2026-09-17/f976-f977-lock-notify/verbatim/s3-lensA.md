## gate protocol の deadlock / livelock

指定資料はすべて読めた。以下は静的検査であり、実装・実 flock の実行検証は行っていない。`conftest.py` は `orchestrator/tests/conftest.py`、`s1-brief.md`・`s2-plan.md` は指定された親の資料を指す。

**所見**: 昇降格を gate から除外しても、legacy/common をまたぐ三者循環が新しく成立する。
**分類**: plausible
**根拠**: `s2-plan.md:82` は「新しい循環を作らない」とするが、`conftest.py:1428` の legacy 取得と `:1441` の common 取得の間で reader が停止でき、`:1356` の入れ子昇格は既存 common SH を保持したまま legacy EX を要求する。
**影響**: gate がなければ進める reader が途中で止まり、昇格と writer が deadline まで相互待ちして受入を赤にする。
**推奨**: plan v2 の無循環の主張を撤回し、次の三者シナリオを実 flock の必須反例に追加して、解消する取得・再入手順を示す。

`Lα/Lβ` は異なる worktree の legacy main、`C` は共有 common main、`G(C)` はその gate。矢印は「左が右の解放を待つ」。

```text
A: Lα SH + C SH を保持する既存 reader
W: Lβ EX + G(C) EX を取得し、C EX を待つ
B: Lα SH を取得し、G(C) SH を待つ
A: 入れ子 writer として Lα EX への昇格を開始

A ── Lα EX / B の SH ──→ B
B ── G(C) SH / W の EX → W
W ── C EX / A の SH ───→ A
```

A の legacy conversion が元の SH を失っても、B の legacy SH と A の common SH は残るので循環は消えない。gate がなければ B は common SH へ進み、終了できる。これは既存の「複数 reader が同時昇格する」問題とは別である。`parent` だけで成立し、`ccbench` に置き換えても成立する。

**所見**: fresh 取得の順序だけでは、process 全体の RLock を含む待ちグラフの無循環性を証明できない。
**分類**: real
**根拠**: `conftest.py:1055` は単一の `Condition(threading.RLock())`、`:1328`〜`:1364` はそれを保持して flock 待ちし、解放側も `:1377` の `with condition:` を必要とする。
**影響**: 既存 holder の解放を別 thread の flock 待ちが妨げ、gate 導入前から deadline 停止する組合せがある。
**推奨**: plan v2 の証明対象を明記し、次の既存循環を「gate で解消した」と扱わない。

```text
同 process の T1: ccbench SH を保持
別 process の W: parent EX を保持し、ccbench EX を待つ
同 process の T2: global RLock Q を保持し、parent SH を待つ
T1: ccbench の解放に Q が必要

T1 ─Q→ T2 ─parent→ W ─ccbench→ T1
```

取得種別ごとの境界は次のとおり。

| 組合せ | 待ちグラフの検算 |
|---|---|
| fresh のみ・単 thread・入れ子なし | `G(P,L) → M(P,L) → G(P,C) → M(P,C) → G(S,L) → M(S,L) → G(S,C) → M(S,C)` の順序で説明できる。SH/EX は競合辺の有無を変える |
| 同 thread・同 mode 再入 | `holders` の加算だけなら新しい flock 待ち辺はない |
| 昇格にも gate を要求 | `既存 SH holder → gate 保持 writer → 既存 SH holder` の直接循環 |
| 昇格は gate を迂回 | 直接循環は避けるが、上記 legacy/common 三者循環は残る |
| 降格にも gate を要求 | EX holder と、その main EX を待つ gate holder が直接循環する |
| 降格は gate を迂回 | gate による直接循環はないが、conversion の非 atomic 性は別問題 |
| 複数 thread | resource/key の順序とは別に global RLock の辺が加わる |

**所見**: gate の即時解放案も保持継続案も、writer 全員の進捗や reader の飢餓回避を保証しない。
**分類**: real
**根拠**: `s2-plan.md:45`〜`:50` の SH/EX gate は、`conftest.py:1267` の `LOCK_NB` と `:1280` の polling を使い、待機 writer の登録や取得順を持たない。
**影響**: reader が gate SH を重ねれば writer が gate で期限切れになり、writer が連続して gate EX を取れば reader や別 writer が期限切れになり得る。
**推奨**: 「gate EX 取得後の流入抑止」と「待機 writer の優先」を区別し、裁定項33との差を未解決事項として残す。

即時解放案では次 writer が main 待ち中に gate を占有できるが、誰が次に取るかは保証されない。writer が本体終了まで gate を保持しても公平性は得られない。reader まで本体終了まで保持すれば、元の reader overlap による writer 飢餓を gate に移す。deadline があるため、ここでいう無限待ちは実運用では期限切れとして現れる。

## fails-closed の保存

**所見**: 共通 deadline の範囲は一回の resource 取得であり、全 resource・RLock 待ち・降格まで含む245秒上限ではない。
**分類**: real
**根拠**: `conftest.py:1426` の deadline は legacy/common に共有されるが、`:1463` は resource ごとに `_real_repo_file_lock` を呼び、`:1402` は降格用に再起算し、`:1267` は期限確認前に flock を試す。
**影響**: 「全取得が245秒以内」「期限後には成功しない」という検査を置くと、現契約と異なる期待を固定する。
**推奨**: plan v2 では「一回の `_real_repo_file_lock` の四段で待機予算を共有」と限定し、global RLock 待ちと別 resource の予算を混同しない。

**所見**: gate open を既存の例外処理の外へ置くと、main fd と空 state が漏れる余地がある。
**分類**: plausible
**根拠**: `conftest.py:1346`〜`:1349` は main fd/state を先に作り、削除・close・`notify_all()` は `:1365`〜`:1369` の `except BaseException` に限られる。`s2-plan.md:69` は gate fd の finally を指定するが、gate open の配置までは確定していない。
**影響**: gate の owner/mode 拒否、open 失敗、割込み時に process manager が残留して後続取得を壊す。
**推奨**: gate open・登録・待ち・解放を既存 cleanup の保護範囲内に置くことを明記し、timeout だけでなく open 拒否時も fd/state/通知を検査する。

同じ `_real_repo_flock_until` をそのまま使えば、gate timeout も `conftest.py:1275` の `RuntimeError` と `real-repo lock deadline exceeded; fails-closed:` を使う。実装後は gate/main 両 timeout でこれを確認する必要がある。

**所見**: gate fd が取得区間だけの寿命でも、fork 子が継承した fd を保持すれば親の close だけでは gate が解放されない。
**分類**: plausible
**根拠**: `s2-plan.md:69` の「close により gate を解放する」に対し、`conftest.py:1329` の reset は子が再び manager を呼ぶまで実行されない。fork した fd は同じ open file description を共有する。[flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html)
**影響**: 子が reset を呼ばず生存すると、親が本体へ進んだ後も gate EX が残り、後続を期限切れにできる。
**推奨**: plan v2 に「取得中 fork、子は manager を呼ばず待機」のケースを追加する。親の通常解放と、親の lock を解除してはいけない子の reset を分けて設計する。

## 受理集合の向き

**所見**: 既存 fd の conversion 失敗後も外側 reader の保護が残る、という前提は現コードからは証明できない。
**分類**: plausible
**根拠**: `conftest.py:1365` は `created == False` の失敗時に元の SH を復元せず、`state.mode` と `holders` をそのまま残す。flock の conversion は非 atomic で、元 lock を失って失敗し得る。[flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html)
**影響**: common SH→EX の失敗を外側が捕捉して継続すると、state は read のまま実際の common SH がなく、別 worktree writer と reader が同時に処理する恐れがある。
**推奨**: gate 導入前からの問題として区別し、conversion 失敗後の外側 context の契約と実 flock 検査を plan v2 に追加する。「同じ fd」を排他維持の証拠にしない。

fresh 取得については main SH/EX 成功後だけ body に進み、既存 key と main の安全検査を残す限り、gate は待ち条件を追加する方向である。`s2-plan.md:37` は `_open_real_repo_lock(gate_path)` の再利用を指定しており、安全検査を省く案ではない。別 process・別 worktree の common key、旧 session 向け legacy key を外す変更も指定されていない。ただし、この確認を上記 conversion 失敗や fork の全ケースへ一般化できない。

## 模擬と実の差

**所見**: N1 は gate 取得後の流入抑止だけを検査し、裁定が要求する writer 待機開始後の優先を検査しない。
**分類**: real
**根拠**: `s2-plan.md:95` は「writer が main EX の最初の EAGAIN」を同期点にするため、変更後はその時点ですでに writer が gate EX を取得している。既存模擬も `test_real_repo_serialization.py:2086` で fd を無視する writer 専用モデルである。
**影響**: N1 と変更後の `[6.0, 6.0]` が通っても、writer が gate で飢餓する実装を受理する。
**推奨**: N1 の検証対象を限定して記載し、gate 待機中の reader 流入と前節の三者循環を別ケースにする。模擬の時刻一致を kernel の公平性の証拠にしない。

**所見**: N1 の「約1秒」実時間 deadline は、handshake があっても高負荷下の正例を不安定にする。
**分類**: plausible
**根拠**: `s2-plan.md:95`〜`:100` では writer の待機予算内に、通知受信、B の起動後処理、gate 競合通知、A 解放、writer の再スケジュールが必要になる。
**影響**: protocol が正しくても48 worker の負荷で writer が先に期限切れになり、F976 対策のテスト自体が非帰属赤になる。
**推奨**: production の245秒は変えず、テストを競合順序の検査と deadline 計算の検査に分け、実時間の短さを成功条件にしない。

gate 無しの負例は、**次 reader の取得確認まで前 reader を解放しない**条件を守れば、実 flock で常時 SH holder が存在するため成立する。これは単なる sleep のタイミング頼みではない。一方、正例の1秒以内の進捗は別問題である。また、固定 fd の模擬は open file description・fork・conversion を表現していないため、それらの保証には使えない。

## rolled-back の述語

`B` は報告用 `main_before`、`L` は直前の `locked_main`、`T` は `landing_tip`、`R` は保存済み `origin.rollback_ref`、`F` は fold commit。各文字は有効な SHA とする。

| 経路・根拠 | status | main_before | main_after | wave_tip | P3 |
|---|---|---:|---:|---:|---|
| 通常 fold 失敗・rollback 成功 `dev_wave_land.py:5585`, `:4675` | fold-failed | L | L | T | 真：L≠T |
| recovery shape A の fold 失敗・rollback 成功 `:5240`, `:5257` | fold-failed | T | R | T | **偽：R≠T なら before≠after、R=T なら tip=after** |
| already-landed 側 fold 失敗・rollback 成功 `:5510`, `:5519` | fold-failed | B | T | T | 偽 |
| candidate planning 失敗 `:5287` | fold-failed | B | L | T | B=L≠T のとき真 |
| declared no-fold 拒否 `:5458` | fold-failed | B | L | T | B=L≠T のとき真 |
| already-landed 側 preflight 失敗 `:5500` | fold-failed | B | T | T | 偽 |
| merge 前 preflight 失敗 `:5557` | fold-failed | B | L | T | B=L≠T のとき真 |
| `main_after` 欠落の防御経路 `:4539` | fold-failed | 呼出元値 | None | T | 偽 |
| rollback 不完全 `:4675` | fold-rollback-failed | 呼出元値 | 観測 HEAD / None | T | 偽 |
| 通常 merge 成功・fold noop `:4868`, `:5582` | landed | L | T | T | 偽 |
| fold 成功 `:4632` | landed | 呼出元値 | F | T | 偽 |
| already-landed・fold noop `:5483` | already-landed | B | T | T | 偽 |

**所見**: P3 は recovery 経路で実際に merge を巻き戻した結果を必ず拒否する。
**分類**: real
**根拠**: `dev_wave_land.py:5006` は開始時 main を `main_before` にし、shape A は `:5199` の分岐を通過して `locked_main == landing_tip`、`:5257` は `rollback_ref=origin.rollback_ref` を渡す。既存 `test_dev_wave_land.py:6401` も `:6443`〜`:6444` で fold-failed と旧 base への復帰を期待している。
**影響**: rollback 通知が必要な実経路が無通知のまま残り、plan の経路表もこれを見落とす。
**推奨**: plan v2 に recovery 行と JSON 正例を追加し、P3 を改訂する。既存 field なら `before==tip` の recovery 形を受理候補として全経路で検算し、親 P3 との変更点を明示する。

**所見**: `fold-rollback-failed` は main ref が戻っていない場合だけを意味しない。
**分類**: real
**根拠**: `dev_wave_land.py:4379` の ref CAS 成功後でも、`:4387` の read-tree、`:4393` の復元、`:4400` 以降の journal 処理が失敗すると、`:4677` は `fold-rollback-failed` を返す。
**影響**: main_after が merge 前 SHA でも rc=28 になるため、SHA の等式だけに述語を置き換えると通知拒否契約を破る。
**推奨**: status 条件を必須のまま保持し、`fold-rollback-failed / before==after / tip!=after` の負例を具体的に追加する。

`current != expected_tip` でも、その親が `expected_tip` なら `:4374` の拒否には入らない。CAS と後処理が成功すれば `main_after` は **fold commit の親ではなく `rollback_ref`** になる。通常経路では L、already-landed 経路では T、recovery では R である。

**所見**: 固定文の本文は P3 の不動ケースに対応しているが、ヘッダーの `unlanded=` と現在形は JSON が証明する範囲を超える。
**分類**: real
**根拠**: `s2-plan.md:185` は `unlanded=<wave_tip>`、`:186` は「main は記載の SHA にあり」とする一方、`wave_land_window.py:608` は保存 JSON を読むだけで、tip の祖先関係も通知時点の main も検査しない。
**影響**: tip 不一致を未取り込みと読み違えたり、通知生成前に進んだ main を古い SHA にあると誤認したりする。
**推奨**: `unlanded=` を `wave-tip=` にし、「この land 結果の観測時点では main=…、wave tip とは異なる」とする。`rolled-back` kind は不動ケースも含む結果通知であることを明記する。

## 親 brief 自身の点検

**所見**: P1 の「process 内 writer 優先は不要」は、RLock 保持の事実からは導けない。
**分類**: real
**根拠**: `s1-brief.md:22`〜`:23` に対し、`conftest.py:1342` は非互換 thread 待ちで `condition.wait()` を呼び、`:1308` は既存 holder が reader だけなら新規 reader を許す。
**影響**: 同 process の writer が待っていても reader が増え続け、別 process の gate EX holder も、その共有 main SH の消滅を待ち続ける。
**推奨**: P1 を「kernel flock 待ち中の RLock 保持区間」に限定し、同 process の互換性待ち・参照追加・入れ子昇格は別の保証対象とする。

**所見**: brief の P3 にある「merge 前失敗も同形で通る」は条件付きであり、行番号補正にも未反映箇所がある。
**分類**: real
**根拠**: `s1-brief.md:27` に対し `dev_wave_land.py:5411` は `locked_main` だけを更新するため B≠L があり得る。また plan の `:4669` は現在 `pass` で、失敗結果の生成は `:4675`、deadline 算出は plan の `:1429` ではなく `conftest.py:1426`、降格呼出しは `:1397`。
**影響**: P3 の説明のずれは通知対象の誤認につながり、行番号だけのずれは nit。
**推奨**: P3 を B=L≠T の条件付き説明へ修正し、plan v2 の参照を現物へ合わせる。brief の checker pin `467` と fixture `55` は現物と一致している。

## 裁定パッケージ候補

**所見**: 裁定項33の「待機 writer がいる間は新規 reader を待たせる」と、提案された gate EX holder だけへの優先には仕様差がある。
**分類**: real
**根拠**: `rulings-verbatim.md:8` の決定に対し、`s2-plan.md:311` 自身が gate 取得前の優先を保証しないと記載する。
**影響**: 現案のテストが通っても、裁定どおりの writer 優先を実現したとは判定できない。
**推奨**: 「保証を gate EX 取得後へ限定する」か「待機開始を扱う取得方式まで scope を広げる」かを裁定候補として分離する。新しい gate・待機台帳・一般化した取得管理を must-fix に紛れ込ませない。

deadline 延長・同時実行数制限は、本レビューの対処案には含めない。

## 総括

plan v2 で先に解消すべき中心点は、**legacy/common をまたぐ新しい三者循環**と、**recovery rollback の通知漏れ**である。

加えて、gate の fork 継承時の解放、open 失敗時の cleanup、短すぎる実時間テストを具体化する必要がある。P1 と「gate を通さないから無循環」という説明は、そのまま採用できない。

ファイル変更・git 状態変更・pytest 実行は行っていない。`plausible` とした実行スケジュールは未実測であり、緑とは判定していない。
