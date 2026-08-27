静的監査の結論は「条件付きで実装可能」です。P2・P3・P6・P7 は方向として正しい一方、P5 は DAG 基盤だけ再利用可能、P8 は誤りです。特に、同一 uid で AI が broker を起動できる運用では、TTY 要求や鍵の非書込化を足しても D905/D906 を満たしません。

Web 検索、編集、pytest 実走は行っていません。以下の行番号は現行 main または回収物の行番号です。

## A. 回収 3 単位の採否

### A-1. Ed25519 検証子

| file | 判定 |
|---|---|
| `recovered/u1/ed25519_verify.py` | 採用 |
| `recovered/u1/test_ed25519_verify.py` | 改訂して採用 |

`ed25519_verify.py` が実際に検査するのは、exact bytes 型・鍵長・署名長 (`109-114`)、`S < L` (`118-120`)、canonical point encoding (`78-101`)、公開鍵の identity と prime subgroup (`122-126`)、cofactor 付き検証方程式 (`129-138`) です。

構造上の注意は次です。

- `97-98` の二度目の parity 検査は到達不能です。`x != 0` なら `x -> P-x` で parity は必ず反転し、`x == 0 && sign` は `93-94` で拒否済みです。
- `99-100` の曲線式は通常経路では `86-92` の平方根検査から導かれる冗長検査です。定数式でも denominator が 0 になる y は存在しないため、独立防壁として数えられません。
- `R` の subgroup は明示検査せず、`132-136` の cofactor 方程式で処理しています。親監査の低位数 5 種は公開鍵だけで、crafted low-order `R` の網羅ではありません。
- 検証対象 message に上限がなく、`130` の連結は message 全体を複製します。receipt 側で行長を先に制限しないとメモリ DoS 面が残ります。
- variable-time 実装ですが公開検証だけなので秘密情報の timing leak ではありません。

回収 test の問題は以下です。

- `291-295` の runner-discovery test は恒真です。`assert "__main__" in path.read_text(...)` 自身が `__main__` という文字列を含むため、実際の runner block を削除しても通ります。AST で `if __name__ == "__main__"` と `pytest.main([__file__, ...])` を検査するか、この meta-test を削除します。
- `132-135` の small-order-R test は「small order を独立に拒否した」ことを測らず、単に既存署名の `R` を identity に置換して方程式が赤になることしか測りません。
- 現行 repo test の第 4 vector は親監査の msglen=1023 vector ではありません。
- message/signature の `bytearray`、`memoryview`、bytes subclass は未検査です。

改訂後は RFC 4 vector、固定 seed による 40 valid / 200 corrupted differential、`S+L`、低位数公開鍵と `R`、全 3 引数の型規律を deterministic test として入れます。親監査 script は乱数・print・外部実行用のため、そのまま test file へコピーせず、固定入力へ変換します。

### A-2. 署名 receipt verifier

| file | 判定 |
|---|---|
| `recovered/u2/enforcement_source_ratification_receipt.py` | 改訂して採用 |
| `recovered/u2/test_enforcement_source_ratification_receipt.py` | 改訂して採用 |
| `recovered/u2/enforcement-source-ratification-receipts.v2.jsonl` | 不採用・書き直し |

採用できる核は canonical JSON/base64 (`70-114`)、trust-root schema (`183-228`)、署名・serial・previous hash・path/hash/root binding (`281-391`)、最終 digest/path match (`453-474`) です。

不足または誤りは次です。

- `394-450` は線形 `git log --reverse --full-history` であり、main の DAG 修正を失っています。
- shallow/graft 拒否がありません。
- ledger が `orchestrator/campaign/` にあり、AI が garbage を直接追記できる面です。
- trust root と ledger の Git tree mode を検査せず、regular file であることを保証しません。
- `source_commit` は `268-278` で object の存在しか検査しません。reachable であることも、その commit の 27 blob が署名された closure digest と一致することも検査しません。現状では署名 field が意味上 decorative です。
- trust-root JSON は exact schema ですが canonical bytes + LF を要求しません。
- ledger blob、行長、行数、JSON nesting に上限がありません。
- `374-377` の decision 拒否と `468` の最終 decision 条件は二重です。
- `_SIGNED_KEYS` は署名以外の全 field を含むので署名対象選択自体は正しいです。

