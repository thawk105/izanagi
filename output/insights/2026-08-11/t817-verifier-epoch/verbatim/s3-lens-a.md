# 段 3 敵対相談 — レンズ A（正しさ境界）

指定された親 brief と段 2 プランは全文読了した。関連実装と既存 WAL を静的に追跡した。pytest・build・ベンチ再実行は行っておらず、緑も主張しない。

## 所見 1 — BLOCKER: detached receipt は same-run witness を証明しない

- **(a) 壊れるもの:** t756 と同型の誤帰属を防げない。receipt が完全でも、stdout が対象 WAL attempt と同じ実行由来である保証がない。
- **(b) 根拠:** プランの receipt は lock SHA、WAL SHA、record 行、binary、stdout SHA、return code などを自己申告するだけである（[plan.md:124](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s2/plan.md:124>)）。現行 producer は subprocess stdout を捕捉・解析するが、WAL と stdout の双方に同一 execution nonce を記録しない（[pipeline.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:348)）。さらにプランが許す `trace_bin` は 16 桁の legacy display prefix であり、実装自身が identity check に使うなと明記している（[buildcache.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/buildcache.py:37)）。実際の P2-2 WAL にもこの短縮値しかない（[wal.jsonl:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl:2)）。
- **(c) 具体的な入力・状態:** 同じ binary・variant・workload を二度実行し、run B の stdout を保存する。receipt には run A の WAL SHA／行番号と、run B の stdout SHA／return code を書く。counter が一致すれば全 field が個別には検証可能だが、A と B を結ぶ producer-origin の値がないため通過する。full binary SHA を使っても証明できるのは実行物の同一性までで、process/run の同一性ではない。
- **(d) scope:** 根治は scope 外。producer が生成した一意な execution ID を WAL と stdout の双方へ出し、同一処理で永続化する必要がある。プランは stdout 永続化と pipeline 変更を明示的に除外している（[plan.md:205](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s2/plan.md:205>)）。過去記録には遡及的に追加できないため、別途裁定された署名／人手 attestation がなければ recovery は成立しない。

**成果物影響:** 別 run の counter が eligibility ledger の正証拠となり、不適格な genome が current certified accepted set・winner・レポートへ混入する。

## 所見 2 — HIGH: 実 corpus では positive branch が永久に到達不能

- **(a) 壊れるもの:** 「正しく束縛された stdout があれば必ず positive branch」という検査は、synthetic fixture では発火しても、現存する historical campaign では発火しない。
- **(b) 根拠:** pre-policy artifact は ledger の `created_from_commit` に固定された exact Git snapshot から読む（[artifact_admission.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:367)、[artifact_admission.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:388)）。一方、producer は stdout を一時領域で捕捉した後（[pipeline.py:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:928)）、その領域を削除する（[pipeline.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1064)）。親実測どおり、固定 snapshot 内に候補はない。
- **(c) 具体的な入力・状態:** 既存 P2-2 campaign 用の receipt/stdout を現在の commit に追加しても、gate は過去の `created_from_commit` を探索するため見えない。将来 campaign は WAL 内 `commit_witness` を使うため detached recovery を必要としない。したがって recovery-positive は synthetic snapshot 専用になる。
- **(d) scope:** 「既存は全除外」と明記して dead branch を削るなら scope 内。過去 snapshot 後に追加された receipt を権威化するなら、新しい detached-attestation trust root が必要で scope／裁定の拡張になる。

**成果物影響:** 実 campaign の accepted set は常に空のままで、ledger の recovery 成功件数は常に 0 だが、synthetic positive test だけが非恒真性を装う。

## 所見 3 — HIGH: 三重 gate を迂回する生きた consumer が残る

