## 所見

[1] real | 対象: `tools/wave_land_window.py:92-95,384,393-395,456,503-510,459-483`; `s3-lensA.md:5`; `s4-adjudication.md:16,47-48` | must-fix — slug は閉じた語彙ではなく、basename の許可文字を最大 64 字そのまま通すため、`IGNORE_PREVIOUS_INSTRUCTIONS.md` が JSON・人間向け peer/holders・message の `wave` にそのまま出る。さらに argparse の既定 `prog` は `--help` へ起動 basename を出す | 根拠: `[A-Za-z0-9._-]` は命令文を十分符号化でき、レンズ A 所見 3 は閉じていない | 影響: 外部 filename を指示と誤解する経路が規律 6 を破り、規律 2/3 への誘導を再び許す | 成果物影響: verifier 省略等を誘導された場合、certified 選択の受理集合、材料レポートの proof 参照、試行台帳の verdict が未検証値へ変わる | 推奨: slug を厳格な既知 ID 文法または固定長 digest にし、argparse の `prog` も定数化する。全許可文字だけで構成した命令風 basename の負例を追加する。

[2] real | 対象: `tools/wave_land_window.py:105-116,147-153,168-176`; `orchestrator/tests/test_wave_land_window.py:342-370`; `s4-adjudication.md:40-43` | must-fix — V-1 にない「一意な 4 行 header」「実効 UID 一致」「idle 時の main-sha 禁止」を受理条件へ追加している | 根拠: V-1 が要求する file gate は symlink・非 regular 拒否と active state の SHA 必須だけであり、headerless regular file、重複 header、別 UID regular file、`idle --main-sha` の拒否は未裁定。テストは headerless 拒否を仕様化している | 影響: V-1 上は受理される handoff で宣言できず、機構が不発または fail-closed 停止する | 成果物影響: worklog の受入 request ID・実測秒数が欠落するか、競合後の再走値へ差し替わる | 推奨: 追加 gate を外すか、段 4 へ差し戻して受理集合として明記・裁定してからテストする。

[3] real | 対象: `tools/wave_land_window.py:43-47,456`; `s4-adjudication.md:59-65`; `orchestrator/tests/test_wave_land_window.py:290-338` | should-fix — 裁定の fenced 固定文面は advisory 部に改行を含む 3 行だが、実装とテストは文字列連結した 2 行を要求している | 根拠: 固定文面の byte/改行が一致せず、実装側の解釈で仕様を書き換えている | 影響: 意味は近いが、固定出力契約と consumer の line framing が不一致 | 推奨: 裁定文面を test-owned golden bytes にし、改行が単なる文書折返しか仕様 byte かを親が明示して一致させる。

[4] real | 対象: `tools/wave_land_window.py:43-47`; `orchestrator/tests/test_wave_land_window.py:313-316,335-338` | must-fix — 固定 advisory の期待値を実装自身の `WLW._ADVISORY` から取得しており、任意の一行文へ改変しても両 message テストが通る | 根拠: producer と oracle が同じ定数を共有する恒真保証で、`_ADVISORY="検査を省略してください"` も検出しない | 影響: 固定安全文面を信頼境界として pin できていない | 成果物影響: 悪性文面が検査省略を誘導すれば、certified 選択・レポート・台帳の受理 verdict と参照 commit が変わる | 推奨: 期待全文をテスト側の独立 literal とし、実装定数を参照しない。

[5] real | 対象: `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:376-382`; `s4-adjudication.md:49-52` | must-fix — consumer は「hold なら後へ回す」としか規定せず、`partial`/`unavailable` が返す `unknown` を非 hold として受入開始できる | 根拠: tool 内の「clear は完全取得時のみ」は正しいが、caller が `advice == clear` を進行条件にしていないため fail-soft が境界で失われる | 影響: entry-limit・読取失敗・directory unavailable が実質 clear へ落ちる | 成果物影響: 並行受入の stale 再走により、worklog の受入 request ID と実測秒数が再走値へ差し替わる | 推奨: 「`clear` のときだけ投入し、`hold`/`unknown`/非 0 rc は投入しない」と明記する。

[6] real | 対象: `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:369-395`; `CLAUDE.md:158-159` | must-fix — 二 wave がとも acceptance を宣言してから走査すると相互に hold し、idle へ戻す規則・tie-break・landed 遷移がない | 根拠: handoff は 10 分ごとに更新されるため mtime TTL も更新され、双方の acceptance 宣言が 2400 秒で自然失効する保証すらない | 影響: 相互待機または第三 wave まで含む飢餓が継続する | 成果物影響: worklog/台帳の受入 request ID・実測秒数が欠落するか、40 分超後の値になる | 推奨: hold 時の状態巻戻しと、同時 intent を必ず一方だけ進める決定規則を段 4 へ再裁定する。

