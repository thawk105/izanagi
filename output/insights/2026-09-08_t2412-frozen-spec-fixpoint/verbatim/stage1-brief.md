# 段 1 brief — T-2412 凍結 spec loader の hash 不動点

## scope

`orchestrator/campaign/floor_pair_driver.py` の `load_frozen_spec` が、凍結 spec を実 repository 上で
一度も作成できない状態を閉じる。実装差分は同 file と `orchestrator/tests/test_floor_pair_driver.py`
(および spawn 数 pin の登録簿) に限る。

## 実測した事実 (模擬でなく実 git)

- 不動点は実在する。実 git repo で確認した: base commit `edb191d2…` を `provenance.source_commit`
  に書いた spec を commit すると HEAD は `badb380b…` になる。bytes 一致 (`git show HEAD:spec.json`
  == 現物) は成立するが、`source_commit == HEAD` は成立しない。spec を commit しなければ
  `git show HEAD:spec.json` が `fatal: … not in 'HEAD'` で落ちる。どちらか一方しか満たせない。
- 該当箇所: `floor_pair_driver.py:1190-1191` (bytes == HEAD blob)、`1235-1239`
  (`provenance.source_commit != loaded_head` で拒否)。実行時にも `2175-2183` が
  `runtime_head == loaded_head == source_commit` を要求し、`2650` は期待 header の `runtime_head`
  を `spec.provenance.source_commit` から再構成する。
- 既存 test はこの不動点を構造的に見られない。`_install_git` (`test_floor_pair_driver.py:306-331`)
  が `subprocess.run` を monkeypatch し、`rev-parse HEAD` を定数 `HEAD = "b"*40` に、
  `show HEAD:<path>` を on-disk bytes に固定する。`SOURCE_COMMIT = HEAD` (26-27 行) なので
  模擬では両条件が常に同時成立する。F29 の型 (自己 hash・参照・pin を模擬で裁定した結果)。
- 凍結 spec の tracked 実体は repo に無い (`git ls-files` に floor-pair spec 無し)。spec を書く
  producer も無く、手書き commit を前提とした設計である。

## 不変条件 (規律 2 を緩めない)

1. spec は tracked かつ HEAD blob と byte 一致であること (事後編集を弾く) を維持する。
2. 測定は特定の commit へ束縛され続ける。「どの commit でも走る」方向へ緩めない。
3. 受理形を実質的に広げない。緩和に見える変更は、失う保証を 1 行で言えるまで採らない。
4. T-2423 (成果物名の protocol 要素) は未裁定のため触らない。`p3_b4_floor_artifact_issuer.py` は
   変更しない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** `provenance.source_commit` の意味を「spec を含む commit」から「spec を凍結した時点の
  code state = spec 導入 commit の親」へ読み替える。loader は `source_commit == HEAD の第一親` と、
  `source_commit..HEAD` の変更 path が spec の relpath ちょうど 1 件であることを要求する。
  bytes 束縛も code 束縛も失わずに不動点だけが消える、というのが親の読み。
- **(P1-b)** 実行時 `2175-2183` は `runtime_head == spec.loaded_head` を要求し、`source_commit`
  との一致要求は落とす。`2650` の期待 header の `runtime_head` は `spec.loaded_head` へ揃える。
  この 2 箇所を同時に直さないと、loader を通しても実行段で必ず落ちる。
- **(P1-c)** 実 git repo を作る test fixture を最低 1 本足し、実 commit で正例が通ることを示す。
  模擬 git だけの緑を「作成可能になった」の根拠にしない。

## 対抗案 (段 3 で潰すか採るかを決める)

- **案 X**: `provenance.source_commit` field を廃し、束縛を `loaded_head` だけにする。
  失うもの = 事前に「どの code state 向けの spec か」を宣言する能力。schema の exact key 集合が変わる。
- **案 Y**: `source_commit` を「HEAD の祖先であること」まで緩める。失うもの = spec 凍結後に
  任意の commit を積んでも load できてしまう (code state の同一性が消える)。親は不採用寄り。

## 変更面 (実アンカー)

| # | file:line | 内容 |
|---|---|---|
| 1 | `orchestrator/campaign/floor_pair_driver.py:1235-1239` | source_commit == HEAD の判定 |
| 2 | `orchestrator/campaign/floor_pair_driver.py:2175-2183`, `2650` | 実行時 / 期待 header 側の同一判定 |
| 3 | `orchestrator/tests/test_ccbench_spawn_sites.py:115-117` | git 呼出しを増やすなら (file, 関数) 単位の spawn 数 pin へ登録が要る |
| 4 | `orchestrator/tests/test_floor_pair_driver.py:26-27, 306-331` | 模擬 git fixture と定数 |
| 5 | `orchestrator/tests/test_official_perf_closure.py:53` | file 名の一覧のみ。内容変更では動かない (確認済み) |

## 成果物影響 (DW-G05)

放置すると `candidate_floor` が権威成果物として一度も発行できない。B-4 の材料レポートは floor
未接続のままで、分析 verdict が `protocol_violation` に固定される (D1592)。閉じれば発行経路の
生死を初めて実測できる。

## 分割方針

正しさ防壁に触り受理集合が変わるため、段 2 プラン・段 3 敵対 2 本・段 6 レビュー 2 本は省かない。
実装は 2 file が密結合なので実装子 1 本。Codex author = D95。仮想リスク向けの gate・検査・台帳・
一般化は追加しない (ユーザー明示)。
