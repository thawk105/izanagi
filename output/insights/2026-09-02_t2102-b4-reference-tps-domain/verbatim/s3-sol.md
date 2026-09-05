## 母集合の取り違えの検査

判定は **real**。親の `commit.payload.fitness_tps` は D1344 の母集合そのものではなく、現時点では上位集合であることも証明されていない。

- §5.1.1 は、各 block の precursor から遡った最初の certified snapshot と、`PerfConfig`・`env_tag` が一致する receipt の throughput を要求する。[verbatim-prereg-5-1-1.md:38](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/verbatim-prereg-5-1-1.md:38)
- 運用上の母集合は、発行前なら完全な `scheduled_inputs` の `reference_tps`、発行後なら sealed registry の `scheduled_attempts[*].reference_tps` である。型の入力点は [p3_b4_analysis_ledgers.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:123)、issuer の受取点は [p3_b4_prerun_issuer.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:707)、封印は [p3_b4_analysis_ledgers.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:662)。
- manifest は eligible 行の先頭 201 件だけを registry からコピーするため、D1344 の「予定された input すべて」の代用にはならない。[p3_b4_analysis_ledgers.py:1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:1063)
- 親が引用した raw-record producer の `fitness_tps` は各 on/off arm の観測 `throughput` である。[p3_b4_raw_record_producer.py:1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_raw_record_producer.py:1320) `reference_tps` は別に manifest row から取得される。[p3_b4_raw_record_producer.py:1538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_raw_record_producer.py:1538)

`commit.fitness_tps` を上位集合とするには、全 scheduled row が走査済み COMMIT のいずれかから exact に導出されたことを示す写像が必要だが、ledger 自身は authoritative producer を作成・特定しないと明記する。[p3_b4_analysis_ledgers.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:3) repo-wide の constructor/caller 調査でも、production の祖先探索 producer は見つからず、非 test の constructor は prereg consumer の自己検査用 behavior fixtureだけだった。[p3_b4_analysis_prereg_consumer.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:757)

現存 production 母集合内に確認済みの非有限十進値はない。ただしこれは「0 件を正しく測った」のではなく、「母集合をまだ実体化・認証できていない」という状態である。

影響: この取り違えを放置すると、履歴 WAL の値域を根拠に registry の受理集合を縮め、実際の予定 batch とその参照 provenance を測らずに D1344 の択一を確定してしまう。

## 列挙の完全性の検査

判定は **real**。2 つの repo-local `output/` は、現行の公式 campaign 出力の完全な root 集合ではない。

- 実測が走査したのは明示された2 rootだけである。[measurement-1.json:467](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measurement-1.json:467)
- 現行の official campaign は `--output-root` または `IZANAGI_OFFICIAL_OUTPUT_ROOT` が必須で、しかも repository 外の絶対 path を要求する。[layout.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:323) [layout.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:412) WAL はその外部 root の `campaigns/<id>/runs/wal.jsonl` に置かれる。[layout.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/layout.py:248)
- B-4 publication 自体も caller 指定の絶対 `publication_root` に、`scheduled-attempt-registry.jsonl`、`analysis-manifest.json`、`prerun-issuer-receipt.json` を書く。[p3_b4_prerun_issuer.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:45) [p3_b4_prerun_issuer.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:715)
- 測定スクリプトは exact filename `wal.jsonl` だけを再帰列挙する。[measure_reference_tps_domain.py:111](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:111) ファイルを開けない場合も無記録で除外する。[measure_reference_tps_domain.py:125](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:125)

親の2 root内については、公式 B-4 registry、manifest、issuer receipt、および圧縮 `wal.jsonl.*` はいずれも 0 件だった。圧縮成果物の見落としが現在の結果を変えた証拠はない。また、未 COMMIT record 自体は certified snapshot throughput ではないため、単に abort・途中 WAL を加える必要はない。

一方、外部 official root と任意の B-4 publication root は実在する正規経路であり、親の走査範囲外である。したがって上位集合論法は成立しない。

影響: 外部 root に provenance-valid な schedule/publication があれば、親の件数・参照一覧・D1344 の択一根拠から丸ごと欠落し、report と registry の参照集合が一致しなくなる。

## 数え方の欠陥

`has_finite_decimal()` 自体は正しい。既約 `Fraction` の分母から 2 と 5 を除き、1 になるかを見る判定は有限十進有理数と正確に一致する。[measure_reference_tps_domain.py:26](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:26)

問題はその前段である。

