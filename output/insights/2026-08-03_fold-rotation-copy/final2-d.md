結論は **NO-GO**。現在の差分では、ruling 5 件と本 wave fragment を同時に fold すると `rotation-capacity` で計画段階から失敗し、実 land に到達しない。

### 所見 1 — must-fix: 6 fragment 後の worklog が、現行ローテーションでも 100,000 bytes を超える

**根拠 (file:line):** [`_rotate_worklog`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1594) は `original_entries[-1]` を必ず現行 worklog に残し、移動対象を fold 前から存在した entry に限定する（[1603–1611 の起点](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1603)）。超過すると `plan_fold` がそのまま失敗する（[spool_fold.py:1810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1810)）。land は候補 plan の例外を `fold-failed` に畳むため（[dev_wave_land.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1795)）、main は変更されない。

read-only の in-memory 再構成では、親の「ruling 2 件で 48,401 bytes」を再現した。同じ計算で：

- ruling 5 件適用後のローテーション済み worklog: **94,193 bytes**
- 本 wave の最小 fragment が作る entry: **10,268 bytes**
- 合計: **104,462 bytes**、上限を **4,462 bytes 超過**

最小 fragment は本文なし・1文字 title・T-352/T-357/T-358 の最短 completion で計算している。実際の記録はこれより大きいため、文章を縮めても回避できない。

**失敗シナリオ:** ruling 5 件と本 wave fragment を統合した tip を land する。全 fragment の遷移と `base:` が正しくても、`_rotate_worklog` が entry (121) を残した結果 100,000 bytes 以下にできず、`rotation-capacity` で plan が中断する。path closure、`docs/phase3.md` target、`check_docs.py`、transaction apply には到達しない。

**成果物影響:** worklog・phase3 発火記録・FOLDED receipt・rotation archive が一つも生成されず、T-352/T-357/T-358 を完了にできない。T-357 の実 land positive control も不成立。

**推奨:** projected worklog 上で分割点を選び直す。少なくとも、新 entry が存在する場合は元 worklog の最新 entry (121) も archive へ移せるようにし、最終 current worklog が上限以下になるまで連続した古い entry を移す。ruling 5 件＋本 wave fragmentを同時に入れる land 統合テストを追加し、現行の「元 latest を必ず残す」変異が赤になることを固定する。

### 所見 2 — must-fix: producer 文書に `見送り追記` の閉じた文法がまだ全部書かれていない

**根拠 (file:line):** 確定仕様は、section 使用時の1件以上、非空白 suffix、suffix placeholder、日付・回数・「発火記録:」を自動生成しないことまで要求する（[spec2.md:33](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/spec2.md:33)、[spec2.md:37](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/spec2.md:37)）。実装も空 section と shape を拒否する（[spool_fold.py:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:516)）。一方 README は「`見送り` の後」「1物理行」「base/H4なし」までで、これらを明記していない（[worklog README:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/worklog/README.md:71)）。

特に「`見送り` の後」は、`見送り` 節自体が省略可能な場合の相対順序だと明記しないと、本 wave のように新規見送りがない producer が空の `### 見送り` を足し、`defer-category` で失敗し得る。

**失敗シナリオ:** `/rulings` または dev-wave 段7が README の例を模倣し、空の `見送り` 節、空の `見送り追記` 節、または日付等を fold が補う前提の短い suffix を生成する。前二者は spool 全体を停止し、後者は検査を通っても発火履歴の意味が欠落する。

**成果物影響:** pending fragment 全体の fold停止、または `docs/phase3.md` の発火日・回数・経緯の欠落。

**推奨:** `docs/spool/worklog/README.md` に次を明記する。

- `見送り` が無くても `見送り追記` 単独でよい。両方ある場合だけ後順。
- section を置くなら1件以上、suffix は非空白。
- suffix 内 placeholder は許可され plan 時に解決される。
- 日付・発火回数・「発火記録:」は author が書き、fold は補わない。

トップ README の「ledger別 README も必ず読む」という dispatch（[docs/spool/README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/README.md:24)）により、`/rulings` command、Rulings Skill、`docs/dev-wave/core.md` からの導線自体は閉じている。禁止された3ファイルへの直接追記は不要。

## 本 wave fragment の check list

