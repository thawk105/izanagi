**NO-GO。主因は、failures に残す「違反した規則」の説明が依頼原文と一致しないことです。**

指定資料だけを静的に確認しました。README・fragment は commit `0b952aa74` と差分なし。要求された成果物の項目は本文上揃い、Elapse の合計も 10,836 秒＝3.01 node 時間で整合しています。図・表・ログの実体は今回の検査対象に含めていません。

| ID | 重大度 | 根拠（path・該当文） | 修正案 | 放置した場合の影響 |
|---|---|---|---|---|
| B-01 | **must-fix** | [README:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:18) は共通指示を「食い違えば投入前に相談」と要約し、[fragment:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/2026-10-01-t2853-r2-fig2c-1.md:16) は「親が単独で決め」たことを根本原因とする。しかし [common:3](/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-common.txt:3) は明文で「md_N.txt を優先」、同21–22行は承認済み計算量について「相談不要」。衝突時の相談義務は同資料にない。 | ①分割規則、②優先順位、③計算量の相談免除、④投入後のユーザー指摘を分けて記録する。分割しなかった事実は残すが、投入前から存在した相談義務への違反とするなら、その別の根拠を示す。恒久対応も、当時の規則と後から追加した手順を区別する。 | 台帳が、当時明記されていなかった義務への違反を史実として固定してしまう。 |
| B-02 | **should-fix** | [README:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:133) は再現用 checkout を「生成器の sha256 が `04db851a…`」だけで指定。一方、同77行は依存 `plot_backoff.py` が変わっても生成器本体の hash は同じで、依存は固定されないと説明する。また再現コマンドが必要とする wrapper を138行で「使い捨て」と呼ぶ。 | 描画用 checkout の commit、依存版を特定できる provenance の具体的な欄、外部入力・wrapper の保管先を再現手順にまとめる。「使い捨て」は「この測り直し専用・出力親に保管」などへ変更する。 | 指示どおり生成器本体だけを合わせた利用者が、異なる依存で描画・検査し、結果の違いを測定差と取り違える。 |
| B-03 | **should-fix** | [README:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:134) の傾向説明に続いて「原図…と同じ形の図」と断定している。§0では再現精度を評価しないと約束しており、「同じ形」の判定基準も示していない。 | 「同じ形」を削り、R2で観測された傾向の記述で止める。原図との関係は「同じ生成器本体を使用」「別 attempt の値として併記」と具体化する。 | 記述的な並記が、形状の再現成功を判定した結論として引用されうる。 |
| B-04 | **should-fix** | [brief:13](/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/s1-brief.md:13) は「設計択一なし」のため段2・3を省略。一方、[README:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:162) は分割との「択一」を出さなかったことが誤りとする。また brief のP1は親の provisional 裁定とされるが、原 source commit の使用は [md_4:13](/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-md_4.txt:13) の直接指定。 | 原 brief は逐語として保存し、READMEに振り返りを追記する。原 commit 使用は依頼への適合、軽量版は当時の判断、分割規則との整合は見落とした論点、と分ける。省略段の事後実施までは必要ない。 | 「設計択一なし」が検証済みの事実として残り、同様の省略を正当化する前例になる。 |
| B-05 | **nit** | [README:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:156) は「受入全走1回（見積り約0.3 node時間）」「実測は worklog に書く」。見積りとの区別はあるが、1回が予定なのか実施済みなのか不明。 | この版の時点で「予定・未実施」または「実施済み・費用未集計」を明記する。実績確定後は該当記録への参照に置き換える。 | 費用の見積りを示した文が、受入検査を実施済みという証拠として読まれる。 |

fragment の frontmatter、`## 新規`、`### {{F:slug}}. … [手順漏れ]` は指定形式に沿っています。**memory を恒久対応の参照先にすること自体は、[fragment規則:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/README.md:41) が許容しています。** ただし、当該 memory の更新実体、型タグの正本との照合、既存Fとの重複は指定資料外なので未検証です。

P1の原 source commit 使用そのものに問題は見つかりません。標本・CIの合成、他図の実行、機序・採否の主張も本文には見当たりません。§8は将来案の記録に留まっています。

## 総括

**NO-GO。B-01を直してから台帳へ反映すべきです。** 分割しなかった事実とユーザーの指摘を残しつつ、明文の優先順位・相談免除を欠落させない記録にしてください。B-02〜B-04も、再現条件と主張の範囲、軽量版を選んだ経緯を明確にする修正を推奨します。