# S-1 freeze 再発行 wave ([T-005]) の逐語 (2026-07-21)

ハイブリッド標準ループ (/dev-wave) の各段の逐語。基準 HEAD `f2f3756`、branch `worktree-dev-wave-ruling-ac`。
task-run = `20260720-s1-freeze-reissue-e5aef5fe`。**scope 判定・裁定の正本は worklog と D71 であり、本ファイルは素材である。**

本 wave は **実装せず裁定パッケージで終わった**。canonical 成果物 (`output/s1-freeze/*.json`、
`output/s8b-freeze/holdout_freeze.json`) は 1 byte も変更していない。逐語を残す理由は、
親の provisional 裁定 8 件のうち 6 件が敵対相談で否認された経緯そのものが素材だからである。

---

## 段 1: brief (親、逐語)

# brief — [T-005] S-1 freeze の再発行 (dev-wave 段 1)

## scope

`output/s1-freeze/known_axes_freeze.json` と `output/s1-freeze/measurement_freeze.json` を正規手順で
**再発行**し、旧凍結との対応を機械検査可能な形で残す。合わせて、再発行が今後も同じ理由で壊れないよう
generate 時のガードを入れる。S-1 reader を共有 WAL parser へ収束させる作業は**本 wave の scope 外**
(裁定文が「これが済むと収束できる」と後続扱いしている)。

## 確定済みユーザー裁定 (2026-07-21)

- 再発行そのものは**承認済み**の実装 wave
- 条件: **再発行時は旧凍結との対応を記録に残す**こと
- 収束 (S-1 reader → 共有 parser) は本 wave の後

## 実測で確定した事実 (brief の土台。ここが誤っていれば以降は全部誤り)

- **F1** 破損は `frozen_at_head` の 1 点のみ。記録値を override して `build_document()` を回すと
  freeze 内容は**完全一致**で再構成できる (entries / sources sha256 / generator sha256 は健全)
- **F2** 歴代 5 回すべての `frozen_at_head` が repo に存在しない (`c648bbe` / `ca92133` / `c890e95` /
  `0f30427` / `2066ce6b` の全てが GONE)。**構造的**であって一度の事故ではない
- **F3** `python_version` は検査されない。`verify_document` が記録値を override として echo する
  (`orchestrator/campaign/s1_known_axes_freeze.py:762`)
- **F4** `ccbench_pin` は一致 (`d706650`)
- **F5** `generate()` は既存 freeze を拒否する (`s1_known_axes_freeze.py:770-773`)。再発行経路は
  「人間が明示削除 → 再実行」しかない
- **F6** `measurement_freeze.json` も同じ死んだ SHA (`2066ce6b`) を持ち、その verify は known_axes を
  照合するので連鎖して落ちる
- **F7** ancestry 検査 = `s1_known_axes_freeze.py:747-754` (`cat-file -e` + `merge-base --is-ancestor
  <sha> HEAD`)。失敗は公式 oracle gate (`s8b_oracle_driver.py:261`) の `known-axes-freeze-verify` 拒否へ伝播
- **F8** ref 現況: `origin/main`=`da37d7f` (published)、local `main`=`8108059` (未 push、HEAD の ancestor)、
  HEAD=`f2f3756` (未 published の wave branch)

## 不変条件 (破ったら即 reject)

- **規律 2**: verify を通すために検査を外す・緩める・期待値を実測へ寄せる変更は禁止。
  D68 (7) の再発 (fixture へ現行 hash を差し込んで破損を隠す) は最優先の禁止事項
- 再発行で変わってよいのは `frozen_at_head` と `python_version` のみ。**それ以外に差分が出たら停止**し
  原因を報告する (それは再発行ではなく内容の変質)
- 実装子が触ってよいのは**コードとテストだけ**。docs 編集と git commit は禁止
- 「改竄耐性」「改竄不能」「証明可能」とは書かない (D68 (6)、脅威境界は「正直だがバグりうる producer
  への構造検査」)

## 親の provisional 裁定 (= 攻撃対象。1 件ずつ否認/採用を返してほしい)

- **(P1)** 本作業は「値を作り直す」のではなく「**provenance anchor を貼り替える**」作業である。
  内容 (entries / sources) は健全なので再測定・再選定は不要
- **(P2)** `frozen_at_head` は**published commit** (`origin/main` に含まれ、かつ HEAD の ancestor) を
  指すよう改める。未 published の wave branch HEAD に張ると、次の rebase で F2 が再発する
- **(P3)** published 判定は **`generate()` 側のガードに限定**し、`verify()` は現状のまま
  (HEAD に対する ancestry の fail-closed) を維持する。verify に remote 依存を持ち込まない
- **(P4)** 旧凍結との対応は freeze JSON の中ではなく**別台帳ファイル**に記録する。freeze の
  `TOP_LEVEL_KEYS` は完全一致検査 (`:701-702`) なのでキー追加は再構成検査へ波及する
- **(P5)** 台帳は**機械検査する**。最新エントリの `new_sha256` が現行 freeze の実ハッシュと一致することを
  テストで固定する。検査されない台帳は恒真な記録にすぎない
- **(P6)** 旧 freeze のバイト列は git 履歴が保持しているので、**アーカイブ複製は作らない**。台帳には
  content sha256 と旧 `frozen_at_head` を書いて対応が引けるようにする
- **(P7)** 2 つの freeze は**同時に再発行**する (F6 のため片方だけでは不整合)
- **(P8)** S-1 reader の共有 parser 収束は scope 外。ただし本 wave の再発行機構が「script を変えたら
  正規手順で再発行できる」ことを実際に示すため、generator の変更 (P2/P3 のガード追加) を**再発行の
  実演として使う**。これにより機構が恒真でないことが実証される

## 成果物の形

1. 再発行された 2 つの freeze JSON (差分は `frozen_at_head` と `python_version` のみ)
2. 旧→新の対応台帳 (機械検査つき)
3. `generate()` の published-anchor ガードと、再発行の正規経路
4. 変異で裏取りしたテスト群

## 並列分割の方針 (ファイル所有を素集合に)

- 単位 A: `s1_known_axes_freeze.py` + その test (anchor ガード・台帳検査)
- 単位 B: `s1_measurement_freeze.py` + その test (同型適用)
- 台帳の実データ生成と 2 freeze の実再発行・受入全走は**親**が行う (実装子は commit しない)

## 事前登録する変異 (B-057、段 6 で実測)

- **M1** ancestry 検査 (`:750-754`) の `merge-base --is-ancestor` を無条件成功へ → 死んだ SHA を受理するか
- **M2** published-anchor ガードを無効化 → 未 published commit を anchor にした生成を許すか
- **M3** 台帳の `new_sha256` 照合を外す → 現行 freeze と食い違う台帳を受理するか
- **M4** `generate()` の既存拒否 (`:770-773`) を外す → 既存 freeze の暗黙上書きを許すか
- **M5** source sha256 照合 (`:739-741`) を外す → 改竄 source を受理するか (既存テストで kill 期待)

kill の判定は「テストが赤くなった」ではなく「**受理集合または fail-closed 挙動が期待方向へ変わった**」。
診断文字列だけの変化は帰属不成立として数えない。

---

## 段 1 追補: 起草後に判明した実測事実 (親、逐語)

# brief 追補 — 起草後に判明した実測事実 (F9..F12)

これらは brief 執筆後に子エージェントの構造調査と親の実読で確定した。**brief 本体と同じく攻撃対象**。

- **F9** 共有 WAL parser は `orchestrator/campaign/wal.py` (D68 で新設)。公開 API は
  `parse_line` (:48-82) / `iter_lines` (:95-104) / `append` (:109-130) / `log` (:133-140) /
  `read_records_collected` (:145-173、行単位 issue reader) / `read_records_checked` (:176-195) /
  `read_records` (:198-201)。**S-1 は未収束**で、自前 reader は `s1_known_axes_freeze.py:128-144`
  (`_wal_records`: 素の `json.loads`、duplicate key 拒否なし、必須 5 キー検査なし)

- **F10** `generate()` の既存拒否は**二層**である。`s1_known_axes_freeze.py:770-773` の
  `output_path.exists()` 検査に加え、`:776-781` の `open(output_path, "x")` が `FileExistsError` を
  `FreezeError` へ翻訳する TOCTOU 二重防御。**片方だけ変異させても受理集合は変わらない (等価変異)**。
  事前登録 M4 は**両層同時変異**でなければ kill を数えられない。
  `s1_measurement_freeze.py:453-456` + `:468-469` も同一構造

