# [T-202] real_repo_receipt_memo の2欠陥 — 段1-4 一次資料

commit `2fc7655e` の設計根拠。handoff (`/work/1/SFC/tanab/dev-wave-jobs/2026-08-19-t202-receipt-memo-handoff.md`、
セッション終了後は非保証) の段1-4 部分をここに保全する。

## 完了した中間成果 (着手前調査)
- worklog 一次資料を特定: `docs/archive/worklog-phase3-0731-73.md:102-106` (entry 73、原文)。
  現行 worklog 末尾 (709) でも `[T-202] (708)` として不変carry確認 (裁定待ちなし、実装専念可)。
- 欠陥 (b) の現物確認: `orchestrator/tests/real_repo_receipt_memo.py:144` (`pickle.loads`)、
  `:150` (`isinstance`)。`_cache_load()` 内、型検査前にデシリアライズが実行される。
- `ReceiptResolution` (`orchestrator/campaign/t080_freeze_migration.py:151-159`) の全 field 確認:
  `state:str, refusals:Tuple[str,...], t080_freeze_migration_observation:Optional[Mapping],
  validation_head:str, introduction_commit:Optional[str]=None, receipt:Optional[Mapping]=None,
  receipt_raw:Optional[bytes]=None, held_checks:Tuple[Mapping,...]=()`。`receipt_raw` が bytes
  なので JSON 化には base64 等の変換が要る。
- 欠陥 (a) の設計材料: `orchestrator/tests/conftest.py` の `pytest_configure` が
  `_RECEIPT_MEMO_SESSION_ID_ATTR = uuid.uuid4().hex` を config へ既に設定済み (controller 限定、
  worker は `if hasattr(config, "workerinput"): return` で prewarm から除外)。この nonce は
  当初プロセス内 (`finish_session` の入れ子復元) にしか使われていなかった。
  installed pytest-xdist 3.8.0 で controller→worker 伝播機構を実在確認: `xdist/newhooks.py`
  の `pytest_configure_node(node: WorkerController)`、`xdist/workermanage.py` の
  `self.workerinput = {...}` / `self.channel.send((self.workerinput,...))`、`xdist/remote.py`
  (worker 側 `config.workerinput = workerinput` は worker 自身の `pytest_configure` より前に
  完了)。`pytest_sessionstart`(worker起動) は `pytest_configure` の後に発火するため、controller
  の nonce 生成→`pytest_configure_node`での`workerinput`注入、の順序はタイミング上成立する
  (D517 の「移送先の実在」を実測)。
- `write_once()` は `path.exists()` で無条件 fail-closed (pre-exist を signal と見なさない)。
  read 側 `get()`/`read_existing()` にはこの疑いガードが無く、path が存在すれば無条件で
  `_cache_load` へ渡す — 非対称性が (a)(b) 両方の実効箇所。
- 兄弟モジュール `real_repo_ratified_memo.py` は pickle 不使用と確認 (同型欠陥なし、scope外)。
- `tools/run_tests.py` に `testrunuid` 関連コードなし (「素通し」の裏取り)。
- DW-O09 (凍結bytesのpin閉包) 確認: `real_repo_receipt_memo` の全 hit は import/呼出しのみで、
  FROZEN_MANIFEST 等の凍結台帳への出現なし → 非該当。

## 段1 brief (P1 = 親 provisional 裁定・段3 攻撃対象)
- **scope**: `orchestrator/tests/real_repo_receipt_memo.py` の2欠陥のみ。conftest.py への
  最小追加 (nonce 伝播 hook) は (a) の fix に必要なら許容。
- **確定済みユーザー裁定**: 「裁定待ち表記なし、実装専念でよい」。worklog原文の示唆する
  閉じ方向 = 「controller 所有の非再利用 nonce」+「closed-schema JSON」。
- **不変条件**: (1) memo は production resolver の実戻り値をそのまま運ぶ、受理集合は変えない。
  (2) D518 の barrier 位置・UID charset非拒否は変更しない。(3) `receipt_raw:bytes` を含む
  全 field が JSON 経由でロスレス往復。(4) `run_tests.py` の argv 形は変更しない。
  (5) (P1) 欠陥(a)の fix 方向は段2 codex が file:line で実在検証してから確定する。

## 段2 (codex plan) 結果概要
(b) pickle→closed-schema JSON。(a) controller nonce を新設 `pytest_configure_node` フックで
`workerinput` 経由 worker へ伝播し、cache path に混ぜる。reason語彙・既存test literalの
更新一覧を提示。

