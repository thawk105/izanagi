# 実測台帳 — dev-wave [T-989] / [T-932]

すべて Pegasus login node、repo 外 probe、production 無編集。
**測定条件**: 段 2 の codex 子 2 本が並行稼働中 (LLM 呼出主体、local は grep 程度)。
変動幅が大きいのはこの外乱を含むためであり、前後比較は**同一条件で撮り直す**。

## 前値 (改修前、branch = worktree-dev-wave-t989-t932-snapshot-cost @ 518a87e1)

### 【正本】fixture 全列 3 走、**静かな窓** (14:53-14:56 JST、codex 子ゼロ、warm cache)

D357 の「測定中は自分の他 job を同時に走らせない」を満たす条件で撮り直したもの。
**前後比較にはこちらを使う。**

| 走 | total | `_build_snapshot_base` | derive POS | derive NEG |
|---|---|---|---|---|
| 1 | 43.72 | 35.02 | 4.12 | 3.84 |
| 2 | 56.86 | 47.65 | 4.24 | 4.20 |
| 3 | 41.68 | 31.95 | 4.49 | 4.36 |
| **中央値** | **43.72** | **35.02** | 4.24 | 4.20 |

**ノイズ床**: 静かな窓でも total の幅は 41.68〜56.86 (中央値比 −5% / +30%) ある。
共有 login node + Lustre の変動であり、**10% 未満の差は主張できない** (D357)。

### 【参考・条件不良】同じ 3 走、codex 子 2 本の並行稼働中 (14:28-14:31 JST)

| 走 | total | `_build_snapshot_base` | derive POS | derive NEG |
|---|---|---|---|---|
| 1 | 41.54 | 32.29 | 4.19 | 4.16 |
| 2 | 60.63 | 50.11 | 4.37 | 5.39 |
| 3 | 51.16 | 42.32 | 4.11 | 4.01 |
| **中央値** | **51.16** | **42.32** | 4.19 | 4.16 |

初回 cold 走 (13:58 JST、他負荷なし) は total 61.65 / `_build_snapshot_base` 52.63。

### `_build_snapshot_base` 相当の 3 方式 x 3 走 順序交互 (14:17-14:20 JST)

| 方式 | 走 1 | 走 2 | 走 3 | 中央値 |
|---|---|---|---|---|
| 現行 `git clone --no-hardlinks --no-checkout` | 33.09 | 34.31 | 43.21 | **34.31** |
| A `git init` + `git fetch <path> <生 SHA>` | 6.07 | 7.13 | 5.21 | **6.07** |
| B `pack-objects` → `index-pack --fix-thin` | 4.68 | 5.01 | 7.07 | **5.01** |

9 走すべて: `_one_git_closure_reasons` reason 0 件 / 8,209 object / 834 commit /
`.git` 35,132 KB / `commit_graph.present=false` / 残留 pseudo ref 0 件。

### 段別内訳 (代表値)

| 段 | clone | A fetch | B pack |
|---|---|---|---|
| transfer | 3.91-4.98 | 0.89-2.31 | 0.93-0.98 |
| `_init_submodules_from_local_source` | 0.58-1.79 | 0.39-2.38 | 0.38-0.66 |
| `_seal_git_object_closure` | **25.43-37.20** | 2.50-2.98 | 2.47-4.74 |

### 構造の値

- 実 repo: 3,920 commit / `.git/objects` 159 MB
- clone 直後の base: 157 MB → seal 後 11 MB (root のみ) / 35 MB (submodule 込み)
- `BASE_COMMIT` 到達分: 834 commit / 8,209 object (**固定。将来の commit 増で増えない**)
- fixture consumer 17 本中 14 本が既定 skip (保留)、既定で走るのは 3 本

### seal の root / submodule 分離 (14:35-14:36 JST、委譲 wrapper、production 無編集)