- **F11** `s8b_holdout_freeze.py` の `supersedes_sha256` は「採用済みの作法」**ではない**。
  `:618-626` の `GENERATION_SCHEMA_FIELDS` に含まれ、`:629-638` の `_reject_unratified_generation` が
  **その field を持つ document を一律拒否**する (承認束縛方式が §8 で未裁定のため fail-closed)。
  さらに `:641-652` は「世代別 filename + supersedes 連鎖 + 承認束縛」を伴う v2 でのみ blob 救済が
  許されると明記する。**freeze 内の世代連鎖は本 repo では裁定待ちの概念**であり、S-1 の freeze へ
  `supersedes_sha256` を入れると、s8b が意図的に無効化している機構を S-1 側で裏口から有効化することになる

- **F12** `measurement_freeze.json` は `implementation_hashes.known_axes_freeze` に
  **known_axes JSON ファイル全体の sha256** を記録する (`s1_measurement_freeze.py:252-258`)。
  かつ `verify_document` (:387-444) の :408 が `_verify_known_axes` 経由で known_axes の
  `verify_document` を連鎖実行する。**片方向依存**であり、親が実測した通り known_axes が壊れている間は
  measurement の `build_document()` すら例外で止まる。再発行順序は known_axes → measurement で強制される

- **F13** 公式 oracle gate の伝播: `s8b_oracle_driver.py:257-261` が `verify` の例外を `refusals` へ
  翻訳 → `:288` で `allowed=not refusals` → `run_block` (:948-953) が実走前に
  `status="refused"` で早期 return → `_EXIT_CODE_BY_STATUS` (:1342-1348) により**プロセス終了コード 2**

- **F14** 過去の再発行前例 `15fcc08` (2026-07-15) は freeze を**丸ごと上書き**しており、
  `frozen_at_head` と各 sha256 のみが変わり `entries` の実測値は不変。対応記録キーは追加されず、
  旧 blob は git 履歴側にのみ残る。**アプリケーション側の archive 機構はコードに無い**

## F11 を受けた親の裁定修正 (これも攻撃対象)

- **(P4′)** 旧凍結との対応は freeze JSON の外の**別台帳ファイル**に記録する。根拠は当初の
  「`TOP_LEVEL_KEYS` 完全一致検査への波及」に加え、**F11** — freeze 内世代連鎖は本 repo で
  fail-closed 扱いの未裁定概念であり、S-1 でだけ有効化するのは越権である。
  台帳は「発効中の唯一の freeze」という現行モデルを変えない純粋な provenance 記録に留める。
  **この区別が詭弁でないかを攻撃してほしい** — 台帳が事実上 supersedes 連鎖と同じ信頼を要求するなら、
  それは s8b が拒否している機構の裏口実装であり、本 wave では作らずユーザー裁定へ回すべきである

---

## 段 2: プラン起草 (codex gpt-5.6-sol / reasoning=max / read-only、逐語)

## brief の裏取り結果

結論は、F1〜F6・F8 は概ね正しいものの、brief のままでは実装不可です。主な問題は次の4点です。

- measurement は known freeze の全バイト SHA を持つため、「両 freeze とも差分は `frozen_at_head` / `python_version` だけ」は成立しない。
- generator を変更すれば自己 SHA も必ず変わるため、P8 と差分制約が衝突する。
- S8b holdout freeze も known freeze の旧 SHA を固定しており、2ファイルだけの再発行では別の公式 gate が不一致になる。
- 変異 M1 と M4 は記載どおりでは受理集合を変えず、kill と数えられない。

pytest は実行していない。以下はコード読解、Git object/ref 検査、読み取り専用の `build_document()` 再構成による結果である。

### F1〜F8

| ID | 判定 | 裏取り結果 |
|---|---|---|
| F1 | 採用（known 側に限定） | 記録済み4値を override して [build_document()](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:608) を実行し、文書全体、entries、selection rules、63件の source record が完全一致した。generator 実 SHA も記録値と一致する。通常 verify は [ancestry 検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747) だけで停止した。 |
| F2 | 採用 | Git 履歴から `80b3010→c648bbe`、`15fcc08→ca92133`、`8f7fca2→c890e95`、`b4e5cb6→0f30427`、`e5dfa84→2066ce6b` を復元し、5 SHA すべて `git cat-file -e` 不成立を確認した。 |
| F3 | 採用 | [known:759-763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759) と [measurement:430-438](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:430) は記録値を再構成へ渡すだけで、実行中 Python との一致を検査しない。型も明示検査されない。 |
| F4 | 採用（表現差あり） | submodule 実 HEAD は `d706650c…`。known は40桁、measurement は `pin.CURRENT_PIN == "d706650"` の短縮形で、それぞれ verifier の期待と一致する。 |
| F5 | 採用 | 両 generator とも事前の存在検査に加え、`open("x")` でも競合を拒否する。[known:769-782](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:769)、[measurement:447-470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:447)。公式 CLI に再発行操作はない。 |
| F6 | 採用 | 両 JSON は `2066ce6b…` を共有する。measurement は [known の verify を先に呼ぶ](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:407) ため、実測でも `known_axes_freeze 照合失敗` で停止した。 |
| F7 | 要修正 | cited path と [oracle refusal への伝播](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249) は正しい。ただし oracle はその前に v1 holdout も [verify()](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216) する。holdout は [known の旧 SHA](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:9) を固定し、[worktree bytes との一致](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:641) を要求する。known 再発行後はここも不一致になる。 |
| F8 | 採用 | 実測値は `origin/main=da37d7f…`、`main=8108059…`、`HEAD=f2f3756…`。前二者は HEAD の ancestor、local main は origin/main に未包含だった。なお「published」はローカル remote-tracking ref に基づく観測で、今回 fetch はしていない。 |

さらに、[test_frozen_artifacts.py:33-39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33) が2つの S-1 freeze の現行 SHA を literal 固定している。再発行時に必ず追随設計が必要であり、brief のファイル分割から漏れている。

### P1〜P8

| ID | 判定 | 理由 |
|---|---|---|
| P1 | 要修正 | 再測定・再選定は不要という部分は採用する。ただし artifact transition は anchor だけではなく、measurement の known hash と、コード変更時の自己 hash を含む。 |
| P2 | 採用 | `refs/remotes/origin/main` の commit を anchor とし、それが HEAD の ancestor でもあることを生成時に要求する。今回は tip `da37d7f…` を選ぶのが最も単純。 |
| P3 | 採用 | remote 依存は生成・再発行だけに閉じ、既存 verify の `commit 実在 + HEAD ancestry` は維持する。remote ref がなければ生成は停止し、HEAD や local main へ自動 fallback しない。 |
| P4 | 採用 | known の [TOP_LEVEL_KEYS 検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:700) と measurement の [同検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:282) を変えず、別台帳にする。 |
| P5 | 要修正 | 最新 `new_sha256` と現行ファイルの一致だけでは旧側との対応を検査できない。旧 bytes の取得元 commit、旧 hash、実差分 pointer、2ファイル間依存まで検査する必要がある。 |
| P6 | 採用（条件付き） | 現行旧版を含む `e5dfa84…` は origin/main と HEAD の ancestor で、両 blob を取得できる。台帳からその commit の bytes を読み直すなら複製不要。ただし shallow clone や将来の公開履歴書換えでは検査を停止させる。 |
| P7 | 要修正 | S-1 の2ファイルは必ず同時処理する。ただし known の SHA を固定する v1 holdout への影響を別裁定にせず「全依存が整合する」とは言えない。 |
| P8 | 否認（現文のまま） | generator を変更すると自己 SHA が必ず変わるため、「差分は2フィールドだけ」と両立しない。差分契約を下記の pointer 集合へ改訂するなら採用可能。 |

### 必要な差分契約の訂正

generator を変えない純粋な再構成でも、実測上の差分は次になる。

| freeze | 必須または許容される差分 |
|---|---|
| known | `/frozen_at_head`、実行環境が異なる場合 `/python_version` |
| measurement | `/frozen_at_head`、`/implementation_hashes/known_axes_freeze/sha256`、実行環境が異なる場合 `/python_version` |