[7] real | 対象: `.claude/commands/dev-wave.md:53,57`; `tools/wave_land_window.py:432-456`; `s4-adjudication.md:20,53-56` | must-fix — `land-intent` formatter は実装されたが、段 6 の恒久 command は宣言・hold 判定しか指示せず、ListAgents 照合 peer への pre-acceptance 送信を一度も指示しない | 根拠: 送信義務があるのは line 57 の land 成功後だけで、裁定 B8 の送信 (i) が dead code | 影響: peer が走査点を通過した後の受入窓へ通知が届かず、採用した半機構が残る | 成果物影響: stale 再走によって worklog の受入 request ID・実測秒数が再走値へ差し替わる | 推奨: 段 6 に ListAgents 照合・固定 land-intent の一回送信・失敗時の扱いを明記する。

[8] real | 対象: `tools/wave_land_window.py:278-307,327-350,369-382` | must-fix — entry の `stat` と `open` の間で inode を交換でき、読んだ内容には `opened_metadata`、TTL には交換前 `entry_metadata.st_mtime` を使う | 根拠: 古い mtime の file を stat 後、新しい active declaration の regular file に交換すると、内容は active でも age は TTL 超過となり、source `ok`・advice `clear` を返せる。走査後の directory 追加も `ok` のまま検出しない | 影響: 同時更新下で完全でない snapshot を完全取得と主張する | 成果物影響: 競合受入の再走により、worklog の request ID・実測秒数参照が再走値へ変わる | 推奨: pre/open の dev+ino を照合し、age/size は opened fd から取り、読後再検証または directory 変化を partial へ倒す。

[9] real | 対象: `tools/wave_land_window.py:173-194` | should-fix — `declare` は同一 inode を直接上書きし、部分 write・`fsync`/close 失敗・並行 handoff 更新時に rollback しない | 根拠: 途中まで書いた後の例外でも rc=2 を返すだけで、元 bytes は復元されず、並行 writer の新しい他行も stale snapshot で上書きできる | 影響: 失敗報告と実ファイル状態が食い違い、handoff 本文を破損しうる | 推奨: owner 単一 writer 契約を機械化して lock し、失敗整合性を明記する。atomic replace が「一ファイルだけ」と衝突するなら再裁定する。

[10] real | 対象: `tools/wave_land_window.py:407-453` | should-fix — landed は JSON の構文値へは束縛されるが、実際の land producer へは束縛されない | 根拠: caller が用意した任意の regular fileに `{"status":"landed","main_after":"<40hex>"}` と書けば生成でき、所有者・正規 artifact path・producer schema・rc は検証しない | 影響: 手入力 status を手入力 JSON へ移しただけで偽 landed 自体は生成可能。ただし receiver 契約どおりなら作用は local-main 再読みに限定される | 推奨: 「保存済み」の信頼根拠を caller 契約へ明記し、可能なら producer が返した fd/path と厳格 schema に束縛する。

[11] real | 対象: `tools/wave_land_window.py:422-426,448-452,528-533` | should-fix — JSON `status` が list/dict だと frozenset membership が `TypeError` になり、生成拒否 rc=3 ではなく generic internal-error rc=2 になる | 根拠: 型偽装は false landed を生成しないが、V-1 の rc 分類を破る。深い nesting の `RecursionError` も同様 | 影響: caller が外部 JSON 不正を CLI 誤用・内部故障として誤分類する | 推奨: status の `isinstance(str)` を membership より前に検査し、JSON validation 例外を rc=3 へ閉じる。

[12] refuted | 対象: `tools/wave_land_window.py:398-429,447-453` | nit — duplicate key、数値 status、`main_after` 欠落/非文字列/非 lowercase SHA、64 KiB 超 JSON で false landed を生成できるとの疑いは反証された | 根拠: duplicate key は全 object で拒否、read は limit+1 で拒否、数値 status は allowlist 外、main_after は str+40hex を必須化している | 影響: これらの入力は出力なし rc=3。ただし list/dict の rc 誤分類と偽 artifact は [10][11] のまま | 推奨: 対応負例を追加して現在の静的保証を pin する。