`_seal_one_git_closure` を委譲 wrapper で包み、`expected_ref is not None` を root、
`None` を submodule として別集計した。

| 段 | clone 経路 | pack 経路 (方式 B) |
|---|---|---|
| transfer | (計測内) | (計測内) |
| `_init_submodules_from_local_source` | 1.88 s | 0.47 s |
| `_seal_git_object_closure` 合計 | 36.44 s | 2.46 s |
| └ **root の seal** | **33.64 s** | **0.38 s** |
| └ submodule の seal 合計 | 2.76 s | 2.03 s |
| 　└ ccbench / shirakami / googletest | 0.71 / 0.38 / 1.67 | 0.24 / 0.39 / 1.41 |

**結論: 支配項は root repository の `repack -Ad` ただ 1 つである (33.64 s)。**
狭い転送にすると **0.38 s** になる (88 倍)。submodule 側は 2.0〜2.8 s で
izanagi の成長に依存せず、改修の前後でほぼ変わらない。

**これは `plan-s1b.md` の仮説 (「submodule seal が 55〜75% の約 6.8〜9.3 秒、
init が 25〜45% の約 3.1〜5.6 秒」) を反証する。** 実測は root seal 92%、
submodule seal 8%、init は seal 合計の 5% である。
brief 本文の「submodule 約 12.3 秒」も同時に反証されている (追補 3 で取消済み)。

### (P1) 方式 A がなぜ通るのか — 経験的特定 (14:33 JST)

- `git --version` = **2.34.1**
- 元 repo に `uploadpack.allowAnySHA1InWant` / `uploadpack.allowReachableSHA1InWant` /
  `protocol.version` の設定は**いずれも無い** (`git config --get` が rc=1)
- `BASE_COMMIT` は **HEAD から到達可能** (`merge-base --is-ancestor` rc=0) だが、
  **どの ref も指していない** (`for-each-ref --points-at` = 0 件)
- **path transport (`<path>`) と `file://` transport の両方で rc=0**、いずれも 8,209 object。
  つまり local 経路の特例ではなく、upload-pack が到達可能 SHA の want を受けている。

**結論:** 方式 A は「到達可能な SHA の want を upload-pack が受ける」挙動に依存する。
本ホスト・本 git 版では成立するが、**設定・git 版に依存する契約である**。
倒れる向きは `fetch` の非 0 終了なので fail-closed であり、静かに別物ができる経路は
本実測の範囲では観測されていない。
方式 B (`pack-objects`) はこの受理方針に**一切依存しない**。

`git fetch <path> <sha>` の残留物: `FETCH_HEAD` が生成される (remote は作られない)。
`FETCH_HEAD` は `_seal_one_git_closure` の `*_HEAD` 削除 (`tools/codex_reasoning_ab.py:843-850`)
で消える — 9 走の probe で残留 0 件を実測済み。

## 後値 (改修後、S1 実装済み tree)

### fixture 全列 3 走、静かな窓 (15:10-15:12 JST、codex 子ゼロ、warm cache、前値と同一手順)

| 走 | total | `_build_snapshot_base` | derive POS | derive NEG |
|---|---|---|---|---|
| 1 | 15.67 | 6.89 | 4.13 | 3.90 |
| 2 | 20.83 | 11.60 | 4.16 | 4.31 |
| 3 | 22.76 | 10.31 | 4.03 | 3.99 |
| **中央値** | **20.83** | **10.31** | 4.13 | 3.99 |

### 前後比較 (どちらも静かな窓の 3 走中央値、D357)

| 量 | 前 | 後 | 変化 |
|---|---|---|---|
| fixture 全列 | 43.72 s | **20.83 s** | **−22.89 s / −52.4%** |
| `_build_snapshot_base` | 35.02 s | **10.31 s** | **−24.71 s / −70.6%** |
| `_derive_snapshot_from_base` x2 | 8.44 s | 8.02 s | −5% = **変化なし** (D357 の 10% 未満) |
| `prepare_cases` (session corpus) | 0.13 s | 0.13 s | 変化なし |