本 wave で両 generator に生成ガードを入れるなら、さらに次が必要になる。

| freeze | generator 変更に伴う追加差分 |
|---|---|
| known | `/generator/sha256` |
| measurement | `/generator/sha256` と `/implementation_hashes/s1_measurement_freeze/sha256`。両値は同一でなければならない。 |

これら以外の entries、sources、cells、comparisons、schedule、selection rules、ccbench pin 等は完全一致を要求する。

## file:line 粒度の実装プラン

### 単位A — anchor 規則、known、ペア再発行、台帳

所有ファイルは以下に限定する。

- `orchestrator/campaign/s1_known_axes_freeze.py`
- 新規 `orchestrator/campaign/s1_freeze_reissue.py`
- `orchestrator/tests/test_s1_known_axes_freeze.py`
- 新規 `orchestrator/tests/test_s1_freeze_reissue.py`
- `orchestrator/tests/test_frozen_artifacts.py`

1. [s1_known_axes_freeze.py:30-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:30) に既定 published ref `refs/remotes/origin/main` を定義する。

2. [s1_known_axes_freeze.py:89-96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:89) の直後に生成専用 helper を追加する。

   - ref を曖昧名ではなく `show-ref --verify` 相当で解決する。
   - 40桁 commit に正規化する。
   - `cat-file -e <sha>^{commit}` を要求する。
   - `merge-base --is-ancestor <sha> refs/remotes/origin/main` と `<sha> HEAD` の双方を要求する。
   - ref 不在、非 ancestor、Git エラーはいずれも `FreezeError`。
   - fetch は行わず、HEAD/local main への fallback もしない。

3. [s1_known_axes_freeze.py:747-754](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747) の既存 local ancestry 検査は意味を変えない。テスト可能な小 helper へ抽出しても、`verify_document()` が同じ2コマンドを必ず通る構造を維持する。

4. [s1_known_axes_freeze.py:769-782](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:769) は存在検査を最初に残し、その後で published anchor を解決し、`build_document(frozen_at_head=anchor)` を呼ぶ。`open("x")` も残す。単体 `generate()` に既存ファイルを置換する機能は持たせない。

5. 新規 `s1_freeze_reissue.py` を、概ね次の責務に分ける。

   - `:1-80`: path、schema、SHA/40hex、許容 JSON Pointer 集合。
   - `:81-160`: duplicate key を拒否する JSON loader、単一 read bytes、SHA計算、RFC 6901形式の leaf diff。
   - `:161-280`: 台帳の exact schema、世代連続性、旧 Git blob、最新現物、2ファイル間整合の検査。
   - `:281-400`: ペア専用 `reissue()`。
   - `:401-end`: `reissue` / `verify-ledger` CLI。

6. `reissue()` は次の順で処理する。

   1. canonical 2ファイルを一度ずつ読み、SHAと bytes を保持する。
   2. 両旧 bytes を含む `predecessor_commit` を特定し、`git show <commit>:<path>` と byte 一致を要求する。今回は `e5dfa84…` が該当する。
   3. published anchor を一度だけ解決する。
   4. known candidate をメモリ構築し、空の staging pathへ exclusive createする。
   5. staged known を通常の `known.verify()` で検査する。
   6. staged known を入力に measurement candidate を構築する。
   7. resolver で staged known を指して通常の `measurement.verify()` を通す。
   8. 旧→新の実差分 pointer が許容集合の部分集合で、必須 pointer が存在することを検査する。
   9. 台帳の次 entry を構築し、staged 3ファイルに対して台帳 verifier を通す。
   10. canonical 旧 bytes が開始時から変わっていないことを再確認してから置換する。

   filesystem 上の3ファイル同時 renameはできないため、正式な同時性は「全 candidate を先に検査し、2 freeze と台帳を同じ Git commit に入れる」ことで定義する。途中失敗時は commit せず、旧 bytes は `predecessor_commit` から回収可能とする。

7. 台帳は `output/s1-freeze/reissue_ledger.json` とし、exact schema を次とする。

```json
{
  "schema_version": "s1-freeze-reissue-ledger/v1",
  "entries": [
    {
      "generation": 1,
      "reason_code": "dangling-frozen-at-head",
      "predecessor_commit": "<40hex>",
      "anchor": {
        "published_ref": "refs/remotes/origin/main",
        "published_tip": "<40hex>",
        "selected_commit": "<40hex>"
      },
      "files": {
        "known_axes": {
          "path": "output/s1-freeze/known_axes_freeze.json",
          "old_sha256": "<64hex>",
          "new_sha256": "<64hex>",
          "old_frozen_at_head": "<40hex>",
          "new_frozen_at_head": "<40hex>",
          "changed_json_pointers": ["..."]
        },
        "measurement": {
          "path": "output/s1-freeze/measurement_freeze.json",
          "old_sha256": "<64hex>",
          "new_sha256": "<64hex>",
          "old_frozen_at_head": "<40hex>",
          "new_frozen_at_head": "<40hex>",
          "changed_json_pointers": ["..."]
        }
      }
    }
  ]
}
```

8. 台帳 verifier は少なくとも以下を要求する。

   - generation が1始まりの連番。
   - entry N の `old_sha256` が N-1 の `new_sha256` と一致。
   - 初回旧 bytes は `predecessor_commit:path` から取得し、`old_sha256` と一致。
   - 最新 `new_sha256` は canonical 現物と一致。
   - 記録した `changed_json_pointers` が実 diff と完全一致し、許容集合外がない。
   - 両 freeze の新 anchor が同じ。
   - measurement の known hash が new known bytes の SHA と一致。
   - 通常の両 verifier が成功する。
   - remote ref の現況は再検証しない。remote 判定は発行時だけとする。

9. [test_s1_known_axes_freeze.py:58-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:58) は、例外だけでなく既存 sentinel bytes が不変であることと、事前存在検査時に builder/anchor resolver が呼ばれないことまで確認する。

10. 同テストの [one-byte test 前後](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:66) に以下を追加する。

   - checked-in known freeze を fixture 化せず直接 `M.verify(M.FREEZE_PATH)` する正例。
   - 実在するが HEAD と分岐した commit を tmp Git repo に作り、local ancestry helper が拒否するテスト。
   - remote main の子である未公開 HEAD を published guard が拒否するテスト。
   - remote ref 不在を停止させ、出力を作らないテスト。

   `_run()` は [tmp_path だけを注入する契約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:151) なので、`monkeypatch` fixture は追加せず `unittest.mock` または手動 save/restore を使う。

11. 新規 `test_s1_freeze_reissue.py` は synthetic old/new pair と tmp Git repo を使い、schema、Git旧blob、pointer差分、hash連鎖、pair依存を検査する。加えて canonical ledger と実ファイルを直接読む integration test を置く。現行 SHA literal は置かない。

12. [test_frozen_artifacts.py:25-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:25) から S-1 の2 literal hash を外し、残る6件の静的 manifest と、S-1 ledger verifier の2系統へ分ける。[shape test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:75) も6件へ直す。単に新 SHA を貼り直す変更にはしない。

### 単位B — measurement の同型適用

所有ファイルは以下だけとする。

- `orchestrator/campaign/s1_measurement_freeze.py`
- `orchestrator/tests/test_s1_measurement_freeze.py`

1. [s1_measurement_freeze.py:447-470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:447) で、既存拒否を最初に維持したまま、単位Aの published-anchor helper を呼び、[build_document()](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:240) に明示 anchor を渡す。

2. [verify_document:387-445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:387) は remote 非依存のままにする。known の通常検査、implementation hashes、own ancestry、再構成 equality のいずれも外さない。

3. [test_s1_measurement_freeze.py:185-189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:185) を sentinel bytes 不変まで強化する。

4. 同テストに以下を追加する。

   - published resolver の失敗時に output が作られない。
   - staged known を入力に生成すると、`implementation_hashes.known_axes_freeze.sha256` が staged bytes と一致する。
   - checked-in measurement freeze を fixture/mockingなしで直接 verify する正例。
   - known→measurement の順序を逆にした candidate は hash 不一致で拒否される。

### 単位間依存と順序

ファイル所有は素集合になる。ただし単位Bは単位Aが追加する published-anchor helper の署名に依存する。

