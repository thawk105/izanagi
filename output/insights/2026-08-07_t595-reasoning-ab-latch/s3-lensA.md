判定は **NO-GO** です。P1「本 wave では実走しない」は維持すべきですが、`9〜15 pair` という費用推定は根拠にできません。段 2 プランは P2 の直接代理を撤回していますが、full-wave endpoint にも以下の穴があります。静的検査のみで、pytest・実走は行っていません。

### A-1 — must-fix: 歴史 cohort と将来 case の母集団が未定義

- 成果物影響: 容易な survivor case だけで `decision=noninferior` となり、reward-hack／oracle 穴を落とす既定が採用され、certified 選択・材料レポートの受理集合が広がる。
- 再現・確認: 親は残存 job artifact を母集団にしていますが、包含・除外表がありません。[brief.md:42–48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:42) 将来側も registry の置場しか定義せず、task の抽出枠・層化・独立性を規定していません。[s2-plan.md:159–173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:159) 現在の直下集合には `s2-plan.md` があり fix file がない候補が多数あり、どの 3 件をゼロ巡として採ったか再現不能です。
- 最小修正: 対象母集団、包含・除外規則、censored/中断例、task strata を arm 実行前に署名付き case registry へ固定する。歴史 survivor 群は power 根拠から外し、代表的な独立 task の層化標本に結論を限定する。

### A-2 — must-fix: 「`s6-fix*.md` 1 file = 1 巡」が実データと矛盾する

- 成果物影響: `fix_cycles`、歴史平均・SD、`n_pairs` が誤り、非劣性の受理集合と材料レポートの資源値が変わる。
- 再現・確認: 直下 job directory の `s6-fix*.md` を素朴に数えると、親分布の非ゼロ部分 `1×4, 2×7, 3×5, 4×4, 7×1` を完全再現します。[brief.md:43–48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:43) しかし、その集合には worker fix でない[裁定文書](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:1)や別の[fix-ruling](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s6-fix-ruling.md:1)が混入しています。段 2 プラン自身も、並列 `u1/u2` は一巡、`s6-fix-ruling.md` は非 fix と認めています。[s2-plan.md:124–133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:124)
- 最小修正: 歴史各 wave を prospective な `generation` 定義で二読者が再符号化し、artifact→generation 対応表を凍結する。判定不能なら歴史分布を破棄し、ファイル数を power 設計へ使わない。

### A-3 — must-fix: `n=15` は paired 差にも全 co-primary にも power されていない

- 成果物影響: `protocol-freeze.n_pairs=15` と paired-t の CI が未校正のまま `decision` を PASS/NULL にし、非劣性を材料レポートへ誤記できる。
- 再現・確認: 歴史 SD≈1.6 は max 下の task 間分散です。[brief.md:47–52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:47) paired 差の分散は `Var(HH-MM)=Var(HH)+Var(MM)-2Cov(HH,MM)` であり、high の分散も相関も未観測です。さらに SD=1.6 をそのまま差の SD と仮定しても、正規近似だけで `((1.645+0.842)×1.6)^2=15.83`、すなわち最低 16 pair で、有限標本 t はさらに必要です。ところが 15 を literal にし、must-fix、cycle、token の joint power は計算していません。[s2-plan.md:173–180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:173)
- 最小修正: margin を先に固定し、arm 非開示の独立 pilotまたは保守的な paired-SD 上側限界から、全 co-primary と欠測率を含む joint power を計算する。離散・裾の重い count、ゼロ分散時の扱いも解析計画へ固定し、それまでは `n=15` を実装 literal にしない。真の n が一桁小さければ P1 の費用根拠は変わりますが、後続の妥当性 blocker があるため今回の「実走なし」は変わりません。

### A-4 — must-fix: “initial” must-fix が後続の `resolution=="resolved"` で選別される

- 成果物影響: 未解決 must-fix が `initial_unique_count` から消えて HH が良く見え、欠陥が材料レポートに残らないまま受理集合が広がる。
- 再現・確認: primary は initial review の値と称しながら、集計条件に後続状態の `resolution == "resolved"` を含めています。[s2-plan.md:100–114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:100) 一方、cycle は中断を censored と区別しています。[s2-plan.md:135–142](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:135) 同じ保護が finding 単位にはありません。
- 最小修正: review-0 裁定時点で `real && must_fix` の集合を先に凍結し、resolution を別 ledger にする。未解決 finding は件数から除かず、campaign decision を reject または null にする。

