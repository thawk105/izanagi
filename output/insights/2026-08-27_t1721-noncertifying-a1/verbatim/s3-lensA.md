結論から言うと、段 2 の停止判断は正しいです。主張された再包装経路は実在します。ただし「禁止中の 2 ファイルを編集すれば十分」という将来修正案までは証明されておらず、署名または改変不能な同一性束縛も必要です。

## 検査 1: 主張された昇格経路

**判定: real**

| 段 | 判定 | 独立確認した根拠 |
|---|---|---|
| 1. 非認証宣言入り v1 identity | real | `ident.py:150-177` は `search_config` 全体を含む exact 5-key preimage を作る。`ident.py:459-462` は環境契約を要求しない経路でその preimage を v1 lock として書く。現行 A-1 にも既に `promotion_prohibited=True` がある (`paper_story_a1_paired.py:698-714`) |
| 2. 同じ identity を v2 で包む | real | `campaign_lock.py:154-166` は identity の top-level 5 key と `search_config` が object であることだけを検査する。nested marker は見ない。`campaign_lock.py:255-275` は公開 mapping だけから v2 を生成し、署名、process seal、批准 receipt を要求しない |
| 3. artifact admission を通る | real | `artifact_admission.py:987-1116` は committed 25-path map、activation、build policy、WAL topology を検査するが、`promotion_prohibited` や将来の authority class を拒否しない。批准 gate も呼ばない |
| 4. current map 一致で E1 | real | `artifact_admission.py:805-822` が記録 map から E1 を作り、`artifact_admission.py:843-865` が current map との equality だけを要求する。批准集合との照合はない |
| 5. CertifiedCampaignView 発行 | real | admission status と E1 を通れば `artifact_admission.py:1148-1172` が正規 token 付き `CertifiedCampaignView` を発行する |

読み取り専用 probe でも、批准されていない現在の 25-path closure を直接 v2 authority に入れ、既存の `promotion_prohibited=True` を保持したまま activation 検査と certified-purpose E1 を通せました。結果は `E1:ab51c8...` でした。これは pytest ではなく、ファイルを書かない in-memory probe です。

### v2 に実際に必要な材料

**判定: real。非認証 run 専用の秘密や発行 capability は必要ありません。**

- closure commit と 25-path map:
  `contract_loader_binding.py:349-362` の `capture_contract_loader_binding()` で誰でも取得できます。ここは批准を検査しません。批准検査は `ident.py:239` にしかありません。

- activation state:
  `env_contract.py:381-386` と `env_contract_activations/00000001.json:1` に pinned state が公開されています。`env_contract.py:805-838` も current/historical state を公開関数で返します。per-campaign の秘密ではありません。

- build admission:
  現行 pipeline は `pipeline.py:946-1006` で receipt を `build_start` に残します。永続 receipt の検証は構造と hash の自己整合性であり、真正な発行者を認証しないことが `build_admission.py:4-20` に明記されています。さらに空 WAL でも topology 検査は通るため、lock-only E1 や空の certified view には build receipt 自体が不要です。

- WAL topology:
  WAL には hash chain がないことが `wal.py:14-15` に明記されています。artifact reader は `wal.py:749-766` で構文を読み、`wal.py:1150-1308` で attempt topology を見るだけです。通常の producer が COMMIT 時に要求する live verifier capability (`wal.py:447-470`) は、artifact admission の読取経路では再要求されません。

### `contract_sha256` の出所

**判定: real**

非認証 COMMIT から `contract_sha256` を省けば、そのままの v2 再包装は `wal.py:1131-1147` で拒否されます。しかし値は隠されていません。

1. 再包装者が選んだ v2 authority の `environment_contract_sha256` が期待値になります (`wal.py:1116-1120`)。
2. その hash は activation record の active contract 行から取得できます。
3. 同じ値を COMMIT payload に戻せば exact equality を満たします (`wal.py:1134-1142`)。
4. 現在の Pegasus 値は `e576e9cd...e242c01` で、読み取り専用 probe でも同値を使って v2 authority を構成できました。

別 terminal stage にしても stage と field を書き換えられます。D1038 が禁止する「field の除去や付け替えによる昇格」そのものです。