- 実装は、署名を先に固定すれば並行可能。
- 統合順は A → B。
- ペア再発行は両単位のコード bytes が最終化した後にだけ行う。
- review/fix でどちらかの generator が1 byteでも変わった場合、freeze と台帳を再生成してから受入へ進む。
- 実装子はコード・テストだけを変更し、実 JSON、台帳データ、docs、commit は親が担当する。

### 再発行と親受入の順序

1. コードとテストを確定する。
2. `origin/main` の存在と期待 tip、HEAD ancestry を確認する。
3. `reissue` を一度実行し、known → measurement → ledger の順で staging 検査する。
4. pointer diff を人間も確認し、許容外が1件でもあれば commitせず停止する。
5. canonical known、measurement、ledger を同じ commit に載せる。
6. 通常 verify 2本、`verify-ledger`、対象テスト、`test_frozen_artifacts.py`、関連 oracle tests、全走、リポジトリ所定 checker を親が実測する。
7. commit 後の provenance 検査も親が行う。

remote ref のない clone/CI では `generate` / `reissue` は停止する。一方、通常 verify は remote を要求しない。ledger の旧 blob 検査には履歴が必要なので、shallow clone で `predecessor_commit` がなければ skip せず停止し、当該 job を full-history checkout にする。

## 事前登録変異 M1〜M5

| 変異 | テストと kill 判定 |
|---|---|
| M1 | 記載どおり「merge-base だけ成功化して死んだ SHA を受理」は成立しない。`cat-file -e` が先に拒否するためである。M1を「実在する非ancestor commitの merge-base 拒否を除去」に訂正する。[known:750-754](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:750) に対応する tmp Git test で、baseline は拒否、mutant は helper が正常復帰するため `pytest.raises` が失敗する。 |
| M2 | `test_s1_known_axes_freeze.py` の新 published test で、remote main の未公開子 HEAD を candidate にする。baseline は出力前に拒否、guard 無効化 mutant は生成を許す。例外文ではなく「ファイルが生成された」という受理域拡大で kill。remote-ref 不在も別テストで固定する。 |
| M3 | 新 `test_s1_freeze_reissue.py` で最新 freeze の JSON 意味を変えず bytes だけ変え、ledger は据え置く。baseline は `new_sha256` 不一致で拒否、照合除去 mutant は受理する。 |
| M4 | 元の定義は無効。事前存在検査 [known:770-773](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:770) だけを消しても `open("x")` が残り、受理集合は変わらない。M4′を「事前検査と exclusive create の双方を無効化し上書きを許す」に改訂する。[既存テスト:58-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:58) の sentinel bytes 不変 assertion が、mutant の置換成功で失敗する。事前検査だけの削除は kill 数に含めない。 |
| M5 | [source hash 検査:731-741](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:731) と [既存負例:77-88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:77) を対応づける。再発行後の正例が先に通ることを前提に、別 resolver の変更済み source を baseline は拒否、検査除去 mutant は最後まで受理する。現在の死んだ anchor による別理由の拒否を kill と数えない。 |

## fixture への現行 hash 差し込みを構造的に避ける手当て

- canonical 正例は実ファイルに対して公開 `verify()` を直接呼び、`build_document` を monkeypatch しない。
- テスト内に generator SHA、known SHA、measurement SHA の current literal を置かない。
- 最新 SHA は ledger のデータとして一度だけ記録し、テストは現物 bytes から独立に再計算する。
- 旧 SHA は `predecessor_commit:path` の Git bytes から再計算する。
- `test_frozen_artifacts.py` の S-1 literal pin は ledger 検査へ置き換え、単なる期待値更新を不要にする。
- negative test は「期待値も一緒に更新」せず、bytes、台帳、Git旧blobのいずれか一方だけを変える。

## 未解決の設計択一

1. **差分契約の改訂が必要。**  
   推奨は、上記 JSON Pointer 集合を許容し、それ以外を完全一致とする案。従来の「2フィールドだけ」を維持する場合、measurement の known hash 更新すらできず、再発行は不可能である。

2. **v1 holdout freeze の旧 known SHA をどう扱うか。**  
   推奨は、T-005 を S-1 内の再発行として完了させる一方、「公式 oracle 全体が復旧する」とは扱わず、v1 holdout の世代移行を別のユーザー裁定へ送る案。既存 holdout verifier の source 完全一致を緩めて台帳上の後継を通す案は採用不可。今回の完了条件に oracle 全体の成功を含めるなら、S8b 世代移行まで scope を拡張する裁定が先に要る。

3. **Git 履歴への依存を許容するか。**  
   推奨は P6 のまま、`e5dfa84…` が公開 main に含まれることを前提とし、object 不在の clone は停止させる案。shallow CI でも通す必要があるなら、旧 bytes の別保管を認める追加裁定が必要になる。
---

## 段 3-A: 敵対相談 — 正しさ境界レンズ (codex gpt-5.6-sol / max / read-only、逐語)

結論は **NO-GO**。現行 scope のまま canonical artifact を再発行してはいけない。pytest は実行していない。以下はコード読解と read-only の Git object/ref 検査による判定である。

特に問われた3点への回答は次のとおり。

1. **[T-005] は現 scope では完了不能。** S-1 だけ直すと v1 holdout の source binding を壊し、holdout も直すと S8b の v1 trust root・v2 transition・承認連鎖まで変更が必要になる。先に scope 拡大のユーザー裁定を取るべきであり、実装子が黙って広げてはいけない。
2. **holdout の標本選択自体は決定論的だが、freeze 全体の再生成は純粋な provenance 追随ではない。** H1/H2 と nearest-ratio binding は定数・known entries から決まる。しかし検索 snapshot は tracked/untracked を含む全 worktree、確認者、日時、HEAD に依存する。
3. **現状維持も悪いが、S-1 だけの部分再発行はさらに悪い。** 現状は fail-closed で故障が露出している。部分再発行は S-1 を局所的に緑化しながら downstream trust root を不整合にし、しかも plan はその不整合を検出していた literal pin を外す。

## 所見

1. **real / 致命 / 対象:** [holdout_freeze.json:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:9)、[s8b_holdout_freeze.py:641](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:641)、[s8b_ratified_freeze.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:60)、[同:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:110)

   **壊れ方:** known freeze が1 byte変わると、holdout の記録済み SHA と worktree SHA が不一致になり、v1 verifier は必ず拒否する。holdout 自身も再生成すると、その bytes は `V1_FREEZE_SHA256` と不一致になり、legacy loader と g1 の `supersedes_sha256` 起点が壊れる。さらに `_TRANSITION_V1_TO_G1` は `/known_axes_freeze/sha256` の変更を許可していないため、既存 v2 世代経路でも追随不能である。

   **推奨対処:** S-1、v1 holdout、`V1_FREEZE_SHA256`、v2 transition、approval/active pointer、manifest/protocol binding を一つの裁定対象にする。裁定前は canonical 2 freeze を変更しない。

2. **real / 高 / 対象:** [s8b_holdout_freeze.py:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:197)、[同:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:297)、[同:507](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:507)

   **壊れ方:** 空の untracked `notes.txt` を1個置くだけでも列挙対象が増え、`search.file_count` が変わる。軸文字列を含めば per-axis count、positive control、場合によっては conjunction 判定も変わる。新規 reissue script・test・ledger 自身も `output/s8b-freeze/` 外なので検索対象になる。さらに `confirmed_by`、`confirmed_at`、`frozen_at_head` も再生成入力である。したがって holdout 全体の再生成は「known bytes の hash だけを追随」ではない。

   H1/H2 は定数、variant binding は known の entries から導かれるため、許容された S-1 差分だけなら標本と binding は変わらない。だがそれだけでは freeze 全体の同一性を意味しない。

   **推奨対処:** full `generate()` を使わない。既存標本を保つ provenance-only transition を別途裁定し、許容 pointer を厳密に定める。過去検索 snapshot を再生成するなら、当時の完全なファイル集合が保存されていないため同一再構成とは主張しない。

3. **real / 高 / 対象:** [s1_known_axes_freeze.py:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:608)、[同:718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:718)、[s1_measurement_freeze.py:240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:240)、[同:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:387)

   **壊れ方:** generator を編集した後、push 前の `origin/main` を anchor にすると、freeze は新しい generator SHA を記録する一方、`git show <anchor>:<generator-path>` は旧 bytes を返す。それでも verifier は worktree の generator hash と HEAD ancestry を別々に見るだけなので通る。measurement の新 known freeze bytes も同じ anchor commit には存在しない。

   つまり `frozen_at_head` は source closure を復元できない。「provenance anchor の貼り替え」という P1 は虚偽になる。

   **推奨対処:** anchor commit の blob と全 source hash を照合する。少なくともコード commitを人間が pushした後に発行する二段階手順が必要。remote 非依存 verify は、local object の `git show <anchor>:<path>` を照合すれば維持できる。