- **real — Decimal token 判定は恒真。** JSON 数値 literal は有限個の十進数字と指数で表されるため、`Fraction(Decimal(token))` は定義上必ず有限十進になる。[measure_reference_tps_domain.py:66](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:66) 上流の exact `1/3` が `0.3333333333333333` へ丸められていても「有限」と報告する。
- **real — float 往復判定も恒真。** 任意の有限 IEEE-754 float は分母が 2 の冪の有理数なので、`Fraction(float(token))` は常に有限十進である。[measure_reference_tps_domain.py:81](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:81) これは「丸め後の float が有限十進」を保証するだけで、元の exact 値との一致は保証しない。
- **real、ただし現コーパスでの発火は未確認 — `raw_token` は構造 parser ではない。** 最初の文字列一致を採るため、先行する nested key や duplicate keyがあれば `payload[key]` と別の tokenを返す。[measure_reference_tps_domain.py:35](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/measure_reference_tps_domain.py:35) 測定側は `json.loads` を使い duplicate-aware な公式 `wal.parse_line()` を通さない。公式 parser は duplicate keyを拒否する。[wal.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/wal.py:352)
- 現行公式 writer は空白なし JSON、非有限 float禁止であり、current pipeline の COMMIT payloadでは `fitness_tps` が先に挿入される。[wal.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/wal.py:397) よって `raw_token` が今回の852件を実際に誤読した証拠まではない。

なお registry の exact ratio は JSON数値1個ではなく `[numerator, denominator]` で保存される。[p3_b4_analysis_ledgers.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_ledgers.py:279) この母集合を現在の `Population.add()` に渡すと、listとして `non_numeric` に落ち、非有限十進判定へ進まない。

影響: 現行の2判定は、丸め済みの値しか見ないことで結果を必ずゼロ側へ寄せ、正当な exact ratio が存在した場合でも registry 縮小を誤って選びうる。

## 「正当な upstream 出力」の範囲

確認結果は次のとおり。

| 経路 | 実際の数値型・処理 | 判定 |
|---|---|---|
| `throughput[tps]` | raw文字列を `float()` 化 | 現行出力は float |
| `commits / extime` fallback | 両方を先に float化して float除算 | 現行出力は float |
| runner | `throughput_tps()` の floatを蓄積 | float |
| calibrator median | float列を `statistics.median` / float加算 | float |
| pipeline COMMIT | median floatを `fitness_tps` にコピー | float |
| B-4 issuer | callerの `Fraction/int/(n,d)` を exact ratioとして封印 | floatを経由しないが、出所を認証しない |

直接経路と fallback は [benchparse.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/benchparse.py:39) および [benchparse.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/benchparse.py:53)。runner はその値を保存する。[runner.py:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/runner.py:1216) median と COMMIT は [analyze.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/calibrator/analyze.py:208) と [pipeline.py:1739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/pipeline.py:1739)。

したがって「現行 benchmark → pipeline → WAL の受理済み出力は有限 float」という狭い命題は確認できる。`commits / extime` の数学的な商が 1/3 になりうるとしても、現行実装の出力は exact ratioではなく、既に floatへ丸められた値である。

一方、issuer/ledger は `Fraction | int | tuple[int,int]` を受理する。[p3_b4_analysis_contract.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_analysis_contract.py:94) 実際、testには `(1,3)` をissuerへ通し、raw producerでだけ名指し拒否する経路がある。[test_p3_b4_raw_record_producer.py:1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/tests/test_p3_b4_raw_record_producer.py:1138)

ただし、これを「正当な upstream 出力」と扱う段2の主張は **refuted**。issuer自身が caller schedule は external authoritative population に束縛されていないと明記する。[p3_b4_prerun_issuer.py:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range/orchestrator/campaign/p3_b4_prerun_issuer.py:8) 任意の `(1,3)` と形式上正しいhashを渡せることは、技術的な registry 受理経路を示すだけで、§5.1.1 の祖先 snapshot・receipt・`PerfConfig`・`env_tag` を満たす upstream provenanceを示さない。

確認済みの正当な非有限十進 upstream 出力は、今回の資料内には存在しない。将来の exact producer は可能性にすぎず、実在・予定された実装としては確認できなかった。

影響: 任意 caller値を「正当」と誤認すると、syntheticな `(1,3)` だけを理由に consumer変更を要求し、certified reportへ未認証の参照 provenanceを持ち込む。

## 結論の恒真性

親の「0 件」は、かなりの部分で測定対象の表現により自明に決まっている。

