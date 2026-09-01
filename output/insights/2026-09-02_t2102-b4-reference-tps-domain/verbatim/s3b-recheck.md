## 争点 1 — 恒真性

判定は **部分的に維持される**。

JSON 十進 token を `Decimal` に変換する検査と、有限 `float` を `Fraction` に戻す検査が有限十進について恒真である、という数学的批判自体は追加実測 D でも変わらない。[measure_reference_tps_domain.py:59](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:59) [measure_reference_tps_domain.py:81](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:81)

ただし、「その恒真なゼロの背後に、正当な upstream の非有限 exact 比が隠れているかもしれない」という批判の含意は維持できない。

- `benchparse` は stdout の字句を一度 `float` に変換し、fallback も `float / float` を返す。exact ratio を返す経路ではない。[benchparse.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/benchparse.py:39) [benchparse.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/benchparse.py:53)
- pipeline はその `float` 系列の median を bench payload と COMMIT の `fitness_tps` に保存する。[pipeline.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/pipeline.py:835) [pipeline.py:1739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/pipeline.py:1739)
- WAL は有限 `float` のみを許し、通常の JSON 数値として書く。[wal.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/wal.py:310) [wal.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/wal.py:397)
- ledger は exact ratio を形式上受理するが、authoritative producer を作成・特定しないと明記している。[p3_b4_analysis_ledgers.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:3) issuer も caller schedule が authoritative population に束縛されないと明記する。[p3_b4_prerun_issuer.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:52)

repo-wide の非 test constructor 調査でも、実在する producer はない。見つかる直接構築は prereg consumer 自己検査用の `_behavior_attempt` だけである。[p3_b4_analysis_prereg_consumer.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:757)

したがって、**記録外に成立する別の「正当な upstream exact 経路」は確認できない**。任意の `(1,3)` を issuer に渡せることは transport 経路であって、正当な upstream 出力ではない。

成果物影響: 恒真な検査を exact-domain の証明と呼ぶのは不正確だが、存在しない exact producer を仮定して (b) を残すと、未認証値を理由に registry の受理集合または consumer を変えることになる。

## 争点 2 — 列挙の完全性

判定は **部分的に維持される**。

追加実測 B により、「repo 内 2 root しか見ておらず、`/work/1/SFC/tanab` 内の external campaign root を落としている」という先行批判は無効化された。5541 WAL の列挙は、その subtree 内については大幅に強化されている。

しかし、`layout.py` の契約上、まだ拾えていない正規の所在がある。

- official root は明示 `output_root`、または `IZANAGI_OFFICIAL_OUTPUT_ROOT` で決まる。[layout.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:257) [layout.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:412)
- 条件は絶対 path・repository 外・実効 UID 所有などであり、`/work/1/SFC/tanab` 配下に限定されない。[layout.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:323)
- WAL の所在は `<resolved-root>/campaigns/<id>/runs/wal.jsonl` である。[layout.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:203) [layout.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:248)

したがって、例えば `IZANAGI_OFFICIAL_OUTPUT_ROOT=/scratch/...`、`/tmp/...`、別 `/work/...`、または同等の明示引数は契約上成立しうるが、`/work/1/SFC/tanab` 走査には入らない。現在の shell で env が未設定でも、過去の明示引数や別 process の pin は復元できない。

追加実測 C も実際のコマンドは `/work/1/SFC/tanab -maxdepth 8` であり、文字どおりのマシン全域ではない。[measurement-addendum.md:33](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measurement-addendum.md:33) B-4 `publication_root` も任意の canonical absolute path であり、layout root への従属はない。[p3_b4_prerun_issuer.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:169) [p3_b4_prerun_issuer.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:707)

ゆえに「このマシンのどこにも存在しない」「列挙は完全」は証明されていない。

成果物影響: 未走査 root に provenance-valid な snapshot、receipt、registry があれば、件数・参照一覧・D1344 の判断根拠から欠落し、report と台帳の参照集合が変わる。

## 争点 3 — D1344 の充足条件

判定は **先行レンズの読みが維持される**。D1344 の決定文に整合するのは、完全な scheduled batch を実走前に列挙する読みである。

D1344 は「予定されている scheduled input すべての `reference_tps`」を列挙し、それが正当な upstream 出力か確認すると明記する。[verbatim-D1344.md:3](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/verbatim-D1344.md:3) 理由欄も判断材料を production 値域そのものとしている。[verbatim-D1344.md:9](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/verbatim-D1344.md:9)

