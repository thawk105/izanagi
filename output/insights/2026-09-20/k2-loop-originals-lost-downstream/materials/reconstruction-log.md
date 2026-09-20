# 実測記録 — 残存資料の sha256 照合と、派生物からの再構成 (2026-09-20 20:5x〜21:0x JST、login node)

読み取り専用の検査 (§9 の複製だけ repo 外 → repo 外の書込み)。使い捨て script (`sha_capture.py` / `reconstruct_loop_state.py` / `compare_ao2.py` / `reconstruct_ao.py` /
`wal_keyorder.py` / `wal_canon_r2.py` / `scan_roundtrip.py` / `copy_pair_originals.py`) は job dir (repo 外 `/home/SFC/tanab/.claude/jobs/cc931155/tmp/`) に置き、
repo へは入れない (probe は Codex author 無しで repo に入れない)。
**本文は抜粋・要約である** (sha256 を先頭 8 桁に省略した箇所、日本語の注釈、`$` 行の command 表記を加えた)。**生 stdout の逐語は同 dir の `reconstruction-stdout.txt`**
(tee で採った `.log` をそのまま連結。§1・§2 の `sha256sum` / `wc` / `ls` の初回実行は tee していないので、同じ file を `sha_capture.py` で 21:24 JST に採り直した出力を逐語とする)。
期待値の出所は 3 巡稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` §5.1 (消失前の同日に再計算された原本の sha256 と bytes)。

## 1. t2746 job dir `scratch-campaign/` (2026-09-18 08:00 JST の dogfood 用写し) の 6 file

```
$ sha256sum campaign.lock knowledge_manifest_receipt.json loop_state.json s4_loop_digest.txt runs/agent_outputs.jsonl runs/wal.jsonl
fc7acacabd871a180c2f1f4b86d0b2bb90ce5f682476b3a230862c495ed401de  campaign.lock
c42dc712bbd11fc7e7a29921f7e760fa5a4e8c315a5ea62266c32f5ea97d4d2a  knowledge_manifest_receipt.json
03ebaf94339c89849e969cb7547f31f6c241a81698f5195c090bc8351db716a7  loop_state.json
a0a4c204f9d214bb52f87d1cdc0dcf9d19a307e36d6db0d9d3c5f13b517e6c9c  s4_loop_digest.txt
1866ebc89cb82ddefec2913282db4b6235273fde4ceb441dc7ec140de7d5f19d  runs/agent_outputs.jsonl
03ac8508ba9a3d28b89f9a7b39046c76a49375e381a6c3b135949171c4f16d26  runs/wal.jsonl
$ wc -c (同順)
 8307 / 1317 / 255 / 1938 / 34020 / 7057
$ wc -l runs/agent_outputs.jsonl runs/wal.jsonl
 4 / 5
mtime: 全 file 2026-09-18 08:00:05〜08:00:14 +0900
```

3 巡稿 §5.1 の round 2 との照合: `campaign.lock` `fc7acaca…` (8,307 B) **一致**、受領証 `c42dc712…` 一致、`loop_state.json` `03ebaf94…` 一致、
`s4_loop_digest.txt` `a0a4c204…` 一致、WAL `03ac8508…` (7,057 B) 一致。AO は `1866ebc8…` (34,020 B) ≠ 本走 `804c62c7…` (34,017 B) — 別走の写し。

## 2. T-2795 pair 走 (`dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/`)

```
$ sha256sum runs/wal.jsonl campaign.lock loop_state.json s4_loop_digest.txt knowledge_manifest_receipt.json
b5754f98c0643e80fc02f8bcc02f080ba43ee7d72464ef8fa6ad1410a3b2c56a  runs/wal.jsonl        (7,062 B)
962ef7d787b7031a99e6c57088746f1a00646ac5e69c979110cc131bcb39ff03  campaign.lock          (8,307 B)
a8c6a8b69bc7bdd5eaee3203025968b4e198e082e5cca6b40244d75fa7a49ae0  loop_state.json        (255 B)
8bde66fa21413dda8f269a1b7736164e354a371db465387a52e23bd4fe9ece8e  s4_loop_digest.txt     (1,939 B)
c42dc712bbd11fc7e7a29921f7e760fa5a4e8c315a5ea62266c32f5ea97d4d2a  knowledge_manifest_receipt.json (1,317 B)
mtime: 2026-09-20 19:13:03〜19:13:40 +0900
```

`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §1 の表 (WAL `b5754f98…` 7,062 B、lock `962ef7d7…`、loop_state `a8c6a8b6…`、digest `8bde66fa…`、
受領証 `c42dc712…`) と 5/5 一致。`git worktree list` (20:56 JST) で `submit-tree-pair` は **locked 印なし**。cleanup 候補 list (`/work/1/SFC/tanab/cleanup-20260920/candidates-{1,2,3}*.txt`、
16:26 JST 時点の棚卸し) には入っていない (pair 走 19:13 は棚卸しより後)。

