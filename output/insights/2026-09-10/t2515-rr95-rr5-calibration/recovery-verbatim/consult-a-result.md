結論は「production合成は概ね妥当、ただし変異8/8の説明とF934の位置づけに修正必須」です。静的確認時点では4実装fileは未合成であり、pytestは実行していません。

## Real

1. M5/M6の旧expected nodeは、現mainでは実効性killを保証しません。

[submit_certify.sh:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:40)のrratio関門を正規化変異が通過しても、直後のoffline staging検査 [同:51](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:51)で同じrc=2になり得ます。一方、負例 [test_pegasus_calibration_workload.py:1402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1402)は後続前提を準備せず、error文字列も検査します。このためM5/M6がKILLEDでも、不正値の受理によるreceiptやqsub値の実害ではなく、診断文字列の相違だけかもしれません。

最小修正は、負例を三者staging付きclean fixtureと`--dry-run`で動かし、baselineではsubmissionが作られず、変異時にはrc=0またはreceipt生成まで進むことを観測することです。module fixture共有化は不要で、同test file内の既存helperを局所拡張すれば足ります。

2. 8変異は同じ強さではありません。

- M1/M2: 5または95がpre-submit、receipt、qsub exportへ届かなくなるので実効性kill。
- M3/M4: gate literalから受理集合の増減を直接検出するため、単なる診断文字列ではありません。ただしM4は同一test内の静的assertが先に落ちるため、job正例を実行した証拠とは呼べません。
- M5/M6: 上記のとおり、現main向けfixture修正前は診断文字列killの疑いあり。
- M7: README参照整合だけ。production実効性の証拠ではありません。
- M8: argvの構造検査によるkillです。実害は旧`python3`で落ちた988653/988654と、選定後に関門まで届いた988706/988708が別途裏付けますが、mutation run自体を実効性killとは呼べません。

M8もruntimeで殺すなら、[test_pegasus_calibration_workload.py:483](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:483)のrecorderを`CALIBRATE_PYTHON`専用名にし、PATH上の裸`python3`を失敗sentinelに分けるのが最小です。

したがって報告は「8/8 KILLED」だけでなく、「runtime実害、受理集合の構造検査、docs整合」を区別すべきです。

3. F934は、観測はrealですが前提はrefutedです。

988706/988708が`BACKOFF_FIXED`関門で赤になりaccepted calibrationが0件だった事実は残ります。しかし後続裁定は、define有無でbinaryが一致するため、不要な指定、宣言、専用条件要求を整合撤去すると確定しています。[new-rulings.md:59](/work/1/SFC/tanab/dev-wave-jobs/t2515-recovery-20260910/new-rulings.md:59)

従って旧説明の「必要な正しさ条件を関門が正しく拒否した」「patch materializeが必要」はrefutedです。正しい説明は「不要と裁定済みの旧条件が、今回scopeでは意図的に残されて停止した」です。

最小修正は説明だけです。現行の関門 [certify_calibration.sh:405](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:405)、silo限定呼出し [同:664](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:664)は今回削除しません。「別途裁定待ち」という古いコメントだけは「撤去は裁定済みだが別wave実装待ち」と訂正可能です。

patch materialize、schema拡張、項6の実装、新規測定は範囲外です。

## Refuted

- offline契約喪失: refuted。5個のFetchContent引数は [certify_calibration.sh:652](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:652)にあり、関門は`configure_argv[@]:5`を転送します。[同:413](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:413)
- verifier interpreterの混同: refuted。`THIRD_PARTY_VERIFY_PYTHON`は独立選定です。[同:556](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:556) `CALIBRATE_PYTHON`前倒し時にも統合・削除してはいけません。
- 承認外rratio受理: refuted。shell両側をexact `{5,20,50,80,95}`に揃え、入力の整数化はsubmit側関門後です。[submit_certify.sh:185](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:185) receipt文字列とjob envも再照合されます。[certify_calibration.sh:236](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:236)
- Python選定前倒しによる新たな過剰拒否: refuted。Python 3.10は従来もaccepted生成前の必須条件でした。[certify_calibration.sh:900](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:900) 変わるのは失敗位置であり、最終受理集合ではありません。
- 規律2違反: refuted。ただし今回、F934関門だけを部分削除する場合は違反方向です。項6は指定、宣言、専用条件要求を一括撤去し共通検査を残す別実装なので、本回収へ混ぜません。[main-update.md:4](/work/1/SFC/tanab/dev-wave-jobs/t2515-recovery-20260910/main-update.md:4)

## 総括

must-fixは2点です。

- M5/M6を後続offline失敗や診断文字列ではなく、不正値の実際の受理で殺すhermetic負例へ直す。
- F934を「正しい正しさ拒否」ではなく「不要と裁定済みだが今回scopeで残した停止条件」と記録する。

4実装fileの合成方針、offline 5引数、二重rratio検査、receipt束縛、独立verifier interpreterは維持可能です。accepted calibrationは0件、取得は認可済み、項6実装と測定は未完、という状態を崩してはいけません。