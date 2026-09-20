# 受入全走 attempt 1 の赤 1 件と親の裁定 (2026-09-20 23:48 JST)

- tip: `43c32588b` (main `6305f2d05` を取り込んだ merge)、session root `/work/1/SFC/tanab/.izanagi-acceptance-shards/e637a58cef6d6d14ad92ae0037714885`、shard-1。
- node: `orchestrator/tests/test_b10_backoff_static_tail_formal.py::test_formal_loader_rejects_real_exploration` (0.504 s)。
- 本文 (junit 逐語):

```
AssertionError: Regex pattern did not match.
  Expected regex: 'not formal'
  Actual message: 'authority.contract_loader_blob_sha256s の exact key 集合が不正'

    def test_formal_loader_rejects_real_exploration(spec):
        binding = formal.load_preregistration(ROOT,"HEAD")
>       with pytest.raises(ValueError,match="not formal"):
            formal.load_formal_campaign(spec,binding,_explore(),correctness_mode="legacy")
orchestrator/tests/test_b10_backoff_static_tail_formal.py:406
```

## 親の裁定 (DW-O18)

- **帰属: 本 wave (自分起因)。** `_explore()` は実在の exploration campaign
  `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8/`
  (記録 grammar exact-63、`exact63-locks-verify.json` の 20 本のうちの 1 本) を certified 経路 `load_formal_campaign` に渡す。収載 tuple が 85 になったので
  通常 decoder が decode 段で exact key 集合不正として拒否し、run_kind の「not formal」検査に到達しない。裁定 §6 が開示した受理集合の変化そのもので、
  production は設計どおり (D1653: certified は現行 grammar のみ)。test の期待 message が古い。
- **対応:** test の主張を 2 つに分けて残す — (1) 実 exploration (exact-63) は decode 段で拒否される (message = exact key 集合不正)、
  (2) 「not formal」の拒否は現行 grammar の合成 campaign (run_kind を formal 以外にした certified lock) で検査し続ける。regex の緩和・skip はしない。
  Codex fix 子 (`s6-fix2`) が test file だけを変える。
- 他の赤: なし (total=1)。F945 型 (setup timeout) ではないので受入 script は停止した。fix 後に同じ tip 系列へ受入を再投入する。
- 静的検査で見落とした理由: 段 6 レビュー A/B は `orchestrator/tests/test_b10_backoff_static_tail_formal.py` を必読に含めておらず、焦点走の file 集合
  (symbol consumer 15 + inventory 4) にも入っていなかった (この test は `campaign_lock` / `artifact_admission` の symbol を直接参照せず、
  `b10_backoff_static_tail_formal` 経由で実 campaign を読む)。実 lock probe (§5) の C は代表 4 本で、この campaign は A (歴史 decode) だけを測っていた。
