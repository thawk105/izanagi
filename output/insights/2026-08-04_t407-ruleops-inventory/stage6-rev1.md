## 署名遵守の検証 (行を引く)

実装本体は攻撃したが、署名違反を作れなかった。

- `kind` 判定は regular-mode 判定より前で、`selected` には scope・kind・regular blob の三条件を通った path だけが入る。[tools/ruleops.py:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:645)
- counter はその `selected` の path 単位ループ内にあり、`UnicodeDecodeError` と同じ分岐で `+= 1` して直後に `continue` する。例外分岐内に早期 return はない。[tools/ruleops.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:660)
- decode 成功後は suffix、JSON/Python 妥当性、NUL、size による `continue` がなく、全 path が `items.append` へ到達する。[tools/ruleops.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:671)
- BOM JSON は `_strict_json` の `bom-json` を `_markers` が握って `(None, None)` にするだけで、item 自体は残る。[tools/ruleops.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:622)
- 同一 blob OID でも counter は OID 辞書ではなく `selected` path のループで増えるため、path 件数になる。
- 根の `skipped_non_utf8` は常時整数で出力され、snapshot 再検査は出力構築後・return 前の従来位置に残る。[tools/ruleops.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:686)
- CLI 出力は引き続き `sort_keys=True`、NaN 禁止、末尾 LF の canonical JSON である。[tools/ruleops.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:142)、[tools/ruleops.py:2219](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2219)

inventory 外の strict 境界も差分・実体の両方で無傷だった。

- `inspect`: [tools/ruleops.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1009)
- 共通 `_strict_json`: [tools/ruleops.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:191)
- receipt: [tools/ruleops.py:1310](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1310)
- ledger/check: [tools/ruleops.py:2023](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2023)
- insight candidate 本文: [tools/ruleops.py:1952](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1952)

`RuleOpsError("non-utf8")` も死んでいない。ledger/receipt の `_strict_json`、observed hit の `_blob_text`、`inspect`、insight candidate 本文から引き続き到達可能である。

## 実装とテストの共犯検査

### MF-1 — non-regular counter test は decode 不能な non-regular entry を作っていない

**real。**

裁定は scope 外 / non-regular の非計上を要求するが、追加テストの symlink target は ASCII の `"../source.md"` であり、strict UTF-8 decode 可能である。[test_ruleops.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:487)

したがって次の誤実装が静的に生存する。

- `items` は従来どおり regular mode だけから作る。
- counter だけは全 scoped blob mode を走査し、decode 不能なら加算する。

現在の symlink は decode 可能なので counter は 0 のまま、既存の symlink item 非掲載 assertion も通る。非 UTF-8 target bytes の symlinkを与えると、selected 外なのに counter が増えて署名を破る。

実装報告の「scope内symlink/gitlinkの非計上を固定」は、fixture の識別力について過大である。

**成果物影響:** 誤実装が受理されると inventory report の `skipped_non_utf8` が、`items` から一度も落としていない symlink path 分だけ水増しされる。

### MF-2 — size 上限を流用する誤実装が生存する

**real。**

署名は size による除外を明示禁止しているが、追加 control はすべて小さい。既存の oversize テストは ledger/receipt の拒否境界であり、inventory の retained-item 境界ではない。[test_ruleops.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:615)

例えば `entry.size > MAX_LEDGER_BYTES` の valid UTF-8 item を黙って `continue` する誤実装は、追加された全 synthetic assertion を通せる。real-repo test も inventory が非空で小さい特定 test path が残ることしか要求せず、大きい scoped path の membership を固定しない。[test_ruleops.py:1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1918)

これは `_markers` 内だけに閉じるべき `MAX_LEDGER_BYTES` を inventory 選別へ漏らす、十分に現実的な共有誤解である。[tools/ruleops.py:628](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:628)

**成果物影響:** 誤実装が受理されると、大きい valid UTF-8 insight が report の `items` と人間レビュー候補母集団から消え、`skipped_non_utf8` にも反映されない。

