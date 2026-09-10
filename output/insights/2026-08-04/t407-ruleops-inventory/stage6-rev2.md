結論は **NO-GO**。静的には事前登録 M01〜M12 はすべて殺せる。ただし、裁定の一般契約を破りながら現テストを通過できる未登録変異を 3 件確認した。テストは実行していない。

## 変異 M01〜M12 の殺傷判定 (表 + 根拠 assertion)

| 変異 | 判定 | 赤になる assertion と入力 | 未検出時の成果物影響 |
|---|---|---|---|
| M01 | KILLED / real | 全 3 path が非 UTF-8 の repo で CLI が rc=2 となり、[`result.returncode == 0`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:529) が `2 != 0`。 | inventory が生成できず、レポート・ledger 候補母集団が失われる。 |
| M02 | KILLED / real | matrix で全 item を `continue` すると counter は 0、全件加算型でも selected 17 件となる。どちらも [`skipped_non_utf8 == 6`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:416) が不成立。UTF-8 control も消えるため [control subset assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:421) も偽。 | `items` が空または過少となり、レポートと候補集合が壊れる。 |
| M03 | KILLED / real | 非 UTF-8 `.raw` は 1 path だけなので、`.raw` だけ skip すると counter=1。[`== 6`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:416) が失敗する。 | `.py/.md/.json/.sh` の非 UTF-8 が `items` に混入し、受理集合と件数が変わる。 |
| M04 | KILLED / real | 非 UTF-8 insight は 5、direct test は 1。insight だけ skip すると matrix の [`== 6`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:416) が `5 != 6`。kind 内訳も [期待 `1/5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:446) に対して test=0 となる。 | test-kind の候補母集団へ非 UTF-8 が残り、レポートの内訳も誤る。 |
| M05 | KILLED / real | skip だけ行い加算しなければ、matrix の [counter assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:416) が `0 != 6`。 | `items` は正しくても `skipped_non_utf8` が過少となる。 |
| M06 | KILLED / real | kind 外も数えると `all/test/insight` は `6/6/6`。[`{"all":6,"test":1,"insight":5}`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:443) との equality が失敗する。 | kind 別レポートの分母と skip 件数が誤る。 |
| M07 | KILLED / real | 別セルに同一 bytes の 2 path が実在する（[書込み](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:514)、[OID 同一 assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:523)）。unique OID は shared 1 + direct test 1 = 2 なので、[`count == 3`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:532) が失敗する。 | 同一 blob を持つ複数 path が過少計上され、レポート件数が誤る。 |
| M08 | KILLED / real | 同一 `.raw` path の UTF-8+NUL 状態でも `.raw` 数は 1。opaque 時の `selected_count` は 6、readable 時は `items=6,count=1` で 7 となり、最初に [保存 assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:471) が `7 != 6`。続く [`count == 0`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:472) も失敗する。 | 内容遷移後も counter が残り、レポート値が stale になる。 |
| M09 | KILLED / real | NUL control は [`b"opaque\x00payload\n"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:193) で、fixture 自身が [strict decode 成功](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:206)を確認する。これも skip すると counter=7 となり [期待6](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:416) が失敗し、[membership assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:432) も偽。 | valid UTF-8 item が候補母集団から消え、counter が過大になる。 |
| M10 | KILLED / real | scope 外に非 UTF-8 regular blob が 2 件実在する（[`docs/` と `output/campaigns/`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:491)）。数えれば2となり、[期待0](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:505) が失敗する。 | inventory 外のファイルで skip 件数が膨らみ、レポート母数が誤る。 |
| M11 | KILLED / real | 全 selected が非 UTF-8 の repo で rc=2 に戻れば、[`returncode == 0`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:529) が失敗する。さらに [`items == []`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:531) と count=3 も固定済み。 | 正当に空の inventory が拒否され、レポート・ledger 作成経路が停止する。 |
| M12 | KILLED / real | v1 のままなら、matrix の [`schema_version == "ruleops-inventory/v2"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:414) が `"v1" != "v2"`。 | v1 名で v2 shape を出し、consumer の schema 受理・参照が二義化する。 |

## SURVIVED と判定した変異 (あれば)

事前登録された M01〜M12 に SURVIVED はない。

これは静的な反実仮想判定であり、mutation harness の実走結果ではない。また、下記の未登録変異が生存するため、M01〜M12 全殺だけでは十分でない。

## 恒真性と過適合

| 新規テスト | 削除してもそのテストが緑のままになる側面 | 判定 |
|---|---|---|
| `test_inventory_non_utf8_skip_matrix_and_utf8_formats` | schema、decode、counter、`continue`、root key の各変更は削れない。一方、[`_markers` 呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:673)を常に `(None, None)` にしても、assertion は BOM の `(None,None)` だけなので通る。 | **real**。typed insight の marker 保存に対して一方向の恒真。成果物影響は report item の marker 欠落。 |
| `test_inventory_non_utf8_counter_respects_selected_kind` | schema v2 化を削っても通る。また counter 加算を残したまま `continue` だけ削ると invalid item が混入するが、item の kind 集合は依然 `test` / `insight` なのでこのテスト単体は通る。 | **real / nit**。matrix の membership assertion が横で殺すため suite-level の成果物影響は残らない。 |
| `test_inventory_non_utf8_counter_tracks_same_path_content_transition` | schema v2 化は検出しない。`selected_count` は [最初の実装出力から算出](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:463)しており独立 oracle ではない。 | **real / nit**。直接の count・membership assertion が M08 を殺すため、登録変異への成果物影響は閉じている。 |
| `test_inventory_non_utf8_counter_excludes_out_of_scope_and_nonregular` | decode/skip 実装を丸ごと削除して counter を常に0にしても、このテスト単体は前後とも0で通る。 | **real**。negative-only。ただし matrix/all-selected が全削除を殺す。non-regular の別穴は後述。 |
| `test_inventory_all_selected_non_utf8_succeeds_and_counts_paths` | 変更された schema、decode、counter、`continue`、root key のどれを削っても assertion/error になる。 | 攻撃したが破れなかった。 |
| `test_inspect_non_utf8_target_fails_closed_without_traceback` | inventory v2 の全変更を削っても通る。別経路の [`_inventory_item` strict decode](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1012)だけを固定する preservation test だからである。 | **real / nit**。inventory 検出力はないが、inspect の受理集合を守る独立目的としては妥当。 |

新規テストに `parametrize` はなく、parameter id と実装分岐の一対一対応はない。invalid path 名も `alpha`〜`echo`、`amber` など中立で、非 UTF-8/UTF-8 の期待を path から露呈していない。

ただし fixture の相関は残る。

- **real:** NUL 入り control は matrix の `india.raw` と transition の `quartz.raw` のみ。`.raw` 以外だけ NUL を除外する変異が生存する。
  成果物影響: valid UTF-8 の `.py/.md/.json/.sh` が `items` から消え、counter と ledger 候補母集団が変わる。
- **疑い:** 同一 OID control は insight `.raw` の 2 path だけ。global な M07 は殺すが、kind/suffix 条件付き dedupe は未固定。
  成果物影響: 条件付き実装が入れば duplicate direct test 等の skip 件数を過少計上する。

## 被覆の穴

裁定採用 #1〜#7 はコード上はすべて何らかの形で反映されている。ただし #3 と #5 は一般契約を十分に固定していない。

| 要求境界 | 状態 | 根拠 |
|---|---|---|
| zero case | 固定済み | [初期 repo で count=0](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:489) |
| scope 外非加算 | 固定済み | 非 UTF-8 regular blob 2件と [最終 count=0](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:505) |
| non-regular 非加算 | **部分的** | symlink payload は [`"../source.md"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:493) という valid UTF-8。gitlink は commit entry で decode 対象 blob ではない。非 UTF-8 symlink blob を誤って数える変異は発火しない。 |
| 全件非 UTF-8、rc=0/items空 | 固定済み | [rc/items/count assertions](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:528) |
| NUL 保持 | **部分的** | unconditional M09 は殺すが、NUL fixture がすべて `.raw`。suffix 条件付き NUL 除外が生存する。 |
| suffix 独立 | 固定済み | 非 UTF-8 `.py/.md/.json/.raw/.sh` は [fixture 6 cell](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:170)と count/membership で固定。 |
| 同一 path の内容遷移 | 固定済み | [非UTF-8→UTF-8+NUL→非UTF-8](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:455) |
| kind 内訳 | 固定済み | [`6/1/5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:443) |

加えて、retained item 値の preservation に穴がある。`_base_repo` には typed marker 付き insight が複数あるが、inventory marker の positive assertion は存在しない。repo 全体検索でも値を検査する assertion は BOM の `(None,None)` だけだった。`_markers` を常時 `(None,None)` にしても静的には全テストが通る。

裁定 #8 docs、#9 decisions、#10 採番、#11 brief/worklog は親担当として対象外。今回の2ファイルに無いことを欠落扱いしていない。

既存テストの弱体化はない。`git diff` のテスト削除は旧4-key `_INVENTORY_ROOT_KEYS` の1行だけで、5-key exact set へ置換されている。assertion の削除・緩和・skip 化はない。

## 新規テスト自体の健全性

- 攻撃したが破れなかった: 非 UTF-8 bytes はすべて `tmp_path` 配下の一時 repo にだけ `write_bytes` される。変更された2つの `.py` はともに UTF-8 text で、実 repo の `orchestrator/tests/` に binary fixture は作られていない。
- 攻撃したが破れなかった: `_base_repo` は [user.email/user.name を設定](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:120)し、独自 repo も [同じ設定を行う](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:511)。`tmp_path` による後始末境界も守られる。
- 攻撃したが破れなかった: hash、日時、実 repo 件数を期待値へ焼き込んでいない。同一 blob は動的取得した OID 同士を比較している。
- **real / nit:** function-scope の matrix fixture は3テストで再作成され、全新規テスト合計で静的に6 repo init・13 commit。matrix の3 consumer は read-only なので共有余地があるが、実測時間が無く、成果物の値・受理集合・参照には影響しない。

## must-fix (成果物影響つき)

1. **real — non-regular 境界を非 UTF-8 payload で発火させること。**  
   現 fixture の symlink blob は valid UTF-8 である。in-scope mode `120000` blob の payload 自体を非 UTF-8 にし、「non-regular を decode して失敗時だけ counter 加算する」変異を殺す assertion が必要。  
   成果物影響: 放置すると `skipped_non_utf8` が非 regular path 分だけ過大となり、RuleOps レポートの母数が誤る。

2. **real — NUL control を `.raw` 以外と直交させること。**  
   少なくとも `.md` または direct `.py` に strict UTF-8 の NUL 入り control を追加し、membership と counter 不変を固定する必要がある。  
   成果物影響: 放置すると valid UTF-8 の非 `.raw` item が候補母集団から消え、counter、レポート、ledger 作成前の受理集合が変わる。

3. **real — retained marker の positive preservation を固定すること。**  
   typed insight の `authority_marker == "none"` と `default_effect_marker == "no-state-change"` を1件以上 assertion する必要がある。現在の BOM negative だけでは `_markers` 常時 None 変異が生存する。  
   成果物影響: inventory/report の marker 値が null へ退行し、typed insight の authority/default-effect 参照が失われる。

## nit / backlog

- **real / nit:** transition の `selected_count` は実装出力由来で、独立した literal oracle ではない。直接の count・membership assertion が M08 を殺すため、現成果物への残存影響はない。
- **疑い / backlog:** shared OID cell が insight `.raw` に偏る。kind/suffix 条件付き unique-OID 計数を将来防ぐなら、direct test 側にも同一 bytes 2 path を置く余地がある。放置時の潜在影響は duplicate test path の counter 過少。
- **real / nit:** matrix repo の三重構築は削減可能。正しさ成果物への影響はない。

## 攻撃したが破れなかった点

- M07 は matrix の「6 bytes 全て異なる」とは別に、同一 bytes・同一 OID の複数 path cell が存在し、count=3 assertion まで接続されている。
- M08 は valid `.raw` 状態でも `.raw` 件数が1のままなので、payload を見ない計数を実際に破る。
- M10 の scope 外 control は存在するだけでなく、2件とも非 UTF-8 regular blob として commit される。
- M06 は `all/test/insight` の literal 内訳を固定しており、production の kind 集合から期待値を導出していない。
- M09 の control は fixture 内で strict UTF-8 decode 成功を確認し、count と membership の双方で unconditional NUL skip を破る。
- invalid bytes は6セルで相異なり、direct test は PEP 263 Latin-1 sourceとして `compile` 可能。path 名にも encoding の答えはない。
- 既存 assertion の削除・緩和はない。

## 総括 (GO / NO-GO を明記)

**NO-GO。**

M01〜M12 はすべて静的に KILLED と判定できる。しかし、non-regular の非 UTF-8 payload、非 `.raw` NUL、typed marker positive preservation の3契約には、成果物を変えながら現テストを通過できる未登録変異が残る。親の「89 passed」は通常実装の基線を示すだけで、この検出力不足を反証しない。