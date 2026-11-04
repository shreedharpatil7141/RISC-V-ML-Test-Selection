# Vivado 2026.1 Project Setup

No `.xpr` is committed: a hand-written .xpr would be invalid. Create it from Vivado:

## GUI method
1. Extract the project to `C:\RISC-V-ML-Test-Selection`.
2. Open Vivado 2026.1 -> *Create Project*.
3. Name: `RISC_V_ML_Verification`, location: `C:\RISC-V-ML-Test-Selection` (uncheck "Create project subdirectory" so the `.xpr` lands in the root).
4. Project type: *RTL Project*; tick "Do not specify sources at this time".
5. Part: any (e.g. xc7a35tcpg236-1); no hardware is used.
6. After creation: *Add Sources -> Add or create design sources*, add `rtl/` (use *Add Directories*, enable "Scan and add RTL include files", do not copy sources).
7. *Add or create simulation sources* -> add `verification/` and `tests/` (simulation set `sim_1`).
8. Set file type to SystemVerilog for `.sv` files; confirm `Settings -> Simulation -> xsim`.
9. Set compile order manually if Vivado's auto-order is wrong: packages first (see `documentation/architecture/rtl_modules.md` and `documentation/verification/verification_architecture.md`).
10. Set the simulation top module per stage (Stage 1 testbench top).

Stage 0 has no sources, so there is nothing to compile yet.

## Tcl method (to be created in Stage 1 under `scripts/simulation/`)
A `create_project.tcl` using `create_project`, `add_files`, `set_property top` will be provided once source files exist, and will be run with `vivado -mode batch -source`. It will be tested before being claimed to work.
