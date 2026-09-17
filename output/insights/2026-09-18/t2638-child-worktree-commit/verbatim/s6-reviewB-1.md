## 削除候補 (番号、対象、根拠、失うもの)

1. **必須の削除候補なし。** helper の引数・状態・出力、`GIT_COMMANDS` の追加5操作、120秒 timeout、待ち手の opt-in と死亡確定後の呼出しは裁定 §2 に一致する。削ると残差保存・対象外判定・失敗伝達のいずれかが失われる。残して増えるのは裁定済みの終端処理であり、保存 framework への一般化は認めない。

2. **nit：provenance テストの欠落ケース。** `test_commit_worker_worktree_provenance_values` の `None` と `records_residue_then_noop` はともに unknown を検証する。ただし前者は「指定した receipt が不存在」、後者は「receipt 指定なし」で入口が異なる。削ると前者の確認を失い、残すと実 commit が1回増える。成果物影響を示せないため、削除必須とはしない。

固定件名・本文・trailer は裁定どおり。件名の「残差を記録」と `scope: worktree residue at job end` は採用を宣言していない。本文に裁定外の行はなく、stdout も保存状態だけを報告する。説明文をさらに commit ごとに追加する必要はない。

cleanup・祖先保持・submodule 再帰・排他の変更は差分にない。操作 marker の列挙は裁定された単一の `operation-in-progress` 判定であり、rebase 個別処理の再導入ではない。

## 不足 (本体に足りないもの)

**実装差分に、裁定 §2 の本体欠落は見つからない。**

- 残差は `add -A` 後に commit。clean は commit しない。
- read-only・非 author/fix・dry-run の不発火を維持。
- launcher 非0を保持し、成功＋保存拒否／失敗だけ rc=3。
- provenance は recorded → requested → unknown、`none` は unknown。
- 待ち手は絶対 path の opt-in。死亡確定後に1回呼び、既存成功＋保存拒否／失敗を `producer-commit` にする。done の内容再解釈は追加していない。

不足は **docs の対象指定契約と記録の位置付け**。詳細は docs 所見に記す。新しい検査や gate で補う必要はない。

## テスト所見 (赤 1 件の最小是正案を含む)

**赤1件は局所修正が必要。** `test_producer_commit_worktree_after_death` の `captured.err == ""` は、ログに現れた既存の pid-only 縮退診断まで拒む。放置すると、保存成功を失敗と報告し、焦点走が赤のままになる。

その1行を次に置き換える案が最小。任意の stderr を許さず、当該 PID の既存診断だけを許す。

```python
assert "NG:" not in captured.err
assert "producer-commit" not in captured.err
assert captured.err in (
    "",
    f"producer: /proc/{producer.pid}/stat を読めないため pid-only へ縮退します\n",
)
```

`RC_OK`、stdout の完全一致、commit 数、`HEAD:residue`、trailer、receipt 成功の検証は維持する。削るのは「正常系で stderr は常に空」という誤った条件だけであり、残す検証は保存失敗と未知の診断を引き続き拒む。

その他の評価：

- **正例は実体を名指ししている。** helper は実 Git、待ち手は実 process と実 Git。起動器は fake launcher を使うが、レビュー対象の終端保存・rc 合成は実 subprocess と実 Git を通る。保存 helper の stub で正例を代替していない。
- **失敗テスト3層は冗長ではない。** helper は staged 残差保持、起動器は rc 合成、待ち手は receipt 公開抑止を検証する。削ると別々の成果物契約を失う。
- **待ち手の失敗テスト追加は妥当。** §2.5 の一覧にはないが、§2.3 の保存失敗時契約を直接検証する。残す負担は実 Git の2ケースで、仮想リスク向け追加ではない。
- **nit：`--check-only` と opt-in の併用を追加テストは直接固定していない。** 差分は通常待機への配線のみで、書込み混入は確認できない。補うなら既存 check-only テストへの局所的な確認で足りる。現状の成果物欠陥を示せないため必須追加とはしない。

提示ログは **461 passed / 1 failed**。赤の assertion より後にある commit 内容・receipt の検証は、その走行では到達していない。修正案が通ったとは扱わない。

## docs 所見

**要修正：DW-S05-A:25 は裁定された説明を省きすぎている。**

現文には次がない。

- 保存範囲が投入先 worktree **全体**であること。
- 待ち手には呼出し側が対象を正しく指定すること。
- 終端 commit は記録であり、採用・land・撤去とは別であること。

放置時の成果物影響は、所有 path 限定保存との誤認、対象外 worktree の指定による commit、および保存 commit の採用状態の誤認。待ち手は receipt を読まないという裁定なので、指定責任の説明は実装の代わりを担う。

局所的な置換案：

> 起動器は workspace-write の author/fix の投入先全残差を終端 commit。待ち手は呼出側が同対象を `--commit-worktree <abs>` で指定する。記録のみで採用・land・撤去とは別（D2044 項16）。

削ると対象・保存範囲・採用境界が失われ、残すと必要な説明 bytes が増える。予算内への相殺は必要だが、検査機構の追加は不要。

ほかの縮約について：

- `<base>` は明示的比較元となり、「子作成 SHA」も残る。**nit として「子作成時の固定 SHA」へ明確化**すると裁定 A6 により忠実。現表現から具体的な誤抽出までは示せない。
- `--commit-worktree` と D2044 項16の名指しは残っている。ただし現文は引数と指定責任の説明が不足。
- A の別 worktree・所有 path 限定・依存順・startup 非0停止・NOTE 再読は保持。
- B/C の xfail 禁止、期待値を甘くしない義務、実走証拠、未実走申告、meta-test、波及列挙、期待赤の事前指定も保持。縮約による安全義務の脱落は認めない。

## 総括

実装は裁定 §2 に沿い、過剰な保存機構や scope 外変更は見当たらない。修正対象は **待ち手正例の stderr assertion** と **DW-S05-A の対象・保存範囲・採用境界の説明不足**。残りは nit。

指定資料の静的レビューのみを実施。ファイル変更・pytest 実行は行っていない。