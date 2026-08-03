修正は working tree に残しています。docs 編集、commit / add / branch 操作はしていません。

## 対応表

| 赤の型 | 状態 | 対応 |
|---|---|---|
| T126 artifact 5件 | closed（pytest 未実測） | receiptless fixture を policy-bound lock＋canonical stock receipt に更新 |
| T126 driver 1件 | closed（pytest 未実測） | `SourceDigestSpy.STOCK` を実 module の公開面へ追随 |
| S6 sweep 1件 | closed（pytest 未実測） | screening fixture を source-bound generator receipt と正規 attempt topology に更新 |
| S8a sweep 1件 | closed（pytest 未実測） | S6 と同じ post-policy fixture に更新 |
| gate 回帰 | regressed なし（静的確認） | admission / qualification / sweep の production gate は変更なし |

変更箇所:

- [test_t126_qualification_artifacts.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h3/orchestrator/tests/test_t126_qualification_artifacts.py:246)
- [test_t126_qualification_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h3/orchestrator/tests/test_t126_qualification_driver.py:79)
- [test_s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h3/orchestrator/tests/test_s6_sort_sweep.py:522)
- [test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h3/orchestrator/tests/test_s8a_trigger_sweep.py:728)

## T126 の判断

(a) fixture を post-policy 形へ直しました。

`layer3_report` は admission 検証済み view を取得した後に、lock/WAL の qualification lineage を検査します。(b) の検査順変更では未検証 raw WAL を先に読むことになり、consumer の信頼境界を崩すため不適切です。historicity gate は維持しています。

## 検証

pytest 実行 nodeid: **なし**。

`hostname=pegasus02` で、AGENTS.md がログインノード上の pytest を単一 nodeid も含め禁止しているためです。したがって緑は主張しません。

実行済み:

- 所有 production/test の `python3 -m py_compile`: rc=0
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: rc=0
- docs / output 差分の追加なし

未実行:

- 指定された8 nodeid
- 所有 test file 全体
- フルスイート、build、campaign 実走

## 直さずに報告した項目

- `build_admission.py` / `source_digest.py` の production 公開面は不足していません。spy 側だけを修正しました。
- T126 の series identity / preimage / protocol / control pin は未変更です。
- admission gate、qualification production、S6/S8a production は今回変更していません。
- 所有外の残赤と、開始時から存在した所有外の未コミット差分には触れていません。

## 総括

残赤8件の合成 fixture を現行 admission policy に追随させました。T126 固有拒否へ到達できる post-policy campaign、sweep consumer が受理できる canonical generator receipt、実 module と一致する spy 公開面を整えています。実測だけは計算ノード側に残ります。