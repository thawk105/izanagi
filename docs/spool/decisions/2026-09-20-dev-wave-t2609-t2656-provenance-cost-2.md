---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2609-t2656-provenance-cost
seq: 2
---

## {{D:provenance-batch-path-acquisition}}. 全史 provenance 監査の実装 path 取得と trailer parse を一括取得へ置き換え、失敗は既存 per-commit 経路へ戻す

**決定:** `tools/check_ai_provenance.py` の authoritative (引数なし) 監査で、commit ごとに起動していた git subprocess のうち
(a) 親取得 `show -s --format=%P`、(b) non-merge の `diff-tree --name-only`、(c) merge の親別 `diff --name-only`、(d) 同一 message への
重複 `interpret-trailers --parse` を、次の形で減らす。判定・findings・rc・公開出力・重複 selected の監査回数は 1 bit も変えない。

- (a) `_build_ancestry` が既に取っている `rev-list --topo-order --parents` の閉包全体から検証済み親表 (`_Ancestry.parents`) を作り
  `_commit_paths(commit, *, parents=...)` へ渡す。検証 (終端 LF・全 token が hex・40/64 混在なし・重複なし・要求根を含む・全親が index 内で
  子より先) に 1 つでも失敗したら親表全体を捨て従来経路。閉包外の親を root と解釈しない。
- (b) `git diff-tree --stdin --root --no-renames -r --name-only -z --always` に non-merge の OID を初出順で流し、40/64 hex の **全 token** を
  見出し候補として要求列と順序・件数込みで一致することを要求する。hex 名の path は候補が余るので全体 fallback。非空要求への空 stdout は失敗。
- (c) `git config --get diff.ignoreSubmodules` と `--get diff.relative` が **両方 rc=1 (全層で未設定)** のときだけ、`diff-tree --stdin` の
  `<merge> <parent>` 行 (`--diff-filter=ACMRDTUXB --always`) で親番号ごとに batch を取る。全 batch 成功後にだけ公開し、1 つでも失敗すれば
  全 merge を従来 `diff` × 親へ戻す。候補集合の intersection → `diff-tree --cc` は不変 (D721)。設定を argv (`--ignore-submodules=`) へ移す案は
  旧判定を変えるので不採用。
- (d) `validate_message` / `validate_implementation_author` に keyword-only `values=None` を足し、`_normal_commit_audit` (ancestry あり) で 1 回だけ
  parse して両方へ渡す。`values is None` のときだけ parse し、`[]` は再 parse しない。
- 高速経路は authoritative かつ ancestry ありに限る。oracle (`ancestry is None`) と `--range` の親・path 取得は従来のまま (values 共有は ancestry の
  ある両経路)。一括取得の失敗を新しい公開診断にしない。捕捉例外は投機取得に限り `RuntimeError, OSError, UnicodeError, ValueError`。
- dispatch 判定 (`main`)・`authoritative = args.rev_range is None`・`--force-dispatch`・受領証の束縛/publish・land の 480 秒 timeout は変えない。

**理由:**
- 計算ノード全史 (11,769 commit) の実測で subprocess 累積 1,128 秒のうち実装 path 取得が 66 % (`show %P` 29 %、merge `diff` 21 %、non-merge
  `diff-tree` 19 %)、trailer parse が 20 % で、D2033 後に残る per-commit コストの本体だった。起点の順位 (trailer → 隔離 fs → path → 祖先) は
  実測と逆で、隔離 parse の tempdir は 6 %、祖先索引は 0.1 % だった。
- 固定全史 (11,770 commit) の旧版 (`b7f970dfa` の blob) と新版の比較で、内部 `HistoryAudit`・selected 列・監査回数と、公開 rc/stdout/静的 stderr が
  login 4 走・計算ノード 4 走とも完全一致した。CPU 総量は login 305〜368 → 95〜105 秒、計算ノード 226 → 68 秒 (−70 %)、wall は login
  88〜143 → 69〜126 秒 (負荷依存)、ピークメモリ 718〜733 → 484〜625 MB。
