単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/brief.md — 親の段 1 brief (scope・確定裁定・不変条件・前提実測・(P1)〜(P5))。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/gate-log-inventory.txt — 門番 log の全数 inventory (mtime・size・絶対 path、9/15 以降 192 file)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/memory-gate-facts.md — 門番の条件・jitter・leaders 判定の偽陽性・T-2610 飢餓の実測 (ユーザー裁定の正本は記憶 file、逐語)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/D2148-item12.md — 「inbox の門番条件値・FIFO・自動再投入・追加 L2 節を丸ごと採用した裁定ではない」の逐語。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/D2185-gate-relax-line.md — 1 wave だけ上限 2 へ緩めた先例の逐語。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/DW-O27.md — acceptance は lease を待たない (D662) の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/gate-loop-final.log — loop 型 log の実物 (attempt 2 系列、rc=70 postcheck → 再投入)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/gate-acceptance-loop.sh — loop 型門番 script の実物 (leaders の grep、周期、jitter、rc 分岐)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/acceptance-final.chain.log — chain 型 log の実物 (`gate: load=… leaders=… workers=… (cond …)`)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/run-acceptance-gated.sh — chain 型門番 script の実物。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/gate-loop-final.log — 飢餓の実例 (08:51 起動 → 12:44 GO、記憶の T-2610 節に対応)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-watchdog-segments/gate-loop-acc.log — 9/18 の「5 本同時投入」帯 (12:49〜12:50) を含む log。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis/tools/dev_wave_wait.py — 待ち手の正本。`acceptance` の claim / post-claim merge / receipt の流れだけ grep で引く (`_claim_once`、`lease_holder`、`started.txt`)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis/tools/wave_land_window.py — lease primitive。履歴を残す機構が無いことを確かめる。

## 役割

あなたは「受入門番の待ち時間診断」wave の段 3 敵対相談 (read-only、reasoning=medium) である。**親の brief 自身が検査対象**である。
brief の母集合定義・(P1)〜(P5) の前提・親の前提実測とその一般化・成果物の形 (裁定パッケージ) を攻撃し、集計 probe を書く前に直すべき欠陥だけを、
根拠 (file:line、log の行、brief の節名) 付きで返せ。プランを守る側に立つな。見つからなければ「見つからない」と書け。
この wave は診断のみで、repo の実装面は 0 行、門番の閾値・周期・lease TTL の変更はユーザー裁定 (実装しない)。lease primitive と待ち手は変えない。

書込可能な tmp は無い。静的検査でよい。テスト実測は親が行い、あなたの非実走を親は緑と記録しない。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 背景 (資料を読んで確かめること)

- 門番は repo に正本が無く、各 wave が job dir に script を写す。log は 2 形式 (loop 型 / chain 型)。条件は多くが `leaders ≤ 1 ∧ load1 ≤ 60`、2 周連続成立 → 0〜45 秒乱数 → 再カウント → 投入。周期 100〜140 秒乱数。一部は `≤ 2`、`l1 < 30`、pigz hold などの変種。
- leaders の数え方は wave によって「`[d]ev_wave_wait.py` を含む行を数える (codex 子の prompt 文字列が偽 leader)」と「interpreter で始まる行だけ数える (9/20 以降の写し)」が混在する。
- lease dir (`dev-wave-jobs/land-lease/`) は現在 stale ticket 1 件だけで履歴を持たない。receipt JSON 2 種にも時刻 field が無い。待ち時間は log の時刻文字列と started.txt / finished.txt / mtime からしか復元できない。
- 直近 20 wave (最終 log mtime 順) は 9/20 21:29 〜 9/21 05:20 の約 8 時間に収まる。T-2610 の飢餓 (9/20 08:51〜12:44) はこの窓の外。

## 2 つのレンズを 1 本で担え

### レンズ A — 測定設計・定義・復元の穴 (実効性)