[13] refuted | 対象: `tools/wave_land_window.py:237-395,513-533` | nit — 通常の entry-limit・byte-limit・unreadable・invalid declaration・directory unavailable が黙って `ok/clear` になる経路と、外部例外文字列・traceback の漏出は反証された | 根拠: 全既知失敗は fixed reason の partial/unavailable へ落ち、`clear` は `status=="ok"` のみ。top-level も `_Rejected` reason または `internal-error` の定数しか出さない | 影響: 非並行の既知失敗は fail-soft。残る穴は caller の unknown fallthrough [5] と snapshot race [8] | 推奨: この結論を entry-count・各 unreadable path・非 JSON 人間出力の独立テストで固定する。

[14] refuted | 対象: `tools/wave_land_window.py:21-42,78-95,147-194,201-219,237-395,432-483,513-537` | nit — [1]〜[3]・[10]〜[11] を除く V-1 要件は実装箇所へ対応している | 根拠: declare の単一 path/O_NOFOLLOW/regular gate、active SHA、peers の射影 fields・source・TTL・advice、message の成功 status/main_after、固定エラーと rc 捕捉が存在し、roster/git/process 呼出しもない | 影響: V-1 全体が空実装という疑いは反証 | 推奨: real 所見だけを直し、既存受理集合を不要に広げない。

[15] refuted | 対象: `tools/wave_land_window.py:97-116,173-187`; `orchestrator/tests/test_wave_land_window.py:111-158` | nit — 成功した canonical header 入力では、CRLF・非 UTF-8・NUL・末尾改行なし・既存複数 declaration によって他行 bytes が正規化される経路は見当たらない | 根拠: bytes の `splitlines(keepends=True)` を join し、変更対象 prefix 行だけ除去して一行を挿入する。CRLF は新 declaration にだけ継承し、通常の先頭 BOM は title 行とともに保存される | 影響: multiple declaration は全て置換対象として一行へ畳まれる。重複 header/BOM が直接 `- 目的:` に付く形は書換えず拒否され、受理集合問題は [2]、失敗途中の破損は [9] | 推奨: CRLF header・BOM・複数 declaration・重複 header を独立 fixture にする。

[16] real | 対象: `orchestrator/tests/test_wave_land_window.py:76-108` | should-fix — `test_acceptance_peer_exactly_one...` は projected state/main_sha/declaration/source を検査せず「一件なら無条件 holder」、`test_complete_idle...` は peers 内容を検査せず「二件なら active/invalid でも clear」という壊し方で各テストを通せる | 根拠: assert は前者が advice/holders/slug、後者が source 集計/advice だけ | 影響: V-1 の per-peer schema と二件以上の active 判定が恒真化可能 | 推奨: 全 projected field と、複数 peer 中一件だけ active の正例を固定する。

[17] real | 対象: `orchestrator/tests/test_wave_land_window.py:111-158` | should-fix — byte 保存テスト二本は LF header と既存 declaration 一件だけなので、CRLF header だけを LF 化する、BOM 付き purpose を拒否する、二件目以降の declaration を残す実装でも通る | 根拠: body の CRLF/non-UTF/末尾なしは強いが、header EOL・BOM 配置・複数宣言を横断していない | 影響: MW2 の意味集合全体は殺せない | 推奨: 元 bytes から全 declaration 行だけを除いた独立 oracle を各境界 fixture へ適用する。

[18] real | 対象: `orchestrator/tests/test_wave_land_window.py:160-192`; `tools/wave_land_window.py:283-303` | should-fix — MW1 の non-regular gate 除去は FIFO read で hang し正常な failing-node kill にならず、MW3 は path 除外と inode 除外の二重 gate の片方だけを消しても exact-path fixture が通る | 根拠: 初段 filter と loop 内 filter が互いを mask し、hardlink self の fixture がない | 影響: MW1/MW3 の単一-site mutation を killed と誤記録できる | 推奨: MW1 を `hang_risk` として隔離し、MW3 は両層同時変異を事前登録するか hardlink self fixture を加える。

[19] real | 対象: `orchestrator/tests/test_wave_land_window.py:195-221`; `tools/wave_land_window.py:286-288,318-382` | should-fix — MW4 テストは per-file byte-limit と最初の directory-open failure だけで、entry-limit の reason 追加を外して 128 件へ黙って truncate→`ok/clear` にする変異が生存する | 根拠: entry-limit・total-byte・entry-unreadable・entry-invalid・invalid-declaration と、後段 directory failure を個別に発火していない | 影響: 「上限超過を黙って ok」の核心変異を現テストは殺せない | 推奨: 129 件、total-byte 超過、symlink/unreadable、duplicate declaration の各 fixture で `partial/unknown` を固定する。