## 3. round 3 `loop_state.json` を `materials/run-summary.json` の `loop_state` から再構成 (`reconstruct_loop_state.py`)

writer = `orchestrator/campaign/p3_s4_loop.py` `save_loop_state` (`json.dump(state_to_dict(state), f, ensure_ascii=False, indent=2)`、key 順 =
`iteration, start_wall, reverse_recommendations, whiteboard[{iteration, direction, magnitude, result, delta_pct}]`、末尾改行なし)。

```
round2 scratch bytes 255 reserialized 255 byte-identical: True
round3 reconstructed bytes 255 sha256 917ba3d3b34df45eff85aa536999dd30b895256fdefaef68214431ae88a1f950
round3 expected            255 sha256 917ba3d3b34df45eff85aa536999dd30b895256fdefaef68214431ae88a1f950
round3 match: True
rc=0
```

round 2 の scratch (原本と sha 一致) を同じ手順で round-trip して byte 一致 (手順の正例)。round 3 は記録 sha256 と **一致**。

## 4. round 2 / 3 の本走 `runs/agent_outputs.jsonl` を `layer3_report.json` の `agent_outputs` から再構成 (`reconstruct_ao.py`)

行形式は round 2 scratch AO で総当たり検算: `json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"` (sort_keys は True / False どちらでも同 bytes =
AO の event は writer 側で canonical 順に書かれている)、event の並びは `ts` 昇順。

```
scratch AO: bytes 34020 lines 4 trailing newline: True
  sort_keys=True ensure_ascii=False separators=(',', ':'): round-trip OK (34020 B)
round2: rebuilt 34017 B sha 804c62c713e6785a1560725cb35690ffa044208ae94249d21deffdb41fa0a17b | expected 34017 B sha 804c62c7… | match=True
round3: rebuilt 32979 B sha 66d3e737c1e4bb2e651805d97d40e047093f85273642464d24b23b797813efce | expected 32979 B sha 66d3e737… | match=True
```

補足 (`compare_ao2.py`): round 2 scratch AO の 4 event と `layer3_report.json` の 4 event は `ts` を除く全 field (payload の `input_sha256` / `output` / `provenance` / `refs`)
が一致 (ts を除いた canonical sha `fc6c41ad…` 同一)。scratch の ts は 08:00 JST (dogfood)、本走の ts は 08:25 JST。

## 5. round 2 / 3 の WAL を `layer3_report.json` の `variants[].events` から再構成 (`wal_keyorder.py`、`wal_canon_r2.py`)

```
scratch WAL record keys: ['variant', 'stage', 'env_tag', 'ts', 'payload']   (dataclass WalRecord の順)
payload sorted: False (5 record とも。挿入順で書かれている)
round2 rebuild (top-level を dataclass 順、payload を sorted): sha f51b7b21… match False
round3 rebuild (同):                                              bytes 7057 sha 2e97f644… match False (期待 eb8927b7…)
round3 canonical refs from layer3 events == materials/wal-refs.json: True 5 5
round2 scratch WAL canonical refs == layer3 events: True 5 5
round2 layer3 events canonical refs == materials/wal-refs.json: True 5
```

canonical ref = `"wal:" + sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")))` (`orchestrator/campaign/agent_outputs.py`
`canonical_bytes` / `p3_s4_loop.py` の `known_refs`)。**内容は 5/5 同一、bytes は payload の挿入順が sorted 写しから復元できず不一致** (bytes 数は同じ 7,057)。

## 6. digest (`s4_loop_digest.txt`)

round 3 の `f993251d…` / round 2 の `a0a4c204…` と sha 一致する file、および round 2 digest 先頭 200 B を含む file は、repo の insight dir 3 つ
(`2026-09-19/k2-loop-round3`、`2026-09-18/t2746-k2-loop-round2`、`2026-09-20/t2795-k2-pair-attempt`) の全 file 走査で **0 件**。round 2 は scratch 写しが原本と一致。
round 3 の digest は WAL 内容 + verifier epoch (`layer3_report.json` の `campaign_verifier_epoch` = `E1:7198f909…`) からの決定論的描画なので固定 checkout
(`a99425b66`) で再描画できる可能性があるが、**本 wave では実測していない**。

## 7. repo 側派生物の sha256 (本 wave 実測、記録値と一致)