### A-5 — must-fix: count/cycle が品質でなく reviewer・親の挙動を測れる

- 成果物影響: finding を見落とす、まとめる、または fix を一巡へ詰め込む arm が低負担として通り、reward-hack／oracle finding が certified 選択と材料レポートから脱落する。
- 再現・確認: 直接の plan-review 代理は撤回されています。[s2-plan.md:146–153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:146) しかし primary は依然、読者の `real/must_fix/G05` 閾値、`equivalence_id` の分割・併合、親の resolution、fix の batching/generation 判断で動きます。[s2-plan.md:102–133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:102) T-181 も semantic dedup、読者、masking の限界を明記しています。[README.md:73–81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/README.md:73) `candidate-only hard harm` は観測された finding には効きますが、両読者が落とした未知 finding を検出できません。
- 最小修正: 代表 task 群とは別に、複数の凍結済み正例・負例を持つ adversarial oracle 群を設け、検出 miss と false positive を co-primary safety gate にする。読者 prompt、fresh context、packet 順、semantic matching、batching policy を凍結し、must-fix/cycle は burden endpoint に限定する。

### A-6 — must-fix: 資源 endpoint が「full-wave 総消費」になっていない

- 成果物影響: `resource_ledger.cli_reported` と token 節約 gate が過小になり、実際には総消費が増える HH を受理できる。
- 再現・確認: 収集対象として列挙されるのは段 2/3/5、downstream review、fix worker と retries です。[s2-plan.md:144–151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:144) arm の出力に応じて増減する段 4 親裁定、fix 裁定、第三読者、段 7–9 の LLM 消費は必須集合にありません。generic worker receipt も job 一件の値しか持ちません。[codex_worker_launch.py:1401–1444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_launch.py:1401) これは D207 が排除したかった「後段総消費が増える」経路そのものです。[decisions.md:9906–9910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9906)
- 最小修正: allocation から段 9 終端までの全 Codex session、親、条件付き第三読者、失敗・retry を一つの campaign closure に含める。人間/custodian 工数は token と混ぜず別値で記録し、session 欠落時は resource decision を null にする。

### A-7 — must-fix: hash-chain は実 treatment と全 event の完全性を証明しない

- 成果物影響: arm 別 CODEX_HOME、config、auth、環境、argv、欠落 worker を reasoning 差へ誤帰属し、台帳の arm 差と受理判断を反転できる。
- 再現・確認: 新設計は worker receipt を後から `register-wave-event` へ取り込むだけです。[s2-plan.md:54–67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:54) generic launcher は containment 非保証を明記し、receipt 自身も `limits_assertion=self_asserted`、`escaped_process_containment=not_attempted` です。[codex_worker_launch.py:2–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_launch.py:2) [codex_worker_launch.py:1427–1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_launch.py:1427) 対して現 T-181 supervisor は実 binary/config/auth/env/argv を process launch と同時に捕捉しています。[codex_reasoning_ab.py:1966–2103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1966)
- 最小修正: caller 登録 API ではなく、一つの trusted paired supervisor が割付、全 worker spawn/wait、実 argv/env/config/auth/CODEX_HOME、attempt closure を直接生成する。arm 間で許される差を「effort とその下流 artifact」だけの causal closure として verifier に固定する。

### A-8 — must-fix: serving・時刻・cache・carryover の交絡を planned order だけで扱っている

- 成果物影響: backend更新、quota/cache、同時負荷、先行 arm からの学習を HH/MM 差として記録し、品質・資源の台帳値と採否を誤る。
- 再現・確認: 設計は control-first 7 / candidate-first 8 の予定順だけを規定し、実時刻の最大 gap、非重複、同時 job、fresh manager context、fresh CODEX_HOME を規定していません。[s2-plan.md:181–187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:181) 現装置には実 monotonic 時刻の overlap/gap gateがありますが、新 family が継承する記述はありません。[codex_reasoning_ab.py:4225–4345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4225) また receipt が確認するのは backend の自己申告 `effort/model` fieldです。[codex_reasoning_ab.py:2929–2936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:2929) T-181 も実計算の証明がないと明記しています。[README.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/README.md:81)
- 最小修正: pair を隔離 fresh context で隣接実行し、最大 gap・非重複・period blockを凍結する。CLI/backend fingerprint、service tier、cache tokens、rate limit、auth/config、時間帯、同時 job を記録し、不一致 pair は null にする。backend attestation が得られない場合の estimand は「当該 serving 期間に requested effort を割り付けた ITT」に限定し、実計算が異なったとは主張しない。

