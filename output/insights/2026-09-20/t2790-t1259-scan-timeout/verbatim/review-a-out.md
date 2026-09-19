## 所見

静的レビューのみ。54 passed と provenance 監査結果は親からの報告であり、本レビューでは再実行していません。

1. **real | must-fix — M2 の期待 KILLED 集合が不足しています。**
   根拠: `adjudication.md:98`、`orchestrator/tests/test_t1259_scan_bound.py:69`・`:90`。固定 dict を返す M2 は、test 2 の `len(calls) == 4` と、test 3 の `pytest.raises(TimeoutExpired)` の両方に違反します。新 test file 全体を対象にした静的予測は次のとおりです。

   | 変異 | test 1 | test 2 | test 3 |
   |---|---|---|---|
   | M1: 定数を 0.0 | 生存 | kill：64 行の literal assertion | 生存：timeout=0.0 の同一例外を代役が送出 |
   | M2: 固定 dict | 生存 | kill：69 行で呼出し数 0 | kill：90 行で DID NOT RAISE |

   M2 の test 2 は呼出し数の assertion で止まるため、HEAD 不一致まで到達しません。「走査省略」という変異原因は一つでも、赤の直接理由は二つです。実走前に期待集合と理由を訂正してください。test 3 を弱める必要はありません。
   **放置時の影響:** production の受理集合は変わりませんが、変異 matrix／F945 の kill 帰属が実結果と不一致になります。

2. **refuted | should — production の timeout・走査・例外条件が変更されたという疑いは棄却します。**
   根拠: `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:133`・`:149`・`:167`・`:684`・`:852`。production 内の呼出しを全列挙すると、`_run_git` は snapshot 内の **170・176・184 行**、`_repo_is_detached` は **194 行**、`_repo_snapshot` は observe 内の **684・852 行**です。observe は引数追加なしで、全 Git 呼出しが既定 30.0 秒になります。追加の production caller は見つかりません。

   差分は引数定義・timeout の参照・中継に限られ、argv 4 種、`GIT_OPTIONAL_LOCKS=0`、`check=True/False`、返り値の計算、`ProbeError` 条件は不変です。helper にも例外捕捉はありません。型注釈は値を検証しないので、明示的に `None`／負値を渡せば到達できますが、現行 production／fixture caller にその経路はありません。なお CLI の `main()` が例外を失敗結果へ変換する既存挙動は別です。
   **放置時の影響:** 現行 caller の production 受理集合と、fixture の timeout 時 fail-closed は維持されます。

3. **real | should — 「拒否能力維持」は、実 repo の汚れ検出を実証したという意味にはできません。**
   根拠: `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:77`・`:78`・`:632`、production probe `:289`。module fixture は取得後に detached・tracked・untracked を従来どおり上書きします。負例はその後で `untracked_paths=["unexpected"]` を注入して observe の拒否を検査するため、今回の変更で弱まってはいません。ただし実 repo の untracked 出力から拒否までを接続した検査ではありません。

   また `adjudication.md:101` の「untracked 走査だけを省く変異は等価」は**既存 module fixture の観測面に限定**すべきです。実際に Git 呼出しを一つ削れば、新 test の「4 件」assertion は検出できます。
   **放置時の影響:** 実装の拒否条件は維持されますが、F945 台帳が実証範囲を過大に記述します。

4. **refuted | should — 新 test の spy・比較・例外注入に、production を緩める変更はありません。**
   根拠: `orchestrator/tests/test_t1259_scan_bound.py:41`・`:64`・`:76`・`:79`。spy は保存した本物の `subprocess.run` へ委譲します。tmp repo は各 test 専用で、二つの snapshot 間に作業木を書き換える処理がないため、untracked を含む全 dict 比較に今回固有の不安定要因は見つかりません。

   test 3 は例外伝播専用の故障注入であり、実 Git の timeout 発生を実証する test ではありません。同一例外オブジェクトまで検査しており、production を緩めていません。120.0 の literal pin は現在の**候補実装**の固定として整合します。採用値変更時は更新が必要ですが、採用の実測根拠にはなりません。commit `4208bf332` も候補値・採用未確定と明記しており、食い違いはありません。
   **放置時の影響:** 受理集合は変わりませんが、この test の緑を120 秒の妥当性の証明に転用すると F945 の主張が過大になります。

