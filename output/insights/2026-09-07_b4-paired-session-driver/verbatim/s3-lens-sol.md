## 所見

- **id**: correctness-boundary-1
- **対象**: プラン、[plan.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:58)、[plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:103)、[plan.md:161](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:161)
- **主張**: 測定関数の差し込み口は消えていない。テストが置換する `F.runner.measure_point` は、production adapter が実行時に参照するものと同一である。[floor_pair_driver.py:1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1418) の動的属性参照を維持するため、`measure_fn` 引数を拒否しても権威経路は差し替え可能なままである。現行テストも実際に同じ面を置換している。[test_floor_pair_driver.py:1105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1105)
- **具体例**: `F.runner.measure_point` を、binary path を無視して全 candidate/reference に `(100.0, 100.0)` と正常な sink を返す関数へ置換して `F.run_window` を呼ぶ。SHA-256、role、measurement ID は driver が canonical plan から記録するため整合し、全 measurement が complete になる。結果は `D=abs((100/100-1)-(100/100-1))=0` である。
- **成果物影響**: `candidate_floor=0` を生成でき、tie 集合を不当に狭められる。逆に偽関数が任意の異なる値を返せば床値を大きくし、tie と受理集合を広げることもできる。
- **確度**: 高。テスト用と production 用の adapter 分岐はなく、同じ module attribute が呼ばれる。

- **id**: correctness-boundary-2
- **対象**: プラン、[plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:21)、[plan.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:62)、[plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:89)
- **主張**: 二つの独立した `measure_point` 呼び出しを一つの `PlannedSession` と probe 区間で包むだけであり、D1699 の「1つの低水準 session」を満たしていない。これは D1699 が却下した、複数の低水準実行を上位の「組」として同一 session と呼ぶ読み替えである。[d1699-verbatim.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/d1699-verbatim.md:3)、[d1699-verbatim.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/d1699-verbatim.md:11)
- **具体例**: `measure_point(candidate)` は candidate の全 reps を別々の child と tmp directory で完了してから戻り、その後で `measure_point(reference)` が新しい実行列を開始する。[runner.py:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/calibrator/runner.py:1122)、[runner.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/calibrator/runner.py:637) candidate が高負荷帯で 120、後続 reference が低負荷帯で 80、他 side が清浄な 120/100 なら、同じ真の gain でも `D=|0.5-0.2|=0.3` になる。
- **成果物影響**: 走行間ドリフトが D に入り、床値が 0 から 0.3 へ偽装されうる。tie と受理集合が不当に広がる。
- **確度**: 高。プラン自身も二つの呼び出しが同一 process または原子的実行でないと明記しており、低水準で共有される session 状態は存在しない。

- **id**: correctness-boundary-3
- **対象**: プラン、[plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:66)、[plan.md:167](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:167)
- **主張**: 中間の post/pre probe を除去するため、現行なら検出できる競合を受理する窓が新設される。`NOT_PROVEN` への追記は、この正しさゲートの緩和を閉じない。
- **具体例**: `pre → candidate → reference → post` で、競合が candidate の途中に開始し、candidate/reference 境界を越えて reference の途中で終了する。最初と最後の probe は clear だが、現行の candidate 直後の post-probe または reference 直前の pre-probeなら競合を検出して標本を落とす。新設計では両 measurement が complete になる。
- **成果物影響**: 競合が片方の binary を強く劣化させれば D は上下どちらにも動く。例えば clean な `120/100` に対し汚染された分母 80 を受理すれば D と床値が大きくなり、受理集合が広がる。
- **確度**: 高。probe の呼び出し順から静的に成立する追加の未検出区間である。

- **id**: correctness-boundary-4
- **対象**: プラン、[plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:71)
- **主張**: `probe_fn` を caller から受ける明示的な差し込み口を維持するため、`COMPETING_PROBE_ARGV` を定数化しても競合検知そのものは権威化されない。`run_window` の production 経路がその callable を直接使用する。[floor_pair_driver.py:1952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1952)、[floor_pair_driver.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1563)
- **具体例**: 実際に競合中でも `probe_fn=lambda argv, timeout: (1, "", "")` を渡せば、全 pre/post probe が clear と分類される。既存テストの `_clear_probe` が同じ経路を実証している。[test_floor_pair_driver.py:1170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1170)
- **成果物影響**: 汚染された四測定が complete として D に入り、床値を任意方向へ動かしうる。
- **確度**: 高。CLI は固定 `_run_probe` を渡すが、プランは `run_window` を非権威 API と限定せず、同じ経路を測定関数について権威経路として扱っている。

