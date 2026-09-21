単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切っては
ならない (その path は「不在」と記録して先へ進め)。

W = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8 (レビュー対象は commit `784db3f02` に固定済み。作業ツリーは clean)

- W/output/insights/2026-09-21/paper-methods-ja/methods.md (**レビュー対象 1**、方法節草稿 2026-09-21 版、349 行)
- W/output/insights/2026-09-21/paper-methods-ja/implementation.md (**レビュー対象 2**、実装対応メモ 2026-09-21 版、213 行)
- W/output/insights/2026-09-21/paper-methods-ja/README.md (**レビュー対象 3**、wave 記録、75 行。§4 段 6 と §6 検査はレビュー後に親が足す。未記載はそれだけの理由では所見にしない)
- W/output/insights/2026-09-21/paper-methods-ja/verbatim/request.md (ユーザー依頼の逐語。**scope の正本**)
- W/output/insights/2026-09-21/paper-methods-ja/verbatim/s1-brief.md (親の段 1 brief と provisional 裁定 (P1)(P2)(P3)。攻撃対象)
- W/output/insights/2026-09-20/paper-methods-ja/methods.md と W/output/insights/2026-09-20/paper-methods-ja/implementation.md (前稿、bytes 不変。差分の妥当性を見る。`diff` で新稿と比べてよい)
- W/output/insights/2026-09-20/paper-methods-ja/README.md (前稿の wave 記録。冒頭の「前方 pointer」節だけが本 wave の追加)
- W/docs/phase3.md (現行チェックポイント先頭の [x] 1 項だけが本 wave の追加。先頭 30 行だけ読め)
- 一次資料 (B-8): W/docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md (結果稿、204 行)、
  W/output/insights/2026-09-21/t2807-b8-effective/README.md (発効記録、225 行)、
  W/docs/b8-final-candidate-longrun-verify-preregistration.md (事前登録 v1、557 行。§0・§3・§4・§5・§6・§7・§8・§12 を読め)
- 一次資料 (K2): W/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md (§0)、W/output/insights/2026-09-21/t2795-pair-repair/README.md (§0)
- 一次資料 (B-5): W/docs/b5-generator-contrast-preregistration.md (§0 だけでよい)

**巨大 file の扱い (必ず守れ):** `W/docs/decisions.md` は 70,675 行。**全文を `cat` してはならない。** `grep -n "^## D<番号>\. "` で
位置を出し `sed -n` で 60 行以内ずつ読め。検算に要る D = D2158、D2172 (項 4)、D2175、D2183、D2186 (項 1)、D2187、D2190、D2194 (項 1・2)、
D2200 (項 1)、D2202、D2205、D2206 (「窓と収集」付近の B-5 / K2 の状態)。worklog は `W/docs/archive/worklog-phase3-09*-<番号>.md` に
1 エントリ 1 file (先頭 1〜20 行が本文、残りは carry 行) — 読むのは 1746 / 1749 / 1754 / 1755 / 1779 / 1790 / 1791 / 1795 / 1801 の先頭 20 行だけ。
コードは `W/orchestrator/campaign/loop.py` (`authorization_session` 周辺)、`W/orchestrator/campaign/p3_s4_loop.py` (`main` の pair_mode 分岐、
3,600 行超なので `grep -n` と `sed -n` で読め)、`W/tools/pegasus/p3_s4_loop_pegasus.sh` (`IZANAGI_S4_STOCK_CONTROL`) だけ。
git は read-only の `git -C W log` / `git -C W show` / `git -C W diff` だけ使ってよい。

この段では commit・push・file の書き込みを一切行わない。成果は最終メッセージの本文だけで返す。pytest・build・測定は走らせない
(静的検査でよい。テスト実測は親が行う)。予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## これは何のレビューか

自分たちのプロジェクト (izanagi) の論文用文書に対する独立レビューである。親 (Claude) が前稿を複製して書き換えた。軽量版 docs-only
wave (実装面ゼロ) で段 2・3 は省いた。**お前は `DW-C00` が残せと定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only
独立レビュー 1 本」で、下の 2 レンズを 1 本で担う。** 本来は Codex の子が担うが、Codex が利用上限 (復帰 9/26) のため同系統モデルの
独立 context で代替している。親に遠慮せず攻撃せよ。

依頼の要点 (逐語は request.md): 主対象は B-8 の方法 (発効束・検証 runner v5・校正段と本走段・3 値判定の規則) の追加。付随して同じ方法節内で
直接関係する状態記述だけを揃える — K2 の stock 対照口は D2187 (同 job pair の初投入の不成立) と D2205 (pair mode の修復) を区別して成功を
示唆しない、B-5 は D2200 項 1 の段階認可 (本走は未認可) として B-8 と分けて書く。09-20 以後の着地全般の総点検には広げない。出所は一次資料で、
版や要約を出所にしない。B-8 の件数は「本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠」と 1 文に並べる。新しい日付の
dir、前稿の bytes は不変 (前稿 README に前方 pointer だけ)。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 は緩めない。

