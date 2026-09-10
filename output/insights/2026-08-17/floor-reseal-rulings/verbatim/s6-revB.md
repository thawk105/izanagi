### 同一 contract 2 件で certified writer admission が停止する

- 深刻度: major
- file:line: [s8b_floor_campaign.py:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:882)、[certified_writer_admission.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:201)、[floor_campaign.sh:954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/tools/pegasus/floor_campaign.sh:954)
- 失敗筋: 同一の現行 contract に pin 違いの record が 2 件あると resolver は `count=2` で失敗し、admission は `AdmissionRejected` へ変換する。これは fail-closed であり、shell の固定 legacy path を使う driver には到達しない。現時点の fail-open はない。
- 成果物影響: 実 artifact 発行後は床値 submit の受理集合が空になり、pilot result、レポート、試行台帳が新規生成されなくなる。
- 提案する修正: 本差分で resolver だけを変更してはならない。T-1255 の実発行前に、T-419(3) の shell・driver・固定 path consumer 配線と resolver の選択意味論を同一変更で着地させる。2 件状態の admission 拒否と driver 未到達を確認する統合テストもその変更へ追加する。
- 判定上の扱い: 段 4 が明記した既知の fail-closed 残件であり、本 wave は実 artifact を発行しないため、このコード land 自体の blocker とはしない。実発行だけを先行するなら NO-GO。

### 全 scan consumer の確認

`scan_floor_protocol_index` の結果を使う実装経路は全件確認した。

- resolver: 上記のとおり 2 件で fail-closed。
- reseal 発行前: [s8b_floor_campaign.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:940) で exact pair だけを拒否する。異なる pin は意図どおり受理。
- publish 後: [s8b_floor_campaign.py:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:1045) は full index を再走査し、target の path と bytes を再確認する。発行前拒否による恒真化や到達不能化はない。[test_s8b_protocol_builder.py:815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:815) も 2 回目 scan から target を落とすと赤になるため、検査は生きている。
- `check-protocol-index` CLI: [s8b_floor_campaign.py:6705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:6705) は複数 record を列挙するだけで、破損しない。

### launch certificate・freeze の波及

追加所見はゼロ。

- freeze allowlist は versioned path を明示的な chain record として受理する。[s8b_floor_campaign.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:271)、[s8b_floor_campaign.py:3845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3845)
- 追加 record により `clean_scan_digest` と新規 launch certificate hash は変わるが、journal・result 側の参照も同じ新規 certificate に束縛されるため不整合にはならない。
- ratified freeze の full scan は追加 path を列挙 digestへ含めるが、canonical protocol は holdout 軸 hit を増やさないため赤にならない。[s8b_ratified_freeze.py:3299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:3299)
- `FROZEN_MANIFEST` は列挙済み 23 key の bytes 検査であり、未登録 versioned file の存在だけでは赤にならない。

### 既存テストの巻き添え

所見ゼロ。変更された三つの旧 test 名・旧 error 逐語に対する外部参照はない。指定された 4 file 外では `test_campaign.py` の admission テストだけが resolver を参照するが、singleton fixture または mock record を使うため本差分では赤にならない。pytest は指示どおり実走していない。

### 最終判定

**GO**。ただし、これは段 4 の「実 artifact を発行しない」という境界込みの判定である。T-419(3) と resolver の原子的配線より先に T-1255 の実発行を行う場合は **NO-GO**。

## 総括

現差分に fail-open 回帰はない。  
publish 後 full index 検査は到達可能で、実効性も維持されている。  
複数 record は launch certificate、freeze allowlist、ratified freeze を新たに赤くしない。  
唯一の実質的波及は certified writer admission の fail-closed 停止であり、段 4 記載の既知残件と一致する。  
コード land は GO、consumer 配線前の実 artifact 発行は NO-GO とする。