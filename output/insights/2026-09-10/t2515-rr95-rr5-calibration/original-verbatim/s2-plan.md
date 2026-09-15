結論として、現状の制約には実装不能な矛盾が 1 件あり、pin 閉包も射影不足で完結できません。したがって、以下を条件付きプランとして親へ返し、実装段へは進めないのが正しいです。

## 裁定評価

- P1: 採用。射影内では A-6 の一次資料を再確認できないため解除とは主張せず、T-2515 の workload 別 calibration 不足だけを根拠にする。
- P2: 採用。受理集合は閉じた exact 集合 `{5,20,50,80,95}` とする。
- P3: 採用。[sweep.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/sweep.py:121) と [analyze.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/analyze.py:27) が飽和点または D15 の下限を決める。最終 records は固定しない。
- brief の A4 は誤り。[test_pegasus_calibration_workload.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:22) の `README` は `tools/pegasus/README.md` であり、`docs/pegasus-runbook.md` ではない。
- brief の「registered に JSON + md」は現行実装と異なる。[cli.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/cli.py:1025) は accepted JSON だけを registered へ publishし、md は attempt staging に残す。今回この成果物契約は広げない。

## 実装を止める理由

既存期待値を変えない制約と、95 を受理する目的が両立しません。

- [test_pegasus_calibration_workload.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:38) は旧 usage `20|50|80` を exact に要求する。
- [test_pegasus_calibration_workload.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:429) は 95 が rc=2 で拒否されることを要求する。
- [test_pegasus_calibration_workload.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:445) は旧 error 文字列を要求する。

これらを残したまま 95 を受理させれば受入全走は必ず赤です。旧文字列をコメントとして残す、skip/xfail にする、テストを削除する案はいずれも pin の検出力を壊します。ユーザー指示どおり、期待値は変更せず停止すべきです。

## 条件解消後の file:line プラン

| file:line | 変更 | なぜそこか |
|---|---|---|
| [submit_certify.sh:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh:7) | usage を `--rratio 5|20|50|80|95` にする。 | 公開 CLI の closed set を正確に表示する唯一の usage。 |
| [submit_certify.sh:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh:40) | exact 比較へ `"5"` と `"95"` を加え、error を `5, 20, 50, 80, or 95` にする。範囲判定や regex にはしない。 | policy 読込、tree 検査、directory 作成より前の投入側 gate。 |
| [certify_calibration.sh:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:15) | 現在の rratio gate を PBS 変数・job ID 検査の直後、`TMPDIR` 設定前へ移し、exact 5 値へ拡張する。ここでは stderr を直接出す。 | 現在の gate は `/scr` と repo `output` の作成後なので、「副作用前の拒否」を満たさない。gate を増やさず移動する。 |
| [certify_calibration.sh:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:154) | 旧 gate を削除し、移動先で設定した `CALIBRATION_RRATIO` を後続へ渡す。 | 二重化ではなく relocation とし、「追加 gate を新設しない」を守る。 |
| [test_pegasus_calibration_workload.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:35) | 許可される値を両 shell から抽出し、双方が exact に `["5","20","50","80","95"]` であることを pin。usage/error も新しい exact 文字列へ更新する。 | 片側だけの拡張、任意値受理、表示 drift を検出する。 |
| [test_pegasus_calibration_workload.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:429) | 旧「95 拒否」を未登録値の parameterized test へ置き換える。 | 95 は正例になるため、この期待値変更は不可避。 |
| [test_pegasus_calibration_workload.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:467) | dry-run helper に任意 `rratio` を渡せる引数を加え、5/95 の receipt と qsub export を検査する。 | 実 qsub なしで投入側の正例と伝播を確認できる。 |
| [test_pegasus_calibration_workload.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:639) | 既存 20/80 の docs pin は残し、5/95 の例も pin する。 | 既存 H1/H2 例を失わず、新 workload の sanctioned argv を文書化する。 |
| `tools/pegasus/README.md:<H1/H2 節>` | 20/80 の例を残して rr95/rr5 の投入例を追記する。 | 実際にテストが読む docs はこのファイル。射影されていないため実 line は確定不能。再 dispatch が必要。 |

次は変更しません。

- [cli.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/cli.py:913) の `("20","80")` は certification admission ではなく calibration observation capability の発行条件。capability は optional で、[sweep.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/sweep.py:106) は未発行でも通常の測定を続ける。
- [report.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/report.py:87) の accepted 8 条件。
- `schema_v2.py`、`admission_registry.json`、既存 registered 2 件。
- `docs/pegasus-runbook.md`。検索した射影範囲には `--rratio`、`"20"`、`"80"` の allowlist pin がない。

## pin 閉包

射影された実物で確認できた閉包は次です。

