---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2339-b5-prereg
seq: 3
---

## 再発

### F344

- **再発: 2026-09-07** — 今回は `land rc=0` の後ではなく、land が
  `status=rejected` / `release_safe=false` を返して**意図的に lease を保持した**経路で起きた
  (`lease_release state=retained reason=land-result-not-release-safe`)。
  修正後の受入再投入が `stage=claim-self-unverified rc=70` で 1 回空振りした。
  F344 の恒久対応は「`land rc=0` の直後に release する」であり、**land が成功しなかった経路を
  覆っていない。** land が `landed` / `already-landed` 以外を返して lease を保持したまま
  受入を取り直すときは、投入前に
  `python3 tools/wave_land_window.py status --lease-dir <dir> --wave <slug> --json` を 1 回実行し、
  `state=held` かつ `main_sha` が現行 main と異なれば
  `python3 tools/wave_land_window.py release --lease-dir <dir> --wave <slug>` で解放してから
  投入する。同じ検知手順が F344 の再発検知節に既にある。