- JSON decimal tokenを `Decimal` として読む検査は、JSON数値を選んだ時点で必ず有限十進。
- floatへ往復する検査は、有限 floatを選んだ時点で必ず有限十進。
- `commit.fitness_tps` は upstream exact値ではなく、既に float化・集計・JSON化された終点である。

循環を破る測り方は次である。

1. 実際に発行予定の完全な `scheduled_inputs` を、封印前の exact型のまま列挙する。発行済みなら `load_scheduled_attempt_registry()` で全 `scheduled_attempts` を読む。`None` は別件数とし、manifestの201件へ縮めない。
2. 各非 `None` 値を `Fraction` にして、既約分母から2と5を除く。JSON decimalやfloatへ変換しない。
3. 各値について、ancestor探索結果、snapshot hash、receipt hash、`PerfConfig`、`env_tag` が一致する upstream資料への対応を確認する。arbitrary caller値は数えない。
4. upstreamの意味が raw `commits/extime` の exact商だと定義される場合だけ、raw lexemeから exact商を作る。現行 `throughput_tps()` のfloat出力を意味とするなら、その事実を測定結果と分離して記す。
5. root一覧は、実行に使う official/exploration output rootとB-4 publication rootから得る。repo-local `output/` を既定の全体集合としない。

「sealed registryが0件だからD1344は原理的に未充足」という読みは強すぎる。sealed artifactは必須ではなく、発行予定の完全な pre-seal batchを列挙すれば充足可能である。しかし現時点ではその batchも、祖先からそれを生成・認証する producerも無い。D1344 が理由欄で要求する production 値域の測定という趣旨上、空のregistryを空集合として数えて「ゼロ」とすることも充足にはならない。[verbatim-D1344.md:9](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2102-b4-reference-tps-range/verbatim-D1344.md:9)

影響: 空集合や丸め後表現の恒真なゼロを採用すると、実際の予定 batchを測る前に受理集合変更が確定し、D1344 が止めた「実測前の禁止」と同じ結果になる。

## real / refuted の一覧

- **real:** `commit.fitness_tps` は B-4 `reference_tps` の母集合ではなく、完全な上位集合である証明もない。
  影響: registryの受理集合を無関係な履歴値域から決める。

- **real:** parentの2 root走査は、現行 official external output rootと任意のB-4 publication rootを拾わない。
  影響: scheduled参照・report参照・件数が欠落しうる。

- **real:** Decimal-token検査とfloat往復検査は有限十進について恒真である。
  影響: 非有限 exact値が丸められていてもゼロと報告する。

- **real、現コーパス発火は未確認:** `raw_token` は同名nested/duplicate keyを区別できない。
  影響: token件数・字句値をsemantic payloadと取り違えうる。

- **real:** 現行D1344実測は未完了。正しい予定batchもprovenance写像も測っていない。
  影響: 現 brief のP1cをD1344の実測結果として確定できない。

- **refuted:** 現行 benchmark出力経路に非floatのexact throughput producerがある。直接値、fallback、median、COMMITはいずれもfloat経路だった。
  影響: この経路だけを対象に consumer受理を広げる根拠はない。

- **refuted:** callerが任意の有理数を渡せることだけで、それが「正当な upstream 出力」になる。issuerは出所非保証を明記している。
  影響: synthetic入力をproduction値域として扱う誤りを防ぐ。

- **refuted:** D1344を満たすには既存sealed registryが絶対に必要である。完全なpre-seal scheduled batchでも測定できる。
  影響: 要求は原理的に実行不能ではないが、現時点では必要なbatch/producerが欠けている。

- **refuted:** 現在の2 root内に圧縮registry/WALがあり、それが結果を変えている。対象名の圧縮成果物は確認できなかった。
  影響: 現在の主因は圧縮ではなくrootとschemaの取り違え。

- **refuted:** `has_finite_decimal()` の数学判定が誤っている。述語自体は正しい。
  影響: 修正対象は述語ではなく母集合と変換前の値の取得方法である。

## 総括

段2の中心結論「親の852件はD1344のscheduled `reference_tps` 全件実測ではない」は正しい。ただし、次の2点は退ける。

- sealed registryだけが唯一の測定可能物ではない。
- arbitraryなcaller有理数は、それだけでは正当なupstream出力ではない。

最終判定は、**確認済みの正当な非有限十進値は0件だが、D1344が要求した母集合の実測は未完了**。したがって親briefのP1aは否、P1bは「現行benchmark→WAL経路」に限れば是だがB-4全体への一般化は未証明、P1cはこの実測を根拠にはまだ発火できない。テスト実走はしておらず、所見は静的検査による。