- **(a) 壊れるもの:** `assert_complete` / `replay_evaluate` / `winner_tied_set` を強化しても、旧 certified 相当の値を選択・報告する別経路が残る。
- **(b) 根拠:**
  - `p2_2_report` は WAL の build／bench／commit だけを収集し（[p2_2_report.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/p2_2_report.py:67)）、median 順で winner を選ぶ（[p2_2_report.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/p2_2_report.py:91)）。最後に summary を書いて成功終了する（[p2_2_report.py:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/p2_2_report.py:221)）。
  - critic digest も commit と LI だけで genome を並べ（[digest.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/critic/digest.py:216)）、先頭を fastest とする（[digest.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/critic/digest.py:475)）。
  - プランは `GenomeResult.certified` を歴史値のまま公開し、`load_landscape()` も全件を返す（[plan.md:160](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s2/plan.md:160>)）。現行 API も bool を直接公開している（[replay.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:47)）。
- **(c) 具体的な入力・状態:** wave 実装後に `p2_2_report` または critic digest を既存 P2-2 WAL に対して実行する。新しい assessment を一度も参照せず、旧 commit の winner／fastest が再生成される。
- **(d) scope:** scope 内で修正可能。両 consumer を ownership map に加え、共通 eligibility assessor を必須化する必要がある。P1 の「生きた選択」に含めない意図なら、P1 の境界自体が狭すぎるため裁定が必要。

**成果物影響:** replay が unavailable でも、`p2-2-summary.md` と critic 入力は旧 winner を現在値として再発行し、レポート間で accepted set が食い違う。

## 所見 4 — HIGH: epoch SHA が実際の gate 実装に束縛されない

- **(a) 壊れるもの:** 同じ `campaign_verifier_epoch` のまま acceptance semantics を変更できる。epoch が「適用された正しさ規則」の識別子にならない。
- **(b) 根拠:** プランは policy JSON の SHA を epoch ID とする（[plan.md:22](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s2/plan.md:22>)）が、現行の exact enforcement closure は 8 path 固定で、新設予定の JSON と `verifier_selection.py` を含まない（[campaign_lock.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:29)、[campaign_lock.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:168)）。live／committed binding 検査もその closure だけを比較する（[contract_loader_binding.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/contract_loader_binding.py:319)）。
- **(c) 具体的な入力・状態:** policy JSON を変更せず、`verifier_selection.py` の missing-witness 分岐を eligible に変える、または batch consistency check を削る。campaign ID と declared epoch は同一だが accepted set が拡大する。
- **(d) scope:** repo 内で修正可能だが、実装前の設計修正が必要。policy artifact に executable enforcement sources の SHA を含めるか、後方互換性を保つ versioned closure に JSON と selector を追加すべきである。

**成果物影響:** 同一 epoch・同一 campaign identity の下で ledger 判定、winner、レポート値がコード版ごとに変化する。

## 所見 5 — HIGH: `record_epoch` と current-shape witness は payload 偽造に弱い

- **(a) 壊れるもの:** 記録の形を根拠に新 epoch／recorded witness と分類すると、verifier が生成していない `verify_done` を eligible にできる。
- **(b) 根拠:** post-policy admission は attempt topology と build receipt／contract を検査する（[artifact_admission.py:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:717)）が、topology validator は build／commit／abort の attempt binding を扱い、`verify_done` の producer-origin や意味を検証しない（[wal.py:1029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/wal.py:1029)）。正規 producer が witness を作る処理は別途存在する（[pipeline.py:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:982)）が、reader はその処理を通ったことを証明できない。
- **(c) 具体的な入力・状態:** 正当な current-epoch lock と build receipt を持つ WAL に、`certified:true`、整合する counter、形だけ正しい `commit_witness` を含む `verify_done` を物理的に commit 前へ挿入する。WAL SHA は変更後のファイルから再計算されるため、それ自体は外部の期待値にならない。declared current epoch と current-shaped record の両方が揃っても、実行 provenance はない。
- **(d) scope:** shape を診断情報だけに限定するのは scope 内。完全な防止には producer に束縛された append-only receipt、署名、または WAL hash chain が必要で、現プランの WAL-format 非変更境界を越える。

