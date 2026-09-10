## 契約語法の判定 (P1 への回答)

**P1 は refuted。`本走` は live preflight を含まない。**

amendment は実行を明確に三段へ分け、第二段を `live preflight`、第三段を `本走` と呼ぶ。そのうえで U11 は「軸 3 の live 本走」を禁止しているため、対象は第三段の `run-ready --live` である。[amendment:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md:103) [amendment:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md:192)

09-01 記録も U11 の禁止対象を exact に `run-ready --live` としている。[registration-preflight:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md:134)

4 件の判定は次のとおり。

- **U11: live preflight には掛からない。** 頁境界の再出現は page 0 probe だけの preflight では評価されず、禁止文も `run-ready --live` に限定される。

- **control evaluator: live preflight には掛からない。** evaluator 不在が現れるのは本走の `_run_stream` である。preflight は取得量・availability の分類だけを行う。[related_work_search.py:6168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6168) [related_work_search.py:6808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6808)

- **resolver: live preflight 自体は止めない。** 未実装行は `blocked` のまま全行 accounting することが契約上許され、実行器も wire request を出さず `blocked` 行を生成する。[amendment:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md:107) [related_work_search.py:6339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6339)

- **independent pass executor: 初回 live preflight には掛からない。** `start_independent_pass` と `blocked_on_ruling` は明示的に実装 scope 外で、preflight は固定 page 0 probe である。[amendment:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md:164)

したがって、U11 を理由に「1 request も出せない」とする解釈は成立しない。

## real 所見

1. **R1 — real: N3 は「記録」から report の受理関門へ変わっている。**

   プランは `pacing_observations` を必須 field にし、件数、WAL との完全一致、下限以上の間隔を validator で要求する。[plan.md:63](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:63) [plan.md:75](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:75) [plan.md:91](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:91)

   しかし N3 は non-blocking かつ `scheduling のみ` と固定されている。[preregistration:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md:1277) [preregistration:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md:1283)

   report digest は `report_sha256` 以外の全 field を束縛するため、この列は参照値にも入る。[related_work_search.py:5830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5830)

   **成果物への影響:** 同じ response 列と同じ `ready/unavailable/blocked` 列でも、間隔値だけで report/bundle が拒否され、certified 選択と後続参照が存在しなくなる。親の「受理集合は完全に同一」は偽である。

2. **R2 — real: limiter が測る時刻と実際の wire send 時刻が違い、短すぎる request 間隔を通せる。**

   プランの順序は `limiter.acquire`、観測記録、`begin_attempt`、budget、transport send である。[plan.md:39](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:39)

   `begin_attempt` は実送信前に WAL を書いて `fsync` する。実送信はその後である。[related_work_search.py:4815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:4815) [related_work_search.py:5026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5026) [related_work_search.py:5563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5563)

   成立条件は、先行 attempt の pre-send WAL 遅延が後続 attempt より長い場合である。limiter 上の時刻差が下限以上でも、実 send 間隔はその遅延差だけ短くなる。契約自身も intent 時刻を取得日時へ読み替えることを禁じている。[amendment:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md:156)

   **成果物への影響:** report の間隔 validator は緑なのに実 send 間隔が下限未満という成果物を受理でき、rate limit 応答と certified row 集合が変わる。

3. **R3 — real: 既存 resume は 429 を後続成功で `ready` に置換でき、§8.4 を潜脱する。**

   §8.4 は 429 を受けた query を `未完走` とする。[preregistration:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md:1046)

   ところが実行器は retry 対象を選び、resume で同一 stream を再送する。[related_work_search.py:5895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5895) [related_work_search.py:8169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8169) [related_work_search.py:8265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8265)

   report 再導出は attempt ごとに同じ row を上書きし、validator も最新 evidence だけを row status と突き合わせる。[related_work_search.py:6038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6038) [related_work_search.py:6513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6513)

   さらにプランがいう「既存 retry 上限」は実装されていない。sequence validator は最新失敗 stream の反復回数を数えず、実効上限は全体の 200000 attempt だけである。[plan.md:85](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:85) [related_work_search.py:5517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5517)

   **成果物への影響:** 429 evidence を保持したまま row は最終的に `ready` となり、`run_ready` の certified 選択へ入る。[related_work_search.py:6910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6910)

## refuted 所見