- [test_pegasus_calibration_workload.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:18): submitter、job body、`tools/pegasus/README.md` の path pin。
- [test_pegasus_calibration_workload.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:35): usage、`20/50/80` の比較、default、伝播、output 除外を pin。
- [test_pegasus_calibration_workload.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:65): job body に独立再検査と workload 記録があることを pin。ただし許可数値集合自体は pin していない。
- [test_pegasus_calibration_workload.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:429): 95 拒否、旧 error、attempts 未作成を pin。
- [test_pegasus_calibration_workload.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:639): `tools/pegasus/README.md` の `--rratio 80` と `--rratio 20` を pin。
- [pegasus-runbook.md:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/docs/pegasus-runbook.md:507)、[同:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/docs/pegasus-runbook.md:558)、[同:800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/docs/pegasus-runbook.md:800): script path と certification 経路のみ。値や usage は pin しない。
- D15 と D1488 の指定節にはこの allowlist の文字列 pin はない。

`tools/pegasus/README.md` 自体が射影外なので、その docs 側の実 line と、repo 全体の tests/docs 閉包は証明できません。完全な pin 閉包には同 README を必読射影へ追加した再 dispatch が必要です。

## テスト設計

| 層 | 正例 | 負例と副作用検査 |
|---|---|---|
| 投入側 | 5、95、加えて既存 20/50/80 を `--dry-run` し、pre-submit の int、receipt の文字列、`-v` export が入力と一致すること。 | `0`、`100`、`51`、空文字、`95 `。非 0、期待 error、`attempts` 不在を確認。空文字は現在 `${2:?}` が gate より前に拒否するため、rc=2 の一律化は要求しない。 |
| job body | source から移動後の exact gate を抽出実行し、5/95 と既存 3 値が `CALIBRATION_RRATIO` へ到達すること。 | 各未登録値で job script を安全な PBS env 付きで直接起動し、rc=2、`/scr/<job-id>` 不在、repo の job-staging 不在を確認。submit receipt は用意せず、ratio gate がそれ以前に発火することを証明する。 |
| 集合閉包 | 両 gate の比較 literal を抽出し、双方が同一の 5 要素集合であること。 | 片側から 1 値を削る、51 を加える、範囲判定へ変える変異で赤になること。 |
| 静的 | `bash -n` を両 shell に実施。 | `report.py`、`schema_v2.py`、既存 registered bytes に base commit から差分がないこと。 |

accepted の条件は変更しません。[report.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/report.py:87) の 8 条件は、TSC、cooldown、完全 rep、必須 metrics、正当な selection、CV 5% 以下、isolation、post-attestation 一致です。さらに [cli.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/calibrator/cli.py:1002) の effective-clock 判定と schema 検査もそのままです。

テストは実走していません。

## 受理集合

変更前を `S0={20,50,80}`、変更後を `S1={5,20,50,80,95}` とします。

- `S1 - S0 = {5,95}`
- `S0 - S1 = {}`
- 両 shell の抽出集合が `S1` と exact 一致
- `0,51,100,"","95 "` はいずれにも含まれず拒否

これにより増分がちょうど `{5,95}` であることを、散文ではなくテストで固定できます。

## 投入手順

同じ worktree を使うなら、実装 commit 後に直列で次を実行します。

```bash
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh \
  --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5 \
  --rratio 95 \
  --protocol silo
```

rr95 の job が終端し、submodule worktree cleanup を確認してから:

```bash
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh \
  --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5 \
  --rratio 5 \
  --protocol silo
```

投入側の前提は [submit_certify.sh:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh:51) 以降から次のとおりです。

- job script、policy、非 symlink の calibration policy が実在する。
- HEAD が完全な 40 桁 commit。
- [submit_certify.sh:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/submit_certify.sh:94) の scope、すなわち repo 全体から top-level `output` だけを除いた tracked/untracked 状態が clean。
- legacy `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` が未設定。
- `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` がすべて成功する。
- 実測は計算ノード。submitter は login 側の sanctioned 経路。

## 同時投入リスク

同じ submit tree からの同時投入は避けるべきです。[certify_calibration.sh:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:536) で両 job が同じ `external/ccbench` gitdir に対し、[同:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:543) の `git worktree add` と [同:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:900) の remove を並行実行します。

実 build と `/scr` path は job ID ごとに分離されますが、worktree 管理 metadata は共有 writer です。[pegasus-runbook.md:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/docs/pegasus-runbook.md:1344) と [同:1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/docs/pegasus-runbook.md:1369) の独立条件を満たさず、add の名前・lock 競合や cleanup 干渉を排除できません。

回避は必要です。最小策は上記の直列投入です。並行化するなら、外側の submit tree だけでなく `git -C external/ccbench rev-parse --absolute-git-dir` が互いに異なる二つの clean treeを用意し、出力回収先も分離する必要があります。

## 総括

既存テストの「95 拒否」を維持する制約と目的が矛盾するため、現状は実装段へ進めない。  
許可後は submitter と job body を exact `{5,20,50,80,95}` へ揃え、job gate を副作用前へ移す。  
accepted 8 条件、schema、records 決定、既存 registered bytes は変更しない。  
docs の正しい対象は射影外の `tools/pegasus/README.md` なので再 dispatch が必要。  
同一 submodule gitdir からの同時投入は避け、直列または gitdir が分離された二 submit tree を使う。