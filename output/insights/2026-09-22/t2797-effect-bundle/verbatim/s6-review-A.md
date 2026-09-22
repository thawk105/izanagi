静的レビューの結論は **NO-GO**。must-fix は親手順の失敗処理に 2 件です。指定資料・実装差分を読み、hash・保存値の読み取りと再集計を行いました。テスト・変異・計算 job は実行していません。親の焦点走は **2,732 passed / 14 skipped、Elapse 110 s** と確認しました。

以下、`E` は `output/insights/2026-09-22/t2797-effect-bundle` を表します。

1. **must-fix — 最終 critic の model 不一致は、登録した「期限切れで系列欠測」にならない**

   根拠: [親 template:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-llm-parent-template.md:35)、`E/README.md:81`、[driver:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/orchestrator/campaign/b5_generator_contrast.py:808)、同 `:817–841`。

   template は全評価後に critic を呼び、不一致なら以後の proposal を公開せず閉じる。しかし B=10、または A=30 の最後の評価では、driver は `slot-k.json` 公開後に探索を抜け、親を待たず endpoint 固定・score 計測へ進む。次の handshake がないので `proposal-wait-timeout` は発生しない。これは競合タイミングに依存せず成立する。

   最終 critic を不一致処置の対象に含めるのか、次回生成へ還流する critic だけを対象にするのかを発効前に確定し、D-4・束・template を一致させる必要がある。

   **成果物への影響:** `models-critic.json` が不一致でも、台帳に正常な score が残り、既存 report の比較へ入る。

2. **must-fix — 親 template に A-only 拒否から次の原提案へ進む手順が欠ける**

   根拠: [親 template:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-llm-parent-template.md:28)、同 `:31–38`、[LLM tool:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/tools/b5_llm_round.py:300)、[driver:754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/orchestrator/campaign/b5_generator_contrast.py:754)、同 `:800–811`。

   `coder` は planner の JSON・schema・方向を検査し、不合格ならそこで停止する。template が `reject` を指示するのは後段の `proposal` 失敗だけで、この早期失敗を扱っていない。また、親側拒否や子側 Tier0 不通過では `slot-k.json` は公開されず、driver は同じ評価番号の次の request へ進む。template にはこの分岐がなく、評価後の slot 待ちへ進むと待ち合わせが成立しない。

   空出力・planner/schema 不合格・proposal 拒否・子側 A-only 拒否について、候補を修正せず、critic を呼ばず、同じ k の次の a へ進む手順を明記すべきである。これは既存予算契約の手順化であり、新 gate は不要。

   **成果物への影響:** 本来 A だけを消費して続行する失敗が、親の未処理停止による系列欠測へ変わり、LLM arm の完走集合を変える。

3. **should — toolchain の「固定」と「試走観測・本走時記録」が区別されていない**

   根拠: [README:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/output/insights/2026-09-22/t2797-effect-bundle/README.md:50)、`E/bundle/b5-effective-bundle.draft.json:51–57`、`docs/b5-generator-contrast-preregistration.md` §12。

   試走 receipt の gcc/g++ 11.4.0・cmake 3.22.1 は一次資料と一致した。しかし JSON は明確に `toolchain_observed_in_pilot` であり、本走は各 job で記録するとしか定めていない。README の状態欄「固定」に対応する、本走で要求する版と不一致時の文書上の扱いがない。

   自動比較 gate を足す必要はない。試走観測値と本走の要求値を分け、手順上の確認・不一致時処理を明示すればよい。

   **成果物への影響:** 異なる toolchain の本走 receipt が得られた場合、発効束への適合・不適合を一意に決められない。

