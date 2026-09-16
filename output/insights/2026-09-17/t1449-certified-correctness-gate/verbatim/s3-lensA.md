## gate 条件と凍結事前登録

参照略号：B＝[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1449-certified-correctness-gate/s1-brief.md)、P＝[s2-plan-2.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1449-certified-correctness-gate/artifacts/dev-wave-t1449-certified-correctness-gate/s2-plan-2.md)、V＝[semantic validator](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/orchestrator/submission_gate/_semantic_validator.py)、U＝[unit3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/orchestrator/tests/test_t338_submission_gate_unit3.py)、R＝[凍結事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md)、A＝[追補 A](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md)、D＝[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/docs/decisions.md)。

**所見**：P の gate は、§7.1(1) の失敗受領証許容を「性能 completed がない場合」に狭めている。
**分類**：real
**根拠**：R:755–757 は「検証割当てが失敗した stage では 0〜5 件を正当な受領証として受理する」；P:31–44 は `if performance_slots` の下で6対未満を拒否し、P:16 はこの縮小を正規手順との非共存で正当化している。
**影響**：既存検査を通過する「性能 completed＋検証失敗＋証拠0〜5件」が受理集合から消えるが、この集合全体が偽造だという根拠はない。
**推奨**：plan v2 ではこの集合差を明記し、「§7.1(1) を維持する」「偽造経路だけを閉じる」という断定を取り下げる。

**所見**：検証割当てで artifact を生成・保存した後、性能割当てと残りの検証処理が重なる反例候補を、指定資料は排除していない。
**分類**：plausible
**根拠**：A:81–84 は「immutable path へ保存して以後の全性能 cluster がそれを stage」、A:110–114 は build 後に correctness/liveness・evidence 検証・後片付けを置くが、検証割当て全体の completed を性能開始条件とは書いていない；A:626–627 の終端規則も過去の性能完了を消さない。
**影響**：この並行時系列が正規なら、性能 completed と検証非 completed の共存を一律拒否する条件は、失敗記録まで過剰拒否する。
**推奨**：plan v2 では「性能完了後に検証失敗」の合法性を未確定とし、特に `post_performance_failure` は R:529–533 の raw 経路も満たす時系列として検算するまで負例の正当性を確定しない。

**所見**：候補の終端 reject と、その失敗を記録した受領証の semantic reject が混同されている。
**分類**：real
**根拠**：A:283 は correctness anomaly を「候補の終端 reject」「削除も置換もしない」とし、R:524 はその attempt の条件を定義する；V:2042–2047 は raw anomaly と `failure_evidence.kind == "correctness"` を検査する一方、V:2031–2035 は別の completed attempt があっても global な anomaly により先に拒否する。
**影響**：性能 completed と raw anomaly の共存例は新 gate の追加拒否ではなく既存拒否であり、これを新 gate の実効性に数えると効果を水増しする。
**推奨**：plan v2 に「失敗受領証の記録」と「候補の認証拒否」を分けて記し、anomaly 共存例は既存挙動として扱い、本 wave の新 gate による拒否例から外す。

## 成功・certified の読み

**所見**：「性能 completed attempt が1件ある」は、D1272 の「成功・certified な受領証」と同値ではない。
**分類**：real
**根拠**：D:41265–41273 は「成功・certified の受領証のときだけ」と「受理集合を必要以上に狭めない」を要求する；R:31 は受領証を stage 単位とし、U:631 は8 slot を予定する一方、U:455 は先頭36 run だけ、U:545 はその1 attempt を completed とする。
**影響**：P:3 の条件は stage の成功が成立していない部分完了受領証にも発火し、D1272 が指定した成功境界より広い集合を拒否する。
**推奨**：plan v2 の P1-c 採用を確定扱いから外し、attempt 成功・stage 成功・certified 採用のどれを D1272 の条件とするかを裁定対象として明示する。

**所見**：「pilot と main_run が揃った時点だけで要求すれば D1272 を満たす」という代替解釈も、そのままでは成立しない。
**分類**：plausible
**根拠**：R:31 の「受領証1枚は study stage 1つ」に対し、V:2639–2657 は2枚の件数・順序を要求し、V:2664–2693 は study ID と検証割当ての同一性を検査するだけで、2枚の存在を certified 成功とは定義していない。
**影響**：study 入口だけへの移設は単体 validator・writer の証拠0件経路を残し、逆に2枚が揃った失敗 study へ無条件に要求すれば過剰拒否を再現する。
**推奨**：plan v2 では study-only 案を単なる配置変更として採らず、認証への全経路で必須になる条件か、失敗受領証発行を維持できるかを併記する。

