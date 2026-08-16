---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1157-fetchcontent-reuse
seq: 1
title: 共有 FetchContent base の再利用を計算ノードで実測した — 置換も再 fetch も起きない (probe は repo 外、docs + insights、branch worktree-dev-wave-t1157-fetchcontent-reuse、実測 = Pegasus gen_S request 912911 / bnode009)
---

## 本文

- **測って `REUSED` を得た。** 床値本走が共有 FetchContent base を再利用できることの実測が
  これまで無く、根拠は CMake 3.22.1 のソース読解だけだった。1 job の中で
  prebuild 1 本 + cell build 2 本の計 3 本の configure を production seam で走らせ、
  `masstree-src` の inode、`config.h` と archive の inode + sha256、gitclone stamp、
  `FETCH_HEAD` / `packed-refs` / HEAD が**すべて不変**であることを確認した。
  材料の正本 = `output/insights/2026-08-16_t1157-fetchcontent-reuse/`。
- **本 wave の値は positive control 3 本の発火に支えられている。** 「変化しなかった」を主張する前に
  同じ job 内で「変化を検出できる」ことを示した。強制再 clone は
  `src_dir` / `config_h` / `archive` / `gitclone_lastrun` を動かし、直接の
  `git fetch --tags --force origin` は `FETCH_HEAD` を動かした。
  **up-to-date な fetch で動くのは `FETCH_HEAD` だけ**であり、そこが唯一の信号だと実測で確かめた。
- **焦点再レビューが「偽の検出力証明」を潰した。** fix 第 1 巡が入れた update 経路の
  positive control は、完全 SHA pin の object がローカルにあるため CMake が
  `fetch_required NO` の枝へ入り、**fetch せず checkout するだけ**だった。
  それなのに probe はその HEAD 変化で `refetch_detection_proven=true` を立てられた。
  **「再 fetch しない」という本 wave の中心値を、検出力ゼロのまま緑にできる経路だった。**
  実 fetch を起こす正例へ差し替えて閉じた。これは F28 の**再発**である —
  「その位置より手前に同じ入力を落とす検査が無いか」を、変異だけでなく
  positive control にも適用する必要がある。
- **実走 2 走目が偽 NO-GO を 1 件炙り出した。** `patch` step の stamp が `REFETCHED` 判定に
  入っており、production の 3 transition で mtime だけが進むため、単独性さえ通っていれば
  `REFETCHED` を返していた。実測すると inode 同一・内容同一 (空 file) で mtime だけが進む
  = `PATCH_COMMAND` を持たない no-op step の touch である。判定を
  `exists` / `st_ino` / `sha256` に限定し mtime は診断へ移した。
  `FETCH_HEAD` の mtime は判定に残した。緩めていないことは、変更後も positive control 2 本が
  発火することで担保した。恒久対応は {{F:false-positive-from-unrelated-field-in-verdict}}。
  **偽陰性 (恒真ゲート) だけでなく、偽陽性が実作業を止める側の害も同じ台帳で数える。**
- **単独性の 1 走目 false は共有ではなく残響だった。** `other_compute_processes` は空で
  `load1=2.96 > 2.4` だけが false 要因。job 開始直後の 1 分平均は直前 job の残響を含む。
  閾値を据え置いたまま 10 秒 × 4 サンプルの最終サンプルで判定する形へ訂正し、
  process 条件は全サンプルへ**強化**した。権威走行は 4 サンプルすべてで他者 process ゼロ、
  load1 は 1.05 → 0.89 → 0.75 → 0.78 だった。
- **第 1 走の失敗は床値の欠陥ではなかった。** `Could NOT find gflags` で configure #1 が落ちたが、
  原因は probe が production job の依存 provisioning を再現していなかったことである。
  `tools/pegasus/floor_campaign.sh` が gflags/glog を build/install して ambient
  `CMAKE_PREFIX_PATH` を張り、`buildcache` の `_canonical_ambient_dependency_prefix` が
  それを読む。**床値の起票にしていたら偽アラームだった。**
- **親 brief の事実誤認を 1 件、子より先に自分で訂正した。** 当初 brief は「base に当たる
  configure は 2 本」と書いていたが、床値は 2 holdout × 6 構成で構成集合が全 holdout 一致のため
  `sort_best` は 2 個あり、正しくは 3 本である。段 6 レビューも独立に同じ点を指摘した。
- **計算資源:** PBS job 3 本 (912848 / 912886 / 912911、いずれも gen_S)。
  権威走行は 103.4 秒。codex 子 6 本 (author 1 / review 1 / focus 1 / fix 4 のうち 3 本は fix)。
- **fix は 4 巡した。第 4 巡は `DW-O16` の 3 巡上限を超えている。** 新しいレビュー所見への追加対応
  ではなく、**実走が出した新事実** (偽 REFETCHED と load 誤測) への対応であり、
  放置すれば床値へ根拠のない NO-GO を出すことが理由である。

## 次の一手差分

### 完了

- [T-1157] 計算ノードで共有 FetchContent base の再利用挙動を 1 job で実測し `REUSED` を得た。
  置換 (inode) も再 fetch (clone stamp・FETCH_HEAD) も起きない。
  検出力は同一 job 内の positive control 3 本で裏づけた。
  射程は `bnode009` / `0:912911.nqsv` の 1 job・cold path に限る。
  remaining: none
  base: 1ca4f291470740a953e5f2d7cb43b0ddb491709f4946d2adf8a8949a3ba20ba4