4. **should — prompt 変更が D-3 (1)〜(7)「だけ」という記述は厳密には成立しない**

   根拠: [LLM tool:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/tools/b5_llm_round.py:382)、同 `:395–397`、`E/README.md:83`、段 4 D-3(5)。

   裁定の欠測変更は CV についてだが、実装は fitness・anomalies・median・反復数・rounds・settled・abort・IPC 等も変更する。例えば欠測反復数は試走版の `0` から `null (欠測)`、IPC は `None` から `null (欠測)` になる。実装子 B はこの拡張を報告済みである。

   欠測を正しく示す方向の変更であり、撤回を要求するものではない。ただし変更一覧に明示して裁定と合わせる必要がある。MB8 の golden は planner/coder の初回だけなので、この critic 差分は検証範囲外。

   **成果物への影響:** critic が受け取る prompt bytes と欠測解釈が、束の列挙した差分より広く変わる。

5. **nit — 費用模型に中間値の丸め規則が記載されていない**

   根拠: [cost-model.txt:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-effect-bundle/output/insights/2026-09-22/t2797-effect-bundle/bundle/cost-model.txt:1)、同 `:8–9`。

   記載式を直接計算すると balanced の C は `274.5〜724.9 s`、read-heavy は `815.75〜1005.45 s`。表はそれぞれ `277〜727 s`、`817〜1007 s` を使用している。検査秒を整数へ切り上げれば表を再現できるが、その丸めが書かれていない。

   **成果物への影響:** 表の総和は整合するものの、読者が記載式から再計算した費用と小差が生じる。k=3・40倍の推奨を覆す差ではない。

追加実装を伴う案は **裁定パッケージ候補** として分離する。所見1を解決するための最終 critic 待ち、model 記録を読む report、台帳への不一致 field の追加は、現 scope の必須修正としては提案しない。まず不一致処置の適用範囲を裁定するべきである。

## 総括

**NO-GO**

- **must-fix 1:** 最終 critic 不一致時の約束と、次の handshake が存在しない実経路の不整合。
- **must-fix 2:** A-only 拒否時の親手順の欠落。a を進め、k を維持する分岐を明記する。

攻撃が成立しなかった項目:

- registered header は既存 report の受理条件と整合する。pilot の header・既存 launcher の env/argv を変更する差分は見つからなかった。
- purpose は shell の env 衛生で消えず、registered だけが driver argv に追加される。非 B-5 への混入は拒否される。
- schedule は D-2 と一致。117 job、各 block/stage の LLM 4 本、各 workload の6順序各2回、先後2対ずつを確認した。
- Decimal の切り上げ・walltime 書式、job 別 tree、全件事前検査、dry-run の処理、投入失敗時停止に成立する攻撃は見つからなかった。
- a/k 分離、初回診断なし、両役割への診断継承、既存継承検査、inputs→proposal 公開、上書き拒否、知識解決の fail-closed は保持されている。
- `record-models` は全 assistant 行を走査し、混在 ID・model 欠落・role 不一致・壊れた JSON を不一致として記録する。収集集合と `matches_expected` の逆転は見つからなかった。
- legacy＋動作点 trace 5、anomaly 即 reject、trace-disabled bench を弱める変更はない。規律6の文言と既存検疫も保持されている。
- MA1〜MA16・MB1〜MB8 は静的には対象変更へ到達する。MA6 は LLM 本数だけでなく順序出現数も検査する。MA15/16 の stub は周辺実行を置換するが、対象の shell 検証・argv 構築は実物を通る。**変異の KILLED は未確認。**
- 事前登録の **51,385 bytes・raw hash・blob・最終変更 commit**、`files_sha256` 全31件、束内の hash 付き参照は一致した。CCBench pin と gitlink の区別、環境契約 `e576e9cd…`／較正 `753f535a…` も一致した。
- random 1,080値・棄却 counter 全0、sweep 36系列、重み表と M は再計算と一致した。
- rep 1 は53 session、最大差 **0.6960199%**、1%以上0件、CV境界変化0件、rep 1最大36件、round数全1で一致した。費用表の総和と40倍上限の算術も一致した。
- N1 の初回 skip で B が少なく残り、report の invalid では拾わず score 欠測になる説明は実コードと整合する。
- 実走 prompt・観測 model ID・承認情報を実走／承認後の値と区別すること自体に欠陥は見つからなかった。