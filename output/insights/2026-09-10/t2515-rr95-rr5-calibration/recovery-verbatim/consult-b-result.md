結論は「planは概ね正しいが、実起動 harness の interpreter 識別が1点不足」です。T-2535 consumer の2境界修正は必須です。T-2536の変更追加は不要です。

## Real

1. **real / must-fix: interpreter stub が M8 を動的には識別できません。**

   [`test_pegasus_calibration_workload.py:483`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:483) は `fake_bin/python3`だけを作り、[`同:487`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:487) では `$@`だけを記録します。planどおり同じstubを`CALIBRATE_PYTHON`へ設定すると、正しい明示pathとM8の裸の`python3`が同じ実体へ到達し、実起動結果は区別できません。

   最小修正は、記録用`python3.10`を`CALIBRATE_PYTHON`へ設定し、PATH上の`python3`には終了97などのpoison stubを別置することです。これなら[`certify_calibration.sh:405`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:405)の参照が裸へ戻るM8を実起動で殺せます。productionへの追加関門は不要です。

2. **real / must-fix: T-2535由来のconsumer境界はplan記載の2件とも修正必須です。**

   - [`test_pegasus_tools.py:255`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:255)は現在`CALIBRATE_PYTHON=""`から`# CLI`までを抽出します。選定前倒し後はgflags、glog、関門まで巻き込みます。選定ブロックと後段PATH shimを別抽出して連結する修正が必要です。
   - [`test_pegasus_tools.py:1134`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:1134)は`run_condition_gate()`直前までをtoolchain fragmentとしています。前倒し後はinterpreter選定まで実行するため、終端を選定ブロック直前へ狭める必要があります。
   - [`test_pegasus_calibration_workload.py:443`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:443)には`CALIBRATE_PYTHON`の注入自体も必要です。ただし上記の別stub方式にします。

3. **real / 証拠限定: 旧報告の「8/8 killed」は「8件すべて実効性kill」とは言えません。**

   - M1、M2はclean fixtureで5、95の受理を実行しており、強い動的証拠です。
   - M3、M4は受理集合への実害がありますが、旧走では主にliteral抽出で赤になっています。
   - M5、M6は受理集合を広げる実害がありますが、旧走の赤は[`submit_certify.sh:109`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:109)のdirty検査まで進んだ結果でした。[`test_pegasus_calibration_workload.py:1402`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1402)が要求するrratio診断との差は関門通過を示しますが、cleanなqsub経路の実行証明ではありません。
   - M7は[`同:1616`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1616)のREADME文字列だけです。これはdocs整合のnitで、runtime実効性には数えません。
   - M8は参照先を未smokeの`python3`へ戻す実害があります。ただし旧killはsource文字列assertだけです。上記の別stub修正で動的証拠にできます。

   最小対応は、合成HEADで再走した上で「material mutationはM1からM6とM8、docs-onlyはM7」と分類して記録することです。

4. **real / 保存必須: 旧枝や旧fileの置換はconsumerを大量に落とします。**

   T-2536の軸とcache写像検査は[`test_pegasus_calibration_workload.py:41`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:41)以降、T-2535のoffline実起動consumerは[`同:443`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:443)以降にあります。さらにsubmit fixtureのstaging作成は[`同:1467`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1467)と[`test_pegasus_tools.py:1643`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:1643)にあります。すべて保持対象です。

## Refuted / 範囲外

- **refuted:** T-2536 consumerを今回のrratio、interpreter変更に合わせて書き換える必要はありません。特に[`test_pegasus_calibration_workload.py:210`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:210)と[`同:301`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:301)のBACKOFF_FIXED期待は、後続裁定の実装waveが扱う対象です。今回変更すると別件実装になります。
- **refuted:** T-1851、T-2417の指定branch tipと対象4ファイルの差分は0でした。T-2535、T-2536は現HEADの祖先であり、現在の問題は所有重複ではなく既存consumer保存です。
- **範囲外:** `THIRD_PARTY_VERIFY_PYTHON`の統合、resolver共通化、BACKOFF_FIXED撤去、fixture共有化、schema変更、追加測定は不要です。
- **nit:** [`certify_calibration.sh:664`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:664)の「separate user ruling待ち」というコメントは後続裁定後には古いですが、挙動への影響はありません。今回直すなら「本回収では既存挙動を維持する」程度のコメント訂正だけで、撤去実装へ広げません。
- 親の`7 failed / 1360 passed / 4 skipped`は未解消です。calibration単独58 passedは局所的な反証になりますが、全受入の緑ではありません。floor切分完了前に実装や期待値を緩める根拠にもなりません。
- read-only指示に従いpytestは実行していません。accepted calibration生成も主張できません。988706、988708は次のBACKOFF関門まで到達した証拠に限ります。

## 総括

採用すべき最小差分は、planの4ファイル合成に加えて、実起動consumerで`python3.10`記録stubと裸の`python3` poison stubを分離することです。T-2535のoffline供給、staging fixture、2つの抽出helperを保持し、T-2536と後続BACKOFF裁定には触れません。変異結果はM1からM6とM8をmaterial、M7をdocs-onlyとして報告し、旧8/8を一括して実効性証明とは扱わないのが妥当です。