## 段3 (敵対相談2レンズ) 結果概要
初回投入は `--lane` 必須を見落とし argparse rc=1 で即死、`--lane luna` を付けて再投入し成功
(`--lane sol` は使っていない)。

レンズA (技術的正確性): plan の「`conftest.py:900-906` で worker が環境変数を設定する」
主張が現物と不一致と検出 (その行域は `pytest_configure()` 本体で環境変数設定は無かった)。
xdist の transport 機構自体 (`pytest_configure_node`/`workerinput`) は実在確認。JSON の
`object_pairs_hook`/`parse_constant` 欠落、DoS bytes上限欠如、reason改名のgrep漏れ1件
(`test_real_repo_serialization.py:1421`)を検出。

レンズB (scope・不変条件・一般化): 「戻り object そのもの」という不変条件表現の訂正必要
(xdist cache 経由では object identity は成立しない)。「report経路に影響しない」の記述も
不正確 (`patch_driver_resolver()` が実際に report 経路へ到達する、ただし値自体は不変)。
DW-G03 族一般化は不成立 (同型2例目なし)。`docs/failures.md` に該当既存Fなし。

## 段4 親裁定 (plan v2、実装子への確定指示)

**採用 (must-fix):**
1. worker 側 nonce 配線の場所を訂正 (controller限定 `pytest_configure_node` とは別に、worker
   でも実行される既存 `if hasattr(config, "workerinput"):` 分岐相当の箇所で読む)。空文字列・
   欠落は fail-closed。
2. JSON 読込を厳格化 (`object_pairs_hook`/`parse_constant`、`t080_freeze_migration.py:186-215`
   に倣う)。
3. 読込 bytes に妥当な上限を設ける (DoS対策)。
4. reason 語彙統合 (`cache-unpickle-failed`→`cache-json-decode-failed`、`cache-type-invalid`
   →`cache-schema-invalid`)。レンズA発見の漏れ含め全 active consumer を更新。
   `output/insights/**` の過去記録は編集しない。
5. `_prune_stale_caches` の glob を新旧両対応に広げる。
6. env var (nonce) の保存・復元を try/finally で例外安全にする。
7. docstring の不変条件表現を訂正。
8. 成果物影響の記述を訂正 (report経路には到達するが値は不変)。

**却下・対象外 (must-document, no code change):**
- reader-before-writer race は D518 barrier により通常経路では発生しない
  (`xdist/dsession.py` で確認)。
- リモート分散 xdist は現行設計も元々前提にしていない制約であり scope外。
- nonce は path にのみ埋め込み、JSON内容とのbinding検証はしない (意図的非目標)。
- nonce導入によるcache蓄積は既存6時間TTLのmtime pruneに委ね、許容するトレードオフとする。
- DW-G03 族一般化は不成立 (単発局所修復が正しいscope)。
- `docs/failures.md`に該当既存Fなし。実装後に実際に再発が起きた場合だけ新規F起票。

**変異事前登録 (DW-M01、暫定):**
M1 (schema検証前構築)・M2 (`object_pairs_hook`除去)・M3 (`parse_constant`除去)・
M4 (cache pathからnonce除去) を候補登録。段6 レビューが M3 は `_is_json_tree` と常に冗長で
単一理由性なし (登録せず defense-in-depth として維持) と判定、M2/M4 は positive control の
再照準が必要 (単一理由性を満たす形へ fix で修正済み) と判定。最終的に M1/M2/M4 の3件を
本走登録し、baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0 (probe再現性確認済み)。

## 落とし穴・気づき
- `write_once()` は pre-exist を即 fail-closed するが、`get()`/`read_existing()` (worker側)
  には同等の疑いガードが無い非対称性がある。(a)の実害はここに集中する。
- xdist worker 起動 (`DSession.pytest_sessionstart`) は controller の `pytest_configure` より
  **後**に走る。したがって `pytest_configure` で生成した nonce を `pytest_configure_node`
  経由で `workerinput` に載せるタイミングは成立する (`xdist/dsession.py` 自体には
  `pytest_configure_node`/`workerinput` の定義は無く、`xdist/newhooks.py` と
  `xdist/workermanage.py`/`remote.py` に実体がある — 探す場所を誤ると「存在しない」と
  誤判定するので注意)。
- 段2 codex plan は「機構 (`pytest_configure_node`/`workerinput`) が実在する」ことは正しく
  検証したが、「新設フックをどこに書くか」の具体的な file:line 主張は誤っていた。段3 敵対相談
  (brief の file:line を明示的に攻撃対象とする既存運用) がこれを捕捉した実例。
