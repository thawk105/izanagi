静的読解による所見です。**単位 4 の中核案は妥当ですが、「単位 5 が verifier を変更せず完了できる」という前提は成立しません。** 実装・テスト・変異実行は行っていません。

以下、`plan`＝[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md)、`brief`＝[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md)、`closure`＝[s1-closure.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-closure.md)、`設計`＝[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/output/insights/2026-09-21/tpcc-trace-certification-design/README.md)。コードの短縮名は `orchestrator/verifier/`、テストは `orchestrator/tests/` 配下です。

| 番号 | レンズ項目 | 所見 | real/refuted の見込み | 重大度 | 根拠 file:line | 成果物への影響 |
|---|---|---|---|---|---|---|
| B1 | 1・2 研究前進 | **存在履歴の担当が欠ける。** P7 のままでは、単位 5 の genesis 誤用試験を通すため verifier の追加実装が必要。plan 自身も認識しているが、着手条件への注記だけでは担当の空白を解消しない。 | real | **must-fix（分担・完了条件）** | brief:58、plan:354、設計:252,281,282、dsg.py:650–668 | INSERT 前 genesis 読みは orphan にならず、非巡回なら他の条件次第で certified。単位 5 の全例をそのまま受け入れる成果物にはならない。 |
| B2 | 1 emitter 整合 | C/R/W/X、表域、取引種別、nS/nQ、P/E は並走返信と一致。「そのまま読めない」という攻撃は不成立。I の追加受理も emit されない通常入力を妨げない。 | refuted／不成立 | nit（修正不要） | request-t2854.md:10以降、plan:74–80、brief:24–28 | 暫定返信どおりの正常 frame は受理できる設計。実 emitter との結合済みという意味ではない。 |
| B3 | 1 出力点 | `result_to_dict_v3` は後続から直接 import でき、identity・tx_type の表現を作り直す必要は見当たらない。ただし capability の digest は旧射影のまま。 | 基本案への攻撃は不成立／接続制約は real | should | plan:152–195、core.py:254–264、campaign/pipeline.py:654–664 | 単位 5 は診断出力を配線できる。**新 metadata まで receipt digest に束縛する要求**が加われば core 側にも変更が必要。現時点で先取り実装は不要。 |
| B4 | 2 過剰実装 | 新 gate・台帳・CLI/pipeline 配線・S/Q 解析・範囲 index・存在履歴実装は含まれない。v3 I 行の安全側処理も小さい既存機構の延長。 | refuted／不成立 | nit（修正不要） | plan:74–80,154,197–222,354 | 単位 4 の列挙に沿う。削る対象は機能本体より重複検査・重複試験。 |
| B5 | 2・3 schema 検査 | sorted outcome 走査で検査済みの schema を merge でも再検査するのは重複。新しい混在エラーまで厳密な先行位置を保証することは、v2 既存互換から自動的には導けない。 | real | should | plan:90–100、parse.py:700–713,827–835、test_verifier.py:2329,2351 | 正常入力の verdict は変わらず、主に診断契約と保守量が増える。優先順位を採用するなら親 outcome 走査に一元化できる。 |
| B6 | 3 identity 局所化 | tuple identity を合成文字列へ変える削減案は不成立。合成・分解規則が増え、生 hex と表の分離を別途守る必要がある。別 map も compact 復元・last-wins・anomaly 射影との同期が必要。 | refuted／不成立 | nit（修正不要） | plan:20–52,114–120,146–152、parse.py:743–770、dsg.py:764–802 | tuple＋token table 列＋派生型は局所的で、後続も再利用しやすい。packed 検索本体を保存する判断も妥当。 |
| B7 | 4 テスト実効 | legacy parser／tuple builder の差替えは実機構を呼ぶため、それ自体は stub 緑ではない。ただし workers=2 だけでは実並列の証明にならない。 | 不成立／経路確認不足の見込みは real | should | plan:256–263、parse.py:813–822、dsg.py:550、test_verifier.py:2642–2645,2867–2874 | 少なくとも代表 fixture は複数 file・複数 task とし、既存方式で子 PID を確認する。単一 file の全ケースに並列確認を重複させる必要はない。 |
| B8 | 4 変異の検出力 | #5 は削除箇所が曖昧。親 outcome 検査と merge 検査の片方だけを消しても、正常な混在 file の拒否試験は通りうる。 | real（計画上の冗長検査による） | should | plan:96,99,276,320 | 「殺す test がある」とする説明が過大。片側削除はその試験集合に対して等価になりうるが、全入力で等価とは未証明。 |
| B9 | 4 変異 fixture | #3 の read-only 解決試験は、同表一致だけでなく**別表・同 hex の writer が存在する対照**を明記すべき。#10 は tx_type 固定と table 欠落を別変異に分ける。 | real の見込み（fixture 未確定） | should | plan:271,273,318,325、dsg.py:414–421 | table を無視しても偶然同じ writer に当たる fixture では検出できない。#1/#2 は参照辺集合 fixture が具体的で、検出根拠がある。 |
| B10 | 4 重複・単一理由 | C 5/7/8 token、通常構文エラー後の file 消失などは既存試験と重複。混在＋E 欠落は基本拒否試験から分け、優先順位を問うケースとして扱うべき。 | real | should | plan:275,278,279、test_verifier.py:472,2351 | 新 v3 分岐・混在時だけを追加すれば試験量を減らせる。複数故障の fixture は優先順位試験には有効だが、個別機構の帰属には弱い。 |
| B11 | 5 閉包検索 | 「4 source file の固定 sha 比較 0 件」は、結果 golden 不在を意味しない。closure の一覧は全 fixture の結果 hash と directory inventory を落としている。plan は拾っている。 | real（closure の一般化不足） | should | closure:9–15、test_verifier.py:2893–2956、plan:308 | source digest が動的でも、振る舞いの変更は赤になる。**結果 hash の存在を source sha pin の反証として数えてはいけない。** |
| B12 | 5 不変条件7・8 | 新 module 禁止は、実行時依存を既存 source closure 内に保つ今回の制約として妥当。fixture dir 禁止も exact inventory に根拠あり。一方「新 test file は必ず inventory 改訂になる」は強すぎる。 | 部分 real | should | campaign/campaign_lock.py:49–63、test_t671_source_binding.py:303、test_verifier.py:2941–2945、test_plain_runner_coverage.py:44–74 | 自走 harness 付き test file は一般 inventory 上ただちに禁止されない。ただし今回は既存 file にまとめる方が変更面は小さい。禁止の理由を区別すべき。 |
| B13 | 5 不変条件9 | EdgeReason の repr pin から全基底 dataclass の field 禁止までは導けない。`repr=False` の field もあるため「field を足すと必ず repr が変わる」も厳密には過大。 | real | should | closure:7、brief:42以降、model.py:314–368、test_verifier.py:2653–2663、plan:130–142 | 禁止は必然的制約というより保守的な設計選択。ただし table を equality から除く安易な縮小は避けるべきで、今回の派生型案を覆す実益は小さい。 |
| B14 | 5 P3 | **現段では非0 nS/nQ を ParseError にする案を支持。** 宣言不一致方式は、未解析の S/Q 件数と構造化違反を先に拡張する必要がある。 | 過剰との攻撃は不成立 | nit（修正不要） | plan:74,80,282、設計:337、parse.py:426–427 | 段 2 では零限定を外して実件数比較を追加すればよい。どちらの案でも段 2 の変更は必要で、今から mismatch を実装しても作り直しを消せない。 |
| B15 | 6 規模・分割 | author 1 本は妥当。800〜1,195 行も概算として不自然ではないが、21 test＋全経路比較＋障害注入を450〜650行へ収める見積りは楽観寄り。 | real の見込み（推測） | should | plan:265–287,335–342 | 共通 fixture/helper の設計次第で変動する。file ごとの分業より、同じ author が契約→parse→DSG→射影の順で整合させる方が手戻りを減らせる。 |
| B16 | 1・4 資料誤読 | 「NewOrder/Order の番号は射影にない」は誤り。brief に5/6がある。また保持する op は `I/D/U` で、`INSERT/DELETE/UPDATE` という入力文字列ではない。 | real | nit | brief:26、plan:269,281,306 | 不要な未決事項を消せる。試験 author が長い op 名を正常入力に使う混乱を防ぐ。 |