4. **real / 高 / 対象:** [s1_known_axes_freeze.py:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:89)、[同:747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747)、[同:769](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:769)

   **壊れ方:** `show-ref` はローカル remote-tracking ref の観測であり、publication の証明ではない。`origin/main` tip を解決して、その SHA が `origin/main` の ancestor か確認する検査は通常は自己比較で恒真である。

   また `build_document(frozen_at_head=HEAD)` で作った文書は、HEAD が未公開 branch commit でも通常 verifier を通る。generate 側だけの guard は受理不変条件ではない。

   各環境の帰結は以下になる。

   | 状態 | 帰結 |
   |---|---|
   | `origin/main` 不在、remote 名が別 | generate/reissue は誤って fail-closed |
   | shallow clone | anchor/predecessor object が無ければ fail-closed |
   | detached HEAD | ref と ancestry が揃えば動く |
   | stale `origin/main` | 古い tip を「published」と誤認して受理 |
   | locally forged remote-tracking ref | 未公開 commit を受理する fail-open |
   | push 前 | anchor に新 generator/source がない |
   | force-push 後 |現在の clone は object 残存で通り、新規 clone は object 不在で落ちうる |

   **推奨対処:** 「published」を「最後にローカルで観測した remote-tracking commit」へ格下げするか、発行時に server ref/immutable tag と結び付ける。verify が published を保証するとは書かない。

5. **real / 致命 / 対象:** [test_frozen_artifacts.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:25)、[s8b_ratified_freeze.py:1185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1185)、[s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)

   **壊れ方:** plan の ledger は末尾 entry を事実上の active generation とし、同じ producer が freeze と `new_sha256` の両方を書く。独立した approval、active pointer、固定 pin がない。S-1 literal pin を削除すると、「壊れた artifact と、それに合わせて更新された ledger」の組を拒否する第三の値が消える。

   例として `/python_version` を truthy な object に変えても、現 verifier は記録値を `build_document()` に戻して echo するため受理する。ledger 側でも許容 pointer 内なので通る。`reason_code="dangling-frozen-at-head"` も、旧 anchor が本当に dangling かを検査する仕様がなく、恒真な説明欄になる。

   **推奨対処:** provenance ledger と発効判定を分離する。ledger を literal pin の代替にしない。再利用可能な世代機構にするなら、S8b と同様に generation、外部 approval、明示 active pointer を分離する。一回限りなら exact old hashes を固定し、generation 2 を拒否する one-shot migrator にする。

6. **real / 高 / 対象:** [s1_known_axes_freeze.py:769](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:769)、[s1_measurement_freeze.py:447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:447)

   **壊れ方:** 現行 `generate()` は事前存在検査と `"x"` の二層で上書きを拒否する。新 `reissue()` は既存 canonical を置換する恒久的な裏口になる。開始時 bytes を再確認しても、その後の rename までに別 writer が変更すれば上書きできる。1個目の rename 後に ENOSPC・権限エラー・process crash が起きれば、known=new、measurement=old、ledger=old/不在という混成状態が残る。「同じ Git commit に入れる」は worktree の部分更新を回復しない。

   **推奨対処:** canonical を直接置換せず versioned candidate を出すか、repo-scoped lock、expected-old hash、durable backup/journal、各 rename 後の fault-injection recovery testを要求する。将来の再発行には別 approval が必要で、今回の承認を恒久 CLI の承認に流用しない。

7. **real / 高 / 対象:** [s1_known_axes_freeze.py:785](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:785)、[s8b_oracle_driver.py:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249)

   **壊れ方:** 通常 `verify()` も公式 oracle も ledger verifier を呼ばない。ledger を欠落・改変した S-1 freeze でも、文書単体が自己整合すれば runtime gate は ledger なしで受理する。機械検査は `test_frozen_artifacts.py` または専用 CLI を忘れず実行するという運用規律にしかならない。

   **推奨対処:** correspondence を correctness condition とするなら、唯一の `verify_s1_pair()` に ledger を組み込み全 consumer をそこへ収束させる。CI-only audit に留めるなら、その限定を明記して correctness gate と呼ばない。

8. **real / 中 / 対象:** [test_s1_known_axes_freeze.py:58](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:58)、[s1_known_axes_freeze.py:770](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:770)

   **壊れ方:** published guard の負例しかなく、resolver が常に例外を投げても全負例を満たす。M2 の「未公開 HEAD を candidate」にする試験も、実装 helper が常に `origin/main` tip を選ぶ設計とは噛み合わない。

   M4′は二層を同時に無効化する複合変異であり、exclusive-create 単独の歯を証明しない。事前検査の直後に anchor resolver が sentinel file を作る race を入れれば、`"x"` を `"w"` にする単独変異を検出できるが、その試験がない。

   **推奨対処:** published tip を受理して実ファイルを作る正例を追加する。M4は「既存時の早期拒否」と「check後競合の exclusive-create拒否」を別々に試験する。

9. **real / 中 / 対象:** [test_s1_measurement_freeze.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:91)、[同:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:98)、[同:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:113)

   **壊れ方:** 既存 fixture は production known generator の**現行 hashを動的に注入**し、さらに `K.build_document` を fixture document の echo に置換している。「current literal を置かない」は D68 (7) の再発防止になっていない。generator が変わっても、この fixture 系の measurement 負例はその変化を吸収する。

   予定された canonical direct verify は full suite では補償になるが、構造的に不可能にはしておらず、単位Bだけの実行では同じ隠蔽が残る。

   **推奨対処:** production generator path/hash を fixture から除去する。measurement 単体試験では `_verify_known_axes` を明示的な synthetic seam として隔離し、production integrity は fixtureなしの別テストだけに担わせる。

10. **real / 高 / 対象:** [holdout_freeze.json:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:4)、[同:622](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:622)、[s8b_holdout_freeze.py:665](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:665)、[s8b_oracle_driver.py:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216)

   **壊れ方:** F17 の「現在は known、再発行後は holdout」という二状態モデルは誤り。現行 holdout 自身の `frozen_at_head=2e20d441…` も Git object 不在であり、v1 verifier は現在すでに `holdout-freeze-verify` を拒否する。さらに `floor` と `budget` は null なので、oracle は別途必ず refusal を積む。

   **推奨対処:** 完了条件を「拒否理由を一個移すこと」ではなく、全 refusal の依存閉包で定義する。S-1だけの部分再発行は landing しない。

## refuted とした攻撃点

- **M1 の訂正は妥当。** 死んだ SHA は [s1_known_axes_freeze.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:751) の `cat-file` で先に拒否されるため、merge-base 単独変異には実在する非ancestor commitが必要。
- **M3 の bytes-only 変異は単独検査として成立する。** JSON意味を変えず whitespaceだけ変えれば通常 verifier は同じ document を見るため、最新 bytes hash 照合の除去を切り分けられる。
- **remote 呼出しの call-graph 漏れ自体は refuted。** planどおり helperを `generate()` だけから呼べば、現行 known/measurement verifier に remote依存は入らない。問題は「published」という新不変条件を verifier が保証しない点である。

## 旧 freeze の復元可能性

現時点では次の操作で復元できる。

```text
git show e5dfa84c6e71824e2312af99b97d60dde11eca20:output/s1-freeze/known_axes_freeze.json | sha256sum
git show e5dfa84c6e71824e2312af99b97d60dde11eca20:output/s1-freeze/measurement_freeze.json | sha256sum
```

read-only 照合では、それぞれ現行旧 hash `354f4b…` / `203de3…` と一致した。ただしこれは `e5dfa84…` object が存在する現在の full history に限る。shallow clone、history rewrite、force-push後のGCでは復元不能になりうる。P6 の「git履歴が保持する」は永続保証ではない。

## brief の誤り

F1〜F8では次が誤りまたは過大である。

