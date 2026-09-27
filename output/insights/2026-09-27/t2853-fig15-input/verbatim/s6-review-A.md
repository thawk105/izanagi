## 所見

- **M1** — [図 README:2038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/docs/paper-story/figures/README.md:2038)、[同:2063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/docs/paper-story/figures/README.md:2063): 現在の検査を「repo 外 5 file」「外部原本からの再導出」と記すが、変更後の2テストは追跡下の写しを読む。放置すると成果物の proof chain が実際と異なる入力先を参照する。該当句を「原保存先の論理 path を記録した、追跡下の逐語写しからの再導出」に直す。
- **S1** — [段1 brief:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig15-input/verbatim/s1-brief.md:22): 「受理集合は広がらない」は入力の配置まで含めると誤り。平坦 layout と混在 layout が新たに受理される。受理される**内容**は5件の SHA-256 pin で不変、と限定する。段2・3省略の根拠もこの限定に合わせる。
- **S2** — [新テスト:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:397): `PLOT.main(..., expected_hashes=pins)` は引数解析と既定入力を通すが、公開 CLI のプロセス実行ではない。「CLI 実行」とする報告は正確に直す。実データでの公開 CLI 実走は別の報告・描き直し log にある。
- **N1** — [図 README:2028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/docs/paper-story/figures/README.md:2028): 「2026-09-27 まで」は日付全体を指すように読める。「この変更前は」に短縮できる。

## 削らない判断

- 論理名と平坦名の固定対応、階層優先 fallback、新テスト1本は段4裁定どおりで、本題の既定入力を成立させる。追加の gate は見当たらない。
- M1〜M3 の指定変異は静的には期待どおり赤になる。M1 は W1 の pin 不一致、M2 は既定 root の逸脱、M3 は平坦 file 不在で失敗する。変異の実走結果としては数えない。
- 5件の写しの SHA-256 は pin と一致した。比較結果の9 leaf 差は時刻、生成器 SHA、出力 path、PDF SHA、再現 argv に限られ、統計などの値の leaf 差はない。PNG bytes も一致する。PDF bytes の差は変更前生成器の対照描き直しにもある。log の「`--evidence-root` なし」、記録された既定 root、実装を合わせると、今回の描き直しが写しを読んだという結論を支持する。

## 判定

**NO-GO** — 実装と値比較に阻害所見はないが、図 README の入力参照の誤記を直してから完了とする。

## 総括

静的レビューのみ実施し、テスト・変異は実走していない。
既定入力、pin、`summary.json.inputs`、provenance の論理名と統計計算は裁定に整合する。