def convertir_svg_a_pdf(svg):
    from cairosvg import svg2pdf

    return svg2pdf(bytestring=svg.encode("utf-8"))
