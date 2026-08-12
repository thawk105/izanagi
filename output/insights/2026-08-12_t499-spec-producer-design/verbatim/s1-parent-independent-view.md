# 親の独立見解 (段 2 出力を読む前に固定、2026-08-12 23:12 JST)

子の出力を読む前に書いた。後で子の結論と突き合わせ、一致/不一致を段 4 裁定に書く。

## D302 択一についての親の読み

### 択一の立て方そのものが誤っている可能性 (最重要)

「据え置き解除か再発行か」という問いは、**contract test が schema version で分岐しない**
(`test_s8b_oracle_manifest_contract.py:128-144`) 以上、どちらを選んでも同じ test が落ちる。
したがってこれは schema version の択一ではなく、**「durable 発行 0 件」という前提を
いつ・どう手放すか**の問題である。

D302 の却下理由は「schema version を上げる — durable 発行 0 件を機械確認したうえで据え置く。
durable 発行後にこの決定を変えるなら再発行が要る」。これを素直に読むと順序契約である。

- 発行 0 件のあいだは schema を自由に変えてよい (誰も v1 の durable bytes を読んでいない)。
- 発行後に schema を変えるなら version を上げる必要がある。

よって**今 v2 へ上げる動機はゼロである。** v1 durable artifact は 1 件も存在せず、
守るべき互換性が無い。上げれば `s8b_oracle_spec.py:18` と fixture・test・docs の pin を
触るコストだけが増え、受理集合は 1 bit も変わらない。

**親の独立推奨 = 選択肢 A (v1 据え置き)。** ただし発行するときは、
zero-file assertion を「発行 0 件」から「発行済み bytes が承認 pin と完全一致し、
それ以外のファイルが存在しない」へ**置換する**必要がある。これは実装であり本 wave の scope 外。

### 置換は「緩め」か

受理する状態集合で見ると、0 件 ⊂ {承認 pin と一致する 1 件} なので**形式的には広がる**。
これを「規律 2 違反ではない」と言えるのは、次が同時に成立する場合だけである。

1. 広がる先が、承認された bytes ちょうど 1 通りに限定されている (pin との完全一致)。
2. 広げる判断が実装者ではなく**ユーザーの明示裁定** (新しい D) として記録される。
3. 広げた後も「未承認の durable artifact が存在しない」ことは機械検査され続ける。

この 3 点を満たさない置換案が出てきたら refuted とする。
「意図は同じだから緩めていない」という説明だけの案は採らない。

### この test は本走の阻止器でもある

`build_approved_manifest` は `output/s8b-oracle-manifest-candidates/` 配下にしか書けず
(`_candidate_output_parts:882-892`)、同じ assertion がその dir も見ている。
つまり **spec を承認して本走すると manifest candidate を出した時点で必ず赤になる。**
この test は D302 の番人であると同時に、8b oracle 本走そのものの阻止器として働いている。
番人としての意図と、阻止器としての実効は分けて書く必要がある。

## producer 設計についての親の読み

### provenance の要求は現状ゼロ

`_load_approved_spec_bytes:182-200` は bytes hash pin だけを見る。git を一切見ない。
`_assert_user_commit` は freeze v2 専用 (`s8b_ratified_freeze.py:537`、呼び手 4 か所すべて同 module)。
裁定控えの「`_assert_user_commit` の要求を満たす形で配置する」は前提の取り違えである。

3 択で提示する。

- (i) 現状維持 (code pin のみ)。承認の実質は「pin を書く diff を人間が review すること」。
  最も安いが、承認の痕跡が git message に残らない。
- (ii) T-810 と同型の receipt を足す (`t810_preregistration.py` の
  `ApprovalReceipt` + `APPROVAL_RECEIPT_SCHEMA_VERSION`)。先例があり、既に動いている。
- (iii) `_assert_user_commit` 相当を spec 経路へ足す。最も強いが、逐語 `AI-Agent: none` は
  誰でも書けるため、**防ぐのは「うっかり AI が承認 record を作る」ことであって
  意図的偽装ではない**。この限界を書かずに (iii) を勧めるのは恒真な保証の再導入に近い。

