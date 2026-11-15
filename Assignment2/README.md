# CSA15 Assignment 2 (CO2) - Virtualization architecture analysis

Student: Lohithaksha D (1921260275), B.Tech IT, SIMATS Engineering

| Folder | Contents |
|---|---|
| Task8_scripts | .wslconfig, Dockerfile, cloud-init files and the benchmark scripts (sysbench, fio, iperf3, stress-ng, syscall test, QEMU VM tests) |
| Task9_results | raw CSV / JSON / log output of the runs |
| report | Word report with the model, the results and the screenshots |

Tested: runc containers, gVisor (runsc) containers, and QEMU VMs.

Limits (same as in the report)
- WSL2 has no KVM, so the VM approach was measured in QEMU software emulation (TCG). It does not show the real cost of a hardware-assisted VM; KVM numbers in the report are model predictions only.
- Scale was reduced where the 9 GB RAM budget required it (VMs up to 4, network pairs up to 8).
