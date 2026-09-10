# A-6 read-heavy 同一 workload 認証 — 初めて測定が取れ、判定は reject

## 結論

**attempt `a6-20260908b` の認証判定は `reject` である。** read-heavy において、
採用版 backoff は **正しさを保つが性能では stock に負ける**。

- outer certification status: `reject`
- effects: `{"rr95": -0.057841193339621455}` (**採用版は stock より 5.78% 遅い**)
- correctness: 2 cell とも `certified` (legacy 1 回 + 本走 5 回、すべて `pass`)

**論文 §8 の但し書き 2 のうち、正しさの側は外挿でなくなった。** これまで read-heavy は
「backoff は正しさに影響しない」という機序論証による外挿だったが、実測で確かめられた。
一方**性能の側は支持されなかった**ので、read-heavy へ採用版を広げる主張はできない。
「証拠が支持しなければ stock を正直に選ぶ」の形どおりの結果である。

| cell | genome | 正しさ | 性能中央値 (txn/s) |
|---|---|---|---:|
| `rr95-stock` | `BACK_OFF=0, BACKOFF_FIXED=-1` | certified | 10,088,796 |
| `rr95-fixed2` | `BACK_OFF=1, BACKOFF_FIXED=2` | certified | 9,505,248 |

生の 5 標本は stock `[10365808, 10103030, 10029940, 10088796, 10073679]`、
採用版 `[9753031, 9587735, 9488225, 9494008, 9505248]`。母標準偏差を中央値で割った値は
stock 1.18%、採用版 1.06% で、**5.78% の差はこのばらつきより大きい。**

## 実行 identity

- attempt: `a6-20260908b`
- request: `982234.nqsv` (Created 01:28:55 / Started 01:29:06 / Ended 02:42:03 JST、Elapse 4382 秒)
- source commit: `ae8a767eb60118c3f9791141603fa01ad4f28406`
- CCBench pin: `511c953`
- protocol SHA-256: `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`
- certification SHA-256: `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab`
- durable authority:
  `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/`
- 公開成果物: `output/insights/2026-09-08_t2411-paper-story-a6-certification/`

### policy bytes は測定後に 1 key だけ変えた — 明記する

走行時の policy bytes SHA-256 は `8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8`、
公開された `certification.json` が持つのは
`96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a` である。
差は `tracked_destination` の 1 key だけで、**`_protocol_preimage` に含まれないため
`protocol_sha256` は前後で同一**である (実計算で確認)。何を測ったかは変わっていない。

変えた理由は、公開先が 2026-09-02 の失敗時に手で書いた README で既に埋まっており、
`collect` が空の新しい leaf を要求して止まったためである。**旧 policy bytes で走った事実は
この追記で残す** — 事前登録の policy SHA は下流の受領証の必須 field に無いので、
機械的には照合されない (この射程の限界は 2026-09-02 の記録が既に挙げている)。

## 前回はどこで止まり、今回は何を直したか

前走 `a6-20260902a` は計算ノードの条件 gate が cell-0 を拒否し、campaign が始まる前に
driver が非 0 終了した (測定 0 点)。その原因はオフライン依存の配線不足で、worklog 1326 が
staged 依存へ配線し直している。

本 wave の 1 回目の投入 (`a6-20260908a`、request `982055.nqsv`) は**その壁を越えた**が、
36 秒で別の場所で止まった。

```
paper-story A-2 indeterminate: [Errno 22] Invalid argument:
  '<attempt>/receipts/condition-gate-rr95.admissions.jsonl'
```

**この地点への到達は、条件 gate が 2 cell とも受理したことを含意する。** 当該 path を書くのは
`paper_story_a2_certification.py` の `_write_condition_gate_admissions_x` だけで、そこへ
到達するには staged 依存での CMake 準備と 2 cell 分の `require_condition_gate_family(...).admitted`
が済んでいる必要がある (拒否時は `condition gate rejected paper workload cell-N` で止まる)。

### 根本原因 — Lustre には `renameat2(RENAME_NOREPLACE)` が無い