1. **F1 — refuted: pacing の追加だけで `declared_total` や一回取得時の row 分類式が変わる。**

   `_probe_response` は non-200 を `unavailable`、arXiv window 超過と lookup failure を `blocked` とし、`declared_total` は body から決める。[related_work_search.py:5694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5694) [related_work_search.py:5779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5779)

   プランはこの関数を変更しない。retry を使わず R1 の新 validator を通るという条件下では、同じ response 列に対する row 値は同一である。[plan.md:79](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:79)

2. **F2 — refuted: rate-limit header の記録値自体が registration seal に入る。**

   header は現在も page evidence に重複を保ったまま入り、その evidence/report digest に束縛される。[related_work_search.py:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2970) [related_work_search.py:5860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5860)

   これは D1206 が要求する実測来歴であり、値は row status の入力ではない。registration seal に入るのは runtime 観測値でなく、変更後 source の digest である。[README:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/README.md:669) [related_work_search.py:3437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3437)

3. **F3 — refuted: 計画された再登録が旧 4 凍結文書を書き換える。**

   実行器は旧登録と amendment を `read_bytes` して literal digest と照合するだけである。[related_work_search.py:3040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3040) [related_work_search.py:3427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3427)

   計画も旧文書を編集対象外とし、新日付出力だけを書く。[plan.md:101](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:101) [plan.md:139](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:139)

   **成果物への影響:** 静的に確認できる経路では旧 4 文書の bytes、参照、hash は変わらない。

4. **F4 — refuted: 「pacing 不在なら数百行が恒久的に未完走になる」という一般化。**

   最初の availability request が 429 の場合は exact 1 request で停止する。[related_work_search.py:6235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6235)

   逆に、それ以外の位置で non-200 が返っても loop は停止せず、残りの complete factory をすべて送る。[related_work_search.py:6335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6335) 登録上の complete factory は 1929 行なので、急性の影響は「数百」に限定されず、最大で残り全行へ及ぶ。[registration-preflight:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md:108)

   一方、R3 の resume が分類を上書きできるので「恒久的」でもない。親の主張は、**一走行中の被害規模を過小評価し、永続性を過大評価している。** 提示資料には「数百」を裏付ける raw locator/digest も無い。

## nit

- 09-01 記録 §0 は「live preflight と本走には後続実装と人間裁定が要る」と広く書き、§6.1 見出しも「live へ進む前」と書く一方、U11 本文は exact に `run-ready --live` だけを止める。[registration-preflight:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md:31) [registration-preflight:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md:132) 契約正本と具体的 command が優先するため P1 判定は変わらないが、記録単体では誤読を誘う。

## 裁定パッケージ候補

1. **N3 を「観測済み」と呼べる条件。** プランが保持するのは継承した固定値と、自分が発行した intent 間隔であり、索引側の安全な最小値そのものを測った値ではない。`Retry-After` が返らない走行では cooldown も観測できない。[plan.md:20](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:20) [plan.md:66](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:66)  
   裁定候補は「継承値への遵守確認を N3 完了と認めるか」。厳格側の判定は、live preflight 自体は許すが N3 は部分観測のままとする、である。N3 は non-blocking なので受理集合へ入れない。

2. **host 単位を bundle 内だけとするか。** state は bundle 内に置かれ、別 bundle/process を直列化しないことをプラン自身が認める。[plan.md:29](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:29) [plan.md:148](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md:148) N4 は共有単位を未確定としている。[preregistration:1284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md:1284)  
   裁定対象は「今回の live preflight 中、同一 login node の別 producer 不在を実行前事実として要求するか」。別 producer が存在する条件では、bundle 内観測が緑でも host 全体の間隔は保証されない。

## 総括

P1 に関する親の読みは正しい。U11 と未実装 3 件は、初回 live preflight の外部 request を全面禁止しない。

ただし段 2 プランはそのまま通してはいけない。少なくとも次の 3 点が real である。

- N3 を validator 条件へ入れて受理集合を変更する。
- intent 前後の時刻を wire issue 時刻として扱い、短すぎる実送信を通せる。
- 既存 resume が 429 を最新成功で `ready` に置換し、per-request retry 上限も持たない。

したがって「U11 により request 0 本」ではないが、現プランのまま live request を開始することも契約適合とは認定できない。静的検査のみで、編集・実行・commit は行っていない。