producer が無いため scheduled batch が未実体化であることは、「測定対象が現在空である」というより、D1344 が要求した対応付けをまだ構成できない状態である。特に、成功する B-4 publication は 201 以上の eligible attempt を必要とするため、空 batch は issuer で `design_not_feasible` になる。[p3_b4_prerun_issuer.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:794)

この読みは B-4 実走まで待つことを要求しない。順序は次のとおりである。

1. caller が完全な `scheduled_inputs` と planned result paths を渡す。
2. issuer が batch hash を確定する。
3. registry を封印し、manifest を生成する。
4. その後に planned result が実行される。

実装も `issue_b4_prerun_publication()` が scheduled batch を先に受け取り、registry sealing と manifest generation を publication 内で行う。[p3_b4_prerun_issuer.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:707) [p3_b4_prerun_issuer.py:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:770)

したがって、必要なのは「B-4 の実走」ではなく、**authoritative producer に束縛された完全な pre-seal batch の実体化**である。現状それが無いことは先行所見を無効化しない。

成果物影響: historical throughput の広い標本を scheduled batch の代用にすると、対応する snapshot・receipt・`PerfConfig`・`env_tag` を固定しないまま D1344 を確定し、registry の受理集合と後続レポートの参照を変える。

## 争点 4 — 結論の向き

証拠の方向だけなら **(a) を支持する**。

- 4034 件の throughput/TPS 系 field に非有限十進なし。
- `/work/1/SFC/tanab` 内の 443911 観測にもなし。
- 現行 benchmark → pipeline → WAL 経路は `float` 出力。
- 正当な非有限 exact upstream producer は確認できない。

一方、**(b) を支持する production 証拠は 1 件もない**。ledger が exact ratio 型を受理すること、consumer 側の exact-rational 設計に一貫性があること、任意 caller が `(1,3)` を渡せることは、いずれも正当な upstream 出力の実在証拠ではない。

ただし、争点 2・3の欠落により、D1344 の手続上「ゼロなら (a)」を確定するための完全列挙は未達である。結論は次の二層に分かれる。

- 証拠の向き: **(a)**
- D1344 に基づく択一確定: **まだ不可**
- (b) の実在証拠: **0 件**

成果物影響: この区別を落として (a) を確定すると、未列挙 root または未実体化 schedule を確認せず registry の受理集合を縮め、certified 選択・レポート・台帳の生成可能集合を変える。

## 先行 2 レンズの所見の維持・無効化の一覧

| 先行所見 | 判定 | 放置した場合の成果物影響 |
|---|---|---|
| `commit.fitness_tps` は scheduled `reference_tps` 母集合そのものではない | **維持** | schedule と provenance の対応なしに registry 受理集合を決める |
| repo-local 2 root では external root が欠落する | **部分的に無効化**。`/work/1/SFC/tanab` 内は B が補ったが、契約上の全 root は閉じていない | 未走査 root の参照・件数が report/台帳から欠落する |
| Decimal-token / float-roundtrip 判定は恒真 | **維持** | 検査件数を exact-domain の非自明な証明と誤記する |
| 恒真なゼロの背後に正当な非有限 exact 値が隠れうる | **無効化**。正当な exact producer・経路なし | 仮想値を根拠に (b) を選ぶと未認証参照を受理対象にする |
| arbitrary caller ratio は正当な upstream 出力ではない | **維持・追加実測 D で強化** | synthetic 値が certified report の参照 provenance に混入する |
| sealed registry が無ければ原理的に測れない、は強すぎる | **維持**。完全な pre-seal batch で測定可能 | 不要に B-4 実走後まで判断を延期する |
| 現在の 0 件は D1344 の完全 scheduled-input 実測ではない | **維持** | unsupported な (a) を確定し、registry・report・台帳の生成集合を縮める |
| exact consumer 側には設計上の整合性がある | **部分的に維持**。設計論としては残るが、(b) の実在証拠ではない | 設計上の好みを実測結果と取り違えると D1344 の択一を逆転させる |

実装境界、M12、closure pin など、この 4 争点外の所見は再判定していない。

## 総括

先行批判は全面的には崩れない。

- 恒真性の数学的批判は残るが、隠れた正当な exact producer という含意は崩れる。
- `/work/1/SFC/tanab` 内の root 欠落批判は B で解消したが、`layout.py` と任意 `publication_root` が許す全所在の列挙にはなっていない。
- D1344 は B-4 実走を要求しないが、authoritative な完全 pre-seal batch の列挙を要求する。現状は未充足。
- production 証拠は一貫して (a) 向きで、(b) の証拠は 0 件。ただし D1344 に基づく (a) の確定条件にはまだ届いていない。

静的検査のみ実施し、pytest は実走していない。