古い verifier receipt は lock hash 変更により replay 専用経路では失敗します。しかし `s6_sort_sweep.py:438-469` と `s8a_trigger_sweep.py:540-571` は正規 view 内の COMMIT/BENCH payload を直接読みます。`s1_report.py:379-395` と `s8b_oracle_report.py:547-558` はさらに WAL admission 前の lock-only E1 だけを使います。したがって replay receipt の失敗は全 consumer を閉じません。

### 成果物への影響

- certified 選択: 非認証 WAL の COMMIT/BENCH 値を certified 候補として読む受理集合が広がります。
- レポート: A-1 自身の `formal=False`、`promotion_prohibited=True` は変わりませんが、その測定値を別の certified report が正規 view 経由で読むことが可能になります。
- 台帳: 再包装により lock/WAL hash は新しくなりますが、新 schema artifact としてその hash がそのまま受理されます。元が非認証だったことを束縛する改変不能な参照は残りません。

## 検査 2: 第 3 の接ぎ目

**判定: real。禁止面を触らずに全経路を閉じる接ぎ目はありません。**

調べた編集可能面と限界は次の通りです。

| 面 | 閉じられる範囲 | 閉じられない理由 |
|---|---|---|
| `ident.py` | full artifact admission の activation 検査で marker を拒否できる | lock-only epoch は `ident.verify_recorded_activation_tuple()` を呼ばない。marker 自体も inner identity から除去できる |
| `wal.py` | full admission の topology 検査で marker/terminal を拒否できる | `require_campaign_verifier_epoch()` は WAL を一切読まない |
| `env_contract.py`, `env_contract_activation.py` | full admission の activation contract を制限できる | activation は campaign identity に束縛されず、lock-only gate は activation を検査しない。global state を失効させると既存 certified も拒否して規律 2 に違反する |
| `layout.py` | official/exploration の producer path を分離できる | artifact admission は任意 path を `CampaignLayout` に戻す (`artifact_admission.py:563-568`)。コピー、移動、marker 除去を防げない |
| `pipeline.py`, `loop.py`, `execution_guard.py`, `guided.py` | 非認証 producer が材料を出さないようにできる | artifact reader は producer API を通らず raw lock/WAL を読む。公開 activation/map と自己整合 receipt から材料を再構成できる |
| `replay.py`, `paper_story_a1_paired.py` | 個別 consumer を拒否できる | S1/S8B lock-only と他の direct-payload consumer が残る |
| `tools/pegasus/`, tests | producer/test の制御 | central certified admission の述語にはならない |

決定的なのは `artifact_admission.py:868-891` の lock-only 経路です。ここは実質的に禁止面の `campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py` だけで E1 を決めます。編集可能な WAL、activation、execution guard を通りません。

4 層別には以下です。

- 鍵: 現行 v2 authority に署名鍵や非公開 capability がない。
- 記録: WAL と永続 receipt は再構成可能で、consumer が live発行 capability を再要求しない。
- schema: lock schema の閉集合は編集禁止の `campaign_lock.py` にある。
- consumer: lock-only E1 と view 発行は編集禁止の `artifact_admission.py` にある。

なお、段 2 が提案した「新 schema と marker 拒否」だけでも十分とはまだ言えません。marker を inner identity から除去して v2 を再生成でき、非-trigger campaign は directory name と inner identity hash の一致を検査しません (`artifact_admission.py:736-752`)。所有解除後も、署名された identity 束縛または全 consumer が参照する改変不能な外部台帳まで設計する必要があります。

### 成果物への影響

完全な第三接ぎ目がないため実装しないのが正解です。部分的な `ident.py`/`wal.py` 拒否だけを入れると、certified 選択、レポート、台帳の受理集合が開いたままなのに「閉じた型」が存在するという、より危険な状態になります。停止中は A-1 の値、レポート行、試行台帳はいずれも増えません。

## 検査 3: 親 brief

### P1-P5

