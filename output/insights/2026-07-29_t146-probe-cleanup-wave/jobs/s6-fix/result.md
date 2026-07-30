指定 fix を [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1093) のみに実装しました。commit は作成していません。

### Review blocker

| Blocker | 状態 | 対応 |
|---|---|---|
| bind失敗＋pathname不在時の `getsockname()` | closed | dirfd＋nofollow で `.s` を先行観測。不在なら非呼出しで `False`。fixture は呼出時EPERM＋`assert_not_called()` |
| fault matrix不足／M-T146-B等価化 | closed | FNF absent×pending True/False、FNF present、EPERM/EIO after-real-unlink、success present、partial-bindを7 nodeで固定 |
| `-rf -rs` によるFAILED記録欠落 | closed（author範囲） | targeted/full commandをすべて `-rfs` で実走。親のmutation本走でも同指定が必要 |
| recording分類 nit | unchanged／regressionなし | 親記録で「旧穴3・regression guard・identity再固定」を分離する項目 |
| close複合fault・hostile writer・production partial-bind | scope外維持 | 実装・testとも拡張なし |

result/error/pathname/identity は recovery前に観測し、finalizerはpatch外側から保存済みreal `unlink` / `close`を使用します。

### 検証結果

- fault policy全7 node: **7 passed / 0 skipped / 0 failed**
- preexisting全2 node: **2 passed / 0 skipped / 0 failed**
- 既存T-138正負gate: **1 passed / 0 skipped / 0 failed**
- long-path node: **0 passed / 1 skipped / 0 failed**
  - exact reason: `sandbox does not permit AF_UNIX bind through /proc/self/fd`
- targeted合計: **10 passed / 1 skipped / 0 failed**
- isolation exactness: **1 passed / 0 skipped / 0 failed**
- integration file全体: **88 passed / 1 skipped / 0 failed**
- isolation file全体: **3 passed / 0 skipped / 0 failed**
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: rc=0

想定外の赤、新規nodeのSKIP、xfail/期待値弱体化はありません。これらはauthor workspaceでの実走結果であり、親のmutation matrix・受入再走を代替しません。

### 波及監査

- 所有外caller: production callerなし。唯一の実consumerは同integration fileのlong-path roundtrip node。
- shared fixture: 共有pytest fixtureの変更なし。局所的な `socket.socket` / `os.unlink` patch、socket double、`dev-waves-runtime` markerのみ。
- consumerへの波及: long-path nodeは制限sandboxで既存exact-reason SKIPへ戻り、許可環境では従来どおり実roundtripを検査。isolation marker exactnessは維持。
- production、isolation meta-test、docs、output、submodule、indexは編集していません。

最終 `git status --short`:

```text
 M orchestrator/tests/test_dev_waves_integration.py
?? output/insights/2026-07-29_t146-probe-cleanup-wave/
```

未追跡wave出力群は既存の所有外状態で、不変更です。

## 総括

段6の必須fixはauthor範囲で **closed、partial 0、regressed 0**。指定1ファイルだけを変更し、全必須検査はfailed 0で完了しました。