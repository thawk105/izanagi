artifacts: 12
job_total_seconds: min=135.9 med=137.2 max=138.7
distinct (cell, workload, threads): 18

== cw-as-dyn-p0 balanced 24t  runs=12
   events/run: min=880 med=924 max=945
   trigger: {'cap': 12, 'count': 11006}
   window_us: min=2560 p50=2562 p90=5125 p99=5128 max=23768
   window_commits: min=0 p1=10016 p50=10283 max=20988
   zero-commit events: 10
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=19875 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=21335 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=15663 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=15235 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=21396 trigger=cap

== cw-as-dyn-p0 balanced 48t  runs=12
   events/run: min=1012 med=1053 max=1088
   trigger: {'cap': 12, 'count': 12614}
   window_us: min=2560 p50=2562 p90=5122 p99=5133 max=65454
   window_commits: min=0 p1=10072 p50=11396 max=37937
   zero-commit events: 9
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=41978 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=44679 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=47511 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=46763 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=33972 trigger=cap

== cw-as-dyn-p0 read-heavy 24t  runs=12
   events/run: min=1155 med=1163 max=1167
   trigger: {'cap': 12, 'count': 13934}
   window_us: min=2560 p50=2561 p90=2563 p99=2566 max=22191
   window_commits: min=0 p1=14804 p50=15494 max=31373
   zero-commit events: 7
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=22191 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=20750 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=15241 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=19650 trigger=cap
      stage2-rep0-0_981444.nqsv.json seq=0 window_us=20336 trigger=cap

== cw-as-dyn-p0 read-heavy 48t  runs=12
   events/run: min=1151 med=1155 max=1161
   trigger: {'cap': 12, 'count': 13850}
   window_us: min=2560 p50=2562 p90=2564 p99=5121 max=46059
   window_commits: min=0 p1=19850 p50=26876 max=56912
   zero-commit events: 8
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=46059 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=38136 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=34914 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=32737 trigger=cap
      stage2-rep0-0_981444.nqsv.json seq=0 window_us=38087 trigger=cap

== cw-as-dyn-p0 write-heavy 24t  runs=12
   events/run: min=666 med=1003 max=1066
   trigger: {'cap': 12, 'count': 11547}
   window_us: min=2560 p50=2562 p90=5124 p99=5128 max=22233
   window_commits: min=0 p1=10011 p50=10396 max=21642
   zero-commit events: 9
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=21985 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=15247 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=22233 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=15200 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=19217 trigger=cap

== cw-as-dyn-p0 write-heavy 48t  runs=12
   events/run: min=748 med=869 max=894
   trigger: {'cap': 12, 'count': 10216}
   window_us: min=2560 p50=2566 p90=5131 p99=5142 max=71948
   window_commits: min=0 p1=10018 p50=10751 max=39644
   zero-commit events: 7
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=38086 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=41904 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=32832 trigger=cap
      stage2-rep0-0_981442.nqsv.json seq=0 window_us=34529 trigger=cap
      stage2-rep0-0_981468.nqsv.json seq=0 window_us=33827 trigger=cap

== cw-as-dyn-p1 balanced 24t  runs=12
   events/run: min=295 med=301 max=316
   trigger: {'cap': 213, 'count': 3414}
   window_us: min=2562 p50=10486 p90=10702 p99=10927 max=23170
   window_commits: min=0 p1=9338 p50=11268 max=19960
   zero-commit events: 11
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=21925 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=19283 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=21586 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=15212 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=15226 trigger=cap

== cw-as-dyn-p1 balanced 48t  runs=12
   events/run: min=372 med=404 max=524
   trigger: {'cap': 12, 'count': 4983}
   window_us: min=2560 p50=7893 p90=8152 p99=10789 max=65343
   window_commits: min=0 p1=10041 p50=11366 max=24302
   zero-commit events: 8
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=33957 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=46592 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=33225 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=45951 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=34248 trigger=cap

== cw-as-dyn-p1 read-heavy 24t  runs=12
   events/run: min=580 med=581 max=595
   trigger: {'cap': 12, 'count': 6976}
   window_us: min=2560 p50=5214 p90=5370 p99=5519 max=33537
   window_commits: min=0 p1=10480 p50=12535 max=28508
   zero-commit events: 7
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=21095 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=21386 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=33537 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=22515 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=15725 trigger=cap