- **F1:** current known単体に限定すれば refuteなし。ただし「破損は1点のみ」を repository closureへ一般化するのは誤り。holdout自身にも死んだ headがあり、measurement/holdoutの参照hashも変わる。
- **F5:** canonical CLI の正規経路に限定すれば正しい。「経路はそれしかない」は `build_document()`、任意 `output_path`、直接書込みを含めると過大。
- **F7:** ancestry拒否のoracle伝播は正しいが、現行 holdout verifierとfloor/budgetの先行・併存 refusalを落としている。
- **F8:** ref値は一致したが、fetchしていない local remote-tracking refを無条件に「published」と呼ぶのは未証明。
- **F2、F3、F4、F6:** 本監査では refuteなし。ただしF6から「2 freezeの差分は各2 fieldだけ」は導けない。

追補では以下が誤りである。

- **F11:** v1 verifier がv2 fieldを拒否する事実は正しいが、「世代連鎖はrepo全体で未裁定・無効」という推論は誤り。[s8b_ratified_freeze.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1) 以降に generation、approval、active pointer、transition、source semantics が実装されている。v1経路の拒否は型誤流入への defense-in-depth である。
- **F17:** 現在すでに holdout own-head、known、floor-null、budget-null の複数拒否がある。

P1〜P8の判定は次のとおり。

- **P1: 否認。** 変更はanchorだけでなく、依存hash・自己hash・downstream trust rootに及ぶ。
- **P2: 否認。** local `origin/main` はpublication証明でも immutable anchorでもなく、plan順序では新sourceを含まない。
- **P3: 要修正。** remote非依存 verify は維持できるが、published invariantを保証するとは言えない。
- **P4/P4′: 要修正。** freeze外に置くこと自体は可能。しかしlatest ledgerをliteral pinの代替にした時点で純粋な記録ではなく、未承認のactive-generation機構になる。
- **P5: 否認。** latest hash一致だけでは不足。planの追加検査でも、同一producerによるartifact+ledger同時更新とallowed fieldの誤値は防げない。
- **P6: 条件付き。** 現在の `e5dfa84…` からは復元可能だが、shallow/history rewriteには耐えない。brief元案の「content hashとold head」だけでは取得commitも特定できない。
- **P7: 必要だが不十分。** known→measurement順は必要。依存閉包はholdoutとS8b trust rootまで続く。
- **P8: 否認。** 自己hash差分契約と衝突し、push前anchorは変更後generatorを含まない。「実演」はpublished guardの正しさを証明しない。
---

## 段 3-B: 敵対相談 — 整合・実効性レンズ (codex gpt-5.6-sol / max / read-only、逐語)

# 判定: NO-GO

pytest は実行していない。以下はコード・Git object/ref・成果物 bytes の静的検査結果。

問いへの結論は次のとおり。

1. **[T-005] は、S-1 二成果物だけなら機械生成できるが、整合した実装 wave としては現 scope で完了不能。** 差分契約の変更と、S8b legacy holdout を歴史成果物として残すのか追随させるのかについて、canonical 書換え前にユーザー裁定が要る。
2. **holdout の H1/H2 選択自体は決定論的。holdout JSON 全体の再生成は決定論的な provenance 追随ではない。** repository 全走査・未追跡ファイル・再承認値が成果物に入るうえ、v1 は immutable trust root、v2 は known hash の変更を許していない。
3. **現状維持と S-1 だけの再発行なら、後者が局所的にはまし。** 現在は S-1 二本だけでなく holdout v1 も既に dangling head で verify 不能。S-1 再発行は二本を直すが、oracle は復旧しない。holdout v1 まで上書きする案は trust root を差し替えるため、現状維持より悪い。

## 所見

### 1 / 致命 / real

対象: `orchestrator/campaign/s1_measurement_freeze.py:252-258,263-266`、`orchestrator/campaign/s1_known_axes_freeze.py:632-637`

壊れ方: known の `frozen_at_head` を変えるだけで known ファイル bytes が変わり、measurement の `/implementation_hashes/known_axes_freeze/sha256` も必ず変わる。さらに両 generator を変更すれば自己 hash も変わる。brief の「差分は `frozen_at_head` と `python_version` のみ」を守れば再発行不能、プランの pointer 集合を採れば brief の即 reject 条件違反になる。

推奨対処: 「未解決の設計択一」のまま実装へ進めず、許容 pointer の exact 集合をユーザー裁定で先に確定する。

### 2 / 高 / real

対象: `output/s8b-freeze/holdout_freeze.json:4`、`orchestrator/campaign/s8b_holdout_freeze.py:665-680,709-712`、`orchestrator/campaign/s8b_ratified_freeze.py:20-23`

壊れ方: holdout v1 の `frozen_at_head=2e20d441…` は既に存在しない。legacy verifier は known hash 照合後に `_verify_head()` を呼ぶため、**S-1 再発行前から** `holdout-freeze-verify` が失敗する。F17 の「現状は known、再発行後は holdout」という状態遷移は成立しない。現状から既に両方が拒否理由になり得る。

推奨対処: 現在と再発行後の refusal 集合を exact に記録し、「拒否理由が移る」説明を撤回する。

### 3 / 致命 / real

対象: `orchestrator/campaign/s8b_ratified_freeze.py:60-62,114-128,988-1008,1329-1347`、`orchestrator/tests/test_s8b_protocol_builder.py:46-62`

壊れ方:

- holdout v1 を残すと、新 known bytes と `known_axes_freeze.sha256` が不一致。
- holdout v1 を上書きすると `V1_FREEZE_SHA256` と protocol golden が不一致になり、immutable trust root を再定義する。
- v2 g1 で追随しようとしても、v1→g1 の許容 pointer に `/known_axes_freeze/sha256` がなく transition verifier が拒否する。

既存の sanctioned path は三方すべて塞がっている。

推奨対処: canonical S-1 書換え前に、次のどちらかを裁定する。

- legacy holdout は歴史成果物として旧 known bytes を参照し続け、oracle 非復旧を明記する。
- S8b trust-root／transition／protocol golden まで含む別 wave に scope を拡張する。

### 4 / 高 / real

対象: `orchestrator/campaign/s8b_holdout_freeze.py:51-85,197-212,232-233,435-497,507-567,581-584`

壊れ方: H1/H2 と anchor workload は定数・最近傍規則なので、known の `entries` が同一なら不変。一方、生成は tracked と untracked の全ファイルを走査する。新しい `output/s1-freeze/reissue_ledger.json` だけでも `file_count` が増え、他 worktree の未追跡ファイルによって per-axis counts や positive-control snapshot も変わる。holdout tuple を含む未追跡ファイルがあれば生成自体が停止する。再生成には再承認値も必要。

推奨対処: holdout 追随案を採るなら、clean な特定 commit の tracked treeだけを入力にし、H1/H2、variant binding、未知性結果の diff 契約と再承認を別途定める。

### 5 / 高 / real

対象: 新規予定 `orchestrator/campaign/s1_freeze_reissue.py:281-400`、`orchestrator/campaign/s1_measurement_freeze.py:400-408`

壊れ方: known→measurement→ledger の canonical rename は三ファイル transaction ではない。known を置換した直後に process kill すると、measurement は旧 known SHA を保持して拒否される。再実行時には「現在の known 新 bytes + measurement 旧 bytes」を同時に含む predecessor commit がないため、計画した predecessor 探索も停止する。Git commit の原子性は、その前の壊れた worktree を回復しない。

推奨対処: reissue CLI は canonical を直接置換せず、別 temporary worktree／temporary index に候補を出して commit tree を構成する。少なくとも排他 lock、耐久 journal、例外時 rollback、directory fsync、crash-resume 規則が必要。

### 6 / 高 / real

対象: `output/s1-freeze/known_axes_freeze.json:107,220,623,653`、`orchestrator/campaign/s1_known_axes_freeze.py:99-106,729-741`

壊れ方: freeze には63 source record、31 unique path がある。例えば parent が再発行後に `docs/phase3-main-experiment.md` を1文字更新すると、known verify は source SHA 不一致、measurement は known 連鎖失敗、ledger verifier も通常 verifier 失敗になる。プランは「docs は親」とするだけで、docs を再発行前に確定する順序を持たない。

推奨対処: 31 path を明示した source snapshot を取り、コード・docs・phase/worklog 更新を完了してから最後に再発行する。commit 前にも同じ31 hashを再照合する。

### 7 / 高 / real

