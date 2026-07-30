## Findings

1. **must-fix — 通常 `AI-Agent` と correction を別 trailer block に置いても受理される**

   [`_ai_agent_values()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:197) は divider 有効の既存 parser、[`_correction_audit()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:222) は `--no-divider` の隔離 parser を別々に使います。[抑止条件](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:558) は両 parser が同じ block を見たことを確認しません。

   次の correction message は現実に、前半 parser が `AI-Agent`、後半 parser が correction を返します。

   ```text
   subject

   AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; role=author
   ---
   body

   AI-Agent-Correction: target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
   ```

   Git parser の read-only probe でもこの分離を確認しました。これは plan の「[同じ最終 trailer block](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:44)」に反します。既存テストは parser 差を明示的に pin していますが、correction と組み合わせていません（[test:401](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:401)）。

   影響: 不正に分離された correction commit が受理され、target の missing finding が消えるため、監査の受理集合が拡大します。

2. **must-fix — 失敗時にも stdout が裸の `forward-corrected=1` を出す**

   [`main()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:676) は corrected record を findings 判定より先に stdout へ出します。target の CAB finding や別 commit の missing findingが残る rc=1 でも同じです。テストもこの挙動を正として固定しています（[test:1387](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1387)、[test:1408](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1408)、[test:1479](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1479)）。

   内部で suppression record を保持すること自体は妥当ですが、失敗時は stdout に成功形を単独表示せず、少なくとも `overall=fail` を同じ record に固定する必要があります。

   影響: exit code の受理集合は変わりませんが、stdout-only consumer・ログ・人間レビューが失敗監査を green と誤認する failure mode が残ります。

3. **should-fix — `_commit_exists()` が Git の全 rc=128 を「object 不在」に畳む**

   [`_commit_exists()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:579) は rc=128 を無条件に `False` とします。missing object だけでなく、object DB破損、permission、repository discovery failure 等も rc=128 になり得ます。その場合、実行不能 rc=2 ではなく通常の missing-target rc=1になります。テストは正常な missing object だけです（[test:1663](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1663)）。

   影響: green にはなりませんが、監査基盤障害が policy violation に誤分類され、復旧・停止判断の failure mode が変わります。

4. **should-fix — singleton 内に target/key の独立 drift 面が残る**

   key は [regex](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:51) と [spec.key](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:79) に別記され、target は `spec.target` と payload 内に二重記載されています。例えば `spec.target=B`、payload 内 `target=A` という状態でも、[payload exact 判定](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:100) と [target lookup](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:530) は独立して成立し、B の finding を A と記した payload で相殺できます。

   production literal pin は有効な独立 oracle ですが、runtime invariant の代わりではありません。

   影響: 将来の片側 drift で、payload が名指す SHA と実際に相殺される SHA がずれ、誤った target が受理されます。

5. **should-fix — 必須境界の追加テストが不足**

   実装は現状正しく見えるものの、次が固定されていません。

   - `--all` 等の複数 tip selected set。
   - target object は存在するが current HEAD の ancestry 外である message-file。
   - 既存 candidate が merge の非 first-parent 側だけにある message-file。現テストは線形履歴だけです（[test:1640](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1640)）。
   - correction value の no-space、tab、二重空白、末尾空白、および key 前の indent。
   - finding 1 の divider 分離。

   具体的には既存探索を `rev-list --first-parent HEAD` へ狭める mutant は現在の M9 テストを通し得ますが、merge-side の既存 candidate を見落として二件目を preflight 受理します。

   影響: 現在の受理集合を直接変える所見ではありませんが、上記の受理集合拡大を起こす回帰・mutant が生存します。

## Refuted

- **refuted — Git graph と exact 1 finding suppression の基本構造**
  [`_audit_history()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:493) は set membership、selected-set candidate 総数、global strict ancestry を分離しています。`T^!`、`C^!`、sibling、later merge、duplicate candidate は期待どおり赤です。抑止対象も full SHA と exact finding の組です（[line 566](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:566)）。target CAB、merge-side missing、別 commit finding は保持されます。

- **refuted — correction 自身の通常 finding の短絡**
  [line 564](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:564) の `not correction.normal_findings` により、missing、format、scope、CAB、Codex-author finding のいずれでも target missing は相殺されません。finding 1 の「parser view 分離」だけが例外です。

- **refuted — raw/canonical multiplicity と payload drift**
  [lines 224–262](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:224) は continuation、body-only、body+trailer、複数 raw、unknown/field driftを閉じています。payload 値の tab・余分な空白も raw exact 比較で拒否されます。key と colon 間の空白/tab は adjudicated plan が「raw value exact」とした範囲では canonical-equivalent です。

- **refuted — `_is_descendant()` と既存 CAB/scope の fail-open 回帰**
  [`_is_descendant()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:354) は rc=0/1だけを意味値として扱い、その他を例外化しています。通常監査の CAB/scope/implementation 順序も [`_normal_commit_audit()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:457) へ実質そのまま移されています。

- **refuted — message-file が既存 candidate を実装上 first-parent に限定している**
  [line 628](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:628) は `rev-list HEAD` の全 reachable ancestry を走査します。target existence、HEAD ancestry、実欠落も別々に検査し、成功表示は通常 child を「仮定」と明記しています。ただし finding 5 のテスト不足は残ります。

### M1〜M11 の静的対応

| 境界 | テスト |
|---|---|
| M1 membership | `C^!` main-level反例 [1261](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1261) |
| M2 strict descendant | sibling＋later merge [1320](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1320) |
| M3 literal/payload exact | production pin [1052](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1052)、field drift [1172](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1172) |
| M4 cardinality | duplicate commit [1365](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1365) |
| M5 raw line | continuation [1101](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1101) |
| M6 actual missing | valid target [1586](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1586) |
| M7 exact target only | side/target/other findings [1387](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1387) |
| M8 correction normal green | finding matrix [1504](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1504) |
| M9 existing candidate | message-file second candidate [1640](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1640) |
| M10 status | rc=0 range [1288](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1288) |
| M11 multiplicity | body＋valid trailer [1120](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1120) |

M1〜M11 は少なくとも意味のある main-level／単体反例を持ち、単なる実装内部の恒真確認ではありません。ただし M9 の topology と M5 の whitespace 弱化は finding 5 の追加反例が必要です。

## 総括

**NO-GO。**

blocker は次の2件です。

- 異なる parser view の trailer block を合成して correction を受理できる。
- findings が残る rc=1 でも stdout が裸の `forward-corrected=1` を出す。

pytest は指示どおり実行しておらず、green は主張しません。編集・commit・ファイル生成も行っていません。