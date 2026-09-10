レビュー対象は、提示された規模と一致する commit `06396d0c^..06396d0c`（4 files、97 行純増）。静的検査のみ実施した。

## must-fix

ゼロ。

## nit

ゼロ。

## 反証結果

### 1. A-1 の恒真性

- 所見: A-1 は恒真ではない。
- 根拠: 新設負例は registry を含む `first_head` と、`later.txt` だけを追加した子 `second_head` を作り、6 report を 3+3 に分ける。[test_trial_registry.py:861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:861)  
  A-1 があると 4 件目で拒否される。[trial_registry.py:2506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2506)  
  A-1 を外すと receipt writer まで到達する。writer は A-2 parser を呼ばず、canonical bytes を直接作成するため、A-2 による mask もない。[trial_registry.py:2365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2365)
- 影響: mixed-head 束は従来 acceptance され receipt に記録されたが、今回から拒否される。
- 提案: 変更不要。
- 自己判定: `refuted`

### 2. A-2 の恒真性

- 所見: A-2 は先行する trial/campaign 集合検査に mask されない。
- 根拠: fixture は trial ID が `trial-0` から `trial-5` の昇順かつ campaign ID も6種類。[test_s8c_acceptance_receipt.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:75) 新設負例はこれらを変えず、1 row の head だけを別の実在 commit にする。[test_s8c_acceptance_receipt.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:172)  
  したがって trial/campaign の先行検査を通過し、A-2 だけが拒否する。[s8c_acceptance_receipt.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:329) A-2 を外せば parser は receipt を返し、後続 verifier は参照 hash を検査するだけで head 間一致を再検査しない。[s8c_acceptance_receipt.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:597)
- 影響: standalone verifier の受理集合が mixed-head receipt の分だけ実際に狭まる。
- 提案: 変更不要。
- 自己判定: `refuted`

### 3. A-1 負例の単一理由性

- 所見: 指定された別層による重複拒否はない。
- 根拠: 両 head は prereg の子孫であり、`first_head` は `second_head` の親でもあるため祖先性を満たす。[trial_registry.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:844) 子 commit は `later.txt` しか変えないので manifest/registry blob は同一で、historical blob、registry prefix、append-only history を通過する。[trial_registry.py:2582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2582)  
  lifecycle fixture は各 report 自身の head と bytes hash を投影し、production 側も trial ごとに同じ値を照合する。[test_trial_registry.py:1281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:1281) [trial_registry.py:2243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2243)
- 影響: A-1 を除去すると負例は acceptance されるため、M-1 の帰属は単一である。
- 提案: 変更不要。
- 自己判定: `refuted`

### 4. 現在 HEAD への過剰束縛

- 所見: A-1 は現在 HEAD との一致を要求しない。
- 根拠: 比較対象は最初に観測した report の head だけで、`current_head` ではない。[trial_registry.py:2509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2509) 既存の history 検査は過去 head が現在 HEAD の祖先であることを求めるだけである。[trial_registry.py:2102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2102)  
  正例は measurement head の後に unrelated commit を作り、古い head の6 report を acceptance へ渡すため、「現在 HEAD と一致」への変異を確実に殺す。[test_trial_registry.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:837)
- 影響: main が計測後に進んだ正当な束は引き続き受理される。
- 提案: 変更不要。
- 自己判定: `refuted`

### 5. 発火順序による既存理由の横取り

- 所見: 既存負例の期待理由を横取りする経路は見つからない。
- 根拠: A-1 は mismatched report の ancestry・historical 検査より前に発火するため、複数欠陥を含む仮想入力では理由の優先順位が変わり得る。[trial_registry.py:2506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2506) ただし既存 acceptance 負例は共通 head を `_reports` へ一度渡して6件を生成しており、新設 mixed-head 負例以外に report 間 head 差を持つものはない。[test_trial_registry.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:663)
- 影響: 既存 test の検出力や、単一欠陥入力の受理集合は変わらない。
- 提案: 変更不要。
- 自己判定: `refuted`

### 6. 受理集合とテストの甘さ

- 所見: 広げる production 変更も、他 gate を無効化する fixture 操作もない。
- 根拠: production の差分は A-1/A-2 の拒否分岐追加だけで、成功 return、schema、key 集合、reason code は不変。A-2 負例の再 commit は receipt を HEAD と一致させるためのもので、manifest・registry・lifecycle・report・journal bytes は変更しない。[test_s8c_acceptance_receipt.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:175) 後続 verifier はそれらを引き続き再 hash する。[s8c_acceptance_receipt.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:609)
- 影響: 変更方向は mixed-head 束の拒否に限定され、既存の参照検証は維持される。
- 提案: 変更不要。
- 自己判定: `refuted`

## 総括

must-fix、nit ともに所見ゼロ。  
A-1 と A-2 はそれぞれ独立に発火する具体的入力を構成でき、恒真ではない。  
A-1 負例は静的に単一理由であり、過去の共通 measurement head も引き続き受理される。  
既存負例の理由横取り、受理集合の拡大、fixture による他 gate の無効化は確認されなかった。  
pytest は制約どおり実行していないため、親の変異実走による最終裏取りが必要である。