== cw-as-dyn-p1 read-heavy 48t  runs=12
   events/run: min=631 med=661 max=742
   trigger: {'cap': 12, 'count': 7997}
   window_us: min=2560 p50=5216 p90=5425 p99=5599 max=50565
   window_commits: min=0 p1=10053 p50=16431 max=52628
   zero-commit events: 9
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=34008 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=34181 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=33932 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=35599 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=50565 trigger=cap

== cw-as-dyn-p1 write-heavy 24t  runs=12
   events/run: min=369 med=387 max=392
   trigger: {'cap': 12, 'count': 4595}
   window_us: min=2560 p50=7867 p90=8079 p99=10691 max=23319
   window_commits: min=0 p1=10034 p50=11296 max=20151
   zero-commit events: 9
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=19606 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=23319 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=15245 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=21548 trigger=cap
      stage2-rep0-0_981442.nqsv.json seq=0 window_us=15219 trigger=cap

== cw-as-dyn-p1 write-heavy 48t  runs=12
   events/run: min=541 med=550 max=561
   trigger: {'cap': 13, 'count': 6586}
   window_us: min=5120 p50=5125 p90=7685 p99=10243 max=75557
   window_commits: min=0 p1=10114 p50=13510 max=22852
   zero-commit events: 9
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=34283 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=75557 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=33664 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=44084 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=33915 trigger=cap

== cw-as-dyn-p2 balanced 24t  runs=12
   events/run: min=351 med=480 max=643
   trigger: {'cap': 12, 'count': 5910}
   window_us: min=2560 p50=5140 p90=7813 p99=10532 max=25704
   window_commits: min=0 p1=10022 p50=12579 max=20287
   zero-commit events: 11
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=22754 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=21442 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=22787 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=21383 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=19419 trigger=cap

== cw-as-dyn-p2 balanced 48t  runs=12
   events/run: min=593 med=671 max=782
   trigger: {'cap': 12, 'count': 8153}
   window_us: min=2560 p50=5135 p90=5186 p99=5438 max=65722
   window_commits: min=0 p1=10065 p50=12656 max=24770
   zero-commit events: 8
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=34551 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=30257 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=37905 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=65722 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=34202 trigger=cap

== cw-as-dyn-p2 read-heavy 24t  runs=12
   events/run: min=593 med=792 max=950
   trigger: {'cap': 12, 'count': 9461}
   window_us: min=2560 p50=2583 p90=5187 p99=5297 max=22609
   window_commits: min=0 p1=10060 p50=14926 max=31114
   zero-commit events: 10
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=20452 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=22609 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=15492 trigger=cap
      stage2-rep0-0_981432.nqsv.json seq=0 window_us=20180 trigger=cap
      stage2-rep0-0_981442.nqsv.json seq=0 window_us=15219 trigger=cap

== cw-as-dyn-p2 read-heavy 48t  runs=12
   events/run: min=1091 med=1156 max=1166
   trigger: {'cap': 12, 'count': 13756}
   window_us: min=2560 p50=2563 p90=2616 p99=5125 max=64364
   window_commits: min=0 p1=10329 p50=15729 max=57387
   zero-commit events: 8
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=34641 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=34412 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=34196 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=32805 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=64364 trigger=cap

== cw-as-dyn-p2 write-heavy 24t  runs=12
   events/run: min=482 med=594 max=665
   trigger: {'cap': 12, 'count': 6953}
   window_us: min=2560 p50=5132 p90=7685 p99=7867 max=34334
   window_commits: min=0 p1=10023 p50=13268 max=21239
   zero-commit events: 11
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=21832 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=21036 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=21847 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=34334 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=15751 trigger=cap

== cw-as-dyn-p2 write-heavy 48t  runs=12
   events/run: min=555 med=617 max=671
   trigger: {'cap': 16, 'count': 7439}
   window_us: min=2560 p50=5139 p90=5206 p99=7709 max=75414
   window_commits: min=0 p1=10042 p50=15005 max=26418
   zero-commit events: 9
      stage2-rep0-0_981402.nqsv.json seq=0 window_us=46761 trigger=cap
      stage2-rep0-0_981411.nqsv.json seq=0 window_us=32672 trigger=cap
      stage2-rep0-0_981417.nqsv.json seq=0 window_us=63448 trigger=cap
      stage2-rep0-0_981424.nqsv.json seq=0 window_us=33874 trigger=cap
      stage2-rep0-0_981429.nqsv.json seq=0 window_us=34681 trigger=cap