回収 test では次を直します。

- `273-313` の merge test は `309` の前提 assert が偽です。これは production `428-429` の欠陥を示していません。
- `746-775` の signed-field mutation は、`decision`、`closure_paths_sha256`、`trust_root_sha256` が署名以外の後段でも拒否されます。署名検査だけを孤立させる fixture は `source_commit` case だけです。
- divergent branches、shallow clone、graft、source-commit/closure 不一致、trust-root/ledger の non-regular mode、blob/line bounds を追加します。

空 ledger は wrong path なので回収 file 自体は不採用です。人間 bootstrap が `hooks/enforcement-source-ratification-receipts.v2.jsonl` を空 file として一度だけ作ります。author は実 repo の ledger を作成・移動しません。

### DAG の具体的判定

v1 で、

```text
base  = [A]
left  = [A, L]
right = [A, R]
merge = [A, L, R]
```

なら main `enforcement_source_ratification.py:568-607` の DAG 判定が正しいです。merge の parent union `{A,L,R}` を保持し、merge 自身は新しい digest を追加していません。回収線形版は left と right を直列の前後版と誤認し、`[A,L] -> [A,R]` を置換として拒否します。

ただし v2 は同じ受理則を使えません。署名行を

```text
S1 = serial=1, previous=null
SL = serial=2, previous=hash(S1)
SR = serial=2, previous=hash(S1)
```

とすると、merge の `[S1,SL,SR]` は 3 行目の serial と previous hash が不正で、逆順も同じです。署名をやり直さずに両 parent の exact 行を 1 本の hash chain へ合流できません。

したがって改訂設計は、

- `_assert_full_history_repository`、`_reachable_commit_parents`、object/mode/size binding は共通化する。
- v2 では parent chain が同一、または一方が他方の exact prefix の merge だけを許可する。
- divergent signed sibling chains は専用エラーで fail-closed に拒否する。
- v1 の digest union と `_is_subsequence` は v2 へ使わない。

とします。divergent merge も受理したいなら serial/previous-hash schema 自体を DAG-native に変える必要があり、これは親に確認が要る未確定事項です。本プランは受理集合を広げない側、つまり拒否を推奨します。

### A-3. Broker

| file | 判定 |
|---|---|
| `recovered/u4/ratification_broker.py` | 不採用・書き直し |
| `recovered/u4/test_ratification_broker.py` | 不採用・書き直し |

再利用できるのは closure digest 計算、remote closure tuple 照合、署名 body の形、HEAD 最終照合の考え方です。production としては次の欠陥があります。

- `54-56`: `data=None` で child stdin を継承する。
- `65-83`: broker が秘密鍵を自動生成する。
- `200-207,238-239`: trust root が無ければ自分の公開鍵を trust root として書く。
- `171`: `--yes-i-have-read-this` は一度も読まれない。
- `217-224`: TTY を要求せず、pipe/PTY のどちらでも `y` を受ける。
- `142-158`: AI が制御する source bytes の C0/ESC を terminal へ生で出し、表示を偽装できます。
- `121-140`: 既存 ledger の signature を検証しません。
- `121-140`: 最終 LF を要求しないため、LF 欠落 ledger を受理して `240` で直結追記し、JSONL を壊します。
- `200,208`: committed HEAD でなく worktree の trust/ledger を読みます。
- trust/ledger の read と `240` の append の間に CAS/lock がありません。
- key file の symlink、owner、mode、regular-file 性を検査しません。
- remote Git は `100-103` で PATH 上の `git` と ambient config を使い、verifier 側の hardening と非対称です。
- repo 内 `tools/ratification_broker.py` は 27-path closure の外です。AI がこの file を変え、人間がそのまま実行すると、鍵が安全でも表示・署名対象を偽装できます。

