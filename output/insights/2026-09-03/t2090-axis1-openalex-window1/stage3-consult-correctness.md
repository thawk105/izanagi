## 所見 (must-fix)

1. **S1 は凍結済み §4.1 の発行 gate をそのまま緩める。U12 の「所有 task」を決めても、この方式までは承認されない。**

   凍結契約は `remaining - 30 >= 直近観測 cost` の場合だけ発行すると定め、窓が明ける瞬間を観測していないことも明記している。[旧 amendment §4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md:201) に対し、プランの `balance_ok or window_elapsed` は `remaining=35, cost=10` を拒否側から受理側へ移す。[stage2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/artifacts/stage2-plan.md:16)

   repo 内の最も強い裏取りは、旧生応答の `observed_at=2026-08-29T14:54:25.112223Z` と `reset=32737` から導く期限が `2026-08-30T00:00:02.112223Z` になる点である。[page evidence](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/output/insights/2026-08-29_t2033-axis1-retake/bundle/pages/AX1-20260829-E1-Q1@openalex_p0.a01.json:323) 小さい値なので Unix epoch 絶対値ではなく、境界までの秒数という解釈とは整合する。しかし、reset 後に `remaining` が回復した観測はなく、契約自身が「窓が明ける瞬間は観測していない」としている。よって式は有力な仮説だが、凍結済み発行規範ではない。

   意味を誤れば、期限を早く見積もる場合は予約以下で HTTP を発行して 429、絶対時刻など別の意味なら期限が遠未来になり永久停止する。

   **放置時の成果物影響:** 同じ低残量観測が、旧実装では `paused_quota`・HTTP 0、新実装では WAL・raw・page evidence を持つ HTTP 1 以上へ変わり、429 なら条件 6、leaf state、checkpoint、manifest digest も変わる。

2. **P2 は契約文面に反する。U13 は明示された取得開始前条件である。**

   U13 は太字で「継続取得を始める前に方式を決める必要がある」と書かれている。[amendment §8 U13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:215) 「人間の裁定へ返す項目」に置かれていても、この逐語を非規範の注記へ降格させる根拠はない。§7 も、検査器が旧生応答の再包装を拒否できないと明示している。[amendment §7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:197)

   **放置時の成果物影響:** 登録前に取得された raw が新 epoch の page・ledger・manifest に算入されうるため、証拠 bundle の時間的 provenance と受理集合が変わり、leaf の完走判定が新規 HTTP ゼロでも前進しうる。

3. **P3 は entry 1169 の案と文字どおり同じ操作ではないが、証明上は同じ穴を残す。**

   今回は fresh root で、S1 commit 後に runner を実行する予定なので、「既存 manifest の SHA だけ張り替える」旧案とは運用構造が違う。一方、検査器が確認する commit 一致は checkpoint と manifest の間だけである。[validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1189) page identity と ledger の `registration_commit` は形式検査だけで、manifest の値との一致を検査していない。[validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1300)

   したがって、旧 raw を使って新 epoch の page・ledger wrapper と manifest を再生成する反例は残る。M3 は旧 Q1 raw が新条件 1 を通ることまで示しており、反例を弱める材料ではなく強める材料である。entry 1169 が拒否した「内部自己整合を外部の登録後取得と取り違える」形と同型である。[worklog-1169.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/materials/worklog-1169.md:22)

   **放置時の成果物影響:** manifest は S1 commit、新 wrapper は任意 commit、raw は登録前取得という bundle が内容検査を通りうるため、`registration_commit` の参照値だけ新しくなり、証拠の実取得時点は変わらない。

