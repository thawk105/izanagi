# [T-139] R4 環境 probe — submission receipt (append-only、qsub より前に作成)

```text
authority: none
default_effect: no-state-change
```

本書は probe を投入する**前**に作る。投入後に既存行を書き換えず、結果は追記する。

## 1. 投入する commit と blob

**期待 commit: `6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec`**

| path | sha256 |
|---|---|
| `tools/pegasus/probes/t139_r4_env_probe_contract.json` | `a1445a65612007e0a0ac6dcb9abb0fbc6b3b1cb98379eeef2c4b90eac8458950` |
| `tools/pegasus/probes/t139_r4_env_probe.sh` | `1f1d80252043ecaab0202b4f2c52a9f80397da2e4c3c1aa201019da16e72f76b` |
| `tools/pegasus/probes/t139_r4_env_probe.py` | `1f94d30bfb3dfe19a8942b8093cc4924779976e5ad3bdcb7d7d9c85292f076a2` |
| `tools/pegasus/probes/t139_r4_env_probe.pbs` | `edfa7b0c2e5d40a91cbfc1bdcd469b52d38a34f2f6ddc2d14f86ce4e35078014` |

**判定写像の凍結**: `output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md` と
上記 contract blob は、本 receipt の commit に含まれており、**probe の実行より前に commit 済み**である。
これが裁定 R4 (a) の「導出写像を probe より前に凍結する」の履行である。

## 2. 凍結 core (bytes 不変)

| path | sha256 | 状態 |
|---|---|---|
| `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` | `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` | 本 wave で 1 byte も変更していない |

## 3. 依存 source root

| 種別 | root |
|---|---|
| gflags / glog | `/work/1/SFC/tanab/izanagi-thirdparty-deps` |
| masstree / mimalloc / googletest | `/work/1/SFC/tanab/izanagi-thirdparty-cache` |

## 4. qsub の env

```text
IZANAGI_T139_EXPECTED_COMMIT=6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec
IZANAGI_T139_EXPECTED_WORKTREE_ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-r4-probe
IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps
IZANAGI_THIRDPARTY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-cache
```

scheduler 出力は `-o` / `-e` で repo 外の具体ファイルへ向ける
(repo を submit directory にする job は、既定では前回出力自体で clean-tree 検査に落ちるため)。

## 5. 再走規律 (凍結済み)

**窓を 1 つでも観測した attempt は terminal とし、再走は 0 回とする。**
job body が probe namespace の既存 attempt を走査し、観測済み行があれば起動を拒否する。

- **限界**: これは scheduler 証拠つきの pre-submit ledger ではない。
  namespace ごと破棄する経路と、まだ観測行を publish していない同時 submit は防げない。
  この限界は契約 blob と受領証にも明記してある。

## 6. submission 台帳 (append-only)

| # | request ID | 投入時刻 | replacement-of | 理由 | terminal state |
|---|---|---|---|---|---|
| 1 | (投入後に追記) | | — | 初回 | (追記) |