いずれもノイズ床 (中央値比 -5% / +30%) を大きく超える。

**残る律速は `_derive_snapshot_from_base` の `shutil.copytree` x2 = 約 8 秒**へ移った。
これは sealed base (35,132 KB) の複製であり、`BASE_COMMIT` が固定である限り
izanagi の成長に比例しない。

### 不変条件の確認 (新コード、15:10 JST)

改修後の tree に対して `probe_narrow_base.py . pack` を実行:
`closure_reasons` **0 件** / `refs` は expected 1 件 / `head` = `BASE_COMMIT` /
object **8,209** / commit **834** / `.git` **35,132 KB** / `commit_graph.present=false` /
残留 pseudo ref **0 件** — **前値と完全一致**。

## 受入 wall

### 段 3 sol 所見 7 の裁き — `pack-objects` の source サイズ依存 (14:52 JST)

同じ `BASE_COMMIT` 閉包を 2 つの source から取り出して 3 走ずつ比較した。

| source | commit | object | pack 数 | 走 1 | 走 2 | 走 3 |
|---|---|---|---|---|---|---|
| 実 repo 全体 | 3,922 | 49,820 | 14 | 0.641 | 0.325 | 0.315 |
| BASE 閉包のみ | 834 | 8,209 | 1 | 0.068 | 0.065 | 0.066 |

出力 pack は **10,341,970 bytes で同一**。

**所見 7 は real。** `pack-objects` の費用は source 側の object 数に**弱く比例する**
(object 数 6.1 倍に対し時間 4.8 倍)。したがって
**「commit 数から完全に切り離した」とは書けない。**
正しい主張は「**33.64 秒の支配的な線形項 (`repack -Ad` の全 object 再圧縮) を除去し、
残る比例項は係数が約 100 分の 1 になった**」である。
現在値 0.32 秒は、commit 数が 10 倍になっても約 3 秒であり、現行の 33.6 秒を下回る。

### 段 3 sol 所見 3 / 所見 4 の裁き — 変異が殺されるか (14:51 JST)

`_build_snapshot_base` 相当の列から特定の段を飛ばして、既定で走る検査が赤くなるかを実測した。

| 変異 | `_one_git_closure_reasons` | `_submodule_repositories` | 既定 node は赤か |
|---|---|---|---|
| なし (方式 B) | reason 0 件 | 3 件 | — |
| `_init_submodules_from_local_source` を飛ばす | **reason 0 件 (受理してしまう)** | **0 件** | **赤** (`:1155` の `assert submodules` が false) |
| `_seal_git_object_closure` を飛ばす | **reason 1 件** (`.: reflog closure is not empty`) | 3 件 | **赤** (`verify_snapshot` が例外) |

- **所見 3 は half real。** production の `verify_snapshot` は submodule 未初期化を
  **reason 0 件で受理する** (既定 `_snapshot_spec` に `submodule_manifest_sha256` が無い —
  実測で `default_spec_pins_submodule_manifest=false`、key は
  branch/case/forbidden/hashes/head/modes/numstat/tracked_paths/untracked の 9 個のみ)。
  これは**本 wave が作ったものではない既存の fail-open** である。
  ただし変異自体は `test_snapshot_submodule_object_store_is_recursive:1155` が殺す。
- **所見 4 は refuted** (ただし snapshot 系 3 本を保留しない場合に限る)。
  seal 削除は reflog 検出で赤になる。

### `.git/shallow` — sol 所見 1 の裏取り (14:50 JST)

`grep -c shallow tools/codex_reasoning_ab.py` = **0**。
`_one_git_closure_reasons` の `closure_paths` (`:1347-1356`) は reflog / replace refs /
alternates / http-alternates / grafts / packed-refs の 6 つで、**`shallow` を列挙しない**。
`git fsck` も shallow 境界を正当な履歴端として扱う。**盲点は実在する。**