```
c37fda1f…  output/insights/2026-09-19/k2-loop-round3/layer3_report.json
f6dca3b9…  output/insights/2026-09-18/t2746-k2-loop-round2/layer3_report.json
5cd8f518…  output/insights/2026-09-19/k2-loop-round3/verbatim/critic-3.md
bd3e5fd2…  output/insights/2026-09-19/k2-loop-round3/materials/proposal-4.json
05f2b267…  output/insights/2026-09-19/k2-loop-round3/materials/knowledge-input.json
7b742268…  output/insights/2026-09-19/k2-loop-round3/materials/diagnosis-4.json
245ebeb314b44c95a6c0d68dcb915820508de099b3005ac9d35f7f9993306b18  output/insights/2026-09-19/k2-loop-round3/materials/run-summary.json
1b0f6f56…  docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md  (= fig12 provenance の caption_source.sha256)
```

## 8. roundtrip 原本と `start_wall` の残存走査 (`scan_roundtrip.py`、段 6 レビュー M1 への追加実測)

走査 root 6 つ (repo の K2 insight dir 4 つ + repo 外 job dir `dev-wave-t2588-k2-loop-roundtrip/` / `dev-wave-t2746-k2-loop-round2/`)、全 615 file。
対象 sha = roundtrip 5 file (`ac12b80f…` / `c42dc712…` / `48520c2b…` / `e6b819f3…` / `1d834279…`) + round 3 の lock / digest / WAL (`f1ab4966…` / `f993251d…` / `eb8927b7…`)。

```
scan time: 2026-09-20 21:23:41 JST
files scanned: 615 roots: 6
sha hits (round1 5 file + round3 lock/digest/wal): [('round1-receipt', '.../dev-wave-t2746-k2-loop-round2/scratch-campaign/knowledge_manifest_receipt.json')]
files containing 'start_wall' or 'reverse_recommendations': 24 file (round 3 README / reviews 4 本 / run-summary.json、pair の run-summary-pair.json、
  t2588 job dir の codex event log 3 本 (plan / consult、走行前の設計議論)、t2746 job dir の diff 3 本・mutation json 2 本・codex event log 8 本、round 2 scratch の loop_state.json)
```

roundtrip の `loop_state.json` の `start_wall` / `reverse_recommendations` の値を持つ file は無い (語を含む 24 file の値の内訳は §10)。

## 9. pair 走の原本の byte 複製 (`copy_pair_originals.py`、付随項)

```
copied 6 files to /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/originals-copy-20260920 at 2026-09-20 21:24:36 JST
all match source: True
  campaign/campaign.lock 962ef7d787b7031a 8307
  campaign/knowledge_manifest_receipt.json c42dc712bbd11fc7 1317
  campaign/loop_state.json a8c6a8b69bc7bdd5 255
  campaign/s4_loop_digest.txt 8bde66fa21413dda 1939
  campaign/runs/wal.jsonl b5754f98c0643e80 7062
```

複製先は T-2795 の job dir (repo 外)。`MANIFEST.json` に 6 file (campaign 5 + `claims/p3-s4-loop-s4-autonomous-b24749ae.claim`) の sha256 / bytes / source 一致。
pair 走に `runs/agent_outputs.jsonl` は無い (役割の起動が無い走なので当然)。worktree の lock は未実施。

## 10. `start_wall` の値の内訳と、走査 (b) の条件込みの採り直し (`scan_values.py`、焦点再レビュー 1 巡目 M1 への追加実測)

同じ 6 root 615 file (21:36 JST)。語 `start_wall` / `reverse_recommendations` を含む file は **24** (§8 の 23 は誤記、24 に訂正)。うち `start_wall` に続く数値を持つのは 4 file だけ:
round 3 `materials/run-summary.json` = `1789824041.4768934` (round 3 の値)、pair `materials/run-summary-pair.json` = `1789899183.7126458` (pair の値)、
round 2 scratch `loop_state.json` と round 3 `reviews/s3-consult-a.md` = `1789681001.1930716` (round 2 の値)。残る 20 file (round 3 README / reviews 3 本、t2588 の codex event log 3 本
= 走行前の plan / consult、t2746 の diff 3 本・mutation json 2 本・codex event log 8 本) は語だけで数値を持たない。
**roundtrip 走行日 (2026-09-16 JST、epoch 1789484400..1789570799) の範囲の値は 0 件。** roundtrip の `start_wall` の値そのものは失われているので、「値が無い」は
「数値を持つ 4 file の値がいずれも roundtrip の範囲外」という意味で言う。

走査 (b) の採り直し (条件を stdout に出す版): 6 root 615 file について (i) round 2 digest `a0a4c204…` / round 3 digest `f993251d…` との sha256 一致、(ii) round 2 digest の
先頭 200 B の包含。結果: (i) hit = round 2 scratch の `s4_loop_digest.txt` 1 件 (round 3 digest は 0 件)、(ii) hit = 同じ 1 file。§6 の走査 (repo の insight dir 3 つ、0 件) は
この採り直しに包含される。