書き直し後は既存の committed trust root・空 ledger・既存鍵を必須にし、生成経路を全削除します。child stdin は data なしなら `DEVNULL`、署名 data ありなら明示 PIPE とし、承認は trusted operator host の `/dev/tty` だけから読みます。ただし TTY は認証ではなく誤操作防止です。

test は PTY を割り当てた positive case、pipe の `y` 拒否、child stdin が EOF になる検査、control-byte escape、既存 ledger signature、LF、committed/worktree drift、HEAD/ledger raceへ書き直します。`test_private_key_bytes_never_leave_client` は鍵生成・mode・stdout・child stdin・remote treeを一つに束ねているため分割します。

### M4 の独立検算

- M4(a) は production 欠陥です。`subprocess.run(input=None)` は stdin を PIPE にせず継承し、回収 test stub `test_ratification_broker.py:79` が承認入力を消費します。実 ssh/openssl が読まない場合もありますが、読める状態を作ったこと自体が欠陥です。
- M4(b) は production 欠陥ではなく test 欠陥です。赤は `test...receipt.py:309` の偽前提で止まり、production `if blob.stdout == previous_raw` へ到達していません。別件として回収 production の線形履歴と shallow 防御欠落は実欠陥です。

### 変更前後の受理形

実装 land 時には v2 ledger を空にし、v1 行を自動移行しません。

```text
変更前:
exact 25-path map
AND digest が committed v1 DAG ledger の canonical unsigned 行に存在

変更直後:
exact 27-path map
AND committed canonical trust root
AND full-history DAG と regular-file 制約
AND 全 v2 行の Ed25519/serial/hash-chain/source binding
AND matching signed receipt
ただし ledger は空なので受理集合は空
```

したがって land 時点では新しい closure を一つも自動受理しません。後日の人間署名は、実装による受理集合拡張ではなく trust root 保有主体による明示的な authorization event です。

## B. P7 配線の完全な閉包

### 実装で触る file:line

| file:line | 改訂 |
|---|---|
| `orchestrator/campaign/ed25519_verify.py:1-138` | u1 を配置。production import は `hashlib` のみ |
| `orchestrator/campaign/enforcement_source_ratification_receipt.py:20-474` | u2 の path、DAG、source binding、bounds、mode を改訂 |
| `tools/ratification_broker.py:1-250` | u4 を bootstrap-free broker として書き直す |
| `campaign_lock.py:27-55` | 25 を 27 にし、新 2 path を ratification group に追加 |
| `contract_loader_binding.py:2,14-15,58-61,387-402` | doc と import を v2 にし、`require_signed_ratification` を呼ぶ |
| `enforcement_source_ratification.py:276-538` | DAG/Git/object kernel を path・row-loader parameter 化。v1 wrapper の挙動は維持 |
| `artifact_admission.py:67-68,157-159,789-790,874-875` | exact 25 を exact 27 に追随 |
| `ident.py:234-245` | endpoint の確認。`239` は変更せず生きた caller として維持 |
| `hooks/README.md:332-345` | v2 trust/ledger、外部 broker、script/subprocess 限界を D526 上限内で記載 |

`CONTRACT_LOADER_RELATIVE_PATHS` の推奨順は、既存 20 番目の v1 module の直後に `ed25519_verify.py` と `enforcement_source_ratification_receipt.py` を置きます。`test_t671_source_binding.py:55-56` は位置 slice なので、単に末尾へ足して silent に receipt group を 5→7 にしてはいけません。ratification group を `[17:22]`、既存 receipt group を `[22:]` と明示します。

### pin と golden

親 M7 は網羅ではありません。M14 の追加結果は正しく、さらに test node 名を記録する duration ledger も波及します。