ログインノードで実測した。

| filesystem | `renameat2(RENAME_NOREPLACE)` |
|---|---|
| `/work` (lustre) | rc=-1 errno=22 EINVAL |
| `/home` (lustre) | rc=-1 errno=22 EINVAL |
| `/tmp` (ノード内蔵) | rc=0 |

`_atomic_write_bytes_noreplace` はこの呼び出しだけを持ち、代替経路が無かった。
同じ file の materialize 経路は commit `5dcea6e56` で既に代替を持っており、
**兄弟の writer 1 箇所だけが取り残されていた。**

### 修復 — `os.link` で、上書き禁止を弱めずに直す

`os.link` は同じ lustre 上で成功し、既存名には EEXIST を返す (実測)。regular file なら
**原子的な create-only publish を弱めずに実現できる。** `orchestrator/calibrator/cli.py` が
同じ選択を既に採っている。directory を publish する materialize 側が弱い代替
(claim + 存在検査) を使っているのは、link が directory に使えないためである。

- 落とす errno は `{EINVAL, ENOSYS, ENOTSUP}` に限る。それ以外はそのまま伝播する。
- `os.link(..., follow_symlinks=False)` を明示する。
- **link 成功時点で publish 完了**とみなし、staging の後始末は best-effort とする。

最後の 1 点は段 3 のレンズ A が出した実在の反例への対応である。main 側が先に着地させていた
修復は `published = True` を後始末の**後ろ**で立てており、link 成功後に unlink が失敗すると
**publish 済みなのに関数が失敗し、再実行が `EEXIST` で永久に拒否される。** これは成立するはずの
走行を indeterminate にする方向の誤りなので直した。

### main 側の独立修復との合成

本 wave の実装中に、main 側の別 wave (commit `31ec382a7`) が同じ欠陥へより弱い修復を
先に着地させていた (EINVAL のみ、`follow_symlinks` 指定なし、`published` の位置が後ろ)。
受入の post-claim merge が `stage=merge rc=70 source_rc=1` で競合し、Codex `role=author` の
合成子に両者を合成させて親が merge を確定した (`5c3c7e658`)。production は本 wave の形を採り、
テストは両 wave の 7 本すべてを保持している。main 側の link 観測 stub は
`follow_symlinks` を受け渡せるよう最小限だけ調整した。

## 変異 matrix

合成後 tip (`5c3c7e658`) で 4/4 KILLED、SURVIVED 0、MISMATCH 0、baseline PASSED。
**期待 node と実測 node は完全一致した。**

| ID | 変異 | 落ちた node |
|---|---|---|
| M1' | 許可 errno から `ENOSYS` を外す | `..._unsupported_rename_uses_link_unlink[38]` |
| M2 | `EACCES` を代替経路へ入れる | `..._nonfallback_errno_propagates` |
| M3' | destination 既存時に先に消してから link する | `..._einval_hard_link_refuses_existing_name`、`..._einval_refuses_existing_destination` |
| M4 | 後始末の失敗を伝播させる | `..._link_publish_survives_unlink_error` |

事前登録の訂正が 2 件ある (erratum)。初回登録の M1「代替分岐を削除」と M3「`os.replace` へ置換」は、
段 6 レビュー B が実装後の現物に対して**単独帰属が成立しない** (それぞれ 3 本・3 本のテストが
同時に落ちる) ことを示したため、上の M1' / M3' へ再照準した。`DW-M01` の
「単独理由性が確認できなければ登録せず実効 gate へ再照準する」に従った。

M3' が 2 node を落とすのは、**同じ上書き禁止の性質を両 wave のテストが独立に検査している**ためで、
層による mask ではない。

登録から外したもの: `follow_symlinks=False` の除去。現環境では Linux の `os.link` が既定でも
symlink を辿らないと**実測**したので受理集合を変えない。T1 が引数を明示検査しているため
テストからは区別されるが、`DW-M08` に従い kill ではなく診断用の pin として別枠に置く。

