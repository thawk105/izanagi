# 本体論文 (日本語) の序論・貢献・限界の新規起草 — wave の記録と、証拠ごとの現在地の別表

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 依頼: ユーザー (2026-09-20、dev-wave 引数、台帳 ID 未起票)。逐語は `verbatim/s1-brief.md` の冒頭。
- wave: `dev-wave-paper-intro-ja` (branch `worktree-dev-wave-paper-intro-ja`)。着手時 local main `fec4a8187` から fresh worktree、
  段 6 レビュー後に local main `482f19b88` ([T-2304] pin 前進を含む) を ff-only で取り込み、資料の採用時点をそこへ揃えた。
- 構成: docs-only 軽量版 (`DW-C00`)。段 2・3 省略、書き手は親、段 6 に read-only codex レビュー 1 本 + 焦点再レビュー 1 本
  (一次資料から事実を再抽出する docs-only wave の規則、D2148 項 11)。実装差分ゼロなので変異 matrix は免除、受入全走は land 前に実施。
- job dir (生ログ・prompt・receipt): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/`。専用 handoff は背景 job の tmp
  (`/home/SFC/tanab/.claude/jobs/dfc0f814/tmp/handoff-paper-intro-ja.md`)。

## 1. 成果物

| file | 内容 | 大きさ |
|---|---|---|
| `intro.md` | 序論草稿 — 問題、取り組み (3 成果物と核 3 点、位置づけの 1 文)、3 幕の要約、言うこと / 言わないこと、構成 | 約 15 KB |
| `contributions.md` | 貢献節草稿 — 5 項 (強い順) + 副産物 + 貢献として書かないもの。各結果に claim-evidence の実証状態 7 値を付す | 約 20 KB |
| `limitations.md` | 限界節草稿 — 測定契約 / 正しさの保証範囲 / 合成能力 / 否定的結果の射程と機序の帯域 / 機構と測定の区別 / スコープと優先権 / 未実証のまま残る主張 | 約 30 KB |

3 稿は平易な日本語の論文本文で、末尾に「出所 (執筆者向け)」を持つ (先例 = `output/insights/2026-09-10/paper-methods-ja/methods.md`、
`output/insights/2026-09-10/paper-results-ja/results-discussion.md` と同じ書式)。本文には T 番号を書かず、D 番号と一次資料は出所へ寄せた。
版 (`docs/paper-story/`)・claim-evidence 稿・results 稿・図・README・既存の methods / results 稿は 1 byte も変えていない。

## 2. 入力と照合

- 入力 = 論文ストーリー 2026-09-20 版の §1 / §2 / §3 / §6 / §7 と claim-evidence 2026-09-20 稿 (§1〜§6)、`docs/paper-story/README.md` の
  stale 注記 (fig10 / B-7 限定付き充足 / fig12)、`figures/README.md` (fig8b / fig10 / fig12 節)。
- 数値は権威 bytes で照合した: A-2 / A-6 / B-7 fixed5 の `certification.json` (`effects` / `status`)、`output/reports/s1_direct_comparison/report.json`
  (`families.s1a` / `s1b`)、`output/campaigns/p2-5-summary.json` (`correction_2026_07_03` / `recalibration_2026_07_02`)、
  `output/env/pegasus/calibration/between_run_noise_*.json` (`between_run.cv`)、P2-4 単独稿の未丸め 3 値、cohort 1 稿の throughput、
  A-1 attempt-0001 稿の対差平均。段 6 レビューも独立に同じ集合を再計算し一致 (下の §4)。
- 相対リンク 73 本 (fix 後) の不達 0、backtick の repo 内 path の実在 (job dir の `check_links.py`)。

## 3. 版・稿より後に動いた状態語 (D 本文へ再照合した現在地)

論文ストーリー版 (導出起点 `b7f970dfa`、09-20 07:04 JST) と claim-evidence 稿が「裁定待ち」「未着地」「未発効」と書いた項目のうち、
採用時点 `482f19b88` までに動いたものを、裁定台帳の本文で読み直して 3 稿へ反映した。旧記述は執筆時点では真であり、版・稿は改めない。

| 項目 | 版・稿の記述 | 3 稿が採った現在地 | 根拠 |
|---|---|---|---|
| B-7 | 要件充足へは昇格しない (D2044 項 3、D2162 維持) | 限定付きで充足 (単一 attempt・descriptive・非認証・反復間安定性は未判定) | D2174 項 3、README stale 注記、fig10 |
| 床値 g1 (A-4) | 未発効。承認 A と active pointer X は人間手番 | AI 委任の批准 (record は Codex author、commit は親) で発効。oracle の gate-check は既存の不整合 2 件で `allowed: false` のまま。「科学的に十分な床」は主張しない | D2180、`output/insights/2026-09-20/t2724-ax-delegated/README.md`、[T-2810] 起票文 |
| A-1 attempt-0002 | gate で拒否、投入経路は裁定待ち | 1 attempt 限定で認可され、認可記録を照合する gate 解除は実装済み。未投入で値は無い | D2172 項 2、D2178、worklog archive entry 1736 |
| K2 同 job stock 対照 | 未達、裁定待ち | pair launcher は実装済み。未投入 | D2172 項 3、D2183、worklog entry 1746 |
| B-5 | 事前登録 v1 未発効、裁定待ち | 部品の段階実装と上限付き試走は認可、本走は未認可、対照未取得 | D2172 項 4 |
| B-8 | 未取得 (検証相の仕分けは要裁定) | 事前登録 v1 が作られた (未発効、試走・本走は未認可)。検証相は別の追加検証 | D2175 |
| B-10 第 2 cohort の図 | 図は無い | 再現欄付きの後継図 fig8b がある。合成しない | D2173、figures README |
| mocc 追加実験 | (記述なし) | 費用対効果で見送り | D2172 項 7 |
| 仮説層 v3 | 前版の見出し「仮説層は未実装」は同版で訂正済み | 実装・適用済み、非 certifying の二次 view | D2143 |
| ccbench pin | 候補 `e9e477ca` への前進は承認のみ (実施は人間手番)、基準 HEAD の pin は `511c9538` | 2026-09-20 に `e9e477ca` (mocc の trace v2 hook と TRACE 専用 lineage witness を含む 4 commit) へ前進 (D2150 項 1 の実施)。較正の再取得・mocc の certified 系列・性能比較は含まず、旧系列は前進前の固定 checkout で継続。X/P 証明面計装は別 patch のまま | `output/insights/2026-09-20/t2304-pin-advance/README.md`、同 wave の spool fragment、`output/insights/2026-09-17/t2756-pin-evidence/README.md` |

## 4. 段 6 read-only レビュー (gpt-6-astra、read-only) と親の裁定

`verbatim/prompt-review-1.md` → `verbatim/review-1.md` (rc=0、`check_codex_output.py` OK)。判定は **NO-GO、所見 8 (must-fix 5 / should-fix 3)、
real 8 / refuted 0**。状態語 9 項目と主要数値はすべて支持された (「古い状態へ戻す修正は不要」)。親は 8 件とも real と裁定し全件採用した。

| # | 所見 (要旨) | 種別 | fix |
|---|---|---|---|
| 1 | 限界 §1 の「この測定の値がある、とは書けない」は attempt-0001 の観測値の存在まで否定する過小表現 | must | 対案どおり「非認証の attempt-0001 は完走し記述的な観測値を得た。ただし正式な結果・要件充足とは扱わない」へ |
| 2 | 貢献稿に certified の保証範囲の定義が無い | must | 貢献稿の冒頭に定義段落を置き、序論の第 3 幕にも保証範囲と限界節への参照を足した |
| 3 | 検証相「30 verify」の母集団 (本走 24 + 校正完走 6) と未完走 2 件 / 候補の欠測が省かれている | must | 限界 §2 に判定集合の内訳と verdict を持たない未完走を書いた |
| 4 | 限界 §7 の表が作業表 (実装済み・未投入など) の転記になっており、§2・§4〜§6 に個別実験の細部が多い (P1 は採らない方がよい) | must | §7 の表を本 README §5 へ移し本文は散文に。§2 の限定 (i)〜(v) を圧縮、§4 の後継図・未測帯、§5 の批准手続と B-4 spec の細部、§6 の準備作業件数を削った |
| 5 | 「7 値に合わせた」と言いながら見出しの表示が 7 値でなく、§4 の 4 結果が同格に見える | should | 見出しは主張の範囲、結果ごとに 7 値を角括弧で付す形へ (P2-5 = 実証済み、S' = 測って届かなかった、S-1b = 登録追試として成立、A-6 / fixed5 / 右 tail = 限定付きで取れた観測、運用 = 運用上の証拠、必要性・機序 = 未取得) |
| 6 | +147.4% の出所説明が照合先 (P2-4 稿は WAL の median から再計算) と違う | should | 出所 2 を「同稿 §3 項 7・§5.4 の再計算値 (147.35883510937478%) を転記」へ |
| 7 | 序論 §2 と貢献 §1 の位置づけが「1 文 + 3 条件 + 調査状態」を超えて先行の比較説明に入っている。限界 §6 の「2 wave」は内部用語 | should | 両方を 1 文 + 3 条件 + 調査状態へ縮め、比較は関連研究節へ委ねると書いた。「2 wave」→「2 段階の準備検証」 |
| 8 | 限界 §4 の右 tail に、同じ格子の性能低下 (3 workload とも半分以下) が併記されていない | must | 固定表現の直後に費用の 1 文を足した |

親が加えた修正 (レビューの所見外): ピア通知を契機に local main を再読し、[T-2304] pin 前進の着地 (main `482f19b88`) を上の表の最終行と
3 稿 (限界 §6、貢献の「書かないもの」) へ反映、採用時点を `482f19b88` へ更新。受入投入後 (claim 前) に別のピア通知で結果・考察草稿の
2026-09-20 版 (`output/insights/2026-09-20/paper-results-ja/results-discussion.md`、09-10 稿を supersede。main `2bf985125`) の着地を知り、
3 稿の結果稿への参照 4 か所を 2026-09-20 版へ向けた (本文の事実命題は変えていない。同稿は「個々の実験の留保は本稿が持ち、論文全体の限界は
序論・限界稿が持つ」と書き、本 wave の分担と対になる)。

**焦点再レビュー 1 (fix 後、gpt-6-astra / medium、26 call、383 秒、`verbatim/prompt-focus-1.md` → `verbatim/focus-1.md`):** 前巡の
所見 8 件は **8/8 closed**。親が fix で新しく書いた派生値・量化語 (4 commit / 141 行、判定集合 30 = 本走 24 + 校正完走 6、未完走 2 件 / 候補、
1250 → 9999 µs で 3 workload とも半分以下 = 44.36% / 48.14% / 40.04%、+147.4% の再計算、certified 4 度到達、oracle 起動検査の不整合 2 件、充足可能条件
1 件、リンク 73 本) はすべて一次資料と一致。判定は **NO-GO、新規所見 2 (must-fix 1 / should-fix 1)、real 2 / refuted 0**:

| # | 所見 (要旨) | 種別 | fix |
|---|---|---|---|
| 新 1 | 限界 §3 の「合成ループは現行の素材コーパスの下で certified の終端判定へ 4 度到達」は、4 走がすべて旧 pin `511c9538` の下 (K2 3 巡の WAL の `build_start` pin) なので、新 pin への実績移転を招く | must | 対案どおり「pin 前進前の CCBench `511c9538` の下で」へ |
| 新 2 | 貢献「書かないもの」の pin 前進の文に、限界 §6 が書く「較正の再取得・mocc の certified 系列・性能比較は含まない」が無い | should | 同じ限定を足した |

所見 4 の残る細部について焦点再レビュー 1 は「残す / 削る」を仕分けし (残す = 保証範囲と 5 限定、検証相の未完走、機序の帯域と右 tail、権限の不在と
床値の量の区別、pin 前進と実働範囲の分離。削ることを推奨 = B-4 推定対象の細かな説明、floor 案の絶対値 2 個と CV 3 値)、「再開理由にはしない」と
した。親は B-4 推定対象の説明を 1 文に圧縮し、floor 案の値と CV 3 値は「配線下限で決まった」「3 つの量は別」を数値で示すために残した。

**焦点再レビュー 2 (3 巡目、2 所見の閉鎖だけを確認。gpt-6-astra / medium、6 call、102 秒、`verbatim/prompt-focus-2.md` →
`verbatim/focus-2.md`):** 新規所見 1・2 とも **closed** (K2 3 巡の WAL の `build_start` pin が `511c9538` であることを直接確認)、所見 4 の圧縮対応は
受容、新規所見なし、**GO**。段 6 は DW-O16 の上限 3 巡内で閉じた。

## 5. 証拠ごとの現在地の別表 (執筆者向けの作業表。論文本文には置かない)

限界節 §7 の本文から移した表。claim-evidence 稿 §2.4 / §4 を土台に、D2172〜D2183 と本日の着地 (fig8b / fig10 / g1 発効 / B-7 限定付き充足 /
pin 前進) で更新した。**件数は準備完了度を表さない** (claim-evidence 稿 G1)。「実装済み」「認可」「投入」は別の状態であり、混同しない。

| 項目 | 主張への関係 | 現在地 (採用時点 `482f19b88`) |
|---|---|---|
| A-1 現行契約の対測定 | 旧 3 値の但し書きは外れず、現行契約下の別の主張が 1 つ増える | 非認証 lane の attempt-0001 が完走 (descriptive)。formal な充足は未判定。独立再現の attempt-0002 は 1 attempt 限定で認可・gate 解除実装済み・未投入 (D2172 項 2、D2178) |
| A-5 別 boot での取り直し | 論文採用値の但し書き | 未取得 (0 件)。Pegasus では充足にならない (D1525) |
| A-4 official 床値 | 8b oracle の前提 | floor 案は配線下限で決定。g1 として発効 (AI 委任の批准、D2180)。oracle の起動検査は不整合 2 件で拒否のまま (T-2810)、W-4 未起動 |
| B-1 既知軸最良の超越 | 合成の性能主張 | 測って不成立。新しい軸の側は「非列挙」の壁 (D1409、未裁定) |
| B-2 descriptor 条件付き合成の因果証拠 | 「ワークロード特化」 | 未実走。完了証明層の充足可能条件は 1 件 (`{"C10"}`) |
| B-3 無人系列の完走 | 「無人ループ」 | 未完走。最上流は権限の不在 (D1829) |
| B-4 還流の on/off ablation | 「正しさシグナルの還流が効く」 | 未実走。適格な赤 precursor 0 件。床値側は第 1 窓完走・集約前、第 2 窓と finalize は後続 |
| B-5 生成器対照 | 「LLM の条件付き優越」 | 事前登録 v1 (未発効)。段階実装と上限付き試走は認可、本走未認可、対照未取得 (D2172 項 4) |
| B-6 リーク制御の完備 | 知識の因果効果 | 未達。3 巡は閉じ、同 job stock 対照は実装済み・未投入 (D2183)、4 巡目は 1 job 認可 |
| B-7 全 workload の退行込み報告 | 失敗条件 (e) の報告要件 | 限定付きで充足 (単一 attempt・descriptive・非認証・反復間安定性は未判定、D2174 項 3) |
| B-8 種を変えた長時間検証 | 最終候補の正しさ | 未取得。事前登録 v1 (未発効、D2175)。採用候補の検証相 (D2160) は別の追加検証 |
| B-9 説明層の拡張 | 「なぜ速いか」の自動化 | 事実層は対象 campaign 群のみ。深い一致検査は本体側で不実施。仮説層は非 certifying (D2143) |
| B-10 機序の帯域外への拡張 | backoff の機序 | 待ち方 grid は 1 対比の判定。右 tail は 2 cohort とも固定表現の結末 (fig8b で併記、合成しない)。機序未同定 |
| C-1 クロスプロトコル | 将来スコープ | 非 Silo の性能比較 0 件。pin は mocc の trace hook を含む候補へ前進したが較正・certified 系列・性能比較は含まない。mocc の機械実証 2 段階は準備、G2 観測 4 件は非 certifying、追加実験は見送り (D2172 項 7) |
| C-4 体系的な先行研究調査 | 優先権 | 軸 1 は限定付き閉鎖 (`RW1`)、軸 3 は未実行 (`RW0`)。停止は完了ではない |

## 6. 検査と受入

- `python3 tools/check_docs.py`: 違反なし (起草後の木、および main `482f19b88` 取り込み後の木)。
- 焦点走・受入・land の結果は専用 handoff と job dir の receipt に集約する。本節には実測前の欄を作らない。

## 7. 限界・言わないこと

- 3 稿は執筆者向けの日本語草稿であり投稿本文ではない。英語化・関連研究節・新規実験・図の作り直しは行っていない。
- 3 稿は版・claim-evidence 稿を数値の出所にせず、権威 bytes と results 稿から写した。ただし本 wave の照合は 1 主体の再計算と段 6 レビュー 1 本による
  もので、当時の実行全体の独立監査ではない (D920)。
- 状態語の更新は採用時点 `482f19b88` に着地した裁定に限る。稼働中・未着地の wave の内容 (A-1 attempt-0002 の投入、K2 4 巡目、B-5 試走、T-2810 の修正、
  W-4) は完成扱いしていない。
- 「3 節を同じ主張の強さで揃える」は段 6 レビューの所見 6 (レンズ B) で検査したが、投稿時の構成が決まれば再照合が要る。
- dev-wave 改善候補: 段 8 で裁定 (本 README 末尾に記録)。

## 8. dev-wave 改善候補 (段 8)

候補ゼロ。本 wave で踏んだ作法はいずれも既存の正本 (`DW-C00` の docs-only レビュー条項、`DW-O16` の 3 巡上限、`DW-O20` の ff-only 取り込み、
ピア通知を local main 再読の契機にだけ使う `DW-C00`) で足り、欠落・無駄・曖昧・失敗は観測していない。版の記述が着地後の裁定で古くなる型
(pin 前進を「承認のみ」と書いた行) は、版・稿を凍結物として保ち採用時点の main で状態語を読み直す既存の運用で処理した。