- [ ] 2026-08-03 に書くならファイル名は `2026-08-03-worktree-dev-wave-fold-rotation-copy-1.md`。frontmatter の `wave` も親裁定どおり `worktree-dev-wave-fold-rotation-copy` とする。
- [ ] `schema: izanagi-spool-v1` を維持し、worklog の必須6 field以外を足さない。
- [ ] H2 は `## 本文` → `## 次の一手差分` のちょうど2節。
- [ ] action は `### 完了` → `### 見送り追記` の順。空の `carry` / `見送り` は作らない。
- [ ] `### 完了` に T-352、T-357、T-358を各1回だけ置く。
- [ ] 各完了 item の末尾 field 群に `  remaining: none` をexact-oneで置く。
- [ ] 同じ末尾 field 群に `  base: <64桁 lowercase sha256>` をexact-oneで置く。`base` と `remaining` の順はどちらでもよいが、間に空行・comment・fence・散文を置かない。
- [ ] 完了本文に「残件あり」「一部完了」を書かない。
- [ ] `base:` は本 wave の完了文ではなく、**Fragment.key 順で直前までを適用した時点の active item本文**の digest。末尾LFを1個に正規化し、`base:`・`remaining:` は含めない（[digest実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:322)、[逐次base照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1310)）。
- [ ] 今回の確定 `base:` は以下。

  - T-352: `62a6450ee4ee027f39ba7ad040005430eb51475a89231c43f1582787936a889a`
  - T-357: `a6676c6c390a91cad56232506e9badf1c6db9e931098a780ce2222b7104e2d9e`
  - T-358: `cce7f7f2a76b950dcfb92c38d17798b75e5a37cd74bdcfdcf4c444209925ae46`

  T-352 は ruling seq 3 の更新後本文、T-357/T-358 は seq 2/4 の新規本文を `[T-357]` / `[T-358]` へ解決した後の digest。
- [ ] `### 見送り追記` は末尾に1節だけ置き、T-058/T-059をそれぞれ1物理行で書く。
- [ ] 形は `- [T-058] <suffix>` / `- [T-059] <suffix>`。target IDはplaceholder不可、`base:`・H4・継続行なし。
- [ ] suffix は空白以外を含み、対象 item 内の既存 suffix と同一でない。
- [ ] 日付、発火回数・経緯、「発火記録:」は fragment 本文に明記する。fold は自動生成しない。
- [ ] suffixでplaceholderを使うなら、本 wave内で定義された同一wave symbolだけにする。既存 D125/D127/D128 は literal IDで書ける。
- [ ] `Fragment.key` は wave が先頭なので（[spool_fold.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:94)）、`worktree...` が `rulings...` より後であることを `plan.fragments` でexact確認する。
- [ ] rotation修正後、統合tip上の `plan_fold` で6 fragment、`docs/phase3.md` target、rotation target、6 GC pathを確認する。
- [ ] `check_docs.py` は構文伝播の確認にはなるが、projected `base:` と追記対象の意味検査は `plan_fold` で初めて発火する。両方を確認する。

## land・回帰・波及の静的確認

rotation planが作れた後の経路には、別の blocker は見つからなかった。

- `docs/phase3.md` は追記により plan target へ入る（[spool_fold.py:1815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1815)）。
- target＋GCが path closureになり（[dev_wave_land.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1237)）、apply後に `check_docs.py`、pending=0、staged path exact equalityを検査する（[dev_wave_land.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1438)）。
- `docs/phase3.md` は fold commit の許可済み変更面に含まれる（[git_state.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:47)）。
- apply/check/commit失敗時はref・index・snapshot・transaction stateをrollbackする（[dev_wave_land.py:1313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1313)）。
- `check_docs.py` は `validate_spool_tree` を動的 importするため、新field検査の配線漏れはない（[check_docs.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:616)）。
- hooks に spool grammar producer/consumer はなく、変更根拠はない。

既存テストへの静的回帰も見つからなかった。`_worklog_body` の新引数はkeyword-onlyで、`completion_remaining=False` が既定のため既存helper出力を維持している（[test_spool_fold.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:118)）。既存の正常 completion call siteは明示的に `True` へ更新され、field欠落テストだけが意図的に既定値を使う。新テストは各 `tmp_path` 内の独立Git repoだけを変更し、環境変数・共有module定数を変更しない。pytest・actual landは実行しておらず、緑は主張しない。

## 総括

must-fix:

- ローテーション後でも6 fragmentで **104,462 bytes** になるため、projected entryを考慮して分割点を選ぶよう修正する。
- `見送り追記` の producer 文書へ、空section・空白suffix・placeholder・自動生成なし・`見送り`省略時の順序を追記する。

nit:

- なし。

scope外の裁定・既存タスク候補:

- 一般的な `base:` 算出・projected plan authoring支援は既存 T-354 の所有（[docs/worklog.md:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/worklog.md:1411)）。本 waveでは上記3 digestを固定して自己適用し、CLI一般化へ広げない。
- T-347、凍結ソース閉包、一般receipt identityには触れていない。