対象: `orchestrator/campaign/s1_measurement_freeze.py:24-25`、`orchestrator/tests/conftest.py:70-95`、`orchestrator/tests/test_real_repo_serialization.py:47-63`

壊れ方: B は A の published helper に依存し、A の reissue integration は B の最終 generator bytes に依存する。これは相互依存であり、A/Bを独立完了できない。また新しい canonical verify tests は実 ccbench source を読むが、xdist 排他の正本と独立 golden に新 node を追加する所有がどちらにもない。共有 submodule を patch する別テストと競合すれば source SHA が一時的に変わる。

推奨対処: `common helper → known/measurement → pair reissue integration` の三段へ直列化する。所有へ `conftest.py` と `test_real_repo_serialization.py` を加える。

### 8 / 高 / real

対象: `orchestrator/tests/test_s1_known_axes_freeze.py:26-40,156-183`、`orchestrator/tests/README.md:34-49,92-113`、`tools/run_tests.py:433-442`

壊れ方:

- submodule 未 init では既存生成テストは SKIP。
- pytest も素 runner も skip のみなら exit 0。skip と PASS の差は表示・sidecarには残るが、終了コード境界で失われる。
- 新規 `test_s1_freeze_reissue.py` に `__main__` harnessもallowlist追加もなければ、`python3 file.py` は0件・exit 0。
- ledger verifierが通常 verifyを呼ぶなら、未 init submoduleでは逆に hard failure。プランはどちらの契約にするか決めていない。
- shallow cloneでは predecessor object 不在で停止するが、full-history checkoutを強制するCI設定は成果物にない。

推奨対処: acceptance jobを「full history + submodule init必須」にし、対象 node の skipped=0 を終了条件にする。新規テストには自走 harnessを必須化する。

### 9 / 高 / real

対象: `orchestrator/tests/test_s8b_oracle_driver.py:503-507,519-527,1345-1371`、`orchestrator/campaign/s8b_oracle_driver.py:216-266`

壊れ方: related oracle tests は「floor-nullがある」「budget-nullがある」「status=refused」「rc=2」しか要求しない。known 再発行後に holdout source mismatch が追加されても、これらの assertion はすべて満たされる。全走が赤くならなくても、oracle 整合の証拠にはならない。

推奨対処: real v1 gateについて、少なくとも `holdout-freeze-verify` と `known-axes-freeze-verify` の有無を exact に検査する。floor/budget拒否とは別テストへ分離する。

### 10 / 高 / real

対象: `orchestrator/tests/test_frozen_artifacts.py:25-39,61-81`、新規予定 `s1_freeze_reissue.py:161-280`

壊れ方: S-1 literal pin 2本を削除し、producerが同時生成する ledger の最新 hash と現物を比較するだけでは、ledgerが自分で次世代を承認する。将来、許容 pointer 内でartifactとledgerを同時更新すれば、外部の承認 pinなしで検査を通せる。これは一回限りの対応記録ではなく、事実上の appendable supersedes chainである。

この台帳が答えられる質問:

- known／measurement の old・new SHA
- old／new `frozen_at_head`
- JSON Pointer差分
- stated predecessor commit
- stated selected anchor
- latest bytesとの一致

答えられない質問:

- 誰がいつこの transition を承認したか
- new bytesを導入した commit はどれか
- `published_tip` が発行時に本当にremoteへ存在したか
- holdout等の全 downstream consumer が移行済みか
- shallow／履歴書換え後に旧bytesをどこから取得するか
- 中間世代のnew bytesを将来どう復元するか

推奨対処: 一回限りの immutable receipt とし、new S-1 2 hashおよびreceipt hashを `FROZEN_MANIFEST` に再pinする。将来のappendable ledgerを作るなら別裁定に回す。

### 11 / 中 / real

対象: `orchestrator/campaign/s1_known_axes_freeze.py:632-637`、`orchestrator/campaign/s8b_ratified_freeze.py:919-932`

壊れ方: generator変更後・commit前に `origin/main` を anchorにすると、`frozen_at_head` は新generator bytesを含まないcommitを指す。これは provenance anchorではなく「消えにくい到達可能commit」にすぎない。local `refs/remotes/origin/main` はfetchしていないため、`published` も証明しない。

推奨対処: 名称を reachability anchorへ格下げする。provenanceを主張するなら、S8b v2のようにgeneration導入commitと親commitの関係を記録・検査する。

### 12 / 低 / refuted — M1

対象: `orchestrator/campaign/s1_known_axes_freeze.py:750-754`

壊れ方: 元の「死んだSHAでmerge-baseだけ無効化」は `cat-file -e` に先に拒否されるため無効。プランの「実在する非ancestor commit」に差し替える修正なら、拒否理由はmerge-base一つにできる。

推奨対処: revised M1を採る。ただし published helper追加後は `merge-base --is-ancestor` が複数箇所になるため、変異ハーネスはexact multi-line targetが1件であることを確認する。

### 13 / 高 / real — M2

対象: 新規予定 helper `s1_known_axes_freeze.py:89-120`、`generate():769-782`

壊れ方: remote main の未公開子がHEADでも、baseline generatorはHEADをcandidateにせず、`origin/main` tip自身を選ぶ。そのanchorはremote mainとHEADの双方のancestorなので、baselineは拒否してはならない。計画した「baseline拒否、mutant生成」は逆である。

推奨対処: selectorを `origin/main → HEAD` に変える変異とし、両方が生成する前提で、出力の `frozen_at_head` がpublished tipかを検査する。候補拒否を試すならcandidate引数を正式APIにする。

### 14 / 中 / real — M3

対象: `orchestrator/campaign/s1_measurement_freeze.py:400-408`

壊れ方: 「latest freezeのbytesだけ変更」が known を指す場合、ledger hash不一致に加えてmeasurementのknown hash不一致でも拒否される。M3を外しても赤いままで帰属不成立。measurement JSONへの末尾空白なら、意味は不変で下流byte hashもなく単一理由にできる。

推奨対処: mutation inputを「measurement bytesへの空白追加」と一意に固定する。

### 15 / 中 / real — M4

対象: `orchestrator/campaign/s1_known_axes_freeze.py:769-781`、`orchestrator/tests/test_s1_known_axes_freeze.py:58-64`

壊れ方: 強化予定テストが「例外」「sentinel不変」「builder未呼出し」「resolver未呼出し」を同時に検査すると、事前検査だけを消した等価変異でもbuilder呼出し assertionが赤くなる。一方、両層除去M4′では複数 assertionが同時に赤くなり、単一理由のkillerではない。

推奨対処: kill判定はsentinel overwriteだけの専用テストにする。未呼出し検査は回帰pinとして別扱いし、単層変異の赤をkillに数えない。

### 16 / 高 / real — M5

対象: `orchestrator/campaign/s1_known_axes_freeze.py:721-741`、`orchestrator/tests/test_s1_known_axes_freeze.py:77-88`

壊れ方: M5をsource fileへ適用すると、その変異自体がgenerator SHAを変える。canonical freezeを読む既存負例はsource検査へ到達する前に `generator sha256 不一致` で拒否される。source照合を外しても赤いままなのでkill帰属は成立しない。

推奨対処: mutantごとにそのmutant自身からfresh documentを構築するか、source検査をself-hashの外の純粋helperへ抽出して変異する。canonical positive testを同じkillerに使わない。

### 17 / 低 / refuted

対象: `orchestrator/campaign/s1_measurement_freeze.py:249-258,407-408`

壊れ方: S-1二本だけを見る限り、依存は known→measurement の片方向であり循環していない。コード確定→known candidate→measurement candidateの順なら、staging resolverを正しく渡す限り中間verifyのデッドロックはない。generator hashにも自己参照循環はない。

推奨対処: この順序は維持する。ただしcanonical逐次置換のcrash問題とholdout依存は別途解消する。

## brief の誤り

### F1〜F8

- **F8:** SHA値はlocal refとして確認できるが、`origin/main`を「published」と断定する根拠はない。fetchもremote照合もしていない。
- **F7:** ancestry失敗がoracle refusalへ伝播する点は正しいが、原因の全体像として不十分。holdout v1自身のdangling headとfloor/budget nullが独立に拒否する。
- **F1:** knownの現行snapshotに限定すれば反証しない。ただしこれを「wave後もanchorだけの貼替え」とP1/P8へ延長するのは誤り。