### A-9 — must-fix: 外部 custodian を足しても full blind にはならない

- 成果物影響: arm を推測した読者の期待バイアスで `must_fix`・equivalence・resolution が動き、材料レポートと受理集合が変わる。
- 再現・確認: 外部 custodian と直接 metadata の遮断は改善ですが、packet は出力 bytes をそのまま読者へ渡します。[s2-plan.md:181–187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:181) 現装置も exact output を packet に複製します。[codex_reasoning_ab.py:4824–4836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4824) 漏洩経路は出力長、文体、冗長さ、構造、自己言及、artifact 数、wall/completion 順、tool-call/resource 値、path/mtime/inode、CODEX_HOME/session/logです。さらに effort を設定する launcher/operator は map を知るため、署名だけでは reader との credential 分離を証明しません。T-181 の same-owner masking が blind でない点も既知です。[README.md:76–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/README.md:76)
- 最小修正: custodian兼launcher、reader、manager を別 credential にし、reader interface を凍結 packet のみに限定する。各読者は verdict freeze 前に arm 推測と確信度も記録し、事前登録した blinding audit に失敗したら `blind=false / decision=null` とする。内容由来の推測を消せない以上、検出情報を削らず `outcome-assessor-masked` と正直に呼び、D207 の “blind” を満たすかは人間裁定へ返す。

### A-10 — must-fix: margin と safety screen が非劣性の意味を支えていない

- 成果物影響: 平均 `+1` must-fix の劣化、または未観測の rare harm を許したまま noninferior と記録し、正しさ finding を落とす既定が受理される。
- 再現・確認: `+1.0` は artifact loss や許容コストから導出されず、そのまま二つの count endpoint に置かれています。[s2-plan.md:173–179](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:173) 15 case で candidate-only harm がゼロでも、iid と仮定した片側95%の発生率上限は `1−0.05^(1/15)=18.1%` であり、「非劣性」ではなく「15件で観測しなかった」だけです。解析の zero-variance、tie、t 仮定、primary と sign-flip sensitivity が食い違う場合の決定表もなく、変異候補にも統計境界試験がありません。[s2-plan.md:221–236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:221)
- 最小修正: margin は arm データを見る前に、成果物影響と人間が許容する最大損失から endpoint 別に決める。correctness miss は margin 0、cycle burden は別の運用 margin とする。paired binary harm、離散 count、zero variance、欠測、CI 境界、sensitivity 不一致の閉じた解析表と負例を追加する。なお「全 co-primary が通る」intersection-union 自体は多重性に対して妥当で、ここを弱める必要はない。

### A-11 — must-fix: freeze 後の campaign 放棄・別 ID 再開が閉じていない

- 成果物影響: 不利な campaign を台帳・材料レポートから落として再実行し、成功した freeze だけで受理集合を変更できる。
- 再現・確認: 一つの campaign 内では success peeking 禁止、ITT、欠測時 null が規定されており妥当です。[s2-plan.md:189–200](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:189) しかし SHA が守るのは既存 receipt と当該 freeze の結合だけです。[s2-plan.md:203–219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:203) 新しい directory/campaign ID で別 freeze を作り、旧 run を「pilot」扱いして捨てる経路を拒否する外部 first-registration はありません。これは campaign 間 peeking と反復検定を残します。
- 最小修正: study question、case-registry root、estimand から一意な study ID を作り、最初の freeze、全 start/stop、abandonment、再試験を外部 append-only registry へ custodian 署名で登録する。二つ目は replication として最初の結果も必ず集計・報告し、成功まで再起動できないよう analyzer が照合する。

## 総括

- must-fix は **11 件**（should-fix / nit は 0 件）。
- この設計のまま実験を走らせてはならない（**NO-GO**）。
- P1「本 wave は実走しない」は維持するが、根拠は `9〜15 pair` ではなく、endpoint・盲検・実 treatment・解析凍結の未閉鎖である。
- 修正後も既定 effort は変更せず、代表 case・外部 custodian・trusted supervisor・事前登録解析が揃ってからのみ実走可能。