| 主張 | 判定 | 根拠と影響 |
|---|---|---|
| P1: 既存 closure file 内だけで閉じる | refuted | full admission の部分拒否は可能だが lock-only gate を閉じられない。新 module 不要という制約自体より、既存編集可能面だけで完結するという前提が成立しない |
| P2: 判定の座は `ident._capture_current_loader_binding` | refuted | 批准 producer の座としては正しいが、再包装 consumer の座ではない。直接 `capture_contract_loader_binding()` と v2 encoder を使えば迂回できる |
| P3: 宣言を CampaignConfig identity に入れる | real | `model.py:66-84` と `ident.py:150-189` が適切な場所。default を serialize せず、非defaultだけ reserved key に入れる方式なら既存 ID は保存できる。ただし昇格不能性は得られない |
| P4: submit script + receipt writer | 根拠不足 | job body は自らを submitter でないと明記し (`paper_story_a1_paired.sh:7-9`)、60 秒以内の receipt を要求する (`:87-98`)。二機能が必要なのは real だが、二ファイル構成が唯一または実機動作可能とは静的検査だけでは証明できない |
| P5: 実 qsub を行わない | 根拠不足 | scope としては可能だが、実機動作済みという完了根拠にはならない。実 qsub がなければ A-1 の値、レポート、submission/completion 台帳はゼロのまま |

### M1-M8

| 測定 | 判定 | 根拠 |
|---|---|---|
| M1 | real | `submit_*.sh` は 8 本、A-1 submitter は 0 本。A-1 schema は定義・validator・job consumer にだけ存在する |
| M2 | real | production の `verify_ratified_contract_loader_binding()` 呼出しは `ident.py:239` の 1 件。下位 `require_ratified_closure()` の production 呼出しも wrapper 内の 1 件だけ |
| M3 | real | current closure digest は `a14a2612...90ab3`、台帳行は `db511c3d...eea44`。読み取り専用 probe は exact `enforcement-source-closure-unratified` で拒否された |
| M4 | real | `campaign_lock.py:29-55` は exact 25 path。`ident.py`、`pipeline.py` を含み、A-1 driver、`layout.py` を含まない |
| M5 | real、ただし記述の一部 refuted | `declared_use_class` が `CampaignConfig` と identity に無い結論は正しい。反面「pipeline と layout にしかない」は誤りで、`loop.py:242-263`、`buildcache.py:2009-2071`、複数 driver にもある |
| M6 | real | `conftest.py:194-236` は `@pytest.fixture` で autouse 指定なし。temporary repo を `ratification._REPO_ROOT` に差す |
| M7 | 根拠不足 | 現在の t1629 branch diffでは、禁止面との衝突と主要な許可 core file の非重複は確認できた。ただし親の「全 branch」と未列挙の「対応 test」までの素集合性は brief から証明できない |
| M8 | 根拠不足 | 親 brief の測定表は M1-M7 までしかなく、M8 行が存在しない (`s1-brief.md:28-38`) |

### campaign ID の裁定

親の「reserved `search_config` key を入れても ID が変わらない」という字面は **refuted** です。`ident.py:166-177` は `search_config` の全 key/value を preimage に入れるため、key を追加すれば hash は変わります。

Pegasus A-1 configへの読み取り専用計算結果は次の通りでした。

| workload | 現行 ID | `authority_class=noncertifying` 追加後 |
|---|---|---|
| write-heavy | `...-fb4d1867` | `...-6a29440b` |
| balanced | `...-38177551` | `...-e841ab12` |
| read-heavy | `...-e8aab893` | `...-07491d29` |

したがって正しいのは段 2 の条件付き serialization です。

- 既存 certified config: default field を canonical preimage に出さないので ID 不変。
- 新規 noncertifying config: reserved key を出すため ID は変化。
- A-1 report: exact `search_config` key 集合を検査する `paper_story_a1_paired.py:2037-2051` の変更が必要で、result/receipt 内の campaign ID 参照も新 ID になります。
- certified 選択: default omission 自体は既存の受理集合を変えません。ただし、この identity 変更だけでは再包装を防げません。

Web 検索、pytest、ファイル書込みは行っていません。実施した動的確認は、closure digest、in-memory v2/E1、campaign ID の読み取り専用 probe だけです。テスト結果を緑とは報告していません。

## 総括

段 2 の停止結論は正しい。