F2〜F6には静的な直接反証なし。

### 追補

- **F11:** 誤り。S8b v2の承認束縛・active pointer・supersedes連鎖は既に `s8b_ratified_freeze.py` に実装済み。legacy verifierがgeneration fieldを拒むのはv2概念が未裁定だからではなく、v1経路へv2 documentを流さない型分離である。
- **F17:** 誤り。holdout v1は現状から既にdangling headでverify不能。「S-1再発行後に初めてholdoutが落ちる」わけではない。またv2機構は未実装ではなく、未発効である。

### P1〜P8

- **P1:** 誤り。measurement known hashと、generator変更時の自己hashが変わる。
- **P2:** 過大主張。reachability改善にはなるが、source provenanceを示さず、履歴書換えも防げない。
- **P3:** remoteをgenerateだけに閉じる方針自体は成立。ただし通常verifyもsubmodule実体を要求するため「環境非依存」ではない。
- **P4:** 別ファイル化自体は成立。**P4′のF11根拠は誤り**で、appendable ledgerを将来のtrust rootにする部分は追加裁定が要る。
- **P5:** 不十分。latest `new_sha256` 一致だけでは旧対応・承認・downstream移行を証明しない。
- **P6:** 一般には成立しない。shallow cloneと再度の履歴書換えで旧bytesを失い、同じ種類の到達不能を再発する。
- **P7:** S-1内の必要条件としては正しいが、全依存整合の十分条件ではない。
- **P8:** 誤り。generator変更は元の差分契約と衝突し、再発行機構の実効性証明にも必須ではない。先に差分契約の裁定が必要。
---

## 段 4: 裁定 (親、逐語)

### 判定: 実装しない。canonical 成果物を変更せず、裁定パッケージでユーザーへ返す

両レンズが独立に NO-GO。親が直接裏取りして確定した閉包が決定的である。

`known_axes_freeze.json` の bytes を変えると、正規の道が **3 方向すべて塞がっている**。

1. **holdout を放置** → `output/s8b-freeze/holdout_freeze.json` の `known_axes_freeze.sha256`
   (`354f4b87…`) が現行 bytes と一致しなくなり、`s8b_holdout_freeze.py:641` の worktree 完全一致
   照合が拒否する
2. **holdout を上書き** → `s8b_ratified_freeze.py:62` の `V1_FREEZE_SHA256 = "315b1eb8…"` は
   holdout の bytes をハードコードで固定した v1 trust root であり、`EQUALITY_CHAIN_ADJACENCY`
   (`:138-140`) で result / journal / cert / manifest の等式連鎖に織り込まれている。上書きは
   trust root の再定義になる
3. **v2 世代で追随** → `_TRANSITION_V1_TO_G1` (`s8b_ratified_freeze.py:115-120`) の許可 JSON Pointer
   集合は `/floor` `/budget` `/refreeze_note` `/schema_version` `/generator/sha256`
   `/design_source/sha256` `/frozen_at_head` `/env_tag` `/floor_protocol` `/floor_source`
   `/measurement_closure` `/generation_number` `/supersedes_sha256` であり、
   **`/known_axes_freeze/sha256` を含まない**。列挙外は前世代と厳密一致が要求されるため拒否される

したがって [T-005] は「承認された scope の中では実行できない」。実装を強行すれば、
S-1 を局所的に緑化する代わりに downstream の trust root を不整合にし、しかも
`test_frozen_artifacts.py` の literal pin を外すことでその不整合の検出手段まで失う。

### 親の provisional 裁定の結末 — 8 件中 6 件が誤り

| ID | 結末 | 理由 (採用した所見) |
|---|---|---|
| P1 | **否認** | 変更は anchor だけでなく measurement の known hash と自己 hash、downstream trust root に及ぶ |
| P2 | **否認** | push 前の `origin/main` を anchor にすると、freeze は新 generator SHA を記録する一方 `git show <anchor>:<generator>` は旧 bytes を返す。anchor が source closure を指さない |
| P3 | 要修正 (方針のみ採用) | remote 依存を generate に閉じる方針は成立。ただし「published を保証する」とは言えず、通常 verify も submodule 実体を要求するので環境非依存でもない |
| P4 | 条件付き採用 | 別ファイル化自体は成立。ただし **P4′ の根拠 (F11) は誤り** |
| P5 | **否認** | 最新 hash 一致だけでは旧対応・承認・downstream 移行を証明しない |
| P6 | **否認 (一般には不成立)** | shallow clone と再度の履歴書換えで旧 bytes を失い、同種の到達不能が再発する |
| P7 | 不十分 | known→measurement の順序は必要条件だが、依存閉包は holdout と s8b trust root まで続く |
| P8 | **否認** | generator 変更は差分契約と衝突し、機構の実効性証明にも必須ではない |

### 親の brief の誤り (自己申告)

- **F11 は誤り。** 「freeze 内世代連鎖は本 repo で未裁定」という推論は成立しない。
  `s8b_ratified_freeze.py` に generation / approval / active pointer / transition / source semantics が
  **実装済み**であり、v1 verifier が世代 field を拒むのは「未裁定だから」ではなく
  **v1 経路へ v2 document を流さない型分離**である。P4′ はこの誤った根拠に立っていた
- **F17 は誤り。** 「現状は known が落ち、再発行後は holdout が落ちる」という二状態モデルは不正確。
  holdout は **再発行前から既に落ちている** (`design_source sha256 不一致`。親が実測で確認)
- **F7 は不完全。** ancestry 失敗の oracle 伝播は正しいが、holdout 自身の dangling head と
  floor/budget null が独立に拒否することを落としていた
- **F8 の「published」は未証明。** fetch していない local remote-tracking ref を publication の
  証明として扱ったのは過大主張だった

### 事前登録変異 M1..M5 は 5 件すべて欠陥 (実測前に判明)

段 6 の変異実測には到達しなかったが、両レンズが事前登録の欠陥を独立に指摘した。記録に残す。

- **M1**: 死んだ SHA は `cat-file -e` (`:751`) が先に拒否するため、`merge-base` 単独変異では
  受理集合が変わらない。「実在する非 ancestor commit」へ差し替えが必要
- **M2**: baseline helper は `origin/main` tip 自身を選ぶ設計なので「baseline 拒否・mutant 生成」が
  逆転している
- **M3**: known の bytes を変える変異は measurement の known hash 不一致でも赤くなり過剰決定。
  measurement JSON への末尾空白追加へ一意化が必要
- **M4**: 既存拒否は `exists()` 検査と `open(...,"x")` の二層。単層変異は等価変異。
  両層同時変異では複数 assertion が同時に赤くなり単一理由の killer にならない
- **M5**: source へ変異を当てるとその変異自体が generator SHA を変え、`generator sha256 不一致` で
  先に拒否される。kill 帰属が成立しない

**教訓: 変異の事前登録は「どこを変えるか」だけでなく「その変異が受理集合を変える単一理由になるか」を
コードで裏取りしてから確定すべきだった。** 5 件中 5 件が机上で誤っていた。

### 本 wave で新たに判明した、未記録の問題

1. **holdout freeze は 2026-07-18 から無効だった** — `docs/phase3-8b-descriptor-design.md` が
   floor protocol 裁定記録の commit 群 (`3d96f57`/`b7b38da`/`cdb16c0`/`05244bf`/`bfa0f08`) で
   更新され、holdout の `design_source` sha256 が外れた。宣言済み pin のドリフトが 3 日間
   気づかれなかった (F9 型)
2. **dangling `frozen_at_head` は freeze 族に共通の病** — S-1 の歴代 5 世代すべて (`c648bbe` /
   `ca92133` / `c890e95` / `0f30427` / `2066ce6b`) と holdout (`2e20d441`) が repo に存在しない
3. **D68 (7) の隠蔽パターンが `test_s1_measurement_freeze.py` に現存する** —
   `:91,98,113` が production known generator の**現行 hash を動的に注入**し、
   `K.build_document` を fixture document の echo に置換している。generator が変わっても
   measurement の負例はその変化を吸収してしまう
4. **oracle 系テストは holdout refusal の追加を検出できない** —
   `test_s8b_oracle_driver.py:503-507,519-527,1345-1371` は「floor-null がある」「budget-null がある」
   「status=refused」「rc=2」しか要求しない。拒否理由が 1 件増えても全走は赤くならない