## plan への削除・局所化の提案

1. **P7 の先送り先を具体化する。** 今回へ存在履歴を無断追加せず、「単位 5 のうち §6.1 genesis 誤用は、別途 verifier の存在履歴実装が必要」と分担・完了条件を直す。pipeline の現 allowlist は、この不足が解決済みである根拠にはならない。

2. **schema 検査は親 outcome 走査に一元化する。** 厳密な診断優先順位を維持するなら、成功・failure・overflow の観測情報は有用だが、検査済み columns の merge 再検査は削除する。これで変異 #5 も一箇所の意味のある変異になる。

3. **tuple identity、compact の表列、派生型は維持する。** 合成 token や外付け metadata map へ替える削減は勧めない。「v2 で触らない行」に加え、共有 helper の v2 戻り値・順序・旧 reporter の結果を既存 golden で守る。

4. **テストの直積を減らす。** identity・cycle metadata・fallback は全経路で確認し、字句拒否の全値を全経路×workersで繰り返さない。既存 v2 ケースを複製せず、新分岐に関係する対照だけ加える。

5. **変異を一変更・一帰属へ整える。** #3 に別表同 hex の対照を明記し、#10 を二つに分ける。nS/nQ 非0のケースには S/Q 行を入れず、未知 tag 拒否による代替検出を防ぐ。

6. **閉包の説明を限定する。** 「source sha pin」「結果 JSON hash」「repr golden」「fixture inventory」を分けて記述する。新 module・fixture dir を増やさない方針は維持しつつ、全 dataclass・全 test file の禁止を実測からの必然とは説明しない。

## 総括

- must-fix は、P7 と単位 5 の全例受入との分担不整合。存在履歴の実装担当を明確にする必要がある。
- 単位 4 の成果だけで、§6.1 genesis 誤用まで verifier 無変更で完了することはできない。
- emitter の暫定形式と parser 案の不一致は見つからなかった。
- identity・tx_type・新出力点の基本設計に、作り直しを必須とする欠陥は見つからなかった。
- schema の二重検査と、それに依存する変異 #5 は局所化・定義修正を勧める。
- 固定 source sha がなくても、全 fixture の結果 hash と inventory は互換制約として残る。
- P3 の非0 nS/nQ 拒否、author 1 本、新規配線を後続へ残す判断は支持する。
- 以上は静的評価であり、受入成功・変異の殺傷・実並列実行は未確認。