## §8 否定検査

**所見**：「reason_code を読んだだけで§8違反」という攻撃は、既存契約とコードにより反証される。
**分類**：refuted
**根拠**：R:768 は「reason_code の分岐条件すべて」を semantic validator に要求し、V:2019–2030 は completed 申告に raw 条件を課す；P:31–44 は既存受理集合から証拠不足を除く拒否条件であり、completed 申告だけで受理する分岐ではない。
**影響**：新条件は completed を受理の十分条件にはしないが、その発火集合が D1272 に適合するかは別問題として残る。
**推奨**：plan v2 の§8説明は「申告値を正の権威にしない」までに限定し、それを成功境界の正当性の証明に使わない。

**所見**：既存の `test_reason_code_completed_is_not_positive_authority` は、新 gate の条件選択の正しさを証明しない。
**分類**：real
**根拠**：U:977 の入力は allocation・marker・actual を欠き、V:1992–1993 の「completed attempt … has no allocation」で拒否されるため、性能完了分岐も新 gate 挿入点も通らない。
**影響**：この test が維持されても、失敗受領証への過剰拒否や reason の変更による gate 非発火は評価できない。
**推奨**：plan v2 では同 test の証明範囲を「completed 申告単独では受理されない」に限定し、成功境界の検証根拠から外す。

## 恒真化・空振り

**所見**：新 gate が全入力で既存6対規則に含意されるという攻撃は反証されるが、検証 completed の入力だけでは新 gate を識別できない。
**分類**：refuted
**根拠**：V:1994–2017 の6対規則は検証 completed の枝だけであり、U:564 の検証 pre failure と U:581–600 の1件証拠はそこを通らない；一方、検証 completed の不足・重複は V:2012 の `reason`、V:2017 の `cardinality` で先に落ちる。
**影響**：改修後の成功 fixture だけでは gate 削除を検出できず、非 completed 検証を含む入力でのみ追加拒否を識別できる。
**推奨**：plan v2 では「追加拒否を識別する合成入力」と「正規手順上も拒否すべき入力」の証明を別々に記載する。

**所見**：`reason_code="correctness"` の一致だけでは、新 gate による拒否を識別できない。
**分類**：real
**根拠**：V:2599 の builds、V:2602 の raw evidence が新 gate より先に走り、V:2035 の raw anomaly も同じ `correctness` を返す；検証 completed の件数不足なら V:2012 が別 reason で先に拒否する。
**影響**：先行拒否を含む負例では gate を削除しても拒否が残り、DW-M01 の単一理由性を満たさない。
**推奨**：plan v2 の各新規負例に、先行検査を通る根拠と gate 削除時に受理へ変わる対応を付け、anomaly・compile 不整合・検証 completed 不足を新 gate 専用負例に混ぜない。

## 三者比較の実効性

**所見**：「空 argv・性能側 compile_commands 流用で三者比較を空振りさせられる」という経路は、通常の top-level 検査では反証される。
**分類**：refuted
**根拠**：V:993–994 は macro の欠落を拒否し、V:974–975 は空 compile_commands を拒否する；V:1163–1164 は性能側に0/0、V:1140–1141 は correctness 側に1/1を要求するため、同じ固定 bytes の commands は両方を満たせない。
**影響**：これらの入力を新 gate の穴として扱うと、既存 `compile` 拒否を見落とした誤指摘になる。
**推奨**：plan v2 の保証を「先行検査を通った各 entry の三脚 macro 検査」に限定し、同一入力で既存拒否される経路を追加対策の根拠にしない。

**所見**：各 entry で三者比較が走ることは、その compile_commands が当該 arm・TU の実 build を示すことまで保証しない。
**分類**：real
**根拠**：D:23185 は「当該 TU の実 compile argv」を要求するが、V:979–987 は correctness 側で entry の argv だけを抽出し、V:1055–1060 は macro を検査する；TU の path・重複・被覆検査 V:1292–1324 は `arms.*.compile` 側にあり、V:1117–1149 は correctness 側で同等の照合を行わない。
**影響**：同じ correctness commands を複数 arm の entry に使っても三脚比較は実行され、6対ラベルの被覆だけでは6対の実 build/run の独立した裏付けにならない。
**推奨**：plan v2 の「必要な三者比較あり」を実装済みの macro 比較の範囲に限定し、TU・arm 束縛の追加検査は本 gate に混ぜず裁定パッケージ候補へ分ける。

## 親 brief 自身の点検