4. **`permits_next` の純粋関数変更だけでは、発行権が原子的にならない。**

   runtime lock は quota の読み出し後に解放され、HostLimiter も HTTP 前に解放される。[runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:629) [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1703) このため、複数 leaf process は同じ失効観測を全員受理できる。また最初の probe が transport exception になれば、同じ失効観測で retry も発行できる。

   さらに resume は checkpoint 内の quota を発行 gate に使わず、bundle の `state/runtime.json` だけを読む。runtime が欠落すると空 state を作り、checkpoint が低残量を記録していても発行する。新規 root も常に quota 未観測から始まるため、bundle 外の probe や別 bundle の消費は機械的には共有されない。

   **放置時の成果物影響:** 失効 1 回につき同時 process 数・retry 数だけ `issued` WAL と request が増え、予約を割る 429、競合した runtime 値、余分な raw/page/checkpoint が manifest に入る。

5. **`_merge_quota` は古い reset を新しい観測時刻へ付け替える。**

   現行 merge は timestamp と request ID を常に現在応答から取り、欠落した `reset_seconds`、remaining、cost は前応答から継承する。[runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:688) 例えば失効後の 200 応答が reset を返さなければ、古い reset 秒数が新しい `observed_at_utc` を起点とする値に変わる。プランの「reset 欠落なら停止」は、実 production 経路では成立しない。

   **放置時の成果物影響:** runtime、page の quota、checkpoint が実応答に存在しない reset を現在応答の観測として記録し、後刻その合成値で HTTP を誤発行するか、余分な時間停止する。

6. **Python 3.10 では writer の末尾 `Z` を `datetime.fromisoformat` が直接読めない。**

   この環境は Python 3.10.12 であり、`datetime.fromisoformat("2026-09-02T00:00:00Z")` は `ValueError` になった。プランが明記する writer 形式と parser が、そのままでは接続しない。[stage2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/artifacts/stage2-plan.md:38) `Z` を厳密に確認してから `+00:00` へ変換する仕様が必要である。

   **放置時の成果物影響:** 全ての実在 runtime 観測が失効不能になり、HTTP 0 の `paused_quota` checkpoint が増えるだけで bundle は永久に未完走となる。

7. **S2 の「pass 1 だけ」と「OpenAlex を取り切る」「最低 152 pass」が矛盾する。**

   78 leaf のうち 74 leaf は独立第 2 走が必須だが、scope は pass 1 のみとしている。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/brief.md:86) pass 1 完了後、それらは `branch_complete` ではなく `pass_complete` と第 2 走 checkpoint を返す。[runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2217)

   **放置時の成果物影響:** 74 leaf は pass 1 の raw・ledgerを持っても未完走で、OpenAlex retrieval の受理集合、残 leaf 数、再開点が brief の「取り切る」という完了報告と一致しない。

## 所見 (nit / backlog)

- **M3 は 1 件の旧 Q1 page にだけ成立する。** 他の 77 leaf、新取得、未知 key、将来の OpenAlex 応答形には一般化できない。  
  **放置時の成果物影響:** 別 leaf の `completion[1]` が偽になれば、その leaf は `blocked_on_ruling`、後続 cursor なし、`retrieval_complete=false` になる。

- **M4 の 200、10 credit、97 request は 1 応答からの planning estimate である。** 凍結契約自身が cursor、複雑 query、429/503、retry の cost 同一性を未確認としている。  
  **放置時の成果物影響:** 実 cost が 10 より大きければ停止位置、最終 remaining、page 数、checkpoint 番号が見積りと変わる。

- **M7 の 3.1 秒は 1 起動の所要時間であり一般値ではない。** 正しさには影響しないが、78 leaf 分の計画時間へそのまま掛けられない。  
  **放置時の成果物影響:** 証拠値は変わらず、実行記録の所要時間見積りだけが外れる。

- **U14 と public API は未防護である。** CLI は既存 root を拒否せず、`run_leaf` / `resume_from_checkpoint` は公開 API から `preflight=True` を受け付ける。[run_axis1_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:110) [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1519)  
  **放置時の成果物影響:** 誤 root への追記や未検証 commit 名の artifact が作られうる。正規 CLI 限定なら限界として残せるが、production surface の明記が必要である。

## 親の provisional 裁定への判定