- `test_t671_source_binding.py:37-56`: 独立 expected tuple と位置 slice
- 同 `181,336,349,357`: `twenty_five` node 名
- 同 `185-208,369-381,529-530,604-605`: exact tuple pin
- 同 `426-489`: v1 fixture helperと live acceptance testを署名 fixtureへ変更
- 同 `736-772`: caller meta-test。`require_signed_ratification` が `contract_loader_binding` から exact 1、`require_ratified_closure` の production caller が 0 であることを追加
- `test_artifact_admission.py:46-72`: production から独立した golden tuple
- 同 `1010-1012`: identity scope literal
- 同 `1134`: `len(...) == 25` を 27 へ変更
- `acceptance_duration_ledger.json:14847-14848,14902-14909`: test rename の key だけ機械移行し、duration 数値は変えない
- `campaign_lock.py:27`、`contract_loader_binding.py:2,58,61`、`artifact_admission.py:67,157,789,874`: production の exact-25 文言

`docs/archive/`、`docs/failures.md`、既存 paper provenance JSON にある 25-path 表記は歴史記録なので変更しません。tracked `campaign.lock` は親 M12 のとおり closure map を持たず、migration は不要です。

### `ratified_enforcement_source` fixture

現行 `conftest.py:194-236` は v1 専用です。改訂は以下です。

1. fixture 内だけで `cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey` を import する。
2. real repo の `contract_loader_binding.capture_contract_loader_binding()` で 27-path map/digest を得る。
3. synthetic repo 内に ephemeral key、canonical trust root、空 hooks ledger を作り commit する。
4. synthetic repo HEAD を `source_commit` とし、実 closure digestを署名した serial 1 receipt を hooks ledger へ書き、もう一度 commit する。
5. `monkeypatch.setattr(receipt_module, "_REPO_ROOT", repo)` を行う。
6. fixture の返値は従来どおり digest のままにする。

`monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)` だけでは切り替わりません。v2 module は回収物 `enforcement_source_ratification_receipt.py:43` の独立した `_REPO_ROOT` を `135-165,459-462` で参照します。fixture は v2 module 自身を patch する必要があります。

`cryptography` は conftest の module top-level や production moduleから import しません。したがって本番 closure は pure Python のままです。

### fixture consumer の完全棚卸し

静的 AST と文字列検索の結果は次です。

- 22 test file
- conftest 自身を除き 112 textual use site
- 111 fixture consumer scope
- module-wide marker を展開すると 792 base pytest node。parametrize suffix の展開数は pytest を走らせていないため数えていません。

Module-wide consumer は次の 10 file / 691 base nodeです。

| marker | node |
|---|---:|
| `test_autonomous_trial_completeness.py:16` | `test_autonomous_trial_completeness.py::*` 148 |
| `test_critic.py:24` | `test_critic.py::*` 75 |
| `test_layer3_admission_diagnosis.py:13` | `test_layer3_admission_diagnosis.py::*` 12 |
| `test_p3_build_authority_cli.py:23` | `test_p3_build_authority_cli.py::*` 19 |
| `test_p3_exploration_namespace.py:22` | `test_p3_exploration_namespace.py::*` 12 |
| `test_paper_story_a1_paired.py:18` | `test_paper_story_a1_paired.py::*` 70 |
| `test_s8b_oracle_report.py:51` | `test_s8b_oracle_report.py::*` 184 |
| `test_t126_pegasus_tools.py:23` | `test_t126_pegasus_tools.py::*` 119 |
| `test_t126_qualification_artifacts.py:52` | `test_t126_qualification_artifacts.py::*` 28 |
| `test_t126_qualification_driver.py:62` | `test_t126_qualification_driver.py::*` 24 |

残る 101 explicit base node は、次の marker/signature 行の直後の test node です。

