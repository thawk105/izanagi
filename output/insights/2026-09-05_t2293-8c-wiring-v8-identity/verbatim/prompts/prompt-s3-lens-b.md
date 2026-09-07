単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md` — 親 brief (検査対象。親自身も攻撃対象である)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/artifacts/t2293-8c-wiring-design/s2-plan.md` — 段 2 の plan (検査対象)
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/decisions-verbatim.md` — D1616 / D1561 / D1190 / D1555 の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/design-doc-verbatim.md` — `docs/phase3-8c-wiring-design.md` の逐語 (特に §3.6、§4.1〜4.4、§7、§10 の恒真化監査)
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/t2261-insight-s6-verbatim.md` — 衝突を発見した実測の逐語

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-design` である。コードはすべてこの worktree の中を読む。HEAD は local main `97ee3cd3a`。

## レンズ: 正しさ境界と恒真化

お前は plan を守る側ではない。**この設計が正しさゲートを 1 mm でも緩めていないか、足すと言う検査が実際には何も拒否しない恒真な保証になっていないか**を攻撃する。物理実行の保証 (§4.2 の双射、§5.3 の run 分離) が設計どおりに成立するかを、偽装シナリオで検査せよ。

必ず次を検査せよ。各所見に severity (blocker / must-fix / nit)、file:line、[実測] / [推測] を付けろ。

1. **受理集合の向き。** plan が触る各拒否条件 (`campaign_claim.acquire_claim`、`_assert_resume_allowed`、`assert_campaign_binding`、`reflux_formal_consumer` の FC03 / FC04 / FC05a〜c、`reflux_origin_topology._validate_members`、`launch_admission_record` の origin 一致、completeness の exact key) について、変更後に**新しく受理される入力**が 1 つでもあるかを列挙せよ。あれば規律 2 違反の候補として blocker にせよ。
2. **偽装シナリオ。** 次の各攻撃が plan の検査を素通りするかを判定せよ: (a) 1 回の物理 run の WAL / receipt / `build_attempt_id` を 33 record で使い回し、`campaign_run_identity` だけ書き換える。(b) 別 trial (別 `binding.campaign_id`) の 33 物理 run を流用する。(c) 同じ trial の過去 attempt (別 `prereg_generation` や別 replicate) の物理 run を流用する。(d) `planned_campaign_run_identity` を envelope 作成時に任意の 33 文字列にしておき、実 run は 1 layout で回す。(e) run plan を後から書き直す (create-only 性の破れ)。(f) `execution-provenance` を producer 不在のまま手書きする。各シナリオで「どの検査が拒否するか」を file:line で名指しし、拒否する検査が無ければ blocker。
3. **`campaign_run_identity` の導出の決定性と一意性。** `ident.campaign_id` の 8 hex 切詰め (`cfg_hash` は SHA-256 先頭 8 hex) で 33 個が衝突する確率と、衝突時の挙動 (claim / layout 衝突が fail-closed か)。`trial` 接尾辞の書式が別 trial の素の `trial` 値と一致し得ないことの証明 (例: trial_id の正規表現 `[a-z0-9][a-z0-9._-]{0,63}` は `-q00` を末尾に含み得る)。
4. **FC03 の 3 項等式を残す (P3) ことの意味。** `execution_provenance.campaign_id` (論理値) を producer が書くとき、その値は物理 run の WAL / lock から再導出できるのか、それとも producer の自己申告か。自己申告なら「provenance の campaign_id 一致」は §10 が却下した「record 内の `issuer` 文字列を権限証明にする」型の恒真化ではないか。代替 (物理 run の `campaign.lock` から論理 campaign を再導出する束縛) が要るなら設計要件として名指しせよ。
5. **`planned_campaign_run_identity` の束縛の実効性。** envelope は capability digest を含むが capability は envelope を含まない。consumer が「この envelope はこの capability のために作られた唯一のもの」と判定する根拠は何か (create-only path、digest、`launch_admission_record_sha256`)。envelope を差し替えて別の 33 identity を宣言する攻撃を拒否する検査は plan にあるか。
6. **§4.2 の双射との冗長性。** `build_attempt_id` 相異 (FC05a) と WAL 区間非重複が既に物理 run の 1 対 1 を保証するなら、`campaign_run_identity` の検査は何を**追加で**拒否するのか。追加で拒否する入力を 1 つ具体的に書け。書けなければその検査は変異を帰属できない冗長 gate (F28 型) であり、設計から外すか帰属を明記させよ。
7. **D1190 の先例との同型性。** s8b の「効果 key は座標、測定世代は run ごと決定的」に対し、本案の「論理 campaign_id は座標、物理 run identity は query ごと決定的」が同じ性質 (resume は同じ identity へ戻る、別 run は別 identity) を持つか。origin topology では resume を許さない (§5.2、Pegasus `allow_resume=False`) ので、決定的導出が逆に「crash 後の再実行が同じ identity・同じ layout に当たって拒否される」形にならないか。それは望ましい fail-closed か、tombstone suffix (§7.2) と矛盾するか。

## 出力

- 所見表 (severity / 所見 / file:line / 偽装シナリオまたは新規受理入力 / 設計への要求)。
- 「plan を作り直すべきか、修正で足りるか」の判定。
- 裁定パッケージ候補 (正しさ境界に関わる択一で、この wave が決めてよくないもの)。
- 各主張に [実測] / [推測]。

## 制約

- 読取専用。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 実装・docs 編集・commit をしない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数・must-fix 件数・plan の判定を 8 行以内で書け。