1. 母集合「最終 log mtime が新しい 20 wave」は依頼の「直近 20 wave」として妥当か。landed wave に限る / attempt 単位にする / 20 wave の窓の中で同時に待った他 wave (窓外の wave、rulings-all 等) をどう数えるか。窓が 8 時間しか無いことで飢餓 0 件になる危険と、9/19 以降 79 wave 126 log の広い母集合を併記する案の是非。
2. (P1) 待ち時間の起点・終点。loop 型は最初の tick 行、chain 型は最初の `gate:` 行が起点でよいか。門番を起動した時刻と最初の tick の差、attempt 2 以降の起点 (前 attempt の rc 行か、60 秒 sleep 後か)、GO 後の post-claim merge (`attempt N: main=… behind=…` → `merged:`) を待ちに含めない判断の妥当性。log が途中で切れた wave (kill、job dir 消失) の扱い。
3. (P2) 飢餓の定義「待ち ≥ 30 分 ∧ 同時待ち最大 ≥ 3」は T-2610 の実例を 1 件として再現し、かつ「単に load が高くて閉じていた」(load1 > 60) や「leader が実際に 2 本走っていた」を飢餓と誤認しないか。T-2610 の log で leaders=1 → recount 2 に戻る型がどれだけ繰り返されているかを実際に数え、定義がそれを捉えるか述べよ。代替定義 (例: 「条件が単独では成立するのに再カウントで戻された回数 ≥ N」) を提案せよ。
4. (P3) 同時待ち数の復元。他 wave の tick 区間の重なりだけで足りるか。数え落とし (門番なし直接投入、~/.claude/jobs の消えた job dir、`rulings-all` の門番)、二重数え (同 wave の attempt 系列の重なり、同 wave の 2 本目 loop)、log の時刻が `HH:MM:SS` だけで日付を持たない問題 (日跨ぎ、mtime との突き合わせ) を挙げよ。
5. leaders 判定の偽陽性 (codex 子の prompt) が「開いた瞬間の leaders」と「飢餓」の数値をどう歪めるか。script の grep 形から wave ごとに判定方式を分類し列に持てば足りるか、それとも log の leaders 値を他 wave の走行区間 (started.txt〜finished.txt) から再計算した「真の leader 数」と並べるべきか。
6. (P5) 反実仮想の効果見積り (記録 tick 列へ `leaders ≤ 2` 等を再適用) の穴。開いた wave が leader になる 2 次効果、load の変化、jitter 後の再カウントの乱数性、同時刻に開く wave 同士の衝突 (9/18 の 5 本同時投入)。1 段伝播の近似で「効果見積り」と呼んでよいか、どう限定して書くべきか (上下限として書かない、出所列を分ける)。
7. 親の前提実測の一般化: 「lease dir に履歴が無い」「receipt に時刻が無い」は `wave_land_window.py` / `dev_wave_wait.py` の file:line で裏取りできるか。他に時刻を持つ一次資料 (acceptance-*.spawn.log、.pid の mtime、chain.log の `attempt N:` 行、started.txt) を列挙し、(P1) の起点として優先すべきものを示せ。

### レンズ B — 過剰・削除・裁定境界 (研究前進と scope)

8. 成果物 (insight README の数表 + 裁定パッケージ) が研究前進 (wave 回転率、8c 無人ループ) に本当に効くか。数表のうち裁定に要らない列、逆に欠けている列 (例: 待ち時間のうち load 起因 vs leaders 起因の分解、時間帯別、wave 種別 paper/実装/診断) を挙げよ。
9. 裁定パッケージの択 (閾値 ≤ 2、jitter 拡大、周期の位相ずらし、FIFO 優先順) は D2148 項 12 と D2185 の裁定と矛盾しない形で提示できるか。「丸ごと採用した裁定ではない」を、今回の提示がどう尊重すべきか。lease primitive・待ち手を変えない不変条件を破る択が紛れていないか。
10. 集計 probe (Codex author が worktree 内に書き、親が job dir へ退避して実行) の設計で、repo に残してはいけないもの、`output/insights/` へ写してよいもの (.md 逐語のみ)、DW-O03 の防護 path 文字列 (job dir の path、dev-wave-jobs) を含む file の作り方の制約を確認せよ。
11. 親が直接 Bash で集計を書きたくなる誘惑 (小さいから) への防壁が brief に書かれているか。

## 出力形式

- `## 所見` — 各所見を `A-n` / `B-n` の番号、重要度 (高/中/低)、根拠 (file:line / log 行 / brief 節)、直し方 1 行で書く。
- `## (P1)〜(P5) の判定` — それぞれ 妥当 / 要修正 (修正案) / 却下 (理由)。
- `## 飢餓定義の検証` — T-2610 log の実数 (streak=2 到達回数、recount で戻った回数、GO までの分) と、提案する定義。
- `## 総括` — 5 行以内。probe を書く前に直すべき欠陥の件数と、最重要 1 件。
