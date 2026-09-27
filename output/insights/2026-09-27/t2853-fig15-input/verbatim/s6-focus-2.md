## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| 初回 M1 | **closed** | 図 README の検査説明と proof chain は、追跡下の逐語写しからの再導出を明記している。 |
| F-M1 | **closed** | [作図ツール README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/tools/plotting/README.md:520) は `validate_external_sources` の入力を「5 file（既定は追跡下の逐語写し）」に修正済み。 |
| F-S1 | **closed** | [insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/output/insights/2026-09-27/t2853-fig15-input/README.md:53) は観測入力5件の写しと、`caption_source` として読む追跡下の稿を区別している。 |
| F-S2 | **closed** | [insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/output/insights/2026-09-27/t2853-fig15-input/README.md:51) は差を leaf の *path 集合* に限定し、値の違いも明記している。 |

## 新規所見

なし。

## 判定

**GO** — 修正文言は生成器の既定入力と2テストの参照先に一致し、指定された README 範囲に検査入力を「外部原本」「repo 外」とする誤記は残っていない。

## 総括

静的検査のみ実施。テストは実走していない。`FOCUS2_RESULT` は指定どおり placeholder として扱った。