- **id**: correctness-boundary-5
- **対象**: brief、[brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/brief.md:5)、[brief.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/brief.md:45)
- **主張**: 「1つの低水準 session」を要求しながら変更を driver と test の二ファイルに限定する scope は内部矛盾している。現行 runner に二 binary の共有 session API がない以上、P1-a は不可能性を報告せず、裁定上の session を probe 区間へ読み替えている。
- **具体例**: author が scope を守ると、実装できるのは `measure_point(candidate)` と `measure_point(reference)` の二呼び出しだけである。runner に paired session APIを追加できず、D1699 の逐語を満たす実装経路がない。
- **成果物影響**: 別実行列間のドリフトを含む比から D と床値が生成され、B-4 の受理集合が変わる。
- **確度**: 高。brief 自身が runner の一 binary 制約と、二ファイル限定を同時に置いている。

- **id**: correctness-boundary-6
- **対象**: brief、[brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/brief.md:33)
- **主張**: 床値と受理集合の単調性を逆に記述している。床値 0 で tie が減るなら、受理集合は最大ではなく狭くなる。
- **具体例**: 観測差が 0.02 の block は `candidate_floor=0` では tie でなく、`candidate_floor=0.05` では tie になる。したがって大きい床値の方が tie と受理集合を増やす。
- **成果物影響**: seam による D=0 攻撃の実際の影響は、tie の消失と受理集合の縮小である。brief の「最大に広がる」は誤りで、修正優先度や検査期待を逆向きにする。
- **確度**: 高。提示された床値の単調性と直接矛盾する。

- **id**: correctness-boundary-7
- **対象**: 実測事実、[parent-measured-facts.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/parent-measured-facts.md:6)
- **主張**: 現行二関数の引数個数から、低水準で二 binary を一 session に収めること自体が不可能だと一般化している。確認できるのは「現行の各 API は一 binary しか受けない」までであり、新しい paired API や session primitive の追加可能性、まして二呼び出しを一 session と呼んでよいことは導けない。
- **具体例**: runner に `measure_pair(candidate_path, reference_path, ...)` を追加すれば、既存 `measure_point` と `capture_measure_point` の signature はそのままでも、一つの低水準 session 契約を定義できる。この可能性は実測事実と矛盾しない。
- **成果物影響**: 過剰一般化を根拠に二呼び出し案を採ると、correctness-boundary-2 のドリフト混入が床値へ流入する。
- **確度**: 高。signature の観察は正しいが、そこから採用された session semantics は論理的に導かれない。

## 所見が無い領域

- canonical plan からの side、role、artifact 対応、nested measurement の exact 順序照合、二 measurement 完備条件については、プラン記載どおりなら raw の自己申告だけへ落ちる具体的経路は見つからなかった。
- 一 measurement の欠落、例外、非有限値を含む side を complete にする経路は、canonical prefix、exact 2 measurement、exact 2 side session の再導出方針では見つからなかった。
- pair-sample 単位の 5% 会計と、値を変えても事前選択した drop key が変わらない検査には、追加の値依存除外経路を見つけなかった。
- 実測事実 2 から 5 は、対象台帳と参照検索の狭い主張について一致した。実測事実 6 は現 worktree の `p3_b4_material_report` がまだ `floor=None` 固定のため、正しさの安全根拠には使用できないが、現状は fail-closed であり受理集合を広げる具体的経路にはならない。実測事実 7にも追加の緩和経路は見つからなかった。
- pytest は実走しておらず、緑の主張はしていない。

## 総括

最大の欠陥は、test monkeypatch が production と同一の `runner.measure_point` を差し替えるため、T-2166 の seam が残る点である。  
二つの低水準呼び出しを一 probe 区間へ入れて session と呼ぶ案は、D1699 が却下した読み替えを再実施している。  
中間 probe の削除と注入可能な `probe_fn` により、競合標本を complete として受理する経路も残る。  
brief の scope と P1-a は両立せず、床値 0 の受理集合への影響も逆向きに記述されている。