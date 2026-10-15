Old Standard TT (© 2011 The Old Standard Project Authors, SIL Open Font License 1.1: OFL-oldstandardtt.txt), cut
down to the Latin letters the settings page uses, for embedding in it (tools/build_page.py):

    uvx --with brotli --from fonttools pyftsubset fonts/OldStandard-Regular.ttf \
      --unicodes="U+0020-007E,U+00A0-00FF,U+0152-0153,U+2013-2014,U+2018-201E,U+2020-2022,U+2026,U+2032-2033,U+2190-2193" \
      --layout-features="kern,liga,sups" --flavor=woff2 --output-file=tools/page/fonts/OldStandard-Regular.woff2

and the same for OldStandard-Italic.
