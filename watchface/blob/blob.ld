/* The renderer's code blob: linked at address 0, its entry table first; main.c adds its load address to every
 * absolute address (the relocations tools/build_blob.py lists after the image). */
ENTRY(plan_api)
SECTIONS
{
  . = 0;
  .text : {
    KEEP(*(.plan_api))
    *(.text .text.*)
    *(.rodata .rodata.*)
    . = ALIGN(4);
  }
  .data : {
    *(.data .data.*)
    . = ALIGN(4);
  }
  .bss (NOLOAD) : {
    *(.bss .bss.* COMMON)
    . = ALIGN(4);
  }
  /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment) *(.note*) *(.ARM.attributes) }
}
