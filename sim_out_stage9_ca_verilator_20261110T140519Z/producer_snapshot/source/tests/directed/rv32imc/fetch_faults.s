  jal x0, fault
  .org 0xfffe
fault:
  .2byte 0x0013