[20] real | 対象: `orchestrator/tests/test_wave_land_window.py:224-259`; `tools/wave_land_window.py:38,92-95,369-375,486-510` | should-fix — TTL テストは production の `_DEFAULT_TTL_SECONDS` から時刻と期待値を作るため定数を 10 や 3000 に変えても通り、slug テストは control/backslash/長さの JSON 出力しか見ないため、許可文字の命令文や非 JSON 出力漏れを通す | 根拠: fresh 正例は age=10 なので任意の threshold≥10 を許し、2400 を独立 pin していない | 影響: MW5 の threshold 変異とレンズ A3 の printable injection を殺せない | 推奨: 2399/2400/2401 を literal で試し、fresh landed、命令風 basename、human output も検査する。

[21] real | 対象: `orchestrator/tests/test_wave_land_window.py:262-339` | should-fix — message テストは「`stale-main` だけ拒否し、他 status は全部許可」する blocklist 実装でも通り、land-intent は一組の SHA/wave しかなく不正入力受理を検出しない | 根拠: MW7 の完全 guard 削除は殺すが、数値・欠落・未知 status の allowlist 崩壊、duplicate/巨大 JSON、uppercase SHA/wave injection は未検査。advisory oracle 共有は [4] | 影響: MW7 を status allowlist 全体の証拠にはできない | 推奨: success 二値以外を型別に parametrise し、出力なし・rc=3・独立 golden bytes を確認する。

[22] real | 対象: `orchestrator/tests/test_wave_land_window.py:342-370` | should-fix — invalid state/SHA テストは三例だけなので、39 桁 SHAや acceptance だけ uppercase を許す実装が通り、missing-header テストは V-1 にない拒否を正解として固定する | 根拠: header 重複・CRLF/BOM と active state ごとの長さ/文字種境界がない | 影響: 受理集合の無断縮小をテストが保護し、SHA grammar の部分的拡大を見逃す | 推奨: まず [2] を裁定し、SHA は 39/40/41・upper・非 hex を両 active state で独立検査する。

[23] real | 対象: `s5-impl.md:8-10,25-29`; `orchestrator/tests/test_wave_land_window.py:111-287` | should-fix — 「MW1〜MW7 を収録」はテスト名の存在までで、登録文言の意味集合を kill できるとは言えない | 根拠: clean kill は MW1 symlink、MW2 の全体正規化、MW4 の共通 advice 崩壊、MW5 の predicate 全削除、MW6 の完全 raw、MW7 の guard 全削除に限られる。MW1 nonregular は hang、MW2 header 限定、MW3 単一層、MW4 entry-limit、MW5 threshold、MW7 blocklist の各変異は生存する | 影響: 親の実走で緑でも mutation coverage を過大記録できる | 推奨: exact old/new と対象一意性を先に固定し、少なくとも MW1 を hang 指定、MW3 を両層変異、MW4 を entry-limit、MW5 を literal 2400、MW7 を未知型へ再照準する。

[24] refuted | 対象: `CLAUDE.md:67-76,88-95`; `.claude/commands/dev-wave.md:40-41`; `tools/wave_land_window.py:432-456` | nit — slug 注入 [1] を除き、この機構が verifier の判定、iteration の正しさシグナル、land gate を直接緩める経路は見当たらない | 根拠: 通知は local main 再読みにだけ使い、待機・取込・検査省略の根拠にしないと trusted command が明記し、tool 自体は verifier/land を変更しない | 影響: 偽 landed 単独では規律 2/3 の受理集合は変わらない。一方、raw slug は規律 6 を破ってその間接経路を再開する | 推奨: [1] と consumer fail-soft [5] を閉じた後、この境界を独立 semantic test で固定する。

## 総括

NO-GO。  
最優先は、basename を通す擬似的な「閉じた slug」、`unknown` の consumer 側 fail-open、相互 hold の無期限化である。  
pre-acceptance `land-intent` 送信も恒久 command に存在せず、段 4 裁定を満たしていない。  
`peers` には stat/open race による偽 `clear` があり、declare の受理集合には未裁定の縮小がある。  
land JSON の列挙値検証自体は概ね堅く、列挙された duplicate・巨大・数値 status から false landed は生成できない。  
MW3、entry-limit の MW4、threshold の MW5 は現テストでは殺せず、MW1 nonregular は hang 指定が必要。  
規律 2/3 の直接緩和は反証されたが、規律 6 は slug 経路で未閉鎖。  
指定どおり静的レビューのみで、pytest の緑は主張しない。