| file | consumer 行 / node 数 |
|---|---|
| `test_campaign.py` | `757,3095,3428,8595,8643,8688,8853,8935,9038,9075,9104,9147,9174,9207,9255,9421,9473,9523,9545,9573,9658,9685,9706,9724,9845,9860,9954,12824` / 28 |
| `test_dev_wave_land.py` | `7612` / 1 |
| `test_p3_autonomous_workload_trial.py` | `1415,4781` / 2 |
| `test_p3_s4_loop.py` | `2231,3217,3241,3319,3354,3412,3497,3539` / 8 |
| `test_p3_s4_loop_sort.py` | `320,679,773` / 3 |
| `test_p3_s4_loop_trigger_gating.py` | `583,690,722,754,935,969,995,1099,1120,1143,1220,1287,1340,2157,2374,2518,2563,2595` / 18 |
| `test_real_repo_serialization.py` | node `2268`; use site `2269,2450` / 1 node・2 site |
| `test_s1_direct_comparison.py` | `322,353,1196,1215,1301,1323,1370,1424,1467,1492,1509,1541,1573,1595,1629,1667` / 16 |
| `test_s6_sort_sweep.py` | `318,361,434,449,518` / 5 |
| `test_s8a_trigger_sweep.py` | `394,443,520,576` / 4 |
| `test_screening_driver.py` | `211,302,473,522,560` / 5 |
| `test_trial_registry.py` | `1746,1801,1844,1885,1922,1967,2025,2152,2203,2291` / 10 |

### v1 gate の扱い

推奨は「production caller をゼロにするが、v1 reader と台帳を今 wave では削除しない」です。

- `contract_loader_binding.py:396` を v2 に置換するので live gate は v2 だけになります。
- `require_ratified_closure` は caller 0 を meta-test で固定します。
- `hooks/enforcement-source-closure-ratifications.v1.jsonl` は 1 行の歴史証拠として残し、production 非消費であることを `hooks/README.md` に明記します。
- `test_enforcement_source_ratification.py` は「約 460 行」ではなく現状 929 行です。DAG/Git kernel を v2 が再利用するため、既存期待を変えず残します。v1 end-to-end 部分は legacy regression になります。

残す害は、古い unsigned 行を現役批准と誤読しやすいこと、将来の accidental fallback、保守時間です。caller 0 meta-test と明示文書で抑えます。

消す害は、hooks file の人間専有変更が必要になること、既存 test 期待を大量削除すること、DAG kernel の回帰 corpus を失うこと、過去の批准証拠を消すことです。今回の制約では削除の害が大きいと判定します。

## C. 信頼根と bootstrap

### 現回収 broker を AI が奪う操作列

止める検査はありません。

1. AI が自分の Ed25519 key を作る。broker 自身の `_ensure_key:65-83` に任せてもよい。
2. AI が PTY 付きで `tools/ratification_broker.py --target host:/repo` を起動する。
3. `ratify?` が出た時点で PTY に `y` を送る。TTY 検査を追加しても AI は PTY を作れます。
4. trust root 不在なので `initial=True` (`203-205`)。
5. broker が SSH child 内の redirect で trust root (`238-239`) と receipt (`240`) を書く。`guard_write.py:155-171` はこの subprocess/remote write を見ません。`hooks/README.md:198-200,303-304,332-345` もこの限界を明記しています。
6. `git add -- hooks/...` は M13 の実測どおり許可されます。

したがって P2 は必須です。

### 人間だけが行う一度きり bootstrap

author が作る broker は key/trust/ledger を一切生成せず、すべての不在を拒否します。人間は AI が read・exec・write できない trusted host/account 上で、例として次を実行します。

```bash
RATIFY_STATE=/var/lib/izanagi-ratification
RATIFY_REPO=/absolute/path/to/izanagi

umask 077
install -d -m 0700 "$RATIFY_STATE"
openssl genpkey -algorithm ED25519 \
  -out "$RATIFY_STATE/ratification-ed25519.key"
openssl pkey \
  -in "$RATIFY_STATE/ratification-ed25519.key" \
  -pubout -outform DER \
  -out "$RATIFY_STATE/ratification-ed25519-public.der"
```