5. **refuted | should — inventory・golden・自走 harness の追加修正は、確認した範囲では不要です。**
   根拠: `orchestrator/tests/test_plain_runner_coverage.py:35`、新 test `:95`、`conftest.py:670`・`:2161`、`test_real_repo_serialization.py:299`、`test_hooks.py:3374`。`_self_runnable()` は最初の `__main__` より後に実行 signal があることを要求し、新 test の `SystemExit(_run())` はこれを満たします。

   新3 node は tmp repo のみを走査し、既存 module fixture の consumer ではありません。real-repo inventory／memo／golden の追加対象になりません。helper は pytest の通常の収集名に一致せず、hooks の既存 probe 分類も不変です。確認した module 列挙系検査にも追加ファイル数を固定する条件は見つかりません。
   **放置時の影響:** 確認した静的契約では、既存51 case の配置・受理集合は変わりません。consumer 実走結果は別途必要です。

6. **不明 | should — G5 が90%を割るかは、実 collection の結果待ちです。**
   根拠: `orchestrator/tests/test_acceptance_schedule_order.py:660`・`:704`・`:712`。条件は全件登録ではなく `covered / collection_count >= 0.90`。新3 node の未登録だけでは赤と断定できません。既存集合が同じなら被覆率は `C / (N+3)` になります。`adjudication.md` §2.5 の「無いと赤になる」は訂正対象で、author 報告の留保が正確です。
   **放置時の影響:** 台帳未登録は新3 node を未知コストとして扱わせますが、G5 不合格かどうかは現在の被覆余裕に依存します。

7. **real | should — 120秒と245秒の比較は、snapshot 全体の時間保証にはなりません。**
   根拠: `brief.md:46`、production probe `:170`・`:176`・`:184`・`:194`。120秒は各 Git 呼出しの上限で、4回の直列呼出しには合計予算がありません。Git 部分だけでも設定値の和は480秒、加えて hash 読取り等があります。「120 < 245」から fixture 全体が lock deadline 内に収まるとは導けません。
   **放置時の影響:** fail-closed 自体は変わりませんが、F945 の待機時間・他 consumer への影響について誤った保証になります。

## 通る正例

- **所見1:** 未変異版の3 test がすべて緑。そのうえで事前登録を **M1＝test 2、M2＝test 2＋test 3** に訂正し、同じ runner 対象で実走した失敗 node 集合と直接の赤理由が一致すること。test 1 は両変異で生存し、test 3 は M1 で生存すること。

## 主張の限界として記録すべき文

- 「production の Git timeout は各呼出し30秒を維持した。fixture の120秒は各呼出しの候補上限であり、snapshot 全体の上限ではない。」
- 「既存負例は注入した untracked snapshot の拒否を検査する。実 repo の cleanliness 出力は既存 fixture が上書きするため、その実出力から拒否までの一貫した検証ではない。」
- 「M1 の kill は候補値の literal assertion によるもので、実 Git の時間切れ発生を証明しない。M2 は呼出し数検査と例外伝播検査の双方で kill される。」
- 「部分走査省略の等価性は変異位置と観測 test に依存する。M2 の結果だけで全走査項目の必要性を実証したとは主張しない。」
- 「tmp repo の正例と例外注入は値の中継・snapshot 内容・伝播を確認する。混雑下の採用値の妥当性は別の実測で判断する。」
- 「group 化前後の改善は観測上の関連であり、時刻・負荷・host 差を分離した因果推定ではない。」

## 総括

**NO-GO：現行の変異事前登録のまま完了扱いにはできません。**
M2 の期待集合・赤理由を実走前に訂正することが must-fix です。production 実装の must-fix は見つかりません。
訂正後の変異走、consumer／受入結果、実測による候補値判定をそろえ、上記の主張範囲を記録することを GO 条件とします。
