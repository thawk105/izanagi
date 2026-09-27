## 攻撃

- **成立 — 排他防壁の受理集合を運用で変える。** 同じ identity の claim が残れば、所有者の生死に関係なく `O_EXCL` で拒否される。退避してから再投入すれば、その拒否を通過できる。コードを変えなくても実効的な受理集合は変わる。D2187 は「削除していない」は退避の反論にならないと明記し、D2205 も claim の退避を却下している。反復 loop の各 job 間でこれを常用するなら、one-shot claim を実質的に運用で解除する設計になる。根拠: `orchestrator/campaign/campaign_claim.py:383–447`、`docs/decisions.md:69404–69415`、`docs/decisions.md:70375–70387`。

- **一部成立 — D2187 との同型性。** 「claim を退避して同じ identity を再取得する」という機構は同じ。ただし D2187 が明示的に却下したのは、**同一 job 内で**候補の後、stock 起動前に job body が自動退避する案である。(A) は終了した job の後に運用者が回収するので、却下文をそのまま適用して「明文違反」とは言えない。この違いを無視した攻撃は弱い。根拠: `docs/decisions.md:69389–69395`、`docs/decisions.md:69413–69415`。

- **成立 — 「手動回収だけ」の射程を広げる危険。** 実装は部分書込み時にも自動削除せず、手動回収を残している。しかしそれは、反復する方策 loop の通常の job 間遷移を毎回手動退避で実装してよい、という積極的な認可ではない。D2205 は pair *内* の再認可問題を session で直したが、次の job の claim 再取得は直していない。親の案は、この残った設計不整合を運用で恒常的に埋める判断を含む。根拠: `orchestrator/campaign/campaign_claim.py:383–386,447`、`docs/decisions.md:70353–70377`。

- **一部成立 — 規律 2。** claim 退避は verifier 自体を緩める操作ではなく、これだけで anomaly のある variant が certified になるとは言えない。ただし claim は測定前の認可防壁であり、拒否を人手で解消して再投入する判断を「コード無変更だから gate 無変更」と扱うのは不正確。再投入後も通常の認可・verifier を全て通す必要がある。根拠: `CLAUDE.md:67–71`、`orchestrator/campaign/loop.py:376–409`、`docs/decisions.md:70358–70365`。

- **不成立 — 規律 6 違反という攻撃。** この事案で、外部出力の指示を信頼した、あるいは未監査の作業物を採用した証拠はない。claim file や job 出力を事実確認の資料として読むこと自体は規律 6 に反しない。根拠: `CLAUDE.md:88–95`。

- **条件付きで成立 — 規律 7 と履歴の解釈。** iteration 3 の `eval-exception` を残し、同じ proposal の次回評価を iteration 4 と明記するなら、異なる実行が同じ campaign に入ること自体は改変でも違反でもない。driver は例外時に履歴を追記し、iteration を進めて保存する設計である。一方、iteration 4 を「iteration 3 が成功した」かのように扱う、または 3 の失敗を消すなら履歴の改変になる。根拠: `orchestrator/campaign/p3_s4_loop_policy.py:433–476`、`docs/decisions.md:73064–73068`、`CLAUDE.md:97–105`。

- **不成立 — 退避だけで証拠改変と断定する攻撃。** 原 claim の内容と移動記録を保存するなら、ファイルを消去したとは言えない。ただし claim の元の path は空になるため、当時その path に存在したことを後から検証できる記録が必要である。根拠: `orchestrator/campaign/campaign_claim.py:400–430`、`CLAUDE.md:97–102`。

## (A) を採る場合の最低条件

終了確認を job ID だけで済ませず、claim record の host・boot ID・PID・process starttime と照合して元所有者が不在であること、同じ protocol の生存所有者がいないことを確認する。元 claim の bytes、SHA-256、元 path、退避先、時刻、job ID、回収理由を保存する。iteration 3 の `eval-exception` と未測定の事実は残し、再投入を iteration 4 の新しい試行として記録する。walltime と通常の認可・correctness gate を再投入時に満たす。手動回収を今後の反復 loop の標準手順として暗黙に一般化しない。根拠: `docs/decisions.md:19324–19338`、`orchestrator/campaign/campaign_claim.py:383–430`、`orchestrator/campaign/p3_s4_loop_policy.py:443–476`、`orchestrator/campaign/p3_s4_loop.py:1364–1382`。

## 総括

(A) を**明文上の絶対禁止**とまでは証明できない。終了後の一回限りの手動回収には裁定上の余地がある。最も強い反対理由は、(A) を「2 本目以降を回す」ための常用手順にすると、D2187・D2205 が守った one-shot の拒否を運用で繰り返し解除し、未修復の driver 設計を事実上置き換える点である。継続運用の判断としては (B) を推す。