- porcelain `git diff` は `diff.ignoreSubmodules` (UI config) を読み plumbing `diff-tree` は読まないため、gitlink が両親と異なる merge で判定差が出うる
  (段 3 相談 A)。未設定のときだけ有効化することで、等価性の論証を「差が効かない条件」に限定した。
- fail-closed の型は D2033 と同じ — 出力の形・件数・OID 一致のどれかが崩れたら部分結果を捨てて既存経路へ戻す。部分 batch の公開は変異で kill を確認した。

**却下した選択肢:**
- `_ai_agent_values` の `%(trailers)` 置換と cwd の隔離 dir 化 (repo cwd 4.3 ms → 1.1 ms) — repo local config (`trailer.*`、`core.commentChar`) を含む
  等価性証明を本 wave に持ち込まない (D2033 と同じ理由)。
- 隔離 parser の private dir を監査 1 走で共有 (11,315 回 → 1 回) — 取り分が計算ノードで累積 74 秒と小さく、監査 context の伝播と寿命管理に見合わない。
- `_batch_commit_messages` の format に `%P` を足す — D2033 の 3 field 契約と既存 fixture を変える。親は `rev-list --parents` に既にある。
- 候補別 ablation ((a)〜(d) の個別寄与の測定) — 時間対効果で総量の改善だけを示した。

## {{D:dispatch-cpu-input-deferred}}. 全史 provenance 監査の dispatch 判定へ CPU 時間 (負荷) を足す案は保留し、再訪条件を置く

**決定:** `login_headroom.grant_budget` がメモリ bytes だけを入力にし CPU/負荷を見ない現状を、本 wave では変えない。「不要と確定」ではなく
「証拠不足で保留」とし、再訪条件を **改善後の checker (D:provenance-batch-path-acquisition 以降) による login 全史監査が混雑時に 480 秒を超える観測が
1 件でも出たとき** に置く。発火したら、負荷を入力にした実行場所判断 (メモリ予約は維持、dispatch 時の予約解放、queue 停止時の扱い、`--force-dispatch` の
保存) を別 wave で設計する。`os.getloadavg()` の絶対しきい値だけでは host 容量・I/O 待ち・cgroup 制約を区別できないので、期限内完了を予測する材料
(履歴量・cold/warm・過去の CPU 秒と wall・実効 CPU 数) から設計する。

**理由:**
- 残存する provenance task の dispatch 受領証 86 件で基盤失敗 (rc=16) は 3 件 (3.5 %、Wilson 95 % 区間 1.2〜9.8 %)。3 件とも監査本体は完走しており
  失敗は前後処理 (呼び出し側 SIGTERM、orphan-hold 解放)。queue 待ちは中央値 5.2 秒だが最大 537.6 秒。
- land の `_run_provenance_checker` は `timeout=480` の呼び出し側 timeout を持ち、dispatcher の既定 queue 待ち上限は 900 秒。dispatch へ倒れると
  監査本体が正常でも queue 待ちだけで land が先に打ち切る構造があり、CPU 判定で dispatch を増やす前にこの両立 (D2148 項 8 の範囲) が要る。
- 起点の「login 428〜574 秒」は D2045 以前の混雑時観測で、本 wave では空いた login の cold 全史が旧 88 秒・新 69 秒、混雑時 (load 25〜45) でも新 78〜126 秒。
  混雑時の現行上限は観測できておらず、「480 秒に確実に収まる」とも「dispatch が必要」とも言えない。
- 受領証再利用は attributes fingerprint が index の directory 集合に依存するため land ではほぼ毎回 cold (直近 60 main commit の 50 % が新 directory を導入)。
  cold な land では dispatch に受領証の追加損失は無いが、計算ノード job は PBS job 環境を継承するので login シェルとは別 partition になる。

**却下した選択肢:**
- 今すぐ `os.getloadavg()` しきい値を判定に足す — 実効 CPU 供給を表さず、dispatch 側の 480/900 秒の構造も未解決。
- 「CPU 判定は不要」と確定する — 混雑時の観測が無い。
- land の `timeout=480` を延長する — 本 wave の scope 外 (T-2484 = D2148 項 8 の実装 wave の範囲)。