**親の独立推奨 = (i) を既定とし、(ii) を別タスク候補として提示する。** (iii) は
freeze v2 側と対称にする価値はあるが、本 wave の設計提示に留め、実装は勧めない。

### 承認は数日で自壊する

`generator_versions` は production source 5 本の実 byte hash を pin する
(`s8b_oracle_manifest.py:53-61`)。この 5 本は直近 30 日で 40 commit、直近 14 日で 20 commit
変更されている。**承認した spec は、次にこの 5 本のどれかを触った瞬間に無効化される。**

これは producer 設計の中心的制約である。結論として、

- spec の承認は「この 5 本が実質凍結された後」でなければ意味を持たない。
- 逆に言えば、**承認手番を今引く判断 ([T-499] Q1 = (b)) は正しかった。**
- 「無効化されにくくする」方向 (hash pin を緩める、path pin だけにする) は規律 2 違反。提案しない。

## 事前登録値の可決可能性についての親の読み

9 項目を、AI が今導出できるか否かで分類する。

| 項目 | 今 AI が決められるか | 根拠 |
|---|---|---|
| `run_contract.verify` | 決められない (値が 1 つに固定) | `legacy+s2` 完全一致 (`:399`) |
| `run_contract.screening` | 決められない (固定) | `off` 完全一致 (`:401`) |
| `run_contract.bench_max_rounds` | 決められない (固定) | `1` 完全一致 (`:415`) |
| `run_contract.reps` / `extime` | 決められない (固定) | 5 / 5 (`s8b_experiment_numbers.py:14-15`) |
| `run_contract.env_tag` / `clocks` / `contract_sha256` | env を選べば決まる | pegasus=2100 / `e576e9cd...`、baremetal=1800 / `1b2ee853...` |
| `run_contract.ccbench_pin` | 決まっている | `511c953` (submodule gitlink 一致) |
| `allowed_excluded_reasons` | 決まっている | 承認凍結 4 件 (`competing_process`, `launch_failure`, `nonfinite_or_partial_output`, `performance_anomaly`) |
| `generator_versions` | 導出できるが**即座に陳腐化** | 5 本の byte hash、直近 14 日 20 commit |
| `n` / `block_sizes` | **AI が設計判断できる** | `sum(block_sizes) == n` のみ (`build_schedule:238`) |
| `master_seed` | **AI が設計判断できる** | identifier であればよい (`:228`) |
| `campaign_ids` | **AI が設計判断できる** | block と一対一・重複なし (`s8b_oracle_spec.py:147-158`) |
| `holdout_ids` | **導出不能** | active freeze の全 holdout と一致必須 (`build_approved_manifest:1193-1200`)、freeze v2 不在 |
| `configuration_ids` | **導出不能** | holdout ごとの構成集合と一致必須 (`:1206-1211`)、同上 |
| `binding_identity` | **導出不能** | schedule cell と一対一で freeze から決まる (`:487-532`) |

**結論: 実質的な設計自由度があるのは `n` / `block_sizes` / `master_seed` / `campaign_ids` の
4 項目だけである。** 残りは (a) validator が 1 値に固定、(b) 環境選択で決まる、
(c) freeze v2 が無いと導出不能、のいずれか。

したがって承認パッケージは「9 項目を承認してください」ではなく、
**「4 項目の設計判断 + 環境の選択 + 残りは freeze v2 待ちで空欄」**という形にしかならない。
空欄を推測で埋めない (規律 3: 正しさシグナルを後付けにしない)。

## 親が予想する子の弱点

- 子は `holdout_ids` / `configuration_ids` / `binding_identity` に**それらしい値を書いてしまう**
  可能性が高い。validator を読まずに「草案だから」で埋めたら refuted。
- 子は D302 択一を「v1 据え置き vs v2 再発行」の二者択一として素直に答え、
  **どちらでも同じ test が落ちる**ことに気づかない可能性がある。
- 子は contract test の置換を「意図は同じ」で正当化する可能性がある。受理集合の包含で論じさせる。
