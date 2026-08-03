# fold 機構 3 件 (T-357 / T-352 / T-358) — 逐語と変異台帳

branch `worktree-dev-wave-fold-rotation-copy` の dev-wave が生成した資料の凍結。
可変状態の正本は worklog 末尾であり、本書は逐語と一次実測の保管である。

## 何をしたか

ユーザー裁定済みの 3 件を、同じ畳み込み機構 (fold) を触るため 1 wave に統合して実装した。

- **T-357** — fold の形検査から git の rename/copy 検出を外す (択 (a))
- **T-352** — `完了` の終端性を語の不在でなく構造 field の必須化で判定する (択 (a))
- **T-358** — 見送り台帳の既存項目へ発火記録を追記する経路を新設する (択 (a))

## 一次実測 (`measurements.md` が全文)

- `-M -C` 付きの `diff-tree` は worklog→archive の移動を `C084` と報告し、`--no-renames` では `A` になる。
  移動割合 50% では `C` が出ない = **類似度閾値依存**であり、現行の拒否は偶然の副産物だった。
- repo-local の `diff.renames` は plumbing の `diff-tree` に効かない (git 2.34.1 実測)。
  porcelain の `git diff` には効く。よって明示 `--no-renames` は config 対策ではなく意図表明である。
- ローテーション閾値は行数でなく **bytes** (`WORKLOG_ROTATE_BYTES = 100_000`)。
- 実 candidate の dry-run: ruling fragment 5 件で
  `rotation_path = docs/archive/worklog-phase3-0802-117-120.md`、`projected_worklog_bytes = 94193`、
  採番 `T:fold-rotation-copy-detection → [T-357]`、`T:fold-deferred-firing-record → [T-358]`。
- **M01 の帰属を実測で確定**: `--no-renames` を `-M -C` へ戻すと、事前登録した 3 node が
  ちょうど赤くなり、land 統合テストは本番と同じ失敗形
  (`fold failed: declared fold shape rejected: path-status`) を再現した。

## 敵対検証が実際に見つけた欠陥 (逐語は各ファイル)

段 3 (`review-a.md` / `review-b.md` / `review2.md`) と段 6 (`final-a.md` / `final-b.md` /
`final2-c.md` / `final2-d.md`) が出した所見のうち、親が real と裁定して直したもの。

1. **land を阻む blocker** (`final2-d.md` 所見 1): ローテーション後でも 6 fragment で 104,462 bytes と
   なり `rotation-capacity` で **plan 段階から失敗**する。`_rotate_worklog` が元 worklog の最新 entry を
   必ず残す設計だったため。分割点を projected worklog に対して選ぶよう直した (fix F1)。
2. **fence 内 decoy** (`final2-c.md` 所見 1): `- ` list container 幅を除いた raw 4-space fence opener を
   見落とし、fence 内の `remaining: none` を field と数えていた。item 相対の fence view を導入 (fix F2)。
3. **replay guard の過剰拒否** (`final2-c.md` 所見 2): 対象 block 全体の raw 部分文字列一致で
   replay 判定していたため、継続行の例示と同じ byte 列があるだけで正当な初回追記が拒否された。
   先頭行の末尾一致に絞った (fix F3)。
4. **Markdown 破壊** (`review2.md` 所見 3): 追記を block 末尾へ連結すると、対象 item の最終行が
   fenced code の閉じ行のとき fence を壊す。先頭行の行末へ入れる設計に変更した。
5. **偽 kill 2 件** (`final-a.md` 所見 1・2): `T` 変異が受理集合を変えず診断文字列だけで赤くなる、
   P01 が未登録の負例まで赤くする。fixture と変異を再照準した。
6. **禁止 flag の抜け** (`final-a.md` 所見 4): 結合短縮形 `-zM` / `-zC` / `-zB` を見逃していた。
7. **fragment 処理順** (`plan2.md` / `review2.md` 所見 8): `Fragment.key` は wave slug の辞書順なので、
   本 wave の記録 fragment は ruling 5 件より後に処理される必要がある。
   wave slug に実 branch 名そのものを使う裁定にした。
8. **親 brief の誤り 2 件**: 閾値を「行数」と書いた (実際は bytes)、不変条件 I3 を
   「他 caller の挙動を変えない」と書いた (valid rotation の受理は意図して変わる)。

## 変異台帳

- 事前登録: `mutation-spec.json` (T-357 分 10 件)、`mutation-spec-2.json` (T-352/T-358 分 14 件)、
  除外候補と理由は `mutation-prereg-2.md`。
- **erratum**: T-357 分の事前登録は段 6 レビューの指摘で本走前に 2 点是正した。
  P01 を `archive_adds > 1 → > 0` へ再照準 (元案は two-archive 負例まで巻き込み MISMATCH になる)、
  M01 の期待 node に land 統合テストを追加 (実測で 3 node ちょうどと確認)。
- **erratum**: 本走を分割して走らせた初回は、途中で親が untracked ファイルを作ったため
  harness が停止し、その後の commit で HEAD 束縛が切れて resume できなくなった。
  結果は破棄し、最終 commit 後に 1 回で走らせ直した。中断時点の記録は 6/10 KILLED・
  期待一致 6/6 だった。

## 資料の対応

| ファイル | 内容 |
|---|---|
| `brief.md` / `brief2.md` | 親 brief (T-357 / T-352・T-358) |
| `measurements.md` | 親の一次実測 |
| `plan.md` / `plan2.md` | 段 2 codex プラン |
| `review-a.md` / `review-b.md` / `review2.md` | 段 3 敵対相談 |
| `spec2.md` / `fix2-spec.md` | 親が段 4 / 段 6 で確定した仕様 |
| `impl.md` / `implA.md` / `implB.md` | 段 5 実装子の報告 |
| `final-a.md` / `final-b.md` / `final2-c.md` / `final2-d.md` | 段 6 敵対レビュー |
| `fix1.md` / `fix2a.md` / `fix2b.md` | 段 6 fix の報告 |