次の human-only command が raw 32-byte key を検査し、trust root と空 ledger を exclusive-create します。

```bash
python3 - "$RATIFY_STATE/ratification-ed25519-public.der" \
  "$RATIFY_REPO/hooks/enforcement-source-ratification-trust-root.v1.json" \
  "$RATIFY_REPO/hooks/enforcement-source-ratification-receipts.v2.jsonl" <<'PY'
import base64
import json
import os
from pathlib import Path
import sys

der_path = Path(sys.argv[1])
trust_path = Path(sys.argv[2])
ledger_path = Path(sys.argv[3])
prefix = bytes.fromhex("302a300506032b6570032100")
der = der_path.read_bytes()
if len(der) != len(prefix) + 32 or not der.startswith(prefix):
    raise SystemExit("not an Ed25519 SubjectPublicKeyInfo")
public_key = der[len(prefix):]
document = {
    "public_key_ed25519_base64": base64.b64encode(public_key).decode("ascii"),
    "schema_version": "enforcement-source-ratification-trust-root/v1",
}
trust_raw = json.dumps(
    document,
    ensure_ascii=True,
    sort_keys=True,
    separators=(",", ":"),
).encode("ascii") + b"\n"

for path, raw in ((trust_path, trust_raw), (ledger_path, b"")):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
PY

git -C "$RATIFY_REPO" add -- \
  hooks/enforcement-source-ratification-trust-root.v1.json \
  hooks/enforcement-source-ratification-receipts.v2.jsonl
```

trust root の逐語形は次です。

```json
{"public_key_ed25519_base64":"<raw 32-byte public key の canonical base64>","schema_version":"enforcement-source-ratification-trust-root/v1"}
```

末尾 LF は 1 個です。ledger は 0 byte です。commit も人間 bootstrap の一部とし、AI はこの 2 file を作成・編集しません。

また、人間は repo 内の可変な `tools/ratification_broker.py` を直接実行せず、review 済み bytes を trusted host の AI 非到達・管理者所有 path へ install して使う必要があります。

### ledger 配置比較

| 観点 | `orchestrator/campaign/` | `hooks/` |
|---|---|---|
| 偽造耐性 | 署名が偽 receipt の受理を止める。AI は ledger bytes 自体を自由に変更可能 | 署名に加え、live hook が観測する直接 write を拒否 |
| 可用性攻撃 | garbage、削除、置換で ledger 全体を fail-closed にできる | 直接攻撃は減る。ただし script、subprocess、Git plumbing、ref 操作、staging withholding は残る |
| broker 書込 | 通常の SSH append | SSH child は hooks guard の外なので append 可能。broker が AI から起動不能であることが必須 |
| `git add` | 可能 | M13 のとおり可能。staging は真正性証明ではなく、index-only garbage は verifier が拒否 |

従って P3 は防御強化ですが、「永久 DoS を完全に消す」は過大です。hooks は sandbox ではなく、直接 write 面だけを狭めます。

### P8 の判定

P8 の「秘密鍵が AI の書ける領域外かだけで強さが決まる」は誤りです。必要条件は少なくとも次の 4 つです。

- key bytes を AI が読めない。
- key を使う signing oracle/broker を AI が起動できない。
- broker 実行 bytes と表示経路を AI が変えられない。
- target host/account と SSH identity を AI が成りすませない。

同一機・同一 uid なら、0600 key は AI にも読めます。read 不可でも同じ uid で `openssl -inkey <path>` や broker を実行できれば署名できます。TTY 要求も AI が PTY を割り当てられるため認証になりません。

コードで owner/mode/symlink、key path、committed trust、host-key strict、HEAD stability は検査できます。しかし「この process を人間が起動した」「AI がこの account/socket/signing serviceを使えない」は検出できません。

そのため、trusted broker host/account の実在とアクセス境界は親に確認が要る未確定事項です。これが用意できないなら D905 完了として land してはいけません。

## D. Ed25519 と署名対象

### 親監査が測っていない面

