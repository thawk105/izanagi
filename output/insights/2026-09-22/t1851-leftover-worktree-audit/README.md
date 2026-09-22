# [T-1851] / [T-2698] 取り残し worktree `dev-wave-t1851-c3c-official-floor` の tracked 外 file 3,485 件を正典と照合し、正典に無い研究記録 216 件を repo 外へ sha256 付きで保全した

authority: none
default_effect: no-state-change

branch `worktree-dev-wave-t1851-leftover-audit`、base `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` (着手時の local main)。
照合は 2026-09-22 08:56〜09:08 JST (棚卸し file と保全 MANIFEST の mtime)。

**本 wave は対象 worktree へ一切書いていない。** lock の解除、worktree と branch の削除、自動撤去の範囲の変更は
していない。撤去の可否と時期は D2194 項 10 (b) (候補 3 は据え置き、原本判定を掃除手順に入れてから 1 本ずつ扱う) の
裁定事項のままであり、本 wave はその「1 本分の原本判定」の材料を揃えただけである。T-2778 / D2163 の子 worktree 撤去の範囲も変えない。

---

## 1. 結論 — 次回の棚卸しで使う要点

- 対象: `.claude/worktrees/dev-wave-t1851-c3c-official-floor` (branch tip `0709a4018ead6da495391674d76284fe479cf983`、
  local main に包含済み、locked)。branch tip の tracked 一覧に無い file は **3,485 件**
  (submodule `external/ccbench` の中は走査していない)。
