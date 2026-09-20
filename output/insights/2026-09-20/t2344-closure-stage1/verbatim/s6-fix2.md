## 変更

変更は [test_b10_backoff_static_tail_formal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2344-fix2/orchestrator/tests/test_b10_backoff_static_tail_formal.py:405) のみです。

- test 1（405行）: `_explore()` の呼出しを残し、`match="exact key 集合が不正"` に更新。
- test 2（412行）: `config_for` → `replace` で `run_kind="t2418-explore"` → `bind_admission_policy` → `_write_certified_lock` で現行 lock を生成。`match="not formal"` を維持。

## 検証

**pytest実走ではなく、module import 後の直接呼出しです。**

- test 1 / 2: 両方成功。合成 lock の85 keyを確認。
- 反実仮想(a): 最初の run_kind 検査だけをメモリ上で除去すると、後続の `ArtifactAdmissionError: campaign requires a directory, campaign.lock, and WAL` で赤。
- 反実仮想(b): test 1 の regex を旧 `"not formal"` に戻すと、regex不一致で赤。
- `git diff --check`: 成功。実 exploration lock の変更なし。

## 観測した拒否 message

`CampaignLockCodecError: authority.contract_loader_blob_sha256s の exact key 集合が不正`

## 裁定との差異

ありません。production・他テスト・docs は未変更。commit・branch操作もしていません。

## 総括

指定の修正と直接呼出し・反実仮想検証は完了しました。
残る検証は、親によるpytest受入全走です。