- crafted low-order `R` と cofactor acceptance の adversarial corpus
- 全 key/R noncanonical encoding
- ledger サイズによる CPU・メモリ DoS
- Python interpreter、big-int、`hashlib` 実装の実行時 integrity
- import shadowing・runtime monkeypatch
- receipt canonicalization と field-selection の意味的衝突
- `source_commit` が署名対象でも実 closure と結び付かない問題
- terminal 表示による人間承認の spoof
- broker bytes と signing authority の integrity

### domain と canonicalization

`_DOMAIN_PREFIX:42` は version を含む固定 prefix + NUL であり、payload は canonical JSON object なので prefix境界は一意です。body の `schema_version` も署名対象です。

`_SIGNED_KEYS:58` は signature 自身以外の全 field を含みます。これは正しい選択です。

`_canonical_json_bytes` は任意 Python object 全体で数学的単射とは言えませんが、受理される signed body は次の strict 型へ制限されています。

-固定 schema/decision strings
- lowercase hex strings
- ASCII canonical paths
- exact int serial
- null または hex previous hash
- exact key set

この受理 domain 内では、異なる意味 field が同じ canonical bytes へ潰れる経路は見つかりません。署名文字列だけ異なる 2 receipt が同じ signed bytes になるのは意図どおりで、statement の意味は同じです。

本当の欠陥は canonicalization collision ではなく、`source_commit` を署名しても `268-278` が存在確認しかせず、署名された digestとの対応を検査しないことです。reachable commit かつ、その commit の exact 27 blob map の digest と一致することを追加します。

### pure Python と外部 library

pure Python なら `ed25519_verify.py` と receipt verifier の Git blob が 27-path closure digest に入ります。ただし CPython、big-int、`hashlib`、OS まで覆うわけではないため、「信頼鎖を全部 closure に閉じた」とは書けません。

`cryptography` / PyNaCl を production で使うと、wheel、shared library、OpenSSL/libsodium、build option、site-package version が Git closure digest の外です。同じ repo digestでも実行 verifier が異なり得ます。

従って現行の「Git blob closure が保証できる範囲」という基準では P4 を支持します。ただし自前暗号の保守リスクは残るため、外部 library は test-side differential oracleとして必須にします。

### test-side へ追加する検査

- RFC 8032 の msglen 0/1/2/1023 全 vector
- 固定 40 key/message の三者 valid differential
- 固定 200 bit-flip corrupted signature differential
- `S=L`、`S+L`
- 親監査で使った低位数鍵 5 種を public key と `R` の双方へ適用
- noncanonical y、x=0/sign=1、identity、order-2 key
- bytes subclass、bytearray、memoryview、wrong length を全引数へ適用
- signed field 全 9 個の一つずつの変更で canonical bytes が変わること
- signature fieldだけは signed bytes が変わらないこと
- domain 無し・別 version domain の拒否
- source commit は存在するが closure が異なる receipt の拒否
- ledger line/blob bounds
- control-byte を含む closure diff が terminal へ生出力されないこと

## E. 変異事前登録候補

### 登録価値あり