**成果物影響:** 細工した `verify_done` が current eligible set に入り、certified ranking・winner・ledger の証拠参照を偽造できる。

## 所見 6 — MEDIUM: P1 の「凍結済みだから歴史事実」は表示上成立しない

- **(a) 壊れるもの:** bytes を不変にしても、それを E0 歴史成果物と識別する current-status overlay がないため、既存成果物は引き続き現行の成功証拠として読める。
- **(b) 根拠:** P2-5 summary は P2-2 WAL からの再計算一致を provenance として記録する（[p2-5-summary.json:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-5-summary.json:528)）。phase doc は現在も P2-5 完了と数値結果を掲げる（[phase2.md:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/docs/phase2.md:113)）。decisions も P2-2 replay を certified 値として扱う（[decisions.md:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/docs/decisions.md:376)）。
- **(c) 具体的な入力・状態:** 新 gate が全 P2-2 を current-ineligible にした後、利用者やツールが既存 summary／phase doc を直接読む。そこには E0-only／current unavailable の表示がなく、従来の結論を現行結果として採用できる。
- **(d) scope:** 凍結 bytes を変更せず、隣接する current-status index／revocation overlay と reader 側参照を追加すれば repo 内で直せる。ただし現プランの ownership 追加が必要。

**成果物影響:** live accepted set は空なのに、summary・phase doc・decision reference は旧数値を有効な certified 成果として提示し続ける。

## 所見 7 — MEDIUM: N1 の「571 件全除外」は単位を混同している

- **(a) 壊れるもの:** eligibility ledger の件数、reason、attempt 対応が不正確になる。
- **(b) 根拠:** 親 brief 自身が `verify_done` 572 件と commit 459 件を別々に計上している（[brief.md:21](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s1/brief.md:21>)）一方、N1 は certified verify record 571 件をそのまま除外単位にしている（[brief.md:65](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s1/brief.md:65>)）。同 brief には 111 commit が legacy と S2 の二検査を持つことも記録されている（[brief.md:53](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t817-verifier-epoch/s1/brief.md:53>)）。replay の選択単位は committed variant である（[replay.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:137)）。
- **(c) 具体的な入力・状態:** 一つの attempt に legacy と S2 の二つの `verify_done` がある場合、571 ベースの台帳では同じ committed result を二重に「除外」する。commit に到達しなかった verify record も混入し得る。
- **(d) scope:** scope 内。assessment 主単位を committed attempt にし、複数 verifier pass はその evidence 子要素として記録すべきである。

**成果物影響:** accepted set が空という集合上の帰結は同じでも、ledger の除外総数と record／reason 参照が誤る。

## 補足

- M1 の「既存 WAL に `commit_witness` 付き記録は 0」は、全 30 WAL の読み取り結果と整合した。
- M2／M3 を覆す P2-2 stdout は、現 worktree と到達可能な `output/campaigns` 履歴からは発見できなかった。ただし親の raw-regex 調査は JSON escape、圧縮物、任意名 blob を網羅しないため、「存在しない」の一般証明ではない。
- `verifier_epoch=None` 時に key を出さないという設計は、既存の optional screening binding と同型であり、実装が本当に omission を維持する限り歴史 campaign-id の byte 不変性を満たし得る。

## 総括

**NO-GO。**

最大の所見は、提案された detached receipt が WAL attempt と stdout の **same-run 因果関係を証明しない**ことである。Git snapshot、WAL SHA、stdout SHA、binary SHA はそれぞれの bytes を固定するだけで、同じ process が生成したことを束縛しない。このまま positive branch を認めると t756 の blocker を再導入する。さらに実 corpus ではその branch は到達不能で、既存 report／critic consumer は新 gate を迂回する。producer-bound witness を追加できない現 scope では、歴史 record を一括 current-ineligible とし、全 live consumer と成果物 status を同じ gate に束縛する設計へ戻す必要がある。