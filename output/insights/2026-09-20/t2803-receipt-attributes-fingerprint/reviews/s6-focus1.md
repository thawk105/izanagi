## 焦点再レビュー

**fix1〜fix3 の実装は GO。新規 must-fix はありません。** HEAD は `00d781372433147a35bf1099ececa9dc176e1924`。静的検査のみ実施し、変異実走・修正後 E-1 の結果は未確認です。

以下、C＝[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2803-provenance-receipt/tools/check_ai_provenance.py)、T＝[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2803-provenance-receipt/orchestrator/tests/test_check_ai_provenance.py)、R＝[段6裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/s6-ruling.md)、P＝[probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/probe/t2803_receipt_attr_cold_rate.py) とします。

| 所見 | 判定 (closed / partial / regressed) | 根拠 (行番号) |
|---|---|---|
| A-M1：候補追加時の属性消失 | **closed** | C2269–2308：監査範囲の merge 第1親 diff から祖先 dir を追加。T8360–8394：反例を実 Git で構成し、属性消失後の cold・rc=1・merge finding・oracle 一致を検査。 |
| B-B1：probe の再導出 | **closed** | P68–85：実装の `_attribute_fingerprint`／`_attribute_candidates` を直接呼ぶ。新形の判定は digest 比較だけ。候補集合差は集計専用（P86–87）。 |
| B-B2：exact 変異と帰属 | **closed（静的）** | [spec v2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/mutation-spec-probe-v2.json:6) の全5置換について、現実装で `old` が各1件、置換後の構文が有効と確認。最初の赤理由は下表。実際の kill は未確認。 |
| B-B3：破損形の独立帰属 | **closed** | fix1 patch L125–174：候補 field 用 helper、T-neg-4／T-neg-5 を削除。対応する保存・復号・包含検査も撤去され、この帰属問題は消滅。 |
| B-B4：E-1 の入力証明・未測定範囲 | **partial** | R11 に旧 blob の出所と hash 記録への参照、P96–102 に測定範囲・入力 hash・環境記録あり。ただし参照先の一致証拠と修正後 E-1 結果は今回の提示資料では未確認。他 binding・partition・受領証探索の非測定も明示列挙されていない。 |
| 撤去漏れ・caller 回帰 | **closed** | C2237、2413–2414、2471–2475、2508–2518、2603、2686以降：schema=1、2値返却と両 caller が整合。対象2ファイルに base64／zlib、保存候補 field、fingerprint の `[0]` 残骸なし。 |
| 既存テスト・argv pin 回帰 | **closed** | base `f94b61fc8` と AST 比較し、既存 `test_*` 272関数の変更・削除0件、新規6件。C2302–2304 の接頭辞は T8985 の `diff-tree --stdin`、T9011 の `log --no-walk=unsorted` と重ならない。 |
| git 失敗時の fail-closed・policy 重複 | **closed** | C2281–2287、2599–2604、2624–2626、2686：候補列挙失敗は RuntimeError → 全史監査、受領証状態なし。publish 側も C2493 で保存を中止。C2400／2411 が policy を共有し、候補列挙で再取得しない。 |
| 費用値の限定・計算回数 | **partial** | R34–35 はホスト・load・実測対象を限定。ただし「1走に1回」は現実装と不一致。下記 nit 参照。 |

**A-M1 の論証と反例再現**

監査集合は C1857–1867 の `{policy} ∪ policy..head`。候補列挙も同じ範囲の merge に加え、`--no-walk policy` で policy 自身が merge の場合を含みます。`--first-parent` で履歴を限定していないため、側枝の merge も対象です。

監査側は全親差分の交わりを候補にしてから `--cc` を呼ぶため（C1773–1791）、第1親差分は上位集合です。fix2／fix3 の `git log` は commit 見出しを空にし、NUL 区切りの bytes をそのまま祖先 dir へ展開します。hex 名の除外はなく、merge 0件では log を呼びません。同一 policy・祖先関係のある tip 間では、この履歴由来集合が減りません。

T-neg-6 は A で nested 属性による上書きと成功受領証を作り、B では README **だけ**を stage します。commit 前後の未追跡 assertion（T8380／8382）により、index の属性束縛が反例を肩代わりしません。nested 削除後は digest 差、finding、全史1回を確認し、T8256–8261 の helper で受領証を削除した oracle の rc・stdout・stderr と比較します。

指定された経路から追加の反例は構成できませんでした。非 merge の name-only と trailer parse はこの属性による patch 選別を行わず、pickaxe の結果は epoch／CAB の束縛に入ります。worktree 不在時の index 属性も C2356–2374 で path と metadata を束縛しています。

**変異の帰属**

| 変異 | 最初の赤理由（静的予測） |
|---|---|
| M-1 | 既存 `test_additional_attribute_sources_fall_back[untracked]`：実在属性を落とし、違反を検出すべき監査が warm になる。 |
| M-2 | T8271：absent 候補追加で digest 同一 assertion が失敗。warm 観測より前。 |
| M-3 | T8352：lstat unreadable を落とし、digest 不一致 assertion が失敗。 |
| M-4 | T8306 の digest 不一致、および T8370 の履歴候補包含 assertion が失敗。どちらも履歴由来候補の欠落が理由。 |
| EQ-1 | `attribute_paths` は元から set。`sorted(set(attribute_paths))` は同じ bytes を同順で返すため等価。 |

spec は probe 用として全件 `expected_status: SURVIVED`、`expected_nodes: []` です。これは kill 対応表の機械的な受入登録ではありません。今回確認できたのは exact 置換と静的帰属までで、plan-only rc=0 を kill の証拠には数えません。

**新規所見**

- **must-fix：なし。**
- **should：なし。**
- **nit N1 — 費用記述の更新。**
  (i) R34–35 は旧 `diff-tree` 方式の実測と「1走に1回」を記載していますが、現実装は lookup と publish の双方で候補列挙します（C2471、2603）。R51–52 と fix1 報告末尾は再計算維持を認めています。
  (ii) 判定・受理集合・再利用可否は変わりませんが、最終実装の費用を過小評価する記録になります。
  (iii) 「旧方式・当該 login 環境での参考実測。現方式は発行時に再列挙し、最終費用は未測定」と訂正してください。提示値を最終方式や一般的性能へ外挿しないことが必要です。

親ログの **2718 passed／5 skipped**（focus-6 L45）と **555 passed**（focus-8 L24）は確認しました。いずれも焦点走の証拠であり、変異 kill・E-1・受入全走の証拠には拡張しません。

## 総括

**GO — must-fix 0件。**

A-M1、B-B1、B-B2 の修正は静的検査で成立し、fix2／fix3 による新規回帰は見つかりません。B-B4 の記録確認、費用記述の訂正、変異実走と修正後 E-1 の評価は残っています。