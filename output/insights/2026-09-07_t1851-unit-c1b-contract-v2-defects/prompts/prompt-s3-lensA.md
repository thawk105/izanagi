単独段 dispatch: stage=consult; lane=A; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md

## レンズ A: 正しさ境界 — 封印は本当に偽造できないか

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/parent-verification.md` — **親が段 3 の前に自分で走らせた検算 (V1〜V3)。plan の [実測] と食い違う箇所はこちらが正本**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/s2-plan.md` — 検査対象の段 2 プラン
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md` — **親 brief。これ自身も検査対象である**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-s4-adjudication.md` — 契約 v2 の正本 (3 節)、境界 (5 節)、裁定パッケージ (6 節)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-README.md` — 継承元 C1a の成果と閉じていない窓
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1113 / D1114 / D1341 / D1522 / D1533)

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD は `9c1951179` である。コードはすべてこの worktree の中を読む。

## 共通の制約

- 読取専用である。実装しない。書込可能な tmp が無いので pytest 緑を要求せず、静的検査と python の直接評価だけで論じる。テストの実測は親が行う。子の非実走を緑と数えない。
- **plan を守らせるのではなく攻撃する。** 親 brief の (P1)〜(P5) と、親検算 V1〜V3 の一般化も攻撃対象である。
- 主張には **[実測] / [推測]** を付ける。行番号・件数・key 集合・値域は必ず [実測] にする。plan の行番号を転記せず自分で現物に当たる。
- 所見は次の形式で書く。`| ID | 所見 | real / refuted の自己判定 | 根拠 (file:line または実行結果) | 成果物影響 (この所見を無視すると何が壊れるか) | 提案する処置 |`
- **成果物影響を書けない所見を real にしない。**
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、real 所見の件数、最も重い 3 件、plan を採用してよいか (yes / 条件付き / no) を 12 行以内で書け。

## このレンズの依頼

C1b が新設するのは**正しさの gate そのもの** (v2 台帳の terminal を開ける封印証拠) である。規律 2 は「正しさゲートを緩める変異を許さない」、規律 3 は「正しさシグナルを後付けにしない」、D1113 は「呼び手は証拠の値を選べない」。plan の設計がこれらを実際に満たすかを、**攻撃者の視点**で検査せよ。

次を必ず含めること。

1. **偽造経路の全数列挙。** plan の `SealedTerminalEvidence` / `ValidatedTerminalEvidence` / issuer table 案に対し、呼び手が正規の launcher 実行なしに validated capability を得る経路を探せ。少なくとも次を検査する: dataclass の通常 constructor、`dataclasses.replace()`、`copy` / `pickle` / `__reduce__`、module 属性の差し替え、issuer table への直接 insert、crash replay 用 private API、test 用 hook、`__init_subclass__`。**「private だから安全」を根拠にしない** — 実際に到達可能かを現物で確かめよ。
2. **capability と row の束縛の穴。** plan の M16 は「row digest と capability digest の束縛削除」を変異にしている。逆に、束縛があっても**別 attempt の正当な証拠を持ってきて通る**経路 (証拠の使い回し) が無いかを検査せよ。`attempt_binding` の 12 key が実際にそれを塞ぐか、adapter が三者照合する対象 (`_AttemptState` / claim / terminal 行) が本当に独立な出所かを見よ。
3. **E1 再導出の忠実性。** 契約 3 節の 6 枝と campaign `s8b_floor_campaign.py:6312-6327` の現物を突き合わせ、順序・条件・排他性・網羅性が一致するかを行単位で照合せよ。plan は「辞書を持たず if/elif 6 枝」と書いているが、**枝 2 と枝 3 が同じ E2 語を返す**設計になっている。この重複が (a) 契約の意図どおりか (b) 変異 M6 / M7 が互いを殺し合って帰属不成立にならないかを判定せよ。
4. **cross-field 不変条件の網羅性。** 契約 3 節が挙げる不変条件だけで、`observed` へ落とす逃がし道が本当に 0 本かを検査せよ。特に `nonfinite_count` の再計数、`exec_failures` の unavailable projection、`len(throughputs) + nonfinite_count + exec_failures == reps_expected` が **failure 非 null のとき**どう振る舞うかを、契約の文面から矛盾なく導けるかを見よ。導けない組合せがあれば列挙せよ。
5. **classification reason と E2 の衝突 (plan の先行裁定 3 件目)。** plan は core `attempt_registry_core.py:1381-1408` の等値検査が validator 到達前に E2 terminal を全部拒否すると主張している。**現物で確かめよ。** 正しければ、plan が提案する「capability 付き v2 だけ profile validator が三者を検査してから等値を代替する」形が、規律 2 を緩めていないか (= 等値検査の穴を新設していないか) を判定せよ。契約 3 節は「core では**外さない** (A4)」と明記している点と突き合わせよ。
6. **親検算 V3 の帰属を独立に確かめよ。** `run_cmd` が原因だとして、`notes` / `probe_before.stdout` / `probe_after.stdout` など他の field も同じ三軸を運びうるかを現物で検査せよ。**運びうる field を全列挙**し、`campaign_record` を証拠へ載せる契約が現行 writer と両立する形が存在するか (存在するなら何か、存在しないなら契約のどこを変えるべきか) を判定せよ。この判定は C1b の実装可否を決める。
