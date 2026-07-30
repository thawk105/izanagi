# T-173 段 6 focused re-review 裁定 — fix round 2

## accepted

- finding 4 partial: normalized H2 substringはblockquote、indented code、H3、追加但書、fence-info edgeを
  構造として区別できない。対象H2の許可top-level block列だけをexact照合する狭いparserへ直す。
- finding 8 partial: negative IDsのproduction/test一致だけでなく、各IDが `_COMMAND_GUARD_CASES` に
  exactly once含まれ、needle mapにも存在することを独立meta-testで固定する。
- finding 9 partial: mutation exact node / subset / erratumは実装fixではなく親の本走前記録で閉じる。
- duplicate H2 / duplicate block、legal rewrap、blockquote、indented code、H3、追加但書、comment、
  backtick/tilde fenceとinfo-string edgeを恒久controlにする。

## refuted / scope外

- accepted 1〜3、5〜7はclosed。Skill / metadataを再変更しない。
- checker責務文言のnitは、exact textが意味証明そのものではないため現行説明と両立し、今回のdocs fixにしない。
- generic Markdown parserへ拡張しない。cleanup Skill / commandの指定H2だけを検査する。
- cached 4-file確認はcommit前の親責務のまま。

## 成果物影響

未修正では安全句をblockquote/codeへ退避し危険なlive blockを置いてもchecker greenとなり、
main/primary/foreign worktreeや共有Git metadataを失わせ得る。registry spread脱落では16負例が実行されず、
検出力を過大記録する。

fix roundは2/3。相互依存するchecker/parserとtestsを単一Codex unitへ戻す。
fix前snapshotは `s6-round2-pre-fix.patch`。
