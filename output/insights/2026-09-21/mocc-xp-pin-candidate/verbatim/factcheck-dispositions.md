# 事実照合 (Claude 独立 context、読み取りのみ) の所見と対応

- 照合子: Claude (Agent tool の `Explore`、model 指定 `opus`)、本会話を参照しない fresh context。対象 = insight README (R)、worklog fragment (W)、decisions fragment (D) の初稿。
- 所要: 79 tool 呼び出し、784 秒。照合済み・一致 約 62 件 (verbatim の probe log・report・stderr・brief・plan・裁定・events・prompt は job dir の原本と cmp でバイト一致)。
- 位置付け: Codex の利用枠切れで dev-wave 契約の段 3・段 6 (Codex read-only) が走らなかったための補助。Codex レビューの代替ではない。
- 本表は親が所見を要約し対応を書いたもの (照合子の報告の逐語ではない)。対応はすべて親が一次資料で確かめてから反映した。

| # | 所見 (要約) | 重大度 | 対応 |
|---|---|---|---|
| M1 | R §7-4「C は gitlink でないので submodule update では取得されない」は plan が反証した強い形。主 module store へ fetch した branch は後から初期化された木に origin/<branch> として入りうる (witlight 5b02546f が実例) | must-fix | R §7-4 を「C を持つ保証は無い、fetch 前に初期化された木には無い、fetch 後の木には入りうる」へ書き換え |
| M2 | R §3・裁定文「検査器の入力 = old/new blob・差分 path 集合・祖先関係」は不足 (head define の cmake 2 file、`--repo` の作業木と tree、compiler も読む) | must-fix | R §3 を tree の同一性 + 検査器の版 + compiler で書き直し。裁定文は逐語のまま R §6 に訂正を注記 |
| M3 | 段 3 相談の投入は 14:32:57 / 14:32:59、所要 6 / 5 秒、launcher rc=2・codex exit 1 | must-fix | R §6・W を訂正。裁定文は逐語のまま R §6 に訂正を注記 |
| M4 | R §2「いずれも clone --shared の scratch」は不正確 (p1 は作業木への apply --check と git archive の scratch、p5 は作業木を読む、p7 は読み取り) | must-fix | R §2 の表に probe ごとの手段の列を足した。§9 に scratch-e9 を追加 |
| M5 | R §1「統合に要る修正を実測で確定」は、実測が TRACE=0 の D297 だけで採否は次 wave なので言い過ぎ | must-fix | 「D297 (TRACE=0) を通す修正案を実測で特定、TRACE=1 未測定、採否は次 wave の段 3・4」へ |
| S1 | 「負例 4 本は e9e477ca + 計装の上でだけ当たる」は試した基底 2 つを超える量化 (p4 版でも当たる) | should | 「e9e477ca 単独では rc=1、+ 計装では rc=0」へ |
| S2 | p6 の argv・rc・compiler path の記録が無い | should | p6 を argv・compiler 解決・rc を log へ書く script で再実行 (14:56、rc=1、`p6-d297-clang.log`) |
| S3 | p8 の出力が保存されていない | should | 再実行して `p8-t152-ancestry.log` を保存 |
| S4 | 復帰日時の時間帯が不明なことが R・W で落ちている | should | 「表示どおり、時間帯の表記なし」を R §0・§7 と W に追記 |
| S5 | D の「D297 は header 差分と include 活性の変化を保証範囲外として拒否、trace.hh 例外は D297」は帰属が不正確 | should | D297 = header 差分の拒否と include 活性の同一性の保証、trace.hh 例外は検査器の実装 (t1506 の経緯) へ書き分け |
| S6 | W の T-2295 更新「emit しない (再確認)」は文字列検索の限界が落ちている | should | 「verifier が I emitter と認識する文字列を含む file 0 件、別表記の不在までは証明しない」へ。検索を `p9-i-emitter-grep.log` として保存 |
| S7 | W「親は実装面を書いていない」は、repo 外の probe script と scratch 上の置換 (D95 決定 (2) では実装面の性質) を覆っていない | should | 「repo の実装面 (commit 対象) は書いていない、repo 外 probe と scratch 上の測定用置換は親」へ |
| S8 | D95 決定 (3) (Codex 不可用時は停止してユーザー裁定へ返す) をどう満たしたかが無い | should | 親は代筆せず実装を止めた。既定は Codex 復帰後の次 wave、復帰前に進めるなら D105 waiver のユーザー裁定が要り、本 wave は求めていない、と R §0・W に明記 |
| N1 | R §1 の section 参照のずれ | nit | 修正 |
| N2 | p3・p4 行が型置換を書いていない | nit | 追記 |
| N3 | include 行の同一性の典拠は report JSON | nit | R §2 の report 節に `include_line_count` を明記 |
| N4 | (P1)〜(P6) は brief の provisional 裁定 | nit | R §6 を訂正 |
| N5 | D95・D780 が job dir の逐語に無い | nit | `extract_verbatim.py` に追加して再抽出 |
| N6 | 開始 gate の rc=0 は log に無い | nit | R §6 に「OK 表示、rc=0 は親 session の出力」 |
| N7 | brief 訂正は 3 項目 | nit | W を 3 点へ |
| N8 | 段 3「1 度も実行されず」は不正確 (turn.started まで進んだ) | nit | R 冒頭を「起動直後に枠切れで失敗、出力 0 byte」へ |
| N9 | T-2295 更新「certified 化は妨げない」 | nit | 「I の不在は gate の妨げにならない」へ |
| N10 | 波及表の検算と I emitter grep の出力が未保存 | nit | `count-ripple.log`・`p9-i-emitter-grep.log` を保存 |
| N11 | probe commit が store に無いことの確認範囲 | nit | wave の submodule store で 3 本とも `cat-file -e` rc=128 を親が確認 (`p10-probe-commits-absent.log`)。主 module store は隔離 session から読んでいない (probe は `--shared` clone の自前 object dir に commit しており、主 store へは書いていない) |

未確認のまま残るもの: 主 module store に probe commit が無いことの直接確認 (上記 N11 の理由で書き込み経路が無い)。