| 位置・old 逐語 | 無効化時の単一理由 | 他層 | KILLED node |
|---|---|---|---|
| `ed25519_verify.py:119` `if s >= _L:` | `S+L` だけが方程式を通る | 後段なし | `test_rejects_s_at_or_above_group_order` |
| 同 `125` `if not _is_identity(_scalar_multiply(public_point, _L)):` | nonidentity small-order key が cofactor 方程式を通る | identity check は通る | `test_rejects_nonidentity_small_order_public_key` |
| 同 `137` `if not _equal(left, right):` | 1-bit message変更が受理される | 後段なし | `test_rejects_message_changed_by_one_bit` |
| receipt `333-337` の `verify(...)` call | wrong-key earlier row が ledger 全体を汚染しなくなる | 他 field は valid | `test_different_signing_key_on_earlier_row_rejects_the_whole_ledger` |
| 同 `335` `_DOMAIN_PREFIX + _canonical_json_bytes(signed)` | domain 無し署名が通る | 後段なし | `test_signature_without_domain_prefix_is_rejected` |
| 同 `343` `if type(serial) is not int or serial != line_number:` | 正しく署名された duplicate serial が通る | previous hash は正しく合成可能 | `test_correctly_signed_duplicate_serial_is_rejected` |
| 同 `352` `if previous != expected_previous:` | 正しく署名された wrong previous hash が通る | history prefix は行追加だけを見る | `test_correctly_signed_wrong_previous_hash_is_rejected` |
| 同 `467` `and row["closure_paths"] == expected_paths` | 同 digest・別 path statement が matching receipt になる | path schema/hash は valid | `test_matching_digest_with_different_closure_paths_is_rejected` |
| main `enforcement_source_ratification.py:553` `_assert_full_history_repository(root)` | shallow clone が履歴欠落を隠す | 後段は欠落を知れない | `test_shallow_repository_is_rejected` と v2 counterpart |
| main `511-515` の tree mode condition | JSONを内容にした symlink/gitlink blob が regular ledger 扱いになる | parserだけでは modeを知れない | `test_non_regular_ledger_entries_are_rejected` と v2 counterpart |
| 改訂 receipt の source binding check | reachableだが別 closure の source commit が通る | signatureは正しい | 新 `test_source_commit_must_bind_signed_closure` |
| 改訂 broker の absent-trust rejection | AI鍵の TOFU が復活する | verifierはその鍵を正当 root として受理 | 新 `test_absent_committed_trust_root_never_writes` |
| 改訂 broker の non-TTY rejection | pipe の `y` で署名できる | signatureは完全にvalid | 新 `test_non_tty_cannot_approve` |
| 改訂 broker の control-byte escaping | ESCで人間表示を偽装できる | verifierは検出不能 | 新 `test_control_bytes_are_escaped_before_prompt` |

改訂後に行番号が動く最後 4 件は、段 4 で author commit の exact old bytes を再取得してから登録します。

### 登録しない候補

- receipt `374` の decision check: 無効化しても `468` が同じ `"reject"` を拒否する。
- Ed25519 `82` の canonical-y checkを既存 fixtureだけで殺す案: public subgroupまたは方程式も同じ入力を拒否する。
- Ed25519 `93` の x-zero/sign check: public-key fixtureでは identity checkも拒否する。
- Ed25519 `97-98`: 到達不能。
- Ed25519 `99-100`: reachable inputでは冗長。
- broker `190-196` の remote path tuple check: 最終 v2 verifier の expected-path checkも同じ receipt を拒否する。
- broker `197-199` の digest計算を remote claimへ付け替える変異: final verifier の live digest matchが拒否する。
- `test_signed_field_single_mutation` の decision/path-hash/root-hash casesを signature変異の KILLED node にする案:署名を外しても各専用後段が拒否する。source-commit caseだけが署名層を孤立させます。
- `closure_paths_sha256:367` と `trust_root_sha256:384` は専用 testで殺せますが、コメントどおり診断冗長性です。security matrixではなく schema-contract matrixへ分離します。

## 総括

採るべき着地点は、pure-Python verifier、hooks 配下の canonical trust root と空 signed ledger、DAG-aware だが v2 hash chainに合わせて divergent branchを拒否する verifier、既存 trust/keyしか使えない外部 broker、`contract_loader_binding.py:396` から `ident.py:239` までの live 配線です。

親 provisional の判定は、P1/P2/P3/P4/P6/P7 を条件付き支持、P5 は「DAG substrateのみ支持」、P8 は棄却です。M4(a) は production 欠陥、M4(b) は test 欠陥です。

author 着手前に必要な親確認は 1 点です。AI が read・exec・writeできず、review済み broker bytesを固定できる trusted host/account が実際に存在するか。存在しない場合、同一機同一 uid のコードだけでは D905/D906 を満たせません。