## 所要の内訳 — 直列なのは正しさ検査である

campaign WAL の時刻差から、cell あたりの内訳は次のとおり。

| 工程 | 所要 |
|---|---|
| ビルド | 15 秒 |
| 正しさ検査 (legacy) | 17 秒 |
| **正しさ検査 (本走) 5 回** | **約 7 分 × 5** |
| 性能計測 | 17 秒 |

2 cell 合計 約 73 分のうち、**約 70 分が正しさ検査**である。ビルドでも性能計測でもない。
各検査は 48 スレッドを使い切るので 1 ノード内では並べられない。

**投入器は workload 単位では既に分割している** (A-2 は rr5 / rr50 で 2 job)。直列なのは
workload の内側である。`docs/pegasus-runbook.md`「ノード間の性能差は未測定である」節に従えば、
分割禁止の根拠にしてよいのは**処置とノードの一対一割付け (完全交絡)** だけであり、それは
量を比べる計測にだけ効く。**真偽値を返す正しさ検査には効かない。** したがって正しさ検査は
ノードへ割ってよい。

実際の障害は別にある — 認証は `perf_bin_sha256` を実ファイルと照合するので、検査を別ノードで
走らせるには同一 bytes の実行ファイルが要る。ノードを跨いで建て直すと bytes が変わることは
2026-09-02 に実測済みである。**これは「技術的に不可能」ではなく「現行 protocol では禁止」に
当たり、裁定で解ける。** 次の一手に置く。

## 主張の上限

1. **性能の差は 1 attempt・5 標本の中央値比較である。** 反復 attempt も別ノードでの再現も
   取っていない。`a4_noise_floor_status` は `open`、
   `global_minimality_established` は `false` のままである。
2. **`-5.78%` は read-heavy のこの 1 点 (rratio 95 / 48 thread / zipf 0.9 / extime 3) の値**で
   あって、read-heavy 一般の値ではない。他の read 比率へ外挿しない。
3. **正しさの certified は「この protocol の検査が通った」であって、実装が正しいことの証明では
   ない。** 検査自身の射程は既存の記録に従う。
4. **link と unlink の間で process が死ぬと staging の別名が残る。** 1 関数の局所修復では
   消せず、単一 syscall で無名 inode を publish する別 primitive が要る (scope 外)。
   consumer は destination の正確な名前しか見ないので、成果物の値も参照も変わらない。
   **この限界は主張せず明記する** (絶対規律 7)。
5. **`collect` は投入した checkout から実行する必要がある。** 投入時に記録した policy の
   絶対 path と、実行時に解決した policy の path を突き合わせるためで、記録用 worktree から
   実行すると `qsub -v is not bound to workload and current pin` で止まる。
   既存 A-2 の受領証が現配置で再検証できない件と同じ族である。
6. **本 wave の親の言い方 2 件を段 3 レンズ B が訂正した。** 受理証跡の path を作る helper の
   呼出しは 6 箇所あり (production writer は 1 箇所)、また job body の EXIT trap も
   `ln` による create-only publish なので「repo 全体で no-replace publish は 2 箇所」は
   広義には偽である。正しくは「`paper_story_a2_certification.py` 内で `_rename_noreplace` を
   呼ぶ publish が 2 箇所」。

## 段 6 レビュー

敵対レビュー 2 本とも実装への must-fix はゼロだった。nit 5 件のうち 3 件は変異証拠の帰属に
ついてで、上の erratum で対応した。残り 2 件 (例外の同一性検査が bare re-raise の構文までは
識別しない、T4 単体では unlink の試行そのものを証明しない) は成果物の値・受理集合・参照を
変えないので `DW-G05` により nit のまま fix していない。

## 検査

- 焦点走: 241 passed (`test_paper_story_a2_certification.py`、`test_paper_story_a2_job_contract.py`、
  `test_plot_a2_certification.py`)
- 受入全走: `child-green`、`child_rc=0`、赤ゼロ
- provenance 全史監査: 8636 件、新規違反なし