その他の fixture 攻撃では破れなかった。

- 6 個の rejected payload はすべて異なり、各 payload 自身を strict decode して `UnicodeDecodeError` を要求している。[test_ruleops.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:164)、[test_ruleops.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:200)
- Latin-1 direct test は第一行に有効な PEP 263 cookie があり、import 後の test 本体も truthy な `label` を assert するだけなので実行可能である。
- BOM、NUL、空 shell、UTF-8 だが構文不正な Python はすべて strict decode 可能で、membership が固定されている。[test_ruleops.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:178)
- 非 UTF-8 bytes は `tmp_path` 配下の synthetic repo にだけ書かれる。[test_ruleops.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:161)

## 受理集合の意図しない変化

production 差分で inventory 外の受理集合が動く経路は攻撃したが破れなかった。

- `INVENTORY_SCHEMA` だけが v2 になり、inspection、ledger、receipt、insight marker の各 schema は v1 のまま。[tools/ruleops.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:25)
- repo-wide caller 検索では `INVENTORY_SCHEMA` の production consumer は `build_inventory` の出力行だけだった。
- CLI の `inventory` / `inspect` / `check` dispatch は分離されたままである。[tools/ruleops.py:2203](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2203)
- D99 の対象 scope――direct test と `output/insights/**` の regular blob――自体は変わっていない。[docs/decisions.md:4395](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/decisions.md:4395)

`git diff --unified=0` で削除された test 側の行は旧 `_INVENTORY_ROOT_KEYS` 定義だけで、削除された `assert` は 0 件。現在の 5-key 定義への更新以外、既存期待値の反転・緩和・skip・削除はない。[test_ruleops.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:52)

## must-fix (成果物影響つき)

1. **MF-1 / real:** synthetic repo に strict UTF-8 decode 不能な target bytes を持つ in-scope symlinkを作り、`items` 非掲載かつ `skipped_non_utf8 == 0` を固定する。  
   **成果物影響:** 未修正なら、selected 外 symlink を inventory report の skip 件数へ混入させる誤実装を test gate が受理する。

2. **MF-2 / real:** literal な上限超過サイズの valid UTF-8 selected blob、望ましくは valid JSON を synthetic repo に置き、item retained・counter 不変を固定する。  
   **成果物影響:** 未修正なら、大きい valid insight を report の `items` と参照候補から黙って消す誤実装を test gate が受理する。

## nit / backlog

- **real / nit:** 既存 real-checkout test は `_REPO` の中身と `test_plain_runner_coverage.py` の実在に依存する。[test_ruleops.py:1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1918)  
  今回の差分が加えた依存ではなく、固定 hash・日時・総件数も焼いていない。現成果物への直接影響はないため nit とする。

## 攻撃したが破れなかった点

- kind filter より外の path、scope 外、symlink/gitlinkが実装の counter loop に入る経路。
- 同一 blob OID の複数 path が 1 件へ畳まれる経路。
- counter 加算と `continue` が分離される経路。
- 全件 skip 時の rc=2 復帰または snapshot 再検査回避。
- BOM JSON、NUL、空 file、構文不正 Pythonを content validity で落とす経路。
- `inspect`、receipt、ledger/check、insight candidate の strict decode 緩和。
- schema v2 が他 schema/version checkへ波及する経路。
- root key の型・canonical JSON・path sort の破壊。
- 実 repo の `orchestrator/tests/` へ非 UTF-8 fixture を生成する経路。
- 実装報告と差分のファイル所有・変更行の食い違い。material な差は MF-1 の「固定した」という証明上の過大主張だけだった。

## 総括 (GO / NO-GO を明記)

**NO-GO。**

production hunk自体には署名違反を発見できなかったが、MF-1 と MF-2 は、署名違反実装を緑のまま通せる実在の test gate 欠落である。親が実測した 89 passed はこの二つの witness mutation を識別しないため、契約充足の証拠にならない。テストは実行しておらず、以上は read-only の静的レビュー結果である。