| 裁定 | 判定 | 理由 |
|---|---|---|
| P1 | **部分支持** | T-2090 が U12 の所有 task になることは、ユーザー依頼と entry 1169 から支持される。ただし所有決定は `observed_at + reset` 方式の承認でも、凍結 §4.1 の改訂でもない。 |
| P2 | **棄却** | U13 は「継続取得を始める前」と明記された前提条件であり、注記扱いはできない。 |
| P3 | **条件付き棄却** | S1 commit を実行 commit にする運用自体は必要だが、それだけで証拠鎖や登録後取得は証明されない。U13 解決後の commit 選択としてのみ採用可能。 |
| P4 | **支持** | ユーザー明示と整合する。ただし「wave の失敗ではない」と「成果物の `retrieval_complete` / `axis_complete` は偽」を分けて記録する必要がある。 |

## 恒真な保証の検査

| テスト主張 | 判定 |
|---|---|
| 失効済み観測が最初の HTTP を許す正例 | expiry branch の削除では落ちるので有効。ただし初回 quota gate 全体を削除しても単独では緑になる。未失効負例との組でのみ保証になる。 |
| 時計巻き戻り負例 | `reset >= 0` なら `now < observed_at` は自動的に `now < observed_at + reset` でもある。明示的な巻き戻り conjunct を削除しても緑で、当該保証は恒真に近い。 |
| reset 欠落負例 | `reset=None` を直接保存する fixture だけでは、`_merge_quota` が旧 reset を新時刻へ付け替える production 経路を検査しない。 |
| 429/503 既存テスト | 失効した旧観測を持たない fresh bundle なので、失効 probe 後の retry 多重発行を検査しない。 |
| 全体 | 並行 leaf、失効後 transport exception、runtime 欠落時の checkpoint fallback、別 bundle、bool・NaN・Infinity、3 gate 個別の mutation が不足する。 |

追加正例は Python 3.10 の `Z` 非対応を実際には検出するため、その点では恒真ではない。pytest は実走しておらず、緑とは判定していない。

## 裁定パッケージ候補

1. **U12 と凍結 §4.1 の改訂**

   推奨案は「期限経過後に一般発行を許す」のではなく、同一 quota authority につき原子的な 1 本だけを再観測 probe として許す方式。reset の意味、時計、safety margin、0 の扱い、probe 失敗時は再試行しないこと、完全な quota tuple を同じ応答へ束縛することを契約化する。これには runner だけでなく runtime ownership、merge、checkpoint fallback、並行テストが scope に入る。

2. **U13 の anti-replay 方式**

   登録 commit、完全な request bytes、取得時刻、response digest を外部事実へ束縛する受領証・nonce・追記専用登録のいずれかを人間が選ぶ。少なくとも現行 `registration_commit` field をその代替と扱わない。

3. **quota state の射程**

   無認証枠が bundle 単位、process 単位、IP 単位のどれかを裁定し、それに一致する単一の発行 lease を置く。新規 root、別 bundle、checkpoint 内 quota、runtime 欠落を同じ決定に含める。

4. **取得完了の意味**

   「本 wave は pass 1 のみ」か「74 leaf の第 2 走まで含めて OpenAlex を取り切る」かを固定する。前者なら成果物名を部分取得とし、残り 74 pass と checkpoint を必ず記録する。

5. **U14/U15 と API surface**

   U14 は新規 root の create-only 強制を採るか、運用確認に留めるか。U15 は現 wave の直接 blocker ではなく、一括 Git blob 検査を先行させる backlog でよい。併せて production entry を CLI 限定と宣言するか、公開 API の `preflight=True` を閉じるかを決める。

## 総括

現プランは **NO-GO**。条件 1〜6 の関数自体は変更しないが、quota gate の受理集合を広げることで、生成される raw・page・ledger・checkpoint と、それらを完走判定へ算入できる入力集合が間接的に変わる。

最低限、U13 を解決し、U12 の方式を凍結 §4.1 に明文化し、原子的な 1 回 probe・quota merge・runtime/checkpoint/root の射程を閉じる必要がある。P4 だけはそのまま採用できる。書き込みと pytest 実走は行っていない。