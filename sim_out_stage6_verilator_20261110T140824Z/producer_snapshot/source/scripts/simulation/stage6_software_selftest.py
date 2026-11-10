#!/usr/bin/env python3
"""Independent CSR encoding, access-legality, and ISS behavior checks."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rv32_asm
import rv32imc_iss as iss


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def assemble_words(source):
    image = rv32_asm.assemble(source)
    return [image.get(4 * i, 0) for i in range(max(image) // 4 + 1)]


def main():
    encodings = {
        'csrrw': (1, True), 'csrrs': (2, True), 'csrrc': (3, True),
        'csrrwi': (5, False), 'csrrsi': (6, False), 'csrrci': (7, False),
    }
    for mnemonic, (f3, register) in encodings.items():
        source = 'x7' if register else '7'
        raw = rv32_asm.assemble(f'{mnemonic} x9, 0x800, {source}\necall\n')[0]
        require((raw >> 12) & 7 == f3, f'{mnemonic}: funct3')
        require((raw >> 15) & 31 == 7, f'{mnemonic}: source field')
        require((raw >> 20) & 0xFFF == 0x800, f'{mnemonic}: CSR address')
        require(iss._decode32(raw, z_enabled=True)[0], f'{mnemonic}: RW encoding legal')
        require(not iss._decode32(raw, z_enabled=False)[0], f'{mnemonic}: disabled mode must reject')

    require(not iss._decode32(0xC0002073, z_enabled=True)[0], 'unimplemented standard counter')
    require(not iss._decode32(0x300020F3, z_enabled=True)[0], 'unimplemented machine CSR')
    require(not iss._decode32(0x00002073, z_enabled=True)[0], 'unimplemented CSR address')
    require(not iss._decode32(0xCC102073, z_enabled=True)[0], 'CC1 remains unimplemented')
    require(iss._decode32(0x0000100F, z_enabled=True)[0], 'exact FENCE.I is legal')
    require(not iss._decode32(0x0000900F, z_enabled=True)[0], 'malformed FENCE.I is illegal')

    for op in ('csrrs x0, 0xCC0, x0', 'csrrc x1, 0xCC0, x0',
               'csrrsi x2, 0xCC0, 0', 'csrrci x3, 0xCC0, 0'):
        raw = rv32_asm.assemble(op + '\necall\n')[0]
        require(iss._decode32(raw, z_enabled=True)[0], f'RO read with write suppressed is legal: {op}')
    for op in ('csrrw x0, 0xCC0, x0', 'csrrwi x0, 0xCC0, 0',
               'csrrs x1, 0xCC0, x5', 'csrrsi x1, 0xCC0, 1'):
        raw = rv32_asm.assemble(op + '\necall\n')[0]
        require(not iss._decode32(raw, z_enabled=True)[0], f'RO write attempt is illegal: {op}')

    # Focused regression for the former `csrs[0xCC0]` KeyError in sidecar
    # construction: fixed RO state is read consistently but never inserted
    # into the RW scratch dictionary.
    ro_events = []
    ro_program = assemble_words('csrrs x6, 0xCC0, x0\ncsrrsi x7, 0xCC0, 0\necall\n')
    ro_cause, ro_regs, _, ro_footer, _, _ = iss.run(
        ro_program, c_enabled=True, z_enabled=True, z_events=ro_events)
    require(ro_cause == iss.CAUSE_ECALL and ro_regs[6] == iss.CSR_STAGE6_ID and
            ro_regs[7] == iss.CSR_STAGE6_ID, 'focused RO sidecar read returns fixed ID')
    ro_csr_events = [event for event in ro_events if event[0] == 'CSR']
    require([(event[8], event[9], event[10]) for event in ro_csr_events] ==
            [(iss.CSR_STAGE6_ID, iss.CSR_STAGE6_ID, 0)] * 2,
            'focused RO sidecar before/after values and suppressed intent')
    require('CSR cc0 53544736' in ro_footer,
            'focused RO value remains fixed in architectural state')

    src = '\n'.join([
        'li x7, 0x123', 'csrrw x8, 0x800, x7', 'addi x5, x0, 0',
        'csrrs x9, 0x800, x0', 'csrrs x14, 0x800, x5',
        'csrrc x10, 0x800, x0', 'csrrw x15, 0x800, x0',
        'csrrw x16, 0x800, x7', 'csrrwi x11, 0x801, 5',
        'csrrsi x12, 0x801, 0', 'csrrci x13, 0x801, 1',
        'csrrs x1, 0xCC0, x0', 'csrrsi x2, 0xCC0, 0',
        'fence.i', 'ecall', ''
    ])
    events = []
    assembled = rv32_asm.assemble(src)
    cause, regs, rows, footer, oob, retired = iss.run(
        [assembled.get(4 * i, 0) for i in range(max(assembled) // 4 + 1)],
        c_enabled=True, z_enabled=True, z_events=events)
    require(cause == iss.CAUSE_ECALL and oob == 0, 'deterministic CSR program termination')
    require(regs[8] == 0 and regs[9] == 0x123 and regs[10] == 0x123, 'old values and suppression')
    require(regs[11] == 0 and regs[12] == 5 and regs[13] == 5, 'immediate CSR old values')
    require(regs[14] == 0x123, 'nonzero rs1 with zero value still requests CSRRS write')
    require(regs[15] == 0x123 and regs[16] == 0, 'CSRRW x0 source writes and returns old value')
    require(regs[1] == 0x53544736 and regs[2] == 0x53544736, 'fixed RO identification reads')
    require('CSR 800 00000123' in footer and 'CSR 801 00000004' in footer and
            'CSR cc0 53544736' in footer, 'CSR final values')
    csr_events = [e for e in events if e[0] == 'CSR']
    require([e[10] for e in csr_events] == [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0], 'CSR write suppression intent')
    require(all(e[8] == 0x53544736 and e[9] == 0x53544736
                for e in csr_events if e[4] == 0xCC0), 'RO ID remains fixed')
    event_summary = [(event[0], f'{event[1]:08x}') for event in events]
    fence_words = [pc for pc, word in assembled.items() if word == 0x0000100F]
    require(len(fence_words) == 1, f'expected one assembled FENCE.I, found {fence_words}')
    fence_pc = fence_words[0]
    expected_fence = ('FENCEI', fence_pc, 0x0000100F, 4, fence_pc + 4, 0, 0, 0, 0, 0)
    actual_fences = [event for event in events if event[0] == 'FENCEI']
    expected_csr_events = [(pc, (word >> 20) & 0xFFF)
                           for pc, word in sorted(assembled.items())
                           if word & 0x7F == 0x73 and word not in (0x00000073, 0x00100073)]
    actual_csr_events = [(event[1], event[4]) for event in events if event[0] == 'CSR']
    ordered_events = [('CSR', pc) for pc, _ in expected_csr_events] + [('FENCEI', fence_pc)]
    actual_order = [(event[0], event[1]) for event in events]
    ecalls = [pc for pc, word in assembled.items() if word == 0x00000073]
    require(len(ecalls) == 1, f'expected one terminating ECALL, found {ecalls}')
    ecall_pc = ecalls[0]
    expected_retired_pcs = [pc for pc, _ in sorted(assembled.items()) if pc < ecall_pc]
    actual_retired_pcs = [int(row.split()[1], 16) for row in rows]
    stop = next((line.split() for line in footer if line.startswith('STOP ')), None)
    print(f'STAGE6_DIAGNOSTIC events(type,pc)={event_summary}', flush=True)
    print(f'STAGE6_DIAGNOSTIC retired_count={retired}', flush=True)
    print(f'STAGE6_DIAGNOSTIC architectural_instruction_rows={len(rows)} (STOP/footer excluded)', flush=True)
    print(f'STAGE6_DIAGNOSTIC executed_fence_pc={fence_pc:08x} expected_event={expected_fence}', flush=True)
    require(actual_fences == [expected_fence],
            f'FENCE.I event identity/count/order: expected={[expected_fence]} actual={actual_fences}')
    require(actual_csr_events == expected_csr_events,
            f'CSR event identity/order: expected={expected_csr_events} actual={actual_csr_events}')
    require(actual_order == ordered_events,
            f'Z event order: expected={ordered_events} actual={actual_order}')
    require(retired == len(rows) == len(expected_retired_pcs),
            f'retirement accounting mismatch: retired={retired} rows={len(rows)} expected={len(expected_retired_pcs)}')
    require(actual_retired_pcs == expected_retired_pcs,
            f'instruction retirement identity/order mismatch: expected={expected_retired_pcs} actual={actual_retired_pcs}')
    require(ecall_pc not in actual_retired_pcs and stop is not None and
            int(stop[1], 16) == ecall_pc and int(stop[2], 16) == 0x00000073,
            f'terminating ECALL retirement/STOP mismatch: ecall={ecall_pc:08x} stop={stop}')

    for source in ('csrrw x0, 0xCC0, x0', 'csrrwi x0, 0xCC0, 0',
                   'addi x5, x0, 0\ncsrrs x6, 0xCC0, x5'):
        bad_image = rv32_asm.assemble(source + '\necall\n')
        badcause, badregs, bad_rows, badfooter, badoob, bad_retired = iss.run(
            [bad_image.get(4 * i, 0) for i in range(max(bad_image) // 4 + 1)],
            c_enabled=True, z_enabled=True)
        require(badcause == iss.CAUSE_ILLEGAL and badoob == 0, f'RO write faults: {source}')
        require(badregs[6] == 0 and 'CSR cc0 53544736' in badfooter,
                f'RO write fault has no architectural side effect: {source}')
        bad_stop = next(line.split() for line in badfooter if line.startswith('STOP '))
        fault_pc = next(pc for pc, word in bad_image.items()
                        if word >> 20 == iss.CSR_ID_ADDR and (word & 0x7F) == 0x73)
        bad_row_pcs = [int(row.split()[1], 16) for row in bad_rows]
        expected_bad_row_pcs = [pc for pc, _ in sorted(bad_image.items()) if pc < fault_pc]
        require(bad_retired == len(bad_rows) == len(expected_bad_row_pcs) and
                bad_row_pcs == expected_bad_row_pcs and fault_pc not in bad_row_pcs and
                int(bad_stop[1], 16) == fault_pc,
                f'failing CSR instruction retired or STOP PC is wrong: fault={fault_pc:08x} rows={bad_row_pcs} STOP={bad_stop}')
    print('STAGE6_SOFTWARE_SELFTEST PASS encodings=6 legality=13 deterministic_csr=1 ro=read-only')


if __name__ == '__main__':
    main()