**所見**：B:31 は、生成元の一意性から実行順序を導き、さらに検証失敗の終端状態を一種類にまとめている。
**分類**：real
**根拠**：B:31 は「失敗なら `design_not_feasible`」「正規手順で生じない」とするが、A:314 は生成元の規定に留まり、A:626–627 は correctness anomaly＝候補終端 reject、開始前 infra failure＝`design_not_feasible` と区別する。
**影響**：gate の受理集合縮小を正当化する中心的前提が、引用元より強い断定になっている。
**推奨**：plan v2 の brief 訂正に「build 先行≠検証全体の成功先行」を追加し、P:16 に残った同じ推論も削除する。

**所見**：brief の実アンカー表には、被覆拒否行の欠落と liveness の誤参照がある。
**分類**：real
**根拠**：B:41 の `V:1993–2015` は被覆不一致を拒否する V:2016–2017 を含まず、B:44 の「liveness 641」は実際には U:637 の `"liveness": []` で、U:641 は `schema_ref`；P の phase 説明で挙げる U:358 も実際の `_phase_data("verification", 100)` は U:351。
**影響**：nit。
**推奨**：plan v2 と brief の訂正一覧を、6対規則 V:1994–2017、liveness U:637、verification phase U:351 に更新する。

**所見**：P1-c の「declared_use_class は§8で受理入力に使用禁止」という記述への疑義は反証される。
**分類**：refuted
**根拠**：R:786 は「受理条件の入力に使ったら落ちるテスト」、R:789 は `declared_use_class` を明記する。
**影響**：この field を成功・certified の判別に使う代案は、凍結契約に反する。
**推奨**：plan v2 では同 field を条件候補に戻さず、P1-c のうち未確定なのは「性能 completed の存在＝成功」という部分だと切り分ける。

## scope 外の層

**所見**：「study-level は scope 外」という記述は、変更対象外と挙動影響外を区別しないと誤解を生む。
**分類**：real
**根拠**：`orchestrator/submission_gate/_writer.py:73–78` は単体 validator を呼び、V:2645–2651 も各受領証を個別検証する；一方、`orchestrator/submission_gate/__init__.py:3–7` は「単位6で公開 API を統合するまで」空の import surface とする。
**影響**：新 gate は単体・private writer・study 検証へ波及するが、単位6の公開 API や certified 選択への配線完了を意味しない。
**推奨**：plan v2 では「直接変更＝reason branches」「既存呼出しによる影響＝private writer／study」「未実装＝単位6公開 API／認証への統合」と分記する。

B へ：fixture 変更の consumer 波及、46 vector、凍結 pin、直接 pytest 案の扱いは別レンズの検証対象とする。

## 裁定パッケージ候補

**所見**：D1272 を実装条件へ落とすには、失敗記録の受理と成功・certified への採用を分けた発火条件の確定が必要である。
**分類**：plausible
**根拠**：D:41265–41273 は成功側の非空・三者比較と失敗側の空配列維持を同時に要求するが、R:31 の stage 粒度、R:755–757 の失敗許容、V:2639–2693 の study 検査のいずれも「性能1件完了＝certified」とは定義していない。
**影響**：現案は単体受領証を厳しくする点では強いが過剰拒否の疑義があり、study-only 案は全認証経路で強制されなければ正しさゲートを弱める。
**推奨**：裁定候補を「raw から導く成功・certified 採用条件 ⇒ 必要な証拠と三者比較」「失敗記録は§7.1(1)を維持」とし、その採用条件と強制入口を確定してから具体式を選ぶ。

**所見**：correctness compile の TU・arm 対応を追加で束縛する案は、今回の件数 gate とは独立した契約変更である。
**分類**：real
**根拠**：V:1117–1149 の現行検査は source 一致・macro 三脚・性能 binary との digest 不一致であり、D:23185 の「当該 TU」と実 build の対応を追加照合する処理はここにない。
**影響**：追加すれば受理集合と必要な証拠が変わり、「gate 1条件」の実装に隠して扱えない。
**推奨**：必要なら別裁定で束縛対象と既存契約との差を提示し、本 wave は保証範囲の正確な記述に留める。

## 総括

**現案を確定する根拠は不足している。** 最大の問題は「性能 completed が存在すれば成功・certified」という読みと、「検証失敗との共存は正規手順で起きない」という未証明の前提である。

受理集合の縮小は real、正規並行手順による具体的な過剰拒否は plausible。raw anomaly 共存例は既存拒否に隠れるため、新 gate の効果には数えられない。成功境界を確定し、追加拒否の正当性と単一理由性を分けて plan v2 に反映する必要がある。

静的検査のみ実施。ファイル変更・git 状態変更・テスト実行はしていない。