親が実走した検査: `tools/check_docs.py` 違反なし、相対リンクの解決、本文の repo 相対 path の実在、`git diff --cached --check` 空。
親が一次資料で確かめた点: K2 pair の初投入は `482f19b88` より後の main `6a3e158` の submit-tree から (新 campaign ID)、D2187 の main 着地は
fold `7baf3f375` (2026-09-20 20:42)、D2190 は fold `7c0a1c63a` (22:54)、B-5 driver の初出 `c41cfb09f` (20:34)。D2205 以後に pair 再投入を、
D2200 以後に B-5 本走を認可した D は無い (grep)。

## レンズ A — 事実の整合 (正しさ境界)

1. methods §3 の B-8 の 9 段落と 3 項、implementation の B-8 行・読み分け行・境界節の各文を、事前登録の節・D の項・結果稿・発効記録と
   1 対 1 で照合せよ。特に: 適格の条件列、打ち切り条件、共通部分の最大値と丸め禁止、予算 14,400 s と段下げ、判定集合の定義、3 値の評価順と
   各条件、校正の未完走 (運用上の indeterminate) と判定器が完走して返す `indeterminate` verdict の区別、本走の未完走の 2 分岐、bench 失敗の扱い、
   hard timeout の 3 値、発効束 JSON の作り方、束縛の掛け方、runner v5 の所在と sha256、request ID と日時、件数。
2. **規律 2 を緩めて書いていないか。** 失格規則・校正の即失格・再検証の禁止・pass に丸めない・研究成功と書かない、の文が一次資料より弱くなって
   いないか。逆に一次資料に無い強い主張 (serializable の証明、乱数列の独立性、同一 binary、S-1 充足、検証相との比較) を足していないか。
3. **「数に付く条件」:** 判定集合 30 枠の全体を「独立 8 反復 × 3 workload・extime 10 s」へ帰属させている文が、3 file と phase3 の項のどこかに
   残っていないか (前回の同種 wave で must-fix になった型)。
4. K2: D2187 と D2205 が区別され、修復の緑・結合検査を対照の成立と読ませる文が無いか。pair mode の実装アンカー (関数名・引数・CLI・job body の
   条件) がコードと一致するか。「前進前の巡の campaign を再開したものではない」の根拠が一次資料にあるか。
5. B-5: 未発効・試走完走 (主標本外)・D2200 項 1 は段階認可で本走未認可、が一次資料と一致するか。D2172 項 4 の範囲を越えて書いていないか。
6. README §3 の表の「型」(前稿の照合時点で既に偽か / 後の着地か) と、その根拠の commit・時刻が正しいか。

## レンズ B — 過剰・削除・scope (実効性)

1. 依頼の scope (三つの対象) を越えて書き換えた箇所は無いか。逆に、三つの対象の記述なのに書き換え漏れ (前稿の「未発効」「1 job も投入していない」
   「runner・生成器は実装されていない」型の文) が残っていないか — 3 file と phase3 の項を全数で走査せよ。
2. (P1) の扱い — 採用時点を `36fb14a3d` と書きつつ継承部分を再照合しない — は読者に誤読を生まない書き方か。継承部分の「本稿の時点」表記を
   「前稿の照合時点」へ直したのは 4 箇所 (methods §1・§5、implementation の A-1 行・境界節の兄弟 wave の文) で足りているか (「本稿の」「現行」
   「未反映」等で新稿の時点を指すと読めて偽になる継承文が他に無いか)。直し過ぎて scope を越えていないか。
3. (P2) (B-8 を §3 に置く) と (P3) (pin 前進の段落の末尾の限定) は妥当か。より小さい変更で足りるなら指摘せよ。
4. 出所の取り違え: 論文ストーリーの版や同日の草稿 (entry 1801) を事実の出所にしている文が無いか。D (裁定) を実施の出所にしていないか
   (認可・禁止・手番 = D、完走・件数・日時 = 実施記録)。
5. 仮想リスク向けの追加 (gate・検査・台帳・一般化) を書いていないか。削れる冗長な文があれば指摘せよ (ただし限定文は削らせるな)。

## 出力形式

先頭行に `VERDICT: GO` または `VERDICT: NO-GO` (must-fix が 1 件でもあれば NO-GO)。続けて所見を
`[must-fix|should-fix|nit] <file>:<行> — <問題> / 根拠: <一次資料の path と節・行> / 直し方: <具体案>` の形で 1 行ずつ。
攻撃して不成立だった項目は `[refuted] <攻撃内容> — <不成立の根拠>` で列挙せよ (親が網羅性を判定する)。最後に、照合した D と entry と
一次資料の一覧を 1 段落で書け。
