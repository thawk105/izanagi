単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (provisional 裁定 (P1)〜(P7)、不変条件 1〜9、変更面の実アンカー表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 段 2 plan (codex read-only 起草、全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md
- 依頼文と並走 wave の返信の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- 段 1 の pin 閉包検索の結論 (親の実測): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-closure.md
- 設計 (投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/output/insights/2026-09-21/tpcc-trace-certification-design/README.md の §3.1〜§3.3、§6.1、§7.1
- repo 内コード (read-only、投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/ 配下の
  `orchestrator/verifier/{parse,model,dsg,core,report,__init__,cli}.py`、`orchestrator/tests/test_verifier.py`

## 前置き — これは自分たちのコードの設計レビューである

研究用 repo (並行性制御の自動合成) の trace verifier (直列化可能性の検査器) に TPC-C 用の trace 形式 v3 を読ませる計画を点検してもらう。
verifier の certified 判定は合成した CC を採用してよいかの唯一の正しさゲートで、偽の認定 (本当は直列化不能なのに serializable と返す) は
研究の成果物を無価値にする。あなたは read-only の相談役で、実装・テスト実行はしない (書込可能 tmp が無いので静的読解でよい)。
**plan を守らせず点検せよ。親 brief の前提・file:line・親自身の実測値 (s1-closure.md) とその一般化も点検対象である。**
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## レンズ A — 正しさ境界と整合

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (certified 判定・anomaly の構造化出力・
YCSB の既存判定) の値や受理集合がどう変わるかを 1 行で書く。攻撃が成立しなかった項目は正直に「不成立」と書け。全項目を無理に成立させるな。

1. **偽の認定**: plan の identity 表現で、(a) 表の違う同一 key bytes が同じ object に戻る経路、(b) 同じ (table, key) が別 object に割れて
   依存辺が消える経路 (表番号の表現揺れ「01」と「1」、先頭 0、符号、空白)、(c) object 経路と compact 経路 (packed / tuple、workers=1 と複数、
   並列 → 逐次の fallback、`_ParsedFileNeedsLegacy` の legacy 落ち) のどれか 1 つだけが表を落とす経路、を具体の入力で探せ。
2. **v2 の不変**: v2 の受理・拒否集合、verdict、integrity 値、notes 文言、result_to_dict の bytes、witness の選択順・辺の追加順が変わる経路。
   特に interning・key id の採番順・set の反復順 (dsg.py の adjacency 構築の注意書き) が v2 で変わらないか。
3. **schema の混在と ParseError の優先順位**: run 内の v2 / v3 混在の検出位置 (単一 file、file 跨ぎ、並列 worker と親の再走査
   `_raise_parent_file_error`)、P/A 行だけの file・空 file・C の無い file の扱い、ParseError と integrity (indeterminate) の使い分けが
   fail-closed か。
4. **v3 の厳格検査**: C の token 数、table / tx_type の範囲と表記、W op、nS/nQ、v3 frame 内の v2 形の行、X/I の v3 形、宣言件数と E の検査が
   plan で抜けていないか。受理すべきでない入力を受理する (受理集合の過大) 経路、逆に並走 wave の返信どおりの正当な v3 を拒否する経路。
5. **anomaly の構造化 (規律 3)**: 表・取引種別が cycle の各理由・各節点へ正しく載るか (取り違え・同一 txid の別 file 版 = last-wins との整合)。
   report.py を編集しない制約のもとで、plan の出力点が v2 の出力を変えず、v3 で情報を落とさないか。
6. **(P7) の穴**: §3.3 の存在履歴 (insert 前の unborn、delete 版の読み、genesis 誤用) を本単位で実装しないことが、本単位の成果物
   (verifier が v3 trace に返す verdict) で偽の認定を作るか。作るなら、本単位で閉じるべきか、単位 5 へ送ってよいかを根拠つきで述べよ
   (本 wave の verifier が返す certified を本番の認定経路が使わない、という brief の主張も検査せよ: orchestrator/campaign/pipeline.py の
   allowlist、他に verify_trace_dir を呼ぶ経路)。
7. **変異の帰属**: plan §8 の変異候補それぞれについて、同じ入力を拒否する別の層が前後・内側に無く赤の理由が 1 つに絞れるか。
   絞れない変異と、足りない変異 (殺す test が無い機構) を挙げよ。

## 出力形式

Markdown。所見の表 (番号・レンズ項目・所見・real/refuted の見込み・重大度・根拠 file:line・成果物への影響)、その後に「plan への修正提案」、
最後に `## 総括` (5〜10 行、must-fix の要点)。推測は推測と明記せよ。