## 運用上の制約 (14:39 JST 実測)

`python3 tools/run_tests.py orchestrator/tests/test_hold_inventory.py` (flag なし) は
**rc=16** で止まる。理由は bounded local scope の
`memory.max` / `memory.oom.group` を走行中に attest できないこと
(「dispatcher infrastructure failure」)。予算算出自体は成功している
(3,131,485,080 bytes 予約、回収不能 9,753,416,808 bytes、実効天井 15,032,385,536 bytes)。

**したがって本 wave の焦点走は `--force-dispatch` で計算ノードへ出す必要がある。**
bounded local の回避路は今は使えない。

## erratum 1 — commit `ffe74a1f` 本文の root seal 値 (段 6 レビュー B 所見 1)

commit 本文は 4 つの bullet をまとめて「3 走中央値」と導入したが、
そのうち **root seal の 33.64 秒 → 0.38 秒は単発計測**であり中央値ではなかった。
3 走中央値を持っていたのは fixture 全列 / `_build_snapshot_base` / derive の 3 量だけである。

**3 走ずつ順序交互で撮り直した値 (15:46-15:49 JST、静かな窓)。**

| 量 | 走 1 | 走 2 | 走 3 | 中央値 |
|---|---|---|---|---|
| clone 経路の root seal | 23.29 | 27.26 | 26.30 | **26.30 s** |
| pack 経路の root seal | 0.33 | 0.38 | 0.32 | **0.33 s** |
| clone 経路の submodule seal 合計 | 3.03 | 2.31 | 2.82 | 2.82 s |
| pack 経路の submodule seal 合計 | 2.16 | 2.04 | 2.03 | 2.04 s |

**訂正後の正しい記述: root seal は 26.30 秒 → 0.33 秒 (中央値、約 80 分の 1)。**
commit 本文の 33.64 / 0.38 は取り消す。**単発値であり、かつ 33.64 は 3 走の上振れだった。**
submodule seal は 2.8 → 2.0 秒で、izanagi の成長に依存しない固定費である。

## erratum 2 — 「残る律速は copytree 約 8 秒」は誤り (段 6 レビュー B 所見 3)

逐次計時で分離した結果 (15:42 JST)、derive 段の内訳は次のとおりだった。

| 段 | POS | NEG |
|---|---|---|
| `_preflight_snapshot_relocation` (base) | 0.03 | 0.03 |
| **`shutil.copytree`** | **0.21** | **0.24** |
| `_preflight_snapshot_relocation` (snapshot) | 0.04 | 0.04 |
| golden 書込 + artifact 取り出し | 0.12 | 0.07 |
| **`verify_snapshot`** | **3.62** | **7.38** |
| case 合計 | 4.03 | 7.76 |

**copytree は 0.21〜0.24 秒であり律速ではない。残る費用の 90% 以上は `verify_snapshot`** である
(snapshot の全 file の sha256 + `.git` の `_metadata_manifest` + `_filesystem_file_set` 走査)。
親が `measurements.md` 初版と handoff に書いた「残る律速は copytree」は**取り消す**。

`verify_snapshot` の費用は snapshot の内容 (= `BASE_COMMIT` の tree + submodule の checkout) に
比例する。`BASE_COMMIT` は定数なので izanagi の commit 増では増えないが、
**submodule pin が前進すれば増えうる**。この点はレビュー B 所見 3 の指摘どおりで、
「`BASE_COMMIT` 固定だけを固定費の条件とする」記述は狭めた。

なお、wrapper 会計による最初の分離計測は成分和 (12.7 秒) が全体 (8.8 秒) を超える
内部矛盾を起こしたため**採用しなかった**。上表は逐次計時による撮り直しである。

## 受入 wall

未実施。段 6 で受入 lease 内に測る。