- **正典に bytes が無い研究記録 216 件 (86,922 bytes) は repo 外へ保全した:**
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-leftover-audit/preserved/`
  - `MANIFEST.json` (各 file の相対 path・bytes・sha256・複製元・mtime) の sha256 =
    `be432a6cbe9bd145791ee7661fe14e30fa209642ff176a17b2c6244f1c6a022b`。
    同じ bytes を本 insight の `evidence/preserved-MANIFEST.json` に置いた
  - `SHA256SUMS` (`sha256sum -c` で検算できる形) の sha256 =
    `e689599b63d451b7972bac497ea1d9fbf23fd745c076905581b98bcdc87b5ff5`
- 残りの 3,269 件は保全していない。内訳と理由は §3 の表のとおり
  (正典と bytes 一致 12 件、pin 固定の第三者ソース複製 3,128 件、dispatch 1 回分 9 件、`__pycache__` 120 件)。
- したがって **照合時点の中身のままなら、この worktree を撤去しても研究記録は失われない**
  (保全物・正典・T-2724 の退避 bundle・repo 外 job 証拠置き場のどこかに bytes がある)。
  照合後に worktree の中身が変われば、この結論は及ばない。
- **注意: tracked 外 file の約 3 分の 1 は `.gitignore` の無視対象で、`git status` に出ない。**
  `output/env/pegasus/floor/job-staging/`、`output/pegasus-dispatch/`、
  `output/env/pegasus/silo_ladder_rung1/job-staging/`、`__pycache__/` がそれに当たる (branch tip の `.gitignore` で確認)。
  T-2724 §4 が記録した dirty の内訳 (claims 3 件 + submissions 3 dir) にも、依頼文の対象
  (claims + submissions 3 件) にも、無視対象の job-staging 3 dir (同じ 3 走行の受領証・失敗記録・環境記録) は入っていなかった。
  本 wave はこれも照合・保全の対象に含めた (§2 の P1)。

## 2. 対象と方法

- 読むだけの操作に限った。対象 worktree へは git を向けない (Bash guard が隔離 session からの `git -C` を拒否する)。
  代わりに、`os.walk` で列挙した file 集合と `git ls-tree -r --name-only 0709a4018` の差を tracked 外の集合とした
  (ignored と untracked を区別しない)。
- 各 file の sha256 と git blob hash を取り、(i) local main `8fd2a2f5c` の全 blob (32,761 行の `ls-tree -r`) と、
  (ii) 正典 evidence dir 2 本 (`output/insights/2026-09-15/t1851-c3c-official-floor-run/evidence/`、
  `output/insights/2026-09-16/t2698-official-floor-resubmit/evidence/`) の sha256 に照らした。
  保全の判定は (ii) との sha256 一致だけで行う — 環境記録 (compiler version 等) には別走行の同一 bytes が main の他所に
  在るものがあるが、それは本 3 走行の記録ではないので正典扱いしない。
- 保全は create-only (宛先 root が在れば停止)。複製直前に複製元を再 hash して棚卸し値と照合し、複製後に宛先を再 hash した。
  その後、宛先の実 file 集合と MANIFEST を別 script で突き合わせ (216 = 216、不一致 0)、`sha256sum -c` も rc=0 だった。
- 親の provisional 裁定 (攻撃対象として段 6 レビューへ渡した):
  - **(P1)** 無視対象の job-staging 3 dir も照合・保全に含める。撤去時に `git status` で見えず黙って失われる位置にあり、
    「次回の棚卸しで調べ直さずに済む」目的に要るため。
  - **(P2)** 正典 = 上記 evidence dir 2 本 (と T-2724 §4 の退避 bundle)。判定は sha256 一致。
    保全は第三者ソース複製以外で正典に bytes が無い file 全部 (rc・空 file も投入記録の一部として含める)。
  - **(P3)** 保全しないもの = 第三者ソース複製、dispatch 999017、`__pycache__`。§3 の理由による。
- 使った script (repo には入れていない): job dir の `scripts/` (`inventory.py`、`untracked_scan.py`、`classify.py`、
  `compare_third.py`、`preserve.py`、`verify_preserved.py`、`aggregate.py`、`summarize.py`)。
  棚卸し結果: `inventory.jsonl` (sha256 `9b1cd22e…`、2,409 行)、`inventory-extra.jsonl` (sha256 `ede3ca88…`、956 行)、
  `untracked-all.txt` (sha256 `fa82758a…`、3,485 行)、`compare-third.txt` (sha256 `aaf1c990…`)。

## 3. 照合結果

| 区分 (worktree 内 path) | 件数 | 判定 | 扱い |
|---|---:|---|---|
| `output/claims/*.claim` | 3 | 正典に無い | **保全** (940 bytes) |
| `output/env/pegasus/floor/attempts/submissions/<nonce>/` の小 file (3 dir × 20) | 60 | 57 件は正典に無い、`submit-receipt.json` 3 件は正典と bytes 一致 | **57 件保全** (27,506 bytes)、3 件は正典参照 |
| 同 `<nonce>/masstree-payload/` (3 dir) | 2,346 | pin 固定 clone の複製 (下記) | 保全しない |
| `output/env/pegasus/floor/job-staging/0:<request>.nqsv/` (3 dir × 55、無視対象) | 165 | 156 件は正典に無い、`job-result.json` / `floor-driver.stderr` / `submit-receipt.json` の 9 件は正典と bytes 一致 | **156 件保全** (58,476 bytes)、9 件は正典参照 |
| `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/` (無視対象) | 782 | payload の複製元 (下記) | 保全しない |
| `output/pegasus-dispatch/` (無視対象) | 9 | 開発工程の検査記録 (下記) | 保全しない |
| `__pycache__/` (無視対象) | 120 | 再生成物 | 保全しない |
| 計 | 3,485 | | 保全 216 |

正典と bytes 一致した 12 件の対応は `evidence/matched-canonical.json` (sha256 `d81dc70d…`) にある。
対象 3 走行は T-1851 insight §1 の表の 3 件 (`998882.nqsv` / nonce `83ec41df…`、`999039.nqsv` / `acb88122…`、
`999102.nqsv` / `d198cec4…`) である。

### 保全した記録の中身 (正典に無かったもの)

- **claims 3 件** — campaign identity ごとの一回限りの所有記録 (`orchestrator/campaign/campaign_claim.py`、release を持たない)。
  実行ノード・boot id・pid・process 開始時刻・job id を持つ。実行ノードは順に `bnode016` / `bnode030` / `bnode022`。
  同じノード名と boot id は job-staging の `reservation.json` にも在る。正典の evidence には実行ノードの記録が無い。
- **submissions の小 file 57 件 (各走行 19 件)** — 投入直前の `check_quota` / `pegasusinfo` / `qstat -Q` / `rbudgetcheck` の
  rc・stdout・stderr とそれをまとめた `pre-submit.json`、`qsub` の出力 (request ID)、`scheduler.stderr`
  (scheduler の会計: Elapse 93 / 111 / 128 秒。正典 §1 の「約 90 / 111 / 128 秒」の出所に当たる)、
  `evidence-index-status.json` (repo 外 job 証拠置き場の索引の発行記録)。
- **job-staging 156 件 (各走行 52 件)** — `failure.json` (3 走行とも stage `floor_driver`、rc 1)、`reservation.json`
  (要求 36,000 秒、実行ノード、boot id、script sha256)、`scheduler-elapse.json`、cell ごとの `phase-preflight-*.json` (各走行 12 件)、
  `sort-swo-oracle-dependency.json` (依存 archive の hash と第三者ソース pin の捕捉値)、gflags / glog の configure・build・install の
  出力、compiler / cmake / python の path と version、`qstat -f` の出力、hostname。

### 保全しなかったものの根拠

- **第三者ソース複製 (payload 2,346 件 + thirdparty-src 782 件)** — `tools/pegasus/submit_floor.sh` が投入時に
  常設 root `thirdparty-src/<name>` を pin 固定・clean と検査したうえで `cp -a` した複製である。
  3 つの clone の `.git/HEAD` は branch tip の `tools/pegasus/policy.json` の pin と一致した
  (masstree `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`、mimalloc `02a2f5df9d7d46d30263b83832eebeeab62dc5fe`、
  googletest `f8d7d77c06936315286eb55f8de22cd23c188571`)。3 つの payload と常設 root の 4 組は file 集合が同一 (各 782 件) で、
  作業 file 712 件の sha256 がすべて一致し、違うのは `.git/index` (stat のキャッシュ) 3 件だけだった。
  主 checkout に常設 root は無いので、再取得は policy に記録された URL と pin から行う。
- **dispatch 999017 (9 件)** — T-1851 wave が計算ノードで走らせた provenance 全史監査 (request の task = `provenance`)。
  結論 (10,105 件、新規違反なし) は T-1851 insight §8 の検査表に記載済みで、研究記録ではない。
- **`__pycache__` 120 件** — Python の byte code キャッシュ。

### 正典側で確かめたこと

- 3 走行の run directory (`journal.jsonl` + `launch_certificate.json`) は対象 worktree に**現存しない**。T-2724 が
  2026-09-18 06:43 JST に退避 bundle `<git common dir>/izanagi/s8b-floor-evacuation/pegasus/payload/` へ移しており
  (`output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` §4)、bundle の 6 file は T-1851 insight evidence の
  同名 6 file と sha256 がすべて一致した。
- repo 外 job 証拠置き場 `/work/1/SFC/tanab/izanagi-job-evidence/` に 3 走行の `checkpoint.jsonl` (各 10,197 bytes) と索引が在る。
  対象 worktree の外なので撤去の影響を受けない。本 wave は触れていない。
- T-2698 insight には 3 走行の request ID が「cell build 段で停止した先行走行」として 1 回出るだけで、3 走行の原本は持たない。
  T-2698 自身の claim・submission 記録は同 wave の `run-backup/` にある (同 insight の erratum)。

## 4. 到達範囲と非保証

- 照合は照合時点の bytes に対するものである。以後に対象 worktree の中身が変われば、§1 の結論は及ばない。
- submodule `external/ccbench` の中 (build 生成物を含みうる) は走査していない。
- 「研究記録かどうか」の線引き (dispatch 記録と `__pycache__` を保全しない、rc・空 file は保全する) は親の判断である。
  保全しなかった file も sha256 は job dir の棚卸し file に残る。
- 保全先 `dev-wave-jobs/` は repo 外で snapshot が無い。T-2698 の `run-backup/` と同じ置き場であり、耐久性も同じである。
- 撤去の可否は判断していない。D2194 項 10 (b) が前提にした原本判定の掃除手順への組み込み (T-2814) は
  2026-09-21 に着地している (worklog entry 1775、`.claude/commands/cleanup-branches.md` §2 の「未追跡 `output/` は
  該当 wave の insight『証拠の所在』節で repo 外原本か確かめる」)。ただしこの命令の入口は「未追跡」であり、
  `git status` に出ない無視対象 (§1 の注意) は同じ手順で見えるとは限らない。本 wave は手順に何も足していない。

## 5. 証拠の所在 (`/cleanup-branches` §2 の照合先)

対象 worktree の tracked 外 file が持つ記録の所在を、照合時点で次のとおり確かめた。

| 記録 | 所在 (repo 外原本 / 正典) |
|---|---|
| claims 3 件、submissions の小 file 57 件、job-staging 156 件 | repo 外: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-leftover-audit/preserved/` (MANIFEST sha256 `be432a6c…`) |
| submit-receipt 6 件、job-result 3 件、floor-driver.stderr 3 件 | 正典: `output/insights/2026-09-15/t1851-c3c-official-floor-run/evidence/` (bytes 一致) |
| 3 走行の run directory (journal + 起動証明書) | 正典: 同 evidence/ と、T-2724 の退避 bundle `<git common dir>/izanagi/s8b-floor-evacuation/pegasus/payload/` (worktree には現存しない) |
| 3 走行の計算ノード側 checkpoint | repo 外: `/work/1/SFC/tanab/izanagi-job-evidence/pegasus/<request>/<nonce>/checkpoint.jsonl` |
| 第三者ソース複製 3,128 件 | 原本不要: policy の URL と pin (§3) から再取得できる |
| dispatch 999017 の 9 件 | 結論は T-1851 insight §8、生 log は保全していない (sha256 は job dir の棚卸し file) |
| `__pycache__` 120 件 | 再生成物 |

## 6. 収録物

- `evidence/preserved-MANIFEST.json` — 保全 216 件の一覧 (job dir の `preserved/MANIFEST.json` と bytes 一致)
- `evidence/matched-canonical.json` — 正典と bytes 一致して保全しなかった 12 件と、その正典 path
